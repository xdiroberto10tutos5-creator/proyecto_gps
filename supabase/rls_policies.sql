-- PASO 2 DE 2
-- Ejecutar solamente cuando la consulta de verificación devuelva:
-- coaches_user_id_creada = true
-- jugadores_coach_id_creada = true

begin;

alter table public.coaches
  drop constraint if exists coaches_user_id_fkey;
alter table public.coaches
  add constraint coaches_user_id_fkey
  foreign key (user_id) references auth.users(id) on delete cascade;

alter table public.jugadores
  drop constraint if exists jugadores_coach_id_fkey;
alter table public.jugadores
  add constraint jugadores_coach_id_fkey
  foreign key (coach_id) references public.coaches(id) on delete cascade;

create or replace function public.crear_perfil_coach()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.coaches (user_id, nombre, email)
  values (
    new.id,
    coalesce(nullif(new.raw_user_meta_data ->> 'nombre', ''), split_part(new.email, '@', 1)),
    new.email
  )
  on conflict (user_id) do update
    set email = excluded.email;
  return new;
end;
$$;

drop trigger if exists crear_coach_al_registrarse on auth.users;
create trigger crear_coach_al_registrarse
  after insert on auth.users
  for each row execute procedure public.crear_perfil_coach();

insert into public.coaches (user_id, nombre, email)
select
  u.id,
  coalesce(nullif(u.raw_user_meta_data ->> 'nombre', ''), split_part(u.email, '@', 1)),
  u.email
from auth.users u
where not exists (
  select 1 from public.coaches c where c.user_id = u.id
)
on conflict (user_id) do nothing;

alter table public.coaches enable row level security;
alter table public.coaches force row level security;
alter table public.jugadores enable row level security;
alter table public.jugadores force row level security;
alter table public.sesiones enable row level security;
alter table public.sesiones force row level security;
alter table public.gps_data enable row level security;
alter table public.gps_data force row level security;
alter table public.metricas enable row level security;
alter table public.metricas force row level security;

do $$
declare
  policy_record record;
begin
  for policy_record in
    select schemaname, tablename, policyname
    from pg_policies
    where schemaname = 'public'
      and tablename in ('coaches', 'jugadores', 'sesiones', 'gps_data', 'metricas')
  loop
    execute format(
      'drop policy if exists %I on %I.%I',
      policy_record.policyname,
      policy_record.schemaname,
      policy_record.tablename
    );
  end loop;
end
$$;

create policy coaches_select_own on public.coaches
  for select to authenticated using (user_id = auth.uid());
create policy coaches_insert_own on public.coaches
  for insert to authenticated with check (user_id = auth.uid());
create policy coaches_update_own on public.coaches
  for update to authenticated using (user_id = auth.uid())
  with check (user_id = auth.uid());
create policy coaches_delete_own on public.coaches
  for delete to authenticated using (user_id = auth.uid());

create policy jugadores_select_own on public.jugadores
  for select to authenticated using (
    exists (
      select 1 from public.coaches c
      where c.id = jugadores.coach_id and c.user_id = auth.uid()
    )
  );
create policy jugadores_insert_own on public.jugadores
  for insert to authenticated with check (
    exists (
      select 1 from public.coaches c
      where c.id = jugadores.coach_id and c.user_id = auth.uid()
    )
  );
create policy jugadores_update_own on public.jugadores
  for update to authenticated using (
    exists (
      select 1 from public.coaches c
      where c.id = jugadores.coach_id and c.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.coaches c
      where c.id = jugadores.coach_id and c.user_id = auth.uid()
    )
  );
create policy jugadores_delete_own on public.jugadores
  for delete to authenticated using (
    exists (
      select 1 from public.coaches c
      where c.id = jugadores.coach_id and c.user_id = auth.uid()
    )
  );

create policy sesiones_select_own on public.sesiones
  for select to authenticated using (
    exists (
      select 1 from public.coaches c
      where c.id = sesiones.coach_id and c.user_id = auth.uid()
    )
  );
create policy sesiones_insert_own on public.sesiones
  for insert to authenticated with check (
    exists (
      select 1 from public.coaches c
      where c.id = sesiones.coach_id and c.user_id = auth.uid()
    )
  );
create policy sesiones_update_own on public.sesiones
  for update to authenticated using (
    exists (
      select 1 from public.coaches c
      where c.id = sesiones.coach_id and c.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.coaches c
      where c.id = sesiones.coach_id and c.user_id = auth.uid()
    )
  );
create policy sesiones_delete_own on public.sesiones
  for delete to authenticated using (
    exists (
      select 1 from public.coaches c
      where c.id = sesiones.coach_id and c.user_id = auth.uid()
    )
  );

create policy gps_select_own on public.gps_data
  for select to authenticated using (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = gps_data.sesion_id and c.user_id = auth.uid()
    )
    and exists (
      select 1 from public.jugadores j
      join public.coaches c on c.id = j.coach_id
      where j.id = gps_data.jugador_id and c.user_id = auth.uid()
    )
  );
create policy gps_insert_own on public.gps_data
  for insert to authenticated with check (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = gps_data.sesion_id and c.user_id = auth.uid()
    )
    and exists (
      select 1 from public.jugadores j
      join public.coaches c on c.id = j.coach_id
      where j.id = gps_data.jugador_id and c.user_id = auth.uid()
    )
  );
create policy gps_update_own on public.gps_data
  for update to authenticated using (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = gps_data.sesion_id and c.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = gps_data.sesion_id and c.user_id = auth.uid()
    )
    and exists (
      select 1 from public.jugadores j
      join public.coaches c on c.id = j.coach_id
      where j.id = gps_data.jugador_id and c.user_id = auth.uid()
    )
  );
create policy gps_delete_own on public.gps_data
  for delete to authenticated using (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = gps_data.sesion_id and c.user_id = auth.uid()
    )
  );

create policy metricas_select_own on public.metricas
  for select to authenticated using (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = metricas.sesion_id and c.user_id = auth.uid()
    )
  );
create policy metricas_insert_own on public.metricas
  for insert to authenticated with check (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = metricas.sesion_id and c.user_id = auth.uid()
    )
    and exists (
      select 1 from public.jugadores j
      join public.coaches c on c.id = j.coach_id
      where j.id = metricas.jugador_id and c.user_id = auth.uid()
    )
  );
create policy metricas_update_own on public.metricas
  for update to authenticated using (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = metricas.sesion_id and c.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = metricas.sesion_id and c.user_id = auth.uid()
    )
    and exists (
      select 1 from public.jugadores j
      join public.coaches c on c.id = j.coach_id
      where j.id = metricas.jugador_id and c.user_id = auth.uid()
    )
  );
create policy metricas_delete_own on public.metricas
  for delete to authenticated using (
    exists (
      select 1 from public.sesiones s
      join public.coaches c on c.id = s.coach_id
      where s.id = metricas.sesion_id and c.user_id = auth.uid()
    )
  );

grant usage on schema public to authenticated;
revoke all on
  public.coaches,
  public.jugadores,
  public.sesiones,
  public.gps_data,
  public.metricas
from anon;
grant select, insert, update, delete on
  public.coaches,
  public.jugadores,
  public.sesiones,
  public.gps_data,
  public.metricas
to authenticated;

commit;
