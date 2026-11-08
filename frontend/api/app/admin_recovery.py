import os
import sys
import getpass
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models import User, UserRole, AuditAction
from app.auth import get_password_hash
from app.audit import record_audit_event

def recover_admin(email: str = "admin@trustvault.io", password: str = None) -> bool:
    """
    Safely creates or resets an administrator account.
    Never prints password to standard output or logs.
    """
    if not password:
        password = os.getenv("RECOVERY_ADMIN_PASSWORD")
    if not password:
        if sys.stdin.isatty():
            password = getpass.getpass(prompt="Enter new administrator password: ")
        else:
            print("Error: RECOVERY_ADMIN_PASSWORD environment variable or TTY input required.")
            return False

    if len(password) < 8:
        print("Error: Administrator password must be at least 8 characters.")
        return False

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == email).first()
        if admin:
            admin.hashed_password = get_password_hash(password)
            admin.role = UserRole.ADMIN
            db.commit()
            db.refresh(admin)
            record_audit_event(
                db,
                AuditAction.USER_LOGIN,  # or custom administrative event
                user_id=admin.id,
                metadata={"action": "admin_recovery", "note": "Administrator password reset via CLI recovery tool"}
            )
            print(f"Success: Administrator account '{email}' password updated.")
        else:
            username = email.split("@")[0]
            admin = User(
                email=email,
                username=username,
                hashed_password=get_password_hash(password),
                role=UserRole.ADMIN
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            record_audit_event(
                db,
                AuditAction.USER_REGISTER,
                user_id=admin.id,
                metadata={"action": "admin_recovery", "note": "Administrator account provisioned via CLI recovery tool"}
            )
            print(f"Success: Administrator account '{email}' provisioned.")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    target_email = sys.argv[1] if len(sys.argv) > 1 else "admin@trustvault.io"
    recover_admin(email=target_email)
