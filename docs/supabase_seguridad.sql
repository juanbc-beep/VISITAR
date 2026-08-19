-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  MIGRACIÓN DE SEGURIDAD: cierra seis huecos en las reglas de acceso
--
--  Se corre UNA VEZ, en el SQL Editor del panel de Supabase, con la cuenta
--  dueña del proyecto. No borra datos y se puede correr de nuevo sin romper:
--  todo está escrito para ser idempotente.
--
--  Corré esto si tu base ya está andando (da igual si la instalaste con
--  supabase.sql o con supabase_roles_medicos.sql: los seis puntos faltan en
--  las dos). Si estás instalando desde cero con supabase.sql, ya vienen
--  incluidos y no hace falta correr este archivo.
--
--  ---------------------------------------------------------------------
--  QUÉ ARREGLA, Y POR QUÉ IMPORTA
--  ---------------------------------------------------------------------
--  1. «observaciones» nunca tuvo RLS habilitada. Sus dos policies existían
--     pero PostgreSQL no las evaluaba: una policy sobre una tabla con RLS
--     apagada no protege de menos, no hace absolutamente nada. Cualquier
--     cuenta —incluida una PENDIENTE, que no debería ver nada— podía leer,
--     escribir y borrar todas las observaciones. Es el más grave de los seis.
--
--  2. transferir_admin() dejaba la base SIN NINGÚN administrador, y sin
--     avisar. Son dos UPDATE seguidos: después del primero quien llama ya no
--     es admin, así que en el segundo «perfiles_guardia» veía es_admin()=false
--     y revertía el ascenso del sucesor en silencio. Comprobado: la función
--     terminaba sin error y quedaban cero administradores.
--
--  3. El médico administrador podía BORRAR una corrección entera. La policy
--     era «for all» (incluye DELETE) pero el guardia que lo acota sólo corre
--     «before insert or update». Borrar lograba el mismo daño que editar la
--     ficha, que es justo lo que el diseño le niega.
--
--  4. El guardia de correcciones buscaba la fila anterior por «new.codigo».
--     Como «codigo» es la clave y se puede cambiar en un UPDATE, renombrarla
--     a un código libre hacía que no encontrara nada: la corrección original
--     desaparecía de su código y reaparecía vacía en el nuevo.
--
--  5. Cualquier usuario activo leía la fila entera de sus compañeros: notas
--     personales, favoritos y la U.B. de cada uno. Alcanzaba con que la app
--     necesitara los nombres para atribuir quién hizo qué.
--
--  6. Al pedir una verificación se podían mandar «validada_por» y
--     «validada_en» a mano. No daba permisos —el estado seguía pendiente—
--     pero ensuciaba la línea de auditoría, que es lo que se mira cuando
--     una facturación se discute.
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. OBSERVACIONES: encender RLS
--
--    Las policies «obs_ver» y «obs_escribir» ya existen desde el principio.
--    Lo único que faltaba es esta línea, sin la cual no se evalúan nunca.
--    Se vuelven a declarar abajo para que este archivo deje la tabla bien
--    aunque se corra sobre una base donde alguien las haya tocado.
-- ---------------------------------------------------------------------
alter table public.observaciones enable row level security;

drop policy if exists obs_ver on public.observaciones;
create policy obs_ver on public.observaciones for select to authenticated
  using (public.es_activo());

drop policy if exists obs_escribir on public.observaciones;
create policy obs_escribir on public.observaciones for all to authenticated
  using (public.es_admin() or public.es_medico_admin())
  with check (public.es_admin() or public.es_medico_admin());

-- ---------------------------------------------------------------------
-- 2. TRANSFERIR LA ADMINISTRACIÓN SIN QUEDARSE SIN ADMINISTRADOR
--
--    El arreglo es invertir el orden: PRIMERO se asciende al sucesor y
--    DESPUÉS se degrada al saliente. Mientras corre el ascenso, quien llama
--    sigue siendo administrador, así que el guardia lo deja pasar; y cuando
--    corre la degradación también lo sigue siendo, porque todavía no se
--    tocó su fila. En el orden original, el ascenso ocurría cuando el que
--    llamaba ya se había degradado a sí mismo, y el guardia lo revertía.
--
--    Hacerlo en una sola sentencia con «case» no alcanza: el guardia es una
--    función volátil y toma un snapshot nuevo en cada invocación, así que al
--    procesar la segunda fila ya ve aplicada la primera. Está comprobado.
--
--    Entre las dos sentencias hay un instante con dos administradores. Eso
--    es exactamente para lo que «perfiles_un_admin» se declaró deferrable:
--    el control se evalúa al cerrar la transacción, cuando ya hay uno solo.
--
--    No se desactiva ningún trigger a propósito: «hacerme_admin» puede
--    hacerlo porque se corre a mano desde el SQL Editor, pero esta función
--    la llama la app, y un ALTER TABLE toma un lock exclusivo sobre
--    «perfiles» que trabaría a todo el equipo.
--
--    El control «un solo administrador» es diferido: se evalúa al cerrar la
--    transacción, cuando ya hay exactamente uno. No hace falta tocarlo.
-- ---------------------------------------------------------------------
create or replace function public.transferir_admin(nuevo uuid) returns void
  language plpgsql security definer set search_path = public as $$
declare filas int;
begin
  if not public.es_admin() then
    raise exception 'Sólo el administrador puede transferir la administración.';
  end if;

  -- Antes no se comprobaba: con un uuid inexistente el segundo UPDATE no
  -- afectaba ninguna fila y el resultado era el mismo, quedarse sin nadie.
  if nuevo is null or not exists (select 1 from public.perfiles where id = nuevo) then
    raise exception 'No existe la cuenta a la que se quiere transferir la administración.';
  end if;

  -- Ya es el administrador: no hay nada que hacer y así evitamos degradarlo.
  if exists (select 1 from public.perfiles
              where id = nuevo and rol = 'admin' and estado = 'activo') then
    return;
  end if;

  -- 1) Asciende el sucesor. Quien llama todavía es administrador.
  update public.perfiles set rol = 'admin', estado = 'activo' where id = nuevo;
  get diagnostics filas = row_count;
  if filas <> 1 then
    raise exception 'No se pudo ascender a la cuenta indicada. No se cambió nada.';
  end if;

  -- 2) Degrada al saliente. Sigue siendo administrador mientras esto corre,
  --    porque su fila se toca recién ahora.
  update public.perfiles set rol = 'usuario'
   where rol = 'admin' and id <> nuevo;

  -- Cinturón: al cerrar la transacción tiene que quedar exactamente uno, y
  -- tiene que ser el nuevo. Si el guardia hubiera revertido algo, esto lo
  -- detecta acá y deshace todo en vez de dejar la base sin dueño.
  if not exists (select 1 from public.perfiles
                  where id = nuevo and rol = 'admin' and estado = 'activo') then
    raise exception 'La transferencia no se completó: la cuenta destino no quedó como administrador. No se cambió nada.';
  end if;
end $$;

-- ---------------------------------------------------------------------
-- 3. CORRECCIONES: borrar vuelve a ser sólo del administrador general
--
--    Se parte la policy «for all» en tres. Escribir y actualizar siguen
--    abiertos al médico administrador —el guardia acota QUÉ puede cambiar—,
--    pero borrar queda del lado del dueño del manual. Mismo criterio que ya
--    regía en «propuestas» y «verificaciones».
-- ---------------------------------------------------------------------
drop policy if exists correcciones_escribir on public.correcciones;

drop policy if exists correcciones_insertar on public.correcciones;
create policy correcciones_insertar on public.correcciones for insert to authenticated
  with check (public.es_admin() or public.es_medico_admin());

drop policy if exists correcciones_actualizar on public.correcciones;
create policy correcciones_actualizar on public.correcciones for update to authenticated
  using      (public.es_admin() or public.es_medico_admin())
  with check (public.es_admin() or public.es_medico_admin());

drop policy if exists correcciones_borrar on public.correcciones;
create policy correcciones_borrar on public.correcciones for delete to authenticated
  using (public.es_admin());

-- ---------------------------------------------------------------------
-- 4. EL GUARDIA MIRA LA FILA QUE DE VERDAD SE ESTÁ EDITANDO
--
--    Dos cambios sobre el original: la clave se fija («codigo» no se puede
--    mover en un UPDATE, igual que «perfiles_guardia» hace con el id) y la
--    fila anterior se busca por old.codigo, no por new.codigo.
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

  if tg_op = 'UPDATE' then
    -- Sin esto, renombrar el código a uno libre vaciaba la corrección: la
    -- búsqueda de abajo no encontraba nada y los cuatro campos de la ficha
    -- se guardaban en null. Era otra forma de borrarla sin permiso.
    new.codigo := old.codigo;
    select * into viejo from public.correcciones where codigo = old.codigo;
  else
    select * into viejo from public.correcciones where codigo = new.codigo;
  end if;

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

-- ---------------------------------------------------------------------
-- 5. LAS NOTAS PERSONALES DEJAN DE SER PÚBLICAS PARA EL EQUIPO
--
--    La fila entera de «perfiles» pasa a verla sólo su dueño y el
--    administrador. Pero la app necesita poner nombre a los uuid para
--    mostrar quién escribió cada propuesta o corrección, y eso lo necesita
--    cualquiera, no sólo el administrador.
--
--    Para eso está «equipo()»: las cuatro columnas que hacen falta para
--    atribuir autoría, y ninguna de las personales. Corre con los permisos
--    de quien la define, así que ve la tabla entera; el «where» de adentro
--    es lo que decide a quién le contesta. Una cuenta pendiente sigue
--    viendo únicamente la suya.
--
--    FUNCIÓN Y NO VISTA, a propósito. Una vista de una sola tabla es
--    auto-actualizable: PostgreSQL acepta UPDATE y DELETE a través de ella.
--    Y como Supabase le da permisos de escritura a «authenticated» sobre
--    todo lo que hay en «public», una vista acá se convierte en una puerta
--    para escribir en «perfiles» salteándose RLS: un administrativo común
--    podía renombrar la cuenta del administrador. Comprobado. Una función
--    no tiene por dónde escribir, y es el mismo patrón que es_admin().
--
--    Si ya corriste una versión anterior de este archivo, el «drop view»
--    de abajo se lleva la vista que quedó. Era la que el Security Advisor
--    de Supabase marcaba en rojo como «Security Definer View», con razón.
-- ---------------------------------------------------------------------
drop policy if exists perfiles_ver on public.perfiles;
create policy perfiles_ver on public.perfiles for select to authenticated
  using (id = auth.uid() or public.es_admin());

drop view if exists public.equipo;

create or replace function public.equipo()
  returns table (id uuid, nombre text, rol text, estado text)
  language sql stable security definer set search_path = public as $$
  select p.id, p.nombre, p.rol, p.estado
    from public.perfiles p
   where public.es_activo() or p.id = auth.uid();
$$;

comment on function public.equipo() is
  'Nombre y rol del equipo, para atribuir autoría. Sin notas, favoritos ni U.B.';

revoke all on function public.equipo() from public, anon;
grant execute on function public.equipo() to authenticated;

-- ---------------------------------------------------------------------
-- 6. NO SE PUEDE FIRMAR UNA VALIDACIÓN AJENA AL PEDIRLA
--
--    Al insertar, «validada_por» y «validada_en» tienen que venir vacíos.
--    Los llena la base cuando el administrador valida de verdad, vía
--    validar_verificacion() o pedir_verificacion() si es él quien pide.
-- ---------------------------------------------------------------------
drop policy if exists verif_solicitar on public.verificaciones;
create policy verif_solicitar on public.verificaciones for insert to authenticated
  with check (public.es_activo()
              and estado = 'pendiente'
              and solicitada_por = auth.uid()
              and validada_por is null
              and validada_en  is null);

commit;

-- =====================================================================
--  DESPUÉS DE CORRER ESTO
--
--  Comprobación rápida: las seis tablas tienen que dar «t».
--
--    select relname, relrowsecurity
--      from pg_class
--     where relnamespace = 'public'::regnamespace
--       and relname in ('perfiles','correcciones','observaciones',
--                       'verificaciones','propuestas','ajustes')
--     order by relname;
--
--  La app necesita la versión que lee «equipo» en lugar de «perfiles» para
--  los nombres. Si publicás la base antes que la app, durante un rato los
--  aportes van a figurar como «—» en vez del nombre de quien los hizo:
--  molesto y nada más, no se pierde ni se rompe nada.
-- =====================================================================
