-- Protege tablas auxiliares que no forman parte del acceso público de la app.
-- Sin políticas explícitas, RLS aplica denegación por defecto.

begin;

alter table public.equipos enable row level security;
alter table public.equipos force row level security;

alter table public.device_status enable row level security;
alter table public.device_status force row level security;

revoke all on public.equipos from anon;
revoke all on public.device_status from anon;

commit;
