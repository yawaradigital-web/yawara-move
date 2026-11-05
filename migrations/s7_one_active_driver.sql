-- Safe, repeatable addition for the isolated Yawara Move demo schema.
-- Verified on Supabase Yawara Move on 2026-11-05.
CREATE UNIQUE INDEX IF NOT EXISTS demo_driver_one_active_idx
    ON ym_demo.rides (driver_id)
    WHERE driver_id IS NOT NULL AND status IN ('accepted','in_progress');