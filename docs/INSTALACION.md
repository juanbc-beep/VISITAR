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

### 1.3 Apagar la confirmación por correo

Como la aprobación la hacés vos a mano, pedir además una confirmación por mail es
un paso de más que sólo trae problemas.

1. **Authentication** → **Sign In / Providers** → **Email**.
2. Desactivá **Confirm email**. Guardá.

### 1.4 Copiar la dirección del proyecto y la clave pública

1. Engranaje **Settings** (abajo a la izquierda) → **API Keys**.
   *(Si no lo encontrás, los mismos datos están en el botón **Connect**, arriba a
   la derecha.)*
2. Anotá los dos valores:

| Qué copiar | Dónde dice | Cómo se ve |
|---|---|---|
| **Project URL** | arriba de todo | `https://abcdefghijklmnop.supabase.co` |
| **Clave pública** | *Publishable key* o *anon public* | `sb_publishable_…` o `eyJhbGciOi…` |

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

> **Este paso es obligatorio antes de publicar.** Si GitHub Pages no está
> habilitado, el despliegue falla con *«Get Pages site failed»* y GitHub manda un
> correo de error por cada intento.

1. En el repositorio → **Settings** → **Pages**.
2. En **Source**, elegí **GitHub Actions**. Guardá.
3. La dirección va a ser:

```
https://juanbc-beep.github.io/VISITAR/
```

### Cómo publicar una versión

La publicación es **manual, a propósito**: así nada se despliega sin que vos lo
decidas y no llegan correos de error por cambios de trabajo.

1. Pestaña **Actions** → **Publicar el manual** (menú izquierdo).
2. Botón **Run workflow** → **Run workflow**.
3. En un minuto la versión nueva está en línea, y a cada persona le aparece el
   cartel «Hay una versión nueva del manual».

Si más adelante preferís que se publique solo en cada cambio, descomentá el bloque
`push:` de `.github/workflows/pages.yml`.

---

## Parte 4 — Crear tu cuenta de administrador (3 minutos)

El sistema no tiene un administrador de fábrica: **la primera cuenta también nace
pendiente**, y hay que habilitarla a mano una única vez.

1. Entrá a la dirección de la app.
2. **No tengo cuenta todavía → crearla**. Poné tu nombre, tu correo de trabajo y
   una contraseña.
3. Va a decir que quedó pendiente. Es lo esperado.
4. Volvé a Supabase → **SQL Editor** → **New query** y corré esto **cambiando el
   correo por el tuyo**:

```sql
update public.perfiles set rol = 'admin', estado = 'activo'
 where id = (select id from auth.users where email = 'vos@visitar.com.ar');
```

5. Volvé a la app y entrá. Ya sos el administrador.

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

### Cambiar de administrador
**Administración → Perfiles → Transferir administración**. Hay **uno solo**: al
transferirlo, vos dejás de serlo. Al administrador no se lo puede eliminar sin
transferir primero el rol.

### Contraseñas
Las maneja Supabase y **nadie puede verlas**, ni vos. Si alguien la olvida:
**Authentication → Users** en Supabase, y desde ahí se envía un restablecimiento.

---

## Qué se comparte y qué no

| Dato | Dónde vive |
|---|---|
| Cuentas, roles, aprobaciones | Base compartida |
| Favoritos, notas personales, valor de U.B. | Base compartida, atados a tu cuenta: los tenés igual desde cualquier computadora |
| Catálogo de códigos, CIE-10, SURGE, abreviaturas | Dentro del archivo de la app |
| **Verificaciones, propuestas y correcciones de ficha** | **Todavía locales.** Las tablas ya existen en la base; falta conectarlas. Mientras tanto siguen viajando con «Exportar correcciones para la base» |

---

## Si algo no funciona

| Síntoma | Causa habitual |
|---|---|
| «Sin conexión con la nube de la empresa» | Las claves del paso 2 están mal pegadas (fijate que la URL no tenga barra al final ni espacios), o el proyecto de Supabase está pausado (se pausa solo tras una semana sin uso; se reactiva desde el panel) |
| No encontrás la Project URL en el panel | **Settings → API Keys**, arriba de todo. También aparece en el botón **Connect** de la barra superior. Es única de tu proyecto: nadie te la puede pasar |
| Se creó la cuenta pero no aparece en Perfiles | Falta correr el SQL del paso 1.2, o tu cuenta no quedó como `admin` (paso 4.4) |
| No aparece el cartel de «Instalar» | Sólo aparece en Chrome, Edge o navegadores derivados, y sólo con `https://`. En Firefox la app funciona igual pero no se instala |
| «La cuenta todavía no está confirmada por correo» | Faltó desactivar *Confirm email* en el paso 1.3 |
| Los cambios no llegan al equipo | La publicación es manual: **Actions → Publicar el manual → Run workflow**. Si la acción falla, ahí dice por qué |
| «Get Pages site failed» al publicar | Falta el paso 3: **Settings → Pages → Source: GitHub Actions** |

Para diagnosticar desde adentro de la app: `F12` → consola → escribí
`NBUNube.pendientes()` y presioná Enter. Si contesta con números, la base
responde bien.

---

*Diseñado por Juan Pablo Besada.*
