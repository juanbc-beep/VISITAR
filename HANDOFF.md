# TRASPASO DE SESIÓN — Manual Inteligente Unificado (VISITAR SRL)

> Documento para retomar el trabajo en una sesión nueva sobre **el mismo artefacto**.
> Última actualización: 2026-07-28 (commit `7bbaa70`, 63 commits).

---

## 1. Identificación del proyecto

| Dato | Valor |
|---|---|
| **Repo** | `juanbc-beep/VISITAR` (dir. de trabajo `/home/user/VISITAR`) |
| **Rama de desarrollo** | `claude/unified-medical-codes-manual-o9nw1w` (⚠️ NO pushear a otra rama) |
| **Artefacto publicado** | https://claude.ai/code/artifact/85d149a9-9bfb-478b-b817-3d039a335f1f |
| **Archivo de la app** | `web/index.html` — HTML **autocontenido** (~1,35 MB) |
| **Usuario** | Experto en auditoría médica y facturación en VISITAR SRL |
| **Autoría a mostrar** | «Diseñado por **Juan Pablo Besada**» (ver punto 6.11) |
| **Idioma de trabajo** | Español (Argentina) |

**Para republicar el artefacto** (misma URL): copiar `web/index.html` al scratchpad como
`nbu_artifact.html` y llamar a la herramienta Artifact pasando `url` =
`https://claude.ai/code/artifact/85d149a9-9bfb-478b-b817-3d039a335f1f`, con
`favicon: 🩺`. **Siempre la misma URL**, nunca crear una nueva.

> Si la publicación devuelve **409 (conflicto)**: hacer `WebFetch` de la URL primero para
> traer la versión publicada, comparar contra el repo y recién entonces republicar.

---

## 2. Qué es la app — y para qué la usa el usuario

Un **manual inteligente unificado de códigos médicos argentinos**, en un único archivo
HTML que funciona **sin servidor y sin internet**.

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
| Códigos con **abreviaturas posibles** | 1.022 |
| Códigos con **tipo de muestra** (sangre/orina) | 776 (703 por texto + 73 por sufijo) |
| Códigos con **diagnósticos CIE-10** relacionados | 242 |
| Códigos con **cobertura** | 115 → 106 *obligación* + 9 *observación* |
| Códigos con **lateralidad** | 130 (109 del OCR + 21 curados por auditoría) |
| Códigos con **normativa** relacionada | 61 |
| Códigos con **vínculo SURGE** | 60 |
| Códigos con **tope PMO** | 38 |
| Pares **-emia / -uria** vinculados | 25 |
| Único **sin equivalencia** (agrupados aparte) | 79 |
| Marcador del Único separado del título | 1.724 |
| **Marcas de calidad** | 84 `titulo_revisar` · 139 `texto_truncado` · 1 `sin_denominacion` |

---

## 3. Arquitectura y pipeline

### Estructura
```
/home/user/VISITAR
├── web/index.html                  # LA APP (autocontenida; DB embebida comprimida)
├── data/                           # fuentes + JSON intermedios + nbu_db.json (12 MB)
│   ├── lateralidad_curada.json     # ← dato de la casa (ver 3.1)
│   └── correcciones_curadas.json   # ← dato de la casa (ver 3.1)
├── scripts/                        # parsers + ensamblador + inyector
├── README.md                       # documentación funcional
└── HANDOFF.md                      # este documento
```

### Cómo se compila la base
1. **Parsers** (`scripts/parse_*.py`) → JSON intermedios en `data/`.
2. **`scripts/assemble.py`** → une todo en `nbu_db.json` (6.346 códigos + datasets).
3. **`scripts/inject_db.py`** → comprime la DB (**gzip + base64**) y la embebe en
   `web/index.html` dentro de `<script id="nbu-db-gz" type="text/plain">`.
   La app la descomprime al cargar con `DecompressionStream('gzip')` en un IIFE async.

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
`cie10_relaciones.py`, `parse_abreviaturas.py`, `parse_surge.py`.

### Testing
No hay framework. Se valida con **Playwright** (Node) desde el scratchpad:
```js
import pkg from '/opt/node22/lib/node_modules/playwright/index.js';
const { chromium } = pkg;   // playwright NO está en node_modules del repo
```
Para pasar el acceso en los tests (crea empresa + perfil administrador de una):
```js
await p.fill('#suUser','emp'); await p.fill('#suPass','1234');
await p.fill('#suName','Ana'); await p.fill('#suPPass','1234');
await p.click('#suGo'); await p.waitForTimeout(1200);
await p.evaluate(()=>{['onboard','tour'].forEach(i=>document.getElementById(i)?.classList.remove('on'));
  localStorage.setItem('nbu-onboarded','1');document.getElementById('scrim')?.classList.remove('on');});
```
⚠️ El overlay del recorrido guiado es **`#tour`** (antes `#onboard`); ambos se cierran por
las dudas. Si no se cierran, **interceptan todos los clics** y los tests fallan raro.

**Suite de regresión** (en el scratchpad; recrearla si se perdió):
`test_cuentas`, `test_tour`, `test_pend`, `test_carga`, `test_muestra`, `test_busq`,
`test_cob`, `test_ux2`, `test_smoke`, `test_pleg`, `test_vacio`, `test_imp`, `test_autoria`.
Al 2026-07-28 pasan **todas, sin errores JS**.

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
6. **Impresión**: `body.imp-ficha` imprime sólo la ficha, y `imprimirComprobante()` genera
   un **comprobante para el afiliado** (qué presentar, sin datos internos: no muestra U.B.,
   ni valores, ni normas).

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

### 4.4 Acceso, cuentas y perfiles
- Acceso de **empresa** (usuario compartido) + **perfiles individuales**.
- **PBKDF2/SHA-256** (310.000 iteraciones, salt por registro), bloqueo por intentos
  fallidos, auto-logout por inactividad (25 min).
- **Alta de cuenta con aprobación** (último trabajo hecho):
  `administrativo → crea cuenta → estado 'pendiente' → administrador aprueba → puede entrar`.
  La cuenta pendiente **no aparece** en la lista de perfiles (si apareciera, la persona
  intentaría entrar sin entender el rechazo); en su lugar hay un aviso al pie con cuántas
  esperan. Pantalla `'espera'` del gate: *«Cuenta creada … pendiente de aprobación»*.
  `enterProfile()` **bloquea** una cuenta pendiente aunque la contraseña sea correcta.
- **Administrador único**: el botón de rol **transfiere** la administración (con confirm y
  aviso de que dejás de serlo), no suma un segundo admin; y **el administrador no se puede
  eliminar** — primero hay que transferir el rol.
- **Panel de administración** (`openAdmin`), pestañas:
  `Perfiles · Pendientes · Empresa · Textos · Nube · Registro · Respaldo`.
- **Sincronización Supabase** opcional (REST + polling) con cifrado **AES-GCM** por
  passphrase. ⚠️ La anon key es pública → **no cargar datos de pacientes**.
  ⚠️ **No funciona dentro del artefacto**: la CSP bloquea el fetch a Supabase. Sirve sólo
  si el HTML se sirve desde otro lado.

### 4.5 Recorrido guiado (onboarding)
`pasosTour()` — **20 pasos** para el administrativo, **23** para el administrador (suma
Pendientes, Modo edición y Administración). Es un **spotlight**: recorta el elemento real
con `box-shadow: 0 0 0 9999px` y ubica el globo al lado. Varios pasos tienen `antes:` que
prepara la pantalla (abre el rail, abre una ficha, carga un caso en la Mesa de trabajo).
Se puede volver a ver desde **Glosario y leyes → Ver tutorial de uso**.

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
8. No cargar datos sensibles de pacientes (la anon key de Supabase es pública).
9. Dominio `ais.paho.org` **bloqueado** por política de red — no reintentar ni rodear.
10. Servidores MCP **Adobe** y **Whimsical** requieren autorización → no disponibles.
11. **La autoría debe quedar registrada en lugar visible**: «Diseñado por **Juan Pablo
    Besada**». Motivo textual del usuario: *«para que nadie pueda decir que el trabajo fue
    realizado por él»*. Hoy figura en **5 lugares**: pie de la app (`.autoria`), todas las
    pantallas de acceso (`.au-gate`, se inyecta en cualquier `.gcard`), encabezado de
    impresión del listado y de las dos auditorías, y el informe copiable.
12. **Odontología está oculto**: `NOMEN_OCULTOS = new Set(['ODO'])`. Los 79 códigos siguen
    en la base (no se borraron), pero no se listan ni se buscan. VISITAR no lo usa.
13. **Regla de nombres de laboratorio** dictada por el usuario:
    **`-emia` = en sangre** (glucemia, uremia) · **`-uria` = en orina** (hematuria,
    glucosuria). Se aplica en `assemble.py` (`MUESTRA_TEXTO`, sufijos) y se muestra como
    etiqueta de color en la fila y en la ficha, con filtros «en sangre» / «en orina».
    ⚠️ **Excepción**: `MUESTRA_SUF_EXCL = {"isquemia"}` — termina en `-emia` y no es una
    determinación en sangre. Si aparecen más falsos positivos, van ahí.

---

## 7. Historial de trabajo (63 commits)

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

---

## 8. Pendientes y sugerencias abiertas

### Propuesto y NO construido (por orden de utilidad para el usuario de carga)
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
