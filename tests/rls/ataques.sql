-- =====================================================================
--  Los seis ataques que funcionaban antes de la corrección de seguridad.
--
--  Cada uno se ejecuta como un usuario autenticado real, con RLS activa.
--  Si alguno vuelve a funcionar, el archivo corta con «raise exception» y
--  la Action queda en rojo.
--
--  No son pruebas teóricas: los seis se reprodujeron contra esta misma
--  base antes de arreglarlos. Están acá para que no puedan volver en
--  silencio dentro de seis meses.
-- =====================================================================

\echo ''
\echo '  Ataques que NO tienen que funcionar'

-- ---------------------------------------------------------------------
-- CN-001  Una cuenta pendiente no toca las observaciones
--
--   La tabla se creó sin «enable row level security», así que sus dos
--   policies no se evaluaban nunca y quedaba abierta a cualquiera que se
--   registrara, aunque no estuviera aprobado.
-- ---------------------------------------------------------------------
do $$ begin
  if not (select relrowsecurity from pg_class where oid = 'public.observaciones'::regclass) then
    raise exception 'CN-001: «observaciones» no tiene RLS habilitada. Sus policies no se evalúan y la tabla está abierta.';
  end if;
end $$;

do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'pend@test'), false); end $ident$;
set role authenticated;
do $$ begin
  if (select count(*) from public.observaciones) > 0 then
    raise exception 'CN-001: una cuenta PENDIENTE puede leer las observaciones.';
  end if;
end $$;
delete from public.observaciones where codigo = '420101';
reset role;
do $$ begin
  if (select count(*) from public.observaciones) = 0 then
    raise exception 'CN-001: una cuenta PENDIENTE pudo borrar las observaciones.';
  end if;
end $$;
\echo '   ok  CN-001  cuenta pendiente aislada de observaciones'

-- ---------------------------------------------------------------------
-- CN-002  Transferir la administración no deja la base sin dueño
--
--   Al degradar primero, «perfiles_guardia» veía es_admin() = false
--   durante el ascenso y lo revertía sin avisar: la función terminaba
--   sin error y quedaban cero administradores.
-- ---------------------------------------------------------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'admin@test'), false); end $ident$;
set role authenticated;
do $call$ begin perform public.transferir_admin((select id from public.perfiles where nombre = 'Administrativo')); end $call$;
reset role;
do $$
declare n int; quien text;
begin
  select count(*), coalesce(string_agg(nombre, ', '), 'ninguno')
    into n, quien
    from public.perfiles where rol = 'admin' and estado = 'activo';
  if n <> 1 then
    raise exception 'CN-002: tras transferir quedaron % administradores activos (%). Tiene que quedar exactamente uno.', n, quien;
  end if;
  if quien <> 'Administrativo' then
    raise exception 'CN-002: el administrador quedó siendo «%» y no la cuenta destino.', quien;
  end if;
end $$;
\echo '   ok  CN-002  la administración se transfiere sin dejar la base sin dueño'

-- Se devuelve la administración, para que el resto de las pruebas corra
-- con el reparto de roles original.
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'user@test'), false); end $ident$;
set role authenticated;
do $call$ begin perform public.transferir_admin((select p.id from public.perfiles p
                                  join auth.users u on u.id = p.id where u.email = 'admin@test')); end $call$;
reset role;
update public.perfiles set estado = 'activo' where nombre = 'Administrativo';

-- ---------------------------------------------------------------------
-- CN-003  El médico administrador no puede borrar una corrección
--
--   La policy era «for all», que incluye DELETE, y el guardia que lo
--   acota sólo corre «before insert or update». Borrar lograba el mismo
--   daño que editar la ficha.
-- ---------------------------------------------------------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'medico@test'), false); end $ident$;
set role authenticated;
delete from public.correcciones where codigo = '420101';
reset role;
do $$ begin
  if (select count(*) from public.correcciones where codigo = '420101') = 0 then
    raise exception 'CN-003: un médico administrador pudo BORRAR la corrección entera.';
  end if;
end $$;
\echo '   ok  CN-003  borrar correcciones sigue siendo del administrador general'

-- ---------------------------------------------------------------------
-- CN-004  Renombrar el código no vacía la corrección
--
--   El guardia buscaba la fila anterior por «new.codigo». Como la clave
--   se puede cambiar en un UPDATE, apuntarla a un código libre hacía que
--   no encontrara nada y guardara los cuatro campos de la ficha en null.
-- ---------------------------------------------------------------------
set role authenticated;
update public.correcciones set codigo = '999999' where codigo = '420101';
reset role;
do $$
declare n text;
begin
  if not exists (select 1 from public.correcciones where codigo = '420101') then
    raise exception 'CN-004: un médico administrador movió la corrección a otro código.';
  end if;
  select nombre into n from public.correcciones where codigo = '420101';
  if n is distinct from 'Consulta médica' then
    raise exception 'CN-004: la ficha quedó en «%» en vez de conservarse.', coalesce(n, 'NULL');
  end if;
end $$;
\echo '   ok  CN-004  la clave de una corrección no se puede mover'

-- ---------------------------------------------------------------------
-- CN-005  Las notas personales no las lee el resto del equipo
-- ---------------------------------------------------------------------
set role authenticated;   -- seguimos como el médico administrador
do $$
declare n int;
begin
  select count(*) into n
    from public.perfiles
   where id <> auth.uid() and (notas::text <> '{}' or ub is not null);
  if n > 0 then
    raise exception 'CN-005: un usuario activo lee las notas o la U.B. de % compañero(s).', n;
  end if;
end $$;
reset role;
\echo '   ok  CN-005  notas, favoritos y U.B. quedan en su dueño'

-- ---------------------------------------------------------------------
-- CN-006  No se puede firmar una validación ajena al pedir una verificación
-- ---------------------------------------------------------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'user@test'), false); end $ident$;
set role authenticated;
do $$ begin
  begin
    insert into public.verificaciones (codigo, estado, solicitada_por, validada_por, validada_en)
    values ('420101', 'pendiente', auth.uid(),
            (select id from public.perfiles where nombre = 'Admin General'), now());
    raise exception 'CN-006: se pudo insertar una verificación con la firma de otro.';
  exception
    when insufficient_privilege then null;   -- la policy lo rechazó: es lo esperado
  end;
end $$;
reset role;
do $$ begin
  if exists (select 1 from public.verificaciones where codigo = '420101' and validada_por is not null) then
    raise exception 'CN-006: quedó registrada una firma de validación falsa.';
  end if;
end $$;
\echo '   ok  CN-006  la firma de validación no se puede falsear'

-- ---------------------------------------------------------------------
-- CN-011  No hay forma de escribir en «perfiles» esquivando RLS
--
--   «equipo» nació como vista para no exponer las notas personales. Una
--   vista de una sola tabla es auto-actualizable, y como corría con los
--   permisos de su dueño se saltaba RLS también para escribir: un
--   administrativo común podía renombrar la cuenta del administrador con
--   un UPDATE a través de ella. Lo marcó el Security Advisor de Supabase
--   y se comprobó que funcionaba de verdad.
--
--   Ahora es una función, que no tiene por dónde escribir. Esta prueba
--   falla si alguien la vuelve a convertir en vista o deja cualquier otro
--   objeto escribible que llegue a «perfiles» sin pasar por RLS.
-- ---------------------------------------------------------------------
do $$
declare vistas text;
begin
  select coalesce(string_agg(table_name, ', '), '') into vistas
    from information_schema.views
   where table_schema = 'public'
     and view_definition ilike '%perfiles%';
  if vistas <> '' then
    raise exception 'CN-011: hay vistas sobre «perfiles» (%). Una vista simple es auto-actualizable y saltea RLS: usá una función.', vistas;
  end if;
end $$;

do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'user@test'), false); end $ident$;
set role authenticated;
update public.perfiles set nombre = 'HACKEADO' where nombre = 'Admin General';
reset role;
do $$ begin
  if not exists (select 1 from public.perfiles where nombre = 'Admin General') then
    raise exception 'CN-011: un usuario común pudo renombrar la cuenta del administrador.';
  end if;
end $$;
\echo '   ok  CN-011  no se puede escribir en perfiles esquivando RLS'
