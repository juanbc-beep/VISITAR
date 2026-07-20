# Manual Inteligente Unificado de Códigos Médicos

Herramienta para consultar, interpretar y **facturar correctamente** los códigos de los
nomencladores médicos argentinos, con relaciones entre códigos y reglas de auditoría por práctica.

Estado actual: cargados **tres nomencladores relacionados** en una sola base (**3.113 códigos**):

- **NBU — Nomenclador Bioquímico Único** (Versión 2012 · Actualización 2016, CUBRA) — 1.815 códigos, con el
  **Anexo Enero 2024** y la **U.B. vigente** (planilla oficial actualizada al día) aplicados como overlay.
- **Catálogo de Prestaciones del PMO** (Resolución 201/2002, S.S. Salud) — 1.219 prestaciones médicas y
  quirúrgicas por especialidad.
- **Nomenclador Nacional — Odontología** (Anexo II, Res. 201/02) — 79 prácticas dentales valorizadas.

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
- **Glosario** de referencias y flags + **marco normativo** (12 leyes vigentes).
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

La interfaz separa **tres secciones** con un selector principal: **Laboratorio (NBU)**, **Prestaciones
médicas (PMO)** y **Odontología** — en cada una solo se ven sus códigos, grupos y determinaciones (no se mezclan).

## Uso

Abrí **`web/index.html`** en cualquier navegador (no requiere servidor ni conexión — la base va embebida).

Tres vistas (pestañas):
- **Listado** — buscá por código, práctica, sinónimo o abreviatura; filtrá por sección, grupo o reglas/estados. Detalle con **códigos relacionados clickeables** que navegan entre sí. Enlace directo por hash: `index.html#660475`.
- **Árbol de módulos** — jerarquía expandible de los módulos de facturación (qué incluye cada código y no debe facturarse por separado).
- **Validador de facturación** — pegás una lista de códigos (con cantidades `×N`) y detecta doble facturación por inclusión, urgencias sin 661200, Acto Bioquímico faltante, seriados excedidos, desuso e inexistentes; calcula U.B. netas y arancel.

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

### Perfil administrador
Los perfiles marcados como **administrador** pueden:
- **Gestionar perfiles**: crear, eliminar, restablecer contraseñas y promover/quitar admin (siempre queda al menos un admin).
- **Editar el contenido de la página**:
  - **Textos generales** (título y subtítulo) desde *Administración → Textos*.
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

Luego se embebe `nbu_db.json` dentro de `web/index.html` (bloque `<script id="nbu-db">`).

## Notas y alcance

- La clasificación por **grupo/especialidad** es orientativa (heurística por palabras clave); la
  clasificación **oficial** es la sección (PMO/PE/Gestión). ~20% de los códigos quedan en “Otros / general”.
- Las **relaciones y reglas de auditoría** se extraen del Anexo de Normas e Interpretaciones oficial.
- Fuente: **CUBRA — Confederación Unificada Bioquímica de la República Argentina**, NBU v2012 act. 2016 + Anexo Enero 2024.
