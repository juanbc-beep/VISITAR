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
  if (select count(*) from public.equipo) <> 4 then
    raise exception 'REG: la vista «equipo» no devuelve las 4 cuentas (devolvió %).',
                    (select count(*) from public.equipo);
  end if;
end $$;
reset role;
\echo '   ok  el equipo lee el contenido compartido y sus propias notas'

-- --- La vista «equipo» no filtra columnas personales -----------------
do $$
declare cols text;
begin
  select coalesce(string_agg(column_name, ', '), '') into cols
    from information_schema.columns
   where table_schema = 'public' and table_name = 'equipo'
     and column_name in ('notas', 'favoritos', 'recientes', 'ub');
  if cols <> '' then
    raise exception 'REG: la vista «equipo» expone columnas personales: %', cols;
  end if;
end $$;
\echo '   ok  la vista «equipo» no expone notas, favoritos ni U.B.'

-- --- Una cuenta pendiente no ve nada del equipo ----------------------
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select p.id::text from public.perfiles p
                     join auth.users u on u.id = p.id where u.email = 'pend@test'), false); end $ident$;
set role authenticated;
do $$ begin
  if (select count(*) from public.correcciones) > 0 then raise exception 'REG: una cuenta pendiente lee las correcciones.'; end if;
  if (select count(*) from public.equipo) <> 1      then raise exception 'REG: una cuenta pendiente ve más que su propia fila.'; end if;
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
