// Caso "relaciones": el médico administrador y el administrador general
// pueden agregar/quitar prácticas de las relaciones entre códigos —lo que
// arma el árbol de módulos— desde el menú de edición, y el cambio se
// espeja en el otro código (incluye <-> incluido en). El médico
// administrador ve SÓLO esos campos, nunca el resto de la ficha (nombre,
// norma, auditoría), que sigue siendo del administrador general — mismo
// límite que ya prueba tests/rls/regresion.sql del lado de la base; esto
// prueba que la interfaz respeta el mismo límite.
//
// 660102/660101/660001 son códigos NBU reales y estables (data/nbu_db.json,
// ACTO BIOQUÍMICO y BACILOSCOPIA), no inventados: 660102 ya incluye 660101
// en el pipeline, así que el caso también ejercita "agregar sobre lo que ya
// había" y no sólo sobre una ficha vacía.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8614;
const CODIGO = '660102', A_AGREGAR = '660001';

// El recorrido guiado y las pistas contextuales usan overlays a pantalla
// completa que tapan al resto: para un caso que sólo prueba el editor de
// relaciones, no la UI que hay alrededor, sacarlos del medio antes de cada
// clic sensible es más simple y estable que perseguir cada botón de cierre.
async function sinOverlays(page) {
  await page.evaluate(() => {
    const p = document.getElementById('pista'); if (p) p.remove();
    const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on');
  });
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('relaciones: el médico administrador ve sólo relaciones, y el cambio se espeja', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Med Admin', email: 'medadmin@visitar.test', password: 'Password123!', rol: 'medico_admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'medadmin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);

    await page.click('#editModeBtn');
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('#editFichaBtn', { timeout: 5000 });
    await sinOverlays(page);
    afirmar((await page.textContent('#editFichaBtn')).includes('relaciones'),
      'el médico administrador debería ver "Editar relaciones", no "Editar ficha"');
    await page.click('#editFichaBtn');
    await page.waitForSelector('#efInc', { timeout: 5000 });

    afirmar(await page.locator('#efNom').count() === 0,
      'el médico administrador no debería ver el campo de nombre/denominación');
    afirmar(await page.locator('#efAud').count() === 0,
      'el médico administrador no debería ver las normas de auditoría');
    const incActual = (await page.inputValue('#efInc')).split('\n').filter(Boolean);
    afirmar(incActual.includes('660101'), `esperaba ver el 660101 ya incluido, vino: ${incActual}`);

    await page.fill('#efInc', incActual.concat(A_AGREGAR).join('\n'));
    await page.click('#efSave');
    await page.waitForTimeout(400);   // el guardado es async (POST al simulador); no hay un selector que lo confirme

    // "Relaciones entre códigos" es una sección plegable y arranca cerrada
    // (no está en SEC_ABIERTAS): hay que abrirla para leer los chips.
    const abrirRelaciones = async () => {
      await page.waitForSelector('.sec:has(.rel-block) .slabel', { timeout: 5000 });
      const lbl = page.locator('.sec:has(.rel-block) .slabel');
      if (!(await lbl.evaluate(e => e.closest('.sec').classList.contains('abierta')))) await lbl.click();
    };

    // Releer la propia ficha: tiene que mostrar los dos códigos incluidos.
    await sinOverlays(page);
    await page.evaluate(() => { location.hash = ''; });
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await abrirRelaciones();
    const chipsInc = await page.locator('.rel-inc .chipset').textContent();
    afirmar(chipsInc.includes('660101') && chipsInc.includes(A_AGREGAR),
      `"Incluye" de ${CODIGO} debería tener 660101 y ${A_AGREGAR}, tiene: ${chipsInc}`);

    // El espejo: el código agregado tiene que decir que quedó incluido en éste.
    await sinOverlays(page);
    await page.evaluate(() => { location.hash = ''; });
    await page.evaluate((c) => { location.hash = c; }, A_AGREGAR);
    await abrirRelaciones();
    const chipsIncd = await page.locator('.rel-incd .chipset').textContent();
    afirmar(chipsIncd.includes(CODIGO),
      `"Incluido en" de ${A_AGREGAR} debería mostrar ${CODIGO} (espejo de incluye), tiene: ${chipsIncd}`);

    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await correrCaso('relaciones: el administrador general ve la ficha completa, relaciones incluidas', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);

    await page.click('#editModeBtn');
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('#editFichaBtn', { timeout: 5000 });
    await sinOverlays(page);
    afirmar((await page.textContent('#editFichaBtn')) === '✎ Editar ficha',
      'el administrador general debería ver "Editar ficha" (la completa)');
    await page.click('#editFichaBtn');
    await page.waitForSelector('#efNom', { timeout: 5000 });
    afirmar(await page.locator('#efInc').count() === 1,
      'el administrador general también debería ver el campo de relaciones ("Incluye")');
    afirmar(await page.locator('#efReset').count() === 1,
      'el administrador general debería tener "Restaurar original" (la ficha completa)');
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
