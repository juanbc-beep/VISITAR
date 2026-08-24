# Pruebas de interfaz (Playwright + simulador de Supabase)

Hasta ahora esto se armaba a mano en cada sesión de Claude Code, en el
scratchpad, y se perdía al terminar (ver `HANDOFF.md`, sección de Testing).
Cada sesión nueva volvía a explicar el mismo simulador de Supabase, los
mismos siete u ocho escenarios, y corría el riesgo de reconstruirlos un poco
distinto. Esto lo deja versionado, para correr siempre igual y poder sumar
casos sin repetir la base.

## Qué prueba, y qué NO prueba

Esto prueba que la **interfaz** hace lo correcto — que entra quien tiene que
entrar, que lo que publica un administrador lo ve el resto, que la app no se
rompe sin la nube configurada. **No** prueba las reglas de acceso (RLS): eso
es `tests/rls/`, contra un PostgreSQL de verdad. El simulador de acá
(`simulador.mjs`) es permisivo a propósito — no reproduce quién puede hacer
qué, asume que el servidor ya cumple sus reglas.

## Casos cubiertos hoy

| Caso | Qué prueba |
|---|---|
| `casos/login.mjs` | Entrar con la cuenta correcta; contraseña equivocada; cuenta pendiente; cuenta rechazada. Sin violaciones de CSP en ninguno de los cuatro. |
| `casos/nubelocal.mjs` | Sin `NBU_NUBE` configurado, la app arranca en modo local (acceso de empresa) en vez de romperse, y ese flujo de alta funciona de punta a punta. |
| `casos/favs.mjs` | La lista de favoritos que publica el administrador (`ajustes.contenido.equipo.favoritos`) llega a la pantalla de otra cuenta. Es la clase de bug que no se nota mirando la app: si algo rompe la lectura de ese JSON anidado, la solapa queda vacía en silencio. |

## Lo que falta (mismo patrón, agregar cuando haga falta)

De la lista original de `HANDOFF.md` quedan sin persistir: **simul** (dos
personas a la vez, avisos al administrador), **flujo3** (propuesta →
aprobación por el panel real), **fidelidad** (corrección que borra la norma
a propósito), **nube** (pestaña de estado), **recup**/**recup2**
(restablecer contraseña). El simulador ya tiene los endpoints de
`propuestas`, `correcciones` y `recover`/`user` que esos casos necesitan
(ver `simulador.mjs`) — arrancar un caso nuevo es replicar la forma de
`casos/favs.mjs`, no rehacer la base.

## Cómo correrlas

```bash
cd tests/e2e
npm install                 # trae Playwright a node_modules (no se versiona)
bash correr.sh
```

En este entorno de desarrollo los navegadores de Playwright ya están
pre-instalados en `/opt/pw-browsers` — por eso `package.json` fija la
versión exacta de `playwright` (no un rango `^`): si el `npm install` trae
una versión distinta a la de esos binarios, Chromium no arranca. En CI
(`.github/workflows/e2e.yml`) no hace falta ese cuidado: cada corrida instala
sus propios navegadores con `npx playwright install --with-deps chromium`.

Para correr un solo caso mientras se lo escribe: `node casos/login.mjs`.

## Piezas, y por qué están separadas así

- **`simulador.mjs`** — intercepta `https://gavfxnoigomxbteagneu.supabase.co/**`
  (la URL real, ya hardcodeada en `web/index.html`) y contesta en memoria.
  La identidad de cada pedido sale del token `Bearer`, nunca de un valor fijo:
  con un valor fijo, dos sesiones de la misma corrida (por ejemplo para
  simular dos personas a la vez) terminan viendo la misma identidad y la
  prueba miente sin fallar — es el error que ya está anotado en
  `HANDOFF.md` como el que no hay que repetir. La base (`db`) sí es
  compartida a propósito: así un test puede loguear dos cuentas distintas
  contra el mismo estado.
- **`arranque.mjs`** — servidor estático de `web/`, espera de arranque
  (`#boot`), salto del recorrido guiado, y captura de errores de JS/CSP.
  `nuevoContexto()` bloquea el service worker: el registro puede persistir
  entre corridas en este entorno de pruebas y su `controllerchange` recarga
  la página sola a los 600 ms (ver `web/index.html`, función `recargar()`) —
  correcto en producción, pero rompe cualquier test que no lo espere. No es
  lo que estos casos prueban.
- **`correr.sh`** — un puerto por caso (`casos/*.mjs` cada uno con el suyo),
  para que un service worker de una corrida no le sirva una copia vieja a la
  siguiente, y sigue corriendo los casos que quedan aunque uno falle.

## Si un caso falla

El mensaje dice qué se esperaba y qué pasó de verdad — mismo criterio que
`tests/rls/`. Si el cambio que lo rompió era intencional, hay que actualizar
el caso y decir por qué en el commit, no borrar la aserción.

## Agregar un caso nuevo

1. Copiar la forma de `casos/favs.mjs` (es el más corto).
2. Puerto propio, no usado por ningún otro caso.
3. Si necesita un endpoint que `simulador.mjs` todavía no tiene, agregarlo
   ahí — cualquier ruta no reconocida contesta 404 explícito con el método y
   la ruta, así un endpoint nuevo avisa fuerte en vez de colgarse en
   silencio.
