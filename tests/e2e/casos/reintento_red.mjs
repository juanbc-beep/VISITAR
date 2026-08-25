// Caso "reintento_red": un corte de señal momentáneo (wifi de la oficina,
// un rato sin datos) no tiene que perder lo que se estaba guardando ni
// mostrar un error — se reintenta solo, con espera creciente
// (ESPERAS_RED = [2s, 5s, 10s]), antes de darse por vencido.
//
// Se simula abortando la PRIMERA llamada a "/rest/v1/correcciones" con
// route.abort('failed') (mismo TypeError "Failed to fetch" que un corte de
// red real) y dejando pasar el resto al simulador de siempre — no hace
// falta un simulador de red aparte, sólo fallar una vez antes de andar.
//
// Ver web/index.html: hacerConReintento(), y su uso en NUBE.api()/token().
// HANDOFF.md, 26/8/2026.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8631;
// ACTO BIOQUÍMICO — código NBU real y estable (data/nbu_db.json).
const CODIGO = '660001';
const NOMBRE_NUEVO = 'Acto Bioquímico (corregido con la red cortada)';

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

  await correrCaso('reintento_red: un corte de señal momentáneo al guardar se resuelve solo, sin perder el cambio', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);

    // Se registra DESPUÉS del simulador: en Playwright el handler agregado
    // más tarde corre primero, y route.fallback() le pasa el pedido al que
    // ya estaba (el simulador) — así sólo se corta la primera vez, el resto
    // sigue andando como siempre.
    let intentos = 0;
    await ctx.route('**/rest/v1/correcciones', async (route) => {
      if (route.request().method() === 'POST') {
        intentos++;
        if (intentos === 1) return route.abort('failed');
      }
      return route.fallback();
    });

    const page = await ctx.newPage();
    await saltarOnboarding(page);
    // No se destructura `errores`: el corte de red se simula abortando el
    // pedido de verdad (route.abort('failed')), y Chromium lo deja en la
    // consola como "Failed to load resource" — mismo motivo que en
    // casos/mfa.mjs y casos/sesion_muerta.mjs. Lo que sí tiene que seguir en
    // cero es la CSP.
    const { csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#editModeBtn');

    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await sinOverlays(page);
    await page.waitForSelector('#editFichaBtn', { timeout: 5000 });
    await page.click('#editFichaBtn');
    await page.waitForSelector('#efNom', { timeout: 5000 });
    await page.fill('#efNom', NOMBRE_NUEVO);
    await page.click('#efSave');

    // El corte se ve enseguida: la app avisa que está reintentando, sin
    // tirar un error genérico ni pedir que se repita la acción a mano.
    await page.waitForSelector('text=Sin conexión — reintentando', { timeout: 5000 });

    // El nombre nuevo ya se ve en la ficha (el estado local se actualiza de
    // una, sin esperar a la nube — ver efSave() en web/index.html).
    await page.waitForSelector(`.dname:has-text("${NOMBRE_NUEVO}")`, { timeout: 5000 });

    // Y a los ~2s (ESPERAS_RED[0]) reintenta solo y esta vez sí llega al
    // simulador — se comprueba del lado de la "nube" (el `db` de Node), no
    // del DOM, porque eso ya cambió antes de que la nube confirmara nada.
    await page.waitForTimeout(4000); // cubre ESPERAS_RED[0] (2s) con margen
    afirmar(intentos >= 2, `esperaba al menos 2 intentos contra "correcciones" (1 cortado + el reintento), hubo ${intentos}`);
    const guardado = db.correcciones.get(CODIGO);
    afirmar(!!guardado && guardado.nombre === NOMBRE_NUEVO,
      'el reintento tendría que haber guardado el nombre nuevo en la nube, no perderlo por el corte inicial');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
