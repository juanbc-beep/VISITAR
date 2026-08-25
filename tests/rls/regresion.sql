-- =====================================================================
--  Lo que TIENE que seguir funcionando.
--
--  Una regla de acceso demasiado cerrada rompe la app sin que nadie se dé
--  cuenta hasta que alguien no puede trabajar. Estas pruebas son el
--  contrapeso de ataques.sql: si un día se cierra de más, esto avisa.
-- =====================================================================

\echo ''
\echo '  Funcionalidad que SÍ tiene que andar'

-- --- El administrador general edita la ficha entera ------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'admin@test'), false); end $ident$;
set role authenticated;
update public.correcciones
   set nombre = 'Consulta NUEVA', norma = '{"txt":"Res. 9/2026"}'
 where codigo = '420101';
reset role;
do $$ begin
  if (select nombre from public.correcciones where codigo = '420101') <> 'Consulta NUEVA' then
    raise exception 'REG: el administrador no pudo editar la ficha.';
  end if;
end $$;
\echo '   ok  el administrador edita la ficha completa'

-- --- El médico administrador firma la revisión médica ----------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'medico@test'), false); end $ident$;
set role authenticated;
update public.correcciones
   set datos = '{"revision_medica":{"ok":true}}'::jsonb
 where codigo = '420101';
reset role;
do $$ begin
  if (select datos -> 'revision_medica' ->> 'ok' from public.correcciones where codigo = '420101') is distinct from 'true' then
    raise exception 'REG: el médico administrador no pudo firmar la revisión médica.';
  end if;
  -- y sin pisar la ficha, que es el límite de su rol
  if (select nombre from public.correcciones where codigo = '420101') <> 'Consulta NUEVA' then
    raise exception 'REG: el médico administrador pisó la denominación de la ficha.';
  end if;
end $$;
\echo '   ok  el médico administrador firma lo médico y no toca la ficha'

-- --- El médico administrador agrega/quita relaciones (árbol de módulos) ---
-- Mismo código, misma corrección: la fila ya trae datos.revision_medica de
-- la prueba anterior. Escribir sólo «relaciones» no puede vaciarla —el
-- descuido que arregla supabase_relaciones_medico.sql— ni la ficha.
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'medico@test'), false); end $ident$;
set role authenticated;
update public.correcciones
   set datos = datos || '{"relaciones":{"incluye":{"agregar":["420102"],"quitar":[]}}}'::jsonb
 where codigo = '420101';
reset role;
do $$ begin
  if (select datos -> 'relaciones' -> 'incluye' -> 'agregar' from public.correcciones where codigo = '420101')
       is distinct from '["420102"]'::jsonb then
    raise exception 'REG: el médico administrador no pudo agregar una relación.';
  end if;
  if (select datos -> 'revision_medica' ->> 'ok' from public.correcciones where codigo = '420101') is distinct from 'true' then
    raise exception 'REG: guardar una relación borró la revisión médica ya firmada.';
  end if;
  if (select nombre from public.correcciones where codigo = '420101') <> 'Consulta NUEVA' then
    raise exception 'REG: el médico administrador pisó la ficha al guardar una relación.';
  end if;
end $$;

-- Y a la inversa: volver a firmar lo médico no puede vaciar la relación que
-- se acaba de guardar.
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'medico@test'), false); end $ident$;
set role authenticated;
update public.correcciones
   set datos = datos || '{"revision_medica":{"ok":true,"nota":"reconfirmado"}}'::jsonb
 where codigo = '420101';
reset role;
do $$ begin
  if (select datos -> 'relaciones' -> 'incluye' -> 'agregar' from public.correcciones where codigo = '420101')
       is distinct from '["420102"]'::jsonb then
    raise exception 'REG: volver a firmar la revisión médica borró la relación ya guardada.';
  end if;
end $$;
\echo '   ok  el médico administrador agrega relaciones sin perder lo ya guardado, ni tocar la ficha'

-- --- Un administrativo activo lee el contenido del equipo ------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'user@test'), false); end $ident$;
set role authenticated;
do $$ begin
  if (select count(*) from public.correcciones)  = 0 then raise exception 'REG: un usuario activo no lee las correcciones.';  end if;
  if (select count(*) from public.observaciones) = 0 then raise exception 'REG: un usuario activo no lee las observaciones.'; end if;
  if (select count(*) from public.perfiles where id = auth.uid() and notas::text <> '{}') = 0 then
    raise exception 'REG: un usuario activo no lee sus propias notas.';
  end if;
  if (select count(*) from public.equipo()) <> 4 then
    raise exception 'REG: equipo() no devuelve las 4 cuentas (devolvió %).',
                    (select count(*) from public.equipo());
  end if;
end $$;
reset role;
\echo '   ok  el equipo lee el contenido compartido y sus propias notas'

-- --- equipo() no devuelve columnas personales -----------------------
do $$
declare cols text;
begin
  select coalesce(string_agg(p.parameter_name, ', '), '') into cols
    from information_schema.parameters p
    join information_schema.routines r
      on r.specific_name = p.specific_name and r.specific_schema = p.specific_schema
   where r.routine_schema = 'public' and r.routine_name = 'equipo'
     and p.parameter_name in ('notas', 'favoritos', 'recientes', 'ub');
  if cols <> '' then
    raise exception 'REG: equipo() devuelve columnas personales: %', cols;
  end if;
end $$;
\echo '   ok  equipo() no expone notas, favoritos ni U.B.'

-- --- Una cuenta pendiente no ve nada del equipo ----------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'pend@test'), false); end $ident$;
set role authenticated;
do $$ begin
  if (select count(*) from public.correcciones) > 0 then raise exception 'REG: una cuenta pendiente lee las correcciones.'; end if;
  if (select count(*) from public.equipo()) <> 1      then raise exception 'REG: una cuenta pendiente ve más que su propia fila.'; end if;
end $$;
reset role;
\echo '   ok  la cuenta pendiente sigue aislada'

-- --- Pedir y validar una verificación --------------------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'user@test'), false); end $ident$;
set role authenticated;
do $call$ begin perform public.pedir_verificacion('420101'); end $call$;
reset role;
do $$ begin
  if (select estado from public.verificaciones where codigo = '420101') <> 'pendiente' then
    raise exception 'REG: pedir_verificacion() no dejó el pedido pendiente.';
  end if;
end $$;

do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'admin@test'), false); end $ident$;
set role authenticated;
do $call$ begin perform public.validar_verificacion('420101'); end $call$;
reset role;
do $$ begin
  if (select estado from public.verificaciones where codigo = '420101') <> 'validada' then
    raise exception 'REG: el administrador no pudo validar la verificación.';
  end if;
end $$;
\echo '   ok  pedir y validar una verificación'

-- --- Nadie se asciende solo ------------------------------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'user@test'), false); end $ident$;
set role authenticated;
update public.perfiles set rol = 'admin', estado = 'activo' where id = auth.uid();
do $$ begin
  if (select rol from public.perfiles where id = auth.uid()) <> 'usuario' then
    raise exception 'REG: un usuario se pudo ascender a administrador solo.';
  end if;
end $$;
reset role;
\echo '   ok  nadie se cambia el rol a sí mismo'

-- --- La campana contesta a cada rol lo suyo --------------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'admin@test'), false); end $ident$;
set role authenticated;
do $$ begin
  if (public.pendientes() ->> 'cuentas')::int <> 1 then
    raise exception 'REG: pendientes() no cuenta la cuenta sin aprobar (dio %).',
                    (public.pendientes() ->> 'cuentas');
  end if;
end $$;
reset role;
\echo '   ok  pendientes() informa las cuentas por aprobar'

-- --- La auditoría registra lo que tiene que registrar -----------------
-- El caso que motivó todo esto: una baja no dejaba ningún rastro. Ahora
-- tiene que quedar quién la hizo y qué decía la fila antes de irse.
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'admin@test'), false); end $ident$;
set role authenticated;
delete from public.correcciones where codigo = '420101';
reset role;
do $$
declare r record;
begin
  select * into r from public.auditoria
   where tabla = 'correcciones' and operacion = 'baja' and clave = '420101'
   order by id desc limit 1;
  if r is null then
    raise exception 'REG: borrar una corrección no dejó rastro en la auditoría.';
  end if;
  if r.quien_nombre <> 'Admin General' then
    raise exception 'REG: la auditoría no atribuyó la baja a quien la hizo (dice «%»).', r.quien_nombre;
  end if;
  if r.antes ->> 'nombre' is null then
    raise exception 'REG: la auditoría no guardó qué decía la corrección antes de borrarse.';
  end if;
end $$;
\echo '   ok  la auditoría registra las bajas con autor y contenido'

-- --- El Intérprete de orden puede sugerir, y el administrador revisar ---
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'user@test'), false); end $ident$;
set role authenticated;
insert into public.sugerencias_pedida_como (codigo, texto, autor)
  select '340301', 'rx torax f y p', id from public.perfiles where nombre = 'Administrativo';
reset role;
do $$
declare n int;
begin
  select count(*) into n from public.sugerencias_pedida_como where codigo = '340301';
  if n <> 1 then
    raise exception 'REG: la sugerencia recién insertada no quedó guardada.';
  end if;
end $$;

do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select id::text from public.perfiles where nombre = 'Admin General'), false); end $ident$;
set role authenticated;
do $$
declare n int;
begin
  -- La sembrada en datos.sql (código 420101) + la que se acaba de insertar.
  select count(*) into n from public.sugerencias_pedida_como where estado = 'pendiente';
  if n < 2 then
    raise exception 'REG: el administrador debería ver las sugerencias pendientes (vio %).', n;
  end if;
end $$;
update public.sugerencias_pedida_como set estado = 'aprobada', resuelta_por = auth.uid(), resuelta_en = now()
 where codigo = '340301';
reset role;
do $$
declare r record;
begin
  select * into r from public.sugerencias_pedida_como where codigo = '340301';
  if r.estado <> 'aprobada' or r.resuelta_por is null then
    raise exception 'REG: el administrador no pudo resolver la sugerencia.';
  end if;
end $$;
\echo '   ok  el Intérprete de orden puede sugerir, y el administrador revisar'
