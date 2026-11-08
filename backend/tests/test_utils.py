"""Test-only helpers; privileged actors are created directly in isolated test databases."""
from app.models import User, UserRole

def register_user(client, db_session, payload):
    requested_role = payload.get("role", "viewer")
    public_payload = {key: value for key, value in payload.items() if key != "role"}
    response = client.post("/api/auth/register", json=public_payload)
    if response.status_code == 201 and requested_role in {"owner", "admin"}:
        user = db_session.query(User).filter(User.email == payload["email"]).one()
        user.role = UserRole(requested_role)
        db_session.commit()
    return response
