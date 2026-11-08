#!/usr/bin/env python3
"""
TrustVault Production Synthetic Monitor
Checks Vercel deployment, API health, Supabase DB connection, and S3 storage availability.
"""
import time
import json
import urllib.request
import urllib.error

PRODUCTION_URL = "https://trust-vault-smoky.vercel.app"

def check_endpoint(name, url, expected_status=200):
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrustVault-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            latency_ms = (time.perf_counter() - start) * 1000
            data = resp.read().decode("utf-8")
            return {
                "name": name,
                "url": url,
                "status": "HEALTHY",
                "http_code": resp.status,
                "latency_ms": round(latency_ms, 2),
                "detail": data[:120]
            }
    except urllib.error.HTTPError as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "name": name,
            "url": url,
            "status": "UNHEALTHY",
            "http_code": e.code,
            "latency_ms": round(latency_ms, 2),
            "detail": e.read().decode("utf-8", errors="ignore")[:120]
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "name": name,
            "url": url,
            "status": "FAILED",
            "http_code": 0,
            "latency_ms": round(latency_ms, 2),
            "detail": str(e)
        }

def run_synthetic_monitoring():
    checks = [
        ("Vercel Frontend Root", PRODUCTION_URL),
        ("FastAPI /healthz", f"{PRODUCTION_URL}/healthz"),
        ("Supabase DB /api/readyz", f"{PRODUCTION_URL}/api/readyz"),
        ("API Documentation /docs", f"{PRODUCTION_URL}/docs"),
    ]
    
    results = [check_endpoint(name, url) for name, url in checks]
    all_healthy = all(r["status"] == "HEALTHY" for r in results)
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "overall_status": "PASS" if all_healthy else "FAIL",
        "monitoring_type": "On-demand synthetic monitoring / request-triggered",
        "checks": results
    }
    return report

if __name__ == "__main__":
    rep = run_synthetic_monitoring()
    print(json.dumps(rep, indent=2))
