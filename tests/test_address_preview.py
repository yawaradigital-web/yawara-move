"""S20 - optional provider search stays off without a secret and remains info-only."""
import json
from fastapi.testclient import TestClient
from app.main import app
from app import address_search

class FakeResponse:
    def __init__(self, payload):
        self.data=json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self,*exc): return False
    def read(self, amount): return self.data

def test_provider_disabled_by_default(monkeypatch):
    monkeypatch.delenv('MOVE_GEOAPIFY_API_KEY',raising=False)
    with TestClient(app) as c:
        status=c.get('/api/address-preview/status')
        assert status.status_code==200
        assert status.json()=={'enabled':False,'mode':'preview_only','can_request_ride':False,'can_calculate_fare':False}
        request=c.post('/api/address-preview',json={'text':'Avenida Paulista'})
        assert request.status_code==503
        assert 'demo' in request.text.lower()
        assert c.get('/explore').status_code==200
        assert '/static/address-preview.js' in c.get('/explore').text

def test_brazil_filter_and_secret_never_returned(monkeypatch):
    monkeypatch.setenv('MOVE_GEOAPIFY_API_KEY','secret-for-ci-do-not-print')
    def fake_open(request,timeout):
        assert request.full_url.startswith('https://api.geoapify.com/v1/geocode/autocomplete?')
        assert 'countrycode%3Abr' in request.full_url
        assert timeout==5
        return FakeResponse({'results':[
          {'country_code':'br','formatted':'Avenida Paulista, Sao Paulo','lat':-23.561,'lon':-46.656},
          {'country_code':'us','formatted':'Other place','lat':40.1,'lon':-73.3},
          {'country_code':'br','formatted':'Invalid location','lat':120,'lon':0},
        ]})
    monkeypatch.setattr(address_search,'urlopen',fake_open)
    with TestClient(app) as c:
        result=c.post('/api/address-preview',json={'text':'Avenida Paulista'})
        assert result.status_code==200,result.text
        payload=result.json()
        assert payload['mode']=='preview_only'
        assert payload['can_request_ride'] is False
        assert payload['can_calculate_fare'] is False
        assert len(payload['results'])==1
        assert payload['results'][0]['label']=='Avenida Paulista, Sao Paulo'
        assert 'secret-for-ci-do-not-print' not in result.text
        assert 'apiKey' not in result.text

def test_provider_unavailable_fails_closed(monkeypatch):
    monkeypatch.setenv('MOVE_GEOAPIFY_API_KEY','dummy-ci-only')
    def fail(request,timeout): raise OSError('private connection failed')
    monkeypatch.setattr(address_search,'urlopen',fail)
    with TestClient(app) as c:
        response=c.post('/api/address-preview',json={'text':'Avenida Paulista'})
        assert response.status_code==503
        assert 'dummy-ci-only' not in response.text
        assert 'private connection failed' not in response.text
