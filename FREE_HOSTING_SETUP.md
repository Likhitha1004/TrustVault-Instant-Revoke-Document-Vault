# TRUSTVAULT ZERO-COST HOSTING SETUP (₹0/MONTH)

**Architecture Model:** Zero-Cost Serverless & Container Pipeline  
**Monthly Cost:** **Strictly ₹0.00 / month (100% Free Tiers)**  
**Target Services:** Vercel (Edge Frontend) + Render (Free FastAPI Container) + Supabase (Free Managed PostgreSQL) + Cloudflare R2 (Free S3 Object Storage)

---

## 1. Architectural Blueprint & Provider Allocation

```
+-----------------------------------------------------------------------------------+
|                              USER BROWSER / CLIENT                                |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | HTTPS (Web Requests & Static Assets)
                                          v
+-----------------------------------------------------------------------------------+
|                        VERCEL EDGE CDN (Project: trust-vault)                     |
|  - Domain: https://trust-vault-smoky.vercel.app                                   |
|  - Free Allowance: 100 GB Bandwidth / mo, Unlimited Edge Deployments              |
|  - Reverse Proxy: Rewrites /api/* -> https://trustvault-backend.onrender.com/api/*|
|  - SPA Routing: Clean fallback to /index.html for client-side navigation          |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | Proxied API Calls (JSON & Streaming Binary)
                                          v
+-----------------------------------------------------------------------------------+
|                           RENDER FREE TIER WEB SERVICE                            |
|  - Service: trustvault-backend.onrender.com                                       |
|  - Specs: 512 MB RAM, 0.1 vCPU, 750 Free Instance Hours / month                   |
|  - Storage: Strictly Ephemeral (Runtime guard prevents local doc storage in prod) |
|  - Cold Start: Auto-sleeps after 15m idle; resumes automatically on inbound req   |
|  - Probes: /healthz (liveness) and /readyz (database readiness)                   |
+------------------------------------+----------------------------------------------+
                                     |
                +--------------------+--------------------+
                |                                         |
                | PostgreSQL Queries (SSL Required)       | S3 API Signed Requests (SigV4)
                v                                         v
+-----------------------------------+   +-------------------------------------------+
|      SUPABASE FREE POSTGRESQL     |   |         CLOUDFLARE R2 OBJECT STORAGE      |
|  - DB Storage: 500 MB Free Tier   |   |  - Storage: 10 GB Free Monthly Storage    |
|  - Connection: Transaction Pooler |   |  - Class A (Write): 1,000,000 requests/mo |
|  - Port: 6543 (pgbouncer/supavisor|   |  - Class B (Read): 10,000,000 requests/mo |
|  - Egress: 2 GB Free / month      |   |  - Egress Bandwidth: $0.00 (Zero Egress!) |
|  - SSL: sslmode=require           |   |  - Bucket Access: Strict Private Only     |
+-----------------------------------+   +-------------------------------------------+
```

---

## 2. Step-by-Step Setup Guide

### Step 1: Frontend Deployment on Vercel (Completed)
- **Status:** **ACTIVE & LIVE**
- **Vercel Project:** `trust-vault`
- **Production URL:** `https://trust-vault-smoky.vercel.app`
- **Configuration (`frontend/vercel.json`):**
  ```json
  {
    "buildCommand": "npm run build",
    "outputDirectory": "dist",
    "framework": "vite",
    "rewrites": [
      {
        "source": "/api/(.*)",
        "destination": "https://trustvault-backend.onrender.com/api/$1"
      },
      {
        "source": "/(.*)",
        "destination": "/index.html"
      }
    ]
  }
  ```

---

### Step 2: Supabase Free PostgreSQL Provisioning
1. Sign up / Log in to [Supabase](https://supabase.com) (Free tier, no credit card required).
2. Click **New Project**:
   - **Name:** `trustvault-db`
   - **Database Password:** Generate a high-entropy password (save securely).
   - **Region:** Choose closest to Render backend (e.g., `US West - Oregon` or `AWS us-west-2`).
   - **Pricing Plan:** Select **Free ($0/month)**.
3. Obtain Connection String:
   - Navigate to **Project Settings** > **Database** > **Connection Pooling**.
   - Mode: **Transaction** (Port `6543`) or **Session** (Port `5432`).
   - Connection string format:
     ```
     postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
     ```
4. Note: SQLAlchemy automatically handles connection pooling with `pool_pre_ping=True`, `pool_size=5`, and `max_overflow=10` configured in `backend/app/database.py`.

---

### Step 3: Cloudflare R2 Standard Free Storage Provisioning
1. Sign up / Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com).
2. In the sidebar, navigate to **R2 Object Storage**.
3. Click **Create Bucket**:
   - **Bucket Name:** `trustvault-prod-docs`
   - **Location:** Automatic or Western North America.
   - **Default Storage Class:** Standard.
   - Click **Create Bucket**.
4. Enforce Strict Private Access:
   - In bucket settings, ensure **Public Access** remains **Disabled**.
   - Do NOT connect a custom public domain or allow public R2 dev URLs.
5. Create R2 API Tokens:
   - Go to **R2** > **Manage R2 API Tokens** > **Create API Token**.
   - **Token Name:** `trustvault-render-backend`
   - **Permissions:** `Object Read & Write`.
   - **Bucket Scope:** Restrict to `trustvault-prod-docs`.
   - Copy:
     - **Account ID** (for endpoint URL: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`)
     - **Access Key ID**
     - **Secret Access Key**

---

### Step 4: Render Free Backend Configuration
1. Open [Render Dashboard](https://dashboard.render.com).
2. Select your existing Web Service `trustvault-backend`.
3. In **Environment**, configure the following environment variables:

| Key | Value | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Activates production security gates |
| `DATABASE_URL` | `postgresql://postgres.[REF]:[PW]@...pooler.supabase.com:6543/postgres?sslmode=require` | Supabase Pooled Connection |
| `STORAGE_BACKEND` | `s3` | Routes all document binary operations to Cloudflare R2 |
| `S3_ENDPOINT_URL` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` | Cloudflare R2 S3 Endpoint |
| `S3_BUCKET_NAME` | `trustvault-prod-docs` | Cloudflare R2 Private Bucket |
| `S3_ACCESS_KEY_ID` | `<CLOUDFLARE_R2_ACCESS_KEY_ID>` | Cloudflare R2 Credentials |
| `S3_SECRET_ACCESS_KEY`| `<CLOUDFLARE_R2_SECRET_ACCESS_KEY>` | Cloudflare R2 Credentials |
| `S3_REGION_NAME` | `auto` | Cloudflare R2 region |
| `ALLOW_EPHEMERAL_STORAGE`| `false` | Guards against accidental local disk usage |
| `ALLOW_DEMO_SEED` | `false` | Prevents default credentials in production |
| `INITIAL_ADMIN_PASSWORD` | `<SECURE_ADMIN_PASS_2026>` | Used once on first boot to create admin |
| `SECRET_KEY` | `<HIGH_ENTROPY_RANDOM_HEX_64>` | JWT encryption secret |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token validity |

4. Under **Settings**:
   - **Start Command:** `python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/healthz`
5. Click **Manual Deploy** > **Deploy latest commit** from `main`.
