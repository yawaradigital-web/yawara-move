"""S18: map remains opt-in and does not turn a demo into dispatch."""
from fastapi.testclient import TestClient
from app.main import app

def test_map_script_and_marker_interface():
    with TestClient(app) as c:
        page=c.get('/explore')
        assert page.status_code==200
        assert 'id="loadMap"' in page.text
        assert 'id="realMap"' in page.text
        assert '/static/map-explore.js' in page.text
        assert 'openstreetmap.org' in page.text
        script=c.get('/static/map-explore.js')
        assert script.status_code==200
        assert 'tile.openstreetmap.org' in script.text
        assert "button.addEventListener('click'" in script.text
        assert 'L.tileLayer' in script.text

def test_csp_limits_map_domains_and_noncommercial_sandbox():
    with TestClient(app) as c:
        r=c.get('/explore')
        policy=r.headers['content-security-policy']
        assert 'https://tile.openstreetmap.org' in policy
        assert 'https://unpkg.com' in policy
        assert "object-src 'none'" in policy
        status=c.get('/api/health').json()
        assert status['payments_enabled'] is False
        assert status['real_dispatch_enabled'] is False
        assert status['external_maps_enabled'] is False
