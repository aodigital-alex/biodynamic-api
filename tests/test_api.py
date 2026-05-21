"""Integration tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from biodynamic.api.app import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/biodynamic/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_today():
    r = client.get("/api/v1/biodynamic/today?timezone=UTC")
    assert r.status_code == 200
    data = r.json()
    assert "day_type" in data
    assert data["day_type"] in {"fruit", "root", "flower", "leaf"}
    assert 0.0 <= data["moon_illumination"] <= 1.0


def test_day_endpoint():
    r = client.get("/api/v1/biodynamic/day/2026-06-15?timezone=UTC")
    assert r.status_code == 200
    data = r.json()
    assert data["date"] == "2026-06-15"


def test_range_endpoint():
    r = client.get("/api/v1/biodynamic/range?start=2026-06-01&end=2026-06-07&timezone=UTC")
    assert r.status_code == 200
    data = r.json()
    assert len(data["days"]) == 7
    assert "summary" in data


def test_range_too_long():
    r = client.get("/api/v1/biodynamic/range?start=2026-01-01&end=2027-03-01&timezone=UTC")
    assert r.status_code == 400


def test_next_fruit():
    r = client.get("/api/v1/biodynamic/next/fruit?timezone=UTC")
    assert r.status_code == 200
    data = r.json()
    assert data["day_type"] == "fruit"


def test_next_invalid_type():
    r = client.get("/api/v1/biodynamic/next/invalid?timezone=UTC")
    assert r.status_code == 400


def test_week():
    r = client.get("/api/v1/biodynamic/week?timezone=UTC")
    assert r.status_code == 200
    data = r.json()
    assert len(data["days"]) == 7


def test_invalid_timezone():
    r = client.get("/api/v1/biodynamic/today?timezone=Invalid/Zone")
    assert r.status_code == 400
