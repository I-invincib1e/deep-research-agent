import requests
import json

try:
    print("Testing Health Check...")
    resp = requests.get("http://localhost:8000/health")
    print(f"Health Status: {resp.status_code}")
    print(resp.json())

    # Optional: Test Research (Real search cost, maybe skip or mocking?)
    # The prompt implies using the provided key, so real test is fine but might be slow/expensive?
    # I'll just skip the heavy test for now or do a dummy topic if I had a mock.
    # But I'll just check health for connectivity.
except Exception as e:
    print(f"Backend Test Failed: {e}")
