# TRASPASO DE SESIÓN — Manual Inteligente Unificado (VISITAR SRL)

> Documento para retomar el trabajo en una sesión nueva sobre **la misma app**.
> Última actualización: 2026-08-18, rama `claude/unified-medical-codes-manual-o9nw1w`,
> tras fusionar dos ramas de sesiones en paralelo (`nomenclador-chapters-30-29-21-0c4v9o`,
> que ya traía consigo `nomenclador-chapters-20-24-17-eoittj`, y
> `nomenclador-nacional-barrido-gjii29`). El clon es superficial y el total de commits no se
> puede contar, así que se identifica por rama.
>
> **✅ El barrido del Nomenclador Nacional (3.8) terminó, capítulo por capítulo y de punta a
> punta** —transcribir a ojo el recuadro «Texto retirado por el PMO» que el catálogo del PMO
> no reproduce. Los 32 capítulos del PMO están hechos (844 de 1.353 fichas, 62%) y el
> **capítulo 66** (análisis clínicos, 36 páginas) también se completó el 19/8/2026: 134
> códigos con texto sumado a fichas del **NBU** existentes (no al PMO — ver 3.8, «Capítulo
> 66»). Quedan casos «dudoso» documentados página por página en `data/alcance_nn_pmo.json`
> (nombre o método parecido pero no idéntico) para revisión manual; no son urgentes. La
> agenda de 7 bis A ya no tiene barrido pendiente — ver el punto 7 bis para lo que sigue.
>
> **Lo más importante que cambió respecto del traspaso anterior:** la app dejó de ser un
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
| **Códigos totales** | **6.478** |
| — NBU (laboratorio/bioquímica) | 1.815 |
| — PMO / Prestaciones médicas | 1.353 (26 altas del capítulo 34 —ver 3.4—, los capítulos que faltaban enteros —3.6—, el 23.02.34 y el 21.02.08 —3.8—) |
| — Nomenclador Único (VISITAR) | 3.231 |
| — Odontología | 79 (**oculto en la app**, ver 6.12) |
| **CIE-10** (diagnósticos) | **11.581** en 21 capítulos |
| **Abreviaturas médicas** | **1.780** significados / 1.413 siglas únicas |
| **SURGE** (Res. 731/23) | **58** patologías del Anexo II · 38 códigos mapeados |
| **Leyes / normas** | 22 · Glosario 12 |

⚠️ Esos 6.478 son la **base publicada**. `assemble.py` arma **6.372**: los importadores de
capítulo (3.6 y 3.8) corren **después**, sobre `data/nbu_db.json`, y suman los capítulos que
faltaban enteros más el `23.02.34`. Si un conteo no da, mirar cuál de los dos números es —el
resto del documento, escrito antes, dice «sobre 6.372» en varios lados.

### Cruces / inteligencia construida

| Relación | Cobertura |
|---|---|
| Códigos con **abreviaturas posibles** | 1.044 |
| Códigos con **tipo de muestra** (sangre/orina) | 821 (705 por texto + 73 por sufijo + 43 heredados del gemelo del NBU) |
| Códigos con **diagnósticos CIE-10** relacionados | 242 |
| Códigos con **cobertura** | 116 → 107 *obligación* + 9 *observación* |
| Códigos con **lateralidad** | 130 (109 del OCR + 21 curados por auditoría) |
| Códigos con **normativa** relacionada | 61 |
| Códigos con **vínculo SURGE** | 60 |
| Códigos con **tope PMO** | 38 |
| Pares **-emia / -uria** vinculados | 26 |
| Único **sin equivalencia** (agrupados aparte) | 79 |
| Marcador del Único separado del título | 1.724 |
| Laboratorio del Único **emparejado con el NBU** (uno a uno) | 1.694 |
| **Marcas de calidad** | 99 `titulo_revisar` · 139 `texto_truncado` · 1 `sin_denominacion` |
| Capítulo 34 con **alcance del Nacional** (qué abarca el código) | 96 |
| Pares **práctica / exposición subsiguiente** | 10 |

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
│   ├── workflows/rls.yml           # CI: reglas de acceso contra PostgreSQL real
│   ├── workflows/e2e.yml           # CI: interfaz contra el simulador de Supabase
│   └── dependabot.yml              # avisa cuando una acción tiene versión nueva
├── tests/
│   ├── rls/                        # reglas de acceso (RLS) — ver tests/rls/LEEME.md
│   └── e2e/                        # interfaz (Playwright) — ver tests/e2e/LEEME.md
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
2. **`scripts/assemble.py`** → une todo en `nbu_db.json` (6.372 códigos + datasets).
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

### 3.4 ⚠️ Capítulo 34 del PMO (radiología): tres defectos y su arreglo

Los reportó el usuario uno atrás del otro y cada uno tenía una causa distinta.
Documentado con detalle porque el mismo patrón puede estar en otros capítulos.

**a) Nombres empezados por la mitad.** `clean_pmo_name()` le saca al nombre la
palabra inicial cuando coincide con un título de sección del catálogo, porque el
parser viejo los absorbía. Arregla «Radiología radioscopía simple» y **rompe**
«radiología del cráneo, cara, senos paranasales o cavum», donde esa palabra es la
práctica. No hay regla que distinga los dos casos: hay que mirar la fuente.
`scripts/parse_pmo_titulos.py` la relee —palabras a la derecha del código, en su
renglón y en los de continuación, cortando cuando el salto entre renglones supera
el alto normal, si no se lleva puesto el anexo de cobertura— y las 21
denominaciones corregidas quedan en `data/pmo_titulos_curados.json`.

**b) Prestaciones que faltaban enteras.** El catálogo del PMO no imprime todas
las del capítulo: 26, entre ellas **todas las exposiciones subsiguientes**,
figuran sólo en el Nomenclador Nacional, con la leyenda «Texto retirado por el
PMO». Se dan de alta desde `data/pmo_cap34_faltantes.json` con
`scripts/altas_pmo_cap34.py`, y **cada ficha dice en la primera línea de auditoría
que el PMO no la incluye**: esconderlas es peor (el agente concluye que el código
no existe) y mostrarlas sin la aclaración también (las carga creyendo que tienen
cobertura obligatoria). El alta resolvió además 8 equivalencias del Único que
apuntaban a un código inexistente.

**c) El alcance del código, que no llegaba nunca.** El Nacional imprime al lado
de cada práctica qué abarca —«primera exposición», «tres posiciones,
comparativas», «mínimo 3 placas por estudio»— en el mismo renglón que el PMO
retiró. `scripts/alcance_cap34.py` lo rescata para 96 códigos y lo muestra en una
sección propia. **El OCR de esas páginas está dañado**: el texto se limpia de los
errores que se repiten y se muestra siempre marcado como transcripción a
confirmar, con el original guardado al lado.

⚠️ **La regla del nomenclador, relevada por el usuario** (vale para todo el
capítulo, no sólo para lo que ya está cargado):

> Si la exposición tiene **código propio**, ese código se carga **aparte**. Si las
> posiciones **no** tienen código propio, son el **alcance** del código puntual.

Una «Rx de tórax frente y perfil» se carga con `340301` **más** `340302`. En
cambio `340204` no tiene código de exposición siguiente: su propio texto dice que
abarca «tres posiciones, comparativas». Los 10 pares llevan el aviso como **paso
de la carga**, no escondido entre las normas. Estuvo mal una versión: se cargó
`340302` como «incluido en» `340301`, que dice lo contrario —si estuviera
incluido no habría que cargarlo— y lleva a facturar de menos.

⚠️ **Los nombres no se componen.** Se probó llamar al `340210` «radiología de
raquis (columna) — por exposición subsiguiente» para distinguirlos en un listado y
el usuario lo rechazó con razón: el `340210` **no es** la radiografía de raquis,
es un código propio. Cada código se llama como lo llama la fuente; de qué práctica
es la exposición va en el paso de la carga y en la auditoría.

### 3.5 Lo que este cotejo dejó ver y NO se tocó

`data/pmo_titulos_a_revisar.json` — **159 denominaciones** del PMO donde la base y
el renglón impreso no coinciden, con las dos versiones al lado. Se van revisando
por capítulo y las corregidas quedan en `data/pmo_titulos_curados.json` (62 hasta
ahora: capítulos 34, 12, 03 y la pasada mecánica).

⚠️ **No son 159 defectos, y el renglón impreso solo no alcanza para decidir.** Dos
correcciones al criterio con el que se armó esta lista:

- En buena parte de los casos **la base es MÁS completa** que el renglón: el
  nombre sigue en otra columna y el lector lo corta. En el capítulo 03, de 17
  casos sólo 6 eran defectos.
- **El método bueno es cruzar tres fuentes**: la base, la planilla del
  Nomenclador Único y el OCR del Nacional (`data/nn_values.json`). Con eso se
  resolvió el capítulo 11, donde el PDF parecía mostrar un corrimiento de once
  códigos y **no lo había**: el nombre de `110211` se derrama sobre el renglón del
  `110212` y el lector asigna todo al código anterior. El Único y el Nacional
  coinciden con la base.

⚠️ **Corrección de un dato que estuvo escrito acá:** se afirmó que `020106` tenía
el nombre de `020105` y que el corrimiento seguía en `020107` y `020108`. Con las
tres fuentes: **sólo `020106` estaba mal** —arrancaba con un pedazo del nombre
anterior pegado— y `020107` y `020108` siempre estuvieron bien. No era un
corrimiento, era un fragmento pegado adelante. Ya está corregido.

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
`cie10_relaciones.py`, `parse_abreviaturas.py`, `parse_surge.py`, `parse_nbu_normas.py`,
`parse_pmo_titulos.py` (punto 3.4).
Y los que no son parsers: `propagar_al_unico.py` (3.0), `altas_pmo_cap34.py` y
`alcance_cap34.py` (3.4), `inject_db.py` (3.0 bis) y `sellar_csp.py`.

### Testing

⚠️ **Ya no se arma a mano en el scratchpad de cada sesión — desde el 24/8/2026 vive
versionado en `tests/`, con dos suites separadas y las dos con CI propio (corren solas en
cada PR que toque lo que prueban).**

**`tests/rls/`** — las reglas de acceso (RLS), contra un **PostgreSQL 16 real** con una
maqueta del esquema `auth` de Supabase (**tiene que incluir el rol `supabase_auth_admin`
como dueño de `auth.users`**: sin eso no aparece la clase de fallo que rompió el alta de
cuentas, ver 9). `ataques.sql` reproduce seis ataques que funcionaban de verdad antes de
la corrección de agosto de 2026; `regresion.sql` es el contrapeso (lo que sí tiene que
seguir andando). Ver `tests/rls/LEEME.md`. CI: `.github/workflows/rls.yml`.

**`tests/e2e/`** — la interfaz, con **Playwright** + un simulador de Supabase propio
(`tests/e2e/simulador.mjs`, intercepta `ctx.route(HOST+'/**', …)` y contesta en memoria:
`/auth/v1/token`, `/rest/v1/perfiles`, `/rest/v1/rpc/*`,
`/rest/v1/{correcciones,verificaciones,propuestas,ajustes,observaciones}`). Deliberadamente
**no** reproduce RLS — para eso está `tests/rls/`, esto asume que el servidor ya cumple sus
reglas y prueba que la app hace lo correcto. Casos persistidos hoy: `login` (ingreso +
violaciones CSP), `nubelocal` (modo local sin nube configurada), `favs` (favoritos del
equipo). Quedan sin persistir, mismo patrón, agregar cuando haga falta: `simul` (dos
personas a la vez), `flujo3` (propuesta → aprobación por el panel real), `fidelidad`
(corrección que borra la norma a propósito), `nube` (pestaña de estado), `recup`/`recup2`
(restablecer contraseña). Ver `tests/e2e/LEEME.md`. CI: `.github/workflows/e2e.yml`.

Trampas del simulador de interfaz, aprendidas a los golpes (documentadas en el LEEME para
no volver a pisarlas):
- **La identidad es de cada sesión, la base es compartida.** Se resuelve por el token
  `Bearer` de cada pedido, nunca por un valor fijado al instalar el simulador: con un valor
  fijo, dos sesiones de la misma corrida (para simular dos personas a la vez) terminan
  viendo la misma identidad y la prueba miente sin fallar.
- Servir la app por **http://** (no `file://`), porque el service worker no corre en
  `file://`. `tests/e2e/arranque.mjs` levanta un servidor Node mínimo para esto.
- **El registro del service worker puede persistir entre contextos «nuevos» de Playwright
  en este entorno de pruebas** (no debería, pero pasa) y su evento `controllerchange`
  recarga la página sola a los 600 ms (ver `sw.js`, función `recargar()`) — a mitad de
  cualquier test que no lo espere. Se resuelve creando el contexto con
  `browser.newContext({serviceWorkers:'block'})` (`nuevoContexto()` en `arranque.mjs`), no
  bloqueando la request a `sw.js`: eso no alcanza porque el navegador puede ya tener un
  worker activo sin volver a pedirlo.
- **Un puerto por caso**, por la razón de arriba y porque el service worker cachea por
  origen: si dos variantes comparten puerto, una puede terminar sirviéndole a la otra.
- Saltar el recorrido guiado con
  `page.addInitScript(()=>localStorage.setItem('nbu-onboarded','1'))`; si no, `#tour`
  intercepta todos los clics.
- Varias funciones internas (`BYCODE`, `toggleFav`, `CONTENT`) **no son alcanzables** desde
  `page.evaluate`: interactuar por la interfaz o por `window.NBUProfile`.
- La tira de accesos rápidos se redibuja con `render()`; tocar una estrella no la
  refresca. Forzarlo escribiendo y borrando en `#q`.

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

⚠️ Al aplicarse, `actualizando()` muestra un cartel a pantalla completa —«Actualizando el
manual… no perdés nada de lo que estabas haciendo»— y **espera 600 ms antes de recargar**
(constante `ESPERA`, función `recargar()` en `web/index.html`). Sin esa pausa la propia
recarga lo pisa y el aviso no cumple ninguna función. Antes de esto la app se reiniciaba
sola y sin decir nada, y el administrativo no sabía por qué.

⚠️ **Detectar la versión nueva es por el commit, no por el largo del HTML** (24/8/2026).
`sw.js` comparaba `viejo.length!==nuevo.length` entre la copia cacheada y la que acaba de
bajar: dos versiones distintas pueden pesar lo mismo por casualidad y ahí el aviso no salía
nunca. Ahora compara el commit sellado en `window.NBU_BUILD` (que `pages.yml` estampa en
cada publicación, ver 1 bis) y sólo cae al largo cuando ese commit no está disponible —en
local, donde queda como `"local"` en las dos copias—. Función `huboCambio()` en `sw.js`.

### 4.5 Recorrido guiado (onboarding) — DOS recorridos

`pasosEsenciales()` — **7 pasos, 174 palabras, 52 s.** Es el que corre la **primera vez**.
`pasosTour()` — **24 pasos** (27 para el administrador). Es el completo, y sólo sale desde
**Glosario y leyes → ▶ Ver tutorial**; el último paso del esencial lo ofrece con un enlace.

Los dos son un **spotlight**: recortan el elemento real con `box-shadow: 0 0 0 9999px` y
ubican el globo al lado. Varios pasos tienen `antes:` que prepara la pantalla.

⚠️ **El tutorial NO es donde se anuncian las funciones nuevas.** Eso fue lo que lo llevó de
15 a 27 pasos, prometiendo dos minutos y tardando cuatro y medio. Una función nueva se
explica con una **pista** (§ 4.5 bis) o por la campanita de novedades.

**El botón del médico es el elemento principal de la ficha.** `revMedHTML()` dibuja el bloque
**aunque no haya nada cargado** cuando entra un médico (`.revmed.vacia`), con el botón
`.rm-mk` —verde, sólido, 14 px— arriba de todo. Antes su única entrada estaba al final de
«cómo se carga», dentro de la caja administrativa: había que bajar la ficha entera para llegar
a lo único que vino a hacer. Y el médico **ya no ve** esa caja (`puedeProponer` excluye a los
médicos): su canal es el médico, tenerlo en los dos lados era pedirle que eligiera entre dos
cajas que decían casi lo mismo.

`.revmed` y `.obsbox` llevan `margin-top:18px` — quedaban tocando la fila de botones de la
ficha.

### 4.5 bis Pistas contextuales

`PISTAS` + `mostrarPista(id, sel)`. Un cartel chico, sin fondo oscuro, anclado al bloque que
explica, **una sola vez**. Hoy son tres: `pedida` (los nombres alternativos y que el buscador
los encuentra), `propuesta` (lo escribió un compañero y **no es norma**) y `novedades` (qué es
la campanita).

Reglas que costaron encontrarlas: aparece **sólo si el bloque está de verdad a la vista**
(`aLaVista()` pide 70 px o el 60 % del alto — con «asoma 4 px» el cartel tapaba media ficha
para señalar algo que todavía no se leía); **una por vez**; **nunca durante el recorrido**;
**«Entendido»** la da por vista y **«Después»** no. La marca va en `localStorage`, por usuario
(`nbu-pista:<id>:<pista>`) y **no** en el perfil de la nube: el usuario pidió expresamente no
tocar el esquema de Supabase por un cartelito.

### 4.5 bis 2 ⚠️ El onboarding es POR PERSONA, no por navegador

`nbu-onboarded` era **una sola marca global** en `localStorage`. Consecuencia: la segunda
cuenta que entraba en la misma computadora no veía el recorrido — justo el caso de un médico
que se suma al equipo y entra donde ya trabajó otro.

Ahora la clave es `nbu-onboarded:<idDeUsuario>` (`claveOnb()` / `yaVioOnboarding()` /
`marcarOnboarding()`), con **migración**: la primera persona que entra después de actualizar
conserva su estado y no se le repite; de ahí en más cada uno tiene la suya.

**Los médicos tienen recorrido propio, los DOS.**
- Esencial (`pasosEsencialesMedico()`): **5 pasos** el médico administrativo, **6** el
  administrador. No es el del administrativo con pasos de menos — entra a otra cosa, así que
  el paso central es el bloque de revisión médica y su botón.
- Completo (`pasosTour()`): **22 / 24 pasos** contra 24 del administrativo. Se arma
  **filtrando y metiendo**, no copiando la lista: los pasos marcados `noMed:true` se caen
  (valor de la U.B., contá cómo se carga, comparar/copiar, Mesa de trabajo, informe) y entran
  tres de revisión médica antes de «cómo se carga», más dos de panel al final para el
  administrador. Si mañana cambia un paso compartido, cambia para los dos.
  ⚠️ El paso del panel va **al final**: su `antes` cierra el cajón, y en el medio dejaba a los
  pasos siguientes hablando de una ficha que ya no estaba en pantalla.

### 4.5 bis 3 Dr. / Dra. — se pregunta, no se adivina

`pedirTrato()`. **No se puede deducir del nombre**, y no es una limitación técnica: adivinar
el género por el nombre es un error que la persona ve escrito todos los días y frente a todo
el equipo. «Alex», «Cruz», «Trinidad», «Guadalupe» no dicen nada, y en los que «parecen»
decirlo la app se equivocaría igual.

Así que se pregunta **una vez, con un toque**, la primera vez que entra con un rol médico —
no en el alta, porque cuando alguien crea la cuenta todavía no sabe que va a ser médico (el
rol se lo da el administrador después). Tres opciones: `Dr.` / `Dra.` / sin tratamiento.

Se guarda en **`perfiles.nombre`**, la columna que ya existe y que se muestra en todos lados:
cero cambios de esquema, y el tratamiento viaja solo a la firma de la revisión, al chip de la
cuenta, al registro de actividad y al panel. `RE_TRATO` / `sinTrato()` / `tieneTrato()` para no
duplicarlo si ya lo tiene. La elección de «sin tratamiento» se recuerda en
`nbu-trato:<id>` para no volver a preguntar.

### 4.5 ter ⚠️ CUATRO TIPOS DE CUENTA (roles médicos)

| | Administrador general | Médico administrador | Médico administrativo | Administrativo |
|---|---|---|---|---|
| valor en `perfiles.rol` | `admin` | `medico_admin` | `medico` | `usuario` |
| cuántos | **uno solo** (trigger) | varios | varios | varios |
| buscar, favoritos, notas | ✔ | ✔ | ✔ | ✔ |
| pedir verificación | ✔ | ✔ | ✔ | ✔ |
| proponer «cómo se carga» | ✔ | — | — | ✔ |
| escribir un aporte médico | ✔ | **✔, publica en el acto** | ✔, queda pendiente | ✗ |
| dar por buena una revisión médica | ✔ | ✔ | ✗ | ✗ |
| aviso por práctica (observaciones) | ✔ | ✔ | ✗ | ✗ |
| validar verificación administrativa | ✔ | ✗ | ✗ | ✗ |
| editar la ficha completa (modo edición) | ✔ | ✗ | ✗ | ✗ |
| editar relaciones entre códigos — árbol de módulos (modo edición) | ✔ | ✔ | ✗ | ✗ |
| cuentas, roles, transferir | ✔ | ✗ | ✗ | ✗ |
| textos, logo, nube, respaldo | ✔ | ✗ | ✗ | ✗ |

Regla que pidió el usuario, textual: **«el médico administrador NO puede tener el mismo poder
que el administrador general, que soy yo»**. Y la simetría: en los dos carriles, *el
administrativo observa y el administrador valida*.

El médico administrador **hace todo lo que hace el médico administrativo y además valida**.
Por eso su aporte **se publica en el acto** en vez de caer en su propia bandeja para que se lo
apruebe a sí mismo: es la misma regla que ya rige la verificación («si la marca un
administrador, él mismo es el validador y queda validada de una»). Los dos caminos —aprobar el
aporte de otro y escribir el propio— pasan por `publicarRevision()`, para que no haya dos
formas de escribir lo mismo.

**⚠️ ESTO NO SE PUEDE HACER SÓLO EN LA APP.** `perfiles.rol` tenía
`check (rol in ('usuario','admin'))`: la base **rechaza** un rol médico. Y todos los permisos
de escritura eran `es_admin()`. Como la clave publicable es pública por diseño, un permiso
dibujado sólo en el navegador no es un permiso. Por eso hay migración:
**`docs/supabase_roles_medicos.sql`**, que se corre una vez en el SQL Editor del panel.
Es idempotente y **no agrega tablas ni columnas**: cambia el CHECK, suma dos funciones y
reescribe policies.

⚠️ **Son dos archivos y no se pisan.** `supabase.sql` es la instalación **desde cero** (ya
incluye los cuatro roles); `supabase_roles_medicos.sql` es **sólo la diferencia**, para el
proyecto que ya está andando. Los dos dejan la base en el mismo estado. En el proyecto vivo se
corre **únicamente el segundo**.

Piezas clave:
- `es_medico_admin()`, `es_medico()`, `valida_medico()` — mismo patrón `security definer` que
  `es_admin()`, si no las policies de `perfiles` entran en recursión de RLS.
- **`correcciones_guardia()`** — el trigger que hace real el límite. Al médico administrador
  le revierte `nombre`, `norma`, `auditoria` y `asoc_extra` al valor anterior; de `datos` le
  sobreviven **dos** claves, `revision_medica` y, desde el 24/8/2026, `relaciones` (ver 4.5 ter
  bis). Mismo patrón que `perfiles_guardia`.
- `prop_resolver` — el médico administrador sólo cierra propuestas cuyo **autor es médico**.
- `pendientes()` — sigue devolviendo `json` (nada de cambiarle el tipo de retorno) y suma la
  clave `medicas`. Se le sacó el `where es_admin()` final, que hacía que no devolviera ninguna
  fila a quien no fuera administrador.

Del lado de la app: `ROLES`, `ROL_VALIDO()`, `rolLabel()` y **`CAP`** — todas las capacidades
en un solo objeto. Preguntar `role==='admin'` desparramado por treinta lugares fue lo que hizo
que sumar un rol tocara toda la app; ahora se pregunta `CAP.duenio(p)`, `CAP.validaMedico(p)`,
`CAP.observa(p)`, `CAP.editaFicha(p)`, `CAP.editaRelaciones(p)`.

**Dónde vive la revisión médica:** dentro de `correcciones.datos.revision_medica`
`{texto, por, de, t}`. `datos` ya era `jsonb` libre → **cero cambios de esquema**.

**Dónde se ve, y por qué ahí:**
- `revMedHTML(code)` → **la primera sección de la ficha**, arriba de la observación del
  administrador, de la valorización y de «cómo se carga». No es un detalle de ubicación:
  saber cómo cargar algo que no había que pedir no sirve de nada. Bloque `.revmed`, token
  **Contenedor propio** (`<section class="revmed">`, `margin-bottom:20px`): pegado a la
  observación del administrador los dos se leían como un solo bloque de dos colores. Lo
  confirmado y lo pendiente son **dos `<section>` separadas**, no una con una línea adentro.
  Texto a 15 px con `line-height:1.65` y tinta plena —es un criterio clínico, no una nota al
  pie—, la firma abajo separada por una línea, y los botones de editar/levantar como
  etiquetas que sólo se pintan al pasar por encima, para que no le compitan al texto.

  ⚠️ Esta regla estuvo **muerta desde el primer commit de roles** por un comentario CSS mal
  cerrado justo arriba (el `/*` se consumió al insertar el token `--med`): el parser se comía
  el bloque `.revmed{…}` entero y sólo sobrevivían las reglas hijas `.revmed .rm-*`. Se veía
  «casi bien», que es lo peor que puede pasar. Si algún día un bloque no toma estilos y sus
  hijos sí, mirá el comentario de arriba antes que la regla.
- `revMedLinea(code)` → **en el resultado del listado**, junto a `obsLinea()`. Mismo motivo
  que la observación: si hay que abrir la ficha para enterarse de que la práctica no
  corresponde al diagnóstico, ya se cargó mal. Ámbar = aviso administrativo, verde = médico.
- Se mantiene separada de la verificación administrativa: «contrasté contra la fuente» y
  «esto es correcto desde lo médico» no son lo mismo y si se parecieran, ninguno significaría
  nada.

**Editar y levantar desde la ficha misma** (`rmEdit` / `rmDel` → `editarRevision()` /
`quitarRevision()`), no sólo desde el panel: quien la escribió está mirando la ficha cuando se
da cuenta de que quedó mal, y mandarlo a Administración a buscarla en una lista era una vuelta
de más. Al editar se **refirma** con quien edita y la fecha de hoy — si dice «dada por buena
por» tiene que ser cierto del texto que se está leyendo.

**La ficha de un médico no muestra las acciones administrativas** (`Al validador`, `Copiar
código`, `Pasar a un compañero`, `Comparar`). Un médico entra a decir si la práctica se
corresponde con el diagnóstico, no a cargarla. **Imprimir ficha queda** para los cuatro roles:
sirve para llevársela a una junta.

**Si la migración todavía no se corrió**, la app no se rompe: el desplegable de rol muestra el
error real («la base todavía no acepta los roles médicos») y `pendientes()` sin la clave
`medicas` no pisa el conteo calculado del lado del cliente.

### 4.5 ter bis Relaciones entre códigos, editables por el médico administrador (24/8/2026)

`web/index.html`, sección **«Relaciones entre códigos»** de la ficha (incluye / no incluye /
incluido en) — lo que arma el **árbol de módulos**. Hasta acá era de sólo lectura, calculada
por el pipeline; ahora el administrador general y el **médico administrador** pueden agregar o
quitar prácticas, desde el mismo botón de siempre (**modo edición → «✎ Editar ficha»**, que
para el médico administrador dice **«✎ Editar relaciones entre códigos»** y muestra sólo eso —
ni nombre, ni norma, ni auditoría, que siguen siendo del general).

**⚠️ NO se puede hacer sólo en la app, mismo motivo que siempre**: `correcciones_guardia()` ya
sólo dejaba pasar `datos->'revision_medica'` para el médico administrador; todo lo demás
—incluida cualquier clave nueva que se le agregue a `datos`— vuelve al valor anterior del lado
del servidor. Migración: **`docs/supabase_relaciones_medico.sql`** (correr una vez, SQL Editor),
que suma `datos->'relaciones'` a lo que el guardia deja pasar. `supabase.sql` ya la incluye
para instalaciones nuevas. **En el proyecto vivo hay que correr `supabase_relaciones_medico.sql`
una vez** — sin eso, el botón guarda sin error pero el guardia descarta el cambio en silencio y
la ficha vuelve a la lista de antes en el siguiente `cargarContenidoNube()`.

De paso el guardia dejó de poder vaciar una clave que la escritura no traía: antes, guardar sólo
la revisión médica podía pisar con `null` una relación ya guardada (y ahora al revés). Las dos
claves se conservan del valor anterior cuando esta escritura no las trae. Ver el archivo de
migración para el detalle.

**Cómo se guarda**: agregar/quitar sobre la lista del **pipeline**, no un reemplazo — mismo
criterio que `correcciones_curadas.json` en el resto de la app. `CONTENT.codes[code].relaciones
= {incluye:{agregar:[…],quitar:[…]}, no_incluye:{…}, incluido_en:{…}}`, sólo las claves que de
verdad cambiaron. `applyCode()` lo aplica con `mergeListaRel()` contra `c._orig.relaciones`
(agregado a la instantánea del original, junto con nombre/norma/auditoria/asoc_extra).

**El espejo — `incluye` ↔ `incluido_en`**: si el código A pasa a incluir a B, B tiene que decir
que quedó incluido en A, si no el árbol de módulos (que lee `incluye`) y la ficha del hijo más
el detector de doble facturación de la Mesa de trabajo (que leen `incluido_en`) cuentan cosas
distintas. `espejarRelacion(otroCodigo, campo, accion, valor)` escribe la corrección del OTRO
código — sin tocar su nombre/norma/auditoria, que preserva tal cual — cada vez que se
agrega/quita algo de `incluye` o `incluido_en`. `no_incluye` no tiene campo espejo en el
esquema (siempre fue de un solo lado) y no se espeja.

**Restaurar**: el general tiene «Restaurar original» (la ficha entera — sigue siendo un
`DELETE`, que RLS reserva al administrador: CN-003 en `tests/rls/ataques.sql`). El médico
administrador tiene **«Restaurar relaciones originales»**, más chico: no borra la corrección
—no podría, RLS se lo rechazaría—, sólo vuelve `incluye`/`no_incluye`/`incluido_en` al valor del
pipeline y espeja también la vuelta atrás en los códigos afectados.

**Probado**: `tests/rls/regresion.sql` (el médico administrador guarda una relación sin perder
la revisión médica ya firmada, ni tocar la ficha, y viceversa) y `tests/e2e/casos/relaciones.mjs`
(la interfaz muestra los campos correctos según el rol, guarda, y el espejo aparece en el otro
código) — ver la sección de Testing, punto 3.

**Atajo «Vincular código» dentro de «Cómo se carga esta solicitud» (24/8/2026)**: mismo permiso
y mismo dato (`incluye`, con su espejo), pero sin abrir «Editar ficha» — un pedido directo de
Juan, para no tener que salir de la sección donde ya se está mirando qué códigos no se facturan
aparte. `web/index.html`, dentro del bloque `.carga`: se muestra con `CAP.editaRelaciones(current)`
nada más, **sin pedir Modo edición** —Juan lo probó sin saber que ese modo existía, y volver a
pedirlo fue un ajuste posterior: ese modo es para tocar la ficha completa (nombre, normas), un
gesto pensado para no editar por error, y vincular/anexar son livianos, viven al lado de «Contá
cómo se carga acá», que tampoco lo pide—. Guarda con `guardarIncluye(code, finArr)` —mismo
`deltaListaRel`/`espejarRelacion` que usa `editFicha()`, extraído para un solo campo— expuesto
como `NBUProfile.guardarIncluye()` porque el render de `.carga` vive en un `<script>` distinto
del que declara `editMode`/`CAP`/`guardarIncluye`: de ahí también que la condición para mostrar
el atajo se arme con `NBUProfile.editaRelaciones()` y no con `CAP` directamente (no está en ese
scope). Probado en `tests/e2e/casos/vincular.mjs`.

**Atajo «+ Anexar código» dentro de «Cargá esto» (24/8/2026)**: mismo permiso y mismo criterio de
visibilidad que «Vincular código» (sin Modo edición), pero **no es lo mismo dato ni el mismo
significado**. «Vincular» escribe
`relaciones.incluye` —el código vinculado NO se factura aparte, ya está comprendido—. «Anexar»
escribe un campo nuevo, `relaciones.anexar` —el código anexado SÍ se factura, aparte, pero el
administrativo tiene que acordarse de cargarlo junto con éste—. Pedido directo de Juan: son casos
que el pipeline no puede deducir solo (a diferencia de la urgencia → 661200 o el Acto Bioquímico,
que ya son reglas automáticas dentro de `comoSeCargaHTML()`).

Por ser un campo nuevo hizo falta sumarlo en tres lugares de `web/index.html` (buscar `anexar` para
ubicarlos): el snapshot y el merge de `applyCode()` (mismo patrón que `incluye`/`no_incluye`/
`incluido_en`), el render de los pasos en `comoSeCargaHTML(c, puedeAnexar)` —ahora recibe un
segundo argumento, para saber si mostrar la × de cada código anexado— y `guardarAnexar(code,
finArr)`, gemelo de `guardarIncluye()` pero **sin espejo**: no hay `espejarRelacion()` acá porque
ninguno de los dos códigos «incluye» al otro, los dos se cargan por separado. Expuesto también vía
`NBUProfile.guardarAnexar()`, mismo motivo de scope que `guardarIncluye()`.

**No hizo falta ninguna migración SQL**: `correcciones_guardia()` ya deja pasar la clave
`relaciones` entera para el médico administrador (`docs/supabase_relaciones_medico.sql`), sin
importar qué sub-claves tenga adentro — `anexar` viaja gratis con `incluye`/`no_incluye`/
`incluido_en`. Tampoco alimenta el Árbol de módulos ni la etiqueta «relaciones» (`hasRel()`): a
propósito, «anexar» no es una relación de inclusión, es un recordatorio de facturación — tiene su
propia etiqueta, ver más abajo.

Probado en `tests/e2e/casos/anexar.mjs`.

**Etiqueta «+ anexos» en el listado (24/8/2026)**: pedido de Juan, para que se vea desde la fila
de resultados que un código tiene anexados, sin tener que abrirlo. `rowHTML()`, junto a
«relaciones» pero con su propia clase (`.t-anex`) y color (reusa `--accent`/`--accent-soft`, el
mismo que «Cómo se carga»): a propósito NO la misma etiqueta que «relaciones» —confundirlas
mezclaría dos significados distintos (Árbol de módulos vs. recordatorio de facturación) bajo un
solo color—. Sumada también a la leyenda (`#tagLegend`/`TAG_LEYENDA`), mismo patrón que el resto
de las etiquetas. Probado en `tests/e2e/casos/anexar.mjs` (segundo caso: aparece al anexar,
desaparece al quitar el único anexado).

**Bug: vincular/anexar un código del Nomenclador Único devolvía «no existe» (24/8/2026)**: Juan
reportó que anexar el código 430111 (Único) a 200124 (VCC, PMO) decía que 430111 no existía.
Causa: `scripts/assemble.py` guarda los códigos del Único con el prefijo `"U"` —`ukey = "U"+code`—
para que no choquen con un NBU o PMO que use los mismos dígitos, pero la app **siempre** muestra
el código sin ese prefijo (`t.code`, no `_key`). Vincular, anexar y el editor completo de
relaciones (`editFicha()`) buscaban `BYCODE[k]` con `k` tal cual lo tipeaba la persona —lo que ve
en pantalla—, así que un código del Único nunca resolvía.

Arreglado con `resolverCodigo(k)` —declarada a nivel de archivo, junto a `BYCODE`, no adentro de
ninguna IIFE, para que la vean por igual el render de la ficha y el editor completo (viven en
`<script>` distintos)—: prueba `BYCODE[k]` y, si no está, `BYCODE['U'+k]`. Lo que devuelve es la
clave real, y es eso —no lo tipeado— lo que se guarda en `relaciones.incluye`/`relaciones.anexar`
y lo que llevan los atributos `data-quitar`/`data-quitar-anex` de los botones de sacar. Mismo
arreglo en las tres listas del editor completo (`efInc`/`efNoInc`/`efIncEn`).

De paso, el botón de sacar un código anexado (`× Quitar`, antes sólo `×`) pasó de ser un carácter
suelto al final de una línea larga —código y nombre de la práctica— a tener forma de botón
propio, en su propia línea: Juan lo pidió después de no encontrarlo (aunque ya estaba). Probado
en `tests/e2e/casos/anexar.mjs`, segundo caso, con los mismos códigos que reportó Juan.

*Corrección sobre la nota anterior de esta misma sección*: lo que parecía un bug de la app
(`TypeError: Cannot set properties of null (setting 'innerHTML')` en consola, al cerrar una ficha
y entrar a «Árbol de módulos») era un falso positivo del propio test. `sinOverlays()` sacaba de
encima el cartelito de pistas (`#pista`) con `.remove()` en vez de sólo ocultarlo con `.on` —la
app nunca lo borra, sólo lo apaga y prende—; al borrarlo, `revisarPistas()` (que se dispara al
cerrar la ficha) intenta escribirle el `innerHTML` a un nodo que el test acababa de eliminar. No
es nada que un usuario real dispare. Corregido en `casos/relaciones.mjs` y `casos/vincular.mjs`:
ocultar con `classList.remove('on')`, igual que ya se hacía con `tratoModal`.

### 4.5 quater ⚠️ Avisos del linter de Supabase — NO seguir la receta al pie de la letra

El linter marca **«SECURITY DEFINER Function … Revoke EXECUTE»** en las 13 funciones.
**Hacer eso a secas deja la app afuera.** Probado contra PostgreSQL 16 local:

```
revoke execute on function public.es_admin() from public, anon, authenticated;
→ insert en «correcciones» siendo administrador:
  ERROR: permission denied for function es_admin
```

Una expresión de policy se evalúa **con los permisos de quien hace la consulta**, no con los
del dueño de la tabla. Sin EXECUTE para `authenticated`, toda policy que llame a `es_admin()`
deja de poder evaluarse.

Lo correcto está en **`docs/supabase_permisos_funciones.sql`**:
- a **`anon`** se le saca todo (las 13);
- a **`authenticated`** se le deja sólo lo que la app necesita: las 5 de apoyo que usan las
  policies (`es_activo`, `es_admin`, `es_medico`, `es_medico_admin`, `valida_medico`) y las 4
  RPC (`pendientes`, `transferir_admin`, `pedir_verificacion`, `validar_verificacion`);
- las **4 de trigger** (`perfil_nuevo`, `perfil_guardia`, `un_solo_admin`,
  `correcciones_guardia`) se le sacan a todos. **Un trigger no comprueba EXECUTE para
  dispararse** — también probado: el guardia siguió recortando la fila con el permiso
  revocado.
- `alter default privileges … revoke execute on functions from public` para que la próxima
  función no nazca abierta.

Quedan **9 avisos que no se bajan y están bien así**: son justo las que `authenticated` tiene
que poder ejecutar. Cada una controla por dentro quién la llama.

### 4.5 quinquies Las cinco del circuito médico

1. **Filtro «sin revisión médica»** (+ «con revisión» y «revisión que necesita atención»).
   Grupo del rail marcado `'med'` en `GRUPOS_FLAGS`: sólo se dibuja para los médicos, y por
   eso el rail se repinta al entrar (`pintarFiltros()`), no una sola vez al arrancar. Con
   1.815 prácticas y ninguna forma de saber cuáles no tienen criterio, el manual se completaba
   sólo donde alguien se acordaba de mirar.
2. **Trabajo por lote** — `siguienteSinRevision()` / `siguienteHTML()`. Salta a la próxima sin
   criterio **dentro del filtro activo**, sin volver al listado, y dice cuántas faltan. Las
   revisiones vienen en familias; volver a la lista mil ochocientas veces no se hace.
3. **Consultar al médico** — ver el commit `3320eba` y `supabase_consultas_medicas.sql`.
4. **Vencimiento** — `REV_VENCE = 365` (la verificación administrativa usa 180: el criterio
   clínico cambia más despacio que la normativa de facturación).
5. **La ficha cambió después de la revisión** — al publicar se guarda `revision_medica.base`,
   una **huella del contenido** que el médico tenía delante (nombre, norma, auditoría,
   asociación, alcance, cobertura, tope). ⚠️ No se comparan fechas: publicar la revisión
   escribe la misma fila, así que `actualizado` siempre sería posterior y no diría nada.

Los dos últimos los resuelve `estadoRevision()` → `vigente` | `vencida` | `cambio`. La
revisión **sigue publicada** con una advertencia arriba (sacarla dejaría la ficha sin
criterio), y quien valida tiene **✓ Sigue valiendo**, que la refirma sin reescribirla.

### 4.5 sexies «Qué abarca este código», editable

Vive en `correcciones.datos.abarca` `{texto, por, t}`, al lado de `revision_medica`. Lo
escriben **los dos roles médicos y el administrador general** — el texto viene del Nomenclador
Nacional con la transcripción dañada y decide si hay que cargar un código más, así que quien
sabe si dice lo que tiene que decir no es quien factura. La ficha muestra el original debajo
(«La fuente decía: …») y se puede volver a él.

**También se lee en el resultado del listado** (`abarcaLinea()`), como la observación y la
revisión médica: es el dato que decide si hay que cargar un código más, y enterarse recién al
abrir la ficha llega tarde. Lo tienen **585 códigos de 6.478** —eran 96 cuando se escribió
esto; el barrido de 3.8 los multiplicó por seis y los va a seguir sumando—, así que sigue sin
ensuciar el listado: donde aparece, es porque hay algo que saber. Va **antes** de los dos avisos y sin fondo: no es
una alerta, es parte de lo que el código *es*; si compitiera con la observación y la revisión
—que sí son alertas— las tres dejarían de significar algo distinto. El ✓ verde marca las
corregidas por un médico; el ▣ apagado, el texto crudo de la fuente.

✅ **RESUELTO: el capítulo 34 se transcribió del PDF original.** El usuario aportó el
Nomenclador Nacional escaneado (`data/NOMENCLADOR NACIONAL DE PRESTACIONES MEDICAS CON
PMO-COMPRIMIDO.pdf`, 260 páginas, **sin capa de texto**). No hay OCR instalado en el entorno,
así que las páginas del capítulo 34 (**132-142 del archivo**) se renderizaron con `pypdfium2`
y se **leyeron a ojo**, una por una.

Resultado en `data/alcance_nn_cap34.json` (110 códigos) y aplicado a la base:
- **88 de 96 textos estaban mal** y se corrigieron.
- Errores que cambiaban lo que se factura: `Zplacas` era **2 placas**; `Meca dedos` era
  **muñeca dedos**; `(ogregaralcodigo` era **(agregar al código**.
- **5 alcances nuevos** que el OCR había perdido del todo.
- ⚠️ **`342014` no lleva alcance**: lo que mostraba era la **Norma del capítulo 35**, que el
  parser arrastró cruzando el límite de capítulo. Se quitó, no se corrigió.

La ortografía del original se respeta tal cual —casi no acentúa, y tiene erratas propias como
«constraste» en 341003—: es texto normativo, no un descuido de transcripción.

`alcance_cap34.py` carga ese JSON y **manda sobre el OCR**; si el archivo faltara, sigue con
la limpieza vieja. Los alcances transcriptos llevan `fuente: "original"` y por eso el listado
ya **no** los marca «sin confirmar», y el filtro «▣ Alcance sin confirmar» **se esconde solo**
cuando no queda ninguno (hoy: ninguno).

⚠️ **Lo que NO se hizo, y no hay que intentar:** reparar el OCR automáticamente. Se probó
despegar palabras contra un vocabulario armado con las 6.372 denominaciones de la base y
**produce texto peor** («incidenciaypor» → «incid enciay»). Con cantidades de placas de por
medio, adivinar no es una opción.

Migración: **`docs/supabase_alcance_medico.sql`**. Dos hallazgos que costaron:
- El guardia ahora tiene **dos niveles**: al médico administrativo se le abre `correcciones`
  por primera vez, y si se le diera la fila entera podría publicar una revisión sin que nadie
  la valide. `abarca` → los dos; `revision_medica` → sólo `es_medico_admin()`.
- ⚠️ **La restricción de DELETE tiene que ser `AS RESTRICTIVE`.** Las policies permisivas se
  suman (OR): una segunda policy de delete «sólo es_admin()» no le quitaba nada al `FOR ALL`,
  y en la prueba contra PostgreSQL 16 **el médico borró la fila entera**.

### 4.5 septies La cobertura, según quién mira

`coberturaHTML(c, destacada)`. Para el **administrativo** queda donde estuvo siempre, después
de la valorización: él ya sabe que se cubre —se lo dijo el veredicto— y lo que necesita es
cargarla. Para el **auditor médico** sube a la segunda posición, justo debajo de la revisión
médica, con `.cob-card.destacada` (borde de 5 px, 14.5 px, más interlínea): decidir si
corresponde cubrirla **es** su trabajo, y estaba enterrada entre la muestra y el SURGE.

### 4.5 octies La U.B. del otro nomenclador, en la propia equivalencia

`ubDe(key)` lee la U.B. vigente de cualquier ficha. Las dos tarjetas de equivalencia la
muestran ahora en la misma fila del código (`.equb`):
- Ficha del **Único** → «Equivale a 663254 · **160 U.B.**»
- Ficha del **NBU** → «64663254 · **100 U.B.**»

Estaba sólo en «Valorización», al final de la ficha (`refNBU`), y quien mira la equivalencia
justamente se pregunta cuánto vale del otro lado.

Cuando **no coinciden**, sale un aviso `.eqdif`: «la diferencia es del convenio, no un error».
Hoy pasa en **1 sola práctica** de 1.678 (`U64663254` 100 U.B. vs NBU `663254` 160 U.B.) — el
comentario viejo del código hablaba de 101, así que el dato cambió y el aviso es barato.

### 3.8 ⚠️ EL HUECO GRANDE: la norma retirada del PMO falta en el 89% de las fichas

El Nomenclador Nacional trae al lado de cada práctica un recuadro **«Texto retirado por el
PMO»** —qué abarca el código, qué incluye, bajo qué reglas se factura—. El armado de la base
sale del catálogo del PMO, así que ese renglón **no llegaba nunca a la ficha**.

Estado al detectarlo (lo encontró el usuario, verificando 250101/250102 contra el papel):

| | |
|---|---|
| códigos PMO en la base | **1.351** |
| con la norma del Nacional | **156** (11%) |
| **sin nada** | **1.195** |
| capítulos enteros en cero | **30 de 41** |

Los únicos con norma son los que se procesaron del PDF: **34** (transcripto a mano) y **26,
27, 28, 40, 41, 42, 43, 44** (por `importar_capitulos_nn.py`). Todo el resto vino del pipeline
viejo, que nunca leyó esos recuadros.

⚠️ **El PDF es un escaneo sin capa de texto.** Verificado con `pypdfium2`:
`get_textpage().get_text_range()` devuelve **0 caracteres** en todas las páginas probadas. Y el
OCR de estas páginas viene destruido (ver 9.1). Así que no hay atajo: hay que leer a ojo.

#### La maquinaria: `scripts/alcance_nn_pmo.py` + `data/alcance_nn_pmo.json`

⚠️ **No confundir con `importar_capitulos_nn.py`**: aquél **crea** códigos de capítulos que
faltaban enteros; éste **no crea nada**, le agrega la norma a códigos que ya están.

Para sumar un capítulo alcanza con agregarlo al JSON. El script no sabe ninguno de memoria.

- El texto por código va a `alcance_nn` con `fuente: "original"` — eso es lo que hace que la
  ficha lo muestre **sin** el cartel de «transcripción sin confirmar», que es para lo que
  quedó del OCR viejo.
- La **norma de capítulo** va como líneas `Norma del código:` en la auditoría de **todas** las
  fichas del capítulo, no sólo las que tienen texto propio: quien abre una ficha suelta tiene
  que leer la regla que la gobierna sin saber que existe un encabezado de capítulo. Mismo
  criterio que el material radioactivo del 26.
- Termina comparando los 6.476 nombres y aborta si alguno se movió.

⚠️ **Se respeta la ortografía impresa.** El original casi no acentúa y tiene erratas propias
(«cógido» por «código», capítulo 25). No se corrigen: es el texto normativo y un auditor que
compare contra el papel tiene que encontrar lo mismo.

#### La leyenda que define el recuadro (página 3 impresa, 12 del archivo)

Está impresa en el PDF y conviene tenerla a mano, porque explica exactamente qué se está
transcribiendo:

> Los códigos de la primer columna corresponden **tanto al P.M.O. como al Nomenclador
> Nacional**. Los códigos, textos y valores **excluidos del Nomenclador por el P.M.O.** se
> indican con: `Texto retirado por el PMO`. Los textos en negrilla corresponden al Nomenclador
> Nacional y **mantenidos** por el P.M.O. Los valores y unidades corresponden al Nomenclador
> Nacional (valores a marzo/1991). Para una mejor orientación se mantuvieron las normas e
> interpretaciones del Nomenclador Nacional.

⚠️ De ahí sale una distinción que hay que respetar al transcribir: **bastardilla = retirado,
negrita/versalita = mantenido**. El recuadro marca dónde empieza lo retirado, y sigue hasta
donde vuelve la negrita. Un código puede tener **dos recuadros** (p. ej. `010304`, cordotomía:
uno antes de «mielotomía comisural» y otro después).

#### Avance

| capítulo | páginas del archivo | códigos | estado |
|---|---|---|---|
| 01 · Sistema nervioso | 12–17 | 69 | ✅ 33 textos |
| 02 · Aparato de la visión | 18–23 | 51 | ✅ 24 textos + 1 norma por código |
| 03 · Otorrinolaringológicas | 24–32 | 118 | ✅ 45 textos |
| 04 · Sistema endocrino | 33 | 11 | ✅ 2 textos |
| 05 · Tórax | 34–36 | 23 | ✅ 10 textos + 1 norma por código |
| 07 · Sistema cardiovascular | 38–46 | 82 | ✅ 44 textos + 2 normas de sub-capítulo |
| 08 · Aparato digestivo y abdomen | 47–55 | 123 | ✅ 66 textos + 2 normas de sub-capítulo |
| 13 · Piel y tejido subcutáneo | 81–83 | 30 | ✅ 20 textos + 4 normas |
| 10 · Urinario y genital masculino | 57–63 | 82 | ✅ 33 textos + 1 norma de capítulo |
| 11 · Genital femenino y obstetricia | 64–67 | 49 | ✅ 33 textos + 3 normas (una de sub-capítulo, dos por código) |
| 12 · Músculo esquelético | 68–80 | 146 | ✅ 64 textos + 3 normas de capítulo + 13 de sub-capítulo |
| 25 · Rehabilitación médica | 111–112 | 6 | ✅ 6 textos + 5 normas |
| 20 · Gastroenterología | 97–99 | 25 | ✅ 13 textos + 1 norma en dos códigos |
| 24 · Hemoterapia | 109–111 | 21 | ✅ 9 textos + 4 normas del 24.01 + 2 por código |
| 17 · Cardiología | 91–94 | 20 | ✅ 9 textos + 3 normas por código |
| 18 · Ecografía – Ecodoppler | 94–96 | 22 | ✅ 5 textos + 10 normas de capítulo + 3 por código |
| 31 · Otorrinolaringología | 128–129 | 19 | ✅ 3 textos + 1 norma por código |
| 30 · Oftalmología | 126–128 | 18 | ✅ 14 textos + 1 norma por código |
| 29 · Neurología | 125–126 | 14 | ✅ 0 textos — el capítulo no tiene ninguno, y es correcto |
| 21 · Genética humana | 100–101 | 15 | ✅ 8 textos + el 21.02.08, que faltaba |
| 15 · Anatomía patológica | 89–90 | 12 | ✅ 9 textos + 1 norma de código (150109 en el PDF, no en la base) |
| 22 · Ginecología y obstetricia | 101–102 | 13 | ✅ 4 textos + 3 normas de código (220102 en el PDF, no en la base) |
| 33 · Psiquiatría | 130–131 | 13 | ✅ 8 textos + 1 norma de sub-capítulo + 1 de código |
| 06 · Operaciones en la mama | 37 | 12 | ✅ 7 textos |
| 09 · Vasos y ganglios linfáticos | 56 | 8 | ✅ 3 textos |
| 14 · Alergia | 88 | 1 | ✅ 0 textos + 1 norma de capítulo (140101, 140102, 140104 en el PDF, retirados enteros, no en la base) |
| 16 · Anestesiología | 90 | 5 | ✅ 4 textos + 2 normas de código |
| 19 · Endocrinología y nutrición | 97 | 3 | ✅ 0 textos — el capítulo no tiene ninguno, y es correcto |
| 32 · Pediatría | 129 | 1 | ✅ 0 textos + 1 norma de código |
| 35 · Terapia radiante | 141–142 | 9 | ✅ 2 textos + 1 norma de capítulo (6 puntos, A a F) |
| 36 · Urología | 142–143 | 10 | ✅ 3 textos + 1 norma de sub-capítulo (impresa 3 veces; 360104 y 360106 en el PDF, no en la base) |
| 38 · Tratamientos especiales | 143 | 2 | ✅ 0 textos — los dos códigos son agregados del PMO con obligación de cobertura, nada retirado |

**Con esto se terminó el barrido del Nomenclador Nacional capítulo por capítulo.** No queda
ningún capítulo pendiente de transcribir — el único trabajo que sigue es el capítulo 66 (NBU
laboratorio), que es un cotejo distinto, ver más abajo.

Cobertura: **844 de 1.353 (62%)**, desde 156 (11%). El 23 (hemoterapia) queda aparte de esta
cuenta (ver más abajo); el 66 no es del mismo tipo de trabajo ni cuenta acá — ver el punto
siguiente.

#### ✅ Capítulo 66 (análisis clínicos): el mismo texto retirado, pero para el NBU, no el PMO — completo

El usuario aclaró el 18/8/2026 cómo tratar este capítulo: **el texto «retirado por el PMO» de
estas 36 páginas se suma como mejora a las fichas del NBU que ya existen**, no como fichas PMO
nuevas ni como equivalencias — la comparación entre el catálogo del NBU y el de acá queda para
más adelante. Mecánicamente es el **mismo `scripts/alcance_nn_pmo.py`**: como busca el código
sin mirar el nomenclador, declarar el capítulo `"66"` en `data/alcance_nn_pmo.json` con
códigos de 6 dígitos (`66.00.02` → `"660002"`) alcanza para que el texto caiga en la ficha NBU
correcta. **No hace falta un script nuevo.**

⚠️ **Lo que sí cambia respecto de los capítulos PMO: hay que verificar el nombre antes de
declarar cada código.** En capítulos anteriores, que un código exista en la base ya alcanzaba
—ahí el código es la MISMA fila que se está leyendo—. Acá no: el número de la primer columna
puede coincidir por casualidad con un código NBU que es **otra práctica**. Verificado en las
36 páginas: decenas de candidatos con nombre parecido, **varios choques
reales** —número compartido con una práctica totalmente distinta, por ejemplo `660001`
«ACTO BIOQUÍMICO» contra «Acetaldehido enzimático», o `660245` «CHAGAS, SEROLOGÍA» contra
«Chediak, reacción de»— y **varios quedaron dudosos** —nombre o método parecido pero no
idéntico, no declarados hasta revisarlos a mano—. El detalle código por código de cada página
está en `data/alcance_nn_pmo.json` bajo `"66"._nota_pagina_168` a `_nota_pagina_203` (más
`_nota_barrido_completo` con el resumen final). La regla
para seguir: **comparar el nombre en negrita del PDF contra el nombre que ya tiene la ficha; si
no coinciden razonablemente, no declarar ese código** (dejar nota, no adivinar) — el mismo
criterio se aplica si coincide el nombre pero no el **método** (p. ej. `660833` «Bencidina»
química contra «Sangre oculta... inmunológico» de la base, o `660418` «dehidrogenasa» contra
«ISOMERASA» de la base: son dos enzimas distintas aunque el nombre general se parezca).
Otras dos trampas a tener en cuenta: algunos renglones traen su propio código de 6 dígitos
metido en el cuerpo del texto en vez de en la columna CODIGO (ver `_nota_orden` más abajo); y
el PDF a veces **repite el mismo código** en dos o tres posiciones alfabéticas distintas (por
nombre, sinónimo o variante «Plan Materno Infantil»), casi siempre con el mismo recuadro (sin
problema), pero alguna vez con uno distinto — y ahí hay que distinguir dos casos: si los dos
textos **se contradicen** (`660005`/«Astrup», `660166`/«Colpocitograma»), no pisar el ya
cargado; si el segundo texto sólo **agrega detalle sin contradecir** al primero
(`660430`/«Graham», `660293`/«Gravindex»), sí conviene actualizar al texto más completo. Un
código puede además existir en la
base bajo nomenclador **PMO** en vez de NBU (`660185`) — no cambia nada, el script busca por
código sin mirar el nomenclador.

**Escala: terminado el 19/8/2026.** 36 páginas (168-203), ~1.815 fichas NBU candidatas,
**134 códigos con texto cargado**. Cada página documentada en `data/alcance_nn_pmo.json` bajo
`"66"._nota_pagina_168` a `_nota_pagina_203`, con el detalle código por código; el resumen
final está en `_nota_barrido_completo`.
⚠️ Tres códigos (`660430`, `660293`, `660887`) aparecieron dos veces con textos
**complementarios, no contradictorios** (uno más corto, uno más completo sobre la misma
referencia) — a diferencia de `660005`/`660166` (textos que sí se contradicen), ahí se
actualizó al texto más completo en vez de dejar el primero.
⚠️ **Varios «choques» de las primeras páginas se resolvieron solos más adelante**, cuando
apareció la ficha primaria bajo su propio nombre alfabético: `660143`, `660335`, `660767`,
`660594`, `660933` parecían coincidencias de número al principio, pero más adelante el mismo
código reaparece con el nombre correcto y coincide con la base — quedan confirmados, no son
choques reales. La lección para el próximo barrido de este tipo: un «choque» en la primera
aparición no es definitivo, puede ser sólo una referencia cruzada bajo otro nombre; conviene
revisar de nuevo al terminar el capítulo si el mismo número volvió a aparecer.

⚠️ **Que un sub-capítulo no aporte ningún texto puede ser lo correcto.** El `02.09` (LASER) son
ocho códigos que AGREGÓ el PMO: no figuran en el Nomenclador Nacional, así que no hay recuadro
que transcribir. Lo que traen es obligación de cobertura, que la app maneja aparte. Antes de
sospechar una transcripción incompleta, mirar si el bloque dice «CODIGO AGREGADO POR EL P.M.O.».

⚠️ El orden de la tabla es el del JSON, no el numérico. Para saber qué falta, correr el script:
lista cada capítulo cargado con su cuenta.

#### ⚠️ Qué correr después de importar un capítulo (y qué NO)

Medido, no estimado:

| paso | tiempo |
|---|---|
| los tres scripts de datos | **3 s** |
| render de 9 páginas del PDF | **2 s** |
| `scripts/comprobar_datos.mjs` | **2,5 s** |
| batería completa (`hl_check`+`roles_limite`+`lote`+`favglob`) | **80 s** |
| └ de eso, `waitForTimeout` a ciegas | **39 s** |

⚠️ **Los importadores de capítulo NO tocan `index.html`** — escriben `data/nbu_db.json` y de ahí
sale `web/nbu_db.bin`. `roles_limite` (permisos), `favglob` (favoritos) y `tour2` (tutorial)
prueban código que no se movió: correrlos es pagar 77 segundos por nada.

Después de importar un capítulo alcanza con:

    python3 scripts/alcance_nn_pmo.py && python3 scripts/nombres_rotos.py && python3 scripts/propagar_abarca_unico.py && python3 scripts/inject_db.py
    cd web && python3 -m http.server 8890 --bind 127.0.0.1 &
    node scripts/comprobar_datos.mjs

La batería completa va cuando se toca `index.html`, no antes.

#### 🆕 `scripts/propagar_abarca_unico.py` — el «Abarca» pasa al código equivalente del Único

Pedido del usuario (18/8/2026): lo que un código de Prestaciones Médicas o del NBU dice que
abarca —el mismo texto que pone `alcance_nn_pmo.py`— tiene que verse también desde el código
equivalente del Único, porque son la misma práctica con otro número; si uno cambia, el otro
tiene que cambiar con él. `propagar_al_unico.py` (el script viejo) sólo ata el laboratorio
(Único ↔ NBU) y no tocaba este campo. El nuevo cubre las **dos puntas** —Único médico ↔ PMO y
Único laboratorio ↔ NBU— y sólo copia cuando la equivalencia ya está resuelta (`key`
presente): si el destino todavía no existe en la base, no hay de dónde copiar, y ese caso se
arregla solo apenas se importe (igual que `reparar_equivalencias.py`). Corrido el 18/8/2026
sobre la base ya fusionada: **577 fichas del Único heredaron el «Abarca»** (574 médicas, 3 de
laboratorio — estas últimas nada más porque el capítulo 66 recién arrancó, ver más abajo). Va
**siempre** en la receta de después de importar un capítulo, entre `nombres_rotos.py` e
`inject_db.py`.

⚠️ **El tiempo real de un capítulo es leer las páginas**, no verificar: son 9 imágenes de
~527 KB que hay que mirar de a una porque el PDF no tiene capa de texto. Eso es el trabajo y no
se acelera; lo que sí se puede es no sumarle un minuto y medio de tests que no aplican.

⚠️ **Un `waitForFunction` que falla se paga entero.** La primera versión de
`comprobar_datos.mjs` tardaba 47 s —más que la batería— porque tres esperas con timeout de 15 s
no se cumplían nunca. Con timeout de 2,5 s y el cambio de nomenclador arreglado, 2,5 s. Al
escribir un test, el timeout de una espera que puede fallar es el costo, no el techo.

⚠️ **NO canalizar la salida del script por `head`.** El SIGPIPE lo mata antes de que escriba el
JSON, y como `inject_db.py` corre igual sobre la base vieja, todo parece haber funcionado y la
cobertura no se mueve. Pasó una vez; usar `tail` o nada.

#### ⚠️ Normas de sub-capítulo: `normas_prefijo`

El 12 obligó a agregarlas. `norma` gobierna el capítulo entero; `normas_prefijo` gobierna un
sub-capítulo (`{"1219": [...]}` → todas las fichas que empiezan con `1219`).

⚠️ **Cuándo el alcance es el sub-capítulo y cuándo un solo código.** Tres señales, por orden
de fuerza:
1. **La norma dice «este código»** → va al código. (`110404`, `130107`)
2. **Habla en singular de una práctica** —«No *será facturada* cuando sea complementaria»— →
   va al código. (`050202`)
3. **Está impresa DOS VECES en el mismo sub-capítulo** → va al sub-capítulo: si gobernara un
   código no haría falta repetirla. (la de gastos de curaciones, en el `13.01`)

⚠️ **Estar impresa en el encabezado del capítulo NO la hace norma de capítulo.** Lo que manda
es lo que la norma dice de sí misma, y el 20 y el 24 lo dejaron a la vista:

- El **20** tiene una sola norma, en el encabezado, y se acota sola: «los códigos 20.01.01 al
  20.01.03 no incluyen el costo de las sustancias». Va como prefijo de esos códigos. Pegársela
  a los 25 del capítulo diría que la polipectomía tampoco incluye las sustancias, y eso el
  nomenclador no lo dice.
- El **24** tiene cuatro renglones en el encabezado, todos sobre «cada unidad de tranfusión»,
  el grupo del dador y las pruebas de compatibilidad: son del `24.01`. El `24.02/10/11/12`
  —ultrafiltración, criopreservación, trasplante de médula— son códigos que agregó el PMO y no
  están en el Nacional: decirles que su honorario incluye la tipificación ABO del dador sería
  inventarles alcance. Verificado: el `241203` quedó con cero normas y el `240113` con las cuatro.

⚠️ **Una norma puede no tener dónde caer y hay que declararla igual.** La del anti VIH del 24
está impresa dos veces (bajo el `24.01.20` y bajo el `24.01.21`) pero **ambos códigos están en
bastardilla**: el PMO retiró entera la serología del dador (`24.01.14` al `24.01.21`) y ninguno
está en la base. Queda declarada como `"240120"` y el script avisa «NINGUNA ficha con ese
prefijo» en cada corrida — igual que el `12.01`. Que la repetición sea doble **no** la convierte
en norma del `24.01` (señal 3): nombra los códigos con todas las letras, que es señal más fuerte.

⚠️ **El prefijo puede ser el código completo.** El 11.04 tiene dos normas que NO gobiernan el
sub-capítulo: cada una está impresa pegada a su código, y la segunda lo dice con todas las
letras —«estan incluidas en ESTE código»—. Se declaran como `"110401"` y `"110404"`. Verificado:
el 11.04.02 y el 11.04.05 recibieron sólo la del sub-capítulo.

**La distinción no es cosmética**: el 12 tiene trece normas de sub-capítulo, y pegarle a los
146 códigos la del 12.01 —«el arancel para el tratamiento no quirúrgico de las fracturas SIN
DESPLAZAMIENTO será el de la confección del yeso»— sería decirle al administrativo que eso
rige para las amputaciones. Verificado después de importar: la amputación `121601` recibió
sólo las 3 normas de capítulo, y el yeso `121901` recibió además la del 12.19.

⚠️ **Cero fichas no es un error.** `12.01` («fracturas sin desplazamiento») no tiene códigos
propios: el PMO lo vació entero. Su norma queda declarada y el script avisa «NINGUNA ficha con
ese prefijo». **No pegarla al 12.02 ni al capítulo** — sería inventarle alcance a una regla
que el nomenclador escribió para otra cosa.

⚠️ **Un texto de dos palabras no es una transcripción cortada.** El recuadro empieza donde
arranca la bastardilla y termina donde vuelve la negrita, y a veces lo retirado es sólo el nexo
que el PMO borró del renglón: el `240108` es «De» (por «**De** HASTA 500 CC.»), el `240107` es
«Hasta», el `170118` es «dos canales», el `200101` es «Estudio». Es lo mismo que ya pasaba con
el `250103` («y por beneficiario»). Cuando el código trae **dos** recuadros con negrita en el
medio se unen con un espacio, como el `010304`: el `200107` queda «con sonda con control
radioscopico…» y el `200123`, «papila con colangio y/o pancreatografia».

⚠️ **No todos los códigos llevan recuadro.** En el capítulo 01, 33 de 69. Los que no tienen
son los que el Nacional imprime completos en negrita (nada retirado) y los marcados «CODIGO
AGREGADO POR EL P.M.O.», que por definición no están en el Nacional. Que un capítulo quede
con menos textos que códigos es lo normal, no una transcripción a medias.

⚠️ **Y el límite de eso es cero: el capítulo 29 (neurología) no aporta ni un texto.** Se lo
leyó entero igual y quedó declarado en el JSON con `codigos` vacío, porque «leído y no aporta
nada» y «todavía no se leyó» tienen que poder distinguirse — si no, el capítulo vuelve a la
lista de pendientes en la sesión siguiente. Sus 14 códigos son nueve impresos enteros en
negrita y cinco agregados por el P.M.O.; el único recuadro del capítulo es el del `29.01.01`
(electroencefalografía con activación simple), que viene con el **número de código y los valores
también en bastardilla** —el PMO lo retiró entero— y por eso no está en la base. **Ese es el
patrón a reconocer**: cuando el número de código está en bastardilla, la práctica entera salió
del catálogo y no hay ficha que decorar. En el capítulo 30 pasa siete veces (30.01.04, 05, 07,
12, 14, 15 y 21).

#### ✅ El barrido capítulo por capítulo terminó (última tanda: 35, 36 y 38, el 18/8/2026)

`data/paginas_nn.json` tiene **dónde empieza y termina cada capítulo en el PDF**, sacado por
OCR y completado a mano. Los tres que faltaban (el barrido de OCR había llegado sólo hasta la
139) se encontraron buscando el final del capítulo 34: el **35 (Terapia radiante)** arranca a
mitad de la **141**, debajo del `34.20.14`; el **36 (Urología)** a mitad de la **142**; el
**38 (Tratamientos especiales)** a mitad de la **143**, y termina ahí mismo — el `40/41` ya
arranca en la **144**. No hace falta volver a buscar nada de esto a mano.

Lo único que sigue es el **capítulo 66** (análisis clínicos, páginas 168-203): es «texto
retirado por el PMO» igual que todo lo anterior, pero el texto se suma a las fichas del NBU
que ya existen, con el cuidado extra de verificar el nombre antes de declarar cada código —
ver el punto «Capítulo 66» más arriba (dentro de 3.8) para la receta y lo ya encontrado.

**Receta por capítulo**, unos 10 minutos cada uno:

1. `python3 scripts/paginas_nn.py 20` — renderiza el capítulo **recortado** y **leerlas como
   imagen**. (Acepta números de página sueltos también.)
2. Transcribir los recuadros a `data/alcance_nn_pmo.json` bajo el capítulo, respetando la
   ortografía impresa.
3. `python3 scripts/alcance_nn_pmo.py && python3 scripts/nombres_rotos.py && python3 scripts/propagar_abarca_unico.py && python3 scripts/inject_db.py`
4. `node scripts/comprobar_datos.mjs` (2,5 s; NO la batería completa — ver más arriba).
5. Los scripts avisan qué códigos del JSON no están en la base y verifican que ningún nombre
   se haya movido.

⚠️ **Las filas «Norma:» se salen del recorte y hay que releerlas anchas.** El borde de 0,685
está calculado para la columna de descripción, pero los renglones de norma —los que arrancan
con `Norma:` en la primera columna— ocupan **todo el ancho de la página**, así que el recorte
los corta a mitad de frase sin que se note: la del capítulo 20 termina en «…utilizadas para» y
sigue «realizar las distintas pruebas», y la del 17.01.09 se corta en «…que justifique su reali‑».
La receta es no confiar en la primera lectura de esas filas: volver a renderizar **sólo esa
franja** con el borde derecho en 0,95 y la escala en 3,4 (queda en ~1.970 px, que es el ancho
máximo antes de que la imagen se reescale y se vuelva ilegible). Un recorte de tres renglones
cuesta ~300 tokens; no vale la pena ampliar la caja para todas las páginas.

⚠️ **`data/paginas_nn.json` da la página con MÁS códigos, no el capítulo entero: casi todos se
derraman en la siguiente.** El índice salió de contar códigos `NN.NN.NN` por página, así que
cada página quedó asignada a un solo capítulo aunque tenga dos. Los tres de esta tanda se
derramaron y en uno de ellos había texto que transcribir:

- el **21** figura como «100» y sigue arriba de la **101** con el 21.02.05, el 21.02.06 y el
  21.02.07: **tres recuadros**, que son 3 de los 8 textos del capítulo. Sin mirar la 101 el
  capítulo quedaba a mitad de camino y el script no lo habría avisado —ni sobran códigos ni se
  movió ningún nombre—;
- el **30** figura como «126–127» y termina arriba de la **128** con el 30.02.04 y el 30.02.05,
  los dos AGREGADOS POR EL P.M.O. (sin recuadro);
- el **29** figura como «125» y termina arriba de la **126** con los tres del 29.02, también
  agregados.

Ya se sabía que pasaba —el 24 y el 25 comparten la 111, el 19 y el 20 comparten la 97— pero
como ahí el solapamiento estaba escrito en el índice, no se leyó como regla. **Lo es**: la
receta del punto 1 es `paginas_nn.py <cap>` **y además la página siguiente a la última**,
mirando dónde arranca el encabezado del capítulo que sigue. Cuesta ~1.200 tokens y es la
diferencia entre un capítulo completo y uno que parece completo.

⚠️ **Un código impreso «AGREGADO POR EL P.M.O.» que no está en la base es un faltante real, y
no lo arregla este barrido.** `alcance_nn_pmo.py` no crea códigos: sólo le pone la norma a los
que ya están. Cuando aparece uno así hay que anotarlo y pasarlo por
`importar_capitulos_nn.py`, que es el que sí crea.

✅ **Pasó con el `21.02.08` y ya está resuelto** (18/8/2026, por decisión del usuario).
Genotipificación virus hepatitis C en pacientes HIV positivos: impreso en negrita al pie del
capítulo 21, marcado «CODIGO AGREGADO POR EL P.M.O.» —o sea, del catálogo obligatorio— con
coseguro hasta 250 y sin unidades de honorarios ni gastos. Entró como capítulo `"21"` de
`data/capitulos_nn.json` con `agregado_pmo`, sin `alcance` (un código agregado por el PMO no
está en el Nacional, así que no hay recuadro que transcribir) y sin `retirado_pmo`. Mismo
camino que el `23.02.34`.

⚠️ **Y arrastró una equivalencia mal numerada.** El Nomenclador Único ya traía la práctica con
el **mismo número** —`U210208`, mismo nombre palabra por palabra— pero su planilla declaraba
como equivalente el `220209`, que no existe y que además caería en ginecología y obstetricia:
una transposición del 21 por el 22. Quedaba colgada con `destino_inexistente`, y
`reparar_equivalencias.py` **no la arregla** —ése sólo ata las que apuntan a un código que
todavía no existía, no las que apuntan a uno equivocado—. Se ató por
`equivalencias_renumeradas.py` (4.5 undecies), que es el mecanismo para exactamente este caso.
**Al importar un código conviene mirar si el Único ya lo traía**: `grep` del nombre sobre
`data/nbu_db.json` alcanza.

No es un hallazgo nuevo —**`docs/inventario_faltantes.json` ya lo tenía**, junto con el
`29.01.01` y los siete retirados del 30—, y ese cruce sirve de control: los códigos que la
lectura a ojo encontró en bastardilla o sin ficha coincidieron **uno a uno** con lo que ese
archivo lista para los tres capítulos. Conviene abrirlo antes de transcribir: dice de antemano
qué códigos del PDF no van a tener dónde caer, y una diferencia entre esa lista y lo que se ve
en la página es señal de que se leyó mal. ⚠️ Sus páginas son las **impresas**, una más que las
del archivo que usa `paginas_nn.py`.

(El otro renglón suelto del 21, el «21.01.01 A» de consulta genética por Res. 58/17-MS, **no**
es un caso igual: es una fila de coseguro, sin código de seis dígitos y sin ficha que le
corresponda.)

#### ⚠️ EL COSTO REAL DE ESTE TRABAJO: una sesión larga se encarece sola

Cada imagen que entra a la conversación **se reenvía en todos los pedidos siguientes**. No es
un costo que se pague una vez: la primera página de una sesión larga se manda decenas de
veces. Medido en la sesión del 18/8: **74 páginas leídas = ~168.000 tokens de visión**
arrastrados en cada turno, y un pedido trivial al final costaba tanto como el trabajo entero.

Dos consecuencias operativas, ambas importantes:

1. **Las páginas van recortadas.** `scripts/paginas_nn.py` corta la mitad derecha —honorarios,
   gastos, total— que no se transcribe. De 2.265 a 1.199 tokens por página, **47% menos**, con
   la bastardilla igual de legible.
2. ⚠️ **Un lote de capítulos por sesión, y sesión NUEVA para el siguiente.** Este documento
   está escrito para retomar en frío: tiene el índice de páginas, la receta, el orden sugerido
   y las reglas de alcance. Seguir en una sesión ya cargada cuesta entre 5 y 10 veces más que
   arrancar limpio, y no se gana nada a cambio.

**✅ El barrido capítulo por capítulo terminó el 18/8/2026.** Los últimos tres —**35, 36 y
38**— no tenían página en el índice (el barrido de OCR de `data/paginas_nn.json` había
llegado sólo hasta la 139); se encontraron a mano buscando el final del capítulo 34 y ya están
declarados. Lo único que queda del trabajo de datos del Nacional es el **capítulo 66** (NBU
laboratorio), que es otro tipo de tarea — ver D más abajo.

Hechos el 18/8, en cuatro sesiones distintas y fusionadas después: **20, 24, 17, 18, 31, 30,
29, 21** (rama `nomenclador-chapters-30-29-21-0c4v9o`, que incluye los commits de la rama
`nomenclador-chapters-20-24-17-eoittj`), **22, 33, 15** (rama
`nomenclador-nacional-barrido-gjii29`), **06, 09, 14, 16, 19, 32** y **35, 36, 38** (misma
rama, después de fusionar) — ver la tabla de avance más arriba.

⚠️ **Las páginas 84 a 87 no son de ningún capítulo**, y el índice ahora lo dice (`_huecos`). El
13 termina en la 83 y el 14 arranca en la 88, así que el salto parece un capítulo perdido y no
lo es: la 84 es la portada «PROGRAMA MEDICO OBLIGATORIO DEFINITIVO», la 85 está en blanco, y la
86 y la 87 son el **detalle de los coseguros** de los capítulos 14 al 44, odontológicos y
bioquímicos (Resolución 58/2017-MS). Verificado a ojo el 16/8/2026. El capítulo 13 está completo
con sus tres páginas: 30 códigos, 20 con recuadro y 10 sin él.

#### ✅ El 23 (hematología-inmunología) queda AFUERA — resuelto el 16/8/2026

Estuvo meses como «esperando decisión clínica porque se superpone con el NBU bajo otra
numeración». **No hacía falta la decisión clínica: el original ya lo resuelve.** Arriba del
encabezado del capítulo, al pie de la página 102, hay un recuadro impreso que dice:

> Capítulo del Nom.Nac. retirado por el PMO. **A excepción del 23.02.34**

El capítulo entero —`23.01.01` al `23.02.32`, unos 150 códigos de hematología e inmunología,
páginas 102 (pie) a 109— está **fuera del catálogo obligatorio**, y por eso no tiene ni una
ficha en la base. Todos sus códigos vienen en bastardilla, que es la marca de retirado. No se
transcribe: el usuario lo decidió el 16/8/2026 y el motivo es el de arriba, no el cruce con el
NBU. **Tampoco es el de hemoterapia** —ese es el 24, ya hecho—.

✅ **La excepción sí entró: el `23.02.34`.** Estaba en negrita, marcado «CODIGO AGREGADO POR EL
P.M.O.», con sus indicaciones impresas y coseguro hasta 250 — un código **del catálogo
obligatorio que el manual no tenía**. Se agregó el 16/8/2026 por decisión del usuario. Es la
única ficha del capítulo 23 en la base, y no es lo mismo que los trasplantes del `24.12.02`
(autólogo) y `24.12.03` (alogeneico), que ya estaban y son otros dos códigos.

Entró por `importar_capitulos_nn.py` —un capítulo `"23"` **sin** `retirado_pmo`, porque lo único
que entra a la base es lo que sí está en el catálogo—, con:

- `cobertura` → obligación de cobertura con las indicaciones impresas: aplasia medular
  idiopática o adquirida no secundaria a invasión neoplásica; tumores hemáticos (linfomas,
  leucemias); mieloma múltiple; otros con aval de la Sociedad Argentina de Hematología.
- `sinonimos` → el original imprime «**TRANS**PLANTE DE MEDULA OSEA» con N. La ficha lleva la
  ortografía correcta y la impresa entra al índice de búsqueda, así que se encuentra escrito de
  las dos maneras. Verificado: buscando «transplante» aparece.

#### ⚠️ `aviso_nomenclador`: el aviso de «esto no es del nomenclador que buscabas»

Es el campo nuevo que pidió el usuario y **el motivo por el que este código se podía agregar sin
riesgo**. Lo declara el capítulo en `data/capitulos_nn.json` y la app lo muestra en **dos**
lugares:

- **en el resultado del listado** (`.rcruce`, ámbar como el aviso administrativo), porque
  enterarse al abrir la ficha llega tarde: quien busca «médula ósea» ve siete resultados, tres
  de ellos trasplantes de médula de dos capítulos distintos;
- **en la ficha, pegado al nombre y antes de las acciones** (`.cruce-card`), porque no es una
  excepción de la práctica sino parte de lo que el código ES.

El texto: *es el capítulo 23 del Nomenclador Nacional —hematología e inmunología—, que el P.M.O.
retiró entero salvo esta práctica; no se cruza con el NBU ni con el Único, que tienen su propia
numeración de laboratorio y son prácticas distintas, no otro número de ésta*.

⚠️ **El cruce automático no existe, y conviene saber por qué**: todas las equivalencias del
manual son **curadas** —la planilla del Único y las listas revisadas a mano de
`equivalencias_por_nombre.py`—, ninguna se ata por parecido de nombre. El riesgo no era que la
base cruzara sola: era que lo cruzara **la persona que carga**. Por eso el aviso es visible y no
un renglón de auditoría.

Si alguna vez entra otra cosa del 23, va con el mismo `aviso_nomenclador`.

### 3.9 ⚠️ 36 fichas tenían la etiqueta del recuadro METIDA EN EL NOMBRE

`scripts/nombres_rotos.py` + `data/nombres_rotos.json`. Apareció transcribiendo el capítulo 08.
En los renglones donde el P.M.O. retiró **el título entero** de la práctica, el texto retirado
arranca la línea, y el OCR con el que se armó la base se comió la etiqueta como si fuera parte
del nombre:

    080210  «TextotetradoporelPMO»                    ← el nombre es SÓLO la basura
    121931  «Texto retfirado porel PMO Pasta de Unna»
    120202  «PMOEsternon,escapufa,humero,(excepto supracondilea) cubito yfo radio…»

⚠️ **Esto NO contradice la regla de no tocar nombres.** Esa regla existe para respetar la
redacción de cada nomenclador; lo guardado acá no es la redacción de ninguno. `080210` es el
caso extremo: quien busca «laparoscopía» no encuentra la ficha porque la palabra no está.
**Autorizado explícitamente por el usuario** («Sí, corregilos con el PDF»).

⚠️ **Cómo se detectan**: `pmo` dentro del nombre normalizado **sin espacios ni acentos**. Es la
señal correcta —esa sigla no aparece en el nombre de ninguna práctica—. Un patrón con espacios
(`texto retirado por el pmo`) encuentra sólo 9 de las 36: se pierde todas las que quedaron
pegadas a la palabra siguiente (`PMOMano de yeso`).

⚠️ **Falsos positivos que hay que dejar en paz**: `668387` (PLASMINÓGENO… `(PAI - AIP)
(Molecular)` → contiene «pmo» al normalizar) y los `U10…` del Único, que dicen «NO PMO» a
propósito.

⚠️ El nombre viejo **no se tira**: queda en la auditoría de la ficha, con la página del PDF.

**Estado: ✅ CERRADO — los 36 corregidos, quedan 0.** El script sigue sirviendo como control:
si un reimporte volviera a meter la etiqueta en un nombre, lo lista al terminar. Se
corrigen solos a medida que el barrido llegue a esas páginas — el script los lista al terminar.

⚠️ **El OCR cruzaba de renglón, así que el nombre roto arrastra texto del código vecino.**
Pasó dos veces y las dos habrían metido un dato equivocado si se copiaba tal cual:
- `070708` empezaba con «Y Codigo 34.08.11», que es el remate del `07.07.07`. Al `07.07.08` le
  corresponde el **34.08.07**.
- `070205` terminaba en «CIERREDEFECTOSSEPTALES», que es el título del `07.02.06`.

Al transcribir un nombre roto, **leer el renglón entero en el PDF**, no confiar en la parte
legible de lo que hay guardado.

### 4.5 nonies La sigla `NN` — norma del Nacional que el P.M.O. retiró

El Nomenclador Nacional trae, al lado de cada práctica, un recuadro que el Catálogo del
P.M.O. **no reproduce**: qué abarca el código, qué incluye, cómo se factura. El manual sí lo
conserva, pero hasta ahora había que abrir la ficha para enterarse de que existía.

Ahora lleva sigla propia en el listado: **`NN`**, contorneada y no rellena —no es un estado
de la práctica como «urgencia» o «desuso», es un aviso de que hay algo más para leer—.
La decide `normaNN(c)`, que mira los **dos caminos por los que ese texto entró a la base**:

| origen | dónde se guarda | se lee en la ficha |
|---|---|---|
| recuadro «Texto retirado por el P.M.O.» | `c.alcance_nn.texto` | sección **«Qué abarca este código»** |
| norma de capítulo, cargada por los importadores | líneas de `c.auditoria` que empiezan con `Alcance del Nomenclador Nacional:` o `Norma del código:` | bloque propio **`.nn-card`** |

⚠️ **No es lo mismo que la sigla `N`** (`flags.requiere_norma`). Aquélla dice que *hace falta*
una norma para autorizar; ésta dice que *hay* una norma escrita y el manual la tiene.

⚠️ **El `title` de la sigla cambia según el caso**, y tiene que seguir cambiando: donde hay
norma escrita manda a abrir la ficha, y donde sólo hay alcance manda a «Qué abarca este
código». Prometer un bloque que no existe sería peor que no poner la sigla —fue exactamente
el error que tenía la primera versión, con 100 de los 156 códigos mandando a la nada—.

Hoy: **785 códigos con sigla**, de los cuales **428 abren el `.nn-card`** y **357 traen sólo
alcance**. Sobre 6.478, no ensucia el listado. ⚠️ Este número **sube con cada capítulo que se
transcribe** (3.8): eran 156 cuando se escribió esta sección, con 56 abriendo el `.nn-card`.
Si no coincide, no está roto: está desactualizado el renglón. Se recalcula así —

    python3 -c "import json,re; db=json.load(open('data/nbu_db.json'))['codigos']; \
    R=re.compile(r'^(Alcance del Nomenclador Nacional|Norma del código):'); \
    f=[v for v in db.values() if (v.get('alcance_nn') or {}).get('texto') \
       or any(R.match(a) for a in (v.get('auditoria') or []))]; \
    print(len(f), sum(1 for v in f if any(R.match(a) for a in (v.get('auditoria') or []))))"

### 4.5 decies Las equivalencias que habían quedado colgando

`scripts/reparar_equivalencias.py`. El Único ya declaraba, para cada práctica, el código
equivalente del P.M.O. — pero cuando se armó la base **esos códigos todavía no existían**
(capítulos enteros que faltaban), así que la equivalencia se guardó con
`destino_inexistente: true` y sin `key`: la ficha del Único decía «no está cargada como ficha
propia todavía» y la del P.M.O. no mostraba nada. Era el caso de las espirometrías.

Al importar los capítulos, esos destinos aparecieron. El script recorre las colgadas y donde
el destino ya está: completa `key`/`desc` y saca la marca del lado Único, y agrega el
`equivalencia_unico` recíproco del lado P.M.O./NBU.

**No inventa equivalencias**: sólo usa las que la planilla del Único ya declaraba.

Resultado: **60 reatadas · 8 ya tenían el enlace de vuelta · 134 siguen sin destino en la
base** (eran 153 cuando se escribió esto; el número baja con cada capítulo importado). Esas
134 apuntan a códigos de capítulos todavía no importados, así que **algunas fichas siguen sin
la vista previa entre nomencladores** — se arreglan solas a medida que entren los capítulos
que faltan, volviendo a correr el script.

⚠️ **No arregla las que declaran un número EQUIVOCADO**, sólo las que declaran uno que todavía
no existía. Si el número está mal, este script lo deja colgado para siempre y el caso va a
4.5 undecies. Pasó con el `U210208`: apuntaba al `220209`, que no existe, mientras la práctica
entraba a la base como `210208`.

⚠️ Correr siempre `python3 scripts/inject_db.py` después.

⚠️ **U.B. vacía no es un error en estos capítulos.** Neumonología, consultas y sanatoriales
se facturan en unidades de honorarios y gastos, no en Unidad Bioquímica: se importaron con
`valor.ub = null` a propósito, y `ubDe()` devuelve `null`. La tarjeta de equivalencia se ve
igual, sin el chip de U.B.

### 4.5 undecies Seis equivalencias que el Único numeraba distinto

`scripts/equivalencias_renumeradas.py`. En seis prácticas la planilla del Único dice
«equivale al código NNNNNN», ese número no existe en el Nomenclador Nacional, **y la
práctica sí está en el Nacional con el mismo número que usa el Único**:

| Único | la planilla decía | está en el Nacional como |
|---|---|---|
| 280111 Capacidad pulmonar total y volumen residual | 280207 ✗ | **280111** |
| 280201 Lavado alveolar | 280208 ✗ | **280201** |
| 280301 Ablación de lesiones broncopulmonares | 280209 ✗ | **280301** |
| 260528 Perfusión sanguínea miocárdica | 260729 ✗ | **260528** |
| 430601 Luminoterapia | 431604 ✗ | **430601** |
| 210208 Genotipificación hepatitis C en HIV positivos | 220209 ✗ | **210208** |

El sexto entró el 18/8/2026, cuando el `210208` se sumó a la base (3.8). Es el más claro de
los seis: los dos lados se llaman **igual palabra por palabra**, y el número declarado no
sólo no existe —el capítulo 22 es ginecología y obstetricia, donde una genotipificación no
puede caer—. Es una transposición del 21 por el 22 en la planilla.

⚠️ **NO se hace por regla automática «si el número coincide, atalo».** `U430102` coincide en
número y la práctica es otra: el Único dice «cama en habitación individual (aislamiento)» y
el Nacional dice «una cama en habitación de dos con baño». Atarla habría metido un error de
facturación. La lista del script está escrita a mano, código por código, comparando el
nombre de los dos lados.

El número que declaraba la planilla queda guardado en `equivalencia.code_declarado` y en una
línea de auditoría de las dos fichas: un auditor que compare contra el papel se va a
encontrar con ese número y tiene que poder explicárselo.

⚠️ **El script no era idempotente y correrlo dos veces borraba justamente ese número.**
Guardaba `code_declarado = e["code"]` por asignación, pero en la segunda corrida `e["code"]`
ya era el destino corregido, así que los cinco `code_declarado` se pisaron con el número bueno
y el de la planilla se perdió. Pasó el 18/8/2026 al agregar el sexto par, y se vio comparando
contra `git show HEAD:data/nbu_db.json`. Arreglado con `setdefault` —que es como el mismo
script ya trataba `desc_declarada`— y la base se rehízo desde el commit anterior en vez de
parchear el JSON. **La regla general**: estos scripts corren sobre `data/nbu_db.json`, que es
un archivo versionado que se pisa a sí mismo, así que el que reescribe un campo tiene que
poder correr dos veces. Cuando un script de datos toca algo que ya tocó, conviene mirar el
diff contra `HEAD` antes de commitear — no alcanza con que el script no falle.

### 4.5 duodecies ⚠️ El Único repite las prácticas de laboratorio en varios bloques

`scripts/equivalencias_por_nombre.py`. Al buscar por **nombre** las equivalencias que
declaraban un número inexistente apareció el motivo de fondo: el Nomenclador Único lista el
laboratorio **varias veces**, en bloques con prefijo 60, 61, 62, 63 y 64 (1.108 filas sólo el
64). La misma práctica aparece en dos bloques —una con el número correcto del NBU y otra con
un número que no existe— y los nombres difieren sólo en acentos o puntuación:

    64662384 «ÁCIDOS ORGÁNICOS»  → 662384  ✓ atada
    64662389 «ACIDOS ORGANICOS»  → 662389  ✗ ese número no existe

⚠️ **Eso NO es una práctica que falte: es la misma fila repetida.** Se ata igual (quien mire
esa ficha tiene que llegar al 662384 y no leer «no está cargada todavía») pero **sin agregar
el reflejo** en la ficha del NBU — ésa ya muestra la fila canónica, y sumarle una segunda
casi idéntica haría creer que hay dos códigos facturables. Es el tercer campo de `PARES`.

⚠️ **Hay un error PREEXISTENTE en Chagas que no se tocó**, porque corregirlo es decisión de
los médicos: la fila `63663576` del Único se llama «CHAGAS, Ac. Totales Anti- (ELISA)» y está
atada al NBU `663576`, que es «CHAGAS, (PCR)». El ELISA del NBU es el `663580` y ya lo reclama
—bien— la fila `64663580`. Se generó por identidad de número en `assemble.py`. Al atar la
fila `64663581` «CHAGAS (PCR)» al `663576` que le corresponde, la ficha del NBU ahora muestra
las dos y el error queda a la vista.

**Quedaron afuera** por ambigüedad real: HIDATIDOSIS (IFI) —el mismo nombre en `660484` y
`661100`, los dos ya tomados por látex y arco 5, y la del Único es una tercera técnica—,
DOMICILIO «Más de 2 Kms» contra «Hasta 2 Kms», y BCR/ABL «LMC» contra «LLA».

Total: **13 atadas** (10 repetidas sin reflejo, Chagas PCR, y las dos evaluaciones
pretrasplante renal que el Único marca SURGE y el Nacional tiene lisas y llanas).

#### Los nombres NO se tocan, y hay una prueba que lo garantiza

⚠️ Regla del usuario: **los nombres de las fichas se mantienen tal cual los trae cada
nomenclador.** El script termina comparando los 6.476 nombres contra los de antes de correr y
aborta con `SystemExit` si alguno se movió. Cualquier script que toque equivalencias debería
copiar ese cierre.

Reparto de campos en `equivalencia`, para no volver a confundirlos:

| campo | qué es | quién lo usa |
|---|---|---|
| `desc` | el nombre que tiene el **destino**, sin retocar | la línea bajo «Equivale a NNNNNN» |
| `desc_declarada` | cómo llamaba **la planilla del Único** a esa práctica | el aviso ⚠, y sólo si difiere de `desc` |
| `code_declarado` | el número que traía la planilla y no existe | el aviso ⚠ |
| `recalculada` | `"codigo"` o `"nombre"` — cómo se reconstruyó | dispara el aviso ⚠ |

`reparar_equivalencias.py` había pisado 65 `desc` con el nombre del destino, perdiendo la
redacción de la planilla. Se recuperaron desde el commit `e3c9036` a `desc_declarada` (51
tenían texto; el resto venían vacías). La ficha las muestra dentro del aviso: «La planilla la
llamaba: «PERFUSION CARDIACA CON RADIOISOTOPICA»» al lado de «Perfusión sanguínea miocárdica
con radioisótopos» — la diferencia de redacción es justamente lo que el médico mira para
decidir si la equivalencia se sostiene.

Las 5 de `equivalencias_renumeradas.py` pasaron de una marca propia (`renumerado`) a
`recalculada: "codigo"`, que es la que la ficha ya sabía mostrar.

### 4.5 terdecies `aviso_nomenclador` — «esto no es del nomenclador que buscabas»

Nació con el `23.02.34` y está pensado para durar más que ese caso. Hay códigos que se
buscan **con el mismo nombre** que una práctica de otro nomenclador y que NO son esa
práctica: quien busca «médula ósea» ve siete resultados y tres son trasplantes de médula de
dos capítulos distintos. El badge de la sección no alcanza para eso.

Lo declara el **capítulo** en `data/capitulos_nn.json` y el importador lo copia a cada ficha:

```json
"aviso_nomenclador": { "sigla": "cap. 23 · Nom. Nacional", "texto": "…" }
```

Se muestra en **dos** lugares, y las dos veces a propósito:

| dónde | clase | por qué |
|---|---|---|
| resultado del listado | `.rcruce` | enterarse al abrir la ficha llega tarde: para entonces ya copió el código |
| ficha, pegado al nombre y **antes** de las acciones | `.cruce-card` | no es una excepción de la práctica, es parte de lo que el código **ES** |

Ámbar los dos, que es el color del aviso administrativo —el que se lee antes de cargar—, y
no el cobre de la norma ni el verde de la revisión médica.

⚠️ **El cruce automático no existe**: todas las equivalencias del manual son curadas (la
planilla del Único, las listas revisadas a mano de `equivalencias_por_nombre.py`) y ninguna
se ata por parecido de nombre. El riesgo nunca fue que la base cruzara sola — es que lo
cruce **la persona que carga**. Por eso el aviso es visible y no un renglón de auditoría.

Hoy lo lleva **una sola ficha**. Si alguna vez entra otra cosa del capítulo 23, va con el
mismo campo (3.8).

### 3.6 ⚠️ Capítulos 40, 41, 42, 43 y 44: FALTABAN ENTEROS

Se descubrió buscando el capítulo 42 a pedido del usuario. **El 42 es CONSULTAS MÉDICAS**
—consultorio, domicilio diurna/nocturna/emergencia, mayores de 65, atención en internación—
y **no había ni un código** en el manual: la única consulta que existía era la odontológica.
El **43** (prestaciones sanatoriales y de enfermería) tenía **1 de ~25**.

Importados con `scripts/importar_capitulos_nn.py` desde `data/capitulos_nn.json`, transcripto a
mano del PDF (páginas 145-150) por el mismo motivo que el capítulo 34: el OCR de esas páginas
es igual de malo y acá hay **aranceles y coseguros**. **41 fichas nuevas.**

Dos decisiones del importador, las dos para no inventar:
- **`valor.ub` queda en `null`.** Estos capítulos se arancelan por «unidades de honorarios y
  gastos», que NO es la Unidad Bioquímica. Cargarlos como U.B. haría que la app los
  multiplicara por el valor de U.B. y mostrara un arancel inventado. Los números van en el
  texto de `arancel`.
- **`requiere_norma` en `false`.** La app muestra ese flag como «AUTORIZACIÓN: previa ·
  requiere norma», y lo que estos capítulos traen son normas de **facturación** (cuándo se
  factura el día de ingreso, qué incluye la cama), no un requisito de autorización. Van a
  `auditoria`, que es donde se leen como lo que son.

**También se importaron el 40 y el 41** (terapia intensiva, internación por 24 horas) y el
**44** (unidad coronaria móvil). **47 fichas en total.**

⚠️ **El 44 lo marca el propio original: «Capítulo del Nom.Nac. retirado por el PMO».** Existe
en el Nacional pero quedó fuera del catálogo obligatorio, así que va con `en_catalogo_pmo:
false` y un aviso en auditoría. La ficha no puede decir que es de cobertura obligatoria.

⚠️ **Error propio, encontrado al releer:** en el capítulo 43 los valores están en la columna
**Gastos** (marcador `up`/`og`), no en Honorarios — son prestaciones sanatoriales, no acto
médico. Se habían cargado como honorarios y se corrigieron. En el 42 sí son honorarios, y en
el 40 hay de las dos.

El importador (`scripts/importar_capitulos_nn.py` + `data/capitulos_nn.json`) quedó
**general**: para sumar otro capítulo alcanza con agregarlo al JSON.

Lo que entiende cada código del JSON, después de la tanda del 16/8/2026:

| clave | qué hace |
|---|---|
| `nombre`, `grupo`, `alcance` | lo básico de la ficha; `alcance` va además a «Qué abarca» |
| `honorarios`, `gastos`, `total`, `coseguro` | arman el texto de `valor.arancel`. Si no hay ninguno, queda la frase de que el arancel sale del convenio |
| `agregado_pmo` | escribe «Código agregado por el P.M.O.» en auditoría |
| `cobertura` (+ `cobertura_tipo`) | **nuevo**: la obligación de cobertura, que la app ya sabía mostrar —cartel en la ficha, etiqueta en el listado— y hasta ahora no se podía cargar desde acá |
| `sinonimos` | **nuevo**: entran al índice de búsqueda. Sirven para la ortografía del original cuando la ficha lleva la corriente (el `23.02.34` está impreso «TRANSPLANTE») |

Y a nivel capítulo: `titulo`, `norma`, `normas_sueltas`, `retirado_pmo` y **`aviso_nomenclador`**
(nuevo, ver 4.5 terdecies), que se copia a todas las fichas del capítulo.

**Después se importaron el 27, el 28 y el 26** — 57 fichas más. Total del rescate: **104**.
Más tarde entraron por el mismo camino dos códigos sueltos de capítulos que **ya estaban** en
la base: el `23.02.34` (16/8) y el `21.02.08` (18/8), los dos «AGREGADO POR EL P.M.O.» y los
dos descubiertos mientras se transcribían los recuadros de 3.8. **Total: 106.** El JSON no
distingue entre «capítulo que falta entero» y «un código suelto»: se agrega el capítulo con
la lista de códigos que haya, y los que ya están se completan sin pisarse.

⚠️ **Del capítulo 26 se importaron 38 de los 78 que faltaban, a propósito.** El sub-capítulo
**26.03 (determinaciones por radioinmunoensayo, 38 códigos) NO se importó**: el propio
nomenclador lo dice arriba del bloque — «estas determinaciones se efectuan por laboratorio por
lo tanto su valor se establece en el Nomenclador Bioquimico», y ese nomenclador **es el NBU
que la base ya trae**. Se verificó: ACTH, aldosterona, cortisol, prolactina, insulina,
testosterona y tiroxina ya están como códigos `66xxxx`. Importarlo habría duplicado la misma
práctica con dos códigos distintos.

### 3.7 El contraste y el material radioactivo: dos modelos distintos

Pregunta del usuario, respondida contra el PDF. **No hay un código aparte para el contraste**,
pero el nomenclador lo trata de dos maneras según el estudio:

- **TAC y RMN** → el contraste está **dentro del código**. `341001` es la TAC cerebral y
  `341002` la «reforzada», que la norma define como «con inyeccion de substancia de contraste»;
  `342001` es la RMN cerebral y `342002` la «con gadolinio». Se factura el código con
  contraste, no el estudio más el contraste.
- **Medicina nuclear / cámara gamma** → el material **NO está incluido**. Norma del capítulo 26,
  impresa arriba del bloque: «El costo del material radioactivo, en todos los casos en que no
  este aclarado, no se halla incluido en el honorario y se fijara de acuerdo con la lista de
  precios oficiales que rige en la Comision Nacional de Energia Atomica».

⚠️ Esa norma **no estaba en ninguna de las 110 fichas del capítulo 26** —ni en las 37 que ya
existían ni en las 38 recién importadas— y es lo que decide cuánto se cobra. Se agregó a las
110, **primera en la lista de auditoría**.

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

### 4.6 bis ⚠️ El «glitch» al actualizar: el cartel que nunca se veía

Síntoma que reportó el usuario: al publicarse una versión nueva, «aparece el cartel de
actualizando por un microsegundo, se reconecta y vuelve a aparecer el cartel».

Medido con Playwright, filmando el DOM en cada `requestAnimationFrame` y guardando el
registro en `sessionStorage` para que sobreviva a la recarga (`swfilm.mjs`). Lo que pasaba:

```
+ 36ms  pantalla de carga «Cargando base…»        274 ms
+310ms  app visible                               311 ms
+621ms  CARTEL «Actualizando el manual»             3 ms   ← nunca se vio
+621ms  se va la página
+652ms  pantalla de carga «Cargando base…»        282 ms
```

⚠️ **El cartel entra con `opacity:0` y `transition:.18s`**, y el camino del mensaje llamaba a
`location.reload()` en la línea siguiente: el elemento existía 3 ms y moría antes del primer
frame visible. El usuario nunca veía la explicación — sólo dos pantallas «Cargando base…»
idénticas con un parpadeo en el medio, que se lee como una falla.

⚠️ **Por qué justo ese camino.** Hay dos vías de actualización y sólo una tenía la espera:

| vía | cuándo salta | tenía espera |
|---|---|---|
| `controllerchange` | cuando cambia **`sw.js`** | sí, 450 ms |
| mensaje `nueva-version` | cuando cambia **`index.html`** | **no** |

Y `sw.js` **no cambia nunca al publicar** (su `VERSION` es una constante que no se toca), así
que la vía que corre en cada publicación era justamente la que no esperaba.

Arreglado con una sola función `recargar()` por la que pasan las dos, con `ESPERA=600`. No
dupliques el `setTimeout` en cada handler: fue exactamente así como una de las dos se quedó
sin él.

**Y la segunda pantalla ahora continúa a la primera.** `actualizando()` deja
`sessionStorage['nbu-actualizando']`, y un script inline **junto al `#boot`** (no en el script
grande: ése tarda en parsearse y para entonces ya se vio «Cargando base…») cambia el texto a
«Actualizando el manual…». La marca se borra al leerla, así que vale una sola vez. Resultado:

```
+635ms  CARTEL «Actualizando el manual»          602 ms
+1265ms pantalla de carga «Actualizando el manual…»  283 ms
```

⚠️ El script nuevo hace que `sellar_csp.py` selle **3** huellas en vez de 2. Es esperado.

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
    ⚠️ **El síntoma no dice «CSP»**: la página carga, el cartel de arranque no se va nunca y
    cualquier test de Playwright muere en el `waitForFunction` del `#boot` a los 30 s, como si
    fuera lento. Si un cambio de `index.html` deja todo colgado ahí, es esto: sellar y volver
    a correr. Pasó el 16/8/2026 y costó un ciclo de depuración.
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

## 7. Historial de trabajo

**Lo hecho en la tanda del 2026-08-18** (rama `claude/nomenclador-chapters-30-29-21-0c4v9o`),
toda sobre el barrido de 3.8:

- **Capítulos 30, 29 y 21** (oftalmología, neurología, genética humana): 46 códigos, **22
  textos**. El 30 aporta 14 —casi todos la lateralidad que el PMO borró del renglón— y una
  norma que va al `30.01.22` y no al sub-capítulo. El 21 aporta 8. El **29 no aporta
  ninguno**, y quedó declarado igual con `codigos` vacío: «leído y no aporta nada» y «todavía
  no se leyó» tienen que poder distinguirse, o el capítulo vuelve a la lista de pendientes.
- **Regla nueva en 3.8: el índice de páginas da la página con MÁS códigos, no el capítulo
  entero.** Los tres se derramaron en la siguiente, y en el 21 eso eran **tres de los ocho
  recuadros**, arriba de una página que el índice le asigna al 22. Ningún script lo habría
  avisado. La receta ahora incluye mirar la página siguiente a la última.
- **`docs/inventario_faltantes.json` como control previo**: dice de antemano qué códigos del
  PDF no van a tener ficha donde caer. Los siete retirados del 30, el `29.01.01` y el
  `21.02.08` coincidieron uno a uno con lo leído a ojo.
- **El `21.02.08` entró a la base** por `importar_capitulos_nn.py` (3.6 y 3.8) — agregado por
  el P.M.O., del catálogo obligatorio, y faltaba. Con él se ató la equivalencia del Único que
  declaraba el `220209`, un número que no existe (4.5 undecies).
- ⚠️ **Un error propio, encontrado al releer el diff**: `equivalencias_renumeradas.py` no era
  idempotente y la segunda corrida **borró los cinco `code_declarado`** —el número que
  declaraba la planilla, que es justamente lo que hay que poder mostrarle a un auditor—.
  Arreglado con `setdefault`, y la base se rehízo desde el commit anterior en vez de
  parchear el JSON. El detalle y la regla que deja, en 4.5 undecies.

**Lo hecho en la tanda del 2026-08-16** (rama `claude/nomenclador-chapters-20-24-17-eoittj`),
toda sobre el barrido de 3.8 salvo lo último:

- **Capítulos 20, 24 y 17** (gastroenterología, hemoterapia, cardiología): 31 textos y las
  normas de cada uno con su alcance decidido código por código. De ahí salieron tres reglas
  nuevas en 3.8: que estar impresa en el encabezado del capítulo **no** la hace norma de
  capítulo, que una norma puede quedar declarada **sin destino**, y que un texto de dos
  palabras no es una transcripción cortada.
- **Capítulo 18** (ecografía): el bloque NORMAS del encabezado está en **dos columnas** al
  pie de la 94 y son diez líneas que van a las 22 fichas — informe al paciente, tonos de
  grises, y que no se le puede sumar el valor de una consulta.
- **Capítulo 31** (otorrinolaringología): 3 textos y la norma de los estudios endoscópicos
  faringolaríngeos, que incluye biopsia, drenajes y lavados dentro del mismo arancel.
- **Capítulo 23 resuelto sin transcribirlo**: el original lo marca retirado entero salvo el
  `23.02.34`, que sí entró — y con él el campo **`aviso_nomenclador`** (4.5 terdecies), que
  avisa en el listado y en la ficha que ese código es del Nacional y no se cruza con el NBU
  ni con el Único.
- **Dos huecos del índice de páginas cerrados**: las 84 a 87 no son un capítulo (portada,
  blanco y el detalle de coseguros de la Res. 58/2017-MS) y el capítulo 32 arranca al pie
  de la 129, donde el OCR no lo había visto.

**Lo hecho en la tanda del 2026-08-10 y 11** — el detalle está en los mensajes de
cada commit, que explican el porqué y no sólo el qué:

- El **Único hereda todo lo que muestra el NBU** (3.0): siglas, sinónimos, tipo de muestra,
  sección de origen. 1.694 fichas.
- **Logo sobre blanco en tema oscuro**, con el rectángulo del ancho de los campos en la
  pantalla de ingreso.
- **Respaldo**: «Restaurar» no restauraba nada con la nube encendida; ahora escribe en la
  base mostrando antes qué cambiaría, y avisa si hace más de 30 días que nadie baja copia
  (ver 4.7 — el plan de Supabase es el gratuito y **no hay respaldos automáticos**).
- **La base viaja aparte** del `index.html` (3.0 bis).
- **Pasar una ficha o un caso a un compañero**, y **compartir la nota propia** con el equipo.
- **«Qué pasó desde la última vez»**, **propuestas visibles marcadas «sin confirmar»** y
  **registro del equipo** (4.8).
- **Capítulo 34 del PMO**: denominaciones, altas y alcance (3.4).
- **Cartel «Actualizando el manual»**: antes se reiniciaba sola y sin decir nada.
- **La observación llega a todos los códigos equivalentes** (4.6), no sólo al gemelo del NBU.

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

## 7 bis. ▶ AGENDA DE LA PRÓXIMA SESIÓN (escrita el 18/8/2026)

### A. ✅ Barrido del Nomenclador Nacional — terminado de punta a punta (19/8/2026)

⚠️ **El 18/8 hubo cuatro sesiones**: tres hicieron el barrido capítulo por capítulo (dos en
paralelo, ramas separadas y fusionadas después a mano, más una tercera encima ya sobre la
rama fusionada — **20, 24, 17, 18, 31, 30, 29, 21** / **22, 33, 15** / **06, 09, 14, 16, 19,
32, 35, 36, 38**, los 32 capítulos con página conocida) y una cuarta arrancó el **66**. Moraleja
para la próxima vez que haya sesiones simultáneas: **avisar qué capítulos toma cada una**, así
no se pisan ni hace falta reconciliar ramas divergentes.

**Los 32 capítulos del catálogo PMO están hechos (844/1.353, 62%), y el capítulo 66 (análisis
clínicos, 36 páginas, 168-203) se completó el 19/8/2026** con 134 códigos de texto sumados a
fichas del **NBU** existentes (no al PMO — ver 3.8, «Capítulo 66», para el detalle del criterio
usado y los choques de nombre encontrados). No queda barrido pendiente.

**Lo que sí queda, para quien tenga tiempo y ganas de revisar a mano** (no urgente, la app
funciona igual sin esto): los casos «dudoso» que se fueron dejando sin declarar en cada
`_nota_pagina_*` de `data/alcance_nn_pmo.json` bajo `"66"` — nombre o método parecido al de la
ficha de la base, pero no lo bastante como para declararlo sin mirar el PDF impreso de nuevo.
Son pocos por página, no hace falta un barrido sistemático — alguien con el nomenclador
impreso a mano podría resolverlos en una sentada.

⚠️ Si en algún futuro barrido similar aparece un código impreso «AGREGADO POR EL P.M.O.» que
**no está en la base**, no lo crea `alcance_nn_pmo.py`: se anota y va por
`importar_capitulos_nn.py`, como el `21.02.08` y el `23.02.34`. Y si el Único ya lo traía,
revisar la equivalencia — puede estar colgada de un número equivocado (4.5 undecies).

### B. Ciberseguridad — repaso pedido por el usuario

Lo que YA está bien y no hay que tocar:
- CSP sin `unsafe-inline` en scripts (huellas sha256), `connect-src` limitado al proyecto de
  Supabase, `form-action 'none'`, `base-uri 'none'`, `object-src 'none'`.
- Los cuatro roles se hacen cumplir con RLS + triggers, no con la interfaz. Verificado
  llamando la API directo: 8/8 bloqueados con 403 (`roles_limite.mjs`).

⚠️ **Lo crucial, por orden de riesgo real:**

1. **RESPALDOS. El plan de Supabase es gratuito y NO tiene respaldos automáticos** (ver 4.7).
   No es un ataque: es la pérdida más probable y la más cara. Si el proyecto se borra o se
   corrompe, se va todo lo que escribieron los médicos. Es lo primero.
2. ✅ **XSS almacenado por texto que escriben los médicos — auditado el 25/8/2026, sin
   hallazgos.** Se revisaron a mano los tres caminos (revisión médica `rev.texto`,
   observaciones `o.texto`, «qué abarca» `alcance_nn`/`corr.texto`) más `asoc_extra`,
   `auditoria`, `norma.interpretacion`, `observacion_unico`, notas personales, nombres de
   usuario (`por`/`quien`/`autor`) y `c.nombre` editable desde ✎ Editar ficha — en total
   los ~90 usos de `innerHTML` que interpolan datos, uno por uno. El orden `linkCodes(esc(t))`
   es correcto en **todos** los casos: `esc()` corre primero y `linkCodes()` sólo agrega
   `<span data-goto>` alrededor de secuencias `\d{6}` que ya quedaron escapadas, así que no
   hay forma de que el HTML que agrega linkCodes lo controle el texto de origen. `hlList()`
   (resaltado de búsqueda) también escapa antes de marcar. El logo (`logoInner()`) sigue
   protegido por `LOGO_OK` + `E()`. No se encontró ningún camino sin escapar.
3. ✅ **Segundo factor (TOTP) para el administrador general — construido el 25/8/2026.**
   Autoservicio desde **Tu cuenta → Verificación en dos pasos** (sólo visible para
   `rol==='admin'`, y sólo en modo nube): activarlo pide escanear un QR o cargar el
   secreto a mano en una app de autenticación (Google Authenticator, Authy…) y confirmar
   con un código de 6 dígitos. A partir de ahí, `continuarLogin()` (`web/index.html`)
   frena el login con contraseña de esa cuenta y pide el código antes de dejar entrar —
   tanto al loguearse a mano como al reanudar sesión solo al abrir la app (los dos
   caminos usan la misma función, para que no queden desincronizados). Sigue el flujo
   estándar de Supabase Auth: `POST /auth/v1/factors` (alta), `.../challenge` +
   `.../verify` (confirmar o loguear — verify además eleva la sesión a `aal2`, que se
   guarda en `ses.aal` porque el token que devuelve el login no es un JWT que se pueda
   inspeccionar acá), `DELETE /auth/v1/factors/:id` (desactivar).
   ⚠️ **Dos decisiones a propósito, documentadas para no "corregirlas" después:**
   - **No se fuerza la activación.** El único administrador podría quedar afuera de su
     propia cuenta por un problema al activarlo; queda ofrecido, no obligatorio.
   - **Si falla la consulta de qué factores tiene la cuenta (sin red, la nube caída), se
     deja entrar igual** (`continuarLogin()` atrapa el error y sigue). Frenar al único
     administrador que hay por un problema de red es peor que el riesgo que esto cubre —
     no hay segundo administrador que pueda destrabarlo.
   - **No hay códigos de respaldo.** Si el administrador pierde el teléfono con la app,
     nadie puede sacarle el segundo paso desde la propia app (hace falta `aal2` para
     desenrolar un factor verificado, que es justo lo que no tiene). La única salida es
     el panel de Supabase (**Authentication → Users** → esa cuenta → borrar el factor a
     mano) — avisado en la propia pantalla de "activada". El usuario es también el dueño
     del proyecto de Supabase, así que puede hacerlo él mismo si hace falta.
   Probado en `tests/e2e/casos/mfa.mjs`: alta con código incorrecto y luego correcto,
   login con código incorrecto y luego correcto, desactivación, y que el candado **no**
   se le pide a otro rol aunque tenga un factor activado (`activarMFA()` en
   `simulador.mjs`, que también ganó `GET /auth/v1/user` y las rutas de `/factors`).

   ✅ **Ampliado el 25/8/2026: «confiar en este dispositivo», para no pedirlo en cada
   login.** El usuario lo pidió después de probarlo — con el candado a secas, entrar
   todos los días desde la misma computadora del administrador se volvía tedioso.
   `confiarDispositivo()`/`dispositivoConfiable()`/`olvidarDispositivo()` en
   `web/index.html`: guardan en `localStorage` (no en la base) un vencimiento a 30 días
   por cuenta (`nbu-mfa-confia:<uid>`). El dispositivo desde el que se activa la
   verificación queda confiado de una —ya probó tener la app de autenticación en la
   mano—; el checkbox del login («Confiar en este dispositivo…», tildado por
   default, se puede destildar) decide si CADA login la deja confiada; y desde
   **Tu cuenta → Verificación en dos pasos** se puede revocar la confianza de este
   dispositivo en particular sin esperar los 30 días ni desactivar todo.
   ⚠️ **Es una comodidad de la interfaz, no un límite que haga cumplir el servidor**:
   vive en el navegador de quien la activó. Quien tenga acceso a ESE navegador además
   de la contraseña, entra sin el código mientras dure — el mismo trato que cualquier
   «recordarme» de cualquier sistema con 2FA, no es un agujero nuevo de este.
   Probado (mismo archivo): un dispositivo que se activa queda confiado; «dejar de
   confiar» lo vuelve a pedir; el checkbox destildado no confía y tildado sí; y —caso
   aparte, con dos `BrowserContext` sobre la misma base— **un dispositivo distinto no
   hereda la confianza de otro**.
4. **`frame-ancestors` no se puede poner.** La directiva **se ignora en un `<meta>`**: sólo
   funciona como cabecera HTTP, y GitHub Pages no deja mandar cabeceras propias. Queda el
   clickjacking como hueco abierto. Salidas: poner Cloudflare adelante, o aceptarlo y
   documentarlo. **No perder tiempo agregándola al meta: no hace nada.**
5. **Protección de contraseñas filtradas** en Supabase (HaveIBeenPwned). El mínimo ya está en
   10 caracteres.
6. **`style-src 'unsafe-inline'`** sigue abierto a propósito (cientos de `style=`). Inyectar
   estilo es mucho menos grave que inyectar código; sacarlo pide reescribir media interfaz.
7. **Re-correr los 25 avisos del linter** después de las migraciones 02‑05. ⚠️ Ver 4.5 quater:
   seguir su receta al pie de la letra **rompe la app**.
8. ✅ **Cuánto dura la sesión — arreglado el 25/8/2026.** Ya existía `resetIdle()`
   (`web/index.html`, cerca de la línea 5580): 25 minutos sin `mousemove`/`keydown`/`click`/
   `touchstart` y vuelve a la pantalla de ingreso. **Pero era cosmético**: sólo borraba
   `current` en memoria y mostraba el gate — el token de Supabase seguía vivo en
   `localStorage` (`nbu-sesion`), y el arranque de la app (`init`, al final del archivo)
   **reintenta el login solo si encuentra sesión guardada**. Resultado real: en la máquina
   del mostrador, después de que saltara el cierre por inactividad, apretar F5 volvía a
   entrar sin pedir nada — el candado no candaba. Arreglado: ahora `resetIdle()` llama
   también a `NUBE.salir()` (revoca el token en el servidor y limpia `localStorage`), igual
   que hace el botón manual «Cerrar sesión». No hace falta segundo factor para que esto
   importe: es la fuga más simple de todas, la que no requiere ataque.

### C. Decisiones que esperan a los médicos
- **Chagas**: `63663576` (ELISA) está atado al NBU `663576`, que es el **PCR**. Error
  preexistente, no se tocó (4.5 duodecies).
- **Consultas A‑P** del Único (10 filas) — ¿todas a `420101`?
- **Hidatidosis IFI**, **domicilio «más/hasta 2 kms»**, **BCR/ABL LMC vs LLA** — no se ataron.
- ~~**Capítulo 23**: se superpone con el NBU bajo otra numeración.~~ **RESUELTO el 16/8/2026 y
  no hacía falta el médico**: el original lo marca retirado entero salvo el `23.02.34`, que se
  agregó. Ver 3.8. Tampoco era el de hemoterapia —ese es el 24, ya hecho—.

### D. Datos que siguen faltando
- ✅ **Capítulo 66 contra el PDF — terminado el 19/8/2026.** Ver 3.8 → «Capítulo 66» para el
  resumen y el criterio usado. Las 36 páginas (168-203) están hechas, 134 códigos con texto
  retirado sumados a fichas del **NBU** existente, no al PMO ni al catálogo del Único; el
  usuario definió ese criterio el 18/8 («sumalo a la sección de NBU nada más, sin
  equivalencias»). Quedan casos «dudoso» para revisión manual, documentados en
  `data/alcance_nn_pmo.json` (no urgente, ver 7 bis A). La duda vieja sobre «los bloques
  repetidos 60-64 del Único» quedó sin resolver — no llegó a ser necesaria para este enfoque,
  pero si en algún momento se retoma la idea de comparar el catálogo del Único-laboratorio
  contra este mismo capítulo, hay que volver a mirarla.
- ✅ **Propagación del «Abarca» a la equivalencia del Único — hecho el 18/8/2026.** El usuario
  pidió que lo que dice un código del PMO o del NBU sobre qué abarca se vea también desde su
  código equivalente en el Único, porque son la misma práctica con otro número. Nuevo script
  `scripts/propagar_abarca_unico.py`: para cada ficha del Único con equivalencia resuelta
  (`key` presente, no `destino_inexistente`), copia el `alcance_nn` de la ficha origen
  (PMO si `unico_tipo==='med'`, NBU si `'lab'`), con nota de auditoría de dónde salió. No toca
  nombres ni modifica `propagar_al_unico.py` (que sigue atando sólo el laboratorio). Correr
  después de `alcance_nn_pmo.py`/`nombres_rotos.py` y antes de `inject_db.py`, cada vez que se
  agregue texto retirado nuevo — ya forma parte de la receta de 7 bis A.
- ✅ **Filtro Prestaciones médicas / Laboratorio dentro del Único — hecho el 18/8/2026.** El
  Único mezclaba en un solo listado sus 1.512 prácticas médicas (equivalentes al PMO) y sus
  1.719 de laboratorio (equivalentes al NBU); ahora hay un panel «Tipo de práctica» que las
  separa, usando el campo `unico_tipo` que ya traía cada ficha (`med`/`lab`) — sin inventar
  equivalencias nuevas. `state.tipoUnico` en `web/index.html`.
  ⚠️ **El mismo filtro para el lado PMO (Prestaciones Médicas) se pidió y se descartó en la
  misma conversación**: al investigarlo, los códigos de laboratorio del capítulo 66 resultaron
  ser, en su mayoría, las mismas fichas que ya existen como NBU (mismo número de 6 dígitos).
  El usuario decidió no duplicarlas como fichas PMO aparte — ver el punto de arriba. **No
  recrear este filtro del lado PMO sin que el usuario lo vuelva a pedir.**
- **95 equivalencias** del Único siguen sin destino en la base, todas al PMO (eran 135; el
  18/8/2026 se revisaron las 135 a mano contra la fuente —ver «Lo que queda por confirmar en
  los datos», más abajo— y 39 se descartaron por estar mal declaradas, 1 se corrigió y ató).
  La más grande: **capítulo 16, anestesiología, 33 códigos** en fila. El número baja con cada
  capítulo importado — se recalcula corriendo `scripts/reparar_equivalencias.py`.
- ⚠️ **Pero no todas se van a arreglar solas, y siete de las 95 ya se sabe que no.** Apuntan a
  códigos de oftalmología —`300128`, `300130`, `300142`, `300148` (×2), `300184`, `300186`—
  que **no existen en el Nomenclador Nacional**: al transcribir el capítulo 30 se vio que
  termina en el `30.01.22` y el `30.02.05`. Son prácticas propias del Único (IOL Master,
  Pentacam, recuento de células endoteliales, test de But, meibografía) con un número del PMO
  que nadie va a importar nunca. La revisión manual del 18/8 las marcó «correctas» —le
  parecieron razonables contra la fuente— pero conviene que alguien las vuelva a mirar con el
  capítulo 30 ya completo: si el 30 termina antes de esos números, no van a atarse solas por
  más que se espere, así que o se les busca el equivalente real a mano o pasan a sin
  equivalencia.

## 8. Pendientes y sugerencias abiertas

### ⚠️ Lo primero que hay que preguntar al retomar

Lo último que se estuvo trabajando —y lo que conviene retomar sin preguntar, porque el
usuario ya lo pidió varias sesiones seguidas— es el **barrido del Nomenclador Nacional** (3.8):
transcribir a ojo el recuadro «Texto retirado por el PMO», capítulo por capítulo. Van **827
de 1.353 fichas (61%)** y sólo quedan el **35, 36 y 38**, que todavía no tienen páginas en el
índice —hay que sacarlas primero con `rapidocr_onnxruntime`— y el **66** (NBU laboratorio,
un trabajo distinto, ver 7 bis D). Receta completa en **7 bis A**. Todo lo que hace falta para
arrancar en frío está en 3.8: índice de páginas, receta, reglas de alcance y el orden sugerido.
**Sesión nueva para cada tanda** — las páginas son imágenes y se reenvían en todos los pedidos
siguientes.

Antes de eso venía el cotejo del **Nomenclador de Prestaciones Médicas** capítulo por
capítulo, con el usuario midiendo contra la fuente (ver 3.4 y 3.5). Lo que quedó de ahí es
**la lista de 159 denominaciones a revisar** (3.5), de a un capítulo y mostrándole los
cambios antes de aplicarlos.

Dos propuestas suyas quedaron abiertas y él las nombró:

- **Cobertura**: hoy 6.231 de 6.372 fichas dicen «COBERTURA: Sin dato» —el 98%— y es la
  primera pregunta del mostrador. El usuario **frenó esto a propósito**: «aún no tengo un
  Excel donde indique esto si tiene cobertura, esto no». **No inventar nada acá**; esperar
  la fuente.
- **Relaciones diagnóstico → práctica**: sólo 45 de 11.581 CIE-10 las tienen. Es la
  consulta más frecuente en el mostrador y sigue siendo la mejora de datos más grande.

Y una que quedó a mitad de camino: en la Mesa de trabajo, **avisar cuando se carga una
radiografía sola y la orden pedía dos posiciones**. Necesita saber si la cantidad de
posiciones llega en el texto de la solicitud; se le preguntó y no contestó todavía.

### Pendientes concretos, con dueño

| Qué | De quién depende |
|---|---|
| **Fijar las acciones de GitHub por SHA** en vez de por etiqueta | mío, necesita una sesión con red a GitHub |
| **Segundo factor en las cuentas de GitHub y del panel de Supabase** (no confundir con el 2FA de la app, ya construido — ver 7 bis B, punto 3), y **proteger la rama** | del usuario; se le pidió dos veces |
| **Correr `docs/supabase_sugerencias_pedida_como.sql`** en el SQL Editor del panel de Supabase (ver 8, «Intérprete de orden médica», punto 3) — sin esto, «Administración → Sugerencias» va a estar vacía y el Intérprete no puede avisar nada (falla en silencio, no rompe la app) | del usuario, una sola vez |
| **Rotar la secret key** de Supabase | del usuario |
| **Cerrar las altas** cuando el equipo esté completo, subir el mínimo de contraseña | del usuario |
| **Las 119 prácticas «fuera del PMO»** que están en nuestra sección PMO | criterio del usuario |
| **Las 113 prácticas del Excel** que no están en la base (comparación de julio) | decisión conjunta |
| **159 denominaciones del PMO a cotejar** con el renglón impreso (3.5) | de a un capítulo, con su visto |
| **17 títulos del capítulo 34 «a confirmar»** y 2 ilegibles (`340803`, `340813`) | del usuario, o de otra planilla |
| **Redacción del aviso «sin confirmar»** en las propuestas visibles al equipo | del usuario (se publicó una versión y ofreció cambiarla) |
| **Volver la base adentro del `index.html`** si prefiere el archivo único (3.0 bis) | del usuario |

### Propuesto y NO construido (por orden de utilidad para el usuario de carga)
- ✅ **Editar una propuesta antes de publicarla — construido el 26/8/2026.** Ver el bloque
  de esta misma fecha, después de «Sesión muerta del lado del servidor».
- ✅ **Historial por ficha — construido el 26/8/2026.** Ver el bloque de esta misma fecha,
  después de «Editar una propuesta antes de publicarla».
- ~~**Registro de actividad compartido**~~ **ya está construido** (revisado el 26/8/2026, no
  hace falta tocarlo): `CONTENT.actividad` se arma en `cargarNube()` (`web/index.html`) a
  partir de `correcciones`/`observaciones`/`verificaciones`/`propuestas` — las cuatro ya
  viven en la nube, no en cada computadora — y se muestra en **Administración → Registro**
  (`aTab==='registro'`). Este apartado había quedado desactualizado; nadie tachó el
  pendiente cuando se construyó.
- ✅ **Intérprete de orden médica — construido el 25/8/2026, como sector aparte.** Nueva
  pestaña **«Intérprete de orden»** junto a Listado / Árbol de módulos / Mesa de trabajo
  (mismo criterio de visibilidad que Mesa de trabajo: no aparece en Buscar en todo, CIE-10,
  Abreviaturas ni SURGE). Se pega el texto de la orden, `partirOrden()` (`web/index.html`)
  la corta en ítems —por renglón, y dentro de cada renglón por «;», «+» o coma que no está
  entre dígitos, sacando numeración o viñetas iniciales— y cada ítem se busca con el
  **mismo motor tolerante a erratas del buscador principal** (`buscar()`/`puntuar()`, sin
  duplicar lógica), mostrando hasta 5 candidatos con un `%` de coincidencia. Se eligen los
  que corresponden (quedan marcados) y **«Enviar a la Mesa de trabajo →»** los manda
  directo al validador (`#vcodes`) y corre el análisis. Es una **ayuda, no un intérprete
  infalible**: el pie de la pantalla lo dice explícito, «confirmá cada código antes de
  cargarlo».
  ⚠️ **Encontrado al probarlo con el propio ejemplo del placeholder** («Rx tórax F y P»):
  `puntuar()` exige que **todos** los términos coincidan, y «F»/«y»/«P» sueltos —ahí,
  abreviatura de posición (frente/perfil), no parte del nombre de la práctica— alcanzaban
  para tirar abajo el renglón entero, aunque «radiología tórax» sí estuviera. Arreglado en
  `candidatosParaItem()`: si la búsqueda con todos los términos no encuentra nada, reintenta
  sacando los sueltos de 1-2 letras (nunca de entrada — a veces son parte real de una sigla
  corta — sólo cuando hace falta para encontrar algo).
  Probado en `tests/e2e/casos/interprete.mjs`: candidatos correctos por renglón (incluido el
  caso de arriba), «sin coincidencias» para texto inventado, elegir/quitar candidatos con el
  resumen actualizándose, y que «Enviar a la Mesa de trabajo» lleva sólo lo elegido y corre
  el análisis.

  ✅ **Ampliado el 25/8/2026, en tres frentes — se conversó con el usuario cómo «alimentar»
  el intérprete sin sumar una IA externa** (se evaluó y se descartó a propósito: rompe el
  requisito de funcionar sin servidor, tiene costo por consulta, y el texto de la orden
  —que puede traer el nombre del paciente arriba— saldría de la app hacia un tercero,
  justo lo que la Regla 8 evita en el resto del sistema):

  1. **Jerga médica ampliada** en `SINONIMOS_COMUNES` (`web/index.html`): `pap`, `bx`,
     `orl`, `tv`, `eab`, `lcr`, `dxa`, `emg` — cada una **verificada contra
     `data/nbu_db.json`** antes de sumarla (que el nombre largo exista de verdad en algún
     código), no adivinada.
  2. **`pedida_como` pasó a ser editable desde ✎ Editar ficha** (sólo el administrador
     general, mismo criterio que nombre/norma/auditoría): un textarea nuevo,
     «Puede venir solicitada como», que se guarda como reemplazo completo (mismo patrón
     que `auditoria`, no un agregado por encima). Hasta ahora el campo sólo lo llenaba el
     pipeline y sólo se mostraba — no había forma de sumarle una forma más de pedir la
     práctica sin tocar los datos de origen. `rebuildH()` no lo incluía en el índice de
     búsqueda (aunque el arranque sí, en la primera pasada — inconsistencia real que quedó
     resuelta de paso) y los **cuatro sitios que reconstruyen el objeto de corrección**
     (`espejarRelacion`, `guardarIncluye`, `guardarAnexar`, el reset de sólo-relaciones)
     tuvieron que sumarlo también, o guardar una relación **pisaba en silencio** cualquier
     `pedida_como` ya cargado — exactamente la clase de descuido que ya pasó una vez con
     `asoc_extra` (ver `supabase_relaciones_medico.sql`). Probado en
     `tests/e2e/casos/pedida_como.mjs`: se agrega y se puede buscar por ese texto, y un
     médico administrador que edita sólo relaciones en la misma ficha **no lo pisa**.
  3. **Aprende del uso real**: si alguien elige, en el Intérprete de orden, un candidato
     que **no es el primero** (el que el motor cree más probable), queda anotado como
     sugerencia — nueva tabla `sugerencias_pedida_como`
     (`docs/supabase_sugerencias_pedida_como.sql`, **el usuario tiene que correrla en el
     panel de Supabase**; ya está incorporada a `docs/supabase.sql` para instalaciones
     nuevas). El administrador la revisa desde **Administración → Sugerencias** (pestaña
     nueva) y «Agregar» la suma a `pedida_como` del código — mismo mecanismo que la edición
     manual del punto 2. A diferencia de «propuestas» (visible a todo el equipo porque son
     notas de «cómo se carga» que le sirven a cualquiera), el **SELECT queda restringido al
     administrador**: es texto suelto de una orden pegada, no algo pensado para
     publicarse. No queda enganchada al contador de «Pendientes» de la barra superior —
     deliberado, para no tocar esa función compartida en la misma tanda; se puede sumar
     después. **RLS probada contra PostgreSQL real** (`tests/rls/`, CN-014 + un caso de
     regresión): un administrativo no lee ni resuelve sugerencias ajenas, no puede insertar
     a nombre de otro, y el administrador sí puede revisar y resolver. Probado también en
     `tests/e2e/casos/sugerencias_pedida_como.mjs` de punta a punta: elegir un candidato
     que no es el primero avisa, el administrador lo ve, lo aprueba, y la ficha queda con
     el texto nuevo en «Puede venir solicitada como».
  4. **Segunda tanda de jerga (25/8/2026), pedida por el usuario con una lista concreta de
     ~45 siglas**, con una condición explícita: que cada una quede encontrable **en los tres
     nomencladores** (Único, NBU, PMO), «lo podés sacar por igualdad de códigos». Eso ya lo
     hace `_h` solo, por la equivalencia entre nomencladores (ver 4.5 sexies y el bloque de
     `CODES.forEach` que suma `equivalencia.desc`/`equivalencia_unico[].unico_desc` al índice
     de cada ficha) — no hizo falta ningún paso nuevo de «registrar en cada nomenclador»,
     sólo sumar la sigla una vez y confirmar que la equivalencia ya estaba armada, lo que se
     verificó ficha por ficha antes de tocar código (ver más abajo).
     - **31 siglas de una palabra** sumadas a `SINONIMOS_COMUNES`: `cvc`, `oct`, `fo`, `obi`,
       `vcc`, `veda`, `angiormn`, `gadolinio`, `rfg`, `arm`, `rg`, `hiv`, `cd4`, `cd8`, `atg`,
       `cl`, `cea`, `hdl`, `ldl`, `urea`, `hbsag`, `dheas`, `ers`, `e2`, `p`, `pcr`, `pth`,
       `hba1c`, `ctx`, `trabs`, `scl`, `ham`.
     - **Mecanismo nuevo para siglas de dos palabras** (`SINONIMOS_COMPUESTOS`, en
       `web/index.html`): `SINONIMOS_COMUNES` sólo puede resolver un término suelto, así que
       "ANTI DNA", "TEST ADOS", "VIT D3" y afines (11 en total) no entraban. `puntuar()` ahora
       revisa, antes de puntuar término por término, cada par de términos consecutivos de la
       búsqueda contra este diccionario nuevo; si el registro trae la forma larga, cubre las
       dos posiciones de una sola vez. Entradas: `anti dna`, `acido urico`, `contraste tac`,
       `test ados`, `test adir`, `citologico completo`, `vit d3`, `anti la`, `anti ro`,
       `anti sm`, `anti rnp`.
     - ⚠️ **Dos bugs reales encontrados armando esto, los dos por el mismo motivo — un
       "match" que en realidad cae adentro de otra palabra por casualidad**:
       1. **Verificación con borde de palabra, no sólo `.includes()`.** Antes de tocar
          código se armó en Python el mismo `_h` que arma la app (con la propuesta cruzada
          de la equivalencia incluida) y se probó cada frase larga contra los 6.478
          registros reales. Con `.includes()` liso, `"anti ro"` → `"ro, ac. anti"` traía
          también 666956/666958/666965 (Legionella Pneumophila, Ac. Anti): la cola de
          "pneumophi**la**, Ac. Anti" arma el mismo texto por casualidad. Con `"anti ro"` →
          `"ro, ac. anti"` pasa lo mismo con "centro**ro**..." → en realidad con
          "cent**ro**mero, Ac. Anti" (CENTROMERO). La condición en `puntuar()` usa
          `new RegExp('\\b'+escRe(...)+'\\b')`, no `.includes()`, por esto exactamente.
       2. **El puntaje del match compuesto tiene que ganarle al de dos matches sueltos, o el
          mecanismo queda invisible en la práctica.** Primera versión sumaba `score+=5` por
          el par cubierto; en la búsqueda real de "anti ro" en el Intérprete, eso quedaba
          **por debajo** de registros que ni siquiera son la sigla buscada pero puntúan alto
          por casualidad término por término (p.ej. "Anticuerpos antitiroglobulina" empieza
          con "anti" → +6, y contiene "ro" en cualquier lado → +3 más, total 9 > 5): el
          código correcto (668905, "Ro, Ac. Anti") ni entraba en el top 5 de candidatos.
          Encontrado recién al probarlo de punta a punta en Playwright, no en la
          verificación de datos (`tests/e2e/casos/interprete.mjs` tiene ahora un caso para
          esto). El máximo por término en el camino normal es 6 (nombre arranca con el
          término); dos términos compuestos cubren dos posiciones, así que el compuesto no
          puede puntuar menos que el mejor caso posible de esas dos por separado —
          `score+=12`, no `+=5`.
     - **Hallazgo de datos, informado sin tocarlo** (no es lugar de esta sesión "corregir"
       la fuente curada — regla del punto 6): la sigla `CD8` es la abreviatura, no el nombre
       de un código — el usuario confirmó que resolver al genérico NBU 663538 / Único
       63663538 («CD, SUBPOBLACION LINFOCITARIA») es lo correcto, no un gap. Lo que sí queda
       anotado aparte: el NBU 661015 («CD8 - SUB POBLACIÓN LINFOCITARIA», un código distinto
       del anterior) tiene como equivalente Único a 61661015, que dice
       **«CD4 x citometria de flujo»** — nombres
       contradictorios entre las dos puntas de esa equivalencia puntual, no algo que esta
       sesión haya decidido resolver.
     - **La sigla `p` (Fosfatemia) es casi un placebo**, y se avisó así al usuario:
       `coincideLiteral()` prueba primero el término **tal cual lo tipeó** contra `_h`
       (`rec._h.includes(t)`) antes de mirar el diccionario de sinónimos — y la letra "p"
       sola ya aparece en el **60%** de los 6.478 registros (cualquier palabra con una "p"
       adentro), con o sin la entrada nueva. Se sumó de todos modos porque no hace daño
       (nunca se usa cuando el literal ya encontró algo), pero no hay que esperar que
       resuelva búsquedas que hoy fallan.
  5. ⚠️ **El tope de 5 candidatos por renglón, avisado por el usuario el 25/8/2026 al
     probar «TAC» y «RMN» sueltos.** `candidatosParaItem()` cortaba en 5 sin condición: para
     un renglón real de una orden (una práctica puntual) alcanza, pero una sigla amplia
     tiene decenas de variantes reales — "tac" son **36** registros (por región, con/sin
     contraste, en los tres nomencladores) y "rmn" son **25** — y el corte tapaba casi
     todas sin forma de verlas. Ahora `candidatosParaItem()` devuelve hasta 30 (techo de
     seguridad, no un límite pensado para pegarse); `correrInterprete()` sigue mostrando
     sólo 5 de entrada, pero si hay más agrega un botón «Ver N más» que revela el resto sin
     recargar nada (`.int-cands-mas`, oculto con `hidden` hasta tocarlo). Probado en
     `tests/e2e/casos/interprete.mjs`: con «tac» aparecen 5 al principio, el botón está, y
     tocarlo revela más de 5 y pasa a decir «Mostrar menos».
  6. ✅ **Tres pedidos del usuario del 26/8/2026, sobre el Intérprete y la búsqueda
     general — «cuando elijo una interpretación no pasa nada», radiología/radiografía, y el
     ejemplo «rx torax f y p»:**
     - **Elegir un candidato no abría nada.** Cada candidato pasó de ser un botón con sólo
       código+nombre+% a un `<div class="int-cand-item">` con dos botones hermanos (no uno
       anidado en el otro): `.int-cand` sigue siendo el de siempre —elige/saca de la Mesa de
       trabajo, mismo comportamiento, mismos tests— y al lado un `.int-ver` nuevo (el ojo 👁)
       que llama a `openCode()`, el mismo drawer de siempre con ficha completa, normas y
       observaciones — sin tocar la elección. Las mismas **etiquetas de decisión y líneas de
       observación/alcance/cruce de nomenclador** que ya se veían en el listado principal
       (`rowHTML()`) se factorizaron en `decTags()` y se reusan tal cual en el candidato del
       Intérprete: se ve si tiene obligación de cobertura, lateralidad, requiere norma, «qué
       abarca» (primera exposición, etc.) y la observación del administrador **sin abrir la
       ficha**, que es la «vista previa» que pedía el usuario.
     - **«rx torax f y p» tiene que traer 340301 (frente) Y 340302 (perfil).** 340302 se
       llama «Por exposición subsiguiente» en la fuente —no comparte ni una palabra con
       «tórax»— así que `buscar()` por puntaje de texto nunca lo iba a encontrar solo. La
       relación ya estaba en la base (`exposicion_siguiente`/`exposicion_de`, el mismo dato
       que ya usaba `comoSeCargaHTML()` adentro de la ficha completa, para 340301→340302,
       340207→340208, 340201→340202, 340209→340210, 340211→340212, entre otros — ver el
       texto de `auditoria` de esos códigos). Nuevo en `candidatosParaItem()`: si el renglón
       trae un indicio de exposición múltiple (`RE_MULTIEXP`: «f y p», «f/p», «frente y/o
       perfil», «comparativ…») se revisan los 5 candidatos que se ven sin tocar «ver más»
       —no sólo el primero: a igualdad de puntaje `buscar()` desempata por el código más
       bajo, no por relevancia clínica, y para «torax» solo eso ponía primero
       «Operación plástica por tórax…» (050102) antes que «Radiología tórax» (340301)— y se
       agrega como candidato aparte (clase `.comp`, con nota explicando de qué código base
       sale) la exposición adicional de cada uno que la tenga. **El «cuándo no» también
       queda a la vista**: si ninguno de los 5 visibles tiene exposición adicional prevista
       con código propio, se muestra una nota (`.int-note`) diciéndolo, con un enlace directo
       a la ficha del código para confirmarlo — antes ese silencio no aparecía en ningún lado
       de la búsqueda.
     - **«radiografía» y «radiología» no traían el mismo listado**, aunque nombran la misma
       sección («Radiología / Diagnóstico por imágenes»): verificado contra
       `data/nbu_db.json`, 16 códigos dicen sólo «radiografía» (340905 «Radiografía en
       quirófano», 340908 «Radiografía a domicilio», …) y 36 dicen sólo «radiología» (340201,
       340301, …) — buscar por una perdía la mitad de la sección. Agregado el par cruzado a
       `SINONIMOS_COMUNES`: `radiografia:['radiologia'], radiologia:['radiografia']` — buscar
       cualquiera de las dos ahora trae también los códigos que sólo dicen la otra.
     - Probado en `tests/e2e/casos/interprete.mjs` (candidato `.comp` de 340302 con su nota,
       tags/observaciones visibles sin abrir la ficha, y el ojo abre el drawer con la ficha
       de 340301 mencionando la exposición adicional) y en `tests/e2e/casos/
       busqueda_sinonimos.mjs`, nuevo (buscar «radiografia» trae 340301 y buscar
       «radiologia» trae 340905, en modo «Buscar en todo el manual»). Los locators del test
       que ubicaban un renglón por `:has-text()` sobre el ítem entero se volvieron ambiguos
       con las etiquetas nuevas —«Prestaciones Médicas» contiene la subcadena «tac», por
       ejemplo— y se corrigieron para filtrar por el propio `.int-src` del renglón, no por
       cualquier texto del ítem.
  7. ✅ **Bug de fondo en `buscar()`, encontrado armando el punto 6 y corregido a
     continuación en la misma sesión (26/8/2026), pedido explícito del usuario
     («arrancá con el bug de ranking»).** Al revisar por qué el candidato de exposición
     adicional a veces se armaba sobre el código equivocado, apareció que `puntuar()`
     empataba «Radiología tórax» (340301) con «Operación plástica por tórax en carina o
     excavado» (050102, cirugía, sin relación con una orden de rayos) al buscar «torax»
     solo —los dos traen el término con borde de palabra en el nombre, mismo puntaje— y
     `res.sort()` sólo ordenaba por puntaje: a igual puntaje, `Array.prototype.sort` es
     estable y ganaba el que hubiera entrado antes a `CODES`, que en la práctica es el
     código más bajo (050102 < 340301) — **cero relación con relevancia clínica.** No es
     un caso aislado del Intérprete: `buscar()` es el motor tolerante de **toda la
     búsqueda de la app** (listado principal, CIE-10, abreviaturas, SURGE, el propio
     Intérprete), así que cualquier término corto y genérico que apareciera en nombres de
     largo muy distinto tenía el mismo problema.
     Arreglado agregando un segundo criterio de desempate a `res.sort()` en `buscar()`:
     a igual puntaje, gana el nombre más corto (`_hn.split(/\s+/).length`, ya calculado
     por `prepBusqueda()`) — el término buscado es una fracción más grande de lo que dice
     un nombre corto, así que es más probable que sea justamente lo que se busca. **No
     toca el puntaje real** (`_score`, el que se muestra como `%` en el listado y en el
     Intérprete) **ni qué entra a los resultados** (`s>=0`, ya decidido antes de
     ordenar): sólo cambia el orden entre registros que ya habían empatado en puntaje —
     riesgo acotado a propósito, sin tocar la fórmula de puntuación que ya estaba
     afinada con varios casos reales (ver punto 4, «anti ro» / Legionella). Probado en
     `tests/e2e/casos/busqueda_especificidad.mjs`, nuevo: buscar «torax» trae primero
     340301, no 050102. Corrida completa de los 24 casos de `tests/e2e/`, dos veces, sin
     fallas.
     Lo que quedaba pendiente de este punto —extender el patrón de «candidato aparte +
     nota» a `seriado`/`lateralidad`/`muestra`— se resolvió a continuación, en el punto 8.
  8. ✅ **Los tres avisos que quedaban pendientes del punto 7, pedidos por el usuario en
     este orden (seriado, lateralidad, muestra), resueltos en la misma sesión
     (26/8/2026).** `avisosCandidato(c,item)`, nueva, corre por cada candidato visible y
     junta hasta tres avisos (mismo estilo visual que la observación del administrador,
     `.int-aviso`, ámbar):
     - **Seriado**: si el renglón trae una cantidad explícita al final (`×N`/`xN` — misma
       sintaxis que ya lee `runCase()` para la Mesa de trabajo, no una nueva) y supera
       `c.seriado.max`, avisa con la cantidad pedida, el máximo habitual y la nota del
       seriado — mismo dato que ya usaba `renderFacturacion()` para el hallazgo
       «supera el seriado habitual», pero antes de mandarlo, no después de cargarlo mal.
     - **Lateralidad**: la etiqueta (`decTags()`, ya sumada en el punto 6) dice
       «Bilateral»/«Unilateral», pero no qué significa para la carga — acá se explica: un
       código bilateral se carga por **cantidad 1** aunque comprenda los dos lados (ojos,
       miembros), que es la confusión real que ya cubre `renderFacturacion()` del lado del
       validador («figura ×2» → rechazo). El unilateral se carga 1 por lado.
     - **Muestra**: si el renglón nombra un tipo de muestra explícito (mismo vocabulario
       que `MUESTRA_VAR`/`MUESTRA_CLS` de `rowHTML()`: sangre, orina, semen, líquido
       cefalorraquídeo, materia fecal, pelo, saliva) que no es la de ese código, avisa
       antes de elegirlo.
       ⚠️ **Encontrado armando la prueba, no en el diseño**: «acetonuria en sangre»
       —para 660002, que es en orina— no traía NINGÚN candidato, así que
       `avisosCandidato()` nunca llegaba a correr: `buscar()` exige que **todos** los
       términos coincidan, y «sangre» no está en el texto de un código de orina, el mismo
       motivo por el que 340302 nunca aparecía solo para «F y P» en el punto 6. Arreglado
       igual que ahí: `candidatosParaItem()` ahora también saca las palabras de
       `MUESTRA_DETECTAR` del reintento sin resultados (antes sólo sacaba los sueltos de
       1-2 letras) — el texto que lee `avisosCandidato()` para comparar sigue siendo el
       renglón completo, sólo cambia qué términos usa `buscar()` para encontrar el
       candidato.
     Probado en `tests/e2e/casos/interprete_avisos.mjs`, nuevo: los tres avisos con
     códigos reales (660102 seriado ×5, 030203 bilateral, 660002 orina) y un renglón sin
     nada que avisar («Hemograma») que no trae ningún `.int-aviso`. Corrida completa de
     los 26 casos de `tests/e2e/`, sin fallas.
- ✅ **Revisiones médicas como notificación para el administrador general — pedido
  explícito del usuario (26/8/2026): «que las revisiones médicas hechas por el médico
  administrador me aparezcan como notificación en mi perfil de administrador general».**
  Hasta ahora la campanita de «novedades» (🔔, junto a la de Pendientes) era sólo para
  administrativos y médicos —observaciones y correcciones de otros—; al administrador
  general le quedaba **siempre oculta**: «el administrador no recibe aviso: para él está
  la campana de pendientes, que es otra cosa» (comentario viejo de
  `cargarContenidoNube()`). Cierto para observaciones/correcciones —el administrador
  general las ve todas igual, no necesita que se las empujen— pero no para las
  revisiones médicas que publica un médico administrador (`publicarRevision()`,
  `datos.revision_medica` en `correcciones`): eso sí es contenido clínico que él no
  escribió.
  Reusa la misma campanita y el mismo modal («Qué pasó desde la última vez»), pero con
  contenido distinto según el rol: para el administrador general, `CONTENT.novedades` se
  arma directamente desde `codes[código].revision_medica` (no desde las filas de
  `correcciones` con su `actualizado` genérico — esa fila puede haber cambiado después
  por otro motivo, como una edición de relaciones entre códigos, sin que la revisión en
  sí sea nueva; la fecha correcta es la propia `revision_medica.t`, puesta por
  `publicarRevision()`). Reusa también la misma marca de «vistas» (`obs_vistas`): el
  administrador general nunca la había usado —la campanita le quedaba oculta—, así que no
  hay conflicto ni hizo falta una columna nueva. El modal (`verNovedades()`) cambia el
  título («Revisiones médicas»), la etiqueta de cada fila (🩺) y el texto vacío según el
  rol; el resto —fecha, código, detalle, tocar para abrir la ficha— es el mismo bloque
  para las dos cosas.
  Probado en `tests/e2e/casos/notif_revision_medica.mjs`, nuevo, de punta a punta con dos
  cuentas reales sobre la misma base compartida (mismo patrón que
  `sugerencias_pedida_como.mjs`): el médico administrador publica la revisión desde la
  ficha (🩺 «Escribir la revisión médica»), el administrador general entra después y ve
  la campanita resaltada con «1», el modal dice quién y qué escribió, tocar el código
  abre la ficha, y verla la marca como vista (la campanita deja de estar resaltada).
- ✅ **Configuración de los valores de coincidencia de la búsqueda — pedido explícito del
  usuario (26/8/2026): «que el administrador pueda modificar los valores de coincidencia
  de la mesa de trabajo».** Preguntado qué significaba exactamente («valores de
  coincidencia» no es un término que ya existiera en la app), contestó los tres: la
  tolerancia a erratas de tipeo, el umbral que resalta una fila como «coincidencia
  fuerte», y los pesos que usa el buscador para puntuar cada tipo de coincidencia. Los
  tres eran constantes fijas en el código (`tolerancia()`, `puntuar()`, el `90` de
  `rowHTML()`) — texto documentado en HANDOFF.md como «afinado con casos reales», no
  cualquier número: cambiarlos a mano seguía necesitando una sesión de Claude Code.
  Ahora los tres viven en `BUSQUEDA_CFG` (nueva, arriba de `tolerancia()`, antes de
  cualquier otra cosa que la use), con sus valores de fábrica en `BUSQUEDA_CFG_DEF`
  —los mismos números que ya había, así que nadie nota el cambio hasta que alguien entra
  al panel nuevo— y editables desde **Administración → Búsqueda** (pestaña nueva, sólo
  para el administrador general, mismo criterio que Textos/Nube/Respaldo):
  - **Tolerancia**, por largo de palabra (cortas ≤4, medianas 5-7, largas 8+) — mismos
    tres tramos que ya usaba `tolerancia()`, ahora con el número de erratas toleradas
    editable en vez de fijo.
  - **Umbral de «coincidencia fuerte»** (90% de fábrica) — el % desde el que una fila se
    resalta en el listado (`rowHTML()`, clase `.row-match`).
  - **Pesos** de cada tipo de coincidencia (empieza con el término / aparece en el nombre
    con borde de palabra / aparece en cualquier parte / sólo en código-sinónimo-
    abreviatura) — los mismos 6/4/3/2 de siempre en `puntuar()`, ahora configurables. Se
    reordenan solos al guardar si alguien los carga fuera de orden (tienen que ir de
    mayor a menor en ese orden o la búsqueda deja de tener sentido).
  ⚠️ **Un invariante documentado que había que preservar, no romper**: el bonus de
  `SINONIMOS_COMPUESTOS` («anti ro» → «Ro, Ac. Anti», ver punto 4 de esta sección) valía
  `12`, un número fijo elegido a propósito para no puntuar menos que dos coincidencias
  sueltas de `inicio` (6+6) — si el administrador subiera el peso de `inicio` sin que
  ese bonus lo acompañara, el bug real que ese `12` arregló (668905 tapado por
  coincidencias parciales de "Anticuerpos antitiroglucobulina") podía volver a aparecer.
  Se cambió el `12` fijo por `BUSQUEDA_CFG.pesos.inicio*2`, derivado, para que el
  invariante se mantenga solo pase lo que pase con el peso de `inicio`.
  Publicado para todo el equipo (mismo mecanismo que Textos: `guardarAjustesNube()`
  manda `page`+`equipo`+`busqueda` juntos en cada guardado porque `ajustes.contenido` es
  una sola columna jsonb que se reemplaza entera, no se mezcla — dejar `busqueda` afuera
  de un guardado de logo lo habría borrado en silencio la primera vez que alguien tocara
  Textos). También corregido el mismo riesgo en el flujo de «Restaurar respaldo»
  (`aplicarRestaurar()`), que llama a `NUBE.guardarAjustes()` aparte: un respaldo de
  antes de esta función no trae `busqueda`, así que se preserva la configuración ya
  publicada en vez de vaciarla.
  Arranca de `localStorage` (`BUSQUEDA_CFG`, mismo patrón que `ubValue`) para que la
  búsqueda funcione desde el primer segundo sin esperar a la nube, y `cargarContenidoNube()`
  la actualiza si el equipo publicó una propia.
  Probado en `tests/e2e/casos/config_busqueda.mjs`, nuevo, contra el efecto real (no sólo
  contra el valor guardado): con la tolerancia de palabras largas en 0, «hemogrma» (una
  letra de menos que «hemograma», a un cambio de distancia) deja de encontrar nada;
  restaurando los valores de fábrica, vuelve a encontrarlo. También que persiste tras
  recargar, que los pesos fuera de orden se reordenan solos, y que un médico
  administrador no ve la pestaña.
- ✅ **Coincidencia forzada a mano, por código — pedido explícito del usuario (26/8/2026),
  a partir de un caso real de la propia base.** Buscar «urea» encuentra bien 660902 «UREA,
  sérica» (100%, coincide con el nombre), pero **U60660902 «Uremia»** —la misma práctica,
  semánticamente la respuesta correcta— sólo llegaba al **33%**: la palabra «urea» no está
  en el NOMBRE de esa ficha, sólo en la equivalencia cruzada con el NBU, que `puntuar()`
  puntúa en el tier más bajo (`solo`, ver punto anterior sobre `BUSQUEDA_CFG`) porque el
  tier alto (`inicio`/`borde`/`contiene`) sólo mira `_hn` (el nombre), no la equivalencia.
  Los tres valores de `BUSQUEDA_CFG` (punto anterior) son globales, de toda la búsqueda —
  no alcanzaban para este caso puntual sin desafinar el resto—, así que se agregó un
  mecanismo aparte, por código: un campo nuevo `coincidencia_forzada` (lista de frases),
  editable desde **✎ Editar ficha → «Buscarlo así, 100% seguro»** (mismo permiso que
  `pedida_como`, sólo el administrador general). `puntuar()` lo revisa **primero, antes
  que cualquier otra cosa**: si la consulta entera (todos los términos juntos, no uno
  suelto) coincide exacto con una de las frases guardadas, devuelve `100` de una — mismo
  mecanismo que ya usa el código exacto para que `matchPct()`/`pctInterprete()` lo
  muestren como 100%, sin tocar esas funciones. Comparar la consulta **entera** (no
  término por término) es a propósito: fijar «urea» no tiene que forzar también cualquier
  búsqueda de dos palabras que la contenga de casualidad.
  Distinto de `pedida_como` («puede venir solicitada como»): ese ayuda a ENCONTRAR el
  código (entra a `_h`, tier bajo), esto FUERZA el porcentaje — la diferencia que hacía
  falta para el caso de «Uremia», que ya se encontraba bien pero con poca confianza
  visual.
  Sumado al mismo circuito que `pedida_como`/`asoc_extra`: respaldo en `applyCode()`
  (`c._orig.coincidencia_forzada`), aplicación de la corrección, restaurar original, los
  cuatro sitios que reconstruyen `ov` al editar sólo relaciones o espejar (para no
  pisarlo en silencio — la misma clase de descuido que ya pasó una vez con `asoc_extra`,
  ver 6 bis de `docs/supabase.sql`), y la etiqueta en `CAMPO_LABEL_HIST` para que se vea
  bien en «Ver historial». También visible en la propia ficha (sección nueva, con las
  frases en chips) para que se entienda por qué ese código aparece con 100% sin tener que
  abrir Editar ficha.
  Probado en `tests/e2e/casos/coincidencia_forzada.mjs`, nuevo, con el caso real de
  «urea»/Uremia: antes de forzarla no está resaltada, después sí; la ficha explica la
  coincidencia forzada; y agregar «urea» no dispara con «urea clearence» (frase distinta),
  sólo con la consulta exacta.
- ✅ **El Intérprete de orden agrupa por equivalencia entre nomencladores — pedido
  explícito del usuario (26/8/2026), a partir de una captura real.** «radiografia torax
  f y p» mostraba TRES tarjetas para lo que es una sola práctica: 340301 del PMO,
  340301 del Único —**el mismo código, con 83% en un lado y 50% en el otro** («eso no
  debería suceder, si es la misma práctica»)— y 340302 como candidato aparte para la
  exposición de perfil («no hacemos todo un bloque entero… que te diga los
  nomencladores y el código asociado»). Las dos cosas eran la misma raíz: cada
  candidato era un registro suelto (`c._key`), nunca «la práctica», así que dos
  nomencladores de un mismo código nunca se reconocían como una sola cosa.
  Arreglado agrupando en `candidatosParaItem()` con `EQGRUPO` (armado más arriba en
  este archivo — la misma equivalencia que ya usan las observaciones y revisiones
  médicas compartidas entre nomencladores, ver 4.5 y HANDOFF.md del 26/8/2026,
  «Revisiones médicas»): cada grupo es un array de registros (ya vienen ordenados por
  puntaje, porque `cands` lo está) con el mejor puntaje del grupo primero. La
  exposición adicional (`g.comp`) y el aviso de «sin perfil» (`g.sinPerfil`, punto 6-8
  de esta sección) quedaron colgados del grupo, no de un candidato suelto.
  `correrInterprete()` dibuja un solo `<div class="int-grupo">` por práctica:
  - El candidato **principal** (mejor puntaje del grupo) es el `<button class="int-cand">`
    de siempre — mismo comportamiento, mismos tests, un solo porcentaje (el máximo del
    grupo, no uno por nomenclador: **esto es lo que resuelve la inconsistencia** — un
    código nunca vuelve a mostrar dos números distintos porque ahora sólo se muestra
    uno).
  - Los demás nomencladores del mismo código quedan como chips chicos «También en:
    [PMO] [Único]» (`.int-nom-chip`, hermanos del botón principal — nunca anidados
    adentro, dos botones reales) que eligen puntualmente ESE código para la Mesa de
    trabajo, sin abrir una tarjeta nueva.
  - La exposición adicional cuelga del mismo bloque como nota (`.int-cand-comp`, mismo
    tono ámbar que los avisos de seriado/lateralidad/muestra) con sus propios chips por
    nomenclador — no un candidato más en la lista.
  ⚠️ **Bug real encontrado armando la prueba, no en el diseño**: `exposicion_siguiente`
  sólo está cargado del lado del PMO (`340301`), **no** en su equivalente del Único
  (`U340301`) — comprobado contra `data/nbu_db.json`. Buscando «radiografia» (en vez de
  «rx» o «radiología»), el nombre del Único («Radiografía de torax») puntúa más que el
  del PMO («Radiología tórax», que sólo matchea por el sinónimo cruzado del punto
  anterior), así que el PRINCIPAL del grupo terminaba siendo el del Único — y como
  `candidatosParaItem()` sólo miraba `g[0].exposicion_siguiente`, la exposición
  adicional se perdía en silencio, mostrando «este código no tiene exposición
  adicional» siendo falso. Arreglado buscando el dato en **todo el grupo**
  (`g.find(m=>m.exposicion_siguiente)`), no sólo en el principal.
  ⚠️ **Segundo ajuste, también encontrado armando la prueba**: los chips «también en»
  (otro nomenclador del MISMO grupo, que sí matcheó por texto) no deberían quedar
  excluidos de la sugerencia «pedida como» —a diferencia de los chips de exposición
  adicional, que sí quedan siempre afuera, porque ese código nunca pasó por `puntuar()`—:
  si el grupo no es el primero (`rank!=0`), elegir cualquiera de sus chips sigue siendo
  la misma señal de siempre («el buscador no puso esta práctica arriba»), tenga el
  nomenclador que tenga. Se separó `data-int-companion` en dos usos de `nomChip()`: los
  chips de «también en» no lo llevan (gatean sólo por `rank`, igual que el candidato
  principal), los de exposición adicional siempre lo llevan.
  Actualizados `tests/e2e/casos/interprete.mjs` y `sugerencias_pedida_como.mjs` a la
  estructura nueva (los locators ya no pueden asumir `.int-cand` — un código puede
  terminar de principal o de chip según cuál nomenclador puntúe más; y en
  `sugerencias_pedida_como.mjs`, 660412 pasó a formar parte del grupo top —ya no sirve
  como «candidato que no es el primero»— así que el caso pasa a usar 660413, del
  segundo grupo). Nuevo `tests/e2e/casos/interprete_grupos.mjs` con el caso real de la
  captura: un solo bloque, un solo %, el chip «también en», la nota de exposición
  adicional con sus dos chips, y el bug de `exposicion_siguiente` sólo del lado del PMO.
  Corrida completa de los 21 archivos de `tests/e2e/`, dos veces, sin fallas.
- ✅ **El bloque agrupado del Intérprete pasa el borde de «ficha» a `.int-grupo` —
  pedido explícito del usuario (26/8/2026), sobre el punto anterior.** El bloque de
  arriba juntó los candidatos en un solo `<div class="int-grupo">`, pero el borde y el
  fondo de tarjeta seguían siendo del `<button class="int-cand">` de adentro: el chip
  «También en» y la nota de exposición adicional (`.int-cand-otros`/`.int-cand-comp`,
  hermanos del botón, no pueden ir DENTRO de un `<button>` porque traen sus propios
  botones) quedaban visualmente **por fuera** de ese borde, flotando debajo. «Deberia
  aparecer todo dentro de la misma ficha, no por fuera… Establecerlo por fuera es un
  mal diseño UI». Arreglado moviendo el borde/fondo/padding de `.int-cand` a
  `.int-grupo` (con `:has(.int-cand:hover)`/`:has(.int-cand.on)` para el estado
  resaltado, ya que el borde ya no vive en el elemento clickeado) y dejando `.int-cand`
  sin borde ni fondo propio — sólo layout. Mismo HTML de `grupoBtn()`, sólo CSS.
  Verificado con captura real («radiografia torax f y p»): el candidato principal, sus
  etiquetas, «También en: PMO» y la nota ámbar de exposición adicional quedan ahora
  dentro de un único recuadro. Corrida completa de los 31 archivos de `tests/e2e/`, sin
  fallas (sólo CSS: no hizo falta resellar la CSP).
  ⚠️ **Aparte, sobre una captura del usuario con un texto y un % que no coincidían con
  el código local**: el mismo mensaje traía una captura de «torax f y p» con 340301 al
  100% y un cartel ámbar con un texto («Si el estudio lleva más de una exposición…») que
  no existe en ningún lado del código del Intérprete. Se rastreó a `comoSeCargaHTML()`
  (línea ~4534), que es texto **preexistente** de la sección «Cómo se carga» de la
  **ficha completa** (`openCode()`) — no del Intérprete — y que ya estaba en el repo
  antes de esta sesión (`git log -S` no lo encuentra en ningún commit de esta rama).
  Como el propio punto (a) de este bloque hizo que elegir un candidato abra la ficha
  completa, ver ese texto junto con la tarjeta del Intérprete es esperable: son dos
  vistas distintas, mostradas juntas en la misma captura, no una regresión. El 100% (vs.
  el 67% que da esta búsqueda con los pesos por defecto) es consistente con que la
  cuenta del usuario tenga sus propios valores guardados en **Administración →
  Búsqueda** (`BUSQUEDA_CFG`, ver el bloque del 26/8/2026 «el administrador general
  puede editar los valores de coincidencia del buscador») — no hay ningún bug de
  puntaje distinto entre lo local y lo desplegado.
- ✅ **35 códigos PMO con «checksum no cierra» — corroborados contra el PDF fuente y
  corregidos, pedido explícito del usuario (26/8/2026): «esos todos tienen valores
  establecidos en el nomenclador que te pasé».** Del bloque anterior (679 códigos PMO
  sin `valores.galeno`), 35 traían un `total_p` en `nn_values.json` pero con
  `checksum_ok:false` — el usuario pidió corroborarlos uno por uno contra
  `data/NOMENCLADOR NACIONAL DE PRESTACIONES MEDICAS CON PMO-COMPRIMIDO.pdf` (ya
  versionado en el repo) y armar el listado con el valor correcto de cada uno.
  Se leyó la página real de cada código (con `PyMuPDF`, rasterizando cada página y
  leyéndola directamente — el PDF es escaneado, sin capa de texto) y se confirmó: **en
  los 35 casos el nomenclador SÍ trae honorarios**, el checksum fallaba por un bug del
  extractor por posición (`scripts/parse_nn.py`), no por falta de dato en la fuente.
  ⚠️ **Encontrado armando la corroboración, no antes**: el campo `page` de
  `nn_values.json` **no es el número de página impreso del PDF** — está desalineado por
  capítulo (ej. capítulo 03 estaba corrido 2 páginas respecto del pie de página real;
  capítulo 07 en adelante, mucho más) — hubo que ubicar cada código navegando el PDF,
  no confiando en ese campo. Y el bug de fondo en `parse_nn.py`: las bandas de fila se
  arman a partir de la posición Y del código de la fila siguiente/anterior, así que en
  filas con nota larga (ej. «Texto retirado por el PMO…» a varios renglones) la columna
  de anestesista o de gasto a veces toma el valor de la fila de al lado — ej. `020106`
  tenía anestesista=20.24/gasto=132.04 (los valores de la fila 02.01.05, arriba), cuando
  los correctos son 18.67/108.39 (suman exacto contra el total impreso, 190.56).
  ⚠️ **Un solo caso fue una errata real de imprenta, no del extractor**: `060105`
  imprime el $ del ayudante como «80.2», que no cierra contra el total (41.52+80.2+
  20.24+108.39=250.35≠178.17); con 8.02 —mismo factor U.→$ que el resto de la fila—
  cierra exacto. Marcado aparte en el listado, no confundido con los otros 34.
  Corregidos los 35 en `data/nn_values.json` (`checksum_ok:true`,
  `corregido_manualmente:true`) y en `data/nbu_db.json` (`valores`/
  `asociaciones_especificas`, mismo formato que arma `assemble.py`, sin correr el
  pipeline completo —no había intermedios en el scratchpad de esta sesión— sino
  aplicando el mismo cálculo a mano sobre los dos JSON). Publicado con
  `python3 scripts/inject_db.py` (regenera `web/nbu_db.bin`; no toca `<script>` de
  `index.html`, no hizo falta resellar la CSP). Corrida completa de los 31 archivos de
  `tests/e2e/`, sin fallas.
- ✅ **3 códigos PMO más con valor real — encontrados por el usuario revisando el
  listado, 26/8/2026: «100503, 121417, 280105, 430201 tiene valores... 010605, 020105
  tiene valor».** De los cuatro primeros, sólo `100503` (Orquidectomía unilateral)
  resultó ser un caso simple: `nn_values.json` tenía especialista/ayudante/anestesista/
  gasto bien parseados pero **le faltaba sólo el total** (`total_p:null`,
  `checksum_ok:null`, así que `assemble.py` lo descartaba igual que si no tuviera
  nada) — se reconstruyó sumando los cuatro componentes (99.57, confirmado además
  contra la página real). `020105` y `010605` no estaban ni siquiera **como entrada**
  en `nn_values.json` (`nn.get(code) is None`) pese a tener valor real e impreso en la
  misma página que códigos vecinos ya corregidos — se leyeron directo de la página
  (`020105`: 215.78; `010605`: 180.25). `280105` y `430201` resultaron ser síntoma de
  un problema mucho más grande, ver el punto siguiente.
- ✅ **~500 códigos PMO sin valor eran, en realidad, un segundo formato de tabla que el
  extractor nunca entendió — investigado y corregido a mano, página por página,
  26/8/2026.** El usuario, mirando `280105` y `430201`, avisó: «fijate que algunos en
  la ultima fila dice COSEGURO HASTA, NO total... Los de RETIRADO POR EL PMO, fijate
  que muchos tiene valor.. pero la suma no te debe estar dando». Tenía razón: a partir
  del capítulo 14 (`data/NOMENCLADOR NACIONAL DE PRESTACIONES MEDICAS CON
  PMO-COMPRIMIDO.pdf`, título de sección en la página impresa 82 → índice de PDF 91,
  hasta la página impresa ~134 → índice de PDF 150, antes de que empiece la sección de
  odontología en índice 152) el documento cambia de **"P.M.O. de Intervenciones
  Quirúrgicas"** (Especialista/Ayudantes/Anestesista/Gasto/Total, el formato que sí
  entendía `scripts/parse_nn.py`) a **"P.M.O. de Prácticas Especializadas"**
  (Honorarios/Gastos/**Total Práctica**/**Coseguro Hasta**, dos columnas nuevas que
  `parse_nn.py` no tiene mapeadas). Como el extractor buscaba «Total» donde ahora está
  Coseguro Hasta (un número redondo tipo 250.00, 100.00, 50.00 — nunca el valor real de
  la práctica), producía `checksum_ok:false` o, más seguido, ni siquiera encontraba
  nada (`tipo:'sin_valor'`) — de ahí que capítulos enteros (Cardiología, Medicina
  Nuclear + Centellograma, Radiología, Genética Humana, Neumonología, etc.)
  aparecieran 100% sin valor en el listado original: no es que la fuente no los tenga,
  es que nadie los leyó bien nunca.
  ⚠️ **Se probó automatizar la lectura con Tesseract antes de tocar nada a mano** (ver
  el intercambio con el usuario del 26/8/2026: «Probé el parser automático... resultó
  poco confiable») — en la misma página de Genética Humana ya leída a mano, la pasada
  de página completa **se comió el código `21.01.01` entero** y en la columna de
  Coseguro Hasta devolvió basura según el recorte usado. El usuario decidió seguir con
  lectura manual, página por página, como se venía haciendo — mismo método que ya
  había demostrado cero errores en los 35+3 códigos anteriores.
  Se recorrieron ~65 páginas del PDF (capítulos 14 a 44, uno por uno, con
  `PyMuPDF.get_pixmap(dpi=190-200)` y lectura visual directa) transcribiendo
  honorarios/gastos/total práctica/coseguro de cada fila, con la misma validación de
  siempre: honorarios$ + gastos$ tiene que cerrar contra el total práctica impreso
  (tolerancia `max(0.05, total*0.02)`, algo más laxa que la de `parse_nn.py` porque acá
  el redondeo de esta sección corre más). Lo que no cerraba, se dejó afuera en vez de
  forzarlo.
  Resultado, aplicado directo a `data/nbu_db.json` (sin pasar por `nn_values.json`,
  que no tiene columnas para este formato — Honorarios/Gastos, sin
  ayudantes/anestesista, más `coseguro_hasta`; mismo `valores.galeno`/`pesos_2002` que
  usa `assemble.py`, con los campos que no aplican en `None`):
  - **427 códigos** con `valores` reales (honorarios/gasto en galenos y en $ 2002, más
    `coseguro_hasta` cuando la fila lo traía).
  - **90 códigos** marcados explícitamente como **«Código agregado por el P.M.O.: no
    está en el Nomenclador Nacional de Prestaciones Médicas, no tiene valorización en
    galenos»** en `valor.arancel` — pedido explícito del usuario («TODO LO QUE DIGA
    CODIGO AGREGADO POR PMO, debe aclarar que no tiene valor»): son filas donde el
    propio documento no imprime ningún honorario ni gasto, sólo el coseguro (cuando lo
    tiene) — no es un vacío del extractor, es que esa prestación nunca tuvo
    valorización en el Nomenclador Nacional de 1991/2002 y el PMO la sumó después.
  - **1 código** marcado «Incluido en la consulta médica (I/C) — no se factura por
    separado» — la mayoría de las filas «I/C» de la fuente ni siquiera tienen una
    entrada de 6 dígitos en `nbu_db.json` (no forman parte del catálogo PMO cargado),
    así que no había nada que marcar en esos casos.
  - `430201` (CURACIONES, uno de los cuatro códigos que disparó todo esto): la fila
    real es sólo gasto (sin honorario), total práctica **1.04**, coseguro 50 — muy
    distinto del `total_p:50.0` que tenía `nn_values.json` antes, que en realidad había
    mezclado el texto de la norma («Curaciones sin cargo: cirugía hasta 89 u.s. ...»,
    impreso arriba de la fila) con la fila misma.
  ⚠️ **Estado al cierre de este bloque**: aplicado a `data/nbu_db.json` y publicado con
  `python3 scripts/inject_db.py` (regenera `web/nbu_db.bin`). **Falta todavía**: correr
  la suite completa de `tests/e2e/` sobre este cambio (se interrumpió antes de
  terminar) y commitear/pushear — el archivo de trabajo con los ~600 códigos leídos
  (`especializadas.json` y el acumulador `especializadas_acc.py`) quedó en el
  scratchpad de la sesión, no en el repo.
  usuario mirando los logs de Postgres del proyecto (API Gateway/Postgres/Auth de
  Supabase).** Vio 17 errores de Postgres sobre 21 llamados en una hora; el detalle era
  `42501 permission denied for function pendientes` justo después de un
  `POST /auth/v1/token?grant_type=refresh_token` con **400**. Encadenado: el refresh token
  puede morir solo (venció, o quedó invalidado por un login desde otro lado) sin que la app
  haga nada raro, y `NUBE.vigente()` ya detectaba eso — pero **`NUBE.api()` ignoraba el
  resultado** y llamaba igual, con `hdrAuth()` cayendo a la clave pública (`ANON`) como
  `Authorization` cuando no hay sesión. Como `pendientes()` (y toda función que depende de
  la sesión) tiene el permiso de ejecución sacado a propósito para `anon` (ver
  `docs/supabase_permisos_funciones.sql`), cada intento quedaba como «permission denied» en
  la base — y como el aviso de pendientes se sondea solo cada 60 segundos
  (`refrescarCuentasNube()`, con `catch(e){}` silencioso), esto se repetía sin que nadie se
  enterara nunca de que la sesión había muerto. No es un problema de seguridad (los permisos
  hacían exactamente lo que tenían que hacer); el problema era la falta de aviso.
  Arreglado en dos puntas, ambas devolviendo al login con «Tu sesión venció. Iniciá sesión
  de nuevo.» en vez de reintentar en silencio:
  1. `NUBE.api()` corta antes de llamar si `vigente()` dice que la sesión ya está muerta
     (no había, o el refresh acaba de fallar) — antes sólo hacía `await vigente();` sin
     mirar el resultado.
  2. El reintento cuando el access token muere **entre medio** de un llamado (`api()`,
     status 401 con sesión) tampoco avisaba si el refresh de ese reintento fallaba — se
     tragaba el error y dejaba pasar el 401 original como si fuera cualquier otro error de
     la llamada.
  Ambas puntas llaman a `cerrarSesionMuerta()`, una función nueva que es el mismo cuerpo que
  ya tenía `resetIdle()` (cierre por inactividad) sacado aparte — mismo cierre real
  (`NUBE.salir()`, vuelta al gate), ahora con un único lugar para no repetirlo. Probado en
  `tests/e2e/casos/sesion_muerta.mjs`: revocando el access token y el refresh token del lado
  del simulador (mismo cuadro que un refresh vencido de verdad), la app cierra la sesión
  sola, avisa, borra lo guardado en `localStorage`, y un login nuevo después sigue andando
  sin nada roto.
- ✅ **Editar una propuesta antes de publicarla — construido el 26/8/2026.** Hasta ahora,
  en Administración → Pendientes, el administrador sólo podía **Aprobar** el texto de una
  propuesta («Contá cómo se carga acá») tal cual lo escribió el agente, o **Descartarla**
  entera — un typo o una frase ambigua obligaba a rechazarla y pedirle a la persona que la
  volviera a escribir. Se decidió con el usuario que **sólo el administrador edita, al
  revisarla** (no el autor original mientras está pendiente: eso hubiera necesitado una
  regla de acceso —RLS— nueva y sus pruebas; esto no tocó ninguna, `prop_resolver` ya le
  permitía al administrador actualizar cualquier columna de la fila, sólo hacía falta la
  pantalla).
  - El texto de cada propuesta pendiente ahora es un `<textarea>` editable
    (`.prop-edittxt`), no un párrafo fijo.
  - **«Guardar cambios»** (`NUBE.editarPropuesta()`, nuevo — mismo patrón que
    `resolverPropuesta()`) queda deshabilitado hasta que el texto realmente cambia, para no
    mandar un PATCH de la nube por abrir el panel a mirarlo nomás.
  - **Aprobar directo con una edición sin guardar también vale**: no hace falta el paso de
    «Guardar» antes de «Aprobar» — se publica lo último que quedó tipeado, y de paso la fila
    de la nube queda con ese mismo texto (antes de marcarla `aprobada`), no sólo lo que
    llegó a la ficha.
  - El textarea y los botones de cada propuesta se ubican por cercanía en el DOM
    (`closest('.arow')`), no por índice: el `idx` de `propuestasTodas()` es la posición
    dentro de la lista de **cada código**, no global, así que dos propuestas de códigos
    distintos pueden compartir el mismo número — buscar el textarea sólo por ese `idx` (como
    se armó al principio) traía a veces el de otra fila. Encontrado antes de publicar, no en
    producción.
  - Probado en `tests/e2e/casos/editar_propuesta.mjs`: las dos formas de guardar el cambio
    (Guardar aparte, o editar+Aprobar directo) dejan la ficha **y** la fila de la nube con el
    texto corregido, y el botón «Guardar cambios» habilita/deshabilita según corresponda.
- ✅ **Historial por ficha — construido el 26/8/2026.** Se pedía «quién la corrigió, cuándo
  y qué decía antes», y no hizo falta ninguna tabla ni migración nueva: **`public.auditoria`
  ya existe** (`docs/supabase.sql`, sección «7 bis») y ya registraba esto solo desde antes de
  esta sesión — un trigger `SECURITY DEFINER` (`auditar()`) guarda automáticamente la fila
  completa de `correcciones` de antes y de después de cada guardado, en cualquiera de los
  ~12 lugares del código que llaman a `guardarCorreccion()`. Sólo faltaba la pantalla: nadie
  la había construido todavía.
  - **`NUBE.historialFicha(codigo)`** (nuevo): `select` a `auditoria` filtrado por
    `tabla=correcciones` y `clave=<código>`, orden del más nuevo al más viejo. Misma RLS de
    siempre (`es_admin()`) — **no se tocó ninguna policy**, sólo se sumó el método de
    lectura del lado del cliente.
  - Botón **«🕘 Ver historial»**, al lado de «✎ Editar ficha» (mismo criterio de
    visibilidad: administrador general, modo edición activado, y con la nube encendida —
    en modo local no hay `auditoria` que consultar). Se pide **al abrirlo**, no en cada
    render de la ficha: un viaje a la nube de más por cada código que se mira sería
    desperdiciado la mayoría de las veces.
  - **`diffCorreccion()`** compara el `antes`/`despues` completos (columna `datos`, la
    copia exacta que manda — no las columnas sueltas, que no existen para
    `pedida_como`/`incluye`/etc.) campo por campo, sin asumir cuáles van a estar presentes:
    cualquiera de los ~12 sitios que guardan una corrección puede mandar un subconjunto
    distinto de campos (una edición completa de ficha, sólo relaciones, sólo aprobar una
    propuesta…). Para la primera corrección de un código (`operacion='alta'`, la fila de
    `correcciones` no existía) no hay «antes» que mostrar — la ficha, antes de la primera
    corrección, se arma con los datos del pipeline (`data/nbu_db.json`), que `auditoria` no
    conoce; el historial sólo cubre correcciones hechas **desde la app**, no el contenido
    original.
  - Probado en `tests/e2e/casos/historial_ficha.mjs`: sin correcciones todavía dice que no
    hay nada; la primera corrección aparece como alta, sin «antes»; una segunda corrección
    sobre la misma ficha sí muestra el valor anterior real, y las dos quedan ordenadas de la
    más nueva a la más vieja. El simulador (`tests/e2e/simulador.mjs`) emula el trigger a
    mano —no reproduce Postgres real, eso es lo que prueba `tests/rls/`— sólo para poder
    ejercitar la pantalla; como no se tocó ninguna RLS, `tests/rls/` no necesitó cambios.
- ✅ **Un corte de señal momentáneo no pierde lo que se estaba guardando — construido el
  26/8/2026, pedido por el usuario («PWA / offline total»).** Alcance acotado a propósito,
  charlado con el usuario: esto NO es una cola de cambios que persiste mientras no hay
  internet por un rato largo (eso necesita mucho más cuidado — dos ediciones del mismo
  código en cola pueden pisarse, y algunas acciones dependen de una que todavía no se
  mandó); es sólo que el wifi de la oficina se corte **un momento** —unos segundos, un
  minuto— y la app no tire un error ni obligue a repetir la acción a mano.
  - **`hacerConReintento()`** (nuevo, dentro de `NUBE`): envuelve el `fetch` de `api()` y de
    `token()` (el refresh de sesión). Si sale un corte de red de verdad —un `fetch` que ni
    siquiera llega a haber respuesta llega como `TypeError` («Failed to fetch» /
    «NetworkError», mismo patrón que ya usaba `traducir()`, no inventado— reintenta con
    espera creciente (2s, 5s, 10s; ~17s en total) antes de rendirse. Un error real del
    servidor (contraseña mal, 403, un 400 genuino) **no** entra acá: tiene respuesta, y
    reintentar no lo iba a arreglar — demorar ese aviso sería peor que mostrarlo de una.
  - Primer corte: avisa una vez, sin alarmar («Sin conexión — reintentando…»), y si el
    reintento llega a andar, la acción original sigue su camino normal — el mismo «Ficha
    actualizada», el mismo cierre de modal, sin que la pantalla que llamó a `enNube()`
    tuviera que enterarse de nada raro. No hizo falta tocar ninguno de los ~21 lugares que
    usan `enNube()`: al estar en `api()`, que es el único punto por el que pasa cualquier
    llamado a la nube, cubre todos de una.
  - ⚠️ **De paso, corrigió un efecto secundario real del arreglo de «sesión muerta» del
    mismo día**: antes de esto, `vigente()` trataba CUALQUIER falla al refrescar el token
    como sesión muerta — incluido un corte de red pasajero durante ese refresh, que
    hubiera forzado un logout real por algo que se arreglaba solo en el próximo intento.
    Ahora `vigente()` (y el reintento de `api()` tras un 401) distinguen: sólo un rechazo
    de verdad del servidor cuenta como sesión muerta; un corte de red, no.
  - Probado en `tests/e2e/casos/reintento_red.mjs`: se aborta la primera llamada a
    `/rest/v1/correcciones` con `route.abort('failed')` (mismo `TypeError` que un corte
    real) y se deja pasar el resto al simulador de siempre — la app avisa, reintenta sola a
    los ~2s, y el cambio llega igual a la «nube» (comprobado del lado del simulador, no sólo
    mirando la pantalla, que ya se había actualizado local antes de que la nube confirmara
    nada).
- ✅ **Guía provincial de IVE/ILE vinculada a la Ley N° 27.610 — agregado el 26/8/2026,
  a pedido del usuario.** El usuario adjuntó la «Guía de implementación de la interrupción
  voluntaria del embarazo en la Provincia de Buenos Aires» (2ª edición, septiembre 2021,
  Ministerio de Salud de la Provincia de Buenos Aires) y pidió anexarla a la Ley N° 27.610
  ya cargada en el glosario y marco normativo (`ⓘ` → Leyes · Resoluciones · Decretos).
  No es una ley aparte —es una guía que **complementa** la implementación de la 27.610 en
  la provincia, no una norma nueva—, así que no se sumó como entrada nueva de `leyes`: se
  agregó un campo `documentos` (nuevo) a la entrada existente de la 27.610, en
  `scripts/assemble.py` (fuente) y `data/nbu_db.json` (base ya compilada — el pipeline
  completo de `assemble.py` necesita intermedios que no viven en el repo, ver 3.2; para un
  cambio así de acotado, sumarlo a mano en los dos lados y correr
  `python3 scripts/inject_db.py` es lo que corresponde, no reconstruir todo). Sin `url`: es
  un PDF que subió el usuario, no un enlace oficial verificado — no se inventa uno.
  `web/index.html` (`openInfo()`) suma una sección «Documentos relacionados» dentro del
  detalle de la ley, con el mismo patrón que ya usan `cobertura`/`articulos`/`temas`
  (título, fuente, fecha, resumen). Verificado a mano en el navegador (buscar «27.610» en
  el modal trae el texto agregado); no se sumó un caso de e2e dedicado — es contenido, no
  lógica nueva, mismo criterio que las otras 21 leyes ya cargadas, ninguna con test propio.
- **Vista mostrador simplificada**: sólo lo que hay que responderle al afiliado.
- ~~**Navegación «volver» dentro de la ficha**~~ **ya está construida** (revisado el
  25/8/2026, no hace falta tocarla): `navPila` en `web/index.html` apila el código anterior
  sólo cuando el salto sale de **adentro** de una ficha abierta (`data-goto` con
  `origen==='ficha'`; entrar desde el listado, la búsqueda, la paleta o el comparador
  siempre empieza un recorrido nuevo). El botón «← Volver a…» (`#dBack`) muestra el código
  y nombre anterior y llama a `atrasFicha()`, que hace `pop()` de la pila — soporta cadenas
  de varios saltos (A → B → C → volver a B → volver a A), no sólo un nivel. Este apartado del
  HANDOFF había quedado desactualizado: la función se construyó en `3bb720a` (ver 7, tanda
  «De archivo suelto a aplicación de empresa») y nadie tachó el pendiente.
- **Buscador por droga** para autorizaciones de medicación (121 drogas / 22 patologías
  SURGE ya parseadas).
- **U.B. por fecha / por convenio** (hoy hay un solo valor por perfil).
- **Auditoría de facturación por lote**.
- **App instalable (PWA) + offline total** (manifest + service worker) — instalable y
  navegar el manual sin internet **ya andan** (4.4 quater); un corte de señal momentáneo al
  guardar **ya se reintenta solo** (ver el bloque del 26/8/2026, después de «Historial por
  ficha»). Lo que sigue pendiente, a propósito no construido todavía —el usuario decidió
  dejarlo así por ahora—: una cola de cambios que persista mientras no hay conexión por un
  rato **largo** (cargar en el campo, sin señal, y sincronizar todo al volver).
- **Registro de decisiones / historial de casos** vía Supabase (trazabilidad y estadística).
- **Novedades normativas / vigencias**.
- **Chat de consulta con IA**: se conversó, no se decidió. ⚠️ Incompatible con el requisito
  de funcionar **offline y sin servidor** salvo que se acepte una dependencia externa.
- ✅ **Capítulo 43 (Prestaciones Sanatoriales) del barrido de «galenos sin cargar» —
  terminado el 27/8/2026, continuación de la sesión del 26/8/2026** (`35 códigos PMO con
  «checksum no cierra»`, bloque de arriba). Contexto: de los 679 códigos PMO detectados
  sin `valores.galeno`, 35 (checksum que no cerraba) y 3 más (hallados por el usuario)
  ya se habían corregido; quedaban **641**, capítulo por capítulo, y el usuario indicó
  dónde había quedado la sesión anterior: **capítulo 43, páginas 146-148** (del recorte
  de `scripts/paginas_nn.py`; páginas impresas 136-140 del PDF).
  ⚠️ **`scripts/paginas_nn.py` no sirve para esto**: recorta la mitad izquierda de la
  página (código + descripción, para transcribir «Texto retirado por el PMO», ver 3.8) y
  **corta justo antes de las columnas de Honorarios/Gastos/Total** que hacen falta acá.
  Hubo que renderizar la página entera con `pypdfium2` a mano (mismo PDF, sin recorte).
  Ninguna de las tres —`pypdfium2`, `Pillow`, `pymupdf`— estaba instalada en el entorno de
  esta sesión; se instalaron con `pip install` (no quedan persistidas si el contenedor se
  reinicia entre sesiones — dejarlo anotado para no perder tiempo redescubriéndolo).
  El capítulo 43 tiene un formato de columna **más simple que el quirúrgico** (que sí usa
  `assemble.py`/`nn_values.json`, ver 3.8): una sola «Honorarios» (U./$.), sin
  especialista/ayudante/anestesista separados, «Gastos» con sólo una sigla impresa
  (`og`/`up`/`OG`/`UP`, sin cifra) y «Total Práctica» que en los 23 códigos revisados es
  **exactamente igual al $ de Honorarios** (el gasto no suma nada). Corroborados los 23
  contra la página real: **los 23 tenían honorarios impresos** que el extractor por
  posición (`scripts/parse_nn.py`, mismo bug que las 35 anteriores) no había levantado —
  `esp`/`ayu`/`anes`/`gasto` quedaban en `null` en `nn_values.json` (`tipo:"sin_valor"`).
  Corregidos en `data/nn_values.json` (`esp.u`/`esp.p`, `total_p=esp.p`,
  `checksum_ok:true`, `corregido_manualmente:true`, y el **número de página real
  impreso** en vez del `page` de la OCR, que ya se sabía desalineado — ver el bloque de
  las 35) y en `data/nbu_db.json` (`valores.galeno`/`pesos_2002`/`total_2002` y
  `asociaciones_especificas`, mismo formato que arma `assemble.py`, aplicado a mano sobre
  los dos JSON como la vez anterior — no hay intermedios del pipeline completo en el
  scratchpad de esta sesión tampoco). Los otros **3 códigos** del capítulo (`430109`
  «Observación en guardia o piso hasta 8 horas», `431106` «Monitoreo de presión
  endocraneana», `431107` «Oximetría por métodos no invasivos») **ya estaban bien**: el
  original dice «CODIGO AGREGADO POR EL P.M.O.» —no tienen renglón en el Nomenclador
  Nacional— y la ficha ya lo refleja (`auditoria` con «Código agregado por el P.M.O.»,
  sin `valores`); no es un caso pendiente, quedan así a propósito.
  ⚠️ **La columna «Coseguro Hasta»** (50.00 en curaciones y nebulizaciones, `43.02.01`,
  `43.02.02`, `43.04.01`, `43.04.02`) **no se cargó**: no es parte del esquema
  `valores.galeno`/`asociaciones_especificas` que arma `assemble.py`, y agregarla es un
  campo nuevo, no una corrección de este barrido — queda anotado para el usuario, no
  decidido de oficio.
  Publicado con `python3 scripts/inject_db.py` (regenera `web/nbu_db.bin`; no se tocó
  ningún `<script>` de `index.html`, no hizo falta resellar la CSP). Corrida completa de
  los 21 archivos de `tests/e2e/`, sin fallas.
  **Capítulo 43 del barrido: terminado** (0 pendientes reales, los 3 `agregado_pmo` no
  cuentan). **Quedan 618** de los 679 originales, en el resto de los capítulos —
  `34` (127) y `26` (110) concentran casi el 40%, siguen `20` (25), `18` (22), `24` (21),
  `17` (20), `31` (19), `30` (18), `08` (17), `42`/`66` (16 c/u), `21` (15), y el resto
  con menos de 15 cada uno.
  ⚠️ **El capítulo 34 (radiología) es un caso aparte, sin abrir todavía**: los 127
  códigos de ese capítulo que faltan **no tienen ni siquiera la clave `valores` en
  `nbu_db.json`** (no es que el extractor haya fallado con `sin_valor` como en los demás
  — directamente nunca se le corrió `parse_nn.py`/`assemble.py` encima; ese capítulo se
  armó aparte con `altas_pmo_cap34.py`/`parse_pmo_titulos.py`, ver 3.4). Antes de tratarlo
  igual que los demás —capítulo por capítulo, leyendo la página real— conviene confirmar
  con el usuario si la radiología se arancela con el mismo esquema de galenos o con otro
  (tope, unidad bioquímica, etc. — HANDOFF ya documenta 38 códigos con «tope PMO» en la
  sección 1), para no forzarle un campo que no le corresponde.
  ⚠️ **CORRECCIÓN, misma sesión, minutos después: los 23 valores estaban bien en el
  monto, mal clasificados.** Apareció el PR #58 (`claude/interprete-orden-busqueda-oe7bf9`,
  commit `e1d0d4b`) — otra sesión, la misma del bloque de los 35+3 códigos, que sí llegó a
  commitear su barrido de ~65 páginas (capítulos 14 a 44, ~500 códigos) antes de este
  cierre. Se superpone exactamente con este capítulo 43. Cruzando los 23 códigos: **el
  total práctica coincide en los 23**, pero el PR #58 carga el monto bajo `galeno.gasto`
  y acá había quedado bajo `galeno.especialista`. Revisando la página impresa de nuevo con
  más cuidado (recorte a la altura de fila, no toda la columna): el orden real es
  `U./$ (etiqueta) → OG/UP (categoría) → número → Total` — el número aparece **después**
  de la sigla de categoría, en la posición de Gastos, no pegado a la etiqueta `U./$` como
  se había asumido. Con `430109` («sin honorario de especialista» explícito en el capítulo
  34, código ajeno usado como referencia) se confirmó el patrón. Semánticamente también
  cierra mejor: cama de sanatorio, material descartable, oxígeno son gasto de la
  institución, no honorario médico.
  Corregido `especialista→gasto` en `data/nn_values.json` (`esp`↔`gasto`, mismos números)
  y `data/nbu_db.json` (`valores.galeno.gasto`/`pesos_2002.gasto`,
  `asociaciones_especificas` reescrito a «Gasto: N galenos.»), y sumado
  `valores.coseguro_hasta` a los 4 códigos que lo traen impreso (`430201`, `430202`,
  `430401`, `430402`, los 50.00 que en el bloque anterior habían quedado sin cargar) —
  mismo campo que ya usa el PR #58, para no divergir del esquema que va a terminar siendo
  el de todo el barrido. Verificado campo por campo contra el `nbu_db.json` del PR #58:
  **los 23 coinciden exactamente** (`galeno`, `pesos_2002` y `coseguro_hasta` iguales).
  Publicado de nuevo con `scripts/inject_db.py`; corrida completa de los 21 archivos de
  `tests/e2e/` (acá y también sobre la rama del PR #58, por separado), sin fallas en
  ninguna de las dos.
  **Pendiente para el usuario**: decidir qué hacer con el PR #58 en sí (mergearlo,
  pedir revisión, etc.) — este bloque sólo corrige la rama propia para que no quede un
  dato mal clasificado dando vueltas mientras tanto.
- ✅ **PR #58 mergeado — capítulos 01 a 13 del barrido de «galenos sin cargar»,
  terminados el 27/8/2026, misma sesión.** El usuario mergeó el PR #58 a
  `claude/unified-medical-codes-manual-o9nw1w` (commit `cf1a1c7`). Traído a esta rama con
  un merge real (no reset): `data/nn_values.json` no tuvo conflicto (el PR #58 nunca lo
  toca), `data/nbu_db.json`/`web/nbu_db.bin` sí —resueltos tomando la versión de origin
  entera, verificado antes campo por campo que es un superset exacto de los 23 códigos
  del capítulo 43 corregidos acá (0 diferencias, 0 regresiones)—. Quedaban **618 → 214**
  códigos PMO sin `valores.galeno` después del PR #58 (los otros 4 capítulos con formato
  «Prácticas Especializadas» que también corrigió, más lo que ya traía el capítulo 43).
  De esos 214, se completó **capítulo por capítulo el rango 01-13** (el formato clásico
  «P.M.O. de Intervenciones Quirúrgicas» — Especialista/Ayudantes/Anestesista/Gasto/Total—
  que si entiende `scripts/parse_nn.py`/`assemble.py`, a diferencia del rango 14-44 que
  arregló el PR #58): **92 códigos**, leídos página por página contra el PDF real
  (`pypdfium2`, páginas de archivo 14 a 83), con el mismo método y la misma validación por
  checksum de siempre. De esos 92:
  - **16 con valor real** que el extractor no había levantado (mismo bug de fila
    contaminada de siempre): la mayoría **I/C** (honorario del especialista incluido en
    la consulta médica, marcado así en la fuente — no se factura aparte) con sólo un
    gasto fijo detrás (`010309`, `010409`, `010508`, `010606`, `020104`, `020405`,
    `030203`, `050408`, `050411`, `080212`, `090107`, `100209`, `130115`, todos con
    `esp:null`+`gasto` real); dos con especialista propio sin I/C (`121509`, `121714`); y
    **`101010`** («Plastia unión ureteropiélica»), un caso aparte: la fuente dice
    literalmente «ídem al código 10.01.10», así que se copió el valor de `100110` en vez
    de inventar uno.
  - **76 confirmados «Código agregado por el P.M.O.»** — mayoría en capítulos enteros de
    prácticas modernas que el Nomenclador Nacional de 1991/2002 no podía tener
    (angioplastia con stent, trasplantes, cirugía laparoscópica/videoscópica,
    artroscopia, desfibrilador implantable — capítulos **07 y 08 salieron 100% así**,
    ninguno con valor real). Ya estaban bien en la base (sin `valores`, correctamente
    fuera del cálculo), pero con un `valor.arancel` genérico que no explicaba por qué
    —igual al bug que ya se había visto en la sesión de las 35—; se les puso el mismo
    texto explícito que usa el PR #58 («Código agregado por el P.M.O.: no está en el
    Nomenclador Nacional de Prestaciones Médicas, no tiene valorización en galenos.»)
    para no dejarlo en ambiguo.
  ⚠️ **La columna «Coseguro Hasta»** vuelve a aparecer suelta en curaciones/nebulizaciones
  de varios capítulos (mismo caso que el capítulo 43) y **no se cargó** por la misma razón
  de antes: no es parte de este esquema, es un campo nuevo a decidir con el usuario, no
  a agregar de oficio.
  Publicado por tandas con `python3 scripts/inject_db.py`; corrida completa de los 21
  archivos de `tests/e2e/` después de cada tanda (capítulos 01+02+03+05+06, luego 07+08,
  luego 09+10+11+12+13), sin fallas en ninguna.
  **Quedan 198** códigos PMO sin `valores.galeno`, y **del rango 01-13 ya no queda
  ninguno pendiente de revisar** — los `08`→16 y `07`→14 que todavía figuran en el
  conteo (junto con el resto de capítulos de ese rango) son exactamente los códigos
  recién confirmados `agregado_pmo` de este mismo bloque, no un caso abierto: siguen
  «sin galeno» porque por diseño un `agregado_pmo` no lleva ese campo, no porque falte
  revisarlos. Todo lo que queda por mirar es **capítulo 66 en adelante y 14 a 44**,
  donde el PR #58 no llegó a cerrar todo: `66`→16, `34`→13, `18`→9, `42`→9, `24`→8,
  `26`→8, `35`→7, `20`→6, `17`/`29`/`33`→5 c/u, `28`/`30`/`36`→4 c/u,
  `22`/`27`/`31`/`43`→3 c/u, y el resto con 2 o menos — todo en formato «Prácticas
  Especializadas» (Honorarios/Gastos/Total/Coseguro), el mismo trabajo que hizo el PR
  #58, sin pasar por `nn_values.json`.

### Lo que queda por confirmar en los datos
- **84 títulos «denominación a confirmar»** (`titulo_revisar`): ninguna fuente los resuelve
  sin ambigüedad. Se corrigen desde **✎ Editar ficha** y vuelven al repo por 3.1.
- **139 fichas con el texto cortado en el origen** (`texto_truncado`): la planilla del Único
  capa las descripciones a **100 caracteres**. No es recuperable desde el PDF del PMO (trae
  títulos aún más cortos). Haría falta una planilla sin el capado.
- ✅ **RESUELTO (18/8/2026): las 135 equivalencias sin destino posible, revisadas a
  mano por el usuario contra la fuente** (planilla `equivalencias_unico_sin_destino.ods`,
  subida por el usuario). 95 quedaron **verificadas correctas** — la equivalencia es real,
  sólo falta que se importe el capítulo/código de destino; siguen con
  `equivalencia.destino_inexistente=true` a propósito, para que `reparar_equivalencias.py`
  las ate solas apenas ese código exista. 39 quedaron **descartadas** — el código que había
  declarado el emparejador automático no correspondía: se les sacó la equivalencia
  (`sin_equivalencia=true`). Aplicado con `scripts/descartar_equivalencias_invalidas.py`
  sobre `data/equivalencias_sin_destino_revisadas.json` (la fuente curada, con las 135 filas
  y su veredicto).
  ⚠️ **La última (`U210208`) tenía el destino mal declarado, no inexistente**: la planilla
  apuntaba a PMO `220209`, que nunca existió — es un error de renumeración del emparejador
  automático. La sesión de esta revisión la encontró y la corrigió a mano (código real:
  `210208`, verificado contra la página 101, ya releída para el capítulo 22); la sesión en
  paralelo que hacía el capítulo 21 encontró el **mismo bug por su cuenta**, casi al mismo
  tiempo, y lo resolvió por el camino correcto —`scripts/equivalencias_renumeradas.py`,
  el mecanismo que ya existía para esto—. Al fusionar las dos ramas quedó esa versión, que
  es la que corresponde: ver 4.5 undecies para el detalle completo y el porqué.
  ⚠️ **Bug de UI encontrado y corregido en el mismo lote**: el listado del Único mostraba
  «≡ código» en la esquina del valor para *cualquier* equivalencia declarada, resuelta o no
  — así que las 135 con destino inexistente se veían como un link válido, y el usuario
  buscaba ese código y no encontraba nada. Se sacó ese badge de la esquina y se lo llevó a
  una etiqueta junto al título, **igual que ya se hacía del lado PMO/NBU con «= Único»**: del
  lado Único ahora dice «= Prestaciones Médicas» / «= NBU» (mismo lugar, mismo color) sólo
  cuando la equivalencia es navegable; si está verificada pero pendiente de importar, aparece
  como dato de estado de la base («equiv. sin importar», gris, junto a «valores ✓» y «2024»)
  en vez de mezclarse con las decisiones clínicas/de facturación. La esquina del valor, sin
  equivalencia resuelta, ahora es el mismo «s/valor» genérico que usan los demás casos sin
  cobertura. También se corrigió que el código de «Equivale a» en la ficha se viera
  subrayado/clicable cuando en realidad no tenía destino.
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
- **Una limpieza que rompe otra cosa.** `clean_pmo_name()` le sacaba «Radiología» al arranque
  del nombre: arregla los títulos de sección que se colaron y rompe las prácticas que se
  llaman así. Antes de generalizar una limpieza por lista de palabras, mirar contra qué
  fuente se está limpiando (3.4).
- **Un nombre que no está no es lo mismo que un nombre truncado.** Las exposiciones
  subsiguientes del capítulo 34 no estaban mal escritas: faltaban, porque el catálogo del
  PMO no las imprime. Cuando el usuario dice «faltan», medir si están antes de arreglar
  cómo se ven.
- **No componer denominaciones.** Se probó llamar al `340210` «radiología de raquis
  (columna) — por exposición subsiguiente» y está mal: es un código propio, no una variante.
- **`incluido_en` dice lo contrario de «se carga además».** Usar esa relación para el par
  práctica/exposición llevaba a facturar de menos.

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
| **El código QR de la verificación en dos pasos no se mostraba** (pasó en producción el 25/8/2026, sobre el propio administrador), y de paso dejó el alta trabada con «A factor with the friendly name "Administrador" for this user already exists», sin forma de reintentar sin entrar al panel de Supabase | **Causa del QR, encontrada al revisar el formato de la respuesta**: la API de Supabase no manda un *data URI* listo para `<img src>` — manda el **marcado SVG crudo** (`<svg…>…</svg>`). Puesto directo en `src`, eso no es una URL válida y el navegador no puede cargarlo; no tira un error visible, la imagen simplemente no aparece. `qrComoImagen()` (`web/index.html`) lo envuelve en `data:image/svg+xml;charset=utf-8,…` antes de usarlo. No se inyecta el SVG directo por `innerHTML` —podría traer `<script>`—: como imagen, el navegador no ejecuta nada de lo que traiga adentro (misma razón por la que el logo de la empresa tampoco acepta SVG, ver `LOGO_OK`). **Causa del bloqueo posterior**: al no verse el QR, el reintento dejaba un factor **sin verificar** cargado del lado del servidor, y Supabase no deja crear otro con el mismo nombre mientras exista uno, verificado o no. `NUBE.enrolarTOTP()` ahora **borra los factores TOTP sin verificar de la cuenta antes de pedir uno nuevo** — sólo los que nunca se verificaron, nunca toca el que está activo de verdad. De paso, la pantalla de alta quedó más robusta ante cualquier otro motivo posible: si la nube no manda ni QR ni secreto avisa en vez de dejar tipear un código contra nada, y si el `<img>` falla igual el secreto manual sigue visible y usable (enganchado con `addEventListener`, no un `onerror="…"` inline — eso lo bloquearía la CSP). Probado con un QR simulado que reproduce el mismo formato crudo (`tests/e2e/simulador.mjs`), verificando que la imagen **carga de verdad** (`img.complete && img.naturalWidth>0`), no sólo que está en el DOM |
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
| **Equivalencia del Único a un código inexistente se mostraba como si fuera un link válido** («≡ código» en la esquina del valor, para toda equivalencia declarada, resuelta o no) | Se sacó ese badge de la esquina; la info se movió a una etiqueta junto al título, igual que «= Único» del lado PMO/NBU (18/8/2026, ver 8) |
| **Editar `index.html` y correr Playwright da `Refused to execute inline script` (CSP)** | La política fija la huella sha256 de cada `<script>`; cualquier edición al inline la corre. `python3 scripts/sellar_csp.py web/index.html` **después** de cada cambio y antes de probar |
| **Playwright: `page.fill('#nbMail', …)` se queda vacío** (la pantalla de login muestra «Completá correo y contraseña» después de loguear) | Carrera: el gate se re-renderiza una vez más justo después de que desaparece `#boot`, y ese re-render pisa lo que ya se había tipeado. Esperar ~800 ms después de que `#boot` se va, antes de llenar el formulario |

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
