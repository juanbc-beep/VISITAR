-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  MIGRACIÓN: consultas al médico
--
--  Se corre UNA VEZ en el SQL Editor, después de supabase_roles_medicos.sql
--  y de supabase_permisos_funciones.sql. Es idempotente.
--
--  ---------------------------------------------------------------------
--  QUÉ AGREGA, Y POR QUÉ UNA COLUMNA
--  ---------------------------------------------------------------------
--  Hasta ahora el circuito médico iba en un solo sentido: el médico escribe,
--  el equipo lee. Si un administrativo no entiende si una práctica corresponde
--  al diagnóstico, no tiene cómo levantar la mano. Esto le da el botón.
--
--  Una consulta se guarda como una fila de «propuestas», que es la tabla que
--  ya tiene lo necesario: código, texto, autor, estado y quién la resolvió.
--  Lo único que falta es distinguirla de una propuesta de carga, y eso NO se
--  puede resolver marcando el texto: la regla de permiso que decide quién
--  puede cerrarla se evalúa en la base, y una regla que dependa de cómo
--  empieza un campo libre la puede burlar cualquiera escribiendo esa palabra.
--
--  Por eso va una columna. Es una sola, sobre una tabla que ya existe, con
--  valor por defecto: las filas que ya están quedan como 'carga', que es lo
--  que son.
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. EL TIPO DE PROPUESTA
--    carga    — «así se carga esta práctica acá». La resuelve el
--               administrador general, como hasta ahora.
--    consulta — «¿esto corresponde?». La resuelve un médico administrador.
-- ---------------------------------------------------------------------
alter table public.propuestas
  add column if not exists tipo text not null default 'carga';

alter table public.propuestas drop constraint if exists propuestas_tipo_check;
alter table public.propuestas add  constraint propuestas_tipo_check
  check (tipo in ('carga','consulta'));

comment on column public.propuestas.tipo is
  'carga (cómo se carga, la cierra el administrador general) | consulta (pregunta al médico, la cierra un médico administrador)';

create index if not exists propuestas_consultas
  on public.propuestas (estado) where estado = 'pendiente' and tipo = 'consulta';

-- ---------------------------------------------------------------------
-- 2. QUIÉN PUEDE CERRAR QUÉ
--    Se agrega el tercer caso: el médico administrador cierra las consultas,
--    las haya escrito quien las haya escrito. Lo demás queda igual — las
--    propuestas de carga de un administrativo las seguís resolviendo vos.
-- ---------------------------------------------------------------------
drop policy if exists prop_resolver on public.propuestas;
create policy prop_resolver on public.propuestas for update to authenticated
  using (
    public.es_admin()
    or (public.es_medico_admin() and (
          public.propuestas.tipo = 'consulta'
          or exists (select 1 from public.perfiles p
                      where p.id = public.propuestas.autor
                        and p.rol in ('medico','medico_admin'))))
  )
  with check (
    public.es_admin()
    or (public.es_medico_admin() and (
          public.propuestas.tipo = 'consulta'
          or exists (select 1 from public.perfiles p
                      where p.id = public.propuestas.autor
                        and p.rol in ('medico','medico_admin'))))
  );

-- Crear una consulta lo puede hacer cualquiera que esté activo: para eso está.
-- La policy de insert no cambia — ya pedía estado 'pendiente' y autor propio.

-- ---------------------------------------------------------------------
-- 3. LOS CONTADORES
--    Una consulta cuenta para el médico, nunca para el administrador general:
--    él no la puede contestar y un número que no se puede bajar enseña a
--    ignorar el aviso.
-- ---------------------------------------------------------------------
create or replace function public.pendientes() returns json
  language sql stable security definer set search_path = public as $$
  select json_build_object(
    'cuentas',        case when public.es_admin()
                        then (select count(*) from public.perfiles where estado = 'pendiente')
                        else 0 end,
    'verificaciones', case when public.es_admin()
                        then (select count(*) from public.verificaciones where estado = 'pendiente')
                        else 0 end,
    -- Sólo las de carga escritas por alguien que no es médico.
    'propuestas',     case when public.es_admin()
                        then (select count(*) from public.propuestas p
                                left join public.perfiles a on a.id = p.autor
                               where p.estado = 'pendiente' and p.tipo = 'carga'
                                 and coalesce(a.rol,'usuario') not in ('medico','medico_admin'))
                        else 0 end,
    -- Lo médico: los aportes de los médicos MÁS las consultas del equipo.
    'medicas',        case when public.valida_medico()
                        then (select count(*) from public.propuestas p
                                left join public.perfiles a on a.id = p.autor
                               where p.estado = 'pendiente'
                                 and (p.tipo = 'consulta'
                                      or a.rol in ('medico','medico_admin')))
                        else 0 end);
$$;

grant execute on function public.pendientes() to authenticated;
revoke execute on function public.pendientes() from public, anon;

commit;

-- =====================================================================
--  COMPROBAR
--    select tipo, estado, count(*) from public.propuestas group by 1,2;
--  Las filas viejas tienen que estar todas en tipo = 'carga'.
-- =====================================================================
