// Caso "mfa": verificación en dos pasos (TOTP) para el administrador general.
//
// Cubre el circuito completo: alta propia desde "Tu cuenta" (QR + código
// manual + confirmación, rechazando un código incorrecto antes de aceptar el
// bueno), que a partir de ahí el login pide el código (rechazando uno
// incorrecto antes de dejar pasar), y que desactivarla vuelve a dejar entrar
// sólo con contraseña. Ver web/index.html: NUBE.enrolarTOTP/verificarFactor/
// desenrolarTOTP, continuarLogin() y la pestaña "mfa" de renderCuenta().
//
// El simulador (ver simulador.mjs) no hace TOTP de verdad: acepta un único
// código fijo (MFA_CODE_OK, '123456') como "correcto" para poder probar los
// dos caminos sin implementar la aritmética real.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, activarMFA, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8617;
const CODIGO_OK = '123456', CODIGO_MAL = '000000';

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('mfa: alta propia, login pide el código, y desactivarla lo saca', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    // No se destructura `errores`: los dos códigos incorrectos a propósito
    // (challenge/verify con 400) quedan en la consola como "Failed to load
    // resource" — mismo motivo por el que casos/login.mjs no lo pide en el
    // caso de la contraseña equivocada. Lo que sí tiene que seguir en cero es
    // la CSP.
    const { csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    // Login normal: sin factor activado todavía, entra derecho, sin candado.
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'sin verificación en dos pasos activada, tendría que entrar directo');

    // Abrir "Tu cuenta" → "Verificación en dos pasos": todavía no está activa.
    await page.click('#acctChip');
    await page.waitForSelector('[data-cm="mfa"]', { timeout: 5000 });
    await page.click('[data-cm="mfa"]');
    await page.waitForSelector('#cMfaStart', { timeout: 5000 });

    // Arrancar el alta: tiene que aparecer el secreto manual (QR aparte, no
    // se puede leer un QR en la prueba, pero el secreto manual es la vía
    // garantizada — ver el comentario en web/index.html sobre esto).
    await page.click('#cMfaStart');
    await page.waitForSelector('#cMfaCode', { timeout: 5000 });
    const secreto = await page.textContent('#adminBox .mono');
    afirmar(!!secreto && secreto.trim().length > 0, 'debería mostrar el código manual para cargar a mano');

    // Código incorrecto: no confirma, se queda en la misma pantalla de alta.
    await page.fill('#cMfaCode', CODIGO_MAL);
    await page.click('#cMfaConfirm');
    await page.waitForTimeout(300);
    afirmar(await page.isVisible('#cMfaCode'), 'con el código incorrecto tendría que seguir pidiendo el código, no darlo por activado');

    // Código correcto: confirma y pasa a mostrar "activada".
    await page.fill('#cMfaCode', CODIGO_OK);
    await page.click('#cMfaConfirm');
    await page.waitForSelector('#cMfaOff', { timeout: 5000 });

    // Cerrar sesión y volver a entrar: ahora tiene que aparecer el candado.
    await page.click('#cVolver'); // vuelve al menú "Tu cuenta"... si no existe, no rompe: sigue el flujo
    await page.evaluate(() => { const b = document.getElementById('cClose'); if (b) b.click(); });
    await page.evaluate(() => window.NBUNube && window.NBUNube.salir());
    await page.reload();
    await esperarArranque(page);
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#mfaCode', { timeout: 5000 });
    afirmar(await page.isHidden('#acctChip'), 'con la verificación en dos pasos activada, no tendría que entrar sin el código');

    // Código incorrecto en el login: rechaza y no entra.
    await page.fill('#mfaCode', CODIGO_MAL);
    await page.click('#mfaGo');
    await page.waitForSelector('#gErr:has-text("incorrecto")', { timeout: 5000 });
    afirmar(await page.isHidden('#acctChip'), 'con el código de login incorrecto no tendría que entrar');

    // Código correcto en el login: ahora sí entra.
    await page.fill('#mfaCode', CODIGO_OK);
    await page.click('#mfaGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'con el código correcto tendría que entrar');

    // Desactivarla: confirma el diálogo nativo, y una entrada siguiente ya no la pide.
    page.once('dialog', d => d.accept());
    await page.click('#acctChip');
    await page.waitForSelector('[data-cm="mfa"]', { timeout: 5000 });
    await page.click('[data-cm="mfa"]');
    await page.waitForSelector('#cMfaOff', { timeout: 5000 });
    await page.click('#cMfaOff');
    await page.waitForSelector('#cMfaStart', { timeout: 5000 });
    await page.evaluate(() => { const b = document.getElementById('cClose'); if (b) b.click(); });
    await page.evaluate(() => window.NBUNube && window.NBUNube.salir());
    await page.reload();
    await esperarArranque(page);
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    afirmar(await page.isHidden('#gate'), 'desactivada la verificación en dos pasos, tendría que volver a entrar directo');

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
