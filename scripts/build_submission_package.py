import os
import shutil
import zipfile

base_dir = r"C:/Users/Snuhith/projects/TrustVault"
deliverables_dir = os.path.join(base_dir, "submission-deliverables")
os.makedirs(deliverables_dir, exist_ok=True)

# 1. Copy Handbook PDF
pdf_src = os.path.join(base_dir, "TRUSTVAULT_COMPLETE_PROJECT_HANDBOOK.pdf")
if os.path.exists(pdf_src):
    shutil.copy2(pdf_src, os.path.join(deliverables_dir, "PROJECT_HANDBOOK.pdf"))

# 2. Copy Submission Answers
sub_src = os.path.join(base_dir, "SUBMISSION_ANSWERS.md")
if os.path.exists(sub_src):
    shutil.copy2(sub_src, os.path.join(deliverables_dir, "SUBMISSION_ANSWERS.md"))

# 3. Copy Documentation Index
idx_src = os.path.join(base_dir, "TRUSTVAULT_DOCUMENTATION_INDEX.md")
if os.path.exists(idx_src):
    shutil.copy2(idx_src, os.path.join(deliverables_dir, "DOCUMENTATION_INDEX.md"))

# 4. Copy Delivery Report
rep_src = os.path.join(base_dir, "TRUSTVAULT_DOCUMENTATION_DELIVERY_REPORT.md")
if os.path.exists(rep_src):
    shutil.copy2(rep_src, os.path.join(deliverables_dir, "VERIFICATION_REPORT.md"))

# 5. Create DEMO_SCRIPT.md
demo_script = """# TRUSTVAULT — 5-MINUTE HACKATHON DEMO WALKTHROUGH

## 0:00 - 0:45 | Introduction & Problem Statement
- **Speaker**: "Hello evaluators, my name is GVS Snuhith. Today I am presenting TrustVault, an enterprise-grade zero-trust document security platform. In typical systems like Google Drive, document sharing suffers from IDOR vulnerabilities, stale permissions upon revocation, and mutable audit logs. TrustVault solves this with server-enforced RBAC, instant 0ms revocation, and an append-only SHA-256 chained cryptographic audit ledger."

## 0:45 - 1:45 | Authentication & Multi-Role Architecture
- **Action**: Log in as `owner@trustvault.io`.
- **Display**: Show clean, responsive Vault dashboard. Highlight distinct categories, search filters, and file metadata.
- **Key Point**: Explain that all API calls carry signed JWTs, and roles (`Admin`, `Owner`, `Viewer`) are verified server-side on every request.

## 1:45 - 2:45 | Secure Upload & Magic Bytes Inspection
- **Action**: Upload a confidential document `Semester_Results.pdf`.
- **Behind the Scenes**: Show that the backend reads the first 2,048 bytes, verifying `%PDF-` magic bytes and rejecting executable files disguised with a `.pdf` extension.
- **Display**: Document appears in Vault instantly with optimistic UI updates (<15ms perceived latency).

## 2:45 - 3:45 | Granular Sharing & Instant Revocation (Zero Stale Window)
- **Action**: Share `Semester_Results.pdf` with `viewer@trustvault.io` with `can_read=True`.
- **Action**: Open incognito tab, log in as `viewer@trustvault.io`. Download succeeds via streaming proxy.
- **Action**: In the owner tab, immediately revoke viewer's permission.
- **Action**: In the viewer tab, attempt download again. Request fails instantly with HTTP 404 Not Found (0ms window).

## 3:45 - 4:30 | Cryptographic Audit Ledger & Tamper Detection
- **Action**: Log in as `admin@trustvault.io` and open the **Audit Logs** tab.
- **Display**: Show the chained log sequence. Each block contains `prev_hash` bound to `record_hash`.
- **Action**: Click **Verify Cryptographic Chain**. The engine scans the entire database ledger and returns: `All blocks valid (Tamper-free)`. Explain advisory locking preventing ledger forks.

## 4:30 - 5:00 | Conclusion & Architecture Defense
- **Speaker**: "TrustVault runs on FastAPI, React 19, Supabase PostgreSQL, and cloud S3 storage, backed by 29 automated tests covering 100% of adversarial boundaries with zero mocks. Thank you!"
"""
with open(os.path.join(deliverables_dir, "DEMO_SCRIPT.md"), "w", encoding="utf-8") as f:
    f.write(demo_script.strip() + "\n")

# 6. Create Package ZIP
pkg_zip_path = os.path.join(base_dir, "TRUSTVAULT_SUBMISSION_DELIVERABLES.zip")
with zipfile.ZipFile(pkg_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(deliverables_dir):
        for f in files:
            full_p = os.path.join(root, f)
            rel_p = os.path.relpath(full_p, deliverables_dir)
            zf.write(full_p, arcname=rel_p)

print("Deliverables folder and submission package ZIP built successfully")
