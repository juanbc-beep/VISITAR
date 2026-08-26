// Caso "coincidencia_forzada": el administrador general puede fijar, desde
// ✎ Editar ficha, que buscar exactamente una frase encuentre un código con
// 100% de coincidencia, sin depender de cómo puntúe el resto del motor.
// Pedido explícito del usuario (26/8/2026), a partir de un caso real de la
// propia base: buscar "urea" trae 660902 "UREA, sérica" a 100%, pero
// U60660902 "Uremia" —la misma práctica, semánticamente correcta— sólo a
// 33%, porque "urea" no está en el NOMBRE de esa ficha, sólo llega por la
// equivalencia cruzada con el NBU (tier de puntaje más bajo). El usuario
// necesita poder subirlo a mano a 100%.
//
// Ver web/index.html: puntuar() (el atajo al principio, antes de cualquier
// otra cosa), editFicha() (#efCoincForzada) y openCode() (la sección
// "Buscarlo así, 100% seguro" en la propia ficha).
//
// U60660902 "Uremia" (Único) es un código real y estable (data/nbu_db.json)
// — elegido porque es exactamente el caso que reportó el usuario, no uno
// armado para el test.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8637;
const CODIGO = 'U60660902';

async function sinOverlays(page) {
  await page.evaluate(() => {
    const p = document.getElementById('pista'); if (p) p.classList.remove('on');
    const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on');
  });
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('coincidencia_forzada: el administrador general fuerza el 100% de coincidencia para una frase exacta', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#editModeBtn');

    await page.click('[data-mode="ALL"]');
    await page.waitForSelector('#q', { timeout: 5000 });
    await page.fill('#q', 'urea');
    await page.waitForTimeout(300);
    afirmar(!(await page.locator(`.row[data-code="${CODIGO}"]`).evaluate(e => e.classList.contains('row-match'))),
      `antes de forzarla, ${CODIGO} no debería estar resaltada como coincidencia fuerte (es el caso real: 33%)`);

    await page.click(`.row[data-code="${CODIGO}"]`);
    await page.waitForSelector('.drawer.on', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#editFichaBtn');
    await page.waitForSelector('#efCoincForzada', { timeout: 5000 });
    await page.fill('#efCoincForzada', 'urea');
    await page.click('#efSave');
    await page.waitForSelector('.drawer.on', { timeout: 5000 });
    await page.waitForTimeout(300);

    // La propia ficha explica por qué, sin tener que volver a Editar ficha.
    // .slabel va en mayúsculas por CSS (text-transform), así que innerText()
    // ya viene así — se compara sin distinguir mayúsculas de minúsculas.
    const textoFicha = (await page.locator('.drawer').innerText()).toLowerCase();
    afirmar(textoFicha.includes('buscarlo así, 100% seguro'), 'la ficha debería mostrar la sección "Buscarlo así, 100% seguro"');
    afirmar(textoFicha.includes('urea'), 'la ficha debería mostrar la frase forzada ("urea")');

    await sinOverlays(page);
    await page.click('#closeDrawer');
    await page.fill('#q', '');
    await page.fill('#q', 'urea');
    await page.waitForTimeout(300);
    afirmar(await page.locator(`.row[data-code="${CODIGO}"]`).evaluate(e => e.classList.contains('row-match')),
      `con la coincidencia forzada, ${CODIGO} debería aparecer resaltada como 100%`);

    // No es genérico: agregar el término no fuerza CUALQUIER búsqueda que
    // contenga "urea" — sólo la consulta exacta.
    await page.fill('#q', '');
    await page.fill('#q', 'urea clearence');
    await page.waitForTimeout(300);
    afirmar(!(await page.locator(`.row[data-code="${CODIGO}"]`).count()) ||
      !(await page.locator(`.row[data-code="${CODIGO}"]`).evaluate(e => e.classList.contains('row-match'))),
      `"urea clearence" no debería forzar a ${CODIGO} — la frase forzada es "urea" a secas, no cualquier búsqueda que la contenga`);

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
