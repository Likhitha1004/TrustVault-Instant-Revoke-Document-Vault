import os
import io
import uuid
import hashlib
import tempfile
import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.models import User, UserRole, Document, AuditLog, DocumentPermission, AuditAction
from app.auth import get_password_hash, create_access_token
from app.storage import StorageManager, storage_manager
from seed import seed_database

def test_liveness_and_readiness_checks():
    client = TestClient(app)
    
    # 1. Liveness endpoint /healthz
    res_liveness = client.get("/healthz")
    assert res_liveness.status_code == 200
    assert res_liveness.json()["status"] == "healthy"

    # 2. Readiness endpoint /readyz
    res_readiness = client.get("/readyz")
    assert res_readiness.status_code == 200
    assert res_readiness.json()["status"] == "ready"
    assert res_readiness.json()["database"] == "connected"

def test_storage_manager_lifecycle():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = settings.STORAGE_DIR
        settings.STORAGE_DIR = temp_dir
        sm = StorageManager()

        test_data = b"%PDF-1.4 simulated binary payload for S3/R2 storage test"
        expected_hash = hashlib.sha256(test_data).hexdigest()
        
        file_obj = io.BytesIO(test_data)
        upload_file = UploadFile(filename="test.pdf", file=file_obj)

        doc_uuid = str(uuid.uuid4())
        storage_id, size, sha256 = pytest.importorskip("asyncio").run(
            sm.save_file(upload_file, doc_uuid, ".pdf", max_size=10*1024*1024)
        )

        assert size == len(test_data)
        assert sha256 == expected_hash
        assert sm.exists(storage_id) is True

        # Verify streaming read
        streamed_chunks = list(sm.get_stream(storage_id))
        reconstructed = b"".join(streamed_chunks)
        assert reconstructed == test_data

        # Verify deletion
        assert sm.delete(storage_id) is True
        assert sm.exists(storage_id) is False

        settings.STORAGE_DIR = original_dir

def test_seed_idempotency_and_production_security():
    # Test isolated SQLite engine
    test_engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSession()
    # 1. Empty DB in dev mode creates demo accounts
    orig_env = settings.ENVIRONMENT
    orig_demo = settings.ALLOW_DEMO_SEED
    try:
        settings.ENVIRONMENT = "production"
        settings.ALLOW_DEMO_SEED = False
        settings.INITIAL_ADMIN_PASSWORD = "SuperSecureAdminPassword2026!"

        # In production without allow demo seed, must NOT seed demo passwords
        # Monkeypatch sessionmaker in seed to use TestingSession
        import seed
        orig_session_local = seed.SessionLocal
        orig_seed_engine = seed.engine
        seed.SessionLocal = TestingSession
        seed.engine = test_engine

        seed_database()

        # Should have exactly 1 user (the admin provisioned with INITIAL_ADMIN_PASSWORD)
        users = db.query(User).all()
        assert len(users) == 1
        assert users[0].email == "admin@trustvault.io"
        assert users[0].role == UserRole.ADMIN

        # Verify idempotency: calling seed_database() again must NOT recreate or add duplicates
        seed_database()
        assert db.query(User).count() == 1

        # Test case: Ordinary users exist, but no admin
        # Clear admin, add ordinary user
        db.query(User).delete()
        db.commit()
        ordinary = User(email="ordinary@user.com", username="ordinary", hashed_password="pw", role=UserRole.VIEWER)
        db.add(ordinary)
        db.commit()

        # Running seed with INITIAL_ADMIN_PASSWORD should provision admin alongside ordinary user
        seed_database()
        assert db.query(User).count() == 2
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        assert admin_user is not None
        assert admin_user.email == "admin@trustvault.io"

    finally:
        seed.SessionLocal = orig_session_local
        seed.engine = orig_seed_engine
        settings.ENVIRONMENT = orig_env
        settings.ALLOW_DEMO_SEED = orig_demo
        settings.INITIAL_ADMIN_PASSWORD = ""
        db.close()

def test_production_storage_safety_guard():
    orig_env = settings.ENVIRONMENT
    orig_ephemeral = settings.ALLOW_EPHEMERAL_STORAGE
    try:
        settings.ENVIRONMENT = "production"
        settings.ALLOW_EPHEMERAL_STORAGE = False
        settings.STORAGE_BACKEND = "local"

        # Must raise RuntimeError to protect against accidental ephemeral disk data loss in production
        with pytest.raises(RuntimeError) as exc_info:
            StorageManager()
        assert "Production safety violation" in str(exc_info.value)

        # Opt-in explicitly allows it
        settings.ALLOW_EPHEMERAL_STORAGE = True
        sm = StorageManager()
        assert sm.backend == "local"
    finally:
        settings.ENVIRONMENT = orig_env
        settings.ALLOW_EPHEMERAL_STORAGE = orig_ephemeral
        settings.STORAGE_BACKEND = "local"

def test_admin_recovery_tool():
    from app.admin_recovery import recover_admin
    import app.admin_recovery as ar

    test_engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    orig_sl = ar.SessionLocal
    orig_eng = ar.engine
    ar.SessionLocal = TestingSession
    ar.engine = test_engine

    try:
        # Recover admin with explicit password
        ok = recover_admin(email="secadmin@trustvault.io", password="SafeRecoveryPass2026!")
        assert ok is True

        db = TestingSession()
        admin = db.query(User).filter(User.email == "secadmin@trustvault.io").first()
        assert admin is not None
        assert admin.role == UserRole.ADMIN

        # Verify password reset
        ok2 = recover_admin(email="secadmin@trustvault.io", password="UpdatedRecoveryPass2026!")
        assert ok2 is True
        db.refresh(admin)
        from app.auth import verify_password
        assert verify_password("UpdatedRecoveryPass2026!", admin.hashed_password) is True
        db.close()
    finally:
        ar.SessionLocal = orig_sl
        ar.engine = orig_eng

def test_database_persistence_across_simulated_restart():
    # Use on-disk sqlite database to simulate restart persistence
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine1 = create_engine(db_url)
        Session1 = sessionmaker(bind=engine1)
        Base.metadata.create_all(bind=engine1)

        db1 = Session1()
        user_uuid = str(uuid.uuid4())
        u = User(id=user_uuid, email="persist@trustvault.io", username="persist_user", hashed_password="hashed_pw", role=UserRole.OWNER)
        db1.add(u)
        doc_uuid = str(uuid.uuid4())
        doc = Document(id=doc_uuid, title="Persistent Doc", original_filename="doc.pdf", storage_path="/fake/path", mime_type="application/pdf", file_size=100, file_hash_sha256="abc", owner_id=user_uuid)
        db1.add(doc)
        db1.commit()
        db1.close()
        engine1.dispose()

        # Simulate fresh process startup / restart
        engine2 = create_engine(db_url)
        Session2 = sessionmaker(bind=engine2)
        db2 = Session2()

        loaded_user = db2.query(User).filter(User.id == user_uuid).first()
        assert loaded_user is not None
        assert loaded_user.email == "persist@trustvault.io"

        loaded_doc = db2.query(Document).filter(Document.id == doc_uuid).first()
        assert loaded_doc is not None
        assert loaded_doc.title == "Persistent Doc"
        db2.close()
        engine2.dispose()

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
