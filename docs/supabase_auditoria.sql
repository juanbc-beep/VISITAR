-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  RASTRO DE AUDITORÍA: quién cambió qué, y cuándo
--
--  Se corre UNA VEZ, en el SQL Editor del panel de Supabase. No borra nada
--  y se puede correr de nuevo sin romper: todo es idempotente.
--
--  ---------------------------------------------------------------------
--  POR QUÉ HACE FALTA
--  ---------------------------------------------------------------------
--  La app ya anotaba las ediciones, pero en «CONTENT.log», que vive en el
--  navegador de quien editó y se corta a 200 entradas. Es una nota
--  personal, no un registro: si esa persona limpia el navegador o trabaja
--  desde otra computadora, no queda nada. Y las BAJAS no dejaban rastro en
--  ningún lado.
--
--  Para un manual de facturación esto no es sólo seguridad. Cuando una
--  práctica se discute con una obra social, «quién cambió esta corrección
--  y cuándo» es parte de la respuesta.
--
--  ---------------------------------------------------------------------
--  QUÉ SE GUARDA, Y QUÉ NO
--  ---------------------------------------------------------------------
--  De «correcciones» y «observaciones» se guarda la fila entera: ese
--  contenido es justamente lo que se audita.
--
--  De «perfiles» se guardan SÓLO nombre, rol y estado. Las notas, los
--  favoritos y la U.B. son personales, y copiarlas acá volvería a
--  exponerlas por la puerta de atrás: cualquier cambio de perfil dejaría
--  una copia de las notas en una tabla que lee el administrador. Es el
--  mismo error que ya cerramos una vez.
--
--  Nadie puede escribir ni borrar en esta tabla desde la app, ni siquiera
--  el administrador: no hay policies de escritura y los permisos están
--  revocados. Sólo la escribe el trigger, y sólo se puede limpiar desde
--  el SQL Editor. Un registro que el interesado puede editar no sirve.
-- =====================================================================

begin;

create table if not exists public.auditoria (
  id           bigserial primary key,
  tabla        text        not null,
  operacion    text        not null check (operacion in ('alta','cambio','baja')),
  clave        text,
  quien        uuid,
  -- El nombre se guarda además del uuid a propósito: si la cuenta se borra
  -- más adelante, el uuid deja de decir nada y el registro se vuelve inútil.
  quien_nombre text,
  cuando       timestamptz not null default now(),
  antes        jsonb,
  despues      jsonb
);

comment on table public.auditoria is
  'Quién cambió qué y cuándo. La escribe sólo el trigger; no se edita desde la app.';

create index if not exists auditoria_cuando on public.auditoria (cuando desc);
create index if not exists auditoria_clave  on public.auditoria (tabla, clave);

-- ---------------------------------------------------------------------
-- EL TRIGGER
--
--    SECURITY DEFINER porque tiene que poder escribir el registro pase lo
--    que pase, incluso cuando quien provoca el cambio no tiene permiso de
--    escritura sobre «auditoria» —que es siempre, porque no lo tiene nadie.
-- ---------------------------------------------------------------------
create or replace function public.auditar() returns trigger
  language plpgsql security definer set search_path = public as $$
declare
  v_clave text;
  v_antes jsonb;
  v_despues jsonb;
  v_op text;
  v_nombre text;
begin
  v_op := case tg_op when 'INSERT' then 'alta' when 'UPDATE' then 'cambio' else 'baja' end;

  if tg_table_name = 'perfiles' then
    -- Sólo lo auditable. Las notas y los favoritos no entran acá.
    if tg_op <> 'INSERT' then
      v_antes := jsonb_build_object('nombre', old.nombre, 'rol', old.rol, 'estado', old.estado);
      v_clave := old.id::text;
    end if;
    if tg_op <> 'DELETE' then
      v_despues := jsonb_build_object('nombre', new.nombre, 'rol', new.rol, 'estado', new.estado);
      v_clave := new.id::text;
    end if;
    -- Un cambio que no toca ninguno de los tres campos (guardar un favorito,
    -- escribir una nota) no es un hecho auditable: no se registra.
    if tg_op = 'UPDATE' and v_antes = v_despues then
      return null;
    end if;
  else
    if tg_op <> 'INSERT' then
      v_antes := to_jsonb(old);
      v_clave := old.codigo;
    end if;
    if tg_op <> 'DELETE' then
      v_despues := to_jsonb(new);
      v_clave := new.codigo;
    end if;
  end if;

  select p.nombre into v_nombre from public.perfiles p where p.id = auth.uid();

  insert into public.auditoria (tabla, operacion, clave, quien, quien_nombre, antes, despues)
  values (tg_table_name, v_op, v_clave, auth.uid(),
          -- Sin sesión es porque se corrió desde el SQL Editor. Queda dicho.
          coalesce(v_nombre, 'consola de Supabase'),
          v_antes, v_despues);

  return null;   -- AFTER trigger: el valor de retorno se ignora
end $$;

drop trigger if exists auditar_correcciones  on public.correcciones;
create trigger auditar_correcciones  after insert or update or delete
  on public.correcciones  for each row execute function public.auditar();

drop trigger if exists auditar_observaciones on public.observaciones;
create trigger auditar_observaciones after insert or update or delete
  on public.observaciones for each row execute function public.auditar();

drop trigger if exists auditar_perfiles      on public.perfiles;
create trigger auditar_perfiles      after insert or update or delete
  on public.perfiles      for each row execute function public.auditar();

-- ---------------------------------------------------------------------
-- QUIÉN LO LEE
--
--    Lo lee el administrador general y nadie más. No hay policy de
--    insert, update ni delete: eso significa que por la API nadie escribe
--    ni borra, ni siquiera él. El trigger sí puede porque corre con los
--    permisos de quien lo definió.
--
--    Los permisos de tabla se revocan además de la policy. Con RLS
--    alcanzaría, pero ya nos pasó una vez que una tabla se quedara sin
--    RLS por un olvido: si eso volviera a pasar, esta segunda barrera
--    deja el registro intacto igual.
-- ---------------------------------------------------------------------
alter table public.auditoria enable row level security;

drop policy if exists auditoria_ver on public.auditoria;
create policy auditoria_ver on public.auditoria for select to authenticated
  using (public.es_admin());

revoke insert, update, delete, truncate on public.auditoria from authenticated, anon, public;

commit;

-- =====================================================================
--  DESPUÉS DE CORRER ESTO
--
--  Para ver el registro, desde el SQL Editor:
--
--    select cuando, tabla, operacion, clave, quien_nombre
--      from public.auditoria
--     order by cuando desc
--     limit 50;
--
--  Y para ver qué se borró exactamente:
--
--    select cuando, quien_nombre, antes
--      from public.auditoria
--     where operacion = 'baja'
--     order by cuando desc;
--
--  La tabla crece sola y nada la limpia. Con el uso de un equipo chico eso
--  tarda años en importar; si algún día molesta, se recortan las filas
--  viejas desde el SQL Editor, que es el único lugar desde donde se puede.
-- =====================================================================
