# TRASPASO DE SESIÓN — Manual Inteligente Unificado (VISITAR SRL)

> Documento para retomar el trabajo en una sesión nueva sobre **la misma app**.
> Última actualización: 2026-08-05 (commit `f66b55e`, 99 commits).
>
> **Lo más importante que cambió desde el traspaso anterior:** la app dejó de ser un
> archivo que cada uno guarda en su computadora y pasó a ser una **aplicación de empresa
> publicada, con cuentas reales y base compartida**. Si venís del HANDOFF viejo, leé
> primero la sección 1 bis: buena parte de lo que decía sobre acceso y sincronización
> ya no aplica.

---

## 1. Identificación del proyecto

| Dato | Valor |
|---|---|
| **Repo** | `juanbc-beep/VISITAR` (dir. de trabajo `/home/user/VISITAR`) |
| **Rama de desarrollo** | `claude/unified-medical-codes-manual-o9nw1w` (⚠️ NO pushear a otra rama) |
| **App en producción** | **https://juanbc-beep.github.io/VISITAR/** ← la que usa el equipo |
| **Base de datos** | Supabase, proyecto `gavfxnoigomxbteagneu` (South America / São Paulo) |
| **Artefacto** | https://claude.ai/code/artifact/85d149a9-9bfb-478b-b817-3d039a335f1f — **ya no se usa**, ver 1 bis |
| **Archivos de la app** | `web/index.html` (380 KB) + `web/nbu_db.bin` (776 KB, la base comprimida) |
| **Licencia** | `LICENSE` — reserva de derechos a nombre de Juan Pablo Besada / VISITAR SRL |
| **Usuario** | Experto en auditoría médica y facturación en VISITAR SRL |
| **Autoría a mostrar** | «Diseñado por **Juan Pablo Besada**» (ver punto 6.11) |
| **Idioma de trabajo** | Español (Argentina) |

---

## 1 bis. ⚠️ Cómo se entrega el trabajo ahora (cambió por completo)

**Publicar = hacer push.** La acción `.github/workflows/pages.yml` corre sola con cada
cambio en `web/**` y en menos de un minuto la versión nueva está en
`https://juanbc-beep.github.io/VISITAR/`. No hay que hacer nada más.

**El artefacto de Claude quedó fuera de uso.** No sirve para probar: el entorno de
claude.ai **bloquea todo pedido a servidores externos**, así que no puede hablar con
Supabase y **no se puede ni iniciar sesión**. El usuario perdió tiempo con esto. Si querés
mostrarle un cambio visual, mandale **capturas**; si querés que lo pruebe, que use la
dirección de producción.

**Sello de origen.** La acción escribe el commit que generó cada versión en
`window.NBU_BUILD`, visible en la app en **Administración → Nube**. Sirve para saber qué
está usando alguien cuando reporta un problema.

### Lo que el usuario tiene que hacer en Supabase (ya hecho, no repetir)
Documentado paso a paso en **`docs/INSTALACION.md`**. Resumen de lo que ya está
configurado: tablas y reglas (`docs/supabase.sql`), *Confirm email* **apagado**,
*Site URL* y *Redirect URLs* apuntando a la dirección de producción, y su cuenta promovida
a administrador con `select public.hacerme_admin('…')`.

---

## 2. Qué es la app — y para qué la usa el usuario

Un **manual inteligente unificado de códigos médicos argentinos**, que funciona **sin
internet** una vez instalado.

### ⚠️ Para qué NO es (aclarado explícitamente por el usuario)

**La carga de la autorización y la carga de facturación se hacen en OTROS sistemas.**
Esta app **no carga nada**. Es un **centro de respaldo** para que los agentes:

- verifiquen **códigos y prestaciones**,
- consulten **reglamentos y obligaciones de cobertura**,
- y sobre todo **entiendan cómo se carga cada solicitud** en el sistema de siempre.

El destinatario principal es el **usuario de carga / mostrador**, **no** el de facturación.
Toda mejora que se proponga tiene que medirse contra eso: ¿le resuelve una duda al agente
que tiene al afiliado enfrente? Si sólo sirve para auditar facturación, es secundaria.

### Contenido de la base (verificado contra `data/nbu_db.json`)

| Dataset | Cantidad |
|---|---|
| **Códigos totales** | **6.346** |
| — NBU (laboratorio/bioquímica) | 1.815 |
| — PMO / Prestaciones médicas | 1.221 |
| — Nomenclador Único (VISITAR) | 3.231 |
| — Odontología | 79 (**oculto en la app**, ver 6.12) |
| **CIE-10** (diagnósticos) | **11.581** en 21 capítulos |
| **Abreviaturas médicas** | **1.780** significados / 1.413 siglas únicas |
| **SURGE** (Res. 731/23) | **58** patologías del Anexo II · 38 códigos mapeados |
| **Leyes / normas** | 22 · Glosario 12 |

### Cruces / inteligencia construida

| Relación | Cobertura |
|---|---|
| Códigos con **abreviaturas posibles** | 1.044 |
| Códigos con **tipo de muestra** (sangre/orina) | 821 (705 por texto + 73 por sufijo + 43 heredados del gemelo del NBU) |
| Códigos con **diagnósticos CIE-10** relacionados | 242 |
| Códigos con **cobertura** | 115 → 106 *obligación* + 9 *observación* |
| Códigos con **lateralidad** | 130 (109 del OCR + 21 curados por auditoría) |
| Códigos con **normativa** relacionada | 61 |
| Códigos con **vínculo SURGE** | 60 |
| Códigos con **tope PMO** | 38 |
| Pares **-emia / -uria** vinculados | 26 |
| Único **sin equivalencia** (agrupados aparte) | 79 |
| Marcador del Único separado del título | 1.724 |
| Laboratorio del Único **emparejado con el NBU** (uno a uno) | 1.694 |
| **Marcas de calidad** | 84 `titulo_revisar` · 139 `texto_truncado` · 1 `sin_denominacion` |

---

## 3. Arquitectura y pipeline

### Estructura
```
/home/user/VISITAR
├── web/
│   ├── index.html                  # LA APP (código + estilos; la base va aparte)
│   ├── nbu_db.bin                  # la base, gzip (ver 3.0 bis)
│   ├── sw.js                       # service worker (offline + aviso de versión nueva)
│   ├── manifest.webmanifest        # para instalarla como aplicación
│   └── icons/                      # generados con un codificador PNG propio (no hay PIL)
├── docs/
│   ├── supabase.sql                # tablas, reglas RLS y funciones — LA SEGURIDAD VIVE ACÁ
│   └── INSTALACION.md              # guía del administrador, paso a paso
├── .github/
│   ├── workflows/pages.yml         # publica web/ y sella la versión con el commit
│   └── dependabot.yml              # avisa cuando una acción tiene versión nueva
├── data/                           # fuentes + JSON intermedios + nbu_db.json (12 MB)
│   ├── lateralidad_curada.json     # ← dato de la casa (ver 3.1)
│   ├── correcciones_curadas.json   # ← dato de la casa (ver 3.1)
│   └── nbu_reval_2024.json         # U.B. 2024 recuperadas (ver abajo)
├── LICENSE                         # reserva de derechos
├── README.md                       # documentación funcional
└── HANDOFF.md                      # este documento

⚠️ `data/nbu_reval_2024.json` existe porque el `nbu_reval.txt` original **nunca se versionó**:
rebuildear la base sin él borraba en silencio la U.B. 2024 de 50 códigos. Se recuperó desde
la base ya commiteada. Si aparece otra fuente sin versionar, versionarla antes de tocar el
pipeline.
```

### Cómo se compila la base
1. **Parsers** (`scripts/parse_*.py`) → JSON intermedios en `data/`.
2. **`scripts/assemble.py`** → une todo en `nbu_db.json` (6.346 códigos + datasets).
3. **`scripts/inject_db.py`** → comprime la DB con gzip y la deja en `web/nbu_db.bin`.
   La app la busca al arrancar y la descomprime con `DecompressionStream('gzip')`.

### 3.0 bis ⚠️ La base viaja aparte, y se puede volver atrás

`inject_db.py` tiene dos modos y la app soporta los dos sin tocar nada:

```bash
python3 scripts/inject_db.py              # publicación: escribe web/nbu_db.bin
python3 scripts/inject_db.py --embebido   # un solo archivo: la mete en el HTML
```

`loadDB()` usa la base embebida si la encuentra y, si no, pide `nbu_db.bin`. Volver
al archivo único es correr el segundo comando, sellar la CSP y publicar.

**Lo que este cambio NO era.** Se hizo pensando que ahorraba ~19% de descarga. Medido
después: por la red son **891 KB contra 900 KB, 1%**. GitHub Pages comprime el HTML al
servirlo y recupera casi todo el engorde del base64. Lo que sí gana, y por eso quedó:

- **El repositorio y los diff.** `index.html` pasó de 1,41 MB a 380 KB. Antes cada
  cambio de una línea de código reescribía un renglón base64 de 1 MB y el diff era
  ilegible; ahora se lee. La base sólo cambia cuando cambia la base.
- **En el equipo del usuario**: 1,15 MB guardados en vez de 1,41 MB.
- **Arranque**: medido, no cambia (mediana 1.053 ms contra 1.058 ms, n=8 cada uno).

⚠️ Después de cambiar de modo hay que correr `scripts/sellar_csp.py`, y el service
worker tiene que seguir listando `nbu_db.bin` en `SHELL` o la app abre sin datos
cuando no hay señal. La acción de publicar verifica las dos cosas y corta si faltan.

### 3.0 ⚠️ El Único de laboratorio es el NBU con otro número

Las **1.694** prácticas de laboratorio del Único son las mismas del NBU con otro código
(`U64660163` ↔ `660163`). Están **dos veces en la base**, así que todo lo que se agregue de
un lado hay que llevarlo al otro o las dos pantallas empiezan a decir cosas distintas —que
es exactamente lo que reportó el usuario.

`scripts/propagar_al_unico.py` es el que lo mantiene parejo. Corre **al final** de
`assemble.py` (después del tipo de muestra, de las siglas y de las correcciones curadas) y
también se puede correr solo sobre una base ya armada:

```bash
python3 scripts/propagar_al_unico.py data/nbu_db.json
```

Tres reglas que **no** se cruzan, y conviene no «arreglarlas»:
- **La valorización no se toca.** El Único trae su propia U.B. de la planilla de VISITAR y
  en 101 prácticas no coincide con la del NBU: eso es el convenio, no un error. La U.B. del
  NBU va aparte, en `nbu_valor`, y la ficha la muestra rotulada como referencia.
- **El tipo de muestra no se pisa.** Se hereda sólo si el Único no tiene ninguno. Cuando los
  dos nombres indican muestras **sin nada en común** (6 casos) queda un renglón de auditoría
  «Revisar la equivalencia»: ahí el problema es el mapeo, no la ficha.
- **El nombre y la sección propios se respetan.** De qué parte del NBU viene la práctica
  (`Prácticas Especiales`, `PMO`) va en `nbu_seccion_label` y se ve como cartel aparte.

Lo que vive en la **nube** (observaciones) no se resuelve acá sino en la app: ver 4.6.

### 3.1 ⚠️ Patrón «dato curado con prioridad» (importante)

Hay conocimiento que **sólo tiene el usuario** y que ninguna fuente resuelve. Ese dato
**no se infiere**: entra por archivo curado y **pisa** lo que arma el pipeline.

| Archivo | Qué guarda | Cómo entra |
|---|---|---|
| `data/lateralidad_curada.json` | 15 códigos de oftalmología con Bilateral/Unilateral relevados por auditoría | A mano; se propaga a todos los nomencladores donde aparezca el código |
| `data/correcciones_curadas.json` | `codigos{}` (nombre, norma, auditoría, cómo se carga) y `verificaciones{}` (qué ficha se contrastó, cuándo y quién) | Lo **descarga la propia app**: Administración → Respaldo → «⬇ Exportar correcciones para la base». Se reemplaza el archivo del repo por el descargado |

`assemble.py` los aplica **al final**, después de todo lo demás. Corregir el nombre desde
la app además **da por resuelta** la marca «denominación a confirmar» (`titulo_revisar`).

**Este es el circuito por el que el conocimiento del equipo vuelve al repo.** Si el usuario
dice «corregí tal ficha en la app», lo que hay que pedirle es ese JSON exportado.

### 3.2 ⚠️ Cómo ejecutar assemble.py
`assemble.py` necesita JSON intermedios que **viven en el scratchpad**, no en el repo.
```bash
SP="<scratchpad>/"                              # dir. scratchpad de la sesión
cp scripts/assemble.py "$SP/assemble.py"
cp data/<json que hayas regenerado> "$SP/"      # y también a "$SP/data/" si aplica
cd "$SP" && python3 assemble.py                 # genera $SP/nbu_db.json
cp "$SP/nbu_db.json" /home/user/VISITAR/data/nbu_db.json
python3 /home/user/VISITAR/scripts/inject_db.py # ← RUTA ABSOLUTA (ver abajo)
```
⚠️ **Usar rutas absolutas después del `cd`**: el directorio de trabajo del shell persiste
entre llamadas y `inject_db.py` «desaparece» si se lo invoca relativo desde el scratchpad.

Si el scratchpad está vacío, hay que regenerar los intermedios corriendo los parsers desde
`data/` (las fuentes originales están versionadas: `pmo.pdf`, `cie10.pdf`, `surge.pdf`,
`surge.ods`, `unico_*.xls(x)`, etc.).

### Parsers disponibles
`parse_catalog.py`, `parse_intel.py`, `parse_pmo.py`, `parse_pmo_cobertura.py`,
`parse_nn.py`, `parse_odo.py`, `ocr_nn.py`, `parse_unico.py`, `parse_unico_lab.py`,
`parse_cie10.py`, `parse_cie10_detalle.py`, `parse_cie10_tabular.py`,
`cie10_relaciones.py`, `parse_abreviaturas.py`, `parse_surge.py`, `parse_nbu_normas.py`.
Y dos que no son parsers: `propagar_al_unico.py` (punto 3.0) y `sellar_csp.py`.

### Testing
No hay framework. Se valida con **Playwright** (Node) desde el scratchpad:
```js
import pkg from '/opt/node22/lib/node_modules/playwright/index.js';
const { chromium } = pkg;   // playwright NO está en node_modules del repo
```

**⚠️ La app ya no arranca en modo local: arranca pidiendo cuenta contra Supabase, y desde
este entorno la red a Supabase está bloqueada.** Para probar hay que **simular Supabase**
interceptando con `ctx.route(HOST+'/**', …)` y respondiendo a mano `/auth/v1/token`,
`/rest/v1/perfiles`, `/rest/v1/rpc/*`, `/rest/v1/{correcciones,verificaciones,propuestas,ajustes}`.
El simulador vive en `e2e.mjs` del scratchpad; **recrearlo si se perdió** (está descrito
en los commits `c159cfe` y `91a95d6`).

Claves del simulador, aprendidas a los golpes:
- **La identidad es de cada sesión, la base es compartida.** `servidor(quien, db)`: si la
  identidad queda fija, «el administrador» entra como el administrativo y las pruebas
  mienten sin fallar.
- Servir la app por **http://** (no `file://`), porque el service worker no corre en
  `file://`. Un `python3 -m http.server` en el scratchpad alcanza.
- **El service worker cachea**: si probás dos archivos distintos en el mismo puerto, sirve
  el primero para cualquier navegación. Usar **un puerto por variante**.
- Saltar el recorrido guiado con
  `ctx.addInitScript(()=>localStorage.setItem('nbu-onboarded','1'))`; si no, `#tour`
  intercepta todos los clics.
- Varias funciones internas (`BYCODE`, `toggleFav`, `CONTENT`) **no son alcanzables** desde
  `page.evaluate`: interactuar por la interfaz o por `window.NBUProfile`.
- La tira de accesos rápidos se redibuja con `render()`; tocar una estrella no la
  refresca. Forzarlo escribiendo y borrando en `#q`.

**Reglas de la base**: se prueban aparte, en un **PostgreSQL 16 local** (`/usr/lib/postgresql/16/bin`),
con una maqueta del esquema `auth` de Supabase. **Tiene que incluir el rol
`supabase_auth_admin` como dueño de `auth.users`**: sin eso no aparece la clase de fallo
que rompió el alta de cuentas (ver 9). Correr `initdb` como el usuario `postgres` y dar
permiso de recorrido a los directorios padre del socket.

**Suite de regresión** (scratchpad; recrearla si se perdió):
`login` (ingreso + violaciones CSP) · `simul` (dos personas a la vez, avisos al
administrador) · `flujo3` (propuesta → aprobación por el panel real) · `fidelidad`
(corrección que borra la norma a propósito) · `favs` (favoritos del equipo) ·
`nube` (pestaña de estado) · `recup` + `recup2` (restablecer contraseña) ·
`nubelocal` (modo local). Al 2026-08-05 pasan todas, sin errores de página.

---

## 4. Funcionalidades de la app

### Navegación principal
4 tarjetas visibles: **Buscar en todo** · **Laboratorio (NBU)** · **Prestaciones médicas
(PMO)** · **Único (VISITAR)**. En móvil es un **`<select>`** (`.modesel`).

### Consulta rápida (fila aparte)
**Diagnósticos (CIE-10)** · **Abreviaturas** · **SURGE**.

### Búsqueda
- **Tolerante a erratas**: distancia de edición acotada (`distEdicion`, `tolerancia`) —
  «emograma» → HEMOGRAMA, «uremya» → UREA, «creatinia» → CREATININA.
- Busca también por el **nombre que la práctica tiene en el otro nomenclador**.
- **Estado vacío que orienta**: si no hay resultados, sugiere códigos buscando
  **término por término** (no con la misma consulta que ya falló) y cada sugerencia abre
  la ficha.
- **Paleta de comandos** `Ctrl+K` (`#palette`) desde cualquier lado.

### Ficha de un código
Ordenada de arriba hacia abajo por lo que el agente necesita primero:

1. **Veredicto** (`veredictoHTML`) — las cuatro respuestas cortas: **si se cubre**,
   **cuánto vale**, **si requiere autorización**, **qué cantidad**. Cada una despliega su
   sección al tocarla.
2. **Cómo se carga esta solicitud** (`comoSeCargaHTML`) — pasos numerados: qué código y
   en qué cantidad, qué **no** cargar aparte por estar comprendido, qué adicionar (Acto
   Bioquímico / ABI), qué diagnóstico consignar, qué papeles pedir.
3. **Verificación** (`verifHTML`) — ver punto 4.1.
4. Secciones **plegables** con memoria (`plegarSecciones`): valorización, equivalencias,
   relaciones, frecuencia/seriado, sinónimos y abreviaturas, **obligación de cobertura**,
   SURGE, CIE-10, normativa, origen, notas personales.
5. **Comparador** de dos códigos lado a lado con diferencias resaltadas.
6. **Impresión**: `body.imp-ficha` imprime sólo la ficha. El **comprobante para el
   afiliado** se eliminó por pedido del usuario: *«eso no lo hacemos desde acá»*.

### 4.1 Verificación de fichas (dos pasos)
- Un **administrativo** que contrastó la ficha contra la fuente toca
  **«Solicitar verificación»** → queda **pendiente**.
- **Sólo el administrador valida.** Recién ahí la ficha figura verificada.
- La verificación **vence a los 180 días** (la normativa cambia): estado `ok` → `vieja`.
- Se guarda en `CONTENT.verif` y sale por el exportador de correcciones.

### 4.2 «Contá cómo se carga acá» (propuestas)
Lo que el equipo sabe sobre cómo se carga una práctica **en el sistema de VISITAR** no
está en ningún nomenclador. El agente lo escribe una vez, el administrador lo aprueba y
queda publicado para todos (`asoc_extra`).

### 4.3 Pendientes visibles (no escondidos en ajustes)
Botón **`#pendBtn`** en la barra superior, **sólo para el administrador y sólo cuando hay
algo esperando**. `contarPendientes()` devuelve `{v, pr, cu, total}`:
**v**erificaciones · **pr**opuestas · **cu**entas. El botón abre directo la pestaña que
corresponde. El título dice, por ejemplo:
*«Pendientes de revisar: 1 cuenta · 2 verificaciones · 1 propuesta»*.

### 4.4 Acceso, cuentas y contenido compartido ⚠️ REESCRITO POR COMPLETO

**Ya no hay «acceso de empresa» ni perfiles locales en producción.** Cada persona entra
con **su correo y su contraseña**, contra **Supabase Auth**. El módulo `NUBE` (IIFE dentro
de `web/index.html`, expuesto como `window.NBUNube`) es todo el cliente: no usa la
librería de Supabase, son `fetch` contra la API REST.

**El estado inicial lo pone la base, no el cliente.** Un trigger sobre `auth.users` crea el
perfil en `estado='pendiente'`; el administrador aprueba desde **Perfiles**. Un usuario no
puede ascenderse aunque manipule la app: lo revierte el trigger `perfiles_guardia`.

**Hay un solo administrador**, garantizado por un *constraint trigger* diferido. Se cambia
con **Transferir administración**, nunca sumando un segundo.

**Qué vive en la base compartida** (`docs/supabase.sql`):

| Tabla | Quién lee | Quién escribe |
|---|---|---|
| `perfiles` | cualquier cuenta activa | cada uno lo suyo; rol y estado sólo el admin |
| `correcciones` | activos | **sólo el admin** |
| `verificaciones` | activos | pedir: cualquier activo (por función) · validar: sólo admin |
| `propuestas` | activos | crear: cualquier activo · resolver: sólo admin |
| `ajustes` | activos | sólo el admin (textos, logo y **favoritos del equipo**) |

Funciones de apoyo: `es_admin()`, `es_activo()`, `pendientes()`, `transferir_admin()`,
`hacerme_admin()` (arranque, sólo desde el SQL Editor), `pedir_verificacion()` y
`validar_verificacion()`.

⚠️ **Por qué las verificaciones van por función y no por escritura directa:** verificar una
ficha ya verificada es un `UPDATE`, y habilitar `UPDATE` a un no-admin sobre esa tabla le
abriría también la puerta a auto-validarse. La función pone estado, autor y fechas del
lado del servidor.

⚠️ **`correcciones.datos`** guarda la corrección **exacta**. Las columnas sueltas no
distinguen «no toqué la norma» de «la dejé vacía a propósito» —las dos llegan como nulo— y
al releer reaparecía una norma que el administrador había borrado.

**Cómo se sincroniza en la app:** `cargarContenidoNube()` lee las cuatro tablas al entrar,
al abrir el panel y después de cada escritura (`enNube()` reintenta la lectura incluso
cuando falla, para que la pantalla nunca muestre algo que las reglas rechazaron). Los
contadores de pendientes salen de la base (`pendientes()`), se refrescan cada minuto y al
volver a la pestaña — calcularlos sobre lo cargado localmente fue un bug real: una
solicitud hecha después de que el administrador entrara no le aparecía nunca.

**Lo que sigue siendo local**: el **registro de actividad** (pestaña Registro) y el
respaldo `.json`. Está dicho en la interfaz.

**Modo local**: si `window.NBU_NUBE` queda vacío, la app arranca como antes (acceso de
empresa + perfiles en el navegador). Se conserva **a propósito**, como red de contención si
Supabase no responde. No tiene panel de configuración: la pestaña Nube sólo lo informa.

### 4.4 bis Restablecer la contraseña (autogestionado)
**Me olvidé la contraseña** → `POST /auth/v1/recover` → correo → el enlace vuelve con la
sesión en el `#` de la dirección.

⚠️ Tres cosas que hicieron falta y no son obvias:
1. El `#` ya estaba tomado para abrir códigos, así que el enlace se lee en
   **`window.NBU_RECUPERAR`, arriba de todo el archivo**, antes de que nada lo limpie.
2. Si la app **ya estaba abierta**, el enlace cambia sólo el `#` y el navegador no recarga:
   el `hashchange` lo detecta y fuerza `location.reload()`.
3. El pedido contesta **lo mismo exista o no la cuenta**: decir «ese correo no está
   registrado» dejaría averiguar quién trabaja en la empresa.

Requiere *Site URL* y *Redirect URLs* configurados en Supabase; si no, el enlace lleva a
`localhost`.

### 4.4 ter Favoritos del equipo
Lista común que publica el administrador (**👥 Compartir con el equipo**, en la tira de
accesos rápidos). Vive en `ajustes.contenido.equipo.favoritos`, así que la regla que ya
existía alcanza. **Es opcional y no toca los favoritos personales**: cada uno elige qué
solapa mirar.

### 4.4 quater PWA
`web/manifest.webmanifest` + `web/sw.js` + iconos. Instalable, abre sin internet.
La versión nueva **se aplica sola al abrir** si nadie tocó nada todavía; si la app está en
uso, aparece el cartel y decide la persona. Una sola recarga automática por pestaña.

### 4.5 Recorrido guiado (onboarding)
`pasosTour()` — **20 pasos** para el administrativo, **23** para el administrador (suma
Pendientes, Modo edición y Administración). Es un **spotlight**: recorta el elemento real
con `box-shadow: 0 0 0 9999px` y ubica el globo al lado. Varios pasos tienen `antes:` que
prepara la pantalla (abre el rail, abre una ficha, carga un caso en la Mesa de trabajo).
Se puede volver a ver desde **Glosario y leyes → Ver tutorial de uso**.

### 4.8 Lo que el equipo comparte, y por dónde

| Qué | De quién a quién | Cómo viaja |
|---|---|---|
| **Observaciones** | administrador → todos | tabla `observaciones`, una por práctica (ver 4.6) |
| **Fichas corregidas** | administrador → todos | tabla `correcciones` |
| **Propuestas** («contá cómo se carga») | cualquiera → administrador **y ahora también → todos**, marcadas *sin confirmar* | tabla `propuestas` |
| **Verificaciones** | cualquiera pide, el administrador valida | tabla `verificaciones` |
| **Favoritos del equipo** | administrador → todos | `ajustes.contenido.equipo.favoritos` |
| **Nota personal** | privada, **con botón para mandarla como propuesta** | columna `notas` del perfil |
| **Una ficha / un caso** | de una persona a otra | **en la dirección**, no en la base |

Tres cosas que se resolvieron sin tocar el esquema de Supabase, y conviene no
«mejorarlas» agregando tablas:

- **Actividad del equipo** (`CONTENT.actividad`): cada fila de la base ya guarda
  autor y fecha, así que el registro compartido se arma leyendo lo que ya está.
  Antes el registro era el de cada computadora y como registro de un equipo no
  servía. El local sigue abajo, porque tiene lo que la base no guarda (textos,
  logo, restauraciones).
- **«Qué pasó desde la última vez»** (`CONTENT.novedades`): la campanita dejó de
  ser sólo de observaciones. Filtra la actividad por `perfiles.obs_vistas` —la
  marca que ya existía—, saca lo propio y se queda con lo que le cambia la ficha
  a quien atiende: observaciones y correcciones. Las verificaciones son trámite,
  no novedad.
- **Pasar una ficha o un caso**: van en el `#` de la dirección
  (`#660475`, `#caso=660475 660102 x3&modo=autorizacion`). Un caso es de quien lo
  está mirando; guardarlo dejaría cientos de casos viejos de todo el mundo. En
  celular usa `navigator.share` (o sea WhatsApp) y en escritorio copia el enlace.

⚠️ **Propuestas visibles al equipo**: se ven con el texto completo pero con aviso
antes del texto —«sin confirmar», «no es norma»—, recuadro punteado y color de
gestión. La regla es que lo no confirmado **nunca** se vea igual que lo
confirmado: si tuviera el mismo peso, alguien cargaría con eso creyendo que es
norma. No aparecen en el listado de resultados, sólo dentro de la ficha.

### 4.7 Respaldo y restauración ⚠️ el plan de Supabase es gratuito: NO hay respaldos automáticos

Verificado con el usuario: en **Database → Backups** le ofrece contratar el plan. O sea
que **el archivo que baja el administrador es la única copia que existe** del trabajo del
equipo. Eso manda sobre todo lo demás de esta pantalla.

- **⬇ Descargar respaldo** — lleva `content` completo (fichas corregidas, verificaciones,
  propuestas, observaciones, favoritos del equipo, textos). **No lleva las cuentas**: viven
  en Supabase y las contraseñas no están al alcance de la app. El nombre incluye la fecha.
  Cada descarga deja anotado el día en `ajustes.contenido.equipo.respaldo`, y la pestaña
  avisa en rojo si nadie bajó ninguna o si la última tiene más de 30 días.
- **⬇ Exportar correcciones para la base** — es otra cosa: el JSON curado para
  `data/correcciones_curadas.json` del repositorio (ver 3.1).
- **Restaurar** — **escribe en la base**, en dos tiempos: `difRestaurar()` compara el
  archivo contra lo que hay y `previaRestaurar()` muestra qué cambiaría (cuántas vuelven,
  cuántas se agregan, cuántas **se borrarían** por no figurar en el respaldo, con los
  códigos a la vista). Recién con la confirmación, `aplicarRestaurar()` manda los cambios y
  vuelve a leer la base entera —lo que vale es lo que quedó del otro lado, no lo que
  mandamos—. **No toca** cuentas, verificaciones ni propuestas: las dos últimas son pedidos
  en curso, conversaciones abiertas, no contenido. Probado: se pisa una ficha, se borra
  otra, se agrega una tercera, se restaura, y la base queda como el respaldo con la
  verificación y la propuesta intactas; aplicarlo dos veces dice «no hay nada que
  restaurar».

⚠️ Antes de esto, «Restaurar» **no restauraba nada**: escribía sólo en el navegador y a la
primera recarga volvía todo. Si aparece algo parecido en otra pantalla, medirlo así —
cambiar, recargar, mirar.

### 4.6 Observaciones del administrador — una sola por práctica

El administrador deja una observación en la ficha; se ve **debajo del código en el listado**
(`.robs`, sin abrir nada) y arriba de todo en la ficha, y a los administrativos les suena una
campanita hasta que la marcan como vista (`perfiles.obs_vistas`).

⚠️ La observación es **de la práctica, no del código**. La misma práctica está en más de un
nomenclador —el laboratorio del Único es el NBU con otro número, y sus prestaciones médicas
son las del PMO—, así que en `web/index.html` hay un índice `EQGRUPO` que agrupa todos los
códigos equivalentes. Se arma con **las dos puntas** de la equivalencia (la del Único hacia
el otro nomenclador y la del otro hacia el Único), porque hay prácticas del PMO con más de
un equivalente en el Único y la observación tiene que llegar a todas. Entonces:

- `obsDe(code)` busca por el código pedido y, si no hay, **por el gemelo**;
- `claveObs(code)` la guarda siempre en el mismo código del grupo —nunca en el del Único
  si hay otro—, y al guardar **borra las de los demás** si quedaba alguna vieja: si sobrevivieran las dos, la ficha del Único seguiría
  mostrando la vieja y no habría forma de darse cuenta;
- la ficha avisa «Se ve también en el código X»: sin eso, alguien la escribe de nuevo del
  otro lado creyendo que falta.

Esto vale para las observaciones —contenido de la nube—. **Las verificaciones no se
comparten**: contrastan los valores de una ficha contra su fuente, y la fuente del Único (la
planilla de VISITAR) no es la del NBU.

### Vistas
**Listado** (filtros por sección/grupo/reglas, favoritos, CSV/PDF) · **Árbol de módulos**
(NBU y Único) · **Mesa de trabajo** (punto 5).

### Diseño
Responsive verificado en 360 / 620 / 768 / 900 / 1280 px sin scroll horizontal; tema
claro/oscuro; atajos `/`, `Ctrl+K`, `↑`/`↓`, `Enter`; objetivos táctiles ≥42 px;
aria-labels, `role="tablist"`, `aria-modal`, `focus-visible`.
**Accesos rápidos** (`#rapidos`): los favoritos del perfil, arriba, a un clic; se ocultan
al buscar.

---

## 5. Mesa de trabajo

Una sola carga de códigos del caso (acepta **6 dígitos** NBU/PMO y **8 dígitos** Único;
cantidades con `×N`), auditable en **dos modos**:

**📋 Auditoría de autorización** — el modo que le sirve al usuario de carga.
⚠️ **TODAS las prácticas se tratan como «autorización previa»** (regla 6.1). Arma el
**checklist de documentación a solicitar al afiliado** (requerimientos SURGE consolidados
y deduplicados), consolida las **obligaciones de cobertura** de todos los códigos del caso
en tarjetas, lista las **patologías SURGE** y el **CIE-10 justificante** sugerido.

**💲 Auditoría de facturación** — doble facturación por inclusión en módulos, urgencias sin
661200, Acto Bioquímico faltante, seriados excedidos, desuso, códigos inexistentes,
**bilateral cargado con cantidad > 1**; total en U.B. netas y $.

Ambos exportan **CSV / PDF** y un **informe en texto listo para pegar** en el sistema donde
llevan el caso.

Funciones: `initValidator()`, `runCase()`, `renderCase()`, `renderFacturacion()`,
`renderAutorizacion()`, `exportValidatorCSV()`, `exportAuthCSV()`.

---

## 6. ⚠️ REGLAS Y DECISIONES DEL USUARIO (respetar siempre)

1. **NO inferir qué requiere autorización previa y qué no.** El usuario nunca entregó ese
   listado. **Todas las prácticas se toman como autorización previa.**
2. **No inventar contenido normativo.** Todo dato de cobertura, requisitos o topes sale del
   PDF/Excel oficial parseado, no de conocimiento general. Si la fuente está dañada, **la
   ficha lo avisa** — no se completa a ojo.
3. **Sección Medicamentos: eliminada** (descartada explícitamente).
4. **CIE-10 no es un nomenclador**: es un apartado de consulta para administrativos.
5. Pushear **solo** a `claude/unified-medical-codes-manual-o9nw1w`.
6. **No crear PR** salvo pedido explícito.
7. **Republicar siempre en la misma URL del artefacto**, con `favicon: 🩺`.
8. **No cargar datos de pacientes en la base.** La clave publicable es pública a propósito;
   lo que protege los datos son las reglas RLS, no esconderla.
9. Dominio `ais.paho.org` **bloqueado** por política de red — no reintentar ni rodear.
10. Servidores MCP **Adobe** y **Whimsical** requieren autorización → no disponibles.
11. **La autoría debe quedar registrada en lugar visible**: «Diseñado por **Juan Pablo
    Besada**». Motivo textual del usuario: *«para que nadie pueda decir que el trabajo fue
    realizado por él»*. Hoy figura en **5 lugares**: pie de la app (`.autoria`), todas las
    pantallas de acceso (`.au-gate`, se inyecta en cualquier `.gcard`), encabezado de
    impresión del listado y de las dos auditorías, y el informe copiable.
12. **Odontología está oculto**: `NOMEN_OCULTOS = new Set(['ODO'])`. Los 79 códigos siguen
    en la base (no se borraron), pero no se listan ni se buscan. VISITAR no lo usa.
13. ⚠️ **Después de tocar `web/index.html`, correr `python3 scripts/sellar_csp.py`.**
    La política de seguridad lleva la **huella** de cada script en lugar de
    `'unsafe-inline'`. Si el archivo cambia y la huella no, **el navegador se niega a
    ejecutar la app entera**. La acción de publicación lo vuelve a sellar sola, así que
    olvidarse nunca llega al equipo — pero sí rompe la copia local y el artefacto.
14. **No mandar el enlace del artefacto.** No puede hablar con Supabase, así que ahí no se
    puede ni entrar. Para probar, la dirección de producción; para mostrar, capturas.
15. **No inventar identificadores ni valores que no se puedan verificar** (los SHA de las
    acciones de GitHub quedaron pendientes por esto: la red del entorno bloquea GitHub).
16. **La secret key de Supabase no se usa y no debe salir del panel.** El usuario la pegó
    una vez en el chat; se le pidió rotarla. Verificado que **nunca** entró al repositorio.
17. **El código no se puede cifrar** y no hay que intentarlo: es una app web, corre en el
    navegador. Lo que protege la autoría es `LICENSE` + el sello de origen (1 bis).
18. **Redacción rioplatense.** El usuario corrigió «que te la reponga» por sonar acartonado.
    Escribir como habla alguien del rubro en Argentina, no traducir del inglés.
19. **Regla de nombres de laboratorio** dictada por el usuario:
    **`-emia` = en sangre** (glucemia, uremia) · **`-uria` = en orina** (hematuria,
    glucosuria). Se aplica en `assemble.py` (`MUESTRA_TEXTO`, sufijos) y se muestra como
    etiqueta de color en la fila y en la ficha, con filtros «en sangre» / «en orina».
    ⚠️ **Excepción**: `MUESTRA_SUF_EXCL = {"isquemia"}` — termina en `-emia` y no es una
    determinación en sangre. Si aparecen más falsos positivos, van ahí.

---

## 7. Historial de trabajo (99 commits)

**Base y nomencladores**
1. Catálogo NBU (PMO + Prácticas Especiales) e inteligencia (sinonimias, abreviaturas,
   normas). Modelo unificado. Interfaz navegable.
2. Arancel por U.B., favoritos, export CSV/PDF, reglas de frecuencia/seriado, validador.
3. Nomenclador Nacional / Catálogo PMO + valores por OCR. U.B. vigentes desde XLS.
4. Perfiles + acceso empresa, panel admin, Supabase, branding VISITAR, seguridad.
5. Nomenclador Único con **equivalencias bidireccionales**; los 79 sin equivalencia se
   agrupan aparte. Parte de laboratorio del Único (prefijo 2 díg. + código NBU).
6. 22 leyes/normas vinculadas por código. **CIE-10 completo** (11.581). **Compresión
   gzip+base64**: HTML de ~9 MB → ~1,2 MB.
7. Re-parseo de la Res. 201/02 columna a columna: títulos limpios, cobertura obligatoria,
   topes, generalidades, Anexos III y IV.
8. Abreviaturas médicas (HIBA + INSN) con dedup. Búsqueda global «Buscar en todo».
9. SURGE (Res. 731/23): parseo completo de las 58 secciones; grafo de equivalencias para
   propagar el vínculo por todo el componente conexo.
10. Mesa de trabajo con los dos modos de auditoría.

**Calidad de datos**
11. **Auditoría de títulos de los 6.346 códigos**: la planilla del Único mezclaba en una
    celda el nombre, un marcador de clasificación y a veces una observación. Separados en
    campos propios: 1.724 títulos limpios, observaciones a su sección, 139 fichas avisan
    que el texto viene cortado en el origen.
12. **Oftalmología revisada** (prefijos `02` y `30`): títulos recompuestos alineando el PDF
    contra el OCR, equivalencias reparadas, lateralidad.
13. **Extendido a todo el nomenclador**: 265 títulos recompuestos, 170 equivalencias
    re-resueltas (148 por código, 22 por nombre), 109 fichas con lateralidad.
14. **Lateralidad relevada por auditoría** para 15 códigos de oftalmología
    (`lateralidad_curada.json`) → 130 fichas con el dato.

**Centro de respaldo — lo construido en las últimas tandas** *(commits `ddf918b`…`7bbaa70`)*
15. `ddf918b` **Oculta Odontología**, que VISITAR no usa.
16. `91a4c4c` **Obligaciones de cobertura**: relevamiento de todas las fuentes; la cobertura
    se aplica a **cualquier** nomenclador (antes sólo PMO), se distingue *obligación* de
    *observación* (`cobertura_tipo`), hay filtro propio y la Mesa de trabajo las consolida.
17. `f37fc12` **Búsqueda tolerante a erratas** + **exportación de correcciones hacia la
    base** (el circuito de 3.1).
18. `fa02705` Alta de `380201` (Cámara Hiperbárica) y `430106` (cama para acompañante),
    que tenían texto de cobertura y no existían en el catálogo → `solo_anexo_cobertura`.
19. `3f85f82` **UX**: cabecera compacta, **veredicto** en la ficha, **paleta de comandos**,
    **comparador**, informe copiable.
20. `95d795b` **Tipo de muestra** (-emia/-uria, regla 6.13) + **accesos rápidos** por perfil.
21. `5a07b0e` **Instructivo de carga por práctica** («cómo se carga esta solicitud») con
    **propuestas de los agentes** aprobadas por el administrador.
22. `5e27ec1` **Verificación y vigencia** de las fichas (180 días).
23. `67943a3` La verificación **la solicita el administrativo y la valida el administrador**.
24. `bf1f6f9` **Los pendientes salen del panel de ajustes a la barra superior** (estaban
    demasiado escondidos).
25. `fe50f7e` **Recorrido guiado que señala cada elemento en pantalla** (el anterior era un
    cuadrado en el medio que no indicaba dónde estaba nada).
26. `756e02c` **Registra la autoría** (regla 6.11).
27. `94a7ef2` **Ficha plegable con memoria, estados vacíos que orientan, impresión de ficha
    y comprobante para el afiliado.**
28. `7bbaa70` **Alta de cuentas con aprobación del administrador** y administrador único
    (punto 4.4).


**De archivo suelto a aplicación de empresa** *(commits `3bb720a`…`f66b55e`, 36 tandas)*

*Interfaz y contenido*
29. `3bb720a` Rastro para volver dentro de la ficha; etiquetas en dos niveles (las de
    decisión con color, las de estado del dato en gris).
30. `74e8d0a` **Color propio por tipo de muestra** (7 tipos, no sólo sangre y orina): a
    pedido del usuario, *«único y relaciones deben estar con color»*.
31. `0896446` + `c318505` **Glosario y marco normativo**: se quitaron `N8337/N8332/N8327`,
    se agregaron los enlaces oficiales a 22 normas, y el **Anexo I de la Res. 201/02**
    pasó a reconstruirse entero (`scripts/parse_pmo_anexo1.py`) en vez de recortar frases
    sueltas sin marco de referencia.
32. `149b74a` + `f160a24` + `1925ddb` **Recorrido guiado**: bloquea el scroll, mueve la
    página él mismo, funciona en toda resolución, y se movió a animación por `rAF` porque
    el usuario lo describió como *«totalmente tosco»*.
33. `f7cb990` + `66196d1` **Accesibilidad**: contraste, foco y trampa de foco en diálogos,
    `aria-live`, encabezados reales en la ficha, objetivos táctiles de 24 px, salto al
    contenido, `prefers-reduced-motion`.
34. `3437657` **Se quita el comprobante para el afiliado** (regla del usuario).
35. `b84b405` **Sale «NBU» del nombre de la app**: cubre cinco nomencladores, no uno.
36. `a0a8e2b` **La pantalla de ingreso estaba rota**: el campo de correo (`type=email`) no
    entraba en el selector de estilos y se dibujaba crudo, 185×21 al lado de uno de 366×43.
    De paso, `autocomplete`, teclado del celular, 16 px para que iOS no haga zoom, ver la
    contraseña, y estado deshabilitado.
37. `f66b55e` **Se separan «crear cuenta» y «olvidé la contraseña»**: estaban con el mismo
    peso, uno debajo del otro, y se leían como lo mismo.

*Infraestructura*
38. `ede215d` **Cuentas compartidas en la nube y PWA**: `docs/supabase.sql`,
    `docs/INSTALACION.md`, manifest, service worker e iconos.
39. `d9aa335` → `297f091` Habilitar GitHub Pages **no se puede automatizar** (el token de
    las acciones no tiene permiso); queda como paso manual documentado.
40. `9a9cb2c` **App conectada al proyecto real** de Supabase.
41. `2144b5e` → `29f15e3` Publicación: manual mientras Pages fallaba, automática de nuevo
    una vez resuelto, con filtro de rutas para que `docs/` no dispare correos.
42. `4c96f3e` **La versión nueva se aplica sola al abrir** + la acción sella la versión del
    service worker con el commit.
43. `c159cfe` **Correcciones, verificaciones y propuestas pasan a la base compartida** — el
    último pedazo del trabajo en equipo que vivía en cada computadora.
44. `dfb92aa` Avisos al administrador **en tiempo real**; favoritos del equipo; se saca la
    pestaña Empresa.
45. `59f3c5a` + `156cc74` + `36f7751` **Limpieza de lo obsoleto**: la pestaña Nube decía
    «desactivada» mientras la app corría contra la nube, y el panel viejo seguía enseñando
    a crear una tabla abierta a cualquiera. Se eliminó la sincronización `kv` entera con su
    cifrado AES (161 líneas).
46. `91a95d6` **Restablecer contraseña autogestionado** (4.4 bis).

*Seguridad y autoría*
47. `3eaa50f` **XSS almacenado en el logo** cerrado + **Content-Security-Policy**.
48. `a7c379b` **`LICENSE`**, encabezado de copyright, **sello de origen** y endurecimiento
    de la publicación (`persist-credentials: false`, dependabot).

---

## 8. Pendientes y sugerencias abiertas

### ⚠️ Lo primero que hay que preguntar al retomar

El usuario recibió una lista de mejoras y **todavía no eligió**. Sus dos prioridades
recomendadas fueron: **relaciones diagnóstico → práctica** (sólo 45 de 11.581 códigos las
tienen; es la consulta más frecuente en el mostrador) y **poner este HANDOFF al día**
(hecho). Antes de arrancar cualquier cosa, preguntar por dónde quiere seguir.

### Pendientes concretos, con dueño

| Qué | De quién depende |
|---|---|
| **Fijar las acciones de GitHub por SHA** en vez de por etiqueta | mío, necesita una sesión con red a GitHub |
| **Segundo factor** en GitHub y Supabase, y **proteger la rama** | del usuario; se le pidió dos veces |
| **Rotar la secret key** de Supabase | del usuario |
| **Cerrar las altas** cuando el equipo esté completo, subir el mínimo de contraseña | del usuario |
| **Las 119 prácticas «fuera del PMO»** que están en nuestra sección PMO | criterio del usuario |
| **Las 113 prácticas del Excel** que no están en la base (comparación de julio) | decisión conjunta |

### Propuesto y NO construido (por orden de utilidad para el usuario de carga)
- **Editar una propuesta antes de publicarla** (hoy se publica el texto tal cual).
- **Historial por ficha**: quién la corrigió, cuándo y qué decía antes.
- **Registro de actividad compartido** (hoy es de cada computadora).
- **Intérprete de orden médica**: pegar el texto de la orden y que devuelva los códigos
  candidatos. Es la que más le ahorra al mostrador.
- **Vista mostrador simplificada**: sólo lo que hay que responderle al afiliado.
- **Navegación «volver» dentro de la ficha** (hoy se pierde el hilo al saltar entre códigos).
- **Buscador por droga** para autorizaciones de medicación (121 drogas / 22 patologías
  SURGE ya parseadas).
- **U.B. por fecha / por convenio** (hoy hay un solo valor por perfil).
- **Auditoría de facturación por lote**.
- **App instalable (PWA) + offline total** (manifest + service worker).
- **Registro de decisiones / historial de casos** vía Supabase (trazabilidad y estadística).
- **Novedades normativas / vigencias**.
- **Chat de consulta con IA**: se conversó, no se decidió. ⚠️ Incompatible con el requisito
  de funcionar **offline y sin servidor** salvo que se acepte una dependencia externa.

### Lo que queda por confirmar en los datos
- **84 títulos «denominación a confirmar»** (`titulo_revisar`): ninguna fuente los resuelve
  sin ambigüedad. Se corrigen desde **✎ Editar ficha** y vuelven al repo por 3.1.
- **139 fichas con el texto cortado en el origen** (`texto_truncado`): la planilla del Único
  capa las descripciones a **100 caracteres**. No es recuperable desde el PDF del PMO (trae
  títulos aún más cortos). Haría falta una planilla sin el capado.
- **215 equivalencias sin destino posible**: apuntan a códigos que no están en el Nacional
  cargado y no tienen equivalente por código ni por nombre. ~106 tienen un PMO con el mismo
  número disponible y se arreglarían con la misma regla.
- Las **22 equivalencias resueltas por nombre** conviene revisarlas: el criterio es
  estadístico (umbral 0,88), aunque el corrimiento del capítulo 260 se resolvió bien.
- **`130303` sin denominación**: OCR ilegible en origen. Se carga a mano desde ✎ Editar ficha.
- **3 títulos PMO con artefactos de OCR** (`070212`, `070702`, `110103`) y **3 que arrancan
  a mitad de frase** (`010208`, `110204`, `110212`).
- **4 títulos del Único médico con palabras fusionadas**: `160105`, `290202`, `290203`,
  `310125`.
- **`10300205`** conserva `(NO PMO pre CX Cataratas)` en el título **a propósito**: el
  paréntesis aporta información clínica además del marcador.
- Las siglas del marcador (`AA`, `AM`, `AF`, `BF`, `NC`, `SC`) **no están documentadas**: la
  planilla no trae leyenda. Se guardan literales, sin interpretar.
- **La lateralidad está relevada sólo en oftalmología**; el mismo dato existe en otros
  capítulos del Nacional.
- **6 equivalencias Único↔NBU dudosas por el tipo de muestra**: los dos nombres indican
  materiales sin nada en común (`60660192` creatinina orina vs. sangre, `60660307` etanol,
  `64665691` haemophilus, `64667076` levodopa, `64668332` pesticidas, `64669990` zinc). Cada
  ficha lo dice en auditoría. Hay que decidir con la planilla en la mano si la equivalencia
  está mal puesta o si el nombre del Único está mal copiado.
- **101 prácticas con U.B. distinta entre el Único y el NBU**: es el convenio de la empresa,
  no un error. La ficha muestra las dos y aclara cuál es cuál. Confirmar con el usuario si
  alguna de esas diferencias sí es un error de carga.

### Mejoras de datos ofrecidas y no ejecutadas
- Ampliar las **relaciones CIE-10 ↔ prácticas** (hoy 45 curadas + sugerencias por texto).
- **Precios de referencia** del Anexo IV del PMO.
- Revisión por el usuario del **mapeo código→patología SURGE** (38 códigos) y de los
  **CIE-10 por patología** (curados por palabra clave, orientativos).

### Preguntas abiertas al usuario (sin responder)
- ¿El «Requerimiento VISITAR» (Excel) debe seguir teniendo prioridad sobre el del PDF?
- ¿Mostrar u ocultar del listado los encabezados de especialidad del SURGE (ONCOLOGÍA,
  REUMATOLOGÍA…), que contienen el empadronamiento común?

---

## 9. Errores conocidos ya resueltos (no repetir)

### Datos y pipeline
| Problema | Solución aplicada |
|---|---|
| Título del Único con la **observación pegada** (`60660902`, `60660833`) | Los parsers separan **nombre / marcador / observación** en campos propios. La ficha los muestra por separado |
| 1.710 títulos del Único-lab arrastraban el marcador `(PMO AA)` | Se recorta a `marcador_unico` y se muestra como badge. En la parte médica sólo se recorta si el paréntesis es **únicamente** el marcador |
| Truncado a 100 chars no detectado en filas con espacios dobles (`64661195`) | Medir el corte sobre la **celda cruda**, antes de colapsar espacios |
| `130303` sin denominación (OCR ilegible) | Marca `sin_denominacion` y avisa en la ficha, **sin inventar** el título |
| **Oftalmología: títulos cortados entre códigos** (`300117` perdía «afectados», que abría `300118`) | Se **alinean ambos flujos** (PDF y OCR) con `difflib` y se arbitra; si no alcanza, con el nombre del Único |
| **Oftalmología: catálogo corrido un código** (`020108` era «vitrectomía» pero figuraba en `020107`) | Detectado por la misma alineación |
| **Equivalencias a códigos inexistentes** (`300113` → `300153`) | Se re-resuelve por código idéntico y, si no, por proximidad de nombre |
| **Lateralidad ignorada** (el Nacional anota BILATERAL) | Se extrae del OCR **buscando sobre el flujo de letras** (vienen pegadas), se propaga al Único y la Mesa de trabajo rechaza un bilateral con cantidad > 1 |
| **Capítulo mal asignado en códigos del Único de 8 dígitos** (`10300122`, oftalmológico, mostraba «Aparato urinario y genital masculino») | Esos códigos llevan 2 dígitos propios delante: el capítulo son los **dígitos 3º y 4º**. `cap_prefijo()` en `assemble.py` |
| Al extender la realineación, el recorte se tragaba la cobertura del código siguiente (`070115`: 39 → 831 caracteres) | Guarda de **proporción** (3×) contra la firma del OCR + tope duro de 160 caracteres |
| Cortes a mitad de palabra al realinear (`radiol`) | Se completa la palabra en vez de cortarla |
| Nombre del capítulo arrastrado al título (`Oftalmología oftalmodinamometría`) | Se quita el nombre del capítulo cuando encabeza el título |
| Pérdida de acentos al arbitrar con el nombre del Único | El candidato del Único se **penaliza -0,05** para preferir el acentuado |
| Equivalencia por nombre con falsos positivos graves (`Centellograma de cerebro` → `…de bazo`, 0,83) | Umbral subido de **0,80 a 0,88** |
| Cobertura PMO absorbía prestaciones ajenas (`380101` arrastraba Cámara Hiperbárica) | Códigos pegados al título en el PDF (`380201Cámara`); se detectan y se filtran artefactos de página |
| SURGE vinculado en un nomenclador y no en otro (`070208`) | Grafo de equivalencias + propagación transitiva |
| Siglas duplicadas (`ABDI`) | Dedup por sigla + significado normalizado |
| CIE-10 con capítulos '?' y descripciones fragmentadas | Rangos de capítulo extendidos + guard `is_frag` + normalización final |
| `isquemia` etiquetada como determinación en sangre | `MUESTRA_SUF_EXCL` |

### Nube, seguridad y publicación (esta etapa) — los que más costaron

| Problema | Causa real y solución |
|---|---|
| **El alta de cuentas fallaba** con «Unexpected failure, please check server logs» | `un_solo_admin()` era la **única función del SQL sin `security definer`**. Es un *constraint trigger* diferido: corre al confirmar la transacción y con los permisos de quien confirma, que en un alta es el rol interno de Supabase Auth, sin lectura sobre `public.perfiles`. Moría con *permission denied* y Auth devolvía un 500 genérico. **No se reproduce si la maqueta de prueba no incluye el rol `supabase_auth_admin`** |
| **El `update` para hacerse administrador «funcionaba» y no hacía nada** | `perfiles_guardia` revierte rol y estado cuando `es_admin()` da falso, y en el SQL Editor `auth.uid()` es NULL. La consola contesta `UPDATE 1` y la cuenta sigue pendiente. Se reemplazó por `hacerme_admin()`, que apaga el guardia sólo dentro de su transacción. Necesita `set constraints … immediate` antes del `ALTER`, o falla con *pending trigger events* |
| **El aviso «hay una versión nueva» no salía NUNCA** | El service worker devolvía la respuesta cacheada a la página y **después** intentaba clonarla para compararla; clonar una respuesta ya leída lanza excepción y un `.catch()` se la tragaba. La copia se saca **antes** de devolverla |
| **El cartel de «Instalar» era invisible** | `#swbar` en `z-index:120` contra `#gate` en `1000`, con fondo opaco a pantalla completa. Aparece en la primera visita, que es justo cuando se ve el ingreso: nadie lo habría visto |
| **XSS almacenado en el logo** | `logoInner()` interpolaba `CONTENT.page.logo` en un `src` sin escapar. Dejó de ser dato de confianza al pasar a la nube (y entra también por «Restaurar respaldo»). Se escapa **y** se exige que sea imagen embebida; SVG queda afuera por ser el único formato que puede traer código |
| **Una solicitud del administrativo no le llegaba al administrador** | El contador se calculaba sobre lo cargado en esa computadora, que era de cuando esa persona inició sesión. Ahora sale de `pendientes()`, y se refresca al volver a la pestaña, cada minuto y al abrir el panel |
| «Get Pages site failed» × 6 | GitHub Pages nunca se había habilitado. **No se puede automatizar**: `enablement: true` falla con *Resource not accessible by integration* |
| «Email logins are disabled» | Al reactivar el proveedor de correo, *Confirm email* se enciende con él. Son dos interruptores distintos |
| Cuenta aprobada que igual no entra | Son **dos puertas**: `perfiles.estado` (nuestra) y `auth.users.email_confirmed_at` (de Supabase). Apagar *Confirm email* no confirma hacia atrás |
| El enlace de restablecer llevaba a `localhost` | *Site URL* de Supabase por defecto. Pero además la app no sabía leer el enlace: ver 4.4 bis |
| Al probar, «Ana» entraba como administradora | El simulador tenía la identidad fija. **La identidad es por sesión, la base es compartida** |
| Al probar dos variantes en el mismo puerto, se servía siempre la primera | El service worker cachea y usa `index.html` como respaldo de cualquier navegación. Un puerto por variante |

### App y UI
| Problema | Solución aplicada |
|---|---|
| **`toast is not defined`** al usar propuestas, **comparador** o copiar informe | `toast` vive dentro del IIFE de auth; se expuso un puente `window.NBUToast` + wrapper en el ámbito exterior. ⚠️ Un test que sólo verifica «se abrió el modal» **no detecta esto** |
| **Selector de nomenclador invisible en móvil** — la app no tenía forma de cambiar de nomenclador en el celular | `.modesel{display:none}` estaba **después** de la media query y la pisaba. Se movió antes |
| Las sugerencias del estado vacío nunca aparecían | Se calculaban con **la misma búsqueda que acababa de fallar**; ahora busca término por término |
| **Glitch al scrollear** en el navbar y la barra lateral | Dos causas: `--hh` se medía **en el mismo frame** que la animación (la barra saltaba 183→173→170→167), y el **scroll anchoring** del navegador cruzaba un único umbral en ida y vuelta produciendo flip-flop. Solución: `ResizeObserver` para medir la cabecera + umbrales separados (`HDR_COMPACTA=220`, `HDR_EXPANDE=90`) |
| **La pantalla `'espera'` del alta de cuenta no renderizaba** | La rama `if(v==='espera')` se había insertado **arriba de la cadena if/else de `renderGate`**, interceptando la vista antes de armar el HTML y buscando un botón que todavía no existía. Los listeners van en **`wireGate`**, no en `renderGate` |
| Ficha del Único mostraba el badge «NBU» | Faltaba `UNICO` en el mapa de nomencladores de `openCode()` |
| Scroll horizontal en móvil | Grilla en el selector + `minmax(0,1fr)` + `min-width:0` en `<main>` |
| Playwright: clics interceptados | Cerrar **`#tour`** y `#onboard` y el `#scrim` antes de interactuar |
| Tests que se rompen solos al cambiar la UI | Los selectores viejos quedan colgados (tarjeta ODO eliminada, pestaña 'Propuestas'→'Pendientes', overlay `#onboard`→`#tour`). Revisar la suite después de cada cambio de UI |
| Publicación del artefacto con **409** | `WebFetch` de la URL primero, comparar y republicar |
| `inject_db.py` «no encontrado» | El cwd del shell **persiste** entre llamadas tras un `cd`; usar rutas absolutas |

---

## 10. Método de trabajo que viene funcionando

1. **Medir antes de proponer.** Contar sobre `nbu_db.json` cuántos casos tiene el problema
   antes de decidir si vale la pena tocarlo.
2. **Verificar contra la base después de cambiar.** Toda reparación masiva de títulos o
   equivalencias introdujo al menos una regresión que sólo apareció comparando el antes y
   el después código por código.
3. **Cruzar dos fuentes imperfectas.** El PDF del PMO y el OCR del Nacional fallan distinto:
   juntos revelaron defectos que ninguno mostraba solo (el corrimiento de un código en
   oftalmología).
4. **Nunca completar lo que la fuente no dice.** Marcar y avisar en la ficha
   (`titulo_revisar`, `texto_truncado`, `sin_denominacion`) es preferible a inventar.
5. **El conocimiento del usuario entra por archivo curado**, con prioridad sobre el
   pipeline, y **vuelve al repo** por el exportador (3.1).
6. **Correr la suite de Playwright completa** antes de commitear: los cambios de UI rompen
   tests lejanos.
7. **Reproducir el fallo antes de arreglarlo, y con la maqueta completa.** Los dos bugs más
   caros de esta etapa (el alta de cuentas y el `update` que no actualizaba) se escondían
   porque la prueba corría con permisos de más. Una maqueta que no distingue roles no
   prueba reglas de acceso: las confirma por casualidad.
8. **Desconfiar de la propia medición antes que del código.** Varias veces el «bug» era del
   instrumento: el analizador de contraste leía mal un formato de color, el simulador tenía
   la identidad fija, una prueba tocaba la tecla después de que llegara el mensaje. Cuando
   algo no cierra, revisar primero cómo se está midiendo.
9. **Un texto que describe mal dónde están los datos es peor que no tenerlo**, porque se le
   cree. Al mover algo de lugar, buscar los carteles que hablaban de eso.
