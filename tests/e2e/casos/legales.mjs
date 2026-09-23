// Caso "legales": páginas de privacidad, términos y cookies, y el
// consentimiento que la app pide y registra (ver HANDOFF.md, 23/9/2026).
//
//   - Las tres páginas cargan, se enlazan entre sí, no ejecutan scripts ni
//     piden nada a otro sitio, y la app las enlaza desde el acceso y el pie.
//   - Crear una cuenta exige aceptar Términos + Privacidad (incluida la
//     transferencia internacional) y guarda versión y fecha en la cuenta.
//   - Una cuenta que no aceptó la versión vigente la acepta una sola vez al
//     entrar; si ya la aceptó en otro dispositivo, no se le vuelve a pedir.
//   - Minimización: del Intérprete de orden no sale nada que identifique al
//     paciente.

import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { crearDB, altaUsuario, instalarSimulador, LEGALES_VERSION } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto, WEB_DIR } from '../arranque.mjs';

const PUERTO = 8644;
const PAGINAS = [
  ['privacy-policy.html', 'Política de privacidad'],
  ['terms-conditions.html', 'Términos y condiciones de uso'],
  ['cookie-policy.html', 'Cookies y almacenamiento en tu dispositivo'],
];

async function login(page, email) {
  await page.fill('#nbMail', email);
  await page.fill('#nbPass', 'Password123!');
  await page.click('#nbGo');
}
async function sinOverlays(page) {
  await page.evaluate(() => { const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on'); });
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('legales: las tres páginas cargan sin scripts ni terceros y se enlazan entre sí', async () => {
    const ctx = await nuevoContexto(browser);
    const page = await ctx.newPage();
    const { errores, csp } = vigilarErrores(page);
    const ajenos = [];
    page.on('request', r => { if (!r.url().startsWith(base)) ajenos.push(r.url()); });
    for (const [archivo, titulo] of PAGINAS) {
      const html = readFileSync(path.join(WEB_DIR, archivo), 'utf8');
      afirmar(!/<script/i.test(html), `${archivo} no debería tener scripts`);
      afirmar(/Content-Security-Policy/.test(html) && /default-src 'none'/.test(html), `${archivo} debería tener su CSP cerrada`);
      const r = await page.goto(base + archivo);
      afirmar(r && r.ok(), `${archivo} debería cargar (HTTP ${r && r.status()})`);
      afirmar((await page.textContent('h1')).trim() === titulo, `${archivo}: el título debería ser "${titulo}"`);
      for (const [otro] of PAGINAS) afirmar(await page.locator(`.nav a[href="${otro}"]`).count() === 1, `${archivo} debería enlazar a ${otro}`);
      afirmar(await page.locator('.nav a[aria-current="page"]').getAttribute('href') === archivo, `${archivo} debería marcarse como la página actual`);
      afirmar(await page.locator('a.volver[href="./"]').count() === 1, `${archivo} debería tener «Volver al manual»`);
      const fuente = await page.evaluate(() => getComputedStyle(document.body).fontFamily);
      afirmar(fuente.includes('IBM Plex Sans'), `${archivo} debería usar la tipografía de la app, vino ${fuente}`);
    }
    const priv = readFileSync(path.join(WEB_DIR, 'privacy-policy.html'), 'utf8');
    afirmar(priv.includes('AGENCIA DE ACCESO A LA INFORMACIÓN PÚBLICA') && priv.includes('artículo 14, inciso 3 de la Ley N° 25.326'),
      'la política de privacidad debería incluir la leyenda obligatoria de la Disposición DNPDP 10/2008');
    afirmar(ajenos.length === 0, 'las páginas legales no deberían pedir nada a otro sitio: ' + ajenos.join(' | '));
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('legales: crear una cuenta exige aceptar términos y privacidad, y queda registrado', async () => {
    const db = crearDB();
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    afirmar(await page.locator('.glegales a[href="privacy-policy.html"]').count() === 1, 'la pantalla de acceso debería enlazar a la política de privacidad');
    await page.click('#nbNew');
    await page.fill('#naNom', 'Nora Nueva');
    await page.fill('#naMail', 'nora@visitar.test');
    await page.fill('#naPass', 'Password123!');
    await page.fill('#naPass2', 'Password123!');
    await page.click('#naGo');
    afirmar((await page.textContent('#gErr')).includes('aceptar'), 'sin marcar la casilla no debería crear la cuenta');
    afirmar(!db.users.has('nora@visitar.test'), 'sin aceptar, la cuenta no debería llegar a la nube');
    await page.check('#naAcepto');
    await page.click('#naGo');
    await page.waitForFunction(() => !document.getElementById('naGo'));
    const u = db.users.get('nora@visitar.test');
    afirmar(u && u.meta.legales_version === LEGALES_VERSION, 'la cuenta debería guardar la versión aceptada');
    afirmar(u && !isNaN(Date.parse(u.meta.legales_aceptado_en)), 'la cuenta debería guardar la fecha de aceptación');
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('legales: una cuenta que no aceptó la versión vigente la acepta una sola vez al entrar', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Vieja Cuenta', email: 'vieja@visitar.test', password: 'Password123!', legales: '2020-01-01' });
    altaUsuario(db, { nombre: 'Sin Aceptar', email: 'no@visitar.test', password: 'Password123!', legales: null });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    // «Cerrar sesión» en el aviso no deja entrar.
    await login(page, 'no@visitar.test');
    await page.waitForSelector('#lgGo');
    await page.click('#lgSalir');
    await page.waitForSelector('#nbMail');
    afirmar(await page.isHidden('#acctChip'), 'sin aceptar no debería entrar a la app');

    await login(page, 'vieja@visitar.test');
    await page.waitForSelector('#lgGo');
    afirmar((await page.textContent('.gcard h2')).includes('Antes de seguir'), 'debería pedir aceptar la versión nueva');
    await page.click('#lgGo');
    afirmar((await page.textContent('#gErr')).includes('aceptar'), 'sin marcar la casilla no debería entrar');
    await page.check('#lgAcepto');
    await page.click('#lgGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(db.users.get('vieja@visitar.test').meta.legales_version === LEGALES_VERSION, 'la aceptación debería quedar guardada en la cuenta');
    afirmar(await page.locator('.au-legales a[href="terms-conditions.html"]').count() === 1, 'el pie de la app debería enlazar a los términos');

    await page.reload();
    await esperarArranque(page);
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(!(await page.$('#lgGo')), 'ya aceptada, al volver a abrir la app no debería pedirla de nuevo');
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('legales: si ya la aceptó en otro dispositivo, no se le vuelve a pedir', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Dos Equipos', email: 'dos@visitar.test', password: 'Password123!', legales: null });
    const ctxB = await nuevoContexto(browser);
    await instalarSimulador(ctxB, db);
    const b = await ctxB.newPage();
    await saltarOnboarding(b);
    await b.goto(base);
    await esperarArranque(b);
    await login(b, 'dos@visitar.test');
    await b.waitForSelector('#lgGo');           // la sesión de B quedó guardada sin la aceptación

    const ctxA = await nuevoContexto(browser);
    await instalarSimulador(ctxA, db);
    const a = await ctxA.newPage();
    await saltarOnboarding(a);
    await a.goto(base);
    await esperarArranque(a);
    await login(a, 'dos@visitar.test');
    await a.waitForSelector('#lgGo');
    await a.check('#lgAcepto');
    await a.click('#lgGo');
    await a.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });

    await b.reload();
    await esperarArranque(b);
    await b.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(!(await b.$('#lgGo')), 'aceptada en otro dispositivo, este no debería volver a pedirla');
    await ctxA.close(); await ctxB.close();
  });

  await correrCaso('legales: del Intérprete de orden no sale nada que identifique al paciente', async () => {
    const ctx = await nuevoContexto(browser);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    await page.goto(base);
    await esperarArranque(page);
    const casos = {
      'Glucemia': 'Glucemia',
      'Rx tórax F y P': 'Rx tórax F y P',
      'Hemograma x2': 'Hemograma x2',
      'Colesterol HDL y LDL': 'Colesterol HDL y LDL',
      'Sra. López Ecografía mamaria bilateral': '',
      'Pérez Juan Carlos DNI 30.123.456 - Hemograma completo': '',
      'Paciente: María González, afiliado 123456789/01': '',
      'Tel 11-4567-8901 urocultivo': '',
      'Martínez 45 años RMN rodilla derecha': '',
      'Gómez Rodríguez': '',
      'Hemograma 30123456': 'Hemograma',
    };
    const vino = await page.evaluate(cs => Object.fromEntries(Object.keys(cs).map(c => [c, window.NBUPrivacidad.textoSugerible(c)])), casos);
    for (const [entrada, esperado] of Object.entries(casos))
      afirmar(vino[entrada] === esperado, `"${entrada}" debería mandar ${JSON.stringify(esperado)}, mandó ${JSON.stringify(vino[entrada])}`);
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
