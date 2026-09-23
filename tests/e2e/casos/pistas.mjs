// Caso "pistas": el cartel «Novedad · Acá te avisamos qué cambió» (la pista de la
// campanita) salía muchas veces y en cualquier momento. Tres causas, todas
// cubiertas acá (ver HANDOFF.md, 23/9/2026):
//   1. se reevaluaba con cualquier scroll, y la campanita siempre está a la vista;
//   2. «Después» no guardaba nada: volvía al siguiente scroll;
//   3. aparecía encima de una ventana abierta (Contrataciones, Administración).

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8641;

async function entrar(page, base, email) {
  await page.goto(base);
  await esperarArranque(page);
  if (await page.isVisible('#nbMail')) {
    await page.fill('#nbMail', email);
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
  }
  await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
  await page.evaluate(() => { const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on'); });
}

// Un scroll de la página principal, y el tiempo que la app espera antes de revisar.
async function scrollPagina(page) {
  await page.evaluate(() => document.dispatchEvent(new Event('scroll')));
  await page.waitForTimeout(450);
}
const pistaVisible = page => page.isVisible('#pista.on');

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('pistas: «Después» la guarda hasta la próxima vez que se abre la app, «Entendido» para siempre', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Ana Activa', email: 'ana@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await entrar(page, base, 'ana@visitar.test');

    await scrollPagina(page);
    afirmar(await pistaVisible(page), 'la primera vez, al scrollear, debería aparecer la pista de la campanita');
    afirmar((await page.textContent('#pista')).includes('Acá te avisamos qué cambió'), 'debería ser la pista de novedades');

    await page.click('#piLuego');
    for (let i = 0; i < 3; i++) await scrollPagina(page);
    afirmar(!(await pistaVisible(page)), 'después de «Después», seguir scrolleando no debería volver a mostrarla');

    await entrar(page, base, 'ana@visitar.test');
    await scrollPagina(page);
    afirmar(await pistaVisible(page), 'al volver a abrir la app, la pista pospuesta debería aparecer de nuevo');

    await page.keyboard.press('Escape');
    await scrollPagina(page);
    afirmar(!(await pistaVisible(page)), 'Escape también debería posponerla, no traerla de vuelta al siguiente scroll');

    await entrar(page, base, 'ana@visitar.test');
    await scrollPagina(page);
    await page.click('#piOk');
    await entrar(page, base, 'ana@visitar.test');
    await scrollPagina(page);
    afirmar(!(await pistaVisible(page)), 'con «Entendido» no debería volver a aparecer');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('pistas: no aparece encima de una ventana abierta, ni por scrollear adentro de ella', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await entrar(page, base, 'admin@visitar.test');

    await page.click('#contrBtn');
    await page.waitForSelector('#contrModal.on');
    await page.evaluate(() => document.getElementById('contrBox').dispatchEvent(new Event('scroll')));
    await scrollPagina(page);
    afirmar(!(await pistaVisible(page)), 'con Contrataciones abierta no debería aparecer la pista');
    await page.click('#contrClose');

    await scrollPagina(page);
    afirmar(await pistaVisible(page), 'cerrada la ventana, el scroll de la página sí debería mostrarla');
    await page.click('#contrBtn');
    await page.waitForSelector('#contrModal.on');
    afirmar(!(await page.isVisible('#pista')), 'abrir una ventana debería tapar la pista que estaba a la vista');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
