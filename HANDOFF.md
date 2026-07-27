# TRASPASO DE SESIÓN — Manual Inteligente Unificado (VISITAR SRL)

> Documento para retomar el trabajo en una sesión nueva sobre **el mismo artefacto**.
> Última actualización: 2026-07-27.

---

## 1. Identificación del proyecto

| Dato | Valor |
|---|---|
| **Repo** | `juanbc-beep/VISITAR` (dir. de trabajo `/home/user/VISITAR`) |
| **Rama de desarrollo** | `claude/unified-medical-codes-manual-o9nw1w` (⚠️ NO pushear a otra rama) |
| **Artefacto publicado** | https://claude.ai/code/artifact/85d149a9-9bfb-478b-b817-3d039a335f1f |
| **Archivo de la app** | `web/index.html` — HTML **autocontenido** (~1,2 MB) |
| **Usuario** | Experto en auditoría médica y facturación en VISITAR SRL |
| **Idioma de trabajo** | Español (Argentina) |

**Para republicar el artefacto** (misma URL): copiar `web/index.html` al scratchpad como
`nbu_artifact.html` y llamar a la herramienta Artifact pasando `url` =
`https://claude.ai/code/artifact/85d149a9-9bfb-478b-b817-3d039a335f1f`, con
`favicon: 🩺`. **Siempre la misma URL**, nunca crear una nueva.

---

## 2. Qué es la app

Un **manual inteligente unificado de códigos médicos argentinos**, en un único archivo
HTML que funciona **sin servidor y sin internet**. Sirve a dos sectores de VISITAR:
**auditoría de facturación** y **auditoría de autorizaciones a afiliados**.

### Contenido de la base (cifras actuales verificadas)

| Dataset | Cantidad |
|---|---|
| **Códigos totales** | **6.344** |
| — NBU (laboratorio/bioquímica) | 1.815 |
| — PMO / Prestaciones médicas | 1.219 |
| — Odontología | 79 |
| — Nomenclador Único (VISITAR) | 3.231 |
| **CIE-10** (diagnósticos) | **11.581** (2.024 categorías + ~9.500 subcategorías) |
| **Abreviaturas médicas** | **1.780** significados / 1.413 siglas únicas |
| **SURGE** (Res. 731/23) | **58** secciones del Anexo II |
| **Leyes / normas** | 22 |
| Glosario | 12 |

### Cruces / inteligencia ya construida

| Relación | Cobertura |
|---|---|
| Códigos con vínculo **SURGE** | 52 (38 marcados `(SUR)/(SURGE)` + 17 propagados por equivalencia) |
| Códigos con **abreviaturas posibles** | 1.023 (eran 1.025; bajan 3 falsos positivos y sube 1 real al limpiar los títulos) |
| Códigos con **cobertura obligatoria PMO** | 65 |
| Códigos con **diagnósticos CIE-10** relacionados | 242 |
| Códigos con **normativa** relacionada | 61 |
| Único **sin equivalencia** (agrupados aparte) | 79 |
| Generalidades PMO / topes | 14 / 26 |

---

## 3. Arquitectura y pipeline

### Estructura
```
/home/user/VISITAR
├── web/index.html          # LA APP (autocontenida; DB embebida comprimida)
├── data/                   # fuentes + JSON intermedios + nbu_db.json (12 MB)
├── scripts/                # parsers + ensamblador + inyector
├── README.md               # documentación funcional
└── HANDOFF.md              # este documento
```

### Cómo se compila la base
1. **Parsers** (`scripts/parse_*.py`) → JSON intermedios en `data/`.
2. **`scripts/assemble.py`** → une todo en `nbu_db.json` (6.344 códigos + datasets).
3. **`scripts/inject_db.py`** → comprime la DB (**gzip + base64**) y la embebe en
   `web/index.html` dentro de `<script id="nbu-db-gz" type="text/plain">`.
   La app la descomprime al cargar con `DecompressionStream('gzip')` en un IIFE async.
   *Esto bajó el HTML de ~9 MB a ~1,2 MB.*

### ⚠️ Cómo ejecutar assemble.py (IMPORTANTE)
`assemble.py` necesita JSON intermedios que **viven en el scratchpad**, no en el repo.
Procedimiento probado:
```bash
SP="<scratchpad>/"                      # dir. scratchpad de la sesión
cp scripts/assemble.py "$SP/assemble.py"
cp data/<json que hayas regenerado> "$SP/"     # y también a "$SP/data/" si aplica
cd "$SP" && python3 assemble.py                 # genera $SP/nbu_db.json
cp "$SP/nbu_db.json" /home/user/VISITAR/data/nbu_db.json
cd /home/user/VISITAR && python3 scripts/inject_db.py
```
Si en la sesión nueva el scratchpad está vacío, hay que regenerar los intermedios
corriendo los parsers correspondientes desde `data/` (las fuentes originales están
versionadas: `pmo.pdf`, `cie10.pdf`, `surge.pdf`, `surge.ods`, `unico_*.xls(x)`, etc.).

### Parsers disponibles
`parse_catalog.py`, `parse_intel.py`, `parse_pmo.py`, `parse_pmo_cobertura.py`,
`parse_nn.py`, `parse_odo.py`, `ocr_nn.py`, `parse_unico.py`, `parse_unico_lab.py`,
`parse_cie10.py`, `parse_cie10_detalle.py`, `parse_cie10_tabular.py`,
`cie10_relaciones.py`, `parse_abreviaturas.py`, `parse_surge.py`.

### Testing
No hay framework de tests. Se valida con **Playwright** (Node) desde el scratchpad:
```js
import pkg from '/opt/node22/lib/node_modules/playwright/index.js';
const { chromium } = pkg;   // playwright NO está en node_modules del repo
```
Para pasar el login de la app en los tests:
```js
await p.fill('#suUser','e'); await p.fill('#suPass','1234');
await p.fill('#suName','J'); await p.fill('#suPPass','1234');
await p.click('#suGo'); await p.waitForTimeout(900);
await p.evaluate(()=>{const o=document.getElementById('onboard'); if(o)o.classList.remove('on');});
```
(El overlay `#onboard` intercepta clics si no se cierra.)

---

## 4. Funcionalidades de la app

### Navegación principal
5 tarjetas: **Buscar en todo** (búsqueda global) · **Laboratorio (NBU)** ·
**Prestaciones médicas (PMO)** · **Odontología** · **Único (VISITAR)**.

### Consulta rápida (fila aparte, 3 tarjetas)
- **Diagnósticos (CIE-10)** — 11.581 diagnósticos por capítulo, con prácticas relacionadas.
- **Abreviaturas** — 1.413 siglas (Hospital Italiano + INSN); una fila por sigla, el
  detalle lista todas sus acepciones y las prácticas que pueden pedirse con ella.
- **SURGE** — 58 secciones del Anexo II Res. 731/23 agrupadas por especialidad.

### Vistas
- **Listado** (con filtros por sección/grupo/reglas, favoritos, export CSV/PDF)
- **Árbol de módulos** (solo NBU y Único)
- **Mesa de trabajo** ← ver punto 5

### Ficha de cada código
Valorización (U.B. y arancel), equivalencias entre nomencladores, relaciones
(incluye / no incluye / incluido en), frecuencia y seriado, asociación de códigos,
sinónimos y abreviaturas, **«Puede abreviarse en la orden»**, normas de auditoría,
**Cobertura obligatoria (PMO)**, **Sistema Único de Reintegro (SURGE)**,
**Diagnósticos CIE-10 relacionados**, **Normativa relacionada**, notas personales.

### Acceso y perfiles
- Login de **empresa** + **perfiles individuales** (nombre + contraseña) que conservan
  favoritos, notas y U.B. propios.
- **PBKDF2/SHA-256** (310.000 iteraciones, salt por registro), bloqueo por intentos
  fallidos, auto-logout por inactividad (25 min).
- El **perfil admin está oculto** para usuarios "empresa".
- **Panel de administrador**: edición de fichas y textos generales.
- **Sincronización Supabase** opcional (REST + polling) con cifrado **AES-GCM**
  opcional mediante passphrase. ⚠️ La anon key es pública → **no cargar datos
  sensibles de pacientes**.
- **Onboarding** para el primer uso · branding **VISITAR SRL** con logo cargable.

### Diseño
Responsive verificado en 360 / 620 / 768 / 900 / 1280 px (sin scroll horizontal),
tema claro/oscuro, atajos de teclado (`/`, `↑`/`↓`, `Enter`), objetivos táctiles ≥42 px,
aria-labels, `role="tablist"`, `aria-modal`, `focus-visible`.

---

## 5. Mesa de trabajo (lo último construido)

Una sola carga de códigos del caso (acepta **6 dígitos** NBU/PMO/Odonto y **8 dígitos**
Único; cantidades con `×N`), auditable en **dos modos**:

**💲 Auditoría de facturación** — doble facturación por inclusión en módulos, urgencias
sin 661200, Acto Bioquímico faltante, seriados excedidos, desuso, códigos inexistentes;
total en **U.B. netas y $**; export CSV/PDF.

**📋 Auditoría de autorización** — ⚠️ **TODAS las prácticas se tratan como
«autorización previa»** (ver punto 6). Arma el **checklist de documentación a solicitar
al afiliado** (requerimientos SURGE consolidados y deduplicados), lista las
**patologías SURGE**, el **diagnóstico CIE-10 justificante** sugerido y la
**normativa aplicable**; exporta el dictamen (CSV/PDF).

Funciones clave en el código: `initValidator()`, `runCase()`, `renderCase()`,
`renderFacturacion()`, `renderAutorizacion()`, `exportValidatorCSV()`, `exportAuthCSV()`.

---

## 6. ⚠️ REGLAS Y DECISIONES DEL USUARIO (respetar siempre)

1. **NO inferir qué requiere autorización previa y qué no.** El usuario nunca entregó
   ese listado. **Todas las prácticas se toman como autorización previa.** Si en el
   futuro pasa un listado real, recién ahí se aplica el criterio.
2. **No inventar contenido normativo.** Todo dato de cobertura, requisitos o topes debe
   salir del PDF/Excel oficial parseado, no de conocimiento general.
3. **Sección Medicamentos: eliminada** (el usuario la descartó explícitamente).
4. **CIE-10 no es un nomenclador**, es un apartado de consulta para administrativos.
5. Pushear **solo** a `claude/unified-medical-codes-manual-o9nw1w`.
6. **No crear PR** salvo pedido explícito.
7. **Republicar siempre en la misma URL del artefacto.**
8. No cargar datos sensibles de pacientes (Supabase anon key es pública).
9. Dominio `ais.paho.org` **bloqueado** por política de red — no reintentar ni rodear.
10. Servidores MCP **Adobe** y **Whimsical** requieren autorización → no disponibles.

---

## 7. Historial de trabajo (39 commits)

**Base y nomencladores**
1. Parseo del catálogo NBU (PMO + Prácticas Especiales) e inteligencia (sinonimias,
   abreviaturas, normas). Modelo de datos unificado. Interfaz navegable.
2. Arancel por U.B., favoritos, export CSV/PDF, reglas de frecuencia/seriado, validador.
3. Integración del **Nomenclador Nacional / Catálogo PMO** + valores por OCR.
4. U.B. vigentes desde XLS. Pulido de nombres dentales (odontología).

**Acceso, admin y branding**
5. Perfiles + login empresa, panel admin, sincronización Supabase, ocultar admin,
   branding VISITAR, onboarding, endurecimiento de seguridad.

**Nomenclador Único**
6. Integración del Único con **equivalencias bidireccionales** desde XLSX; los que no
   tienen equivalencia se agrupan aparte (79).
7. Parte de **laboratorio** del Único (código = prefijo 2 díg. + código NBU), heredando
   la inteligencia del NBU (relaciones, parentesco, árbol de módulos).

**Normativa y diagnósticos**
8. 22 leyes/normas con detalle y vínculo por código, propagado a todos los nomencladores.
9. **CIE-10 completo**: 12 tomos del PDF tabular → 11.581 diagnósticos, con herencia
   subcategoría→categoría y relación bidireccional con las prácticas.
10. **Compresión gzip+base64**: HTML de ~9 MB → ~1,2 MB.

**PMO**
11. Re-parseo de la Res. 201/02 (columna a columna): títulos limpios, **cobertura
    obligatoria**, **topes** (FKT, salud mental), **generalidades**, Anexos III y IV.
12. **Corrección importante**: la "Cobertura obligatoria" absorbía prestaciones ajenas
    (caso `380101` puvaterapia arrastraba Cámara Hiperbárica, internación, análisis…).
    Causa: códigos pegados al título en el PDF (`380201Cámara`). Corregido → 0 fugas.

**Consulta rápida**
13. Eliminación de Medicamentos; CIE-10 reencuadrado como apartado de consulta.
14. **Abreviaturas médicas** (HIBA + INSN) con dedup de siglas repetidas (caso `ABDI`)
    y registro de «puede abreviarse» en 1.025 prácticas.
15. **Búsqueda global** "Buscar en todo" (cruza los 4 nomencladores + CIE + abreviaturas,
    resultados agrupados por origen).

**SURGE**
16. Sección SURGE (Res. 731/23) con patologías, medicación y requerimiento VISITAR.
17. **Parseo completo del PDF de 67 páginas**: las 58 secciones del índice (incluidos los
    8 títulos partidos en dos líneas, como *Prótesis de implante traumatológicas* p. 53),
    con tecnología, fundamento terapéutico, información requerida, sub-módulos A/B/C/D,
    prestaciones incluidas y observaciones → 1.844 bloques, ~113.000 caracteres.
18. **Corrección importante**: el vínculo SURGE se propagaba un solo salto y quedaban
    códigos vinculados en un nomenclador y no en otro (caso `070208`: sí en Prestaciones
    y en el Único `(SURGE)`, no en el Único base). Ahora se construye el **grafo de
    equivalencias** y se propaga por todo el componente conexo → 52 códigos.

**Mesa de trabajo**
19. Validador reencuadrado en Mesa de trabajo con los dos modos de auditoría.
20. Ajuste final: todas las prácticas = autorización previa.

**Calidad de datos — oftalmología**
23. **Capítulo de oftalmología revisado** (prefijos `02` y `30`, 69 códigos): 30 títulos
    recompuestos, 8 equivalencias reparadas y 28 fichas con **lateralidad**
    (Bilateral / Unilateral / Uni o bilateral). Ver punto 9.

**Calidad de datos — títulos**
22. **Auditoría de títulos de los 6.344 códigos.** La planilla del Único mezclaba en una
    sola celda el nombre de la práctica, un marcador de clasificación y, en algunas filas,
    una observación. Se separaron en campos propios: **1.724 títulos** quedaron con sólo el
    nombre, **20 observaciones** pasaron a su sección y **139 fichas** avisan que el texto
    viene cortado en el origen. Ver punto 9.

**UI/UX**
21. Barra de conteos eliminada (quedan solo Valor U.B. y Favoritos); rediseño de
    Consulta rápida; responsive completo sin scroll horizontal.

---

## 8. Pendientes y sugerencias abiertas

**Sugerido y no implementado** (el usuario eligió primero la Mesa de trabajo):
- **Selector de rol + semáforo en la ficha** — que cada código muestre su estado sin
  pasar por la Mesa de trabajo. *(Ojo: sujeto a la regla 6.1 — hoy todo es autorización previa.)*
- **Registro de decisiones / historial de casos** vía Supabase: nº de caso, decisión
  (aprobado/observado/rechazado), motivo, fecha, auditor. Trazabilidad y estadística.
- **Buscador por droga** para autorizaciones de medicación (la data ya está en SURGE).
- **App instalable (PWA) + offline total** (manifest + service worker).
- **Novedades normativas / vigencias**.

**Oftalmología — lo que queda por confirmar:**
- **2 denominaciones marcadas «a confirmar»** (`titulo_revisar`): `020103` y `020502`.
  Ninguna fuente las resuelve sin ambigüedad; la ficha lo avisa y se corrigen desde
  **✎ Editar ficha**.
- **9 códigos del Único sin destino en el Nacional** (`300130` autorrefractometría,
  los agregados manuales `103002xx`, etc.): no existen en el catálogo cargado.
- **La lateralidad sólo está cargada en oftalmología** (28 fichas), porque es donde el
  usuario la señaló. El mismo dato existe en otros capítulos del Nacional.
- **Las otras 332 equivalencias colgadas** (fuera de oftalmología) siguen sin resolver:
  apuntan a códigos que no están en el catálogo. 106 de ellas tienen un PMO con el
  **mismo número** disponible, así que se arreglarían con la misma regla.
- El **corrimiento de títulos entre códigos** afecta también a otros capítulos del PMO;
  sólo se reparó oftalmología por pedido explícito.

**Defectos de título que quedan abiertos (dependen de la fuente, no se inventó texto):**
- **139 fichas con el texto cortado en el origen** (`texto_truncado`): la planilla del
  Único capa las descripciones a **100 caracteres**. El final se perdió en el archivo,
  no es recuperable desde el PDF del PMO (que trae títulos aún más cortos). Hoy la ficha
  avisa del corte. Para recuperarlos hace falta una planilla sin el capado.
- **`130303` sin denominación**: el OCR del PDF dejó el título ilegible. Se puede cargar
  a mano desde **✎ Editar ficha** (admin).
- **3 títulos PMO con artefactos de OCR**: `070212`, `070702`, `110103` (arrancan con
  «PMo…» y traen palabras fusionadas).
- **3 títulos PMO que arrancan a mitad de frase**: `010208`, `110204`, `110212`.
- **4 títulos del Único médico con palabras fusionadas** (falta un espacio en la fuente):
  `160105`, `290202`, `290203`, `310125`.
- **`10300205`** conserva `(NO PMO pre CX Cataratas)` en el título **a propósito**: el
  paréntesis aporta información clínica además del marcador.
- El significado de las siglas del marcador (`AA`, `AM`, `AF`, `BF`, `NC`, `SC`) **no está
  documentado**: la planilla no trae leyenda. Se guarda literal y sin interpretar.

**Mejoras de datos ofrecidas y no ejecutadas:**
- Ampliar las **relaciones CIE-10 ↔ prácticas** (hoy 45 diagnósticos curados + sugerencias
  automáticas por texto).
- **Precios de referencia** del Anexo IV del PMO (tabla de precios de medicamentos).
- Revisión por el usuario del **mapeo código→patología SURGE** (38 códigos) y de los
  **CIE-10 por patología** (curados por palabra clave, orientativos).

**Preguntas abiertas planteadas al usuario (sin responder):**
- ¿El «Requerimiento VISITAR» (Excel) debe seguir teniendo prioridad sobre el del PDF?
- ¿Mostrar u ocultar del listado los encabezados de especialidad del SURGE
  (ONCOLOGÍA, REUMATOLOGÍA, etc.), que contienen el empadronamiento común?

---

## 9. Errores conocidos ya resueltos (no repetir)

| Problema | Solución aplicada |
|---|---|
| Título del Único con la **observación pegada** (`60660902` «UremiaObservaciones: …», `60660833`) | Los parsers separan **nombre / marcador / observación** en campos propios (`marcador_unico`, `observacion_unico`, `texto_truncado`). La ficha los muestra por separado |
| 1.710 títulos del Único-lab arrastraban el marcador `(PMO AA)` / `(NO PMO BF NC)` | Se recorta a `marcador_unico` y se muestra como badge. En la parte médica sólo se recorta si el paréntesis es **únicamente** el marcador (para no perder `(NO PMO pre CX Cataratas)`) |
| Truncado a 100 chars no detectado en filas con espacios dobles | Medir el corte sobre la **celda cruda**, antes de colapsar espacios |
| Ficha del Único mostraba el badge «NBU» | Faltaba `UNICO` en el mapa de nomencladores de `openCode()` |
| `130303` sin denominación (OCR ilegible en origen) | Guarda final en `assemble.py`: marca `sin_denominacion` y avisa en la ficha, **sin inventar** el título |
| **Oftalmología: títulos cortados entre códigos** (`300117` perdía «afectados», que abría `300118`) | El PDF del PMO trae el texto bien escrito pero mal cortado; el OCR del Nacional lo asigna bien pero con las palabras pegadas. **Se alinean ambos flujos** y se arbitra con el OCR; si no alcanza, con el nombre del Único. 30 títulos recompuestos |
| **Oftalmología: catálogo corrido un código** (`020108` era «vitrectomía» según OCR y Único, pero figuraba en `020107`) | Detectado por la misma alineación. Las abreviaturas siguieron a su título correcto |
| **Equivalencias a códigos inexistentes** (`300113` remitía a `300153`, que no está en la base) | Si el destino no existe se re-resuelve por código idéntico y, si no, por proximidad de nombre en el capítulo |
| **Lateralidad ignorada** (el Nacional anota BILATERAL / UNILATERAL) | Se extrae del OCR (busca sobre el flujo de letras, porque vienen pegadas), se propaga al Único y **la Mesa de trabajo rechaza un bilateral con cantidad > 1** |
| Títulos PMO garbled (`342014` con 360+ caracteres) | Parseo columna a columna separando título/cobertura |
| Cobertura PMO absorbía otras prestaciones | Detectar códigos pegados al título + filtrar artefactos de página |
| Títulos SURGE faltantes en el índice | Detectar títulos partidos en dos líneas |
| SURGE vinculado en un nomenclador y no en otro | Grafo de equivalencias + propagación transitiva |
| Siglas duplicadas (`ABDI`) | Dedup por sigla+significado normalizado |
| Scroll horizontal en móvil | Grilla en el selector + `minmax(0,1fr)` + `min-width:0` en `<main>` |
| CIE-10 con capítulos '?' y descripciones fragmentadas | Rangos de capítulo extendidos + guard `is_frag` + normalización final |
| Playwright: clics interceptados | Cerrar `#onboard` y el `#scrim` antes de interactuar |
