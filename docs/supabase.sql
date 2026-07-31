-- =====================================================================
--  Manual Inteligente NBU — VISITAR SRL
--  Esquema de la base compartida (Supabase / PostgreSQL)
--
--  Se ejecuta UNA VEZ, entero, desde Supabase → SQL Editor → New query.
--  Es idempotente: se puede volver a correr sin romper nada.
--
--  Qué guarda esta base:
--    · cuentas del equipo y su estado de aprobación
--    · verificaciones de ficha y propuestas de «cómo se carga acá»
--    · correcciones de contenido hechas por auditoría
--    · textos y logo de la empresa
--
--  Qué NO guarda, y no debe guardar nunca:
--    · datos de pacientes (nombre, DNI, afiliado, diagnóstico de una persona)
--    · el catálogo de códigos, que viaja dentro del propio archivo de la app
--
--  Diseñado por Juan Pablo Besada.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. PERFILES
--    Una fila por usuario. El id es el mismo que el de Supabase Auth, así
--    que la identidad la maneja Supabase y acá sólo vive el rol, el estado
--    de aprobación y las preferencias personales.
-- ---------------------------------------------------------------------
create table if not exists public.perfiles (
  id           uuid primary key references auth.users on delete cascade,
  nombre       text not null,
  rol          text not null default 'usuario' check (rol in ('usuario','admin')),
  estado       text not null default 'pendiente' check (estado in ('pendiente','activo','rechazado')),
  favoritos    jsonb not null default '[]'::jsonb,
  notas        jsonb not null default '{}'::jsonb,
  recientes    jsonb not null default '[]'::jsonb,
  ub           numeric,
  creado       timestamptz not null default now(),
  actualizado  timestamptz not null default now()
);

comment on table  public.perfiles          is 'Cuentas del equipo. estado=pendiente hasta que el administrador la habilita.';
comment on column public.perfiles.estado   is 'pendiente | activo | rechazado';
comment on column public.perfiles.rol      is 'usuario | admin. Hay un solo admin (lo garantiza un trigger).';

-- ---------------------------------------------------------------------
-- 2. FUNCIONES DE APOYO
--    Van con SECURITY DEFINER para que las policies de «perfiles» puedan
--    consultar «perfiles» sin caer en recursión infinita de RLS.
-- ---------------------------------------------------------------------
create or replace function public.es_admin() returns boolean
  language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.perfiles
    where id = auth.uid() and rol = 'admin' and estado = 'activo');
$$;

create or replace function public.es_activo() returns boolean
  language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.perfiles
    where id = auth.uid() and estado = 'activo');
$$;

-- ---------------------------------------------------------------------
-- 3. ALTA DE CUENTA
--    Cuando alguien se registra, Supabase crea la fila en auth.users y este
--    trigger le arma el perfil PENDIENTE. Nadie puede darse de alta activo:
--    el estado inicial lo pone la base, no el cliente.
-- ---------------------------------------------------------------------
create or replace function public.perfil_nuevo() returns trigger
  language plpgsql security definer set search_path = public as $$
begin
  insert into public.perfiles (id, nombre, rol, estado)
  values (
    new.id,
    coalesce(nullif(trim(new.raw_user_meta_data ->> 'nombre'), ''), split_part(new.email, '@', 1)),
    'usuario',
    'pendiente')
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.perfil_nuevo();

-- ---------------------------------------------------------------------
-- 4. GUARDIA CONTRA LA AUTOPROMOCIÓN
--    Un usuario puede editar su nombre, sus favoritos, sus notas y su U.B.
--    Lo que NO puede es cambiarse el rol ni el estado: si no es admin, esos
--    dos campos se restauran a lo que estaban.
-- ---------------------------------------------------------------------
create or replace function public.perfil_guardia() returns trigger
  language plpgsql security definer set search_path = public as $$
begin
  if not public.es_admin() then
    new.rol    := old.rol;
    new.estado := old.estado;
  end if;
  new.id     := old.id;
  new.creado := old.creado;
  new.actualizado := now();
  return new;
end $$;

drop trigger if exists perfiles_guardia on public.perfiles;
create trigger perfiles_guardia
  before update on public.perfiles
  for each row execute function public.perfil_guardia();

-- ---------------------------------------------------------------------
-- 5. UN SOLO ADMINISTRADOR
--    Constraint trigger DEFERRABLE: la comprobación se hace al cerrar la
--    transacción, así la transferencia (bajar a uno y subir a otro) pasa
--    sin quedar transitoriamente en cero o en dos.
-- ---------------------------------------------------------------------
create or replace function public.un_solo_admin() returns trigger
  language plpgsql set search_path = public as $$
declare n int;
begin
  select count(*) into n from public.perfiles where rol = 'admin' and estado = 'activo';
  if n > 1 then
    raise exception 'Sólo puede haber un administrador activo (hay %). Transferí el rol en lugar de sumar otro.', n;
  end if;
  return null;
end $$;

drop trigger if exists perfiles_un_admin on public.perfiles;
create constraint trigger perfiles_un_admin
  after insert or update on public.perfiles
  deferrable initially deferred
  for each row execute function public.un_solo_admin();

-- Transferencia de la administración, en una sola transacción.
create or replace function public.transferir_admin(nuevo uuid) returns void
  language plpgsql security definer set search_path = public as $$
begin
  if not public.es_admin() then
    raise exception 'Sólo el administrador puede transferir la administración.';
  end if;
  update public.perfiles set rol = 'usuario' where rol = 'admin';
  update public.perfiles set rol = 'admin', estado = 'activo' where id = nuevo;
end $$;

-- ---------------------------------------------------------------------
-- 6. CONTENIDO COMPARTIDO
-- ---------------------------------------------------------------------

-- Correcciones de ficha hechas por auditoría (✎ Editar ficha).
create table if not exists public.correcciones (
  codigo       text primary key,
  nombre       text,
  norma        jsonb,
  auditoria    jsonb,
  asoc_extra   text,
  autor        uuid references public.perfiles(id) on delete set null,
  actualizado  timestamptz not null default now()
);

-- Verificaciones: las solicita un administrativo, las valida el administrador.
create table if not exists public.verificaciones (
  codigo         text primary key,
  estado         text not null default 'pendiente' check (estado in ('pendiente','validada')),
  solicitada_por uuid references public.perfiles(id) on delete set null,
  solicitada_en  timestamptz not null default now(),
  validada_por   uuid references public.perfiles(id) on delete set null,
  validada_en    timestamptz
);

-- Propuestas de «cómo se carga esta práctica acá». El administrador aprueba.
create table if not exists public.propuestas (
  id           uuid primary key default gen_random_uuid(),
  codigo       text not null,
  texto        text not null,
  estado       text not null default 'pendiente' check (estado in ('pendiente','aprobada','rechazada')),
  autor        uuid references public.perfiles(id) on delete set null,
  creada       timestamptz not null default now(),
  resuelta_por uuid references public.perfiles(id) on delete set null,
  resuelta_en  timestamptz
);
create index if not exists propuestas_pendientes on public.propuestas (estado) where estado = 'pendiente';

-- Textos, logo y valor de U.B. de la empresa. Una sola fila.
create table if not exists public.ajustes (
  id           int primary key default 1 check (id = 1),
  contenido    jsonb not null default '{}'::jsonb,
  actualizado  timestamptz not null default now()
);
insert into public.ajustes (id) values (1) on conflict (id) do nothing;

-- ---------------------------------------------------------------------
-- 7. RLS — quién ve y quién toca qué
--    Regla general: una cuenta PENDIENTE no ve nada más que su propio
--    perfil. Recién aprobada empieza a leer el contenido del equipo.
-- ---------------------------------------------------------------------
alter table public.perfiles       enable row level security;
alter table public.correcciones   enable row level security;
alter table public.verificaciones enable row level security;
alter table public.propuestas     enable row level security;
alter table public.ajustes        enable row level security;

-- PERFILES ------------------------------------------------------------
drop policy if exists perfiles_ver on public.perfiles;
create policy perfiles_ver on public.perfiles for select to authenticated
  using (id = auth.uid() or public.es_admin() or public.es_activo());

drop policy if exists perfiles_editar on public.perfiles;
create policy perfiles_editar on public.perfiles for update to authenticated
  using (id = auth.uid() or public.es_admin())
  with check (id = auth.uid() or public.es_admin());
  -- el trigger «perfiles_guardia» impide que un no-admin se cambie rol o estado

drop policy if exists perfiles_borrar on public.perfiles;
create policy perfiles_borrar on public.perfiles for delete to authenticated
  using (public.es_admin() and rol <> 'admin');

-- CORRECCIONES --------------------------------------------------------
drop policy if exists correcciones_ver on public.correcciones;
create policy correcciones_ver on public.correcciones for select to authenticated
  using (public.es_activo());

drop policy if exists correcciones_escribir on public.correcciones;
create policy correcciones_escribir on public.correcciones for all to authenticated
  using (public.es_admin()) with check (public.es_admin());

-- VERIFICACIONES ------------------------------------------------------
drop policy if exists verif_ver on public.verificaciones;
create policy verif_ver on public.verificaciones for select to authenticated
  using (public.es_activo());

-- un administrativo activo puede SOLICITAR, siempre en estado pendiente
drop policy if exists verif_solicitar on public.verificaciones;
create policy verif_solicitar on public.verificaciones for insert to authenticated
  with check (public.es_activo() and estado = 'pendiente' and solicitada_por = auth.uid());

-- validar o borrar es sólo del administrador
drop policy if exists verif_validar on public.verificaciones;
create policy verif_validar on public.verificaciones for update to authenticated
  using (public.es_admin()) with check (public.es_admin());

drop policy if exists verif_borrar on public.verificaciones;
create policy verif_borrar on public.verificaciones for delete to authenticated
  using (public.es_admin());

-- PROPUESTAS ----------------------------------------------------------
drop policy if exists prop_ver on public.propuestas;
create policy prop_ver on public.propuestas for select to authenticated
  using (public.es_activo());

drop policy if exists prop_crear on public.propuestas;
create policy prop_crear on public.propuestas for insert to authenticated
  with check (public.es_activo() and estado = 'pendiente' and autor = auth.uid());

drop policy if exists prop_resolver on public.propuestas;
create policy prop_resolver on public.propuestas for update to authenticated
  using (public.es_admin()) with check (public.es_admin());

drop policy if exists prop_borrar on public.propuestas;
create policy prop_borrar on public.propuestas for delete to authenticated
  using (public.es_admin());

-- AJUSTES -------------------------------------------------------------
drop policy if exists ajustes_ver on public.ajustes;
create policy ajustes_ver on public.ajustes for select to authenticated
  using (public.es_activo());

drop policy if exists ajustes_editar on public.ajustes;
create policy ajustes_editar on public.ajustes for update to authenticated
  using (public.es_admin()) with check (public.es_admin());

-- ---------------------------------------------------------------------
-- 8. AVISO AL ADMINISTRADOR
--    Cuántas cuentas, verificaciones y propuestas están esperando. Se
--    consulta con un solo llamado en vez de tres.
-- ---------------------------------------------------------------------
create or replace function public.pendientes() returns json
  language sql stable security definer set search_path = public as $$
  select json_build_object(
    'cuentas',       (select count(*) from public.perfiles       where estado = 'pendiente'),
    'verificaciones',(select count(*) from public.verificaciones where estado = 'pendiente'),
    'propuestas',    (select count(*) from public.propuestas     where estado = 'pendiente'))
  where public.es_admin();
$$;

-- ---------------------------------------------------------------------
-- 9. EL PRIMER ADMINISTRADOR
--    El trigger da de alta a todos como pendientes, incluida la primera
--    cuenta, así que hay que habilitar una a mano UNA sola vez.
--
--    Por qué esto es una función y no un simple UPDATE: en el SQL Editor no
--    hay sesión iniciada, así que auth.uid() es NULL y es_admin() da falso.
--    El guardia del punto 4 entonces revierte «rol» y «estado» en silencio:
--    la consola contesta «UPDATE 1» y la cuenta sigue pendiente. La función
--    apaga el guardia por el tiempo que dura la transacción, y como en
--    PostgreSQL el DDL también es transaccional, si algo falla el guardia
--    vuelve solo: no puede quedar apagado.
--
--    Se corre así, una vez, con tu correo:
--
--      select public.hacerme_admin('vos@visitar.com.ar');
--
--    Abajo se le quita el permiso a las cuentas de la app: sólo se puede
--    llamar desde el SQL Editor, nunca desde el navegador.
-- ---------------------------------------------------------------------
create or replace function public.hacerme_admin(correo text) returns text
  language plpgsql security definer set search_path = public as $$
declare
  uid uuid; nom text; otro text;
begin
  select u.id,
         coalesce(nullif(trim(u.raw_user_meta_data ->> 'nombre'), ''),
                  split_part(u.email, '@', 1))
    into uid, nom
    from auth.users u
   where lower(u.email) = lower(trim(correo));

  if uid is null then
    raise exception 'No hay ninguna cuenta con el correo «%». Creala primero desde la app, después corré esto.', correo;
  end if;

  select p.nombre into otro
    from public.perfiles p
   where p.rol = 'admin' and p.estado = 'activo' and p.id <> uid;
  if otro is not null then
    raise exception 'Ya hay un administrador activo (%). Hay uno solo: transferilo desde la app, en Administración → Perfiles → Transferir administración.', otro;
  end if;

  alter table public.perfiles disable trigger perfiles_guardia;

  -- El insert cubre el caso de haberse registrado ANTES de correr este
  -- archivo: ahí el trigger de alta todavía no existía y no hay fila.
  insert into public.perfiles (id, nombre, rol, estado)
       values (uid, nom, 'admin', 'activo')
  on conflict (id) do update set rol = 'admin', estado = 'activo';

  -- Sin esto el ALTER de abajo falla con «pending trigger events»: el
  -- control de «un solo admin» es diferido y quedó encolado por el insert.
  -- Adelantarlo también hace que, si algo estuviera mal, el error salte acá
  -- adentro y se deshaga todo junto.
  set constraints public.perfiles_un_admin immediate;

  alter table public.perfiles enable trigger perfiles_guardia;

  return 'Listo: «' || correo || '» quedó como administrador activo. Ya podés entrar a la app.';
end $$;

-- Sólo desde la consola de Supabase. Ninguna cuenta de la app puede llamarla.
revoke all on function public.hacerme_admin(text) from public;
revoke all on function public.hacerme_admin(text) from anon, authenticated;
