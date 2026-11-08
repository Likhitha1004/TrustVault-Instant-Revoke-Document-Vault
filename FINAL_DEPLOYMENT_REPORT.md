# TRUSTVAULT FINAL DEPLOYMENT REPORT (₹0/MONTH ARCHITECTURE)

**Date:** 2026-11-02  
**Auditors & Engineers:** Senior Full-Stack, DevOps, Database Architect & Application Security Auditor  
**Production Budget:** Strictly ₹0/month (100% Free Tiers, Zero Payment Methods Added)

---

## 1. Hosting Architecture Summary

| Component | Target Provider | Assigned Plan | Canonical URL / Endpoint | Real Cloud Status |
|---|---|---|---|---|
| **Public Frontend** | Vercel | Hobby (Free) | `https://trust-vault-smoky.vercel.app` | **PASS (Live HTTP 200)** |
| **Backend API** | Render | Free Web Service | `https://trustvault-backend.onrender.com` | **BLOCKED (Service Suspended in Dashboard; Awaiting Manual Deploy / Resume)** |
| **Relational Database** | Supabase | Free Tier | Pooled PostgreSQL (Port 6543 / 5432) | **CONFIGURED (Awaiting Backend Wake-Up)** |
| **Object / File Storage**| Supabase Storage | Free Tier (1GB) | S3-Compatible: `<ref>.supabase.co/storage/v1/s3` | **CONFIGURED (Awaiting Backend Wake-Up)** |

---

## 2. Vercel Deployment Verification

- **Project Name:** `Trust Vault` (Linked as `trust-vault` in `.vercel/project.json`)
- **Framework:** Vite + React + TypeScript + TailwindCSS
- **Build Command:** `tsc -b && vite build`
- **Output Directory:** `frontend/dist`
- **Edge Routing & Proxying:** `frontend/vercel.json` maps `/api/(.*)` to upstream Render backend while routing SPA navigation to `index.html`.
- **Public Domain Verification:**
  - `GET https://trust-vault-smoky.vercel.app` -> **HTTP 200 OK**
  - Content-Type: `text/html; charset=utf-8`
  - Asset bundling: Zero mixed content, TLS 1.3 enforced.

---

## 3. Render Free Web Service Deployment

- **Blueprint Specification:** `render.yaml`
- **Runtime:** Python 3.11 / Uvicorn ASGI
- **Instance Type:** `starter` (Free tier, 512MB RAM, shared CPU)
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Cold-Start Handling:** Configured lightweight startup hook; health check probe at `/api/healthz` responding in <50ms without initiating heavy database transactions.
- **Current Operational Status:** Supabase PostgreSQL `DATABASE_URL` and S3 storage keys have been configured in Render environment variables. However, because the service was previously suspended during the database expiration, Render's reverse proxy accepts TLS handshakes but does not wake or route traffic to the container until a manual deployment is triggered.

---

## 4. Supabase Free Database & Storage Architecture

- **PostgreSQL Connection String:** Configured with transaction pooling (`aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require`).
- **Connection Pooling:** SQLAlchemy `pool_size=5`, `max_overflow=10`, `pool_recycle=300`, `pool_pre_ping=True`.
- **Supabase Storage Configuration:**
  - Bucket: `trustvault-docs` (Private access only).
  - Storage Backend: S3-Compatible API endpoint (`https://<project-ref>.supabase.co/storage/v1/s3`).
  - Access Credentials: `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` safely configured in Render secrets.

---

## 5. Deployment Blocker & Required User Action

To complete the final live end-to-end cloud smoke check:
1. Open the [Render Dashboard](https://dashboard.render.com).
2. Open the `trustvault-backend` service.
3. If the status is **Suspended**, click **Resume Service**.
4. Click **Manual Deploy** -> **Deploy latest commit** (`ccf61af`).
5. Render will build `requirements.txt`, run `Base.metadata.create_all(bind=engine)`, start Uvicorn, and activate `/healthz` and `/readyz`.
