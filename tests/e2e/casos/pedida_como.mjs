// Caso "pedida_como": el administrador general puede sumar, desde ✎ Editar
// ficha, formas en las que puede venir escrita una orden ("Puede venir
// solicitada como") — hasta ahora ese campo sólo se mostraba, lo cargaba el
// pipeline y no había manera de agregarle algo desde la app. Prueba que:
//   1. lo que se agrega ahí hace que el código se encuentre por ese texto
//      (buscador principal y el Intérprete de orden usan el mismo índice);
//   2. un médico administrador editando sólo las relaciones de la MISMA
//      ficha no lo pisa (ver rebuildH()/applyCode() y los sitios que
//      reconstruyen `ov` en web/index.html).
//
// 660475 (HEMOGRAMA, NBU) es un código real y estable sin pedida_como
// propio en el pipeline — base limpia para el caso.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8625;
const CODIGO = '660475';
const FRASE = 'conteo sanguineo completo';

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

  await correrCaso('pedida_como: sumarla desde Editar ficha la hace encontrable, y el médico admin no la pisa', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    altaUsuario(db, { nombre: 'Med Admin', email: 'medadmin@visitar.test', password: 'Password123!', rol: 'medico_admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    // Admin: agrega la frase desde Editar ficha.
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#editModeBtn');
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('#editFichaBtn', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#editFichaBtn');
    await page.waitForSelector('#efPedidaComo', { timeout: 5000 });
    afirmar((await page.inputValue('#efPedidaComo')).trim() === '', `${CODIGO} no debería traer "pedida como" del pipeline todavía`);
    await page.fill('#efPedidaComo', FRASE);
    await page.click('#efSave');
    await page.waitForTimeout(400);

    // Se busca por la frase nueva: tiene que aparecer en el listado.
    await sinOverlays(page);
    await page.evaluate(() => { document.getElementById('closeDrawer')?.click(); });
    await page.click('.modebtn-all');
    await page.fill('#q', FRASE);
    await page.waitForTimeout(300);
    afirmar(await page.locator('.row', { hasText: CODIGO }).count() >= 1,
      `buscar "${FRASE}" debería encontrar ${CODIGO}, que es lo que se acaba de cargar en "pedida como"`);

    // Y la ficha la muestra como chip.
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await sinOverlays(page);
    await page.waitForSelector('#secPedida', { timeout: 5000 });
    afirmar((await page.textContent('#secPedida')).includes(FRASE), 'la ficha debería mostrar la frase agregada en "Puede venir solicitada como"');
    await page.evaluate(() => { document.getElementById('closeDrawer')?.click(); });
    await page.click('#editModeBtn'); // apaga el modo edición del admin antes de salir

    // Médico administrador: entra, edita sólo relaciones (no ve "pedida como"
    // ni el resto de la ficha) y guarda. La frase agregada por el admin no
    // se tiene que perder.
    await page.evaluate(() => window.NBUNube && window.NBUNube.salir());
    await page.reload();
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
    await page.click('#editFichaBtn');
    await page.waitForSelector('#efInc', { timeout: 5000 });
    afirmar(await page.locator('#efPedidaComo').count() === 0, 'el médico administrador no debería ver el campo "pedida como"');
    await page.click('#efSave'); // guarda sin tocar nada: sólo relaciones (vacías) para esta ficha
    await page.waitForTimeout(400);

    await sinOverlays(page);
    await page.evaluate(() => { location.hash = ''; });
    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await page.waitForSelector('#secPedida', { timeout: 5000 });
    afirmar((await page.textContent('#secPedida')).includes(FRASE),
      'después de que el médico administrador edite sólo relaciones, "pedida como" no debería perderse');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
