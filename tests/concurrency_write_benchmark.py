import asyncio
import httpx
import time
import uuid

BASE_URL = "http://127.0.0.1:8000"

async def register_and_upload(client, idx):
    uid = uuid.uuid4().hex[:8]
    username = f"user_{idx}_{uid}"
    email = f"user_{idx}_{uid}@example.com"
    password = "TestPassword123!"
    
    t0 = time.perf_counter()
    try:
        # 1. Register as owner
        r_reg = await client.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "email": email,
            "password": password,
            "role": "owner"
        }, timeout=60.0)
        if r_reg.status_code not in (200, 201):
            return "reg_fail", (time.perf_counter() - t0) * 1000, r_reg.status_code
        
        # 2. Login to get token
        r_log = await client.post(f"{BASE_URL}/api/auth/login", json={
            "username_or_email": username,
            "password": password
        }, timeout=60.0)
        if r_log.status_code != 200:
            return "login_fail", (time.perf_counter() - t0) * 1000, r_log.status_code
            
        token = r_log.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Upload document with valid title and data
        data = {"title": f"Doc {idx}", "category": "Legal"}
        files = {"file": (f"test_{idx}.txt", b"Hello TrustVault Concurrency Benchmark Data", "text/plain")}
        r_up = await client.post(
            f"{BASE_URL}/api/documents/upload",
            headers=headers,
            data=data,
            files=files,
            timeout=60.0
        )
        dt = (time.perf_counter() - t0) * 1000
        if r_up.status_code in (200, 201):
            return "success", dt, 200
        else:
            return "up_fail", dt, r_up.status_code
    except Exception as e:
        return "exception", (time.perf_counter() - t0) * 1000, str(e)

async def test_write_concurrency(vus=50):
    print(f"\n--- Testing Concurrent Write Workload ({vus} simultaneous users) ---")
    limits = httpx.Limits(max_keepalive_connections=vus + 10, max_connections=vus + 20)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [register_and_upload(client, i) for i in range(vus)]
        results = await asyncio.gather(*tasks)
    
    success = sum(1 for r in results if r[0] == "success")
    failures = [r for r in results if r[0] != "success"]
    lats = [r[1] for r in results]
    print(f"Results: {success}/{vus} succeeded ({success/vus*100:.1f}%)")
    print(f"Average total transaction time: {sum(lats)/len(lats):.1f}ms")
    if failures:
        print(f"Failures ({len(failures)}):")
        for f in failures[:5]:
            print(f"  {f}")
    return success == vus

if __name__ == "__main__":
    asyncio.run(test_write_concurrency(50))
