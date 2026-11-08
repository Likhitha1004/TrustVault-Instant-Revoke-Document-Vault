def kill_port(port):
    try:
        out = subprocess.check_output(f'netstat -ano | findstr 127.0.0.1:{port}', shell=True).decode()
        for line in out.strip().splitlines():
            if 'LISTENING' in line:
                pid = line.strip().split()[-1]
                subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                time.sleep(0.5)
    except:
        pass
import stat

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def force_remove_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path, onerror=remove_readonly)
import os
import sys
import shutil
import subprocess
import time
import json
import urllib.request
import urllib.error

CLONE_DIR = "C:/Users/Snuhith/projects/TrustVault_CleanClone"
SRC_REPO = "C:/Users/Snuhith/projects/TrustVault"

def run_cmd(cmd, cwd=None, check=True):
    print(f">> Running: {cmd} (cwd={cwd})")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"FAILED: {res.stderr}")
        raise RuntimeError(f"Command failed: {cmd}\n{res.stderr}")
    return res

def main():
    print("=== STARTING GENUINE CLEAN-CLONE AUDIT ==="); kill_port(8001); time.sleep(1)
    
    # 1. Clean existing clone dir if present
    if os.path.exists(CLONE_DIR):
        print(f"Cleaning existing clone dir: {CLONE_DIR}")
        force_remove_dir(CLONE_DIR)

    # 2. Clone repository into clean directory
    print(f"1. Cloning repo from {SRC_REPO} to {CLONE_DIR}...")
    run_cmd(f'"C:/Program Files/Git/cmd/git.exe" clone "{SRC_REPO}" "{CLONE_DIR}"')
    assert os.path.exists(os.path.join(CLONE_DIR, "backend")), "backend folder missing in clone"
    assert os.path.exists(os.path.join(CLONE_DIR, "frontend")), "frontend folder missing in clone"
    print("   Git clone: PASS")

    # 3. Backend Setup & Dependencies
    print("2. Setting up backend venv and database...")
    backend_dir = os.path.join(CLONE_DIR, "backend")
    # Create venv
    run_cmd("python -m venv venv", cwd=backend_dir)
    python_exe = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
    
    # Install dependencies from requirements.txt
    print("   Installing backend requirements...")
    run_cmd(f'"{python_exe}" -m pip install --quiet --upgrade pip', cwd=backend_dir)
    run_cmd(f'"{python_exe}" -m pip install --quiet -r requirements.txt', cwd=backend_dir)
    print("   Dependencies installed: PASS")

    # Initialize fresh database via seed.py or migration
    print("   Initializing and seeding database...")
    run_cmd(f'"{python_exe}" seed.py', cwd=backend_dir)
    db_file = os.path.join(backend_dir, "trustvault.db")
    assert os.path.exists(db_file), f"Database file not created at {db_file}"
    print("   Database initialized & seeded: PASS")

    # 4. Start backend on unique test port 8001
    print("3. Launching clean backend on port 8001...")
    proc_backend = subprocess.Popen(
        f'"{python_exe}" -m uvicorn app.main:app --host 127.0.0.1 --port 8001',
        shell=True,
        cwd=backend_dir
    )

    clean_base = "http://127.0.0.1:8001/api"
    # Wait for backend readiness
    for _ in range(20):
        time.sleep(0.5)
        try:
            r = urllib.request.urlopen("http://127.0.0.1:8001/docs")
            if r.status == 200:
                print("   Clean backend online: PASS")
                break
        except:
            pass

    try:
        # 5. Register and Authenticate a test user
        print("4. Registering and authenticating test user...")
        reg_payload = json.dumps({
            "username": "clone_tester",
            "email": "clone_tester@trustvault.io",
            "password": "Password123!",
            "role": "owner"
        }).encode()
        req = urllib.request.Request(f"{clean_base}/auth/register", data=reg_payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            assert resp.status in (200, 201)
        print("   User registration: PASS")

        login_payload = json.dumps({
            "username_or_email": "clone_tester@trustvault.io",
            "password": "Password123!"
        }).encode()
        req = urllib.request.Request(f"{clean_base}/auth/login", data=login_payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            login_data = json.loads(resp.read().decode())
        token = login_data["access_token"]
        print("   User authentication: PASS")

        # 6. Upload a test document
        print("5. Uploading test document...")
        boundary = "----CleanCloneBoundary"
        import io
        body = io.BytesIO()
        body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"clean_clone.pdf\"\r\nContent-Type: application/pdf\r\n\r\n".encode())
        body.write(b"%PDF-1.4 Clean Clone Test PDF")
        body.write(f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\nClean Clone Document\r\n".encode())
        body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"category\"\r\n\r\nConfidential\r\n".encode())
        body.write(f"--{boundary}--\r\n".encode())

        req = urllib.request.Request(
            f"{clean_base}/documents/upload",
            data=body.getvalue(),
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {token}"
            },
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            doc_data = json.loads(resp.read().decode())
        doc_id = doc_data["id"]
        print(f"   Upload document ({doc_id}): PASS")

        # 7. Share / Grant permission
        print("6. Granting permission to viewer@trustvault.io...")
        grant_payload = json.dumps({
            "grantee_email": "viewer@trustvault.io",
            "can_edit": False
        }).encode()
        req = urllib.request.Request(
            f"{clean_base}/documents/{doc_id}/permissions",
            data=grant_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            perm_data = json.loads(resp.read().decode())
        print(f"   Grant permission: PASS")

        # 8. Download document
        print("7. Downloading document binary...")
        req = urllib.request.Request(
            f"{clean_base}/documents/{doc_id}/download",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            assert content == b"%PDF-1.4 Clean Clone Test PDF", "Downloaded content mismatch"
        print("   Download byte-level integrity: PASS")

        # 9. Revoke permission
        print("8. Revoking permission...")
        req = urllib.request.Request(
            f"{clean_base}/documents/{doc_id}/permissions/viewer@trustvault.io",
            headers={"Authorization": f"Bearer {token}"},
            method="DELETE"
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
        print("   Revoke permission: PASS")

        # 10. Delete document
        print("9. Deleting document...")
        req = urllib.request.Request(
            f"{clean_base}/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
            method="DELETE"
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
        print("   Delete document: PASS")

        # 11. Verify cryptographic audit trail on clean install
        print("10. Verifying audit chain on clean clone...")
        # Login admin to verify audit
        login_admin = json.dumps({
            "username_or_email": "admin@trustvault.io",
            "password": "AdminPass2026!"
        }).encode()
        req = urllib.request.Request(f"{clean_base}/auth/login", data=login_admin, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            admin_token = json.loads(resp.read().decode())["access_token"]

        req = urllib.request.Request(f"{clean_base}/audit/verify", headers={"Authorization": f"Bearer {admin_token}"})
        with urllib.request.urlopen(req) as resp:
            chain_res = json.loads(resp.read().decode())
            assert chain_res["status"] == "valid", f"Chain invalid: {chain_res}"
        print(f"   Cryptographic audit chain verification ({chain_res['status']}): PASS")

        print("=== GENUINE CLEAN CLONE AND WORKFLOW VERIFICATION: 100% PASS ===")

    finally:
        # Kill backend
        print("Tearing down clean-clone backend..."); kill_port(8001); time.sleep(1)
        subprocess.run(f"taskkill /F /T /PID {proc_backend.pid}", shell=True, capture_output=True)
        # Clean up directory
        time.sleep(1)
        force_remove_dir(CLONE_DIR)
        print("Clean clone workspace cleaned up.")

if __name__ == "__main__":
    main()
