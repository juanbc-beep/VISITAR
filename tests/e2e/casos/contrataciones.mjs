// Caso "contrataciones": el equipo de Contrataciones sube el Excel de un
// prestador (códigos del Nomenclador Nacional/PMO con el valor pactado) y la
// app devuelve el mismo archivo con el código y nombre equivalentes del
// Nomenclador Único agregados. No hay motor de matching nuevo: usa
// equivalencia_unico, ya calculado en cada código PMO por assemble.py.
//
// Restringido a CAP.contrataciones() (= admin, por ahora, a pedido explícito
// del usuario — "alcanza con restringirlo a admin por ahora").
//
// Los códigos de prueba son reales, elegidos a propósito para cubrir los seis
// estados que distingue la pantalla:
//   010217 -> equivalencia cargada a mano (score null)      = "confirmado"
//   010101 -> similitud automática alta (score 1.0)         = "automático"
//   01.02.02 (= 010202, con puntos) -> similitud automática baja (0.8782) = "revisar"
//     Además prueba un caso real de CSV: sin tipos de celda, un código con
//     puntos como "01.02.02" se confunde con una fecha (1/2/02) al leerlo —
//     contrCeldaCodigo() lo reconstruye antes de matchear.
//   010708 -> código PMO real, sin ninguna equivalencia Único cargada
//   999999 -> no es un código real (no existe en la base)
//   (fila vacía) -> sin código

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8639;

const CSV = [
  'Código Nomenclador,Prestación,Valor pactado',
  '010217,Cirugía hipertensión endocraneana,15000',
  '010101,Encefalomeningocele,22000',
  '01.02.02,Derivación ventriculoauricular,18000',
  '010708,Práctica sin equivalencia cargada,9000',
  '999999,Código que no existe,5000',
  ',Fila sin código,1000',
].join('\r\n');

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

  await correrCaso('contrataciones: el administrador sube la grilla del prestador y baja el Excel con las equivalencias', async () => {
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

    afirmar(await page.isVisible('#contrBtn'), 'el administrador general debería ver el botón de Contrataciones');
    await page.click('#contrBtn');
    await page.waitForSelector('#contrFile', { timeout: 5000 });

    await page.setInputFiles('#contrFile', {
      name: 'grilla_prestador.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(CSV, 'utf-8'),
    });
    await page.waitForSelector('#contrColSel', { timeout: 5000 });
    afirmar(await page.inputValue('#contrColSel') === '0',
      'debería auto-detectar la primera columna ("Código Nomenclador") como la del código');
    afirmar((await page.textContent('.ahint')).includes('6 filas'),
      'el resumen del archivo debería contar 6 filas de datos');

    await page.click('#contrProcesar');
    await page.waitForSelector('.contr-tbl', { timeout: 5000 });

    const filas = await page.locator('.contr-tbl tbody tr').allTextContents();
    afirmar(filas.length === 6, `esperaba 6 filas procesadas, vinieron ${filas.length}`);
    afirmar(filas.some(f => f.includes('010217') && f.includes('Confirmado')),
      '010217 (equivalencia cargada a mano) debería mostrar "Confirmado"');
    afirmar(filas.some(f => f.includes('010101') && f.includes('Automático')),
      '010101 (similitud 1.0) debería mostrar "Automático"');
    afirmar(filas.some(f => f.includes('010202') && f.includes('revisar')),
      '01.02.02 debería normalizarse a 010202 y mostrar "A revisar" (similitud 0.8782, bajo el umbral 0.88)');
    afirmar(filas.some(f => f.includes('010708') && f.includes('Sin equivalencia')),
      '010708 (sin equivalencia cargada) debería marcarse como pendiente, no quedar en blanco');
    afirmar(filas.some(f => f.includes('999999') && f.includes('no encontrado')),
      '999999 (código inventado) debería marcarse como no encontrado');
    afirmar(filas.some(f => f.includes('Sin código en la fila')),
      'la fila sin código debería marcarse, no procesarse en silencio');

    const chips = await page.locator('.contr-chip').count();
    afirmar(chips === 6, `el resumen debería mostrar los 6 estados distintos (uno por fila), vinieron ${chips}`);

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('#contrDescargar'),
    ]);
    afirmar(download.suggestedFilename() === 'grilla_prestador_equivalencias.xlsx',
      `el nombre descargado debería ser "grilla_prestador_equivalencias.xlsx", vino "${download.suggestedFilename()}"`);
    const ruta = await download.path();
    afirmar(!!ruta, 'la descarga debería completarse a un archivo en disco');
    const { readFileSync } = await import('node:fs');
    const bytes = readFileSync(ruta);
    afirmar(bytes[0] === 0x50 && bytes[1] === 0x4b,
      'el archivo descargado debería ser un .xlsx real (firma ZIP "PK"), no basura');
    afirmar(bytes.length > 500, 'el .xlsx descargado no debería estar vacío');

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
    await saltarOnboarding(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'ana@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    afirmar(await page.isHidden('#contrBtn'),
      'un usuario administrativo (no admin) no debería ver el botón de Contrataciones');
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
