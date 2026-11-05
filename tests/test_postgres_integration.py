"""S8 integration against disposable PostgreSQL. Never uses live Supabase secrets."""
import os
from pathlib import Path
import pytest
URL = os.environ.get("MOVE_CI_POSTGRES_URL")
if not URL:
    pytest.skip("PostgreSQL test needs disposable CI DB", allow_module_level=True)
import psycopg
from fastapi.testclient import TestClient
root=Path(__file__).resolve().parents[1]
with psycopg.connect(URL,autocommit=True) as conn:
    conn.execute("CREATE ROLE anon NOLOGIN")
    conn.execute("CREATE ROLE authenticated NOLOGIN")
    conn.execute((root/"migrations/20261105_s6_ym_demo.sql").read_text())
    conn.execute((root/"migrations/s7_one_active_driver.sql").read_text())
os.environ["MOVE_STORAGE_BACKEND"]="postgres"
os.environ["DATABASE_URL"]=URL
os.environ["MOVE_CLOUD_DEMO"]="1"
from app.main import app
A={"label":"Avenida Paulista","lat":-23.5614,"lon":-46.6559}
B={"label":"Parque Ibirapuera","lat":-23.5874,"lon":-46.6576}
def register(c,role):
    r=c.post("/api/register",json={"name":"Ficticio "+role,"role":role})
    assert r.status_code==201,r.text
    return {"Authorization":"Bearer "+r.json()["token"]}
def test_postgres_full_sandbox_lifecycle_and_persistence():
    with TestClient(app) as c:
        health=c.get("/api/health").json()
        assert health["persistent_storage"] is True
        assert health["payments_enabled"] is False
        assert health["real_dispatch_enabled"] is False
        assert c.get("/api/ready").status_code==200
        p=register(c,"passenger")
        d=register(c,"driver")
        online=c.post("/api/driver/location",headers=d,json={"lat":A["lat"],"lon":A["lon"],"online":True})
        assert online.status_code==200,online.text
        ride1=c.post("/api/rides",headers=p,json={"origin":A,"destination":B})
        ride2=c.post("/api/rides",headers=p,json={"origin":A,"destination":B})
        assert ride1.status_code==201 and ride2.status_code==201,(ride1.text,ride2.text)
        id1,id2=ride1.json()["ride_id"],ride2.json()["ride_id"]
        assert ride1.json()["quote"]["commission_cents"]==round(ride1.json()["quote"]["fare_cents"]*.10)
        accepted=c.post("/api/rides/"+id1+"/accept",headers=d)
        assert accepted.status_code==200,accepted.text
        collision=c.post("/api/rides/"+id2+"/accept",headers=d)
        assert collision.status_code==409,collision.text
        assert c.post("/api/rides/"+id1+"/start",headers=d).status_code==200
        assert c.post("/api/rides/"+id1+"/complete",headers=d).status_code==200
        pay=c.post("/api/rides/"+id1+"/simulate-payment",headers=p)
        assert pay.status_code==200,pay.text
        assert pay.json()["mode"]=="sandbox_emulator"
        repeat=c.post("/api/rides/"+id1+"/simulate-payment",headers=p)
        assert repeat.status_code==200 and repeat.json()["idempotent"] is True
        assert c.get("/api/summary",headers=p).status_code==200
    with TestClient(app) as next_c:
        rides=next_c.get("/api/rides/mine",headers=p)
        assert rides.status_code==200,rides.text
        assert any(r["id"]==id1 and r["status"]=="completed" for r in rides.json()["rides"])
        assert next_c.post("/api/logout",headers=p).status_code==200
        assert next_c.get("/api/me",headers=p).status_code==401
