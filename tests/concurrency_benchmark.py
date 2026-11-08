import asyncio
import httpx
import time
import statistics

BASE_URL = "http://127.0.0.1:8000"

async def fetch(client, url):
    t0 = time.perf_counter()
    try:
        resp = await client.get(url, timeout=10.0)
        dt = (time.perf_counter() - t0) * 1000
        return resp.status_code, dt, None
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        return None, dt, str(e)

async def test_concurrency(vus, endpoint="/readyz"):
    limits = httpx.Limits(max_keepalive_connections=vus + 10, max_connections=vus + 20)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [fetch(client, f"{BASE_URL}{endpoint}") for _ in range(vus)]
        results = await asyncio.gather(*tasks)
    
    statuses = [r[0] for r in results]
    latencies = [r[1] for r in results]
    errors = [r[2] for r in results if r[2] is not None]
    
    success = sum(1 for s in statuses if s == 200)
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    max_lat = max(latencies)
    
    print(f"VUs: {vus:3d} | Success: {success}/{vus} ({success/vus*100:.1f}%) | "
          f"p50: {p50:6.1f}ms | p95: {p95:6.1f}ms | max: {max_lat:6.1f}ms | Errors: {len(errors)}")
    return success == vus

async def main():
    print("=== TRUSTVAULT CONCURRENCY BENCHMARK ===")
    for vus in [1, 2, 5, 10, 20, 50, 100]:
        await test_concurrency(vus, "/readyz")
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
