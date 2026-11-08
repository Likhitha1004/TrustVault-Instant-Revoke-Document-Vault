# 08 — BACKEND ARCHITECTURE AUDIT
## Layered Design, ORM Discipline, and Service Modularity

- **FastAPI Layer**: Modular APIRouters split logically into `routes_auth.py`, `routes_documents.py`, `routes_audit.py`, mounted under `/api` in `main.py`.
- **Database Layer**: SQLAlchemy models with strict foreign keys (`ForeignKey(users.id, ondelete='CASCADE')`), UUID primary keys, and indexed query columns (`owner_id`, `category`, `created_at`, `is_deleted`).
- **ORM Optimization**: Document queries employ `joinedload(Document.owner)` and `selectinload(Document.permissions)` to prevent N+1 query performance degradation.
- **Transaction Safety**: All database modifications execute inside explicit scoped transactions (`db.commit()`) with immediate rollback on exceptions.
- **Advisory Locking**: Audit ledger writes acquire `pg_advisory_xact_lock(77123991)` to guarantee deterministic, sequential SHA-256 chaining even under heavy concurrent write loads.
- **Architectural Status**: **PASS** (Zero circular imports, clean separation of concerns).
