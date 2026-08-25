// Caso "sesion_muerta": si la sesión muere del lado del servidor sin que la
// app haga nada raro (el access token se invalida y el refresh token también
// — vencimiento propio de Supabase, o quedó invalidado por un login desde
// otro lado), la app tiene que cerrar la sesión de una y avisar — no seguir
// reintentando cada llamado con la clave pública (anon) como si fuera el
// usuario. Antes de este arreglo, NUBE.api() ignoraba que la sesión estaba
// muerta y llamaba igual: como funciones como pendientes()/factores() tienen
// el permiso de ejecución sacado a propósito para anon, cada intento quedaba
// en los logs de Postgres como "permission denied", en silencio, cada vez que
// corriera el sondeo de fondo (refrescarCuentasNube(), cada 60s) — bug real
// de producción encontrado el 26/8/2026 mirando esos logs.
//
// Se simula revocando el access token Y el refresh token del lado del
// simulador (en vez de hacer avanzar el reloj hasta que venza `expira`, que
// necesitaría reinstalar la sesión desde localStorage para que el módulo la
// vuelva a leer): el primer llamado sale con 401, el reintento con el
// refresh también falla, y ese es exactamente el mismo cuadro que un refresh
// token que venció solo.
//
// Ver web/index.html: NUBE.vigente()/api(), cerrarSesionMuerta(), resetIdle().

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8621;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('sesion_muerta: un refresh token que murió solo cierra la sesión y avisa, en vez de reintentar como anónimo', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    // No se destructura `errores`: el refresh token muerto a propósito sale
    // como 400 real contra el simulador, y Chromium lo deja en la consola
    // como "Failed to load resource" — mismo motivo que en casos/mfa.mjs con
    // el código incorrecto. Lo que sí tiene que seguir en cero es la CSP.
    const { csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });

    // Revoca los dos tokens del lado del simulador — el próximo llamado sale
    // con 401, y el reintento con el refresh también falla.
    const sesion = await page.evaluate(() => JSON.parse(localStorage.getItem('nbu-sesion')));
    db.tokens.delete(sesion.access_token);
    db.refresh.delete(sesion.refresh_token);

    // Cualquier llamado que dependa de la sesión dispara vigente(): abrir
    // "Tu cuenta" → "Verificación en dos pasos" llama a NUBE.factores().
    await page.click('#acctChip');
    await page.waitForSelector('[data-cm="mfa"]', { timeout: 5000 });
    await page.click('[data-cm="mfa"]');

    // Tiene que volver sola a la pantalla de ingreso, con el aviso puesto.
    await page.waitForSelector('#gate:not([hidden])', { timeout: 5000 });
    await page.waitForSelector('text=Tu sesión venció', { timeout: 3000 });

    // La sesión vieja no puede haber quedado guardada: un F5 no debería
    // volver a entrar solo con ella.
    const sesionGuardada = await page.evaluate(() => localStorage.getItem('nbu-sesion'));
    afirmar(sesionGuardada === null, 'la sesión vencida no debería seguir guardada en localStorage');

    // Y el login de nuevo, con la cuenta de siempre, tiene que seguir andando
    // (que la sesión se haya cerrado de golpe no puede dejar nada roto).
    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
