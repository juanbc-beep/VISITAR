// Caso "config_busqueda": el administrador general puede ajustar los
// valores de coincidencia de la búsqueda —tolerancia a erratas de tipeo,
// umbral de "coincidencia fuerte" y el peso de cada tipo de coincidencia—
// desde Administración → Búsqueda, sin tocar código. Pedido explícito del
// usuario (26/8/2026): "que el administrador pueda modificar los valores de
// coincidencia de la mesa de trabajo".
//
// Afecta el motor de búsqueda de TODA la app (buscar()/puntuar()/
// tolerancia(), ver web/index.html), así que se prueba contra el efecto
// real: bajar la tolerancia de erratas en palabras largas a 0 hace que un
// término mal escrito deje de encontrar el código que antes encontraba por
// tolerancia a erratas.
//
// 660001 (ACTO BIOQUÍMICO) y 660102 (BACILOSCOPIA) son códigos NBU reales;
// "hemograma" (660475, HEMOGRAMA) tiene 9 letras — entra en el tramo
// "largos" (8+) de tolerancia() — y "hemogrma" (con una letra de menos, a
// un cambio de distancia) sólo encuentra ese código por tolerancia a
// erratas, no por coincidencia literal.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8636;

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

  await correrCaso('config_busqueda: el administrador general ajusta la tolerancia a erratas, y el efecto se nota en la búsqueda real y persiste', async () => {
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

    await page.click('[data-mode="ALL"]');
    await page.waitForSelector('#q', { timeout: 5000 });
    await page.fill('#q', 'hemogrma');
    await page.waitForTimeout(300);
    afirmar(await page.locator('.row').count() > 0,
      'con la tolerancia de fábrica, "hemogrma" (una letra de menos) debería encontrar algo por tolerancia a erratas');

    await page.click('#adminBtn');
    await page.waitForSelector('.atab', { timeout: 5000 });
    afirmar(await page.locator('.atab[data-t="busqueda"]').count() === 1,
      'el administrador general debería ver la pestaña "Búsqueda"');
    await sinOverlays(page);
    await page.click('.atab[data-t="busqueda"]');
    await page.waitForSelector('#bqTolLarga', { timeout: 5000 });

    // Cargar los pesos a propósito fuera de orden: tienen que reordenarse
    // solos al guardar (inicio ≥ borde ≥ contiene ≥ solo), no guardar una
    // búsqueda rota porque alguien los tipeó al revés.
    await page.fill('#bqTolLarga', '0');
    await page.fill('#bqPesoInicio', '3');
    await page.fill('#bqPesoBorde', '3');
    await page.fill('#bqPesoContiene', '9');
    await page.fill('#bqPesoSolo', '1');
    await page.click('#bqSave');
    await page.waitForTimeout(300);

    await page.click('#aClose');
    await sinOverlays(page);
    await page.fill('#q', '');
    await page.fill('#q', 'hemogrma');
    await page.waitForTimeout(300);
    afirmar(await page.locator('.row').count() === 0,
      'con la tolerancia de palabras largas en 0, "hemogrma" no debería encontrar nada por erratas');

    // Persiste tras recargar (nube) y los pesos quedaron reordenados.
    await page.reload();
    await esperarArranque(page);
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 8000 });
    await sinOverlays(page);
    await page.click('#adminBtn');
    await page.waitForSelector('.atab', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('.atab[data-t="busqueda"]');
    await page.waitForSelector('#bqTolLarga', { timeout: 5000 });
    afirmar(await page.inputValue('#bqTolLarga') === '0', 'la tolerancia guardada debería persistir tras recargar');
    afirmar(await page.inputValue('#bqPesoInicio') === '9', 'los pesos deberían haber quedado reordenados de mayor a menor (inicio=9)');
    afirmar(await page.inputValue('#bqPesoSolo') === '1', 'los pesos deberían haber quedado reordenados de mayor a menor (solo=1)');

    // Restaurar valores de fábrica.
    page.once('dialog', d => d.accept());
    await page.click('#bqReset');
    await page.waitForTimeout(200);
    afirmar(await page.inputValue('#bqTolLarga') === '2', 'restaurar debería volver la tolerancia larga a 2 (valor de fábrica)');
    await page.click('#aClose');
    await sinOverlays(page);
    await page.fill('#q', '');
    await page.fill('#q', 'hemogrma');
    await page.waitForTimeout(300);
    afirmar(await page.locator('.row').count() > 0, 'restaurados los valores de fábrica, "hemogrma" debería volver a encontrar algo');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('config_busqueda: un médico administrador no ve la pestaña "Búsqueda"', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Med Admin', email: 'medadmin@visitar.test', password: 'Password123!', rol: 'medico_admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'medadmin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#adminBtn');
    await page.waitForSelector('.atab', { timeout: 5000 });
    afirmar(await page.locator('.atab[data-t="busqueda"]').count() === 0,
      'un médico administrador no debería ver la pestaña "Búsqueda" (sólo la ve el administrador general)');
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
