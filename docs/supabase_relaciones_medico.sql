-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  MIGRACIÓN: el médico administrador puede tocar las relaciones entre
--  códigos (árbol de módulos)
--
--  Se corre UNA VEZ, en el SQL Editor del panel de Supabase, con la cuenta
--  dueña del proyecto. No borra nada y se puede correr de nuevo sin romper:
--  todo está escrito para ser idempotente.
--
--  ---------------------------------------------------------------------
--  POR QUÉ HACE FALTA UNA MIGRACIÓN Y NO ALCANZA CON LA APP
--  ---------------------------------------------------------------------
--  «correcciones_guardia()» ya deja pasar UNA sola cosa cuando quien
--  escribe es médico administrador: «datos->'revision_medica'». Todo lo
--  demás —incluida cualquier otra clave que se le agregue a «datos»— vuelve
--  al valor anterior del lado del servidor. Es la barrera real: la clave
--  publicable es pública por diseño, así que un botón nuevo dibujado sólo
--  en el navegador no alcanza —lo mismo que ya está dicho en
--  supabase_roles_medicos.sql para los cuatro roles.
--
--  Sin este archivo, el botón «Editar relaciones» que ve el médico
--  administrador GUARDA sin error (la policy ya le permite insert/update
--  sobre «correcciones») pero el guardia descarta el cambio en silencio: la
--  ficha vuelve a mostrar la lista de antes en el siguiente
--  cargarContenidoNube(). Es justo la clase de falla que advierte
--  tests/rls/LEEME.md — no rompe nada visible, así que hace falta la prueba
--  para que se note.
--
--  ---------------------------------------------------------------------
--  QUÉ CAMBIA, EXACTAMENTE
--  ---------------------------------------------------------------------
--  Ninguna tabla nueva, ninguna columna nueva. Una sola función se
--  reemplaza: «correcciones_guardia()» deja pasar una clave más,
--  «datos->'relaciones'», con el mismo criterio que ya regía para
--  «revision_medica». El resto de la ficha —nombre, norma, auditoría,
--  nota de asociación— sigue reservado al administrador general.
--
--  De paso se corrige un descuido del guardia original: si una escritura
--  no traía «revision_medica» (algo que hoy no pasa —el único llamado del
--  médico administrador siempre la incluye— pero que este archivo
--  justamente habilita al agregar un segundo llamado que no la toca), el
--  guardia la reemplazaba por null en vez de conservar la que ya había.
--  Las dos claves ahora se conservan del valor anterior cuando la
--  escritura no las trae, y se reemplazan cuando sí las trae —incluido con
--  «null» a propósito, para poder borrar una revisión médica o vaciar las
--  relaciones sin tocar la otra.
-- =====================================================================

begin;

create or replace function public.correcciones_guardia() returns trigger
  language plpgsql security definer set search_path = public as $$
declare viejo public.correcciones%rowtype;
begin
  if public.es_admin() then
    return new;
  end if;
  if not public.es_medico_admin() then
    raise exception 'Sólo el administrador o un médico administrador pueden tocar las correcciones.';
  end if;
  -- La clave no se puede mover: ver CN-004 en tests/rls/ataques.sql.
  if tg_op = 'UPDATE' then
    new.codigo := old.codigo;
    select * into viejo from public.correcciones where codigo = old.codigo;
  else
    select * into viejo from public.correcciones where codigo = new.codigo;
  end if;

  new.nombre     := viejo.nombre;
  new.norma      := viejo.norma;
  new.auditoria  := viejo.auditoria;
  new.asoc_extra := viejo.asoc_extra;
  new.datos := coalesce(viejo.datos, '{}'::jsonb)
               || jsonb_build_object(
                    'revision_medica',
                    coalesce(new.datos -> 'revision_medica', viejo.datos -> 'revision_medica', 'null'::jsonb),
                    'relaciones',
                    coalesce(new.datos -> 'relaciones', viejo.datos -> 'relaciones', 'null'::jsonb));
  return new;
end $$;

commit;

-- =====================================================================
--  DESPUÉS DE CORRER ESTO
--
--  «datos->'relaciones'» queda con esta forma (la arma la app; acá sólo se
--  documenta para quien lea el registro de auditoría desde el SQL Editor):
--
--    {"incluye":      {"agregar": ["660102"], "quitar": []},
--     "no_incluye":   {"agregar": [], "quitar": ["660103"]},
--     "incluido_en":  {"agregar": [], "quitar": []}}
--
--  Son AGREGAR/QUITAR sobre la lista original del pipeline, no un
--  reemplazo — igual que correcciones_curadas.json en el resto de la app:
--  si un capítulo se vuelve a barrer y la lista base cambia, la curada no
--  la pisa entera, sólo aplica el agregado/quitado a mano.
-- =====================================================================
