import os
import sys
import tempfile
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import backend modules
sys.path.insert(0, "C:/Users/Snuhith/projects/TrustVault/backend")
from app.database import Base
import app.models
from app.models import User, Document, DocumentPermission, AuditLog, RevokedToken, UserRole
from app.auth import get_password_hash

def test_clean_db_setup():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        clean_db_path = tmp.name

    try:
        print(f"[DB Setup Test] Testing clean database setup at: {clean_db_path}")
        engine = create_engine(f"sqlite:///{clean_db_path}")
        
        # 1. Create tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables created
        conn = sqlite3.connect(clean_db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print(f"[DB Setup Test] Tables created: {tables}")
        assert "users" in tables
        assert "documents" in tables
        assert "document_permissions" in tables
        assert "audit_logs" in tables
        assert "revoked_tokens" in tables

        # 2. Seed initial data
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        admin_user = User(
            email="admin@test.io",
            username="admin_test",
            hashed_password=get_password_hash("AdminPass123!"),
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        db.commit()
        
        # Verify user persisted
        saved_admin = db.query(User).filter(User.username == "admin_test").first()
        assert saved_admin is not None
        assert saved_admin.role == UserRole.ADMIN
        print("[DB Setup Test] PASS: Clean database migration and user seed verified")
        db.close()
        conn.close()
        engine.dispose()

    finally:
        if os.path.exists(clean_db_path):
            os.remove(clean_db_path)
            print("[DB Setup Test] Temporary clean DB cleaned up.")

if __name__ == "__main__":
    test_clean_db_setup()
