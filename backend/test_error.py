from fastapi.testclient import TestClient
from main import app
import sys
import os
import asyncio

client = TestClient(app)

print("Starting test...", flush=True)

def test_endpoints():
    response = client.get("/api/v1/projects")
    print(f"Projects response: {response.status_code}")
    print(response.text)

if __name__ == "__main__":
    test_endpoints()
