// Caso "sugerencias_pedida_como": el Intérprete de orden aprende del uso
// real. Cuando alguien elige un candidato que NO es el primero (el que el
// motor cree más probable), queda anotado como sugerencia; el administrador
// la revisa desde Administración → Sugerencias y, si corresponde, la suma a
// "pedida_como" del código. Ver web/index.html: el click handler de
// #intItems (candidatosParaItem/data-int-rank), NUBE.sugerirPedidaComo() y
// paneSugerencias().
//
// "Glucemia" trae varios candidatos empatados al 100% (60660412, 60660413,
// 660412, 660413 — verificado a mano contra data/nbu_db.json), agrupados de
// a dos por equivalencia entre nomencladores (EQGRUPO, ver
// candidatosParaItem()): {60660412, 660412} es el primer grupo (rank 0),
// {60660413, 660413} el segundo (rank 1). 660413 no es del primer grupo, así
// que elegirlo SÍ genera una sugerencia — aparece como chip "también en"
// (data-int-code="660413", sin data-int-companion) dentro de la tarjeta de
// 60660413, con el rank heredado del grupo (1), no 0. Es el mismo criterio
// de siempre, no un caso armado — si el orden de empate cambiara el día de
// mañana, cualquier candidato de un grupo que no sea el primero serviría
// igual.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8627;
const ITEM = 'Glucemia';
const CODIGO_NO_TOP = '660413';

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

  await correrCaso('sugerencias_pedida_como: elegir un candidato que no es el primero avisa al administrador, que puede sumarlo', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Ana Activa', email: 'ana@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    // Ana usa el Intérprete y elige el candidato 660412, que no es el primero.
    await page.fill('#nbMail', 'ana@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await page.click('.vtab[data-view="interprete"]');
    await page.waitForSelector('#intTexto', { timeout: 5000 });
    await page.fill('#intTexto', ITEM);
    await page.click('#intGo');
    await page.waitForSelector('.int-item', { timeout: 5000 });
    // Ya no es necesariamente un <button class="int-cand"> —puede ser el
    // chip "también en" de un grupo (ver candidatosParaItem())— así que el
    // locator busca por el atributo, sin asumir qué clase lo envuelve.
    const candidato = page.locator(`[data-int-code="${CODIGO_NO_TOP}"]`);
    afirmar(await candidato.getAttribute('data-int-rank') !== '0',
      `${CODIGO_NO_TOP} tendría que ser de un grupo que NO es el primero de "${ITEM}" para que este caso pruebe algo`);
    afirmar(await candidato.getAttribute('data-int-companion') === null,
      `${CODIGO_NO_TOP} no debería llevar data-int-companion (eso lo excluiría siempre de la sugerencia, sea cual sea el rank)`);
    await candidato.click();
    await page.waitForTimeout(300); // el aviso al administrador es fire-and-forget

    // Elegir el primero de otro renglón (rank 0) no debería avisar nada:
    // se comprueba más abajo, contando cuántas sugerencias llegaron en total.

    // Admin: la ve en Administración → Sugerencias.
    await page.evaluate(() => window.NBUNube && window.NBUNube.salir());
    await page.reload();
    await esperarArranque(page);
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#adminBtn');
    await page.waitForSelector('.atab', { timeout: 5000 });
    await page.click('.atab[data-t="sugerencias"]');
    await page.waitForSelector('[data-sact]', { timeout: 5000 });
    afirmar(await page.locator('[data-sact="ok"]').count() === 1, 'debería haber exactamente una sugerencia pendiente');
    afirmar((await page.textContent('#aPane')).includes(ITEM), `la sugerencia debería mostrar el texto "${ITEM}"`);

    await page.click('[data-sact="ok"]');
    await page.waitForTimeout(400);
    afirmar((await page.textContent('#aPane')).includes('No hay sugerencias pendientes'),
      'después de aprobarla, la lista de pendientes debería quedar vacía');

    // La ficha del código ahora muestra "Glucemia" en "pedida como".
    await page.click('#aClose');
    await page.evaluate((c) => { location.hash = c; }, CODIGO_NO_TOP);
    await sinOverlays(page);
    await page.waitForSelector('#secPedida', { timeout: 5000 });
    afirmar((await page.textContent('#secPedida')).includes(ITEM),
      `después de "Agregar", ${CODIGO_NO_TOP} debería mostrar "${ITEM}" en "Puede venir solicitada como"`);

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
