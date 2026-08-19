-- =====================================================================
--  Imitación mínima de Supabase, para poder probar docs/supabase.sql
--  contra un PostgreSQL común.
--
--  No pretende ser Supabase. Reproduce las tres cosas de las que dependen
--  las reglas de acceso, y nada más:
--
--    · el esquema «auth» con la tabla de usuarios y auth.uid()
--    · los roles «anon» y «authenticated»
--    · los DEFAULT PRIVILEGES del esquema público
--
--  El tercero es el que más importa y el menos obvio. Supabase le da DML
--  completo sobre «public» a anon y authenticated, así que toda tabla nueva
--  nace abierta y lo único que la protege es RLS. Sin esta línea, una tabla
--  a la que se le olvidó el «enable row level security» parecería segura
--  acá y estaría abierta en producción. Fue exactamente lo que pasó con
--  «observaciones», y por eso el entorno de prueba tiene que traerlo.
-- =====================================================================

create schema if not exists auth;

create table if not exists auth.users (
  id                 uuid primary key default gen_random_uuid(),
  email              text unique,
  raw_user_meta_data jsonb default '{}'::jsonb
);

-- auth.uid() lee el "JWT" de la sesión. En Supabase viene del token; acá lo
-- ponemos a mano con set_config() para poder actuar como cada usuario.
create or replace function auth.uid() returns uuid
  language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
end $$;

grant usage on schema public, auth to anon, authenticated;
grant select on auth.users to authenticated;

alter default privileges in schema public grant all     on tables    to anon, authenticated;
alter default privileges in schema public grant all     on sequences to anon, authenticated;
alter default privileges in schema public grant execute on functions to anon, authenticated;
