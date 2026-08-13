-- =====================================================================
--  COMPROBACIÓN de supabase_consultas_medicas.sql (migración 04)
--
--  Se pega en una query nueva del SQL Editor y se corre. No escribe nada:
--  son todas consultas de lectura. Devuelve una tabla de dos columnas —qué
--  se comprobó y cómo salió— con OK o FALTA en cada renglón.
-- =====================================================================

select * from (

  -- 1. La columna existe, es text, no acepta nulos y viene con 'carga' puesto.
  select 1 as n, '1. Columna «tipo» en propuestas' as comprobacion,
    coalesce((
      select case
        when c.data_type = 'text' and c.is_nullable = 'NO'
             and c.column_default like '%carga%'
        then 'OK — text, not null, por defecto ''carga'''
        else 'REVISAR — existe pero distinta: ' || c.data_type ||
             ', nullable=' || c.is_nullable ||
             ', default=' || coalesce(c.column_default,'(ninguno)')
      end
      from information_schema.columns c
      where c.table_schema='public' and c.table_name='propuestas' and c.column_name='tipo'
    ), 'FALTA — la migración 04 no se corrió') as resultado

  union all
  -- 2. El CHECK que sólo deja pasar los dos valores.
  select 2, '2. CHECK de valores permitidos',
    coalesce((
      select 'OK — ' || pg_get_constraintdef(oid)
      from pg_constraint
      where conrelid='public.propuestas'::regclass and conname='propuestas_tipo_check'
    ), 'FALTA — sin restricción: se podría guardar cualquier texto')

  union all
  -- 3. Lo que ya estaba cargado tiene que haber quedado como 'carga'.
  --    Se lee por to_jsonb y no nombrando la columna: si la migración no se
  --    corrió, «where tipo = …» ni siquiera deja arrancar la consulta y el
  --    informe entero muere con un error en vez de decir qué falta.
  select 3, '3. Filas que ya existían',
    case
      when not exists (select 1 from public.propuestas) then 'OK — no hay propuestas todavía'
      when exists (select 1 from public.propuestas p where (to_jsonb(p) ->> 'tipo') is null)
        then 'REVISAR — hay filas sin tipo'
      else 'OK — ' || (select count(*) from public.propuestas p
                        where to_jsonb(p) ->> 'tipo' = 'carga')::text ||
           ' de carga · ' || (select count(*) from public.propuestas p
                        where to_jsonb(p) ->> 'tipo' = 'consulta')::text ||
           ' consultas'
    end

  union all
  -- 4. La regla que deja al médico administrador cerrar las consultas.
  select 4, '4. Policy prop_resolver actualizada',
    coalesce((
      select case when qual::text like '%consulta%'
             then 'OK — contempla las consultas'
             else 'REVISAR — existe pero sin el caso de consulta' end
      from pg_policies
      where schemaname='public' and tablename='propuestas' and policyname='prop_resolver'
    ), 'FALTA — no existe la policy prop_resolver')

  union all
  -- 5. El índice de consultas pendientes (rendimiento, no seguridad).
  select 5, '5. Índice de consultas pendientes',
    coalesce((select 'OK — ' || indexname from pg_indexes
      where schemaname='public' and indexname='propuestas_consultas'),
      'FALTA — anda igual, sólo que sin índice')

  union all
  -- 6. La función de la campana devuelve la clave nueva.
  select 6, '6. pendientes() devuelve «medicas»',
    -- pendientes() devuelve json (no jsonb), que no tiene el operador «?».
    case when (public.pendientes())::jsonb ? 'medicas'
      then 'OK — claves: ' || (select string_agg(k, ', ' order by k)
                                 from jsonb_object_keys((public.pendientes())::jsonb) k)
      else 'FALTA — la función quedó vieja' end

  union all
  -- 7. Que anon no pueda llamarla (viene de la migración 03).
  select 7, '7. pendientes() cerrada a anon',
    case when has_function_privilege('anon','public.pendientes()','execute')
      then 'REVISAR — anon la puede ejecutar'
      else 'OK — anon no la puede ejecutar' end

) t order by n;
