-- Ejecuta TODO este archivo en una consulta nueva.

alter table public.coaches
add column if not exists user_id uuid;

alter table public.coaches
add column if not exists email text;

alter table public.jugadores
add column if not exists coach_id uuid;

create unique index if not exists coaches_user_id_key
on public.coaches(user_id);

create index if not exists jugadores_coach_id_idx
on public.jugadores(coach_id);

create index if not exists sesiones_coach_id_idx
on public.sesiones(coach_id);

create index if not exists gps_data_sesion_jugador_idx
on public.gps_data(sesion_id, jugador_id);

create index if not exists metricas_sesion_jugador_idx
on public.metricas(sesion_id, jugador_id);

select
  (
    select count(*)
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'coaches'
      and column_name = 'user_id'
  ) as coaches_user_id,
  (
    select count(*)
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'jugadores'
      and column_name = 'coach_id'
  ) as jugadores_coach_id;
