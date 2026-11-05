"""S7: simulated ride integrity, persistence and safety regressions."""
import os
import sqlite3
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient
from app.main import app, DB

POINT_A={'label':'Avenida Paulista','lat':-23.5614,'lon':-46.6559}
POINT_B={'label':'Parque Ibirapuera','lat':-23.5874,'lon':-46.6576}


def make_account(c, role):
    r=c.post('/api/register',json={'name':'Conta Ficticia','role':role})
    assert r.status_code==201, r.text
    return {'Authorization':'Bearer '+r.json()['token']}


def test_one_driver_one_active_ride_and_fixed_commission():
    with TestClient(app) as c:
        passenger=make_account(c,'passenger')
        driver=make_account(c,'driver')
        q=c.post('/api/quote',json={'origin':POINT_A,'destination':POINT_B})
        assert q.status_code==200
        data=q.json()
        assert data['pricing']=='simulated'
        assert data['commission_cents']==round(data['fare_cents']*.10)
        for _ in range(2):
            r=c.post('/api/rides',headers=passenger,json={'origin':POINT_A,'destination':POINT_B})
            assert r.status_code==201,r.text
        rides=c.get('/api/rides/mine',headers=passenger).json()['rides']
        ids=[r['id'] for r in rides[:2]]
        assert c.post('/api/driver/location',headers=driver,json={'lat':POINT_A['lat'],'lon':POINT_A['lon'],'online':True}).status_code==200
        assert c.post(f'/api/rides/{ids[0]}/accept',headers=driver).status_code==200
        second=c.post(f'/api/rides/{ids[1]}/accept',headers=driver)
        assert second.status_code==409,second.text
        with sqlite3.connect(DB) as db:
            assert db.execute("SELECT count(*) FROM rides WHERE status IN ('accepted','in_progress') AND driver_id IS NOT NULL").fetchone()[0]>=1
            first=db.execute("SELECT driver_id FROM rides WHERE id=?",(ids[0],)).fetchone()[0]
            with pytest.raises(sqlite3.IntegrityError):
                db.execute("UPDATE rides SET driver_id=?,status='accepted' WHERE id=?",(first,ids[1]))


def test_sqlite_state_survives_fresh_process():
    with TestClient(app) as c:
        auth=make_account(c,'passenger')
        mine=c.get('/api/me',headers=auth)
        assert mine.status_code==200
        uid=mine.json()['id']
    script='import sqlite3,os; c=sqlite3.connect(os.environ["MOVE_DB"]); print(c.execute("SELECT count(*) FROM accounts WHERE id=?",(os.environ["CHECK_UID"],)).fetchone()[0])'
    env=os.environ.copy()
    env['MOVE_DB']=str(DB)
    env['CHECK_UID']=uid
    r=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,text=True,timeout=10)
    assert r.returncode==0,r.stderr
    assert r.stdout.strip()=='1'


def test_sandbox_cannot_charge_real_payments():
    with TestClient(app) as c:
        state=c.get('/api/health').json()
    assert state['payments_enabled'] is False
    assert state['real_dispatch_enabled'] is False
    assert state['persistent_storage'] is False