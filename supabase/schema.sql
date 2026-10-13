-- Run once in the Supabase SQL Editor. Only a publishable key belongs in clients.
create table if not exists public.cards (
  id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('word', 'sentence')),
  word text not null default '',
  meaning text not null default '',
  sentence text not null default '',
  translation text not null default '',
  structure text not null default '',
  source text not null default '',
  tags text not null default '',
  status text not null default '待复习' check (status in ('待复习', '学习中', '已掌握')),
  deleted boolean not null default false,
  revision bigint not null default 1 check (revision > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((kind = 'word' and word <> '' and meaning <> '') or
         (kind = 'sentence' and sentence <> '' and translation <> ''))
);

create index if not exists cards_user_id_idx on public.cards (user_id, id);
-- Prevent two devices from creating the same active card at the same time.
-- A losing insert is retried on the next sync and adopts the winning row.
create unique index if not exists cards_unique_active_identity on public.cards
  (user_id, kind, lower(btrim(case when kind = 'word' then word else sentence end)))
  where deleted = false;
alter table public.cards enable row level security;
revoke all on table public.cards from anon, authenticated;
grant select, insert, update on table public.cards to authenticated;

drop policy if exists "cards_select_own" on public.cards;
create policy "cards_select_own" on public.cards for select to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "cards_insert_own" on public.cards;
create policy "cards_insert_own" on public.cards for insert to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "cards_update_own" on public.cards;
create policy "cards_update_own" on public.cards for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create or replace function public.set_cards_updated_at()
returns trigger language plpgsql set search_path = '' as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists cards_updated_at on public.cards;
create trigger cards_updated_at before update on public.cards
for each row execute function public.set_cards_updated_at();
