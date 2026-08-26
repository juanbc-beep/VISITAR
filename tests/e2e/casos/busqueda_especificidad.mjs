// Caso "busqueda_especificidad": a igual puntaje, buscar() tiene que
// desempatar por el nombre más corto (más específico), no por el orden en
// que el código entró a la base.
//
// "torax" solo empataba en puntaje "Radiología tórax" (340301, 2 palabras
// en el nombre) con "Operación plástica por tórax en carina o excavado"
// (050102, 8 palabras, un código de cirugía sin relación con una orden de
// rayos) — y como el desempate era el orden de `CODES`, ganaba 050102 por
// tener el número de código más bajo, no por ser más relevante. Encontrado
// armando el candidato de exposición adicional del Intérprete de orden
// (ver candidatosParaItem() en web/index.html). Ver HANDOFF.md, 26/8/2026.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8633;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('busqueda_especificidad: a igual puntaje, gana el nombre más corto (más específico), no el código más bajo', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Ana Activa', email: 'ana@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await page.fill('#nbMail', 'ana@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });

    await page.click('[data-mode="ALL"]');
    await page.waitForSelector('#q', { timeout: 5000 });
    await page.fill('#q', 'torax');
    await page.waitForSelector('.row', { timeout: 5000 });

    const primeraFila = page.locator('.row').first();
    afirmar(await primeraFila.getAttribute('data-code') === '340301',
      'buscar "torax" debería traer primero 340301 "Radiología tórax" (nombre corto, el término es casi todo el nombre), no 050102 "Operación plástica por tórax…" (nombre largo, el término es una palabra suelta), aunque los dos empaten en puntaje de coincidencia');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
