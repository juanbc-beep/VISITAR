#!/usr/bin/env python3
"""Vuelca un resumen legible del reporte JSON de Lighthouse al step summary
de GitHub Actions (o a stdout si se corre a mano).

Por qué existe: la acción de publicación mide performance contra el HTML tal
cual se va a publicar (servido local, no la URL en vivo, para no depender de
que el CDN ya haya propagado el cambio) y es sólo informativo — no bloquea
la publicación. Este script separa "leer el JSON de Lighthouse" de la
receta de CI, así se puede probar en la propia computadora sin tocar nada
del workflow.

Uso:  python3 scripts/lighthouse_resumen.py <reporte.json> [archivo_resumen]
Sin el segundo argumento, imprime a stdout.
"""
import json, sys


def main():
    if len(sys.argv) < 2:
        print("Uso: lighthouse_resumen.py <reporte.json> [archivo_resumen]", file=sys.stderr)
        sys.exit(1)
    reporte = json.load(open(sys.argv[1], encoding="utf-8"))
    cats = reporte.get("categories", {})
    audits = reporte.get("audits", {})

    def puntaje(clave):
        c = cats.get(clave)
        if not c or c.get("score") is None:
            return "—"
        return str(round(c["score"] * 100))

    def metrica(clave):
        a = audits.get(clave)
        return a.get("displayValue", "—") if a else "—"

    lineas = [
        "## Lighthouse — pantalla de acceso (sin autenticar, servida local)",
        "",
        "| Categoría | Puntaje (0-100) |",
        "|---|---|",
        f"| Performance | {puntaje('performance')} |",
        f"| Accesibilidad | {puntaje('accessibility')} |",
        f"| Buenas prácticas | {puntaje('best-practices')} |",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Largest Contentful Paint | {metrica('largest-contentful-paint')} |",
        f"| Total Blocking Time | {metrica('total-blocking-time')} |",
        f"| Cumulative Layout Shift | {metrica('cumulative-layout-shift')} |",
        f"| Speed Index | {metrica('speed-index')} |",
        f"| Time to Interactive | {metrica('interactive')} |",
        "",
        "_Mide sólo la pantalla de acceso: es lo único alcanzable sin credenciales de "
        "Supabase. No bloquea la publicación — es información, no un gate._",
    ]
    salida = "\n".join(lineas) + "\n"
    if len(sys.argv) >= 3 and sys.argv[2]:
        with open(sys.argv[2], "a", encoding="utf-8") as f:
            f.write(salida)
    print(salida)


if __name__ == "__main__":
    main()
