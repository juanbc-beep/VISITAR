// Caso "contrataciones": el equipo de Contrataciones sube la grilla de valores
// pactados con un prestador y la app arma la grilla de carga del Único
// (nom_nom, cta_cdesde, cta_chasta, area, imp_esp/ayu/ane/gto, uni_esp/ayu/ane/gto),
// con una segunda hoja «Sin equivalencia». Ver HANDOFF.md 4.9.
//
// Restringido a CAP.contrataciones() (= admin, por ahora).
//
// La grilla de prueba reproduce lo que trae una grilla real (la de un centro de
// diagnóstico, agosto 2026): títulos arriba del encabezado, rangos "X al Y",
// listas abreviadas ("180201/04"), valores por unidad ("NN X", "NBU X"), un
// mismo código con valores distintos por región, renglones sin código.
// Todos los códigos son reales de la base salvo 999999.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8639;

const CSV = [
  'Grilla de valores - Prestador de prueba,,,,',
  ',,,,',
  'Código,Práctica,Área,Honorarios,Gastos',
  ',ECOGRAFIAS,,,',
  '180104 al 180121,Ecografia General Nomenclada,,,12487.57',
  '180201/04,Eco Doppler Color Cardíaco (cada region),,,59449.60',
  '420103,Consulta en consultorio,,25220.84,',
  '340101 al 340304,Radiologia Convencional Nomenclada,,,NN X 333.36',
  '340214,Escanograma,,,18037.60',
  'NBU,Laboratorio Nomenclado,,,NBU X 420.22',
  '341201,Densitometria 1 region,,,9712.55',
  '341201,Densitometria 2 regiones,,,20812.61',
  '010101,Encefalomeningocele,Internación,150000,80000',
  '999999,Práctica con código inventado,,,5000',
  ',ECG riesgo quirurgico,,,18378',
].join('\r\n');

async function sinOverlays(page) {
  await page.evaluate(() => {
    for (const id of ['pista', 'tratoModal']) { const e = document.getElementById(id); if (e) e.classList.remove('on'); }
  });
}

async function entrar(page, base, email) {
  await saltarOnboarding(page);
  await page.goto(base);
  await esperarArranque(page);
  await page.fill('#nbMail', email);
  await page.fill('#nbPass', 'Password123!');
  await page.click('#nbGo');
  await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
  await sinOverlays(page);
}

// Lee el archivo descargado con la misma SheetJS de la app: devuelve cada hoja como filas.
async function leerLibro(page, bytes) {
  return page.evaluate(b64 => {
    const wb = XLSX.read(b64, { type: 'base64' });
    return wb.SheetNames.map(n => ({ nombre: n, filas: XLSX.utils.sheet_to_json(wb.Sheets[n], { header: 1, defval: '' }) }));
  }, bytes.toString('base64'));
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('contrataciones: la grilla del prestador sale como grilla de carga del Único', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    const { errores, csp } = vigilarErrores(page);
    await entrar(page, base, 'admin@visitar.test');

    afirmar(await page.isVisible('#contrBtn'), 'el administrador general debería ver el botón de Contrataciones');
    await page.click('#contrBtn');
    await page.waitForSelector('#contrFile', { state: 'attached', timeout: 5000 });
    await page.setInputFiles('#contrFile', { name: 'grilla_prestador.csv', mimeType: 'text/csv', buffer: Buffer.from(CSV, 'utf-8') });
    await page.waitForSelector('.contr-tbl', { timeout: 5000 });

    afirmar(await page.inputValue('#contrFila') === '2', 'debería saltear los títulos y encontrar el encabezado en la fila 3');
    afirmar(await page.inputValue('#contrColCod') === '0', 'debería detectar la columna "Código"');
    afirmar(await page.inputValue('#contrColArea') === '2', 'debería detectar la columna "Área"');
    afirmar(await page.inputValue('[data-vrol="0"]') === 'esp', '"Honorarios" debería ir a imp_esp');
    afirmar(await page.inputValue('[data-vrol="1"]') === 'gto', '"Gastos" debería ir a imp_gto');

    // El código Único de las filas editables vive en un <input>: innerText no lo trae.
    const texto = (await page.$$eval('.contr-tbl tbody tr', trs => trs.map(tr =>
      ((tr.querySelector('.contr-cod') || {}).value || '') + ' ' + tr.innerText).join(' '))).replace(/\s+/g, ' ');
    afirmar(/180301[^]*Elegido por la práctica/.test(texto),
      '"180201/04 Eco Doppler Color Cardíaco" debería resolverse por la práctica a 180301 (Ecodoppler cardíaco color)');
    afirmar(texto.includes('999999') && texto.includes('Sin equivalencia en el Único'), '999999 debería quedar sin equivalencia');
    afirmar(texto.includes('ECG riesgo quirurgico') && texto.includes('Sin código en la fila'), 'el renglón sin código debería informarse');

    // A mano: el código inventado se reemplaza por uno del Único.
    await page.click('[data-filtro="err"]');
    await page.fill('.contr-cod[data-clave$="|999999"]', '180601');
    await page.press('.contr-cod[data-clave$="|999999"]', 'Enter');
    await page.waitForSelector('.contr-tbl tbody:has-text("Corregido a mano")', { timeout: 3000 }).catch(() => {});
    await page.click('[data-filtro="todo"]');
    afirmar((await page.locator('.contr-tbl tbody').innerText()).includes('Corregido a mano'), 'el código cargado a mano debería marcarse como corregido');

    // Densitometría por regiones: se elige el segundo valor en vez del primero.
    await page.click('.contr-tbl [data-elegir^="341201|"]');

    afirmar(await page.isDisabled('#contrDescargar'), 'sin nombre de archivo no debería dejar descargar');
    await page.fill('#contrNombre', '37547');
    afirmar(!(await page.isDisabled('#contrDescargar')), 'con nombre debería dejar descargar');
    const [download] = await Promise.all([page.waitForEvent('download'), page.click('#contrDescargar')]);
    afirmar(download.suggestedFilename() === '37547.xls', `el archivo debería llamarse "37547.xls", vino "${download.suggestedFilename()}"`);
    const { readFileSync } = await import('node:fs');
    const bytes = readFileSync(await download.path());
    afirmar(bytes[0] === 0xd0 && bytes[1] === 0xcf, 'el .xls debería ser un libro de Excel 97-2003 real (firma OLE D0 CF)');

    const libro = await leerLibro(page, bytes);
    afirmar(libro[0].nombre === '37547', `la primera hoja debería llamarse como el archivo, vino "${libro[0].nombre}"`);
    afirmar(libro[1] && libro[1].nombre === 'Sin equivalencia', 'debería haber una segunda hoja «Sin equivalencia»');
    const [enc, ...filas] = libro[0].filas;
    afirmar(enc.join() === 'nom_nom,cta_cdesde,cta_chasta,area,imp_esp,imp_ayu,imp_ane,imp_gto,uni_esp,uni_ayu,uni_ane,uni_gto',
      'el encabezado debería ser exactamente el de la grilla de carga: ' + enc.join());
    const fila = (d, a = 'D') => filas.find(f => f[1] === d && f[3] === a);
    const igual = (f, esperado, que) => afirmar(f && JSON.stringify(f) === JSON.stringify(esperado), `${que}: esperaba ${JSON.stringify(esperado)}, vino ${JSON.stringify(f)}`);
    afirmar(filas.every(f => f[0] === 'Unico'), 'nom_nom siempre "Unico"');
    igual(fila(180104), ['Unico', 180104, 180121, 'D', 0, 0, 0, 12487.57, '', '', '', ''], 'rango de la grilla');
    igual(fila(180301), ['Unico', 180301, 180301, 'D', 0, 0, 0, 59449.6, '', '', '', ''], '180201/04 -> una sola fila 180301');
    igual(fila(420103), ['Unico', 420103, 420103, 'D', 25220.84, 0, 0, 0, '', '', '', ''], 'honorarios -> imp_esp');
    igual(fila(340101), ['Unico', 340101, 340213, 'D', 0, 0, 0, 0, 'GALENO RADIOLOGICO', '', '', 'UNIDAD RADIOLOGICA'], 'rango radiológico por unidad, tramo 1');
    igual(fila(340214), ['Unico', 340214, 340214, 'D', 0, 0, 0, 18037.6, '', '', '', ''], 'código con valor propio dentro del rango');
    afirmar(fila(340215) && fila(340215)[2] === 340304, 'el rango radiológico debería seguir después de 340214 hasta 340304');
    igual(fila(60660001), ['Unico', 60660001, 64669990, 'D', 0, 0, 0, 0, '', '', '', 'UNICO_NBU'], 'NBU -> laboratorio completo del Único');
    igual(fila(341201), ['Unico', 341201, 341201, 'D', 0, 0, 0, 20812.61, '', '', '', ''], 'densitometría con el valor elegido');
    igual(fila(10101, 'I'), ['Unico', 10101, 10101, 'I', 150000, 0, 0, 80000, '', '', '', ''], 'dos importes y área de la fila');
    igual(fila(180601), ['Unico', 180601, 180601, 'D', 0, 0, 0, 5000, '', '', '', ''], 'código corregido a mano');
    afirmar(filas.length === 10, `esperaba 10 filas exportadas, vinieron ${filas.length}: ${JSON.stringify(filas.map(f => f[1]))}`);
    const numeros = filas.map(f => f[1]);
    afirmar(numeros.every((n, i) => !i || numeros[i - 1] <= n), 'las filas deberían salir ordenadas por código');

    const pend = libro[1].filas.slice(1).map(f => f.join(' | '));
    afirmar(pend.some(f => f.includes('ECG riesgo quirurgico') && f.includes('Sin código')), 'la hoja 2 debería listar el renglón sin código');
    afirmar(pend.some(f => f.includes('Densitometria 1 region') && f.includes('código repetido')), 'la hoja 2 debería listar el valor de densitometría que no se usó');
    afirmar(!pend.some(f => f.includes('999999')), '999999 ya se corrigió a mano: no debería quedar como pendiente');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('contrataciones: un usuario administrativo (no admin) no ve el botón', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Ana Activa', email: 'ana@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await entrar(page, base, 'ana@visitar.test');
    afirmar(await page.isHidden('#contrBtn'),
      'un usuario administrativo (no admin) no debería ver el botón de Contrataciones');
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
