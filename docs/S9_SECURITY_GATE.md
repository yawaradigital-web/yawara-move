# Yawara Move — Sprint S9: security and readiness gate

## Implemented
- Explicit TLS `sslmode=require` (or stronger) for every **remote** PostgreSQL connection URL; the disposable localhost CI database remains exempt.
- Explicit HEAD / status 200 for Render load/health probes.
- Frontend clears expired or invalid demo session tokens upon HTTP 401 and invites the user to create a new fictitious profile.
- All monetary transactions and ride dispatch remain sandbox-only.

## Automated quality gates
- Existing SQLite regression suite.
- Disposable PostgreSQL lifecycle integration in GitHub Actions.
- New S9 startup, TLS, HEAD and sandbox safety tests.

## Deployment boundary
The public Render application deliberately remains on disposable SQLite until the exact project **Session Pooler** URL and a least-privileged credential are stored directly in Render's encrypted environment variables and tested against Supabase from Render. **Never paste secrets in GitHub, a chat message, or frontend code.**

## One-time external configuration
Open Supabase project Yawara Move > Connect > Session pooler to copy the exact IPv4-compatible connection string. Choose TLS and use a restricted account with permissions only for the `ym_demo` schema. Store `DATABASE_URL` in Render's private environment, test on an isolated staging service, then set `MOVE_STORAGE_BACKEND=postgres` only after validating /api/ready, demo write/read, restart persistence and rollback. The public app must not switch to Postgres until all four tests pass.

Until then, the app remains a demonstration, never an actual transport or payment service.
