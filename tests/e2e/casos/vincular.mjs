// Caso "vincular": dentro de "Cómo se carga esta solicitud" hay un atajo
// para vincular/desvincular códigos —lo que arma el Árbol de módulos—, sin
// pasar por "Editar ficha". Mismo permiso que editar relaciones (admin y
// médico administrador), y sólo en Modo edición. Ver HANDOFF.md.
//
// 660102 ya incluye 660101 en el pipeline (ACTO BIOQUÍMICO / BACILOSCOPIA,
// mismos códigos reales que usa casos/relaciones.mjs), así que el caso
// también ejercita "vincular sobre lo que ya había".

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8615;
const CODIGO = '660102', A_VINCULAR = '660001';

// Ocultar con la misma clase que usa la app (.on), nunca borrar el nodo con
// .remove() — ver el comentario en casos/relaciones.mjs: la app nunca lo
// borra, y borrarlo hace que revisarPistas() tire un TypeError más tarde,
// al cerrar la ficha, que no tiene nada que ver con lo que este caso prueba.
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

  await correrCaso('vincular: agregar y quitar un código desde "Cómo se carga", con espejo', async () => {
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

    // Sin Modo edición, el atajo no aparece.
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('.carga', { timeout: 5000 });
    afirmar(await page.locator('#cgVincInput').count() === 0,
      'sin Modo edición no debería verse el atajo "Vincular código"');

    await sinOverlays(page);
    await page.evaluate(() => { document.getElementById('closeDrawer')?.click(); });
    await page.click('#editModeBtn');
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await sinOverlays(page);
    await page.waitForSelector('#cgVincInput', { timeout: 5000 });

    const incActual = (await page.locator('#cgVincChips .cg-vc').allTextContents());
    afirmar(incActual.some(t => t.includes('660101')),
      `esperaba ver el 660101 ya vinculado, vino: ${incActual}`);

    await page.fill('#cgVincInput', A_VINCULAR);
    await page.click('#cgVincBtn');
    await page.waitForTimeout(400);   // el guardado es async (POST al simulador)

    const chips = await page.locator('#cgVincChips').textContent();
    afirmar(chips.includes('660101') && chips.includes(A_VINCULAR),
      `"Vincular código" debería mostrar 660101 y ${A_VINCULAR}, tiene: ${chips}`);

    // Se refleja en el lugar de siempre: "No cargues aparte", más arriba en la misma sección.
    const noCargues = await page.locator('.cg-no').textContent();
    afirmar(noCargues.includes(A_VINCULAR),
      `"No cargues aparte" debería incluir ${A_VINCULAR} tras vincularlo, tiene: ${noCargues}`);

    // El espejo: el código vinculado tiene que decir que quedó incluido en éste.
    await sinOverlays(page);
    await page.evaluate(() => { location.hash = ''; });
    await page.evaluate((c) => { location.hash = c; }, A_VINCULAR);
    await page.waitForSelector('.sec:has(.rel-block) .slabel', { timeout: 5000 });
    const lbl = page.locator('.sec:has(.rel-block) .slabel');
    if (!(await lbl.evaluate(e => e.closest('.sec').classList.contains('abierta')))) await lbl.click();
    const chipsIncd = await page.locator('.rel-incd .chipset').textContent();
    afirmar(chipsIncd.includes(CODIGO),
      `"Incluido en" de ${A_VINCULAR} debería mostrar ${CODIGO} (espejo), tiene: ${chipsIncd}`);

    // Desvincular: sacarlo del atajo lo saca también de "No cargues aparte" y del espejo.
    await sinOverlays(page);
    await page.evaluate(() => { location.hash = ''; });
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('#cgVincChips', { timeout: 5000 });
    await page.click(`#cgVincChips .cg-vc-x[data-quitar="${A_VINCULAR}"]`);
    await page.waitForTimeout(400);
    const chipsTrasQuitar = await page.locator('#cgVincChips').textContent();
    afirmar(!chipsTrasQuitar.includes(A_VINCULAR),
      `"Vincular código" no debería mostrar más ${A_VINCULAR} tras desvincularlo, tiene: ${chipsTrasQuitar}`);
    afirmar(chipsTrasQuitar.includes('660101'),
      `desvincular ${A_VINCULAR} no debería tocar el 660101 que ya estaba, tiene: ${chipsTrasQuitar}`);

    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
