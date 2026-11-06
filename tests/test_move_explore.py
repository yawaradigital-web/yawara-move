"""Preview S10-S17: service discovery must remain noncommercial."""
from fastapi.testclient import TestClient
from app.main import app

A={"label":"Avenida Paulista","lat":-23.5614,"lon":-46.6559}
B={"label":"Parque Ibirapuera","lat":-23.5874,"lon":-46.6576}

def test_move_explore_is_accessible_without_account():
    with TestClient(app) as client:
        response=client.get("/explore")
        assert response.status_code==200
        assert 'lang="pt-BR"' in response.text
        assert 'MOVE Explore' in response.text
        assert 'Nenhuma' not in response.text or 'reais' in response.text
        assert 'data-tab="entregas"' in response.text
        assert 'data-tab="business"' in response.text
        assert 'src="/static/explore.js"' in response.text
        assert client.get("/static/explore.js").status_code==200
        assert client.get("/static/explore.css").status_code==200

def test_quote_remains_simulated_and_commission_fixed():
    with TestClient(app) as client:
        r=client.post("/api/quote",json={"origin":A,"destination":B})
        assert r.status_code==200,r.text
        result=r.json()
        assert result["pricing"]=="simulated"
        assert result["navigation"]=="not_available"
        assert result["commission_cents"]==round(result["fare_cents"]*0.10)
        health=client.get("/api/health").json()
        assert health["payments_enabled"] is False
        assert health["external_maps_enabled"] is False
        assert health["real_dispatch_enabled"] is False

def test_sandbox_home_kept_and_get_not_mutative():
    with TestClient(app) as client:
        r=client.get("/")
        assert r.status_code==200
        assert "MOVE Explore" in r.text
        assert client.head("/").status_code==200
