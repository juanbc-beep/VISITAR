-- =====================================================================
--  Manual Inteligente — VISITAR SRL
--  MIGRACIÓN: sugerencias de "pedida como" desde el Intérprete de orden
--
--  Se corre UNA VEZ, en el SQL Editor del panel de Supabase, con la cuenta
--  dueña del proyecto. No borra nada y se puede correr de nuevo sin romper:
--  todo está escrito para ser idempotente.
--
--  ---------------------------------------------------------------------
--  QUÉ RESUELVE
--  ---------------------------------------------------------------------
--  El Intérprete de orden (web/index.html) busca cada renglón pegado con el
--  mismo motor que el buscador principal, y muestra hasta 5 candidatos. Si
--  la persona elige uno que NO es el primero —el que el motor cree más
--  probable— es señal de que el renglón está escrito de una forma que el
--  buscador no reconoce bien. Esta tabla guarda esa señal (código elegido +
--  texto del renglón) para que el administrador la revise y, si corresponde,
--  la sume a "pedida_como" del código — el mismo campo que ya se puede
--  editar a mano desde ✎ Editar ficha. Así el buscador y el Intérprete
--  mejoran solos con el uso real, sin tocar código de nuevo.
--
--  No es un IA ni manda nada a un tercero: es texto que ya escribió alguien
--  del equipo, guardado en la propia base, revisado por una persona antes
--  de aplicarse — mismo criterio que "propuestas" (cómo se carga esta
--  práctica).
--
--  ---------------------------------------------------------------------
--  QUÉ CAMBIA, EXACTAMENTE
--  ---------------------------------------------------------------------
--  Una tabla nueva, "sugerencias_pedida_como", con el mismo patrón de RLS
--  que "propuestas": cualquier cuenta activa puede insertar la suya, sólo
--  el administrador general la ve, la resuelve o la borra. A diferencia de
--  "propuestas" (visible a todo el equipo, porque son notas de "cómo se
--  carga" que le sirven a cualquiera), acá el SELECT queda restringido al
--  administrador: es texto suelto de una orden pegada, no una nota
--  pensada para publicarse, y no aporta nada a nadie más verla antes de
--  que el administrador decida si corresponde sumarla.
-- =====================================================================

begin;

create table if not exists public.sugerencias_pedida_como (
  id           uuid primary key default gen_random_uuid(),
  codigo       text not null,
  texto        text not null,
  estado       text not null default 'pendiente' check (estado in ('pendiente','aprobada','descartada')),
  autor        uuid references public.perfiles(id) on delete set null,
  creada       timestamptz not null default now(),
  resuelta_por uuid references public.perfiles(id) on delete set null,
  resuelta_en  timestamptz
);
create index if not exists sugpc_pendientes on public.sugerencias_pedida_como (estado) where estado = 'pendiente';

alter table public.sugerencias_pedida_como enable row level security;

drop policy if exists sugpc_ver on public.sugerencias_pedida_como;
create policy sugpc_ver on public.sugerencias_pedida_como for select to authenticated
  using (public.es_admin());

drop policy if exists sugpc_crear on public.sugerencias_pedida_como;
create policy sugpc_crear on public.sugerencias_pedida_como for insert to authenticated
  with check (public.es_activo() and estado = 'pendiente' and autor = auth.uid());

drop policy if exists sugpc_resolver on public.sugerencias_pedida_como;
create policy sugpc_resolver on public.sugerencias_pedida_como for update to authenticated
  using (public.es_admin()) with check (public.es_admin());

drop policy if exists sugpc_borrar on public.sugerencias_pedida_como;
create policy sugpc_borrar on public.sugerencias_pedida_como for delete to authenticated
  using (public.es_admin());

commit;

-- =====================================================================
--  DESPUÉS DE CORRER ESTO
--
--  La pestaña "Sugerencias" del panel de Administración (sólo la ve el
--  administrador general) lista las pendientes; "Agregar" la suma a
--  "pedida_como" del código (vía la misma corrección que usa ✎ Editar
--  ficha) y la marca aprobada; "Descartar" la marca descartada sin tocar
--  la ficha. Ninguna de las dos borra la fila: queda el registro de qué se
--  decidió y cuándo, igual que con "propuestas".
--
--  No queda enganchada al contador de "Pendientes" de la barra superior
--  (verificaciones + propuestas + cuentas): es deliberado, para no sumar
--  otro cambio a esa función compartida en la misma tanda — se puede sumar
--  después si hace falta.
-- =====================================================================
