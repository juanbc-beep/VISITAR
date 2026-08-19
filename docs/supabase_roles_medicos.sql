-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  MIGRACIÓN: cuatro tipos de cuenta (agrega los dos roles médicos)
--
--  Se corre UNA VEZ, en el SQL Editor del panel de Supabase, con la cuenta
--  dueña del proyecto. No borra nada y se puede correr de nuevo sin romper:
--  todo está escrito para ser idempotente.
--
--  ---------------------------------------------------------------------
--  POR QUÉ ESTO NO SE PUEDE HACER SÓLO EN LA APP
--  ---------------------------------------------------------------------
--  La columna «perfiles.rol» tiene un CHECK que sólo acepta 'usuario' y
--  'admin': hoy es imposible guardar un rol médico, la base lo rechaza.
--  Y todos los permisos de escritura son «es_admin()». Si los cuatro roles
--  se dibujaran únicamente en el navegador, cualquiera con la consola
--  abierta escribiría igual: la clave publicable es pública por diseño y lo
--  que protege los datos son estas reglas, no la interfaz.
--  Por eso el límite «el médico administrador NO tiene el poder del
--  administrador general» se escribe acá, donde se cumple de verdad.
--
--  ---------------------------------------------------------------------
--  QUÉ CAMBIA, EXACTAMENTE
--  ---------------------------------------------------------------------
--  · Ninguna tabla nueva. Ninguna columna nueva.
--  · El CHECK de «rol» pasa a aceptar cuatro valores.
--  · Dos funciones de apoyo nuevas, del mismo tipo que es_admin().
--  · Las policies de propuestas, observaciones y correcciones se abren al
--    médico administrador, y un trigger le impide pasarse de ahí.
--
--  La revisión médica aprobada viaja dentro de «correcciones.datos», que ya
--  es jsonb libre y ya se usa así. No hace falta una tabla para esto.
--
--  ---------------------------------------------------------------------
--  ⚠️ CORRÉ DESPUÉS supabase_seguridad.sql
--  ---------------------------------------------------------------------
--  Este archivo quedó como está por ser el registro de lo que ya se aplicó.
--  Tiene seis huecos que se cierran en «supabase_seguridad.sql»: entre ellos,
--  la policy de correcciones de acá abajo es «for all» y deja que el médico
--  administrador BORRE la corrección entera, que es justo lo que el trigger
--  de más arriba se ocupa de impedirle por la vía de la edición.
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. LOS CUATRO ROLES
--
--    admin        Administrador general. Uno solo. Cuentas, roles, textos,
--                 logo, respaldo, restaurar. Es el dueño del manual.
--    medico_admin Médico administrador. Valida lo médico. Varios permitidos.
--                 NO toca cuentas, ni configuración, ni respaldo.
--    medico       Médico administrativo. Aporta lo médico; no valida.
--    usuario      Administrativo. Como hasta ahora.
-- ---------------------------------------------------------------------
alter table public.perfiles drop constraint if exists perfiles_rol_check;
alter table public.perfiles add  constraint perfiles_rol_check
  check (rol in ('usuario','admin','medico','medico_admin'));

comment on column public.perfiles.rol is
  'usuario (administrativo) | medico (médico administrativo) | medico_admin (médico administrador) | admin (administrador general, uno solo)';

-- El trigger «un_solo_admin» cuenta rol = ''admin'' y nada más, así que los
-- médicos administradores pueden ser varios sin tocarlo. Queda dicho acá
-- para que nadie lo «arregle» pensando que es un olvido.

-- ---------------------------------------------------------------------
-- 2. FUNCIONES DE APOYO
--    SECURITY DEFINER por lo mismo que es_admin(): las policies de
--    «perfiles» consultan «perfiles» y sin esto entran en recursión de RLS.
-- ---------------------------------------------------------------------
create or replace function public.es_medico_admin() returns boolean
  language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.perfiles
    where id = auth.uid() and rol = 'medico_admin' and estado = 'activo');
$$;

-- Cualquiera de los dos roles médicos.
create or replace function public.es_medico() returns boolean
  language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.perfiles
    where id = auth.uid() and rol in ('medico','medico_admin') and estado = 'activo');
$$;

-- Quién puede dar por buena una revisión médica: el médico administrador, y
-- también el administrador general, que está por encima de todo.
create or replace function public.valida_medico() returns boolean
  language sql stable security definer set search_path = public as $$
  select public.es_admin() or public.es_medico_admin();
$$;

grant execute on function public.es_medico_admin() to authenticated;
grant execute on function public.es_medico()       to authenticated;
grant execute on function public.valida_medico()   to authenticated;

-- ---------------------------------------------------------------------
-- 3. EL LÍMITE DEL MÉDICO ADMINISTRADOR
--
--    Sin esto, abrirle «correcciones» le daría la ficha entera: podría
--    cambiar la denominación, la norma y las líneas de auditoría, que es
--    justamente el poder del administrador general.
--
--    El guardia deja pasar UNA sola cosa cuando el que escribe es médico
--    administrador y no el administrador general: la revisión médica, que
--    vive en datos->'revision_medica'. Todo lo demás se revierte al valor
--    anterior, en silencio y del lado del servidor. Mismo patrón que
--    «perfiles_guardia», que ya impide que alguien se cambie el rol solo.
-- ---------------------------------------------------------------------
create or replace function public.correcciones_guardia() returns trigger
  language plpgsql security definer set search_path = public as $$
declare viejo public.correcciones%rowtype;
begin
  if public.es_admin() then
    return new;                                   -- el dueño del manual, sin límite
  end if;
  if not public.es_medico_admin() then
    raise exception 'Sólo el administrador o un médico administrador pueden tocar las correcciones.';
  end if;

  select * into viejo from public.correcciones where codigo = new.codigo;

  -- Campos de la ficha: se conservan como estaban. Si la fila es nueva,
  -- quedan vacíos: un médico administrador no estrena una corrección de ficha.
  new.nombre     := viejo.nombre;
  new.norma      := viejo.norma;
  new.auditoria  := viejo.auditoria;
  new.asoc_extra := viejo.asoc_extra;

  -- De «datos» sólo sobrevive la revisión médica; el resto vuelve al anterior.
  new.datos := coalesce(viejo.datos, '{}'::jsonb)
               || jsonb_build_object('revision_medica',
                    coalesce(new.datos -> 'revision_medica', 'null'::jsonb));
  return new;
end $$;

drop trigger if exists correcciones_limite_medico on public.correcciones;
create trigger correcciones_limite_medico
  before insert or update on public.correcciones
  for each row execute function public.correcciones_guardia();

-- ---------------------------------------------------------------------
-- 4. POLICIES
--    Se reemplazan las que cambian. Las de lectura no se tocan: quien está
--    activo sigue viendo todo el contenido del equipo.
-- ---------------------------------------------------------------------

-- CORRECCIONES: escribe el administrador general y el médico administrador.
-- Lo que el segundo puede cambiar lo acota el trigger de arriba, no esto.
drop policy if exists correcciones_escribir on public.correcciones;
create policy correcciones_escribir on public.correcciones for all to authenticated
  using (public.es_admin() or public.es_medico_admin())
  with check (public.es_admin() or public.es_medico_admin());

-- OBSERVACIONES: el aviso por práctica. El médico administrador también,
-- porque «esta práctica necesita el diagnóstico en la orden» es exactamente
-- lo que un administrativo no tiene cómo saber.
drop policy if exists obs_escribir on public.observaciones;
create policy obs_escribir on public.observaciones for all to authenticated
  using (public.es_admin() or public.es_medico_admin())
  with check (public.es_admin() or public.es_medico_admin());

-- PROPUESTAS: las resuelve el administrador general siempre; el médico
-- administrador, sólo las que escribió un médico. Un aporte médico lo cierra
-- un médico, y una propuesta administrativa la seguís cerrando vos.
drop policy if exists prop_resolver on public.propuestas;
create policy prop_resolver on public.propuestas for update to authenticated
  using (
    public.es_admin()
    or (public.es_medico_admin() and exists (
          select 1 from public.perfiles p
          where p.id = public.propuestas.autor and p.rol in ('medico','medico_admin')))
  )
  with check (
    public.es_admin()
    or (public.es_medico_admin() and exists (
          select 1 from public.perfiles p
          where p.id = public.propuestas.autor and p.rol in ('medico','medico_admin')))
  );

-- Borrar propuestas sigue siendo del administrador general solamente.

-- VERIFICACIONES: sin cambios a propósito. «Verificada» significa
-- «contrasté esta ficha contra la fuente», que es trabajo administrativo y lo
-- seguís validando vos. Lo médico tiene su propio sello, que es otra cosa.

-- AJUSTES (textos, logo, U.B. de la empresa), PERFILES (cuentas y roles) y
-- transferir_admin: sin cambios. Ahí no entra ningún médico.

-- ---------------------------------------------------------------------
-- 5. RESUMEN DE PENDIENTES
--    La función que alimenta la campana tiene que contar distinto según
--    quién pregunta: al médico administrador le importan los aportes
--    médicos, no las cuentas por aprobar.
-- ---------------------------------------------------------------------
--    Sigue devolviendo json y con las mismas claves de antes, más «medicas».
--    Nada de cambiarle el tipo de retorno: «create or replace» no puede, y un
--    «drop function» dejaría la app sin la campana hasta terminar la migración.
--
--    Y se le saca el «where es_admin()» del final, que hacía que la función no
--    devolviera NINGUNA fila a quien no fuera administrador. Ahora contesta
--    siempre, con ceros en lo que no le corresponde ver a quien pregunta.
create or replace function public.pendientes() returns json
  language sql stable security definer set search_path = public as $$
  select json_build_object(
    'cuentas',        case when public.es_admin()
                        then (select count(*) from public.perfiles where estado = 'pendiente')
                        else 0 end,
    'verificaciones', case when public.es_admin()
                        then (select count(*) from public.verificaciones where estado = 'pendiente')
                        else 0 end,
    -- Las propuestas se reparten por el rol de quien las escribió: las
    -- administrativas son tuyas, las médicas del médico administrador.
    'propuestas',     case when public.es_admin()
                        then (select count(*) from public.propuestas p
                                left join public.perfiles a on a.id = p.autor
                               where p.estado = 'pendiente'
                                 and coalesce(a.rol,'usuario') not in ('medico','medico_admin'))
                        else 0 end,
    'medicas',        case when public.valida_medico()
                        then (select count(*) from public.propuestas p
                                join public.perfiles a on a.id = p.autor
                               where p.estado = 'pendiente'
                                 and a.rol in ('medico','medico_admin'))
                        else 0 end);
$$;

grant execute on function public.pendientes() to authenticated;

commit;

-- =====================================================================
--  DESPUÉS DE CORRER ESTO
--
--  Los roles se asignan desde la app: Administración › Perfiles del equipo.
--  Si preferís hacerlo a mano la primera vez, desde el SQL Editor:
--
--    update public.perfiles set rol = 'medico_admin'
--     where nombre = 'Nombre del médico';
--
--    update public.perfiles set rol = 'medico'
--     where nombre = 'Nombre del otro médico';
--
--  Para volver atrás, si hiciera falta: dejar a todos en 'usuario' o 'admin'
--  y restaurar el CHECK original con los dos valores.
-- =====================================================================
