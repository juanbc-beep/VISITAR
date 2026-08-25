// Caso "mfa": verificación en dos pasos (TOTP) para el administrador general,
// con "confiar en este dispositivo" para no pedir el código en cada login.
//
// Cubre el circuito completo: alta propia desde "Tu cuenta" (QR + código
// manual + confirmación, rechazando un código incorrecto antes de aceptar el
// bueno) confía SOLO en ese dispositivo; desde ahí se puede "dejar de
// confiar" (vuelve a pedir el código) o desactivar la verificación entera
// (no la vuelve a pedir nunca). El checkbox del login decide si ESE login en
// particular deja el dispositivo confiado o no. Y un dispositivo distinto
// —otro navegador, mismo usuario— nunca hereda la confianza de otro. Ver
// web/index.html: NUBE.enrolarTOTP/verificarFactor/desenrolarTOTP,
// continuarLogin(), confiarDispositivo()/dispositivoConfiable()/
// olvidarDispositivo(), y la pestaña "mfa" de renderCuenta().
//
// El simulador (ver simulador.mjs) no hace TOTP de verdad: acepta un único
// código fijo (CODIGO_OK, '123456') como "correcto" para poder probar los
// dos caminos sin implementar la aritmética real.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, activarMFA, dejarFactorPendiente, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8617;
const CODIGO_OK = '123456', CODIGO_MAL = '000000';

// Login con correo/contraseña ya cargados en la pantalla de ingreso.
async function loguear(page) {
  await page.fill('#nbMail', 'admin@visitar.test');
  await page.fill('#nbPass', 'Password123!');
  await page.click('#nbGo');
}

async function salirYRecargar(page) {
  await page.evaluate(() => window.NBUNube && window.NBUNube.salir());
  await page.reload();
  await esperarArranque(page);
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('mfa: activarla confía el dispositivo; dejar de confiar y desactivar la sacan', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    // No se destructura `errores`: los códigos incorrectos a propósito
    // (challenge/verify con 400) quedan en la consola como "Failed to load
    // resource" — mismo motivo por el que casos/login.mjs no lo pide en el
    // caso de la contraseña equivocada. Lo que sí tiene que seguir en cero es
    // la CSP.
    const { csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    // Login normal: sin factor activado todavía, entra derecho, sin candado.
    await loguear(page);
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'sin verificación en dos pasos activada, tendría que entrar directo');

    // Abrir "Tu cuenta" → "Verificación en dos pasos": todavía no está activa.
    await page.click('#acctChip');
    await page.waitForSelector('[data-cm="mfa"]', { timeout: 5000 });
    await page.click('[data-cm="mfa"]');
    await page.waitForSelector('#cMfaStart', { timeout: 5000 });

    // Arrancar el alta: tiene que aparecer el secreto manual y el QR
    // tiene que cargar de verdad (el simulador manda SVG crudo, como la API
    // real — ver qrComoImagen() en web/index.html: sin envolverlo en un
    // data URI, el <img> no tiene una URL válida y nunca dispara "load").
    await page.click('#cMfaStart');
    await page.waitForSelector('#cMfaCode', { timeout: 5000 });
    const secreto = await page.textContent('#adminBox .mono');
    afirmar(!!secreto && secreto.trim().length > 0, 'debería mostrar el código manual para cargar a mano');
    const qr = page.locator('#cMfaQr');
    afirmar(await qr.count() === 1, 'debería mostrar la imagen del código QR');
    afirmar(await qr.evaluate(img => img.complete && img.naturalWidth > 0),
      'el QR tendría que cargar de verdad, no quedar como imagen rota');

    // Código incorrecto: no confirma, se queda en la misma pantalla de alta.
    await page.fill('#cMfaCode', CODIGO_MAL);
    await page.click('#cMfaConfirm');
    await page.waitForTimeout(300);
    afirmar(await page.isVisible('#cMfaCode'), 'con el código incorrecto tendría que seguir pidiendo el código, no darlo por activado');

    // Código correcto: confirma, activa, y confía este dispositivo solo.
    await page.fill('#cMfaCode', CODIGO_OK);
    await page.click('#cMfaConfirm');
    await page.waitForSelector('#cMfaOff', { timeout: 5000 });
    afirmar(await page.isVisible('#cMfaOlvidar'), 'al activarla desde este dispositivo, tendría que quedar confiado solo');

    // Salir y volver a entrar: este dispositivo quedó confiado, así que entra
    // directo, sin el candado.
    await page.evaluate(() => { const b = document.getElementById('cClose'); if (b) b.click(); });
    await salirYRecargar(page);
    await loguear(page);
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'el dispositivo que activó la verificación tendría que quedar confiado y entrar directo');

    // "Dejar de confiar en este dispositivo": ahora sí, el próximo login la pide.
    await page.click('#acctChip');
    await page.waitForSelector('[data-cm="mfa"]', { timeout: 5000 });
    await page.click('[data-cm="mfa"]');
    await page.waitForSelector('#cMfaOlvidar', { timeout: 5000 });
    await page.click('#cMfaOlvidar');
    await page.waitForSelector('#cMfaOff', { timeout: 5000 });
    afirmar(await page.isHidden('#cMfaOlvidar'), 'después de dejar de confiar, el botón no tendría que seguir ofreciéndose');
    await page.evaluate(() => { const b = document.getElementById('cClose'); if (b) b.click(); });
    await salirYRecargar(page);
    await loguear(page);
    await page.waitForSelector('#mfaCode', { timeout: 5000 });
    afirmar(await page.isHidden('#acctChip'), 'sin confiar ya en este dispositivo, el login tendría que volver a pedir el código');

    // Código incorrecto en el login: rechaza y no entra.
    await page.fill('#mfaCode', CODIGO_MAL);
    await page.click('#mfaGo');
    await page.waitForSelector('#gErr:has-text("incorrecto")', { timeout: 5000 });
    afirmar(await page.isHidden('#acctChip'), 'con el código de login incorrecto no tendría que entrar');

    // Código correcto, pero con el checkbox de "confiar" destildado: entra,
    // pero el dispositivo NO debería quedar confiado esta vez.
    await page.uncheck('#mfaRecordar');
    await page.fill('#mfaCode', CODIGO_OK);
    await page.click('#mfaGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await salirYRecargar(page);
    await loguear(page);
    await page.waitForSelector('#mfaCode', { timeout: 5000 });
    afirmar(await page.isHidden('#acctChip'), 'con el checkbox destildado, el dispositivo no tendría que quedar confiado');

    // Código correcto, esta vez con el checkbox tildado (el default): entra
    // y el dispositivo queda confiado.
    await page.fill('#mfaCode', CODIGO_OK);
    await page.click('#mfaGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await salirYRecargar(page);
    await loguear(page);
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'con el checkbox tildado, el dispositivo tendría que quedar confiado y entrar directo la próxima vez');

    // Desactivarla del todo: confirma el diálogo nativo, y ya no la pide
    // nunca más, en ningún dispositivo.
    page.once('dialog', d => d.accept());
    await page.click('#acctChip');
    await page.waitForSelector('[data-cm="mfa"]', { timeout: 5000 });
    await page.click('[data-cm="mfa"]');
    await page.waitForSelector('#cMfaOff', { timeout: 5000 });
    await page.click('#cMfaOff');
    await page.waitForSelector('#cMfaStart', { timeout: 5000 });
    await page.evaluate(() => { const b = document.getElementById('cClose'); if (b) b.click(); });
    await salirYRecargar(page);
    await loguear(page);
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'desactivada la verificación en dos pasos, tendría que volver a entrar directo');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await correrCaso('mfa: un dispositivo distinto no hereda la confianza de otro', async () => {
    // Misma cuenta con el factor ya activado de antes (activarMFA seedea
    // directo, sin pasar por el alta): un dispositivo lo confía, el otro —
    // otro contexto de navegador, localStorage propio— tiene que seguir
    // pidiendo el código igual.
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    activarMFA(db, [...db.users.values()].find(u => u.email === 'admin@visitar.test').id);

    const ctxA = await nuevoContexto(browser);
    await instalarSimulador(ctxA, db);
    const pageA = await ctxA.newPage();
    await saltarOnboarding(pageA);
    await pageA.goto(base);
    await esperarArranque(pageA);
    await loguear(pageA);
    await pageA.waitForSelector('#mfaCode', { timeout: 5000 });
    await pageA.fill('#mfaCode', CODIGO_OK); // checkbox de confiar queda tildado (default)
    await pageA.click('#mfaGo');
    await pageA.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await ctxA.close();

    const ctxB = await nuevoContexto(browser);
    await instalarSimulador(ctxB, db);
    const pageB = await ctxB.newPage();
    await saltarOnboarding(pageB);
    const { csp } = vigilarErrores(pageB);
    await pageB.goto(base);
    await esperarArranque(pageB);
    await loguear(pageB);
    await pageB.waitForSelector('#mfaCode', { timeout: 5000 });
    afirmar(await pageB.isHidden('#acctChip'), 'un dispositivo distinto no tendría que heredar la confianza de otro');
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctxB.close();
  });

  await correrCaso('mfa: un alta anterior sin terminar no bloquea el siguiente intento', async () => {
    // Bug real de producción del 25/8/2026: el QR no se mostró, y al volver
    // a tocar "Activar" la nube contestaba "A factor with the friendly name
    // \"Administrador\" for this user already exists" — quedó un factor sin
    // verificar de la vez anterior y no había forma de reintentar sin entrar
    // al panel de Supabase a mano. dejarFactorPendiente() siembra ese mismo
    // factor huérfano; NUBE.enrolarTOTP() tiene que limpiarlo solo.
    const db = crearDB();
    const uid = altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    dejarFactorPendiente(db, uid);
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await loguear(page);
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });

    await page.click('#acctChip');
    await page.waitForSelector('[data-cm="mfa"]', { timeout: 5000 });
    await page.click('[data-cm="mfa"]');
    await page.waitForSelector('#cMfaStart', { timeout: 5000 });
    await page.click('#cMfaStart');
    // Antes del arreglo, acá aparecía el toast de error y la pantalla volvía
    // al botón "Activar"; ahora tiene que llegar directo al formulario del
    // código, con el secreto manual ya cargado.
    await page.waitForSelector('#cMfaCode', { timeout: 5000 });
    const secreto = await page.textContent('#adminBox .mono');
    afirmar(!!secreto && secreto.trim() !== '—', 'debería llegar al formulario del código con el secreto cargado, no quedarse en el botón de activar');

    await page.fill('#cMfaCode', CODIGO_OK);
    await page.click('#cMfaConfirm');
    await page.waitForSelector('#cMfaOff', { timeout: 5000 });

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await correrCaso('mfa: sólo se le pide al administrador general, no a otros roles', async () => {
    // El candado mira pf.rol==='admin' a propósito (ver continuarLogin() en
    // web/index.html): si algún día ese chequeo se afloja sin querer, este
    // caso lo agarra. Un médico administrador con un factor verificado —algo
    // que hoy la interfaz ni siquiera ofrece armar— tiene que poder entrar
    // igual, sin que el login le pida el código.
    const db = crearDB();
    const uid = altaUsuario(db, { nombre: 'Med Admin', email: 'medadmin@visitar.test', password: 'Password123!', rol: 'medico_admin', estado: 'activo' });
    activarMFA(db, uid);
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'medadmin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'un rol que no es administrador general no tendría que ver el candado aunque tenga un factor activado');
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
