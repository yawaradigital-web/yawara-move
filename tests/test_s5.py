import os
import time
from app.main import should_throttle, db, app
from fastapi.testclient import TestClient

def test_window_rate_limit_and_reset():
    key = 's5-test-isolated-client'
    assert should_throttle(key, 'register', 2, 60, now=1000) == 0
    assert should_throttle(key, 'register', 2, 60, now=1001) == 0
    assert should_throttle(key, 'register', 2, 60, now=1002) == 58
    assert should_throttle(key, 'register', 2, 60, now=1062) == 0

def test_expired_demo_token_is_rejected():
    with TestClient(app) as client:
        account = client.post('/api/register', json={'name':'Conta Ficcao', 'role':'passenger'})
        assert account.status_code == 201
        token = account.json()['token']
        import hashlib
        hashed = hashlib.sha256(token.encode()).hexdigest()
        with db() as conn:
            conn.execute('UPDATE accounts SET created_at=? WHERE token_hash=?',(int(time.time())-86410, hashed))
        response = client.get('/api/me',headers={'Authorization':'Bearer '+token})
        assert response.status_code == 401
        assert 'expirada' in response.json()['detail']

def test_demo_remains_noncommercial():
    with TestClient(app) as client:
        h=client.get('/api/health')
        assert h.status_code==200
        fields=h.json()
        for field in ('payments_enabled','real_dispatch_enabled','external_maps_enabled','identity_verification_enabled','persistent_storage','distributed_rate_limit'):
            assert fields[field] is False
        assert fields['demo_access_ttl_hours']==24