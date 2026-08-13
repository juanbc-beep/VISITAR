-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  MIGRACIÓN: «Qué abarca este código» lo escriben los médicos
--
--  Se corre UNA VEZ en el SQL Editor, después de las anteriores.
--  Es idempotente. NO agrega tablas ni columnas.
--
--  ---------------------------------------------------------------------
--  QUÉ CAMBIA
--  ---------------------------------------------------------------------
--  «Qué abarca este código» —«primera exposición», «tres posiciones,
--  comparativas», «mínimo 3 placas»— viene del Nomenclador Nacional con la
--  transcripción dañada, y hasta ahora era sólo lectura. Es el dato que
--  decide si hay que cargar un código más, y quien sabe si el texto está
--  bien es un médico. Ahora lo pueden corregir.
--
--  Vive en correcciones.datos->'abarca', al lado de 'revision_medica': el
--  mismo jsonb libre que ya se usa, cero cambios de esquema.
--
--  ---------------------------------------------------------------------
--  DOS NIVELES, NO UNO
--  ---------------------------------------------------------------------
--  El médico administrativo entra a «correcciones» por primera vez, y hay
--  que tener cuidado con eso: si se le abriera la fila entera podría
--  publicar una revisión médica sin que nadie la valide, que es justo lo
--  que el circuito evita. El guardia distingue:
--
--    médico administrador  → 'revision_medica' Y 'abarca'
--    médico administrativo → SÓLO 'abarca'
--    administrador general → todo, como siempre
--
--  Todo lo demás —denominación, norma, auditoría, nota de asociación— se
--  revierte igual que antes para los dos.
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. EL GUARDIA, CON LOS DOS NIVELES
-- ---------------------------------------------------------------------
create or replace function public.correcciones_guardia() returns trigger
  language plpgsql security definer set search_path = public as $$
declare
  viejo public.correcciones%rowtype;
  base  jsonb;
begin
  if public.es_admin() then
    return new;                                   -- el dueño del manual, sin límite
  end if;
  if not public.es_medico() then
    raise exception 'Sólo el administrador o un médico pueden tocar las correcciones.';
  end if;

  select * into viejo from public.correcciones where codigo = new.codigo;

  -- Los campos de la ficha se conservan como estaban, para los dos roles.
  new.nombre     := viejo.nombre;
  new.norma      := viejo.norma;
  new.auditoria  := viejo.auditoria;
  new.asoc_extra := viejo.asoc_extra;

  base := coalesce(viejo.datos, '{}'::jsonb);

  -- «abarca» lo puede escribir cualquiera de los dos roles médicos.
  base := base || jsonb_build_object('abarca',
            coalesce(new.datos -> 'abarca', 'null'::jsonb));

  -- La revisión médica, SÓLO el que valida. Para el médico administrativo se
  -- conserva la que había: su aporte viaja por «propuestas» y lo confirma un
  -- médico administrador, que es el circuito que este trigger no puede dejar
  -- que se saltee.
  if public.es_medico_admin() then
    base := base || jsonb_build_object('revision_medica',
              coalesce(new.datos -> 'revision_medica', 'null'::jsonb));
  else
    base := base || jsonb_build_object('revision_medica',
              coalesce(viejo.datos -> 'revision_medica', 'null'::jsonb));
  end if;

  new.datos := base;
  return new;
end $$;

drop trigger if exists correcciones_limite_medico on public.correcciones;
create trigger correcciones_limite_medico
  before insert or update on public.correcciones
  for each row execute function public.correcciones_guardia();

-- ---------------------------------------------------------------------
-- 2. LA POLICY SE ABRE A LOS DOS ROLES MÉDICOS
--    Lo que cada uno puede cambiar de verdad lo acota el trigger de arriba.
-- ---------------------------------------------------------------------
drop policy if exists correcciones_escribir on public.correcciones;
create policy correcciones_escribir on public.correcciones for all to authenticated
  using (public.es_admin() or public.es_medico())
  with check (public.es_admin() or public.es_medico());

-- Borrar una corrección sigue siendo del administrador general solamente.
--
-- ⚠️ Y esto tiene que ser RESTRICTIVE, no una policy más. Las policies
-- permisivas se SUMAN (OR): una segunda policy de delete «sólo es_admin()» no
-- le quita nada al FOR ALL de arriba, y el médico borraba igual. Se probó
-- contra PostgreSQL 16 antes de escribirlo, y así fue como salió: el médico
-- administrador borró la fila entera. Las restrictivas se multiplican (AND),
-- que es lo que hace falta acá.
drop policy if exists correcciones_borrar on public.correcciones;
drop policy if exists correcciones_borrar_solo_admin on public.correcciones;
create policy correcciones_borrar_solo_admin on public.correcciones
  as restrictive for delete to authenticated
  using (public.es_admin());

commit;

-- =====================================================================
--  COMPROBAR
--    Entrando como médico administrativo, intentar cambiar la denominación:
--    la fila entra pero el nombre vuelve al anterior y sólo queda «abarca».
--    Y su intento de escribir 'revision_medica' no sobrevive.
-- =====================================================================
