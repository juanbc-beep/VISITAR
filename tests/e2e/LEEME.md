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
| `casos/relaciones.mjs` | Editar las relaciones entre códigos (árbol de módulos) desde el menú de edición: el médico administrador ve sólo esos campos (no nombre/norma/auditoría), el administrador general ve la ficha completa, y el cambio se espeja en el otro código (`incluye` ↔ `incluido_en`). Ver HANDOFF.md 4.5 ter bis. |
| `casos/vincular.mjs` | Atajo «Vincular código» dentro de «Cómo se carga esta solicitud»: sólo aparece en Modo edición, agregar/quitar ahí se refleja en «No cargues aparte» de la misma sección y en el espejo (`incluido_en`) del otro código. |
| `casos/anexar.mjs` | Atajo «+ Anexar código» dentro de «Cargá esto»: sólo aparece en Modo edición, agregar/quitar ahí se refleja como paso más de «Cargá esto», sin tocar «No cargues aparte» y sin espejo en el otro código (a diferencia de vincular). |
| `casos/interprete.mjs` | Intérprete de orden médica: pegar el texto de la orden trae candidatos por renglón (incluido el caso de términos sueltos de 1-2 letras — «Rx torax f y p» — que necesitan el reintento de `candidatosParaItem()`), un renglón inventado no encuentra nada, elegir/quitar candidatos actualiza el resumen, y «Enviar a la Mesa de trabajo» lleva sólo lo elegido y corre el análisis. También: «Rx torax f y p» agrega 340302 (exposición de perfil) como candidato aparte —ligado a 340301 por `exposicion_siguiente`, no por texto— con su nota explicando de dónde sale. Ver HANDOFF.md, 26/8/2026. |
| `casos/busqueda_sinonimos.mjs` | La búsqueda tolerante trata «radiografía» y «radiología» como sinónimos cruzados: buscar cualquiera de las dos trae también los códigos de la sección que sólo dicen la otra (340301 «Radiología tórax» y 340905 «Radiografía en quirófano», que cada uno sólo trae una de las dos palabras). Ver HANDOFF.md, 26/8/2026. |
| `casos/busqueda_especificidad.mjs` | A igual puntaje de coincidencia, `buscar()` desempata por el nombre más corto (más específico), no por el orden en que el código entró a la base: «torax» solo trae primero 340301 «Radiología tórax» (2 palabras) y no 050102 «Operación plástica por tórax…» (8 palabras, cirugía, sin relación), aunque los dos empataran en puntaje antes de este cambio. Ver HANDOFF.md, 26/8/2026. |
| `casos/interprete_avisos.mjs` | El Intérprete avisa, antes de elegir un candidato: si la cantidad pedida (×N) supera el seriado habitual del código, qué implica la lateralidad (bilateral se carga ×1, no ×2) y si la orden nombra un tipo de muestra que no coincide con el del código — este último necesita que `candidatosParaItem()` también saque las palabras de muestra del reintento de búsqueda, igual que ya sacaba los sueltos de 1-2 letras, o el candidato ni aparecía. Ver HANDOFF.md, 26/8/2026. |
| `casos/notif_revision_medica.mjs` | Publicar una revisión médica (médico administrador) avisa al administrador general con la misma campanita de "novedades" que ya usan los administrativos — antes esa campanita le quedaba siempre oculta al administrador general. Ver HANDOFF.md, 26/8/2026. |
| `casos/config_busqueda.mjs` | El administrador general ajusta desde Administración → Búsqueda los valores de coincidencia (tolerancia a erratas, umbral de "coincidencia fuerte", pesos por tipo de coincidencia): se prueba contra el efecto real en la búsqueda (bajar la tolerancia de palabras largas a 0 hace que un término mal escrito deje de encontrar lo que antes encontraba por erratas), que los pesos cargados fuera de orden se reordenan solos al guardar, que persiste tras recargar, que "Restaurar valores de fábrica" vuelve todo atrás, y que un médico administrador no ve la pestaña. Ver HANDOFF.md, 26/8/2026. |
| `casos/coincidencia_forzada.mjs` | Desde ✎ Editar ficha, el administrador general fija que buscar exactamente una frase encuentre un código con 100% de coincidencia — caso real de la base: "urea" encuentra bien 660902 "UREA, sérica" (100%) pero U60660902 "Uremia" sólo llega por la equivalencia cruzada (33%), aunque sea la práctica correcta. Se prueba el antes/después real en el listado, que la propia ficha explica la coincidencia forzada, y que forzar "urea" no dispara con cualquier búsqueda que la contenga (sólo la frase exacta). Ver HANDOFF.md, 26/8/2026. |
| `casos/pedida_como.mjs` | El administrador general puede sumar, desde ✎ Editar ficha, formas en las que puede venir escrita una orden («Puede venir solicitada como»): lo que se agrega se puede buscar por ese texto, y un médico administrador que edita sólo las relaciones de la misma ficha no lo pisa. |
| `casos/sugerencias_pedida_como.mjs` | El Intérprete de orden aprende del uso real: elegir un candidato que no es el primero avisa al administrador (Administración → Sugerencias), que puede sumarlo a «pedida_como» del código con un clic. |
| `casos/mfa.mjs` | Verificación en dos pasos (TOTP) del administrador general: alta propia desde «Tu cuenta» (rechaza un código incorrecto antes de aceptar el bueno) confía el dispositivo desde el que se activa; «dejar de confiar» y el checkbox del login («confiar en este dispositivo») controlan si el próximo login pide el código; desactivarla del todo vuelve a dejar entrar sólo con contraseña; un dispositivo distinto (otro `BrowserContext`, misma cuenta) no hereda la confianza de otro; un factor sin verificar de un alta anterior (`dejarFactorPendiente()`) no bloquea el siguiente intento — bug real de producción del 25/8/2026, ver HANDOFF.md; y el candado no se le pide a otro rol. El simulador no hace TOTP de verdad — acepta un único código fijo como «correcto» (ver `MFA_CODE_OK` en `simulador.mjs`) y rechaza el alta con el mismo error de la API real si ya existe un factor con ese nombre. |
| `casos/sesion_muerta.mjs` | Si el access token y el refresh token mueren del lado del servidor (sesión revocada, o vencimiento propio de Supabase) sin que la app haga nada raro, `NUBE.api()` corta y cierra la sesión de una — vuelve al login con el aviso puesto, en vez de seguir llamando a la API con la clave pública (anon) como si fuera el usuario. Bug real de producción del 26/8/2026 (ver HANDOFF.md): antes esto quedaba en los logs de Postgres como «permission denied», en silencio, cada vez que corría el sondeo de fondo cada 60s. |
| `casos/editar_propuesta.mjs` | El administrador puede corregir el texto de una propuesta («Contá cómo se carga acá») antes de aprobarla, en el panel Administración → Pendientes: «Guardar cambios» persiste la corrección aparte (se puede aprobar después), y editar + «Aprobar» directo publica lo último que quedó escrito sin necesitar el paso de guardar. Las dos formas dejan la fila de la nube con el texto corregido, no el original. |
| `casos/historial_ficha.mjs` | El administrador general ve, desde la propia ficha («🕘 Ver historial», al lado de «✎ Editar ficha»), quién la corrigió, cuándo, y qué decía antes de cada cambio — sin haber tenido que construir una tabla nueva: `auditoria` (`docs/supabase.sql`) ya lo registraba todo solo, por un trigger, desde antes de que hubiera pantalla que lo mostrara. Cubre la primera corrección (un alta, sin «antes» que mostrar) y una segunda corrección sobre la misma ficha (con el valor anterior real), en orden del cambio más reciente al más viejo. |
| `casos/reintento_red.mjs` | Un corte de señal momentáneo al guardar (wifi de la oficina, un rato sin datos) se reintenta solo, con espera creciente, en vez de perder lo que se estaba guardando o mostrar un error de una — `hacerConReintento()` en `NUBE.api()`/`token()`. Se simula abortando la primera llamada a `/rest/v1/correcciones` con `route.abort('failed')` (mismo `TypeError` que un corte real) y dejando pasar el reintento al simulador de siempre. |

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
