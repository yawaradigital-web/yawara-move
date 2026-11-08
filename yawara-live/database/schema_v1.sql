-- Yawara Live / LiveX1 — database v1
-- Run ONLY in a dedicated Yawara Live Supabase project.
-- Public browsers may read active match state, but can never submit verified TikTok events.
create extension if not exists pgcrypto;
create table if not exists public.yl_clubs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 2 and 80),
  created_at timestamptz not null default now()
);
create table if not exists public.yl_matches (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  club_a_id uuid not null references public.yl_clubs(id),
  club_b_id uuid not null references public.yl_clubs(id),
  mode text not null check(mode in ('presidente','diretor','tecnico','lider','vice','solo','equipes')),
  status text not null default 'draft' check(status in ('draft','live','paused','finished')),
  slots_per_team integer not null default 1 check(slots_per_team between 1 and 11),
  share_public boolean not null default false,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now(),
  check(club_a_id <> club_b_id)
);
create table if not exists public.yl_participants (
  id uuid primary key default gen_random_uuid(),
  match_id uuid not null references public.yl_matches(id) on delete cascade,
  club_id uuid not null references public.yl_clubs(id),
  platform_user_key text not null check(char_length(platform_user_key) between 1 and 120),
  display_name text not null check(char_length(display_name) between 1 and 120),
  gift_points bigint not null default 0 check(gift_points>=0),
  fan_points bigint not null default 0 check(fan_points>=0),
  gift_reached_at timestamptz,
  fan_reached_at timestamptz,
  created_at timestamptz not null default now(),
  unique(match_id,platform_user_key)
);
create table if not exists public.yl_events (
  id uuid primary key default gen_random_uuid(),
  match_id uuid not null references public.yl_matches(id) on delete cascade,
  participant_id uuid not null references public.yl_participants(id) on delete cascade,
  source_event_id text not null check(char_length(source_event_id) between 1 and 180),
  event_type text not null check(event_type in ('gift','like','share','follow','heart_me','super_fan','game_mission')),
  units integer not null default 1 check(units between 1 and 100000),
  points bigint not null check(points>=0),
  verified boolean not null default false,
  happened_at timestamptz not null default now(),
  unique(match_id,source_event_id)
);
create table if not exists public.yl_gift_rules (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  platform_gift_key text not null,
  display_name text not null,
  points_per_unit integer not null check(points_per_unit between 1 and 1000000),
  enabled boolean not null default true,
  unique(owner_id,platform_gift_key)
);
create index if not exists yl_matches_owner_idx on public.yl_matches(owner_id,created_at desc);
create index if not exists yl_participants_ranking_idx on public.yl_participants(match_id,club_id,gift_points desc,fan_points desc);
create index if not exists yl_events_match_idx on public.yl_events(match_id,happened_at desc);
alter table public.yl_clubs enable row level security;
alter table public.yl_matches enable row level security;
alter table public.yl_participants enable row level security;
alter table public.yl_events enable row level security;
alter table public.yl_gift_rules enable row level security;

-- Owners can manage their clubs and matches. Public spectating is read-only and opt-in.
create policy yl_clubs_owner_select on public.yl_clubs for select to authenticated using (owner_id=(select auth.uid()));
create policy yl_clubs_owner_insert on public.yl_clubs for insert to authenticated with check(owner_id=(select auth.uid()));
create policy yl_clubs_owner_update on public.yl_clubs for update to authenticated using(owner_id=(select auth.uid())) with check(owner_id=(select auth.uid()));
create policy yl_matches_owner_select on public.yl_matches for select to authenticated using(owner_id=(select auth.uid()));
create policy yl_matches_owner_insert on public.yl_matches for insert to authenticated with check(owner_id=(select auth.uid()) and exists(select 1 from public.yl_clubs a join public.yl_clubs b on b.id=club_b_id where a.id=club_a_id and a.owner_id=(select auth.uid()) and b.owner_id=(select auth.uid())));
create policy yl_matches_owner_update on public.yl_matches for update to authenticated using(owner_id=(select auth.uid())) with check(owner_id=(select auth.uid()) and exists(select 1 from public.yl_clubs a join public.yl_clubs b on b.id=club_b_id where a.id=club_a_id and a.owner_id=(select auth.uid()) and b.owner_id=(select auth.uid())));
create policy yl_matches_public_read on public.yl_matches for select to anon using(share_public=true);
create policy yl_participants_owner_read on public.yl_participants for select to authenticated using(exists(select 1 from public.yl_matches m where m.id=match_id and m.owner_id=(select auth.uid())));
create policy yl_participants_public_read on public.yl_participants for select to anon using(exists(select 1 from public.yl_matches m where m.id=match_id and m.share_public=true));
create policy yl_events_owner_read on public.yl_events for select to authenticated using(exists(select 1 from public.yl_matches m where m.id=match_id and m.owner_id=(select auth.uid())));
create policy yl_gift_rules_owner_all on public.yl_gift_rules for all to authenticated using(owner_id=(select auth.uid())) with check(owner_id=(select auth.uid()));

-- Security: no anonymous or authenticated INSERT/UPDATE on participants/events.
-- Verified events must be written by a separately authenticated backend service.
-- Before production, enforce cross-table match/club/participant consistency in the ingest service,
-- enforce event deduplication, and use a non-exposed secret key server-side only.
