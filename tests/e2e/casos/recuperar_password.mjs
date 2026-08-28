// Caso "recuperar_password": administrativos reportaron que al abrir el
// correo de "restablecer contraseña" les daba un error de acceso.
//
// Causa documentada (ver docs/INSTALACION.md, 1.3 bis, y HANDOFF.md): el
// enlace del correo depende de "Site URL", un ajuste del panel de Supabase
// que vive AFUERA de este repositorio. Si ese ajuste quedó apuntando a
// localhost (el valor de fábrica de Supabase) o a una dirección vieja, el
// enlace lleva a un lugar que no existe y el navegador contesta "No se
// puede acceder" — ni siquiera llega a esta app.
//
// Arreglo de este lado: NUBE.recuperar() ahora manda `redirect_to` en el
// pedido, calculado de la dirección real donde corre la app en ESE momento
// (location.origin+pathname). Sigue exigiendo que esa dirección esté en la
// lista de "Redirect URLs" del panel (mismo paso 1.3 bis), pero ya no
// depende exclusivamente de que "Site URL" esté bien puesto — si alguna vez
// se resetea o queda mal configurado en el panel, el enlace sigue andando.
//
// Esto prueba lo que SÍ se puede probar sin un panel de Supabase real:
//   1. que el pedido de recuperación manda ese redirect_to,
//   2. que un enlace vencido/inválido (Supabase contesta error en el propio
//      enlace, no con una sesión) muestra "el enlace ya no sirve" en vez de
//      romperse,
//   3. que un enlace válido (con access_token real) deja elegir la
//      contraseña nueva y termina la operación de punta a punta.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, emitirTokens, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8661;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('recuperar_password: el pedido manda redirect_to con la dirección real de la app', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    await page.click('#nbOlvide');
    await page.waitForSelector('#olMail', { timeout: 5000 });
    await page.fill('#olMail', 'admin@visitar.test');
    await page.click('#olGo');
    await page.waitForSelector('#gErr:has-text("Si esa cuenta existe")', { timeout: 5000 });

    afirmar(db.recovers.length === 1, 'debería haber quedado un pedido de recuperación registrado');
    afirmar(db.recovers[0].email === 'admin@visitar.test', 'el pedido debería ser para el correo cargado');
    afirmar(!!db.recovers[0].redirect_to, 'el pedido debería mandar redirect_to (antes no se mandaba ninguno)');
    afirmar(db.recovers[0].redirect_to === base, `redirect_to debería ser la dirección real de la app (${base}); mandó "${db.recovers[0].redirect_to}"`);

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await correrCaso('recuperar_password: un enlace vencido o ya usado avisa en vez de romperse', async () => {
    const db = crearDB();
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    // Así vuelve Supabase cuando el enlace ya venció o se usó: error en el
    // propio fragmento de la URL, no una sesión.
    await page.goto(base + '#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired');
    await esperarArranque(page);

    await page.waitForSelector('#gate:not([hidden])', { timeout: 5000 });
    afirmar((await page.locator('#gate').textContent() || '').includes('El enlace ya no sirve'),
      'un enlace vencido debería mostrar "El enlace ya no sirve", no romperse ni quedar en blanco');
    afirmar(await page.locator('#npVolver').isVisible(), 'debería ofrecer volver al inicio para pedir uno nuevo');

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await correrCaso('recuperar_password: un enlace válido deja elegir la contraseña nueva y entra', async () => {
    const db = crearDB();
    const uid = altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    // Un access_token real, emitido para esa cuenta — así vuelve Supabase
    // desde un enlace de recuperación válido.
    const { access_token, refresh_token } = emitirTokens(db, uid);
    await page.goto(base + `#access_token=${access_token}&refresh_token=${refresh_token}&type=recovery`);
    await esperarArranque(page);

    await page.waitForSelector('#gate:not([hidden])', { timeout: 5000 });
    afirmar((await page.locator('#gate').textContent() || '').includes('Elegí tu contraseña nueva'),
      'un enlace válido debería llevar directo a elegir la contraseña nueva');

    await page.fill('#cpUna', 'NuevaPassword456!');
    await page.fill('#cpDos', 'NuevaPassword456!');
    await page.click('#cpGo');
    // El botón dice "Guardar y entrar", pero lo que hace hoy es guardar y
    // volver al login (ver web/index.html, rama 'nubeNuevaPass'): no arma
    // sesión sola con el token de recuperación, pide entrar de nuevo con la
    // contraseña recién puesta. Documentado así a propósito acá — si el
    // texto del botón se corrige para que refleje esto, o si se decide que
    // sí debería entrar directo, este caso es el que hay que actualizar.
    await page.waitForSelector('#nbMail', { timeout: 5000 });
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'NuevaPassword456!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'con la contraseña nueva debería poder entrar');

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await browser.close();
  await new Promise((resolve) => srv.close(resolve));
}

main().then(() => process.exit(process.exitCode || 0));
