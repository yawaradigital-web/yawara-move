"""Road route adapter safeguards: no arbitrary GPS, limited remote calls and no payment integration."""
import json
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import demo_routes

class FakeResponse:
    def __init__(self, payload): self.payload=payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size): return json.dumps(self.payload).encode()

def sample_response():
    return {"code":"Ok","routes":[{"distance":4870,"duration":910,"geometry":{
        "coordinates":[[-46.6559,-23.5614],[-46.6576,-23.5874]]}}]}

def test_demo_route_strict_input_validation():
    with TestClient(app) as c:
        for a,b in [(-1,0),(0,6),(1,1),(900,0)]:
            response=c.get(f"/api/demo-route?origin={a}&destination={b}")
            assert response.status_code==422
        assert c.get("/api/demo-route?origin=https://bad.invalid&destination=1").status_code==422
        assert c.get("/api/health").json()["real_dispatch_enabled"] is False

def test_demo_route_cached_and_filtered(monkeypatch):
    calls=[]
    def fake_open(req, timeout):
        calls.append(req.full_url)
        assert req.full_url.startswith("https://router.project-osrm.org/route/v1/driving/")
        return FakeResponse(sample_response())
    monkeypatch.setattr(demo_routes,"urlopen",fake_open)
    demo_routes._cache.clear()
    demo_routes._last_upstream=0
    with TestClient(app) as c:
        first=c.get("/api/demo-route?origin=0&destination=1")
        assert first.status_code==200,first.text
        body=first.json()
        assert body["status"]=="demo" and body["commercial_dispatch"] is False
        assert body["distance_km"]==4.87
        assert body["cached"] is False
        second=c.get("/api/demo-route?origin=0&destination=1")
        assert second.status_code==200
        assert second.json()["cached"] is True
        assert len(calls)==1
        limited=c.get("/api/demo-route?origin=1&destination=0")
        assert limited.status_code==429
    demo_routes._cache.clear()
    demo_routes._last_upstream=0

def test_remote_failure_does_not_invent_route(monkeypatch):
    def broken(req, timeout): raise OSError("offline")
    monkeypatch.setattr(demo_routes,"urlopen",broken)
    demo_routes._cache.clear()
    demo_routes._last_upstream=0
    with TestClient(app) as c:
        r=c.get("/api/demo-route?origin=0&destination=2")
        assert r.status_code==503
        assert "coordinates" not in r.text
    demo_routes._cache.clear()
    demo_routes._last_upstream=0
