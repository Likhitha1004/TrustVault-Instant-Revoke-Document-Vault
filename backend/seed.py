from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, UserRole, Document, AuditAction
from app.auth import get_password_hash
from app.audit import record_audit_event
from app.config import settings
import os

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first() is not None
        user_count = db.query(User).count()
        is_production = settings.ENVIRONMENT.lower() == "production"

        # Production Gate: Strictly forbid default demo passwords
        if is_production and not settings.ALLOW_DEMO_SEED:
            if admin_exists:
                print("Production environment: Administrator account already exists. Skipping provisioning.")
                return

            if settings.INITIAL_ADMIN_PASSWORD:
                # Do NOT log the password value
                print("Production environment: Provisioning initial administrator from environment secret...")
                admin = User(
                    email="admin@trustvault.io",
                    username="admin",
                    hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                    role=UserRole.ADMIN
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
                record_audit_event(
                    db,
                    AuditAction.USER_REGISTER,
                    user_id=admin.id,
                    metadata={"role": "admin", "note": "Initial administrator provisioned via environment secret"}
                )
                print("Production environment: Initial administrator account successfully created.")
            else:
                if user_count > 0:
                    print("Production warning: Ordinary users exist but no administrator found. Set INITIAL_ADMIN_PASSWORD or run admin_recovery tool.")
                else:
                    print("Production notice: INITIAL_ADMIN_PASSWORD not set. System awaiting initial setup.")
            return

        # Development / test environment
        if user_count > 0:
            print(f"Database already contains {user_count} user(s). Skipping seed.")
            return

        print("Seeding demo accounts for development / testing environment...")
        
        # 1. Administrator
        admin = User(
            email="admin@trustvault.io",
            username="admin",
            hashed_password=get_password_hash("AdminPass2026!"),
            role=UserRole.ADMIN
        )
        db.add(admin)

        # 2. Document Owner
        owner = User(
            email="owner@trustvault.io",
            username="alice_owner",
            hashed_password=get_password_hash("OwnerPass2026!"),
            role=UserRole.OWNER
        )
        db.add(owner)

        # 3. Viewer
        viewer = User(
            email="viewer@trustvault.io",
            username="bob_viewer",
            hashed_password=get_password_hash("ViewerPass2026!"),
            role=UserRole.VIEWER
        )
        db.add(viewer)

        # 4. Unauthorized Viewer (Competitor / External)
        external = User(
            email="eve@competitor.io",
            username="eve_external",
            hashed_password=get_password_hash("EvePass2026!"),
            role=UserRole.VIEWER
        )
        db.add(external)

        db.commit()
        db.refresh(admin)
        db.refresh(owner)
        db.refresh(viewer)
        db.refresh(external)

        # Seed initial audit logs
        record_audit_event(db, AuditAction.USER_REGISTER, user_id=admin.id, metadata={"role": "admin", "note": "System initialized"})
        record_audit_event(db, AuditAction.USER_REGISTER, user_id=owner.id, metadata={"role": "owner"})
        record_audit_event(db, AuditAction.USER_REGISTER, user_id=viewer.id, metadata={"role": "viewer"})

        print("Seed accounts created successfully:")
        print("1. Admin: admin@trustvault.io / AdminPass2026!")
        print("2. Owner: owner@trustvault.io / OwnerPass2026!")
        print("3. Viewer: viewer@trustvault.io / ViewerPass2026!")
        print("4. External: eve@competitor.io / EvePass2026!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
