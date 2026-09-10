-- Votes for "Je soutiens". Run once in the Supabase SQL editor.
-- The page only ever sees the aggregated view and two operations (insert, unvote).

create table if not exists public.votes (
  id          uuid primary key default gen_random_uuid(),
  proposal    text not null,
  client      text not null,
  created_at  timestamptz not null default now(),
  unique (proposal, client)
);

alter table public.votes enable row level security;

-- Anyone may add a vote; nobody may read the raw table (client tokens stay private).
create policy "anon insert" on public.votes
  for insert to anon with check (length(client) between 8 and 64 and length(proposal) between 3 and 64);

create or replace view public.vote_counts
  with (security_invoker = false) as
  select proposal, count(*)::int as n from public.votes group by proposal;

grant select on public.vote_counts to anon;
grant insert on public.votes to anon;

-- Removing a vote requires the client token that created it.
create or replace function public.unvote(p_client text, p_proposal text)
returns void language sql security definer set search_path = public as $$
  delete from public.votes where client = p_client and proposal = p_proposal;
$$;
grant execute on function public.unvote(text, text) to anon;
