import pytest
from httpx import AsyncClient


async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_register_login(client: AsyncClient):
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123",
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    assert r.json()["email"] == payload["email"]
