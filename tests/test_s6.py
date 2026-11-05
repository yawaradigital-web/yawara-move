import os
from fastapi.testclient import TestClient
from app.main import app, PostgresCompat


def test_readiness_and_logout():
    with TestClient(app) as c:
        ready=c.get('/api/ready')
        assert ready.status_code==200
        data=c.post('/api/register',json={'name':'Pessoa de Teste','role':'passenger'})
        assert data.status_code==201
        token=data.json()['token']
        auth={'Authorization':'Bearer '+token}
        assert c.get('/api/me',headers=auth).status_code==200
        assert c.post('/api/logout',headers=auth).status_code==200
        assert c.get('/api/me',headers=auth).status_code==401


def test_postgres_sql_compat_adapter():
    class FakeCursor:
        rowcount=1
    class FakeConnection:
        def __init__(self):self.calls=[]
        def execute(self,statement,params=()):
            self.calls.append((statement,params))
            return FakeCursor()
        def commit(self):pass
        def close(self):pass
    fc=FakeConnection()
    pc=PostgresCompat(fc)
    pc.execute('BEGIN IMMEDIATE')
    pc.execute('SELECT * FROM rides WHERE id=?',('testid',))
    pc.commit()
    assert fc.calls == [('BEGIN',()),('SELECT * FROM rides WHERE id=%s FOR UPDATE',('testid',)),('COMMIT',())]


def test_demo_stays_noncommercial():
    with TestClient(app) as c:
        d=c.get('/api/health').json()
    assert d['payments_enabled'] is False
    assert d['real_dispatch_enabled'] is False
    assert d['external_maps_enabled'] is False


def test_refuses_postgres_without_secret():
    import subprocess,sys
    env=os.environ.copy()
    env.pop('DATABASE_URL',None)
    env['MOVE_STORAGE_BACKEND']='postgres'
    proc=subprocess.run([sys.executable,'-c','import app.main'],env=env,capture_output=True,text=True)
    assert proc.returncode != 0
    assert 'without DATABASE_URL' in proc.stderr

def test_refuses_real_payment_flag():
    import subprocess,sys
    env=os.environ.copy()
    env['MOVE_STORAGE_BACKEND']='sqlite'
    env['MOVE_PAYMENTS_ENABLED']='true'
    proc=subprocess.run([sys.executable,'-c','import app.main'],env=env,capture_output=True,text=True)
    assert proc.returncode != 0
    assert 'forbidden in the sandbox' in proc.stderr