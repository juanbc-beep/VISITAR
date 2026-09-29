-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  MIGRACIÓN: códigos nuevos cargados por el administrador general
--
--  Se corre UNA VEZ, en el SQL Editor del panel de Supabase, con la cuenta
--  dueña del proyecto. No borra nada y se puede correr de nuevo sin romper:
--  todo está escrito para ser idempotente.
--
--  ---------------------------------------------------------------------
--  QUÉ RESUELVE
--  ---------------------------------------------------------------------
--  Hasta ahora todos los códigos del manual salían de la base que compila el
--  repositorio (data/nbu_db.json): si VISITAR creaba un código nuevo en su
--  Nomenclador Único, o aparecía uno que ninguna fuente traía, había que
--  tocar los parsers y volver a publicar. El módulo «Códigos nuevos» de la
--  app (sólo el administrador general) los da de alta a mano y quedan
--  establecidos para todo el equipo: con su denominación, sus equivalencias
--  entre nomencladores, su tipo de cobertura y lo demás que se quiera cargar.
--
--  ---------------------------------------------------------------------
--  QUÉ CAMBIA, EXACTAMENTE
--  ---------------------------------------------------------------------
--  Una tabla nueva, «codigos_nuevos», una fila por código:
--    codigo       la clave interna de la app (los del Único llevan prefijo «U»,
--                 igual que en nbu_db.json, para no chocar con un NBU o PMO
--                 que use los mismos dígitos)
--    nomenclador  NBU, PMO o UNICO
--    datos        lo que cargó el administrador (denominación, equivalencias,
--                 cobertura, etc.); la app arma con eso la ficha completa y el
--                 resto la trata como cualquier otro código
--
--  Quién puede qué:
--    leer     cualquier cuenta ACTIVA (todo el equipo tiene que verlos)
--    escribir SÓLO el administrador general (insertar, cambiar, borrar)
--  El médico administrador NO puede: no es una ficha que corregir sino un
--  código que se agrega al manual, y eso es del dueño del manual.
--
--  También queda auditada (quién dio de alta, cambió o borró cada código y
--  cuándo) con el mismo trigger que ya usan «correcciones» y «observaciones».
--
--  ---------------------------------------------------------------------
--  SI NO SE CORRE
--  ---------------------------------------------------------------------
--  La app no se rompe: el módulo avisa que la base todavía no tiene la tabla
--  y el resto sigue como siempre.
-- =====================================================================

begin;

create table if not exists public.codigos_nuevos (
  codigo       text primary key check (length(codigo) between 1 and 40),
  nomenclador  text not null check (nomenclador in ('NBU','PMO','UNICO')),
  datos        jsonb not null check (jsonb_typeof(datos) = 'object' and octet_length(datos::text) <= 200000),
  autor        uuid references public.perfiles(id) on delete set null,
  creado       timestamptz not null default now(),
  actualizado  timestamptz not null default now()
);
comment on table public.codigos_nuevos is
  'Códigos agregados a mano por el administrador general. Los lee todo el equipo.';

alter table public.codigos_nuevos enable row level security;

drop policy if exists cnuevos_ver on public.codigos_nuevos;
create policy cnuevos_ver on public.codigos_nuevos for select to authenticated
  using (public.es_activo());

drop policy if exists cnuevos_insertar on public.codigos_nuevos;
create policy cnuevos_insertar on public.codigos_nuevos for insert to authenticated
  with check (public.es_admin());

drop policy if exists cnuevos_actualizar on public.codigos_nuevos;
create policy cnuevos_actualizar on public.codigos_nuevos for update to authenticated
  using (public.es_admin()) with check (public.es_admin());

drop policy if exists cnuevos_borrar on public.codigos_nuevos;
create policy cnuevos_borrar on public.codigos_nuevos for delete to authenticated
  using (public.es_admin());

-- Rastro de auditoría. Si el proyecto todavía no corrió supabase_auditoria.sql
-- no hay función auditar(): se omite en vez de cortar la migración.
do $aud$
begin
  if to_regprocedure('public.auditar()') is not null then
    drop trigger if exists auditar_codigos_nuevos on public.codigos_nuevos;
    create trigger auditar_codigos_nuevos after insert or update or delete
      on public.codigos_nuevos for each row execute function public.auditar();
  end if;
end $aud$;

commit;

-- =====================================================================
--  DESPUÉS DE CORRER ESTO
--
--  El administrador general ve el botón «Códigos nuevos» en la barra
--  superior. Nadie más lo ve, y aunque manipulara la app la base le
--  rechazaría la escritura.
-- =====================================================================
