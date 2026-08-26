// Caso "busqueda_sinonimos": el catálogo del PMO nombra la sección
// "Radiología / Diagnóstico por imágenes" así casi siempre, pero 16 de sus
// 6.478 códigos dicen "radiografía" en vez de "radiología" (340905
// "Radiografía en quirófano o habitación", 340908 "Radiografía a
// domicilio", …) — verificado contra data/nbu_db.json. Antes de esto,
// buscar por una de las dos palabras se perdía la mitad de la sección: el
// usuario avisó que "radiografia" no traía todos los códigos de la
// sección. Ver SINONIMOS_COMUNES en web/index.html y HANDOFF.md, 26/8/2026.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8632;
// 340301 "Radiología tórax" y 340905 "Radiografía en quirófano o
// habitación" son códigos reales del PMO (data/nbu_db.json), elegidos
// justamente porque cada uno sólo trae UNA de las dos palabras en su
// nombre — si el sinónimo no estuviera, cada búsqueda se perdería el otro.

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('busqueda_sinonimos: "radiografia" y "radiologia" traen los códigos de la sección sin importar cuál se escriba', async () => {
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

    // "Buscar en todo el manual": los dos códigos son del PMO, y el modo
    // por defecto es NBU (bioquímica), donde no aparecerían aunque el
    // sinónimo funcionara.
    await page.waitForSelector('[data-mode="ALL"]', { timeout: 5000 });
    await page.click('[data-mode="ALL"]');
    await page.waitForSelector('#q', { timeout: 5000 });

    await page.fill('#q', 'radiografia');
    await page.waitForSelector('.row', { timeout: 5000 });
    afirmar(await page.locator('.row[data-code="340301"]').count() === 1,
      'buscar "radiografia" debería traer 340301 "Radiología tórax" por el sinónimo, aunque su nombre no diga "radiografía"');

    await page.fill('#q', 'radiologia');
    await page.waitForSelector('.row', { timeout: 5000 });
    afirmar(await page.locator('.row[data-code="340905"]').count() === 1,
      'buscar "radiologia" debería traer 340905 "Radiografía en quirófano o habitación" por el sinónimo, aunque su nombre no diga "radiología"');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
