// Caso "editar_propuesta": el administrador puede corregir el texto de una
// propuesta ("Contá cómo se carga acá") antes de aprobarla, en vez de tener
// que descartarla entera y pedirle al agente que la vuelva a escribir por un
// typo. Cubre las dos formas de guardar el cambio:
//   1. "Guardar cambios" — persiste la corrección aparte, se puede aprobar
//      después (incluso en otra visita al panel).
//   2. Editar y "Aprobar" directo, sin guardar antes — tiene que publicarse
//      lo último que quedó escrito, no el texto original.
// Ver web/index.html: NUBE.editarPropuesta(), el tab "propuestas" de
// renderPane() (data-psave/data-pact), y HANDOFF.md, 26/8/2026.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8623;
// ACTO BIOQUÍMICO / HEMOGRAMA — códigos NBU reales y estables (data/nbu_db.json).
const CODIGO_1 = '660001';
const CODIGO_2 = '660475';
const TEXTO_TYPO = 'Se carga con modalidad ambulatoria, no ace falta orden previa.';
const TEXTO_CORREGIDO = 'Se carga con modalidad ambulatoria, no hace falta orden previa.';
const TEXTO_2 = 'Va siempre junto con la glucemia en ayunas.';
const TEXTO_2_EDITADO = 'Va siempre junto con la glucemia en ayunas (control post-quirúrgico).';

async function sinOverlays(page) {
  await page.evaluate(() => {
    const p = document.getElementById('pista'); if (p) p.classList.remove('on');
    const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on');
  });
}

async function proponer(page, codigo, texto) {
  await page.evaluate((c) => { location.hash = c; }, codigo);
  await sinOverlays(page);
  await page.waitForSelector('#propAbrir', { timeout: 5000 });
  await page.click('#propAbrir');
  await page.fill('#propTxt', texto);
  await page.click('#propEnviar');
  await page.waitForTimeout(300); // guardarCorreccion/crearPropuesta es fire-and-forget
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('editar_propuesta: el administrador corrige el texto antes de aprobarla, guardando aparte o al aprobar directo', async () => {
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

    // Ana escribe dos propuestas, una con un error de tipeo.
    await page.fill('#nbMail', 'ana@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await proponer(page, CODIGO_1, TEXTO_TYPO);
    await proponer(page, CODIGO_2, TEXTO_2);

    // Admin: entra a Administración → Pendientes. Se limpia el hash antes de
    // recargar: si no, el arranque reabre la ficha de CODIGO_2 sola (mismo
    // código que la dejó abierta el último "proponer") y el drawer tapa
    // "#adminBtn" — ver el "initial=location.hash" al final de web/index.html.
    await page.evaluate(() => { location.hash = ''; });
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
    await page.click('.atab[data-t="propuestas"]');
    await page.waitForSelector('.prop-edittxt', { timeout: 5000 });
    afirmar(await page.locator('.prop-edittxt').count() === 2, 'deberían verse las dos propuestas de Ana');

    // --- Camino 1: editar y "Guardar cambios" primero, aprobar después. ---
    const fila1 = page.locator('.arow', { hasText: CODIGO_1 });
    const ta1 = fila1.locator('.prop-edittxt');
    afirmar((await ta1.inputValue()) === TEXTO_TYPO, 'el textarea debería traer el texto tal como lo escribió Ana, typo incluido');
    const guardar1 = fila1.locator('[data-psave]');
    afirmar(await guardar1.isDisabled(), '"Guardar cambios" debería empezar deshabilitado, sin nada editado todavía');
    await ta1.fill(TEXTO_CORREGIDO);
    afirmar(!(await guardar1.isDisabled()), 'al editar el texto, "Guardar cambios" debería habilitarse');
    await guardar1.click();
    await page.waitForTimeout(300);
    afirmar(await guardar1.isDisabled(), 'guardado, el botón debería volver a quedar deshabilitado');

    // Del lado del simulador ya quedó corregida, aunque todavía no se aprobó.
    const propTypo = [...db.propuestas.values()].find(p => p.codigo === CODIGO_1);
    afirmar(!!propTypo && propTypo.texto === TEXTO_CORREGIDO, 'la corrección debería haber llegado a la nube antes de aprobar');
    afirmar(propTypo.estado === 'pendiente', 'guardar el texto no debería aprobarla sola');

    await fila1.locator('[data-pact="ok"]').click();
    await page.waitForTimeout(300);

    // --- Camino 2: editar y "Aprobar" directo, sin pasar por "Guardar". ---
    const fila2 = page.locator('.arow', { hasText: CODIGO_2 });
    await fila2.locator('.prop-edittxt').fill(TEXTO_2_EDITADO);
    await fila2.locator('[data-pact="ok"]').click();
    await page.waitForTimeout(300);

    afirmar((await page.textContent('#aPane')).includes('No hay propuestas pendientes'),
      'aprobadas las dos, no debería quedar ninguna propuesta pendiente');

    // Las dos fichas muestran el texto CORREGIDO, no el original.
    await page.click('#aClose');
    await page.evaluate((c) => { location.hash = c; }, CODIGO_1);
    await sinOverlays(page);
    await page.waitForSelector('.cg-nota .nt', { timeout: 5000 });
    afirmar((await page.textContent('.cg-nota .nt')).includes(TEXTO_CORREGIDO),
      `${CODIGO_1} debería mostrar el texto corregido, no el que tenía el typo`);

    await page.evaluate((c) => { location.hash = c; }, CODIGO_2);
    await sinOverlays(page);
    await page.waitForSelector('.cg-nota .nt', { timeout: 5000 });
    afirmar((await page.textContent('.cg-nota .nt')).includes(TEXTO_2_EDITADO),
      `${CODIGO_2} debería mostrar el texto editado al momento de aprobar, no el original`);

    // Y la fila de la nube quedó igual — la aprobación directa también
    // guarda la corrección, no sólo lo publicado en la ficha.
    const prop2 = [...db.propuestas.values()].find(p => p.codigo === CODIGO_2);
    afirmar(!!prop2 && prop2.texto === TEXTO_2_EDITADO && prop2.estado === 'aprobada',
      'la propuesta de la nube debería quedar con el texto editado y marcada aprobada');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
