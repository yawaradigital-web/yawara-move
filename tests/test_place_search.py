"""MOVE Explore local searchable demo places and safety regressions."""
from fastapi.testclient import TestClient
from app.main import app

def test_local_place_search_assets_and_documentation():
    with TestClient(app) as c:
        page=c.get('/explore')
        assert page.status_code==200
        assert '/static/place-search.js' in page.text
        search=c.get('/static/place-search.js')
        assert search.status_code==200
        script=search.text
        assert 'initMovePlaceSearch' in script
        assert "origin" in script and "destination" in script
        assert "aria-expanded" in script and "role','combobox'" in script
        assert "ArrowDown" in script and "ArrowUp" in script
        assert "normalize('NFD')" in script
        assert 'fetch(' not in script
        assert 'geolocation' not in script

def test_existing_quote_and_routing_remain_illustrative():
    a={'label':'Avenida Paulista','lat':-23.5614,'lon':-46.6559}
    b={'label':'Parque Ibirapuera','lat':-23.5874,'lon':-46.6576}
    with TestClient(app) as c:
        q=c.post('/api/quote',json={'origin':a,'destination':b})
        assert q.status_code==200
        assert q.json()['pricing']=='simulated'
        assert q.json()['commission_cents']==round(q.json()['fare_cents']*.10)
        status=c.get('/api/health').json()
        assert status['real_dispatch_enabled'] is False
        assert status['payments_enabled'] is False
