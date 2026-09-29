// Caso "codigos_nuevos": el administrador general da de alta códigos que las
// fuentes oficiales no traen (módulo «Códigos nuevos») y quedan establecidos
// para todo el equipo. Ver HANDOFF.md y docs/supabase_codigos_nuevos.sql.
//
// Lo que se prueba, con códigos reales de la base:
//   · 010708 es un código PMO real sin equivalencia Único cargada. Un Único
//     nuevo (999001) que declara equivaler a él tiene que aparecer del otro
//     lado también («= Único» en la fila del PMO), y desaparecer al quitarlo.
//   · el código nuevo queda guardado en la base (tabla codigos_nuevos) y lo ve
//     otra persona del equipo, con la etiqueta «nuevo».
//   · lo opcional (equivalencia, cobertura, observación) se guarda y se ve.
//   · un código que ya existe no se puede duplicar.
//   · sólo el administrador general ve el botón.
//   · si la migración no se corrió, la app avisa en vez de fingir que guardó.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8641;

async function sinOverlays(page) {
  await page.evaluate(() => {
    const p = document.getElementById('pista'); if (p) p.classList.remove('on');
    const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on');
  });
}
// La pista contextual reaparece sola y tapa los botones de la barra: se aparta antes de cada clic.
async function clic(page, sel) { await sinOverlays(page); await page.click(sel); }
async function entrar(browser, db, base, email, con = {}) {
  const ctx = await nuevoContexto(browser);
  await instalarSimulador(ctx, db);
  const page = await ctx.newPage();
  await saltarOnboarding(page);
  const vig = vigilarErrores(page);
  await page.goto(base + (con.hash ? '#' + con.hash : ''));
  await esperarArranque(page);
  await page.fill('#nbMail', email);
  await page.fill('#nbPass', 'Password123!');
  await page.click('#nbGo');
  await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
  await sinOverlays(page);
  return { ctx, page, ...vig };
}
// Busca en un nomenclador y devuelve la fila (o null).
async function fila(page, modo, q, key) {
  await sinOverlays(page);   // la pista contextual reaparece sola y tapa los botones
  await page.click(`.modebtn[data-mode="${modo}"]`);
  await page.fill('#q', q);
  const loc = page.locator(`.row[data-code="${key}"]`);
  try { await loc.waitFor({ timeout: 4000 }); } catch (e) { return null; }
  return loc;
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('codigos nuevos: el administrador da de alta un código con equivalencia, cobertura y observación', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    altaUsuario(db, { nombre: 'Ana Activa', email: 'ana@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
    const { ctx, page, errores, csp } = await entrar(browser, db, base, 'admin@visitar.test');

    afirmar(await page.isVisible('#nuevosBtn'), 'el administrador general debería ver el botón «Códigos nuevos»');

    // Antes: el PMO 010708 no tiene equivalencia Único.
    const antes = await fila(page, 'PMO', '010708', '010708');
    afirmar(antes, 'el código PMO 010708 debería existir en la base');
    afirmar(!(await antes.locator('.t-unico').count()), '010708 no debería mostrar «= Único» todavía');

    await clic(page, '#nuevosBtn');
    await page.waitForSelector('#nvNuevo', { timeout: 5000 });
    afirmar((await page.textContent('#nuevosBox')).includes('Todavía no cargaste ningún código nuevo'),
      'sin códigos nuevos debería mostrar el estado vacío explicativo');
    await page.click('#nvNuevo');
    await page.waitForSelector('#nvCode');

    // Lo obligatorio: se puede guardar sin nada más.
    await page.click('#nvGuardar');
    afirmar((await page.textContent('#nvErr')).includes('Falta el código'), 'sin código debería avisar «Falta el código»');
    await page.fill('#nvCode', '010101');
    await page.click('#nvNom button[data-v="PMO"]');           // cambia de nomenclador conservando lo escrito
    afirmar(await page.inputValue('#nvCode') === '010101', 'al cambiar de nomenclador no debería perderse el código escrito');
    await page.waitForFunction(() => document.getElementById('nvCodeMsg').textContent.includes('Ya existe'));
    await page.fill('#nvNombre', 'Duplicada');
    await page.click('#nvGuardar');
    afirmar((await page.textContent('#nvErr')).includes('Ya existe el código 010101'), 'un código existente no se puede duplicar');

    // Ahora el de verdad: Único 999001.
    await page.click('#nvNom button[data-v="UNICO"]');
    await page.fill('#nvCode', '999001');
    await page.waitForFunction(() => document.getElementById('nvCodeMsg').textContent.includes('Disponible'));
    await page.fill('#nvNombre', 'Prueba de resonancia de rodilla con contraste');
    await page.fill('#nvGrupo', 'Códigos de prueba');

    await page.click('#nvSecEq > summary');
    await page.fill('#nvEqQ', '010708');
    await page.waitForSelector('.nv-op');
    afirmar((await page.textContent('.nv-op')).includes('010708'), 'la búsqueda de equivalencia debería ofrecer el 010708');
    await page.click('.nv-op');
    afirmar((await page.textContent('#nvEqChips')).includes('010708'), 'el 010708 debería quedar como equivalencia elegida');

    await page.click('#nvSecCob > summary');
    await page.click('#nvCobTipo button[data-v="obligacion"]');
    await page.fill('#nvCobTexto', 'Pacientes con diagnóstico confirmado de prueba.');
    await page.click('#nvSecObs > summary');
    await page.fill('#nvObs', 'Pedir orden con diagnóstico (observación de prueba).');

    await page.click('#nvGuardar');
    await page.waitForSelector('.nv-item', { timeout: 6000 });
    const item = await page.textContent('.nv-item');
    afirmar(item.includes('999001') && item.includes('Prueba de resonancia'), `el listado debería mostrar el código nuevo, vino: ${item}`);
    afirmar(item.includes('= 010708'), 'el listado debería resumir la equivalencia');
    afirmar(item.includes('obligación de cobertura'), 'el listado debería marcar la cobertura');

    // Quedó en la base compartida.
    const enBase = db.codigosNuevos.get('U999001');
    afirmar(enBase && enBase.datos.nom === 'UNICO' && enBase.datos.eq[0] === '010708',
      'la fila debería estar en la tabla codigos_nuevos con clave U999001');
    // Una sola observación por práctica: como el Único nuevo equivale al 010708, se guarda ahí (ver claveObs).
    afirmar(db.observaciones.has('010708') && db.observaciones.get('010708').texto.includes('observación de prueba'),
      'la observación debería haberse guardado con el mecanismo de siempre, del lado del PMO');

    // Se ve como cualquier otro código, con su etiqueta.
    await page.click('#nvCerrar');
    await sinOverlays(page);
    const f = await fila(page, 'UNICO', '999001', 'U999001');
    afirmar(f, 'el código nuevo debería encontrarse en el buscador del Único');
    afirmar(await f.locator('.t-nuevo').count(), 'la fila debería llevar la etiqueta «nuevo»');
    afirmar((await f.locator('.t-unico').allTextContents()).join().includes('Prestaciones Médicas'),
      'la fila debería decir que equivale a Prestaciones Médicas');
    afirmar(await f.locator('.t-cob').count(), 'la fila debería llevar la etiqueta de cobertura');
    afirmar(await f.locator('.robs').count(), 'la fila debería mostrar la observación');

    // El otro lado de la equivalencia.
    const despues = await fila(page, 'PMO', '010708', '010708');
    afirmar(despues && (await despues.locator('.t-unico').count()), '010708 debería mostrar ahora «= Único» (espejo de la equivalencia)');

    // La ficha.
    await page.evaluate(() => { location.hash = 'U999001'; });
    await page.waitForSelector('#drawer.on', { timeout: 5000 });
    await sinOverlays(page);
    const ficha = await page.textContent('#drawer');
    afirmar(ficha.includes('Código nuevo'), 'la ficha debería decir que es un código nuevo');
    afirmar(ficha.includes('Pacientes con diagnóstico confirmado de prueba'), 'la ficha debería mostrar la cobertura cargada');
    await page.evaluate(() => { document.getElementById('closeDrawer').click(); });

    // Otra persona del equipo lo ve.
    const otra = await entrar(browser, db, base, 'ana@visitar.test');
    afirmar(await otra.page.isHidden('#nuevosBtn'), 'un administrativo no debería ver el botón «Códigos nuevos»');
    const g = await fila(otra.page, 'UNICO', '999001', 'U999001');
    afirmar(g, 'otra persona del equipo debería ver el código nuevo');
    afirmar(await g.locator('.t-nuevo').count(), 'y con su etiqueta «nuevo»');
    await otra.ctx.close();

    // Un enlace directo al código nuevo (lo que se copia con «Pasar a un compañero») abre la ficha,
    // aunque al arrancar el código todavía no existía: llega con el contenido del equipo.
    const enlace = await entrar(browser, db, base, 'ana@visitar.test', { hash: 'U999001' });
    await enlace.page.waitForSelector('#drawer.on', { timeout: 6000 });
    afirmar((await enlace.page.textContent('#drawer')).includes('Prueba de resonancia'),
      'el enlace directo a un código nuevo debería abrir su ficha');
    await enlace.ctx.close();

    // Sigue ahí después de recargar.
    await page.reload(); await esperarArranque(page);   // la sesión guardada vuelve a entrar sola
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 8000 });
    await sinOverlays(page);
    afirmar(await fila(page, 'UNICO', '999001', 'U999001'), 'el código nuevo debería seguir ahí tras recargar');

    // Editar y quitar.
    await clic(page, '#nuevosBtn');
    await page.waitForSelector('[data-nved]');
    await page.click('[data-nved="U999001"]');
    await page.waitForSelector('#nvNombre');
    await page.fill('#nvNombre', 'Prueba de resonancia de rodilla — corregida');
    await page.click('#nvGuardar');
    await page.waitForSelector('.nv-item');
    afirmar((await page.textContent('.nv-item')).includes('corregida'), 'editar debería actualizar la denominación');
    afirmar(db.codigosNuevos.get('U999001').datos.nombre.includes('corregida'), 'y guardarse en la base');

    page.once('dialog', d => d.accept());
    await page.click('[data-nved="U999001"]');
    await page.waitForSelector('#nvBorrar');
    await page.click('#nvBorrar');
    await page.waitForSelector('#nvNuevo');
    afirmar(!db.codigosNuevos.has('U999001'), 'quitar debería borrarlo de la base');
    await page.click('#nvCerrar');
    await sinOverlays(page);
    await page.fill('#q', '');
    afirmar(!(await fila(page, 'UNICO', '999001', 'U999001')), 'el código quitado no debería seguir apareciendo');
    const pmo = await fila(page, 'PMO', '010708', '010708');
    afirmar(pmo && !(await pmo.locator('.t-unico').count()), '010708 debería volver a estar como antes: sin «= Único»');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('codigos nuevos: un PMO nuevo con equivalencia al Único la muestra de los dos lados', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const { ctx, page, errores, csp } = await entrar(browser, db, base, 'admin@visitar.test');
    await clic(page, '#nuevosBtn');
    await page.click('#nvNuevo');
    await page.waitForSelector('#nvCode');
    await page.click('#nvNom button[data-v="PMO"]');
    await page.fill('#nvCode', '999002');
    await page.fill('#nvNombre', 'Práctica médica nueva de prueba');
    await page.click('#nvSecEq > summary');
    await page.fill('#nvEqQ', '430101');
    await page.waitForSelector('.nv-op');
    const opciones = await page.locator('.nv-op').allTextContents();
    afirmar(opciones.every(t => t.includes('Único')), 'para un código PMO sólo se deberían ofrecer códigos del Único');
    await page.click('.nv-op');
    await page.click('#nvGuardar');
    await page.waitForSelector('.nv-item', { timeout: 6000 });
    await page.click('#nvCerrar'); await sinOverlays(page);
    const f = await fila(page, 'PMO', '999002', '999002');
    afirmar(f && (await f.locator('.t-unico').count()), 'el PMO nuevo debería mostrar «= Único»');
    afirmar(f && (await f.locator('.t-nuevo').count()), 'y la etiqueta «nuevo»');
    afirmar(errores.length === 0, 'sin errores de JS: ' + errores.join(' | '));
    afirmar(csp.length === 0, 'sin violaciones de CSP');
    await ctx.close();
  });

  await correrCaso('codigos nuevos: el médico administrador no ve el botón', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Med Admin', email: 'med@visitar.test', password: 'Password123!', rol: 'medico_admin', estado: 'activo' });
    const { ctx, page } = await entrar(browser, db, base, 'med@visitar.test');
    afirmar(await page.isHidden('#nuevosBtn'), 'el médico administrador no debería ver «Códigos nuevos»');
    await ctx.close();
  });

  await correrCaso('codigos nuevos: sin la migración, avisa en vez de fingir que guardó', async () => {
    const db = crearDB(); db.sinTablaCodigosNuevos = true;
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const { ctx, page, errores } = await entrar(browser, db, base, 'admin@visitar.test');
    await clic(page, '#nuevosBtn');
    await page.click('#nvNuevo');
    await page.fill('#nvCode', '999003');
    await page.fill('#nvNombre', 'No debería guardarse');
    await page.click('#nvGuardar');
    await page.waitForSelector('#nvErr:not([hidden])', { timeout: 5000 });
    afirmar((await page.textContent('#nvErr')).includes('supabase_codigos_nuevos.sql'),
      'debería explicar que falta correr la migración');
    await page.click('#nvCancelar');
    afirmar(!(await page.textContent('#nuevosBox')).includes('999003'), 'no debería quedar ningún código a medias en la lista');
    // El 404 de la tabla que falta es el propio navegador avisando de la respuesta: es lo que se simula.
    const propios = errores.filter(e => !/404/.test(e));
    afirmar(propios.length === 0, 'la app no debería romperse: ' + propios.join(' | '));
    await ctx.close();
  });

  await correrCaso('codigos nuevos: el respaldo los incluye y Restaurar los devuelve (y un respaldo viejo no los borra)', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const { ctx, page, errores, csp } = await entrar(browser, db, base, 'admin@visitar.test');
    // Uno cargado por la pantalla…
    await clic(page, '#nuevosBtn');
    await page.click('#nvNuevo');
    await page.fill('#nvCode', '999004');
    await page.fill('#nvNombre', 'Cargado a mano');
    await page.click('#nvGuardar');
    await page.waitForSelector('.nv-item', { timeout: 6000 });
    await page.click('#nvCerrar'); await sinOverlays(page);
    afirmar(db.codigosNuevos.has('U999004'), 'debería estar guardado');

    // …el respaldo lo lleva adentro…
    await clic(page, '#adminBtn');
    await page.click('.atab[data-t="respaldo"]');
    const [descarga] = await Promise.all([page.waitForEvent('download'), page.click('#bkExp')]);
    const { readFileSync } = await import('node:fs');
    const doc = JSON.parse(readFileSync(await descarga.path(), 'utf8'));
    afirmar(doc.content.nuevos && doc.content.nuevos.U999004 && doc.content.nuevos.U999004.nombre === 'Cargado a mano',
      'el respaldo debería llevar los códigos nuevos');

    // …un respaldo con otro código nuevo: Restaurar agrega el suyo y quita el que no figura.
    const otro = JSON.parse(JSON.stringify(doc));
    otro.content.nuevos = { U999005: { v: 1, nom: 'UNICO', code: '999005', nombre: 'Del respaldo', eq: [], alta: { por: 'X', t: 1 } } };
    await page.setInputFiles('#bkImp', { name: 'r.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(otro)) });
    await page.waitForSelector('#bkGo');
    const previa = await page.textContent('#bkPrev');
    afirmar(previa.includes('código nuevo') && previa.includes('999005') && previa.includes('U999004'),
      `la vista previa debería nombrar los códigos nuevos que se agregan y se quitan, vino: ${previa}`);
    page.once('dialog', d => d.accept());
    await page.click('#bkGo');
    for (let i = 0; i < 40 && !(db.codigosNuevos.has('U999005') && !db.codigosNuevos.has('U999004')); i++) await page.waitForTimeout(200);
    afirmar(db.codigosNuevos.has('U999005') && !db.codigosNuevos.has('U999004'),
      'Restaurar debería dejar la tabla como el respaldo: con 999005 y sin 999004');

    // Un respaldo de antes de que existiera esta función no trae «nuevos»: no puede borrarlos.
    const viejo = JSON.parse(JSON.stringify(doc)); delete viejo.content.nuevos;
    await page.setInputFiles('#bkImp', { name: 'viejo.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(viejo)) });
    await page.waitForSelector('#bkPrev *', { timeout: 5000 });
    afirmar(!(await page.textContent('#bkPrev')).includes('código nuevo'),
      'un respaldo viejo no debería proponer borrar los códigos nuevos');
    afirmar(db.codigosNuevos.has('U999005'), 'y los códigos nuevos siguen en la base');
    afirmar(errores.length === 0, 'sin errores de JS: ' + errores.join(' | '));
    afirmar(csp.length === 0, 'sin violaciones de CSP');
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
