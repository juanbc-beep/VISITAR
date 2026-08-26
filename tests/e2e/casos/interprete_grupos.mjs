// Caso "interprete_grupos": el Intérprete de orden agrupa por equivalencia
// entre nomencladores (EQGRUPO) en vez de mostrar una tarjeta entera por
// cada uno. Pedido explícito del usuario a partir de una captura real:
// "radiografia torax f y p" mostraba TRES tarjetas para lo que es una sola
// práctica —340301 del PMO, 340301 del Único (mismo código, dos
// porcentajes distintos: 83% y 50%) y 340302 como candidato aparte para la
// exposición de perfil— y "eso no debería suceder, si es la misma
// práctica". Ahora es un solo bloque: un porcentaje, un chip "también en"
// para elegir el otro nomenclador si hace falta, y la exposición adicional
// como nota con sus propios chips, no una tarjeta más.
//
// Ver web/index.html: candidatosParaItem() (el agrupado por EQGRUPO y el
// `g.comp`/`g.sinPerfil` colgados del grupo) y correrInterprete()
// (grupoBtn(), nomChip()). HANDOFF.md, 26/8/2026.
//
// 340301/U340301 y 340302/U340302 son códigos reales y estables
// (data/nbu_db.json) — el caso exacto de la captura del usuario, no uno
// armado para el test.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8638;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('interprete_grupos: un solo bloque por práctica, con chips para el otro nomenclador y la exposición adicional', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Ana Activa', email: 'ana@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'ana@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });

    await page.click('.vtab[data-view="interprete"]');
    await page.waitForSelector('#intTexto', { timeout: 5000 });
    // "radiografia" (no "rx torax"): con este texto, el nombre del Único
    // ("Radiografía de torax") puntúa más que el del PMO ("Radiología
    // tórax", que sólo matchea por el sinónimo cruzado) — así que el
    // PRINCIPAL del grupo termina siendo el del Único, no el del PMO. Es
    // a propósito: exposicion_siguiente sólo está cargado del lado del PMO
    // (340301), no en su equivalente del Único (U340301) — si
    // candidatosParaItem() sólo mirara el principal del grupo, la
    // exposición adicional se perdía en silencio. Este es el caso real que
    // lo expuso.
    await page.fill('#intTexto', 'radiografia torax f y p');
    await page.click('#intGo');
    await page.waitForSelector('.int-item', { timeout: 5000 });

    const grupo = page.locator('.int-grupo').first();

    // Un solo bloque, no tres.
    afirmar(await page.locator('.int-grupo').count() >= 1, 'debería haber al menos un grupo');
    afirmar(await grupo.locator('.int-cand').count() === 1, 'el bloque de 340301 debería tener un solo botón principal, no una tarjeta por nomenclador');

    // Un solo porcentaje (antes: 83% en un lado, 50% en el otro, para el
    // mismo código 340301 — "eso no debería suceder").
    afirmar(await grupo.locator('.int-pct').count() === 1, 'el bloque debería mostrar un único porcentaje de coincidencia');

    // El otro nomenclador queda como chip "también en", seleccionable aparte.
    const chipOtro = grupo.locator('.int-cand-otros [data-int-code]');
    afirmar(await chipOtro.count() === 1, 'debería haber un chip "también en" para el otro nomenclador de 340301');
    afirmar(await chipOtro.getAttribute('data-int-companion') === null,
      'el chip "también en" no debería llevar data-int-companion (si su grupo no es el primero, sigue contando para la sugerencia)');

    // La exposición adicional (340302) cuelga del MISMO bloque, con chips
    // para sus dos nomencladores — no una tarjeta aparte.
    const notaComp = grupo.locator('.int-cand-comp');
    afirmar(await notaComp.count() === 1, 'la exposición adicional debería aparecer como nota dentro del mismo bloque, no como grupo aparte');
    afirmar(await notaComp.locator('[data-int-code="340302"]').count() === 1, 'la nota debería traer el chip del 340302 (PMO)');
    afirmar(await notaComp.locator('[data-int-code="U340302"]').count() === 1, 'la nota debería traer el chip del equivalente en el Único (U340302)');
    afirmar(await notaComp.locator('[data-int-companion="1"]').count() === 2,
      'los chips de la exposición adicional sí deberían llevar data-int-companion (nunca cuentan para la sugerencia: no salieron de una coincidencia de texto)');

    // Elegir el chip del PMO para la exposición adicional manda ESE código,
    // no el principal del grupo.
    await notaComp.locator('[data-int-code="340302"]').click();
    await page.waitForSelector('#intResumen:not([hidden])', { timeout: 5000 });
    afirmar(await page.locator('#intResumen .int-chip .mono', { hasText: '340302' }).count() === 1,
      'elegir el chip de exposición adicional debería sumar 340302 al resumen');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
