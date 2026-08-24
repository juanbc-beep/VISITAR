// Caso "anexar": dentro de "Cargá esto" (dentro de "Cómo se carga esta
// solicitud") hay un atajo para anexar códigos que también hay que facturar
// junto con éste — al revés de "Vincular código" (relaciones.incluye, que no
// se factura aparte), acá los dos códigos se cargan y no hay espejo: no
// existe un "incluido en" recíproco. Mismo permiso que vincular (admin y
// médico administrador), sin pedir Modo edición. Ver HANDOFF.md.
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

    // No pide Modo edición: es más liviano que "Editar ficha" y vive al lado
    // de "Contá cómo se carga acá", que tampoco lo pide.
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

  // Los códigos del Único se guardan con el prefijo "U" (scripts/assemble.py)
  // pero se escriben y se muestran sin él — anexar uno tipeando lo que se ve
  // en pantalla devolvía "no existe" antes de resolverCodigo(). 200124 (VCC,
  // PMO) y 430111 (Único) son los códigos reales que reportó Juan.
  await correrCaso('anexar: un código del Nomenclador Único, tipeado sin el prefijo interno', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);

    const CODIGO_PMO = '200124', A_UNICO = '430111';
    await page.evaluate((c) => { location.hash = c; }, CODIGO_PMO);
    await sinOverlays(page);
    await page.waitForSelector('#cgAnexBtn', { timeout: 5000 });

    await page.fill('#cgAnexInput', A_UNICO);
    await page.click('#cgAnexBtn');
    await page.waitForTimeout(400);

    const cargar = await page.locator('#cgCargarOl').textContent();
    afirmar(cargar.includes(A_UNICO) && !cargar.includes('no existe'),
      `anexar ${A_UNICO} (Único) tipeado sin prefijo debería funcionar, "Cargá esto" tiene: ${cargar}`);

    // Se ve desde el listado, sin abrir la ficha (pedido de Juan): una
    // etiqueta propia, distinta de "relaciones" (eso es el Árbol de módulos).
    await sinOverlays(page);
    await page.evaluate(() => { document.getElementById('closeDrawer')?.click(); });
    await page.click('.modebtn-all');
    await page.fill('#q', CODIGO_PMO);
    await page.waitForTimeout(300);
    const filaListado = page.locator('.row', { hasText: CODIGO_PMO }).first();
    afirmar(await filaListado.locator('.t-anex').count() === 1,
      `la fila de ${CODIGO_PMO} en el listado debería mostrar la etiqueta "+ anexos"`);

    await page.evaluate((c) => { location.hash = c; }, CODIGO_PMO);
    await sinOverlays(page);
    await page.waitForSelector('#cgCargarOl', { timeout: 5000 });

    // El botón de quitar guarda la clave real (con el prefijo "U"), no lo tipeado.
    const btn = page.locator('#cgCargarOl [data-quitar-anex]');
    afirmar(await btn.count() === 1, 'debería haber un botón para quitar el código anexado');
    await btn.click();
    await page.waitForTimeout(400);
    const cargarTrasQuitar = await page.locator('#cgCargarOl').textContent();
    afirmar(!cargarTrasQuitar.includes(A_UNICO),
      `"Cargá esto" no debería mostrar más ${A_UNICO} tras quitarlo, tiene: ${cargarTrasQuitar}`);

    // La etiqueta del listado se va con el último anexado.
    await sinOverlays(page);
    await page.evaluate(() => { document.getElementById('closeDrawer')?.click(); });
    await page.click('.modebtn-all');
    await page.fill('#q', CODIGO_PMO);
    await page.waitForTimeout(300);
    const filaTrasQuitar = page.locator('.row', { hasText: CODIGO_PMO }).first();
    afirmar(await filaTrasQuitar.locator('.t-anex').count() === 0,
      `la fila de ${CODIGO_PMO} no debería mostrar "+ anexos" tras quitar el único código anexado`);

    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
