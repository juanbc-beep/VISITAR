-- =====================================================================
--  Cuatro cuentas y algo de contenido, para tener contra qué probar.
--
--  Las cuatro cubren los cuatro estados que le importan a las reglas:
--  el dueño del manual, un médico administrador, un administrativo
--  habilitado y alguien recién registrado que todavía no fue aprobado.
--  Ese último es el más importante: es lo que puede ser cualquier persona
--  de internet, porque el registro es abierto.
-- =====================================================================

insert into auth.users (email, raw_user_meta_data) values
  ('admin@test',  '{"nombre":"Admin General"}'),
  ('medico@test', '{"nombre":"Medico Admin"}'),
  ('user@test',   '{"nombre":"Administrativo"}'),
  ('pend@test',   '{"nombre":"Recien Registrado"}');

do $call$ begin perform public.hacerme_admin('admin@test'); end $call$;
-- De acá en adelante actuamos COMO el administrador, para que los triggers
-- vean es_admin() = true, igual que cuando los cambios los hace la app.
-- Sin esto, «perfiles_guardia» revierte los roles en silencio: auth.uid()
-- sería NULL y es_admin() daría falso.
do $ident$ begin perform set_config('request.jwt.claim.sub',
                  (select id::text from public.perfiles where nombre = 'Admin General'),
                  false); end $ident$;

update public.perfiles set rol = 'medico_admin', estado = 'activo' where nombre = 'Medico Admin';
update public.perfiles set estado = 'activo'                       where nombre = 'Administrativo';
-- «Recien Registrado» queda pendiente, tal como lo deja el trigger de alta.

insert into public.correcciones (codigo, nombre, norma, auditoria, datos) values
  ('420101', 'Consulta médica', '{"txt":"Res. 1/2024"}', '{"linea":"requiere orden"}',
   '{"nombre":"Consulta médica"}');

insert into public.observaciones (codigo, texto) values
  ('420101', 'Pedir orden con diagnóstico.');

-- Una nota personal y una U.B., para comprobar que no las lee el resto.
update public.perfiles
   set notas = '{"420101":"nota privada"}'::jsonb, ub = 1250
 where nombre = 'Administrativo';

do $ident$ begin perform set_config('request.jwt.claim.sub', '', false); end $ident$;
