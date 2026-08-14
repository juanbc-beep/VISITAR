# TRASPASO DE SESIÓN — Manual Inteligente Unificado (VISITAR SRL)

> Documento para retomar el trabajo en una sesión nueva sobre **la misma app**.
> Última actualización: 2026-08-11 (commit `f6bf67c`, 126 commits).
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
| **Códigos totales** | **6.372** |
| — NBU (laboratorio/bioquímica) | 1.815 |
| — PMO / Prestaciones médicas | 1.247 (26 altas del capítulo 34, ver 3.4) |
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

⚠️ Al aplicarse, `actualizando()` muestra un cartel a pantalla completa —«Actualizando el
manual… no perdés nada de lo que estabas haciendo»— y **espera 450 ms antes de recargar**.
Sin esa pausa la propia recarga lo pisa y el aviso no cumple ninguna función. Antes de esto
la app se reiniciaba sola y sin decir nada, y el administrativo no sabía por qué.

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
| editar la ficha (modo edición) | ✔ | ✗ | ✗ | ✗ |
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
  le revierte `nombre`, `norma`, `auditoria` y `asoc_extra` al valor anterior; **lo único que
  le sobrevive es `datos->'revision_medica'`**. Mismo patrón que `perfiles_guardia`.
- `prop_resolver` — el médico administrador sólo cierra propuestas cuyo **autor es médico**.
- `pendientes()` — sigue devolviendo `json` (nada de cambiarle el tipo de retorno) y suma la
  clave `medicas`. Se le sacó el `where es_admin()` final, que hacía que no devolviera ninguna
  fila a quien no fuera administrador.

Del lado de la app: `ROLES`, `ROL_VALIDO()`, `rolLabel()` y **`CAP`** — todas las capacidades
en un solo objeto. Preguntar `role==='admin'` desparramado por treinta lugares fue lo que hizo
que sumar un rol tocara toda la app; ahora se pregunta `CAP.duenio(p)`, `CAP.validaMedico(p)`,
`CAP.observa(p)`, `CAP.editaFicha(p)`.

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
abrir la ficha llega tarde. Lo tienen **96 códigos de 6.372**, así que no ensucia el listado —
donde aparece, es porque hay algo que saber. Va **antes** de los dos avisos y sin fondo: no es
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
| 12 · Músculo esquelético | 68–80 | 146 | ✅ 64 textos + 3 normas de capítulo + 13 de sub-capítulo |
| 25 · Rehabilitación médica | 111–112 | 6 | ✅ 6 textos + 5 normas |
| los otros 27 | ~18–150 | ~1.000 | pendiente |

Cobertura: **341 de 1.351 (25%)**, desde 156 (11%).

#### ⚠️ Normas de sub-capítulo: `normas_prefijo`

El 12 obligó a agregarlas. `norma` gobierna el capítulo entero; `normas_prefijo` gobierna un
sub-capítulo (`{"1219": [...]}` → todas las fichas que empiezan con `1219`).

**La distinción no es cosmética**: el 12 tiene trece normas de sub-capítulo, y pegarle a los
146 códigos la del 12.01 —«el arancel para el tratamiento no quirúrgico de las fracturas SIN
DESPLAZAMIENTO será el de la confección del yeso»— sería decirle al administrativo que eso
rige para las amputaciones. Verificado después de importar: la amputación `121601` recibió
sólo las 3 normas de capítulo, y el yeso `121901` recibió además la del 12.19.

⚠️ **Cero fichas no es un error.** `12.01` («fracturas sin desplazamiento») no tiene códigos
propios: el PMO lo vació entero. Su norma queda declarada y el script avisa «NINGUNA ficha con
ese prefijo». **No pegarla al 12.02 ni al capítulo** — sería inventarle alcance a una regla
que el nomenclador escribió para otra cosa.

⚠️ **No todos los códigos llevan recuadro.** En el capítulo 01, 33 de 69. Los que no tienen
son los que el Nacional imprime completos en negrita (nada retirado) y los marcados «CODIGO
AGREGADO POR EL P.M.O.», que por definición no están en el Nacional. Que un capítulo quede
con menos textos que códigos es lo normal, no una transcripción a medias.

#### ▶ POR DÓNDE SEGUIR (pausado el 13/8/2026, se retoma el martes 18/8)

`data/paginas_nn.json` tiene **dónde empieza y termina cada capítulo en el PDF**, sacado por
OCR. Ya está: no hay que volver a buscarlo a mano.

    cap 02: 18–23   cap 03: 24–32   cap 04: 33      cap 05: 34–36   cap 06: 37
    cap 07: 38–46   cap 08: 47–55   cap 09: 56      cap 10: 57–63   cap 11: 64–67
    cap 12: 68–80   cap 13: 81–83   cap 14: 88      cap 15: 89      cap 16: 90
    cap 17: 91–94   cap 18: 95–96   cap 20: 97–99   cap 21: 100     cap 22: 101–102
    cap 23: 103–108 cap 24: 109–111 cap 29: 125     cap 30: 126–127 cap 31: 128–129
    cap 33: 130–131

⚠️ El índice llegó hasta la página 139; **faltan 35, 36, 38 y el 66**. Para completarlo:
`scripts/` no lo tiene — está en el scratchpad de la sesión, que se recicla. Se vuelve a sacar
con `rapidocr_onnxruntime` contando códigos `NN.NN.NN` por página (≈9 s por página).

**Receta por capítulo**, unos 10 minutos cada uno:

1. Renderizar las páginas con `pypdfium2` a `scale=2.3` y **leerlas como imagen**.
2. Transcribir los recuadros a `data/alcance_nn_pmo.json` bajo el capítulo, respetando la
   ortografía impresa.
3. `python3 scripts/alcance_nn_pmo.py && python3 scripts/inject_db.py`
4. El script avisa qué códigos del JSON no están en la base y verifica que ningún nombre se
   haya movido.

**Orden sugerido** (por códigos cubiertos por página leída): 12 (146), 08 (123), 03 (118),
10 (82), 07 (82), 11 (49), 13 (30), 20 (25), 24 (21), 17 (20), 31 (19), 30 (18), 18 (22),
02 (51), 05 (23), 29 (14), 22 (13), 33 (13), 15 (12), 06 (12), 04 (11), 09 (8), 21 (14),
16 (5), 19 (3), 14 (1), 32 (1).

⚠️ El **23 (hemoterapia, páginas 103‑108)** sigue esperando decisión clínica: se superpone con
el NBU bajo otra numeración. No transcribirlo sin que los médicos definan.

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

Hoy: **156 códigos con sigla**, de los cuales **56 abren el `.nn-card`** (caps. 26, 27, 28,
40‑44) y **100 traen sólo alcance** (cap. 34). Sobre 6.372, no ensucia el listado.

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

Resultado: **60 reatadas · 8 ya tenían el enlace de vuelta · 153 siguen sin destino en la
base**. Esas 153 apuntan a códigos de capítulos todavía no importados, así que **algunas
fichas siguen sin la vista previa entre nomencladores** — se arreglan solas a medida que
entren los capítulos que faltan, volviendo a correr el script.

⚠️ Correr siempre `python3 scripts/inject_db.py` después.

⚠️ **U.B. vacía no es un error en estos capítulos.** Neumonología, consultas y sanatoriales
se facturan en unidades de honorarios y gastos, no en Unidad Bioquímica: se importaron con
`valor.ub = null` a propósito, y `ubDe()` devuelve `null`. La tarjeta de equivalencia se ve
igual, sin el chip de U.B.

### 4.5 undecies Cinco equivalencias que el Único numeraba distinto

`scripts/equivalencias_renumeradas.py`. En cinco prácticas la planilla del Único dice
«equivale al código NNNNNN», ese número no existe en el Nomenclador Nacional, **y la
práctica sí está en el Nacional con el mismo número que usa el Único**:

| Único | la planilla decía | está en el Nacional como |
|---|---|---|
| 280111 Capacidad pulmonar total y volumen residual | 280207 ✗ | **280111** |
| 280201 Lavado alveolar | 280208 ✗ | **280201** |
| 280301 Ablación de lesiones broncopulmonares | 280209 ✗ | **280301** |
| 260528 Perfusión sanguínea miocárdica | 260729 ✗ | **260528** |
| 430601 Luminoterapia | 431604 ✗ | **430601** |

⚠️ **NO se hace por regla automática «si el número coincide, atalo».** `U430102` coincide en
número y la práctica es otra: el Único dice «cama en habitación individual (aislamiento)» y
el Nacional dice «una cama en habitación de dos con baño». Atarla habría metido un error de
facturación. La lista del script está escrita a mano, código por código, comparando el
nombre de los dos lados.

El número que declaraba la planilla queda guardado en `equivalencia.code_declarado` y en una
línea de auditoría de las dos fichas: un auditor que compare contra el papel se va a
encontrar con ese número y tiene que poder explicárselo.

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

**Después se importaron el 27, el 28 y el 26** — 57 fichas más. Total del rescate: **104**.

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

## 7. Historial de trabajo (126 commits)

**Lo hecho en esta última tanda (2026-08-10 y 11)** — el detalle está en los mensajes de
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

## 7 bis. ▶ AGENDA DEL MARTES 18/8/2026

### A. Seguir con la norma retirada del PMO
Ver 3.8 → «POR DÓNDE SEGUIR». Arrancar por el capítulo **12** (146 códigos, páginas 68‑80).
Faltan las páginas del **35, 36, 38 y 66** en `data/paginas_nn.json`.

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
2. **XSS almacenado por texto que escriben los médicos.** La revisión médica, las
   observaciones y «qué abarca» los escribe una persona y se renderizan en la pantalla de
   otra. Hay 81 usos de `innerHTML`. Se escapa con `esc()` y `csp3.mjs` verifica que la
   inyección se bloquee, pero **falta una auditoría dirigida a esos tres caminos**, sobre todo
   al orden de `linkCodes(esc(t))`.
3. **Segundo factor en la cuenta del administrador general.** Es la cuenta que puede todo; si
   se la toman, no hay segunda línea.
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
8. **Cuánto dura la sesión** de un médico en una máquina compartida.

### C. Decisiones que esperan a los médicos
- **Chagas**: `63663576` (ELISA) está atado al NBU `663576`, que es el **PCR**. Error
  preexistente, no se tocó (4.5 duodecies).
- **Consultas A‑P** del Único (10 filas) — ¿todas a `420101`?
- **Hidatidosis IFI**, **domicilio «más/hasta 2 kms»**, **BCR/ABL LMC vs LLA** — no se ataron.
- **Capítulo 23** (hemoterapia): se superpone con el NBU bajo otra numeración.

### D. Datos que siguen faltando
- **Capítulo 66** (NBU laboratorio) contra el PDF — ahora hay que mirarlo sabiendo lo de los
  bloques repetidos 60‑64 del Único.
- **104 equivalencias** esperan que se importe el capítulo al que apuntan. La más grande:
  **capítulo 16, anestesiología, 33 códigos** en fila.

## 8. Pendientes y sugerencias abiertas

### ⚠️ Lo primero que hay que preguntar al retomar

Lo último que se estuvo trabajando es el **Nomenclador de Prestaciones Médicas**, capítulo
por capítulo, con el usuario reportando y midiendo contra la fuente (ver 3.4 y 3.5). El
siguiente paso natural es **la lista de 159 denominaciones a revisar** (3.5), de a un
capítulo y mostrándole los cambios antes de aplicarlos.

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
| **Segundo factor** en GitHub y Supabase, y **proteger la rama** | del usuario; se le pidió dos veces |
| **Rotar la secret key** de Supabase | del usuario |
| **Cerrar las altas** cuando el equipo esté completo, subir el mínimo de contraseña | del usuario |
| **Las 119 prácticas «fuera del PMO»** que están en nuestra sección PMO | criterio del usuario |
| **Las 113 prácticas del Excel** que no están en la base (comparación de julio) | decisión conjunta |
| **159 denominaciones del PMO a cotejar** con el renglón impreso (3.5) | de a un capítulo, con su visto |
| **17 títulos del capítulo 34 «a confirmar»** y 2 ilegibles (`340803`, `340813`) | del usuario, o de otra planilla |
| **Redacción del aviso «sin confirmar»** en las propuestas visibles al equipo | del usuario (se publicó una versión y ofreció cambiarla) |
| **Volver la base adentro del `index.html`** si prefiere el archivo único (3.0 bis) | del usuario |

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
