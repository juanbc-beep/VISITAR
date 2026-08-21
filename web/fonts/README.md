# Roboto Condensed / Roboto Mono (auto-hospedadas)

`RobotoCondensed-{Regular,Bold}.woff2` y `RobotoMono-{Regular,Bold}.woff2`,
subconjunto `latin` (cubre acentos y ñ del español), tomados de Google Fonts
(`fonts.googleapis.com/css2?family=Roboto+Condensed` / `Roboto+Mono`).

Se auto-hospedan en vez de cargarse desde Google en cada visita para no
sumar una petición externa a la CSP (`font-src 'self'` se mantiene sin
tocar) ni filtrar la IP del usuario a un tercero en cada carga.

Licencia: Apache License 2.0 (ver LICENSE.txt en esta carpeta), permite
redistribución.
