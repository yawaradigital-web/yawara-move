"""S9: security and demo reliability regression checks."""
from fastapi.testclient import TestClient
import pytest
from app.main import app, validate_pg_url

def test_remote_postgres_requires_tls():
    with pytest.raises(RuntimeError,match="TLS required"):
        validate_pg_url("postgresql://demo:secret@pooler.invalid:5432/postgres?sslmode=disable")
    with pytest.raises(RuntimeError,match="TLS required"):
        validate_pg_url("postgresql://demo:secret@pooler.invalid:5432/postgres")
    validate_pg_url("postgresql://demo:secret@pooler.invalid:5432/postgres?sslmode=require")
    validate_pg_url("postgresql://demo:secret@pooler.invalid:5432/postgres?sslmode=verify-full")

def test_disposable_ci_localhost_can_use_insecure_postgres():
    validate_pg_url("postgresql://postgres:local@localhost:5432/postgres?sslmode=disable")
    validate_pg_url("postgresql://postgres:local@127.0.0.1:5432/postgres")

def test_invalid_postgres_url_fail_closed():
    for url in ("not-a-uri", "http://example.com/postgres", "postgresql://"):
        with pytest.raises(RuntimeError,match="Invalid PostgreSQL"):
            validate_pg_url(url)

def test_root_head_returns_200_and_readiness():
    with TestClient(app) as c:
        result=c.head("/")
        assert result.status_code==200
        assert result.headers.get("x-content-type-options")=="nosniff"
        assert c.get("/api/ready").status_code==200

def test_sandbox_remains_fictional():
    with TestClient(app) as c:
        data=c.get("/api/health").json()
        assert data["payments_enabled"] is False
        assert data["real_dispatch_enabled"] is False
