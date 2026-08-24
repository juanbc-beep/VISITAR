// Caso "nubelocal": sin nube configurada, la app tiene que seguir andando en
// modo local (acceso de empresa + perfiles en el navegador), no romperse.
// Es la red de contención documentada en HANDOFF.md 4.4: "si NBU_NUBE queda
// vacío, la app arranca como antes".
//
// No se toca web/index.html para simular esto (eso invalidaría los hashes de
// la CSP sellada). En cambio se fija window.NBU_NUBE como propiedad de sólo
// lectura ANTES de que corra el script de la página: la asignación de la
// propia app a esa misma variable (línea ~108 de index.html) es una
// asignación de módulo no estricto sobre una propiedad no escribible, así
// que no hace nada — exactamente el mismo efecto que si NBU_NUBE nunca se
// hubiera completado.

import { chromium } from 'playwright';
import { servirWeb, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8612;

async function forzarModoLocal(page) {
  await page.addInitScript(() => {
    try {
      Object.defineProperty(window, 'NBU_NUBE', {
        value: { url: '', anon: '' }, writable: false, configurable: false, enumerable: true,
      });
    } catch (e) {}
  });
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  try {
    await correrCaso('nubelocal: sin nube configurada arranca en "Configurar el acceso"', async () => {
      const ctx = await nuevoContexto(browser);
      const page = await ctx.newPage();
      await forzarModoLocal(page);
      const { errores, csp } = vigilarErrores(page);
      await page.goto(base);
      await esperarArranque(page);
      await page.waitForSelector('h2:has-text("Configurar el acceso")', { timeout: 5000 });
      afirmar(await page.isVisible('#gate'), 'el portón debería quedar visible en modo local sin configurar');
      afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
      afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
      await ctx.close();
    });

    await correrCaso('nubelocal: crear el acceso de la empresa entra a la app', async () => {
      const ctx = await nuevoContexto(browser);
      const page = await ctx.newPage();
      await forzarModoLocal(page);
      const { errores } = vigilarErrores(page);
      await page.goto(base);
      await esperarArranque(page);
      await page.fill('#suUser', 'visitar');
      await page.fill('#suPass', '1234');
      await page.fill('#suName', 'Admin Local');
      await page.fill('#suPPass', '1234');
      await page.click('#suGo');
      await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
      const nombre = await page.textContent('#acctNm');
      afirmar(nombre.trim() === 'Admin Local', `esperaba "Admin Local", vino "${nombre}"`);
      afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
      await ctx.close();
    });
  } finally {
    await browser.close();
    srv.close();
  }
}

await main();
