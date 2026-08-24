// Caso "anexar": dentro de "Cargá esto" (dentro de "Cómo se carga esta
// solicitud") hay un atajo para anexar códigos que también hay que facturar
// junto con éste — al revés de "Vincular código" (relaciones.incluye, que no
// se factura aparte), acá los dos códigos se cargan y no hay espejo: no
// existe un "incluido en" recíproco. Mismo permiso que vincular (admin y
// médico administrador, sólo en Modo edición). Ver HANDOFF.md.
//
// 660102/660050 son códigos NBU reales y estables (data/nbu_db.json,
// BACILOSCOPIA y ANTIESTAFILOLISINA), sin relación entre sí en el pipeline —
// a propósito, para no mezclarse con lo que ya prueba casos/vincular.mjs.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8616;
const CODIGO = '660102', A_ANEXAR = '660050';

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

  await correrCaso('anexar: agregar y quitar un código desde "Cargá esto", sin espejo', async () => {
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
    afirmar(await page.locator('#cgAnexBtn').count() === 0,
      'sin Modo edición no debería verse el atajo "+ Anexar código"');

    await sinOverlays(page);
    await page.evaluate(() => { document.getElementById('closeDrawer')?.click(); });
    await page.click('#editModeBtn');
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await sinOverlays(page);
    await page.waitForSelector('#cgAnexBtn', { timeout: 5000 });

    await page.fill('#cgAnexInput', A_ANEXAR);
    await page.click('#cgAnexBtn');
    await page.waitForTimeout(400);   // el guardado es async (POST al simulador)

    const cargar = await page.locator('#cgCargarOl').textContent();
    afirmar(cargar.includes(A_ANEXAR) && cargar.includes('Cargar también'),
      `"Cargá esto" debería mostrar ${A_ANEXAR} como paso, tiene: ${cargar}`);

    // No es "incluye": no debería aparecer en "No cargues aparte".
    const noCarguesCount = await page.locator('.cg-no').count();
    if (noCarguesCount) {
      const noCargues = await page.locator('.cg-no').textContent();
      afirmar(!noCargues.includes(A_ANEXAR),
        `"No cargues aparte" no debería incluir ${A_ANEXAR} (eso es de "vincular", no de "anexar"), tiene: ${noCargues}`);
    }

    // Sin espejo: la ficha del código anexado no debería ganar una sección de relaciones.
    await sinOverlays(page);
    await page.evaluate(() => { location.hash = ''; });
    await page.evaluate((c) => { location.hash = c; }, A_ANEXAR);
    await page.waitForTimeout(300);
    afirmar(await page.locator('.sec:has(.rel-block)').count() === 0,
      `${A_ANEXAR} no debería tener "Relaciones entre códigos" propia: anexar no tiene espejo`);

    // Desanexar: sacarlo del atajo lo saca de "Cargá esto".
    await sinOverlays(page);
    await page.evaluate(() => { location.hash = ''; });
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('#cgCargarOl', { timeout: 5000 });
    await page.click(`#cgCargarOl [data-quitar-anex="${A_ANEXAR}"]`);
    await page.waitForTimeout(400);
    const cargarTrasQuitar = await page.locator('#cgCargarOl').textContent();
    afirmar(!cargarTrasQuitar.includes(A_ANEXAR),
      `"Cargá esto" no debería mostrar más ${A_ANEXAR} tras desanexarlo, tiene: ${cargarTrasQuitar}`);
    afirmar(cargarTrasQuitar.includes('660102'),
      `desanexar no debería tocar el paso base de ${CODIGO}, tiene: ${cargarTrasQuitar}`);

    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
