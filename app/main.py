"""Yawara Move local sandbox MVP. NOT production ride dispatch or payment processing."""
from __future__ import annotations
import hashlib
import math
import os
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from collections import defaultdict, deque
from threading import Lock
from fastapi import Request
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent
DB = Path(os.getenv('MOVE_DB', str(ROOT.parent / 'move_sandbox.sqlite3')))
DB.parent.mkdir(parents=True, exist_ok=True)
STORAGE_BACKEND = os.getenv('MOVE_STORAGE_BACKEND', 'sqlite').lower()
if STORAGE_BACKEND not in ('sqlite','postgres'):
    raise RuntimeError('MOVE_STORAGE_BACKEND must be sqlite or postgres')
if STORAGE_BACKEND == 'postgres' and not os.getenv('DATABASE_URL'):
    raise RuntimeError('Postgres selected without DATABASE_URL; refusing silent SQLite fallback')
if any(os.getenv(k, '').lower() in ('1','true','yes','on') for k in ('MOVE_REAL_DISPATCH','MOVE_PAYMENTS_ENABLED')):
    raise RuntimeError('Real operations are forbidden in the sandbox')

app = FastAPI(title='Yawara Move Demo Sandbox', version='1.4.0',
                  docs_url=None if os.getenv('MOVE_CLOUD_DEMO') else '/api/docs', redoc_url=None)

# Best-effort per-process throttling for demo public endpoints. This is not
# distributed protection; use a shared store/edge WAF before a real launch.
_limits = defaultdict(deque)
_limits_lock = Lock()
_LIMIT_SECONDS = 60
_LIMIT_BUCKETS = {
    '/api/register': (30, 60),
    '/api/quote': (45, 60),
    '/api/rides': (25, 60),
}

def should_throttle(client_key: str, bucket: str, limit: int, window: int = 60, now: float | None = None):
    now = time.monotonic() if now is None else now
    key = (client_key, bucket)
    with _limits_lock:
        # Cap memory use even when many distinct clients send requests.
        if key not in _limits and len(_limits) >= 5000:
            oldest = next(iter(_limits))
            _limits.pop(oldest, None)
        calls = _limits[key]
        while calls and calls[0] <= now - window:
            calls.popleft()
        if len(calls) >= limit:
            retry = max(1, math.ceil(window - (now - calls[0])))
            return retry
        calls.append(now)
        return 0


@app.middleware('http')
async def safety_headers(request: Request, call_next):
    if request.method == 'POST' and request.url.path.startswith('/api/'):
        path = request.url.path
        bucket = path if path in _LIMIT_BUCKETS else '/api/mutations'
        max_requests, seconds = _LIMIT_BUCKETS.get(bucket, (70, 60))
        # Ignore untrusted X-Forwarded-For, since clients can forge it.
        remote = request.client.host if request.client else 'unknown'
        retry = should_throttle(remote, bucket, max_requests, seconds)
        if retry:
            return JSONResponse(
                status_code=429,
                content={'detail': 'Muitas tentativas no simulador. Tente novamente em instantes.'},
                headers={'Retry-After': str(retry), 'Cache-Control': 'no-store',
                         'X-Content-Type-Options': 'nosniff'},
            )
    res = await call_next(request)
    res.headers['X-Content-Type-Options'] = 'nosniff'
    res.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
    res.headers['Referrer-Policy'] = 'no-referrer'
    res.headers['Cache-Control'] = 'no-store'
    res.headers['X-Frame-Options'] = 'DENY'
    res.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self' data:"
    return res

class PostgresCompat:
    """SQL compatibility for isolated ym_demo schema; never expose this role to browsers."""
    def __init__(self, conn):
        self.conn = conn
    def execute(self, query, params=()):
        stmt = query.strip()
        if stmt.upper() == 'BEGIN IMMEDIATE':
            stmt = 'BEGIN'
        if stmt.upper().startswith('SELECT * FROM RIDES WHERE ID=?'):
            stmt += ' FOR UPDATE'
        stmt = stmt.replace('?', '%s')
        return self.conn.execute(stmt, params)
    def commit(self):
        # Explicit transaction is opened by BEGIN IMMEDIATE -> BEGIN.
        self.conn.execute('COMMIT')
    def close(self):
        self.conn.close()

@contextmanager
def db():
    if STORAGE_BACKEND == 'postgres':
        # Dedicated server-side connection string. Credential is supplied through
        # Render secret env vars, never committed or returned by the API.
        from psycopg import connect
        from psycopg.rows import dict_row
        conn = PostgresCompat(connect(
            os.environ['DATABASE_URL'], autocommit=True, row_factory=dict_row,
            options='-c search_path=ym_demo', connect_timeout=5))
    else:
        conn = sqlite3.connect(DB, timeout=10, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA busy_timeout=10000')
        conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    if STORAGE_BACKEND == 'postgres':
        with db() as c:
            # Refuse to run against unrelated schemas or incomplete migrations.
            for table in ('accounts','drivers','rides','payments'):
                row = c.execute('SELECT to_regclass(%s) AS rel', (f'ym_demo.{table}',)).fetchone()
                if row['rel'] is None:
                    raise RuntimeError(f'Missing isolated sandbox table ym_demo.{table}')
        return
    with db() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS accounts (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('passenger','driver')),
          token_hash TEXT UNIQUE NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS drivers (
          account_id TEXT PRIMARY KEY REFERENCES accounts(id), online INTEGER NOT NULL DEFAULT 0,
          lat REAL, lon REAL, updated_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS rides (
          id TEXT PRIMARY KEY, passenger_id TEXT NOT NULL REFERENCES accounts(id), driver_id TEXT REFERENCES accounts(id),
          origin TEXT NOT NULL, destination TEXT NOT NULL, pickup_lat REAL NOT NULL, pickup_lon REAL NOT NULL,
          dest_lat REAL NOT NULL, dest_lon REAL NOT NULL, km REAL NOT NULL, fare_cents INTEGER NOT NULL,
          commission_cents INTEGER NOT NULL, status TEXT NOT NULL CHECK(status IN ('requested','accepted','in_progress','completed','cancelled')),
          created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS rides_status_idx ON rides(status);
        CREATE INDEX IF NOT EXISTS rides_driver_idx ON rides(driver_id, status);
        CREATE UNIQUE INDEX IF NOT EXISTS rides_driver_one_active_idx ON rides(driver_id)
          WHERE driver_id IS NOT NULL AND status IN ('accepted','in_progress');
        CREATE TABLE IF NOT EXISTS payments (
          id TEXT PRIMARY KEY, ride_id TEXT UNIQUE NOT NULL REFERENCES rides(id),
          amount_cents INTEGER NOT NULL, provider TEXT NOT NULL CHECK(provider='sandbox_emulator'),
          status TEXT NOT NULL CHECK(status='simulated_paid'), created_at INTEGER NOT NULL);
        ''')

init_db()

class Register(BaseModel):
    name: str = Field(min_length=2, max_length=70)
    role: Literal['passenger', 'driver']
    @field_validator('name')
    @classmethod
    def clean(cls, v):
        v = ' '.join(v.split())
        if len(v) < 2: raise ValueError('Nome muito curto')
        return v

class Point(BaseModel):
    label: str = Field(min_length=2, max_length=100)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class QuoteRequest(BaseModel):
    origin: Point
    destination: Point

class RideRequest(QuoteRequest):
    pass

class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    online: bool = True

def token_hash(token): return hashlib.sha256(token.encode()).hexdigest()

def actor(authorization: str | None, role: str | None = None):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Sessão não informada')
    token = authorization[7:]
    with db() as c:
        a = c.execute('SELECT id,name,role,created_at FROM accounts WHERE token_hash=?', (token_hash(token),)).fetchone()
    if not a: raise HTTPException(status_code=401, detail='Sessão inválida')
    if int(time.time()) - a['created_at'] > 24 * 3600:
        raise HTTPException(status_code=401, detail='Sessão de demonstração expirada; crie uma nova conta de teste')
    if role and a['role'] != role: raise HTTPException(status_code=403, detail='Permissão insuficiente')
    return {'id': a['id'], 'name': a['name'], 'role': a['role']}

def haversine(a,b,c,d):
    p1,p2 = math.radians(a), math.radians(c)
    dp,dl = p2-p1, math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371*2*math.asin(min(1,math.sqrt(x)))

def quote(q):
    air_km=haversine(q.origin.lat,q.origin.lon,q.destination.lat,q.destination.lon)
    if air_km < 0.15: raise HTTPException(422, 'Origem e destino precisam ser diferentes')
    if air_km > 100: raise HTTPException(422, 'Simulador limitado a deslocamentos de até 100 km em linha reta')
    # purely illustrative routing factor, not a route API
    km=round(air_km*1.30,2)
    cents=max(1000, round(650+km*215))
    commission=round(cents*.10)
    return {'distance_km_illustrative':km,'fare_cents':cents,'commission_cents':commission,
            'driver_gross_cents':cents-commission,'pricing':'simulated','navigation':'not_available'}

def serialize_ride(row):
    d=dict(row)
    d['payment_status']='not_paid' if d['status']!='completed' else 'eligible_for_simulated_payment'
    return d

@app.get('/api/health')
def health():
    return {'status':'ok','app':'yawara-move-sandbox','database':'postgres-isolated-demo' if STORAGE_BACKEND == 'postgres' else 'sqlite-development',
            'gateway_mode':'sandbox_emulator','payments_enabled':False,'external_maps_enabled':False,
            'real_dispatch_enabled':False,'demo_hosting':bool(os.getenv('MOVE_CLOUD_DEMO')),
            'identity_verification_enabled':False,'persistent_storage':STORAGE_BACKEND == 'postgres',
            'demo_access_ttl_hours':24,'distributed_rate_limit':False}

@app.get('/api/ready')
def readiness():
    try:
        with db() as c:
            c.execute('SELECT 1')
    except Exception:
        return JSONResponse({'status':'unavailable'}, status_code=503)
    return {'status':'ready', 'environment':'sandbox'}

@app.post('/api/logout')
def logout(authorization:str|None=Header(None)):
    a = actor(authorization)
    token = authorization[7:]
    with db() as c:
        # Rotating the hash immediately invalidates the old bearer token,
        # without breaking test ride records that reference the account.
        c.execute('UPDATE accounts SET token_hash=? WHERE id=? AND token_hash=?',
                  ('revoked:'+secrets.token_hex(24), a['id'], token_hash(token)))
    return {'status':'signed_out','environment':'sandbox'}

@app.post('/api/register', status_code=201)
def register(data:Register):
    new_token = secrets.token_urlsafe(32)
    uid=uuid.uuid4().hex
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('INSERT INTO accounts VALUES(?,?,?,?,?)',(uid,data.name,data.role,token_hash(new_token),int(time.time())))
        if data.role=='driver': c.execute('INSERT INTO drivers VALUES(?,?,?,?,?)',(uid,False,None,None,int(time.time())))
        c.commit()
    return {'account_id':uid,'name':data.name,'role':data.role,'token':new_token,'environment':'local_demo'}

@app.get('/api/me')
def me(authorization:str|None=Header(None)):
    return actor(authorization)

@app.post('/api/quote')
def get_quote(request:QuoteRequest):
    return quote(request)

@app.post('/api/driver/location')
def location(data:Location,authorization:str|None=Header(None)):
    a=actor(authorization,'driver')
    with db() as c:
        c.execute('UPDATE drivers SET online=?,lat=?,lon=?,updated_at=? WHERE account_id=?',
                  (data.online,data.lat,data.lon,int(time.time()),a['id']))
    return {'status':'updated','online':data.online}

@app.post('/api/rides', status_code=201)
def create_ride(data:RideRequest,authorization:str|None=Header(None)):
    a=actor(authorization,'passenger')
    q=quote(data)
    rid=uuid.uuid4().hex
    now=int(time.time())
    with db() as c:
        c.execute('INSERT INTO rides VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (rid,a['id'],None,data.origin.label,data.destination.label,
                   data.origin.lat,data.origin.lon,data.destination.lat,data.destination.lon,
                   q['distance_km_illustrative'],q['fare_cents'],q['commission_cents'],'requested',now,now))
    return {'ride_id':rid,'status':'requested','quote':q}

@app.get('/api/rides/mine')
def my_rides(authorization:str|None=Header(None)):
    a=actor(authorization)
    col='passenger_id' if a['role']=='passenger' else 'driver_id'
    with db() as c:
        rows=c.execute(f'SELECT * FROM rides WHERE {col}=? ORDER BY created_at DESC LIMIT 50',(a['id'],)).fetchall()
    return {'rides':[serialize_ride(r) for r in rows]}

@app.get('/api/rides/available')
def available(authorization:str|None=Header(None)):
    a=actor(authorization,'driver')
    with db() as c:
        driver=c.execute('SELECT * FROM drivers WHERE account_id=?',(a['id'],)).fetchone()
        if not driver['online'] or driver['lat'] is None:
            return {'rides':[],'notice':'Ative sua disponibilidade para receber ofertas simuladas.'}
        rows=c.execute("SELECT * FROM rides WHERE status='requested' ORDER BY created_at LIMIT 50").fetchall()
    offers=[]
    for r in rows:
        distance=haversine(driver['lat'],driver['lon'],r['pickup_lat'],r['pickup_lon'])
        if distance <= 30:
            offers.append({**serialize_ride(r),'pickup_distance_km_air':round(distance,2)})
    return {'rides':sorted(offers,key=lambda x:x['pickup_distance_km_air'])}

def transition(ride_id,authorization,role,expected,new):
    a=actor(authorization,role)
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        r=c.execute('SELECT * FROM rides WHERE id=?',(ride_id,)).fetchone()
        if not r: raise HTTPException(404,'Corrida não encontrada')
        owner=r['passenger_id'] if role=='passenger' else r['driver_id']
        if owner != a['id']: raise HTTPException(403,'Corrida não pertence a esta conta')
        if r['status'] != expected: raise HTTPException(409,'Transição de estado inválida')
        c.execute('UPDATE rides SET status=?, updated_at=? WHERE id=? AND status=?',
                  (new,int(time.time()),ride_id,expected))
        c.commit()
    return {'ride_id':ride_id,'status':new}

@app.post('/api/rides/{ride_id}/accept')
def accept(ride_id:str,authorization:str|None=Header(None)):
    a=actor(authorization,'driver')
    try:
        with db() as c:
            c.execute('BEGIN IMMEDIATE')
            d=c.execute('SELECT * FROM drivers WHERE account_id=?',(a['id'],)).fetchone()
            if not d or not d['online'] or d['lat'] is None: raise HTTPException(403,'Motorista indisponível')
            r=c.execute('SELECT * FROM rides WHERE id=?',(ride_id,)).fetchone()
            if not r:raise HTTPException(404,'Corrida não encontrada')
            if r['status']!='requested':raise HTTPException(409,'Corrida já aceita ou indisponível')
            if haversine(d['lat'],d['lon'],r['pickup_lat'],r['pickup_lon'])>30:
                raise HTTPException(403,'Fora da área demonstrativa')
            busy=c.execute("SELECT 1 FROM rides WHERE driver_id=? AND status IN ('accepted','in_progress')",(a['id'],)).fetchone()
            if busy:raise HTTPException(409,'Motorista já possui uma corrida ativa')
            try:
                count=c.execute("UPDATE rides SET driver_id=?,status='accepted',updated_at=? WHERE id=? AND status='requested'",
                                (a['id'],int(time.time()),ride_id)).rowcount
            except sqlite3.IntegrityError:
                raise HTTPException(409,'Motorista já possui uma corrida ativa') from None
            except Exception as ex:
                # psycopg is optional in local SQLite-only development.
                if STORAGE_BACKEND == 'postgres':
                    from psycopg.errors import UniqueViolation
                    if isinstance(ex, UniqueViolation):
                        raise HTTPException(409,'Motorista já possui uma corrida ativa') from None
                raise
            if count!=1:raise HTTPException(409,'Corrida já aceita')
            c.commit()
    except Exception as exc:
        # The database uniqueness constraint resolves concurrent accepts.
        # Convert expected contention into HTTP 409, not HTTP 500.
        postgres_conflict = (getattr(exc, 'sqlstate', None) == '23505'
                             and 'demo_driver_one_active_idx' in str(exc))
        sqlite_conflict = (isinstance(exc, sqlite3.IntegrityError)
                           and 'rides.driver_id' in str(exc))
        if postgres_conflict or sqlite_conflict:
            raise HTTPException(409, 'Motorista já possui uma corrida ativa') from None
        raise
    return {'ride_id':ride_id,'status':'accepted','driver_id':a['id']}

@app.post('/api/rides/{ride_id}/start')
def start(ride_id:str,authorization:str|None=Header(None)):
    return transition(ride_id,authorization,'driver','accepted','in_progress')

@app.post('/api/rides/{ride_id}/complete')
def complete(ride_id:str,authorization:str|None=Header(None)):
    return transition(ride_id,authorization,'driver','in_progress','completed')

@app.post('/api/rides/{ride_id}/cancel')
def cancel(ride_id:str,authorization:str|None=Header(None)):
    a=actor(authorization,'passenger')
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        r=c.execute('SELECT * FROM rides WHERE id=?',(ride_id,)).fetchone()
        if not r:raise HTTPException(404,'Corrida não encontrada')
        if r['passenger_id']!=a['id']:raise HTTPException(403,'Sem permissão')
        if r['status'] not in ('requested','accepted'):raise HTTPException(409,'Não pode cancelar neste estágio')
        c.execute("UPDATE rides SET status='cancelled',updated_at=? WHERE id=?",(int(time.time()),ride_id))
        c.commit()
    return {'ride_id':ride_id,'status':'cancelled'}

@app.post('/api/rides/{ride_id}/simulate-payment')
def payment(ride_id:str,authorization:str|None=Header(None)):
    a=actor(authorization,'passenger')
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        r=c.execute('SELECT * FROM rides WHERE id=?',(ride_id,)).fetchone()
        if not r:raise HTTPException(404,'Corrida não encontrada')
        if r['passenger_id'] != a['id']:raise HTTPException(403,'Sem permissão')
        if r['status']!='completed':raise HTTPException(409,'Viagem ainda não concluída')
        existing=c.execute('SELECT * FROM payments WHERE ride_id=?',(ride_id,)).fetchone()
        if existing:
            return {'status':'simulated_paid','payment_id':existing['id'],'idempotent':True,'mode':'sandbox_emulator'}
        payid=uuid.uuid4().hex
        c.execute('INSERT INTO payments VALUES(?,?,?,?,?,?)',(payid,ride_id,r['fare_cents'],'sandbox_emulator','simulated_paid',int(time.time())))
        c.commit()
    return {'status':'simulated_paid','payment_id':payid,'idempotent':False,'mode':'sandbox_emulator'}

@app.get('/api/summary')
def summary(authorization:str|None=Header(None)):
    a=actor(authorization)
    with db() as c:
        if a['role']=='passenger':
            records=c.execute('SELECT status,COUNT(*) AS n FROM rides WHERE passenger_id=? GROUP BY status',(a['id'],)).fetchall()
        else:
            records=c.execute('SELECT status,COUNT(*) AS n FROM rides WHERE driver_id=? GROUP BY status',(a['id'],)).fetchall()
        paid=c.execute('''SELECT COALESCE(SUM(p.amount_cents),0) AS gross,
                          COALESCE(SUM(r.commission_cents),0) AS commission
                          FROM payments p JOIN rides r ON r.id=p.ride_id
                          WHERE '''+('r.passenger_id=?' if a['role']=='passenger' else 'r.driver_id=?'),(a['id'],)).fetchone()
    return {'rides_by_status':{r['status']:r['n'] for r in records},'simulated_paid_cents':paid['gross'],
            'simulated_commission_cents':paid['commission'],'environment':'local_sandbox'}

@app.get('/')
def home():return FileResponse(ROOT/'static'/'index.html')

app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')