# Manual Inteligente Unificado de Códigos Médicos

Herramienta para consultar, interpretar y **facturar correctamente** los códigos de los
nomencladores médicos argentinos, con relaciones entre códigos y reglas de auditoría por práctica.

Estado actual: cargados **cuatro nomencladores relacionados** en una sola base (**6.334 códigos**):

- **NBU — Nomenclador Bioquímico Único** (Versión 2012 · Actualización 2016, CUBRA) — 1.815 códigos, con el
  **Anexo Enero 2024** y la **U.B. vigente** (planilla oficial actualizada al día) aplicados como overlay.
- **Catálogo de Prestaciones del PMO** (Resolución 201/2002, S.S. Salud) — 1.219 prestaciones médicas y
  quirúrgicas por especialidad.
- **Nomenclador Nacional — Odontología** (Anexo II, Res. 201/02) — 79 prácticas dentales valorizadas.
- **Nomenclador ÚNICO (VISITAR SRL)** — **3.221 prestaciones** del nomenclador único que la empresa está
  construyendo, en dos partes con equivalencias:
  - **Médicas** (1.502): equivalencias a Prestaciones Médicas (1.425 mapeadas y **77 sin equivalencia**).
  - **Laboratorio** (1.719): el código único = **2 dígitos de prefijo + el código NBU**; cada práctica trae su
    **U.B.** y su **equivalencia con el NBU** (1.678 con ficha NBU; 41 con código NBU no cargado como ficha).

Ambos se cruzan: **315 códigos de laboratorio (66xxxx)** aparecen en los dos nomencladores y quedan
enlazados (en la ficha del NBU se marca "También en Catálogo PMO").

## Qué incluye

### NBU (bioquímica) — 1.377 prácticas
- Clasificación oficial:
  - **PMO** (Programa Médico Obligatorio) — 370
  - **Prácticas Especiales (P.E.)** — 1.005
  - **Gestión Administrativa** — 2
- Por cada código:
  - **Nombre**, **U.B.** (Unidad Bioquímica) y fórmula de arancel.
  - **Sinónimos** (149) y **abreviaturas** (399 códigos) para búsqueda.
  - **Flags**: urgencia (`U`), requiere norma (`N`), en desuso (`#`), metodología PCR.
  - **Norma e interpretación** oficial (texto), para 140 códigos.
  - **Relaciones entre códigos** (197 códigos): *incluye* / *no incluye* / *incluido en*.
  - **Normas de auditoría / facturación** generadas por código (qué no facturar por separado, cuándo adicionar 661200, etc.).
  - **U.B. actualizada 2024** donde el anexo la revaloriza (50 códigos).
  - **U.B. vigente** (actualización al día, planilla oficial XLS): valor de U.B. revalorizado por práctica que
    se toma como **valor efectivo** para el arancel en el listado, la ficha, el árbol y el validador. Se aplicó a
    1.687 códigos (la planilla trae la *terminación* del código y su U.B. vigente; se mapea a los 66xxxx del NBU).
    La ficha conserva el histórico (base v2016 · Anexo 2024 · vigente) sin pisarlo.
- **Glosario** de referencias y flags + **marco normativo** (**22 normas vigentes**; 13 con ficha ampliada —
  resumen, qué cubre, artículos clave y **prácticas del NBU relacionadas** clickeables): discapacidad (24.901, con
  **tabla de valores** de las prestaciones básicas actualizada), celiaquía (26.588), fertilización asistida (26.862),
  leche medicamentosa (27.305), violencia de género/PMO (27.696), **Res. 310/2004** (PMOE) y **Anexo II · HPGD**
  (normas de facturación de Hospitales Públicos de Gestión Descentralizada).
- Clasificación **orientativa** por grupo/especialidad para facilitar la navegación
  (el NBU es alfabético; la clasificación oficial es la sección PMO/PE/Gestión).

### Catálogo PMO (prestaciones médicas) — 1.234 códigos
- Prestaciones médicas y quirúrgicas por **capítulo/especialidad** (código de 6 dígitos):
  cirugía (sistema nervioso, cardiovascular, digestivo, traumatología, etc.), diagnóstico por imágenes,
  cardiología, neurología, hemoterapia, medicina nuclear, radioterapia, laboratorio, y más (~36 capítulos).
- Son prestaciones de **cobertura obligatoria** del PMO; el arancel surge del nomenclador/convenio aplicable
  (el catálogo lista qué se cubre, no valores monetarios).
- **Valores del Nomenclador Nacional** (Anexo II, Res. 201/02) para **674 códigos quirúrgicos**, extraídos por
  **OCR** de los PDF escaneados y **validados por checksum** (los 4 valores en $ suman el Total; 95% de las
  filas con precio pasan la validación). Cada código trae, en **galenos** y en **$ de referencia 2002**:
  honorarios de **especialista**, **ayudantes** (con Nº que admite), **anestesista**, **gasto** y **total**.
- Cada ficha médica incluye **"Asociación de códigos · qué cargar"**: para los códigos con valores, las
  asociaciones son **específicas** (cuántos ayudantes admite, si lleva anestesia y sus galenos, gasto);
  para el resto, **normas generales por capítulo** (cirujano + ayudantes + gastos + anestesia cap. 16 +
  anatomía patológica cap. 15). Marcadas como **orientativas** (verificar contra la norma aplicable).
- El pipeline OCR (`scripts/ocr_nn.py` + `scripts/parse_nn.py`) es reutilizable para la 3ª parte del
  Nomenclador (prácticas y consultas), pendiente de carga.

### Odontología (Nomenclador Nacional dental) — 79 códigos
- Prácticas odontológicas (Anexo II, Res. 201/02) por capítulo: consultas, operatoria dental, endodoncia,
  prótesis, periodoncia, ortodoncia, cirugía bucal, etc.
- Valorización por **OCR validada por checksum** (Honorarios$ + Gasto$ = Valor Práctica; 86% de las filas
  con precio validan): honorarios y gasto en **galenos odontológicos** + **$ ref. 1991** + **coseguro máximo %**.
- Los **nombres de las prácticas dentales fueron pulidos** (se corrigieron los artefactos de OCR del escaneo):
  cada código muestra su denominación limpia (p. ej. *Obturación de amalgama. Cavidad simple*, *Perno muñón simple*,
  *Germectomía*). Código, valores y coseguro se mantienen.

### Nomenclador ÚNICO (VISITAR SRL) — 3.221 prestaciones
- Nomenclador **propio de la empresa, en elaboración**, en dos partes:
  - **Prestaciones médicas** (1.502): cargado desde la planilla de equivalencias (Prestaciones Médicas ↔ Único)
    con puntaje de similitud. Sin valorización todavía.
  - **Laboratorio** (1.719): el código único se forma con **2 dígitos de prefijo + el código real del NBU**;
    trae la **U.B.** (arancel calculable con el valor de U.B.) y su equivalente NBU es exacto.
- Cada código del Único muestra su **equivalencia** (a **Prestaciones Médicas** o a **Laboratorio (NBU)** según
  corresponda): código + descripción + % de similitud, **clickeable** para abrir la ficha del otro nomenclador.
  Recíprocamente, cada prestación médica **o práctica NBU** con equivalencia muestra **"También en Nomenclador
  Único"** — la referencia de que el código está en **ambos**.
- Los **77 códigos médicos sin equivalencia** quedan **separados y agrupados** (filtro **"Sin equivalencia"** y
  etiqueta en el listado) para revisarlos y mapearlos manualmente.
- **Generalidades heredadas** (como en el NBU): la parte de **laboratorio** del Único trae, tomadas de su código
  NBU equivalente, las **relaciones/parentesco entre códigos** (incluye / no incluye / incluido en), las **normas
  de auditoría**, la **norma e interpretación** y las reglas de **seriado**; además tiene su propio **árbol de
  módulos** (pestaña disponible en la sección Único). En la parte **médica**, cada código hereda de su prestación
  médica equivalente las **asociaciones "qué cargar"** y —cuando corresponde— los **valores del Nomenclador
  Nacional** (galenos).

### Consulta rápida — Diagnósticos (CIE-10) y Abreviaturas médicas
Apartado de consulta para el personal administrativo (no es un nomenclador): dos buscadores para **interpretar la
orden médica** antes de cargar las prácticas.

**Diagnóstico (CIE-10):**
- **11.581 diagnósticos: 2.024 categorías (3 caracteres) + ~9.500 subcategorías** detalladas (4+ caracteres,
  p. ej. `E11.9`, `K95.89`) tomadas del manual **CIE-10-ES**, organizados por los **21 capítulos** y buscables por
  código o texto. Cada subcategoría enlaza a su **categoría padre** y hereda de ella las prácticas relacionadas.
- Cada diagnóstico muestra las **prácticas relacionadas**: un **seed curado** (45 diagnósticos frecuentes de
  laboratorio: diabetes, tiroides, dislipidemia, anemias, hepatitis, HIV, celiaquía, infertilidad, IRC, etc.) más
  **sugerencias automáticas por coincidencia de texto**. Los estudios son **clickeables** y saltan a la ficha del
  nomenclador correspondiente. Marcado como **orientativo** (verificar según el caso clínico y la cobertura).

**Abreviaturas médicas:**
- **1.413 siglas** (1.780 significados, deduplicados — misma sigla y significado se unifican, p. ej. `ABDI`) de los
  diccionarios del **Hospital Italiano de Bs. As.** + **INSN**, buscables por sigla o por significado, para
  **descifrar lo que el médico pide en la orden** (p. ej. `RMN` → Resonancia Magnética). Las siglas con varios
  significados se muestran en una sola fila y el detalle lista todas sus acepciones.
- Cuando la sigla coincide con una práctica del nomenclador nacional/único, la ficha de la abreviatura enlaza a las
  **prácticas que pueden pedirse con esa sigla** (clickeables). A la inversa, **1.025 prácticas** llevan en su ficha
  el apartado **«Puede abreviarse en la orden»** con las siglas con que suelen aparecer escritas.

**SURGE — Sistema Único de Reintegro por Gestión de Enfermedades (Res. 731/2023, Anexo II):**
- Apartado propio (en «Consulta rápida») con las **54 patologías** del SURGE agrupadas por **especialidad**
  (Oncología, Reumatología, Enfermedades lisosomales, Trasplantes, etc.), buscables por patología, **medicación
  (droga)**, especialidad o código.
- Cada patología muestra: la **medicación SURGE** que le corresponde, el **requerimiento para autorización que
  VISITAR solicita al afiliado** (RHC, laboratorios, estudios, dictámenes, etc.), los **códigos del nomenclador
  relacionados** y los **diagnósticos CIE-10** asociados.
- Los **38 códigos** del nomenclador marcados **(SUR)/(SURGE)** (trasplantes, neuroestimuladores, TAVI, ECMO,
  radioterapia, cargas virales, etc.) quedan **cruzados con su patología**: llevan un distintivo **SURGE** en el
  listado y, en su ficha, la sección **«Sistema Único de Reintegro (SURGE)»** con la patología (clickeable) y el
  requerimiento de autorización. El cruce se **propaga por equivalencia** NBU↔Único.

**Relación bidireccional CIE-10 ↔ prácticas y normativa por código (en todos los nomencladores):** además de la
pantalla de diagnósticos, **cada ficha de código** (NBU, PMO, Odontología o Único) muestra —cuando corresponde—
sus **Diagnósticos CIE-10 relacionados** (clickeables, abren el diagnóstico) y la **Normativa relacionada** (leyes
y normas de cobertura vinculadas, clickeables, abren su detalle). Las relaciones se **propagan por equivalencia**,
así un mismo estudio muestra los mismos diagnósticos y normas se lo mire desde el NBU o desde el Único.

La interfaz separa **cuatro nomencladores** en el selector principal — **Laboratorio (NBU)**, **Prestaciones
médicas (PMO)**, **Odontología** y **Único (VISITAR)** — más un apartado de **Consulta rápida** (Diagnósticos
CIE-10 y Abreviaturas médicas). En cada nomenclador solo se ven sus códigos y agrupaciones (no se mezclan).

**Buscar en todo (búsqueda global):** una opción "Buscar en todo" cruza en una sola búsqueda **todos los
nomencladores (NBU, PMO, Odontología, Único) + CIE-10 + abreviaturas** a la vez, sin tener que elegir primero a
qué nomenclador pertenece lo que se busca. Los resultados se muestran **agrupados por origen** (con su cantidad) y
cada uno abre su ficha correspondiente al hacer clic.

## Uso

Abrí **`web/index.html`** en cualquier navegador (no requiere servidor ni conexión — la base va embebida
**comprimida en gzip+base64** y se descomprime en el navegador al abrir; el archivo pesa ~0,8 MB en vez de ~9 MB
y arranca en menos de medio segundo). Requiere un navegador moderno (Chrome/Edge/Firefox/Safari recientes, que
soportan `DecompressionStream`).

Tres vistas (pestañas):
- **Listado** — buscá por código, práctica, sinónimo o abreviatura; filtrá por sección, grupo o reglas/estados. Detalle con **códigos relacionados clickeables** que navegan entre sí. Enlace directo por hash: `index.html#660475`.
- **Árbol de módulos** — jerarquía expandible de los módulos de facturación (qué incluye cada código y no debe facturarse por separado).
- **Validador de facturación** — pegás una lista de códigos (con cantidades `×N`) y detecta doble facturación por inclusión, urgencias sin 661200, Acto Bioquímico faltante, seriados excedidos, desuso e inexistentes; calcula U.B. netas y arancel.

Productividad y atajos:
- **Atajos de teclado**: `/` enfoca la búsqueda; `↑`/`↓` recorren los resultados y `Enter` abre el resaltado.
- **Resaltado** del término buscado en código y nombre.
- **➕ Al validador** y **⧉ Copiar código** desde cada ficha (para armar la validación sin tipear).
- **Nota personal por código** (privada de tu perfil) y filtros **“Vistos recientemente”** y **“Con nota personal”**.

Seguridad y auditoría (admin):
- **Cifrado de la sincronización** (opcional, AES-256): con una *clave de cifrado* de empresa, los datos se cifran
  antes de subir a Supabase — ni con la clave pública se pueden leer sin esa frase.
- **Registro de cambios**: quién editó qué ficha/texto y cuándo (*Administración → Registro*), compartido y respaldado.

Funciones operativas:
- **Valor de la U.B.** (arriba): al cargarlo, se muestra el **arancel** ($) en el listado, la ficha y el validador. Se guarda en el navegador.
- **Favoritos** (★): marcá códigos frecuentes; se guardan y se filtran con “★ Favoritos”.
- **Exportar**: descargá a **CSV** (listado y validación) o **Imprimí/PDF** desde el navegador.
- **Frecuencia/seriado**: los códigos con reglas de seriado (p. ej. `660102`, `660468`) las muestran en la ficha y el validador las controla.

## Acceso, perfiles y administración

La app tiene un **control de acceso en dos niveles**, pensado para que todo el personal comparta un
mismo equipo/instalación pero cada persona conserve **sus propios favoritos**:

1. **Acceso de la empresa** (usuario compartido): una sola credencial que usa todo el equipo para entrar.
2. **Perfiles individuales**: dentro del acceso de empresa, cada administrativo crea su **perfil con nombre
   y contraseña propios**. Al iniciar sesión con su perfil se cargan **sus favoritos** y su **valor de U.B.**.

Los **perfiles administrador no se listan** en el selector “¿Quién sos?” que ven los administrativos: el admin
entra por un acceso aparte (**“Acceso administrador”** → nombre + contraseña), de modo que el personal no ve ni
puede elegir el perfil de administración.

**Primer uso:** un **onboarding** guiado (tutorial de bienvenida) explica las secciones, la búsqueda, favoritos,
arancel y el validador; se puede reabrir desde *Glosario → Ver tutorial de uso*.

**Seguridad:** contraseñas con **PBKDF2/SHA-256 (310.000 iteraciones)** y salt por registro; **bloqueo temporal
tras 5 intentos fallidos** y **cierre de sesión automático por inactividad** (25 min, vuelve a pedir la contraseña
del perfil).

### Perfil administrador
Los perfiles marcados como **administrador** pueden:
- **Gestionar perfiles**: crear, eliminar, restablecer contraseñas y promover/quitar admin (siempre queda al menos un admin).
- **Editar el contenido de la página**:
  - **Textos generales** (título y subtítulo) y el **logo de la empresa** (subir imagen PNG/JPG/SVG que reemplaza
    la marca en la barra superior y las pantallas de acceso) desde *Administración → Textos*.
  - **Contenido por código** (nombre, norma de trabajo/interpretación, normas de auditoría y una nota de
    asociación interna): con el **modo edición** activado (botón ✎ en la barra), cada ficha muestra
    **“✎ Editar ficha”**. El original queda respaldado y se puede **restaurar**. Los códigos con contenido
    modificado muestran una etiqueta **“editado”**.
- **Cambiar el acceso de la empresa** y **respaldar/restaurar** todo (perfiles + ediciones) a un archivo `.json`.

### Sincronización entre computadoras (Supabase)
Al ser un archivo sin servidor, los datos viven en el navegador de cada equipo. Para **compartirlos en tiempo
real** entre máquinas se puede conectar un proyecto **Supabase** (gratis) desde *Administración → Nube*:
- El admin pega **URL del proyecto** + **clave pública (anon key)**; la app sincroniza perfiles, favoritos y
  ediciones por *polling* (últ. escritura gana, con merge de perfiles por id).
- El panel incluye el **SQL** para crear la tabla y el **paso a paso**. En otros equipos, en la pantalla de
  acceso se elige **“conectar a la nube”** y se pegan los mismos datos.
- La sincronización **no opera dentro del Artefacto de Claude** (bloquea conexiones externas por seguridad);
  funciona con el archivo `web/index.html` abierto directamente o alojado en la web. La clave pública queda
  visible en el archivo: es un espacio **interno**, no cargar datos sensibles de pacientes.

> Nota: el login es una **barrera organizativa** (separa perfiles y favoritos), no una seguridad criptográfica
> de servidor. Las contraseñas se guardan **hasheadas** (PBKDF2/SHA-256), nunca en texto plano.

## Estructura del repositorio

```
data/
  nbu_db.json           # Base de datos unificada (fuente de verdad) — 1.377 códigos
  nbu_catalog_raw.json  # Catálogo crudo parseado (intermedio)
  nbu_intel_raw.json    # Sinonimias / abreviaturas / normas crudas (intermedio)
scripts/
  parse_catalog.py      # Parser del catálogo NBU (coordenadas) -> catalog.json
  parse_intel.py        # Parser de sinonimias, abreviaturas y normas NBU (tablas) -> intel.json
  parse_pmo.py          # Parser del Catálogo PMO (2 columnas) -> pmo_catalog.json
  assemble.py           # Une NBU + PMO, clasifica, cruza 66xxxx, genera reglas -> nbu_db.json
web/
  index.html            # Aplicación web autocontenida (base embebida)
```

## Modelo de datos (`nbu_db.json`)

```jsonc
{
  "meta":     { "total_codigos": 1377, "secciones": {...}, "grupos": {...} },
  "glosario": { "U": "...", "N": "...", "(#)": "...", "661200": "..." },
  "leyes":    [ { "ley": "27232", "titulo": "Ley NBU", "sancion": "26/11/2015" } ],
  "codigos": {
    "660475": {
      "code": "660475", "nomenclador": "NBU", "seccion": "PMO",
      "grupo": "Hematología y hemostasia", "nombre": "HEMOGRAMA.",
      "sinonimos": [...], "abreviaturas": [...],
      "valor":  { "ub": 3.0, "unidad": "U.B. (Unidad Bioquímica)", "arancel": "...", "ub_actualizado_2024": null },
      "flags":  { "urgencia": true, "requiere_norma": true, "desuso": false, "pcr": false },
      "referencias": [ { "code": "8332", "target": "668332", "texto": "..." } ],
      "norma":  { "trabajo": "...", "interpretacion": "..." },
      "relaciones": { "incluye": ["660354", ...], "no_incluye": [], "incluido_en": [] },
      "auditoria": [ "Urgencia (U): ...", "INCLUYE (módulo): comprende ..." ]
    }
  }
}
```

### Modelo de versión / vigencia

El valor base (v2016) y el revalorizado (`ub_actualizado_2024`) conviven por código, de modo que el
histórico no se pisa. Al sumar nuevas actualizaciones alcanza con agregar otro campo de valor fechado.

## Regenerar la base

Los parsers trabajan sobre el PDF oficial del NBU (fuente externa, no versionada en el repo):

```bash
python3 scripts/parse_catalog.py   # -> catalog.json
python3 scripts/parse_intel.py     # -> intel.json
python3 scripts/assemble.py        # -> nbu_db.json   (usa nbu_reval.txt para el overlay 2024, opcional)
```

Luego se embebe la base **comprimida** dentro de `web/index.html`:

```bash
python3 scripts/inject_db.py   # gzip + base64 de data/nbu_db.json -> bloque <script id="nbu-db-gz">
```

El navegador la descomprime al abrir (`DecompressionStream`), manteniendo el archivo único y offline pero
~11× más liviano.

## Notas y alcance

- La clasificación por **grupo/especialidad** es orientativa (heurística por palabras clave); la
  clasificación **oficial** es la sección (PMO/PE/Gestión). ~20% de los códigos quedan en “Otros / general”.
- Las **relaciones y reglas de auditoría** se extraen del Anexo de Normas e Interpretaciones oficial.
- Fuente: **CUBRA — Confederación Unificada Bioquímica de la República Argentina**, NBU v2012 act. 2016 + Anexo Enero 2024.
