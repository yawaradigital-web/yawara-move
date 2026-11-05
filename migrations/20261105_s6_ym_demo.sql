-- Yawara Move S6. Already applied to Supabase project Yawara Move on 2026-11-05.
-- Non-public, isolated fictional-data schema. Keep all four demo tables RLS-enabled;
-- grants to anon/authenticated/PUBLIC are intentionally denied.
CREATE SCHEMA IF NOT EXISTS ym_demo;
REVOKE ALL ON SCHEMA ym_demo FROM PUBLIC, anon, authenticated;
CREATE TABLE IF NOT EXISTS ym_demo.accounts (
 id text PRIMARY KEY, name text NOT NULL CHECK(length(name) BETWEEN 2 AND 70),
 role text NOT NULL CHECK(role IN ('passenger','driver')),
 token_hash text NOT NULL UNIQUE, created_at bigint NOT NULL
);
CREATE TABLE IF NOT EXISTS ym_demo.drivers (
 account_id text PRIMARY KEY REFERENCES ym_demo.accounts(id),
 online boolean NOT NULL DEFAULT false, lat double precision, lon double precision,
 updated_at bigint NOT NULL,
 CONSTRAINT demo_lat_bounds CHECK (lat BETWEEN -90 AND 90 OR lat IS NULL),
 CONSTRAINT demo_lon_bounds CHECK (lon BETWEEN -180 AND 180 OR lon IS NULL)
);
CREATE TABLE IF NOT EXISTS ym_demo.rides (
 id text PRIMARY KEY, passenger_id text NOT NULL REFERENCES ym_demo.accounts(id),
 driver_id text REFERENCES ym_demo.accounts(id), origin text NOT NULL, destination text NOT NULL,
 pickup_lat double precision NOT NULL, pickup_lon double precision NOT NULL,
 dest_lat double precision NOT NULL, dest_lon double precision NOT NULL,
 km double precision NOT NULL CHECK(km >= 0), fare_cents bigint NOT NULL CHECK(fare_cents >= 0),
 commission_cents bigint NOT NULL CHECK(commission_cents >= 0 AND commission_cents <= fare_cents),
 status text NOT NULL CHECK(status IN ('requested','accepted','in_progress','completed','cancelled')),
 created_at bigint NOT NULL, updated_at bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS demo_rides_status_idx ON ym_demo.rides(status);
CREATE INDEX IF NOT EXISTS demo_rides_passenger_idx ON ym_demo.rides(passenger_id,created_at DESC);
CREATE INDEX IF NOT EXISTS demo_rides_driver_idx ON ym_demo.rides(driver_id,status);
CREATE TABLE IF NOT EXISTS ym_demo.payments (
 id text PRIMARY KEY, ride_id text NOT NULL UNIQUE REFERENCES ym_demo.rides(id),
 amount_cents bigint NOT NULL CHECK(amount_cents >= 0),
 provider text NOT NULL CHECK(provider='sandbox_emulator'),
 status text NOT NULL CHECK(status='simulated_paid'), created_at bigint NOT NULL
);
ALTER TABLE ym_demo.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ym_demo.drivers ENABLE ROW LEVEL SECURITY;
ALTER TABLE ym_demo.rides ENABLE ROW LEVEL SECURITY;
ALTER TABLE ym_demo.payments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA ym_demo FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA ym_demo REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;
COMMENT ON SCHEMA ym_demo IS 'Isolated fictional ride sandbox. No real passengers, drivers, or payments.';