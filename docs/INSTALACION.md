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

### 1.4 Copiar las dos claves

1. **Project Settings** (el engranaje) → **API**.
2. Anotá:
   - **Project URL** → algo como `https://abcdefgh.supabase.co`
   - **anon public** → una cadena larga que arranca con `eyJ...`

> La clave `anon` **es pública a propósito** y va a quedar en el repositorio.
> No es un descuido: lo que protege los datos son las reglas del paso 1.2, no
> esconder esa clave. La otra clave, la `service_role`, **no se usa acá y no debe
> salir nunca del panel de Supabase**.

---

## Parte 2 — Pegar las claves en la app (2 minutos)

1. En este repositorio, abrí **`web/index.html`**.
2. Cerca del principio vas a ver este bloque:

```js
window.NBU_NUBE = {
  url:  "",   // https://xxxxxxxx.supabase.co
  anon: ""    // eyJhbGciOiJIUzI1NiIs...
};
```

3. Completá los dos valores con lo que copiaste en 1.4:

```js
window.NBU_NUBE = {
  url:  "https://abcdefgh.supabase.co",
  anon: "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
};
```

4. Guardá el cambio (**Commit changes**).

Si estos dos campos quedan vacíos la app igual funciona, pero en **modo local**:
cada computadora con sus propios datos, sin compartir nada. Es el modo con el que
venías trabajando.

---

## Parte 3 — Publicar la app (5 minutos)

1. En el repositorio → **Settings** → **Pages**.
2. En **Source**, elegí **GitHub Actions**.
3. Listo. Cada vez que se suba un cambio a la rama de trabajo, la acción
   *Publicar el manual* deja la versión nueva en línea sola.
4. La dirección va a ser:

```
https://juanbc-beep.github.io/VISITAR/
```

Podés seguir el despliegue en la pestaña **Actions**.

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
| «Sin conexión con la nube de la empresa» | Las claves del paso 2 están mal pegadas, o el proyecto de Supabase está pausado (se pausa solo tras una semana sin uso; se reactiva desde el panel) |
| Se creó la cuenta pero no aparece en Perfiles | Falta correr el SQL del paso 1.2, o tu cuenta no quedó como `admin` (paso 4.4) |
| No aparece el cartel de «Instalar» | Sólo aparece en Chrome, Edge o navegadores derivados, y sólo con `https://`. En Firefox la app funciona igual pero no se instala |
| «La cuenta todavía no está confirmada por correo» | Faltó desactivar *Confirm email* en el paso 1.3 |
| Los cambios no llegan al equipo | Mirá la pestaña **Actions** del repositorio: si la acción falló, ahí dice por qué |

Para diagnosticar desde adentro de la app: `F12` → consola → escribí
`NBUNube.pendientes()` y presioná Enter. Si contesta con números, la base
responde bien.

---

*Diseñado por Juan Pablo Besada.*
