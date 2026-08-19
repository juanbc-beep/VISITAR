# Poner el manual a disposición de todo el equipo

Guía para el administrador. Se hace **una sola vez**. Después, cada persona
sólo entra a una dirección y le da a «Instalar».

No hace falta saber programar. Sí hace falta seguir los pasos en orden.

---

## Qué vamos a armar

| Pieza | Para qué | Costo |
|---|---|---|
| **GitHub Pages** | Sirve la app en una dirección con `https://`, obligatorio para que se pueda instalar como aplicación de escritorio | gratis |
| **Supabase** | La base compartida: cuentas, aprobaciones y correcciones. Es lo que hace que un alta hecha en una computadora te llegue a vos | gratis hasta 50.000 usuarios activos por mes |

El catálogo de códigos **no** va a la base: viaja dentro del propio archivo de la
app, así funciona sin internet.

---

## Parte 1 — La base de datos (15 minutos)

### 1.1 Crear el proyecto

1. Entrá a **supabase.com** → **Start your project** → creá la cuenta.
2. **New project**. Ponele de nombre `manual-nbu`.
3. Elegí una contraseña de base de datos y **guardala** (no la vas a usar día a día,
   pero si la perdés no se recupera).
4. En **Region** elegí **South America (São Paulo)**: es la más cercana a Argentina.
5. Esperá a que termine de crearse (tarda un par de minutos).

### 1.2 Crear las tablas

1. Menú izquierdo → **SQL Editor** → **New query**.
2. Abrí el archivo [`docs/supabase.sql`](supabase.sql) de este repositorio,
   copiá **todo** el contenido y pegalo.
3. **Run**. Tiene que decir *Success*.

Eso crea las tablas, y sobre todo las **reglas de acceso**: una cuenta sin aprobar
no puede leer nada del equipo, y nadie puede darse permisos a sí mismo aunque
manipule la aplicación desde su navegador. Esas reglas las hace cumplir la base,
no la app.

> **Si tu base ya estaba andando de antes**, corré además
> [`docs/supabase_seguridad.sql`](supabase_seguridad.sql), una sola vez y del
> mismo modo. Cierra seis huecos en esas reglas —entre ellos una tabla que se
> había quedado sin protección y la transferencia de administración, que dejaba
> la base sin ningún administrador—. No borra datos y se puede correr de nuevo
> sin romper nada. En una instalación desde cero no hace falta: `supabase.sql`
> ya lo trae incorporado.

### 1.3 Apagar la confirmación por correo

Como la aprobación la hacés vos a mano, pedir además una confirmación por mail es
un paso de más que sólo trae problemas.

1. **Authentication** → **Sign In / Providers** → **Email**.
2. Desactivá **Confirm email**. Guardá.

### 1.3 bis Decirle a Supabase cuál es la dirección de la app

**Sin este paso, el enlace para restablecer la contraseña lleva a `localhost` y
el navegador contesta «No se puede acceder».** Supabase viene apuntando a una
dirección de desarrollo y hay que corregirla.

1. **Authentication** → **URL Configuration**.
2. En **Site URL** poné exactamente:

```
https://juanbc-beep.github.io/VISITAR/
```

3. En **Redirect URLs** → **Add URL**, agregá la misma dirección.

### 1.4 Copiar la dirección del proyecto y la clave pública

Son **dos** valores y Supabase los tiene en **dos pantallas distintas**:

| Qué copiar | Dónde está | Cómo se ve |
|---|---|---|
| **Project URL** | **Settings** → **Data API**, arriba de todo | `https://abcdefghijklmnop.supabase.co` |
| **Clave pública** | **Settings** → **API Keys** | `sb_publishable_…` o `eyJhbGciOi…` |

**El atajo:** el botón **Connect**, en la barra de arriba del proyecto, te muestra
los dos juntos. En la solapa *App Frameworks* aparecen así:

```
NEXT_PUBLIC_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
```

Los nombres en mayúsculas son de otro framework: ignoralos y copiá lo que va
después de cada `=`.

**Si el menú cambió de lugar**, la URL se puede deducir sin buscarla. Mirá la
barra de direcciones estando dentro del proyecto:

```
https://supabase.com/dashboard/project/abcdefghijklmnop
                                       └─── tu identificador ───┘
```

Ese código es tu proyecto, y la URL es `https://` + ese código + `.supabase.co`.

> **Sobre el nombre de la clave:** Supabase la renombró. Los proyectos viejos la
> muestran como **anon public** (arranca con `eyJhbGciOi…`) y los nuevos como
> **Publishable key** (arranca con `sb_publishable_…`). **Las dos funcionan igual
> en la app**: copiá la que te muestre tu proyecto.

> **Sobre que sea pública:** esa clave **es pública a propósito** y va a quedar en
> el repositorio. No es un descuido: lo que protege los datos son las reglas del
> paso 1.2, no esconder la clave. La otra, la **service_role** (o *secret key*),
> **no se usa acá y no debe salir nunca del panel de Supabase**.

---

## Parte 2 — Pegar las claves en la app (2 minutos)

1. En este repositorio, abrí **`web/index.html`**.
2. Cerca del principio vas a ver este bloque:

```js
window.NBU_NUBE = {
  url:  "",   // https://xxxxxxxx.supabase.co
  anon: ""    // sb_publishable_...  (o la anon key: eyJhbGciOiJIUzI1NiIs...)
};
```

3. Completá los dos valores con lo que copiaste en 1.4:

```js
window.NBU_NUBE = {
  url:  "https://abcdefghijklmnop.supabase.co",
  anon: "sb_publishable_A1b2C3d4E5f6G7h8"
};
```

Pegalos **entre las comillas**, sin espacios de más y sin barra al final de la URL.

4. Guardá el cambio (**Commit changes**).

Si estos dos campos quedan vacíos la app igual funciona, pero en **modo local**:
cada computadora con sus propios datos, sin compartir nada. Es el modo con el que
venías trabajando.

---

## Parte 3 — Publicar la app (5 minutos)

> **Obligatorio antes de la primera publicación.** Sin esto el despliegue falla
> con *«Get Pages site failed»*. **No se puede automatizar**: crear el sitio pide
> permisos de administrador del repositorio, y el token de las acciones no los
> tiene nunca (contesta *«Resource not accessible by integration»*).

1. Entrá a **`https://github.com/juanbc-beep/VISITAR/settings/pages`**
   *(o: repositorio → **Settings** → **Pages** en el menú izquierdo).*
2. En **Build and deployment** → **Source**, elegí **GitHub Actions**.
   Se guarda solo; no hay botón *Save*.

Se hace **una sola vez**. La dirección va a ser:

```
https://juanbc-beep.github.io/VISITAR/
```

### Cómo se publica una versión

**Se publica sola.** Cada vez que cambia la app, la acción corre y en un minuto la
versión nueva está en línea; a cada persona le aparece el cartel «Hay una versión
nueva del manual», que se actualiza cuando ella lo decide.

Sólo dispara cuando cambia lo que el equipo efectivamente ve — la carpeta `web/` o
la propia acción. Un cambio en `docs/` o en `scripts/` no publica nada, así que no
llegan correos por trabajo interno.

**También se puede publicar a mano**, por ejemplo para reponer una versión sin
haber tocado nada:

1. Pestaña **Actions** → **Publicar el manual** (menú izquierdo).
2. Botón **Run workflow** → **Run workflow**.

Si en algún momento querés volver al modo manual, comentá el bloque `push:` de
`.github/workflows/pages.yml`.

---

## Parte 4 — Crear tu cuenta de administrador (3 minutos)

El sistema no tiene un administrador de fábrica: **la primera cuenta también nace
pendiente**, y hay que habilitarla a mano una única vez.

1. Entrá a la dirección de la app.
2. Vas a ver **Entrar al manual**. Abajo, el enlace
   **«No tengo cuenta todavía → crearla»**.
3. Completá **nombre y apellido**, **correo** y **contraseña** (mínimo 6),
   repetila, y **Crear mi cuenta**.
4. Aparece: *«Tu cuenta … quedó pendiente de aprobación»*. **Es lo esperado**, no
   es un error. Dejá esa pantalla y seguí.
5. Volvé a Supabase → **SQL Editor** → **New query**, y corré esto **cambiando el
   correo por el que acabás de usar**:

```sql
select public.hacerme_admin('vos@visitar.com.ar');
```

   Tiene que contestar: *«Listo: … quedó como administrador activo»*. Si dice que
   no encuentra la cuenta, es que el correo no coincide con el del alta.

6. Volvé a la app, **Volver al inicio**, y entrá con ese correo y contraseña. Ya
   sos el administrador.

> **Por qué una función y no un `update` a mano.** El `update` directo **no
> funciona**, y lo peor es que *parece* funcionar: la consola contesta
> `Success / UPDATE 1` y la cuenta sigue pendiente. Es el guardia
> anti-autopromoción haciendo su trabajo — en el SQL Editor no hay sesión
> iniciada, así que para la base «no sos» el administrador y te revierte los dos
> campos. `hacerme_admin()` levanta el guardia sólo durante esa transacción, y no
> se la puede llamar desde el navegador: las cuentas de la app no tienen permiso.

**Esto se hace una sola vez.** De acá en adelante todas las altas las aprobás
desde la app.

---

## Parte 5 — Que la instale el equipo

Mandales esto:

> **Manual Inteligente NBU**
>
> 1. Abrí https://juanbc-beep.github.io/VISITAR/ en Chrome o Edge.
> 2. Va a aparecer abajo un cartel **«Instalar»**. Tocalo.
>    (Si no aparece: el ícono ⊕ en la barra de direcciones, o menú ⋮ →
>    *Instalar Manual NBU*.)
> 3. Queda como cualquier programa: ícono propio, ventana propia, y **abre sin
>    internet**.
> 4. La primera vez, **Crear mi cuenta** con tu correo de trabajo.
> 5. Avisá que la creaste: hasta que la aprueben no vas a poder entrar.

---

## Cómo se usa a partir de acá

### Aprobar una cuenta
Cuando alguien se da de alta, en tu barra superior aparece el botón de
**pendientes** con el número. Lo tocás y se abre directo en **Perfiles**:
**Aprobar** o **Rechazar**. Recién ahí esa persona puede entrar.

El aviso se refresca solo cada dos minutos y cada vez que abrís el panel, así que
no hace falta recargar nada.

### Actualizar el manual para todos
Cuando se publica una versión nueva de la app, a cada persona le aparece un cartel
**«Hay una versión nueva del manual — Actualizar»**. No se reinicia sola: se
actualiza cuando la persona lo decide, para que no se le corte una consulta con un
afiliado enfrente.

### Favoritos del equipo
Cada persona tiene sus favoritos y nadie se los toca. Aparte hay una **lista del
equipo**, que armás vos: marcá los códigos que más se usan y tocá **Publicar los
míos** en la solapa **👥 Del equipo** de los accesos rápidos.

Es opcional para cada uno: la solapa está al lado de «★ Frecuentes» y se mira
cuando conviene. Sirve sobre todo para que quien recién entra no arranque con la
pantalla vacía.

### Observaciones sobre una práctica
Cuando algo hay que saberlo **antes de cargar** —«esta obra social la está
rechazando», «pedir la orden con el diagnóstico escrito»— lo dejás anotado en la
propia ficha: **Observación del administrador → Dejar una observación**.

Desde ese momento:

- aparece **en el resultado de la búsqueda**, debajo del código, sin que nadie
  tenga que abrir la ficha;
- a cada administrativo le suena una **campanita** en la barra superior con
  cuántas hay nuevas **para él**, y se apaga cuando las lee;
- la escribís, la cambiás o la quitás cuando la situación cambia.

Sólo vos podés escribirlas. El resto las lee.

### Verificaciones y propuestas
Un administrativo puede **pedir que se verifique** una ficha y **proponer cómo se
carga** una práctica. Las dos cosas quedan pendientes hasta que las aprobás vos,
desde **Pendientes**. Al aprobar una propuesta, el texto se publica en la ficha y
le llega a todo el equipo enseguida.

Quién puede hacer qué lo hace cumplir la base, no la aplicación: aunque alguien
manipule la app desde su navegador, no puede validar su propia verificación,
aprobar su propia propuesta ni corregir una ficha si no es administrador.

### Cambiar de administrador
**Administración → Perfiles → Transferir administración**. Hay **uno solo**: al
transferirlo, vos dejás de serlo. Al administrador no se lo puede eliminar sin
transferir primero el rol.

### Contraseñas
Las maneja Supabase y **nadie puede verlas**, ni vos.

Si alguien la olvida, **lo resuelve solo**: en la pantalla de ingreso, **Me
olvidé la contraseña** → pone su correo → le llega un enlace → elige una nueva.
El enlace dura una hora y sirve una sola vez. No tenés que intervenir.

Para que eso funcione tiene que estar hecho el paso **1.3 bis**; si no, el
enlace lleva a `localhost` y no abre nada.

---

## Si perdés el acceso

Hay tres pérdidas posibles y son de gravedad muy distinta. Conviene saber cuál
te tocó antes de buscar la salida.

### 1. Olvidaste tu contraseña de la app

Sin drama. **Me olvidé la contraseña** en la pantalla de ingreso, como cualquier
otra persona del equipo. Ver *Contraseñas*, más arriba.

### 2. Tu cuenta dejó de ser administradora

Pasa si transferiste la administración por error, o si algo quedó a medias. La
app no tiene salida para esto a propósito —si la tuviera, cualquiera podría
usarla—, así que se arregla desde el panel de Supabase:

1. **SQL Editor** → **New query**
2. `select public.hacerme_admin('tu@correo.com');`

Esa función está revocada para las cuentas de la app justamente para que esta
puerta exista y no se pueda abrir desde un navegador. Si ya hay otro
administrador activo, la función se niega: primero hay que transferir desde la
app.

### 3. Perdiste el acceso al panel de Supabase

**Acá no hay salida técnica.** Los datos siguen existiendo y la app sigue
funcionando para quien ya entró, pero nadie puede aprobar una cuenta nueva,
publicar una corrección ni arreglar nada.

Por eso el punto que de verdad protege el manual no es una regla de la base: es
que puedas volver a entrar a Supabase y a GitHub.

## Las llaves maestras

Dos cuentas mandan sobre todo lo demás. **GitHub** publica la app que usa el
equipo; **Supabase** guarda y gobierna los datos. Cualquiera de las dos, en
manos ajenas, vuelve irrelevante todo el resto.

Las dos tienen que tener **verificación en dos pasos con app de autenticación**,
no por SMS: un número de teléfono se puede portar, y con eso se pierde la
cuenta. Al activarla, cada una entrega **códigos de recuperación**.

Dónde vive cada cosa:

| Qué | Dónde |
|---|---|
| Contraseñas de GitHub y Supabase | Gestor de contraseñas |
| Códigos de recuperación de las dos | Gestor de contraseñas |
| **Lo que recupera el gestor mismo** | **Impreso, en un lugar físico** |

La última fila es la que se olvida y la única que importa cuando algo sale mal.
Si los códigos de recuperación están en el gestor, y el gestor pide el mismo
teléfono que tiene la app de autenticación, entonces perder el teléfono te deja
afuera de todo a la vez. La cadena tiene que terminar en algo que no dependa de
ningún dispositivo: la *Emergency Kit* de 1Password, el master password de
Bitwarden, lo que corresponda al gestor que uses. Una hoja, guardada donde
guardarías una escritura.

## Una sola persona

Hoy la administración del manual depende de una sola persona. No es un problema
de seguridad —nadie entra por ahí— pero sí de continuidad: si esa persona no
está disponible por un tiempo, el manual sigue consultándose con normalidad y
deja de poder actualizarse.

Lo más barato que lo cubre, sin sumar a nadie a las cuentas: un sobre cerrado
con lo necesario para recuperar el gestor de contraseñas, en manos de alguien de
confianza de la empresa o en la caja de seguridad de la sociedad, con la
instrucción de abrirlo sólo llegado el caso. No da acceso a nadie hoy y evita
que el manual quede huérfano.

Si algún día hay una segunda persona técnica, la forma prolija es invitarla como
miembro de la organización en Supabase y como colaboradora en GitHub. El rol de
`admin` **dentro de la app** sigue siendo uno solo por diseño, y eso no cambia:
son cosas distintas.

---

## Qué se comparte y qué no

| Dato | Dónde vive |
|---|---|
| Cuentas, roles, aprobaciones | Base compartida |
| Favoritos del equipo (lista común) | Base compartida, la publica el administrador |
| Favoritos, notas personales, valor de U.B. | Base compartida, atados a tu cuenta: los tenés igual desde cualquier computadora |
| Catálogo de códigos, CIE-10, SURGE, abreviaturas | Dentro del archivo de la app |
| Correcciones de ficha, verificaciones y propuestas | Base compartida: lo que corrige o verifica uno lo ve el resto al entrar |
| Observaciones del administrador por práctica | Base compartida; cada persona tiene su propia marca de «hasta acá las vi» |
| Registro de actividad (pestaña **Registro**) | Sólo en cada computadora: es el rastro de lo que se hizo desde ahí |

---

## Si algo no funciona

| Síntoma | Causa habitual |
|---|---|
| «Sin conexión con la nube de la empresa» | Las claves del paso 2 están mal pegadas (fijate que la URL no tenga barra al final ni espacios), o el proyecto de Supabase está pausado (se pausa solo tras una semana sin uso; se reactiva desde el panel) |
| No encontrás la Project URL en el panel | **Settings → Data API** (las claves están aparte, en **Settings → API Keys**). El botón **Connect** de la barra superior te da las dos juntas. Y siempre podés leerla de la barra de direcciones: ver 1.4. Es única de tu proyecto: nadie te la puede pasar |
| Se creó la cuenta pero no aparece en Perfiles | Falta correr el SQL del paso 1.2, o tu cuenta no quedó como `admin` (paso 4.5) |
| Corriste el `update … set rol='admin'` y seguís entrando como pendiente | Ese `update` no sirve aunque diga *Success*: lo revierte el guardia. Usá `select public.hacerme_admin('tu@correo');` (paso 4.5) |
| `hacerme_admin` dice que ya hay un administrador activo | Hay uno solo. Se cambia desde la app: **Administración → Perfiles → Transferir administración** |
| No aparece el cartel de «Instalar» | Sólo aparece en Chrome, Edge o navegadores derivados, y sólo con `https://`. En Firefox la app funciona igual pero no se instala |
| «Falta confirmar esta cuenta por correo», con la cuenta **ya aprobada** | Son dos puertas distintas: aprobar cambia `perfiles.estado`, pero Supabase además exige `email_confirmed_at`. Apagá *Confirm email* (paso 1.3) **y** confirmá a mano las cuentas ya creadas: **Authentication → Users → `⋯` → Confirm email**, o `update auth.users set email_confirmed_at = now() where email = '…';` |
| Volviste a encender **Enable Email provider** y reaparecieron los correos de confirmación | *Confirm email* se enciende junto con el proveedor: viene activado de fábrica. Hay que volver a apagarlo |
| Al crear la cuenta: **«Unexpected failure, please check server logs»** | Es un error 500 de Supabase Auth: se cayó el trigger de alta. Corré de nuevo `docs/supabase.sql` completo — las versiones anteriores del archivo tenían el control de «un solo admin» sin `security definer` y fallaba con *permission denied* justo al confirmar el alta |
| Los cambios no llegan al equipo | Fijate en **Actions** si la última corrida salió verde. Si el cambio fue fuera de `web/`, no publica a propósito: forzalo con **Run workflow** |
| El enlace del correo para restablecer la contraseña lleva a `localhost` | Falta el paso **1.3 bis**: **Authentication → URL Configuration → Site URL** tiene que ser la dirección de la app, no `localhost` |
| «Get Pages site failed» al publicar | La acción no pudo encender Pages sola: hacelo a mano en **Settings → Pages → Source: GitHub Actions** y volvé a correrla |

Para diagnosticar desde adentro de la app: `F12` → consola → escribí
`NBUNube.pendientes()` y presioná Enter. Si contesta con números, la base
responde bien.

---

*Diseñado por Juan Pablo Besada.*
