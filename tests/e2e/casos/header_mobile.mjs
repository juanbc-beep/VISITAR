// Caso "header_mobile": dos bugs de mobile reportados por el usuario en la
// cabecera y el cajón de filtros.
//
// 1) La "X" de cerrar el cajón de filtros (#railClose) quedaba descentrada
//    dentro de su botón. Causa: .rail-close pisa el display:grid;place-items
//    de .icon-btn con display:flex, pero sin repetir align-items/
//    justify-content — mismo bug, y mismo arreglo, que ya tenía documentado
//    .filter-toggle un poco más arriba en el CSS (ver el comentario ahí).
//
// 2) El chip de cuenta (#acctChip, "A Admin General") podía quedar cortado
//    fuera de la pantalla en mobile: con varios botones habilitados (admin,
//    pendientes, novedades…) la fila de íconos + el chip no entraban en una
//    sola línea, y como .hbtns no tenía un ancho propio contra el cual
//    desbordar, nunca envolvía — todo se seguía dibujando en una sola fila
//    que se salía del viewport. Arreglado dándole width:100% + flex-wrap a
//    .hbtns y margin-left:auto al chip, para que quede siempre pegado al
//    margen derecho, entero y visible.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8671;

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

  await correrCaso('header_mobile: la "X" de cerrar el cajón de filtros queda centrada en su botón', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'hm1@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 390, height: 844 });
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'hm1@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);

    await page.click('#filterToggle');
    await page.waitForTimeout(250);
    const boton = await page.locator('#railClose').boundingBox();
    const icono = await page.locator('#railClose svg').boundingBox();
    afirmar(!!boton && !!icono, 'el botón de cerrar y su ícono deberían existir y estar visibles');
    const centroBoton = boton.x + boton.width / 2;
    const centroIcono = icono.x + icono.width / 2;
    afirmar(Math.abs(centroBoton - centroIcono) <= 1,
      `la "X" debería quedar centrada horizontalmente en el botón; centro del botón=${centroBoton}, centro del ícono=${centroIcono}`);

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await correrCaso('header_mobile: el chip de cuenta queda entero y pegado al margen derecho, no cortado por el borde', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'hm2@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 390, height: 844 });
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'hm2@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);

    // Este perfil es admin general: ve varios botones más (admin, modo
    // edición, pendientes) — son justamente los que, todos juntos, hacían
    // desbordar la fila y cortaban el chip antes del arreglo.
    const chip = await page.locator('#acctChip').boundingBox();
    const viewport = page.viewportSize();
    afirmar(!!chip, 'el chip de cuenta debería estar visible');
    afirmar(chip.x >= 0 && chip.x + chip.width <= viewport.width,
      `el chip de cuenta debería quedar entero dentro del viewport (${viewport.width}px); quedó en x=${chip.x}, ancho=${chip.width}`);
    // "Al margen derecho" — no en cualquier lugar visible, pegado al borde
    // (con el padding de .hbar, no exactamente en el borde 0).
    afirmar(viewport.width - (chip.x + chip.width) <= 20,
      `el chip debería quedar pegado al margen derecho; le quedan ${viewport.width - (chip.x + chip.width)}px libres a la derecha`);

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await browser.close();
  await new Promise((resolve) => srv.close(resolve));
}

main().then(() => process.exit(process.exitCode || 0));
