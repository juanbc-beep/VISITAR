# Pruebas de las reglas de acceso

Lo que protege los datos de este manual no es la aplicación: es RLS, las reglas
de acceso de PostgreSQL que están en `docs/supabase.sql`. La clave publicable es
pública por diseño, así que cualquiera puede hablarle a la base en nombre de su
propia sesión. Lo único que decide qué ve y qué toca cada uno son esas reglas.

El problema de una regla mal escrita es que **no rompe nada visible**. La app
sigue andando igual. El error no se nota hasta que alguien lee algo que no
debería, y para entonces ya pasó. Estas pruebas hacen que se note en el pull
request.

## Qué prueba

**`ataques.sql`** — seis cosas que **no** tienen que poder hacerse. Los seis
funcionaban de verdad antes de la corrección de agosto de 2026: se reprodujeron
contra una base real, no son hipótesis.

| | El ataque |
|---|---|
| CN-001 | Una cuenta sin aprobar lee y borra las observaciones del equipo |
| CN-002 | Transferir la administración deja la base sin ningún administrador |
| CN-003 | Un médico administrador borra una corrección entera |
| CN-004 | Renombrar el código de una corrección la vacía |
| CN-005 | Un usuario activo lee las notas personales y la U.B. de sus compañeros |
| CN-006 | Alguien registra una verificación con la firma de otro |

**`regresion.sql`** — lo que **sí** tiene que seguir andando. Es el contrapeso:
cerrar de más rompe el trabajo del equipo, y eso también tiene que fallar la
build. Que el administrador edite la ficha entera, que el médico administrador
firme lo médico sin pisar la ficha, que una cuenta pendiente siga aislada, que
nadie se ascienda solo.

## Cómo correrlas a mano

Hace falta un PostgreSQL cualquiera. No hace falta Supabase: `entorno.sql`
reproduce las tres cosas de las que dependen las reglas —el esquema `auth` con
`auth.uid()`, los roles `anon` y `authenticated`, y los *default privileges* del
esquema público—.

Ese tercero es el que más importa y el menos obvio. Supabase le da permisos
completos sobre `public` a `anon` y `authenticated`, así que **toda tabla nueva
nace abierta** y lo único que la protege es RLS. Sin eso en el entorno de
prueba, una tabla a la que se le olvidó el `enable row level security` parecería
segura acá y estaría abierta en producción. Fue exactamente lo que pasó con
`observaciones`.

```bash
docker run -d --name pg-test -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
PGPASSWORD=postgres tests/rls/correr.sh
docker rm -f pg-test
```

Corre tres escenarios: instalación desde cero, con la migración de seguridad
encima, y con la migración aplicada dos veces (idempotencia). En los tres pasa
los seis ataques y las pruebas de regresión.

## Si una prueba falla

El mensaje dice qué se pudo hacer y no debería. Por ejemplo:

```
ERROR:  CN-002: tras transferir quedaron 0 administradores activos (ninguno).
        Tiene que quedar exactamente uno.
```

**No arregles la prueba para que pase.** La prueba describe una propiedad que la
base tiene que cumplir; si falla, lo que está mal es el cambio que la rompió.
Si de verdad cambió la regla del negocio —por ejemplo, si algún día el médico
administrador sí tiene que poder borrar correcciones—, actualizá la prueba y
dejá dicho en el commit por qué.

## Agregar una tabla

Si sumás una tabla a `docs/supabase.sql`, acordate de las dos cosas, porque son
independientes y olvidarse de la segunda es el error que ya pasó una vez:

1. `alter table public.<tabla> enable row level security;`
2. sus policies

Y agregá acá una prueba de que una cuenta pendiente no la toca.
