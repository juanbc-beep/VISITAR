-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  Cerrar los avisos «SECURITY DEFINER Function» del linter de Supabase
--
--  Se corre UNA VEZ en el SQL Editor, después de supabase_roles_medicos.sql.
--  Es idempotente.
--
--  ---------------------------------------------------------------------
--  ⚠️ NO SEGUIR EL CONSEJO DEL LINTER AL PIE DE LA LETRA
--  ---------------------------------------------------------------------
--  El aviso dice «Revoke EXECUTE». Hacer eso a secas DEJA LA APP AFUERA, y
--  no es una opinión: se probó contra PostgreSQL 16 antes de escribir esto.
--
--    revoke execute on function public.es_admin() from public, anon, authenticated;
--    → insert en «correcciones» siendo administrador:
--      ERROR: permission denied for function es_admin
--
--  El motivo es que una expresión de policy se evalúa con los permisos de
--  QUIEN HACE LA CONSULTA, no con los del dueño de la tabla. Si «authenticated»
--  pierde EXECUTE sobre es_admin(), toda policy que la use deja de poder
--  evaluarse y la escritura muere ahí. Es decir: el linter avisa de algo real,
--  pero su receta corta, aplicada entera, rompe el manual.
--
--  ---------------------------------------------------------------------
--  LO QUE SÍ CORRESPONDE, Y POR QUÉ
--  ---------------------------------------------------------------------
--  1. A «anon» (la clave publicable sin iniciar sesión) se le saca todo.
--     Hoy no hay agujero —cada una de estas funciones filtra por auth.uid(),
--     que para anon es NULL, así que todas devuelven falso—, pero que estén
--     expuestas es superficie que no hace falta.
--  2. A «authenticated» se le deja SÓLO lo que la app necesita de verdad:
--     las cinco de apoyo que usan las policies, y las cuatro que la app llama
--     por RPC. Ninguna otra.
--  3. Las funciones de TRIGGER se le sacan a todos. Un trigger NO comprueba
--     EXECUTE para dispararse —también probado: el guardia siguió recortando
--     la fila con el permiso revocado— así que revocarlas no cambia nada
--     salvo que ya no se las pueda llamar a mano desde la API.
--
--  Después de esto quedan en el linter las nueve que «authenticated» sí puede
--  ejecutar. Eso es correcto y se queda así: son las que hacen andar la app.
--  Un aviso que no se puede bajar enseña a ignorar la lista entera; éstos
--  quedan explicados acá para que el próximo que la mire no los persiga.
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. FUNCIONES DE TRIGGER — nadie las llama a mano, nunca
--    Se disparan solas al insertar o actualizar la fila. Que estén
--    accesibles por la API no habilita nada útil (llamarlas sueltas falla
--    con «trigger functions can only be called as triggers»), pero tampoco
--    tienen por qué estar.
-- ---------------------------------------------------------------------
revoke execute on function public.perfil_nuevo()          from public, anon, authenticated;
revoke execute on function public.perfil_guardia()        from public, anon, authenticated;
revoke execute on function public.un_solo_admin()         from public, anon, authenticated;
revoke execute on function public.correcciones_guardia()  from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- 2. FUNCIONES DE APOYO — las usan las policies
--    Se le sacan a anon; «authenticated» LAS NECESITA. Ver el aviso de
--    arriba: sin EXECUTE, la policy que las llama no puede evaluarse.
-- ---------------------------------------------------------------------
revoke execute on function public.es_activo()        from public, anon;
revoke execute on function public.es_admin()         from public, anon;
revoke execute on function public.es_medico()        from public, anon;
revoke execute on function public.es_medico_admin()  from public, anon;
revoke execute on function public.valida_medico()    from public, anon;

grant  execute on function public.es_activo()        to authenticated;
grant  execute on function public.es_admin()         to authenticated;
grant  execute on function public.es_medico()        to authenticated;
grant  execute on function public.es_medico_admin()  to authenticated;
grant  execute on function public.valida_medico()    to authenticated;

-- ---------------------------------------------------------------------
-- 3. LAS CUATRO QUE LA APP LLAMA POR RPC
--    Cada una comprueba por su cuenta quién es el que llama —transferir_admin
--    y validar_verificacion levantan excepción si no es el administrador— así
--    que dejarlas abiertas a «authenticated» es lo correcto: el control está
--    adentro, no en el permiso.
-- ---------------------------------------------------------------------
revoke execute on function public.pendientes()                   from public, anon;
revoke execute on function public.transferir_admin(uuid)         from public, anon;
revoke execute on function public.pedir_verificacion(text)       from public, anon;
revoke execute on function public.validar_verificacion(text)     from public, anon;

grant  execute on function public.pendientes()                   to authenticated;
grant  execute on function public.transferir_admin(uuid)         to authenticated;
grant  execute on function public.pedir_verificacion(text)       to authenticated;
grant  execute on function public.validar_verificacion(text)     to authenticated;

-- ---------------------------------------------------------------------
-- 4. QUE NO VUELVA A PASAR
--    PostgreSQL le da EXECUTE a PUBLIC en cada función nueva. Esto cambia el
--    valor por defecto para lo que se cree de acá en adelante en «public»,
--    así que la próxima función no nace abierta.
-- ---------------------------------------------------------------------
alter default privileges in schema public revoke execute on functions from public;

commit;

-- =====================================================================
--  PARA COMPROBAR QUE QUEDÓ BIEN
--
--    select p.proname,
--           has_function_privilege('anon',          p.oid, 'execute') as anon,
--           has_function_privilege('authenticated', p.oid, 'execute') as autenticado
--      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
--     where n.nspname = 'public'
--     order by 1;
--
--  Lo esperado: «anon» en false en TODAS. «autenticado» en true sólo en
--  es_activo, es_admin, es_medico, es_medico_admin, valida_medico,
--  pendientes, transferir_admin, pedir_verificacion y validar_verificacion.
--
--  Y probá la app: entrá como administrador y corregí una ficha. Si eso anda,
--  las policies siguen pudiendo evaluarse, que es lo único que este cambio
--  podía romper.
-- =====================================================================
