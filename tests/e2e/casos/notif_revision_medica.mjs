// Caso "notif_revision_medica": cuando un médico administrador publica una
// revisión médica (🩺, dentro de la ficha), el administrador general tiene
// que enterarse sin ir a buscarla — la misma campanita de "novedades" que ya
// usan los administrativos para observaciones/correcciones, pero con
// revisiones médicas para él (antes esa campanita le quedaba siempre
// oculta: "el administrador no recibe aviso" era la regla vieja). Pedido
// explícito del usuario, ver HANDOFF.md, 26/8/2026.
//
// Ver web/index.html: cargarContenidoNube() (la rama `if(esDuenio())` que
// arma CONTENT.novedades desde revision_medica), actualizarPendientes() y
// verNovedades().
//
// 660001 (ACTO BIOQUÍMICO) es un código NBU real y estable (data/nbu_db.json).

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8634;
const CODIGO = '660001';
const TEXTO_REVISION = 'Corresponde con diagnósticos de control metabólico; no indicada como rastreo aislado.';

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

  await correrCaso('notif_revision_medica: publicar una revisión médica avisa al administrador general con la campanita de novedades', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Med Admin', email: 'medadmin@visitar.test', password: 'Password123!', rol: 'medico_admin', estado: 'activo' });
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    // El médico administrador publica la revisión.
    await page.fill('#nbMail', 'medadmin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('#rmNuevo', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#rmNuevo');
    await page.fill('#rmNArea', TEXTO_REVISION);
    await page.click('#rmNGuardar');
    await page.waitForTimeout(400); // guardarCorreccion es fire-and-forget

    // El administrador general entra después. Limpiar el hash antes de
    // recargar: si no, la app vuelve a abrir la ficha del médico apenas
    // arranca (el mismo código que quedó en la URL) y el drawer tapa la
    // campanita.
    await page.evaluate(() => window.NBUNube && window.NBUNube.salir());
    await page.evaluate(() => { location.hash = ''; });
    await page.reload();
    await esperarArranque(page);
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);

    await page.waitForSelector('#obsBtn:not([hidden])', { timeout: 8000 });
    afirmar(await page.textContent('#obsN') === '1', 'la campanita debería mostrar 1 revisión médica sin ver');
    afirmar(await page.evaluate(() => document.getElementById('obsBtn').classList.contains('pendbtn')),
      'con una revisión sin ver, la campanita debería quedar resaltada (.pendbtn)');

    await page.click('#obsBtn');
    await page.waitForSelector('#adminModal.on', { timeout: 5000 });
    const texto = await page.textContent('#adminBox');
    afirmar(texto.includes('Revisiones médicas'), 'el modal debería titularse "Revisiones médicas" para el administrador general');
    afirmar(texto.includes('Med Admin'), 'el modal debería decir quién publicó la revisión');
    afirmar(texto.includes(CODIGO), `el modal debería mostrar el código ${CODIGO}`);
    afirmar(texto.includes(TEXTO_REVISION), 'el modal debería mostrar el texto de la revisión');

    // Tocar el código abre la ficha y cierra el modal.
    await page.click(`[data-obsir="${CODIGO}"]`);
    await page.waitForSelector('#adminModal:not(.on)', { timeout: 5000 });
    await page.waitForSelector('.drawer.on', { timeout: 5000 });
    afirmar((await page.textContent('.dcode')) === CODIGO, `la ficha abierta debería ser ${CODIGO}`);

    // Abrir el modal marca la revisión como vista: la próxima vez ya no cuenta.
    await page.click('#closeDrawer');
    await page.waitForSelector('#obsN', { state: 'hidden', timeout: 5000 });
    afirmar(!(await page.evaluate(() => document.getElementById('obsBtn').classList.contains('pendbtn'))),
      'una vez vista, la campanita no debería seguir resaltada');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
