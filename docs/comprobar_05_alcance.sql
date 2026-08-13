-- =====================================================================
--  COMPROBACIÓN de supabase_alcance_medico.sql (migración 05)
--
--  Se pega en una query nueva del SQL Editor, DESPUÉS de correr la 05.
--  No escribe nada.
--
--  Esta migración es la más delicada de las cinco: le abre «correcciones»
--  al médico administrativo, que hasta ahora no la tocaba. Los renglones 3
--  y 4 son los que hay que mirar con atención — son los que impiden que
--  alguien publique una revisión médica sin que nadie la valide, y que un
--  médico borre una corrección de la ficha.
-- =====================================================================

select * from (

  -- 1. El guardia existe y quedó con los dos niveles.
  select 1 as n, '1. El guardia correcciones_guardia' as comprobacion,
    coalesce((
      select case
        when p.prosrc like '%abarca%' and p.prosrc like '%es_medico_admin%'
          then 'OK — distingue «abarca» de «revision_medica»'
        when p.prosrc like '%abarca%'
          then 'REVISAR — nombra abarca pero no separa por rol'
        else 'VIEJO — es el guardia anterior, sin «abarca»'
      end
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public' and p.proname='correcciones_guardia'
    ), 'FALTA — no existe la función') as resultado

  union all
  -- 2. Y está enganchado como trigger, que es lo que lo hace valer.
  select 2, '2. Enganchado a la tabla',
    coalesce((
      select 'OK — ' || tgname || ' (before insert or update)'
      from pg_trigger
      where tgrelid='public.correcciones'::regclass
        and tgname='correcciones_limite_medico' and not tgisinternal
    ), 'FALTA — la función está pero no se dispara con nada')

  union all
  -- 3. ⚠️ EL RENGLÓN IMPORTANTE. El borrado tiene que ser RESTRICTIVE.
  --    Con una policy permisiva no alcanza: las permisivas se suman con OR y
  --    el FOR ALL de escritura le seguiría dejando borrar la fila entera.
  select 3, '3. ⚠ Borrado cerrado al médico',
    coalesce((
      select case when permissive = 'RESTRICTIVE'
        then 'OK — restrictiva, se multiplica con la de escritura'
        else 'MAL — es PERMISSIVE: un médico puede BORRAR correcciones' end
      from pg_policies
      where schemaname='public' and tablename='correcciones'
        and cmd='DELETE' and qual::text like '%es_admin%'
    ), 'MAL — no hay ninguna restricción de borrado')

  union all
  -- 4. ⚠️ La escritura abierta a los dos roles médicos (el guardia acota).
  select 4, '4. Escritura abierta a los médicos',
    coalesce((
      -- Se busca «es_medico()» con los paréntesis a propósito: «es_medico_admin»
      -- contiene la cadena «es_medico», y con un LIKE suelto la policy vieja
      -- —la que sólo dejaba entrar al médico administrador— daba OK igual.
      select case when qual::text like '%es_medico()%'
        then 'OK — entran los dos roles médicos, el guardia los acota'
        else 'VIEJO — sólo admin y médico administrador' end
      from pg_policies
      where schemaname='public' and tablename='correcciones'
        and policyname='correcciones_escribir'
    ), 'FALTA — no existe correcciones_escribir')

  union all
  -- 5. Las funciones de apoyo que usa el guardia.
  select 5, '5. es_medico() y es_medico_admin()',
    case when (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
               where n.nspname='public' and p.proname in ('es_medico','es_medico_admin'))=2
      then 'OK — las dos existen'
      else 'FALTA — sin ellas el guardia no puede decidir' end

  union all
  -- 6. Que sigan cerradas a anon (viene de la migración 03).
  select 6, '6. Cerradas a anon',
    case when has_function_privilege('anon','public.es_medico()','execute')
           or has_function_privilege('anon','public.es_medico_admin()','execute')
      then 'REVISAR — anon puede ejecutar alguna'
      else 'OK — anon no las puede ejecutar' end

  union all
  -- 7. Cuántas fichas tienen ya alcance corregido por un médico.
  select 7, '7. Alcances ya corregidos',
    'OK — ' || (select count(*) from public.correcciones
                 where datos ? 'abarca' and datos->'abarca' <> 'null'::jsonb)::text ||
    ' ficha(s) con «qué abarca» corregido'

) t order by n;
