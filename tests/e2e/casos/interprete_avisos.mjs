// Caso "interprete_avisos": el Intérprete de orden avisa, antes de elegir un
// candidato, tres cosas que hasta ahora sólo se veían adentro de la ficha
// completa o recién al facturar: que la cantidad pedida (×N) supera el
// seriado habitual, que el código es bilateral/unilateral (y qué significa
// para la cantidad), y que la orden nombra un tipo de muestra que no
// coincide con el del código. Pedido explícito del usuario, en ese orden.
// Ver web/index.html: avisosCandidato(), candidatosParaItem() (el
// reintento que saca las palabras de muestra igual que ya sacaba los
// sueltos de 1-2 letras) y HANDOFF.md, 26/8/2026.
//
// Códigos reales y estables (data/nbu_db.json):
//  - 660102 BACILOSCOPIA, DIRECTA y CULTIVO — seriado {max:5}.
//  - 030203 Miringotomía con o sin colocación de tubo dreneje — Bilateral.
//  - 660002 ACETONURIA — muestra ['orina'].

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8635;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('interprete_avisos: seriado, lateralidad y muestra avisan antes de elegir el candidato', async () => {
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
    await page.fill('#intTexto', 'baciloscopia x8\nmiringotomia\nacetonuria en sangre\nhemograma');
    await page.click('#intGo');
    await page.waitForSelector('.int-item', { timeout: 5000 });

    // Los avisos se calculan sobre el candidato principal del grupo (ver
    // avisosCandidato() en web/index.html), pero el código de la prueba
    // puede terminar como principal o como chip "también en" según cuál
    // nomenclador puntúe más — se busca el bloque entero que lo contiene,
    // no el propio .int-cand.
    const avisoDe = code => page.locator(`.int-grupo:has([data-int-code="${code}"]) .int-aviso`);

    // Seriado: pedir ×8 de un código con seriado habitual hasta ×5.
    const avSeriado = await avisoDe('660102').first().textContent();
    afirmar(avSeriado.includes('×8') && avSeriado.includes('×5'),
      `el aviso de seriado de 660102 debería mencionar la cantidad pedida (×8) y el máximo habitual (×5), vino: "${avSeriado}"`);

    // Lateralidad: bilateral se carga ×1, no ×2.
    const avLat = await avisoDe('030203').first().textContent();
    afirmar(avLat.includes('Bilateral') && avLat.includes('cantidad 1'),
      `el aviso de lateralidad de 030203 debería explicar que es bilateral y se carga por cantidad 1, vino: "${avLat}"`);

    // Muestra: la orden dice "sangre" pero 660002 es en orina.
    const avMuestra = await avisoDe('660002').first().textContent();
    afirmar(avMuestra.includes('sangre') && avMuestra.includes('orina'),
      `el aviso de muestra de 660002 debería decir que la orden nombra "sangre" pero el código es en orina, vino: "${avMuestra}"`);

    // "Hemograma" (sin cantidad, sin muestra explícita, sin lateralidad) no
    // debería traer ningún aviso: no hay que avisar de nada que no aplica.
    const renglonHemograma = page.locator('.int-item').filter({ has: page.locator('.int-src', { hasText: 'hemograma' }) });
    afirmar(await renglonHemograma.locator('.int-aviso').count() === 0,
      'un renglón sin cantidad, muestra ni lateralidad no debería traer avisos');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
