// Caso "login": entrar con la cuenta correcta, rechazar la contraseña
// equivocada, y las dos pantallas de cuenta sin aprobar (pendiente/rechazada).
// Cubre lo que HANDOFF.md describe como "login (ingreso + violaciones CSP)".
//
// index.html trae baked-in la URL real de Supabase (window.NBU_NUBE, arriba
// del todo del archivo) — no hace falta pisarla: el simulador intercepta ese
// mismo host, así que la app cree que le está hablando a la nube de verdad.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8611;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();
  const db = crearDB();
  altaUsuario(db, { nombre: 'Ana Activa', email: 'ana@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
  altaUsuario(db, { nombre: 'Nuevo Pendiente', email: 'nuevo@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'pendiente' });
  altaUsuario(db, { nombre: 'Ex Rechazado', email: 'fuera@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'rechazado' });

  try {
    await correrCaso('login: contraseña equivocada no entra', async () => {
      const ctx = await nuevoContexto(browser);
      await instalarSimulador(ctx, db);
      const page = await ctx.newPage();
      await saltarOnboarding(page);
      const { csp } = vigilarErrores(page);
      await page.goto(base);
      await esperarArranque(page);
      await page.fill('#nbMail', 'ana@visitar.test');
      await page.fill('#nbPass', 'lo-que-no-es');
      await page.click('#nbGo');
      await page.waitForSelector('#gErr:has-text("Correo o contraseña incorrectos")', { timeout: 5000 });
      afirmar(await page.isHidden('#acctChip'), 'con contraseña equivocada #acctChip no debería quedar visible');
      afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
      await ctx.close();
    });

    await correrCaso('login: cuenta activa entra y ve su nombre', async () => {
      const ctx = await nuevoContexto(browser);
      await instalarSimulador(ctx, db);
      const page = await ctx.newPage();
      await saltarOnboarding(page);
      const { csp, errores } = vigilarErrores(page);
      await page.goto(base);
      await esperarArranque(page);
      await page.fill('#nbMail', 'ana@visitar.test');
      await page.fill('#nbPass', 'Password123!');
      await page.click('#nbGo');
      await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
      const nombre = await page.textContent('#acctNm');
      afirmar(nombre.trim() === 'Ana Activa', `esperaba el nombre "Ana Activa", vino "${nombre}"`);
      afirmar(await page.isHidden('#gate'), 'con sesión iniciada el portón (#gate) debería quedar oculto');
      afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
      afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
      await ctx.close();
    });

    await correrCaso('login: cuenta pendiente ve "cuenta creada", no entra', async () => {
      const ctx = await nuevoContexto(browser);
      await instalarSimulador(ctx, db);
      const page = await ctx.newPage();
      await saltarOnboarding(page);
      await page.goto(base);
      await esperarArranque(page);
      await page.fill('#nbMail', 'nuevo@visitar.test');
      await page.fill('#nbPass', 'Password123!');
      await page.click('#nbGo');
      await page.waitForSelector('h2:has-text("Cuenta creada")', { timeout: 5000 });
      afirmar(await page.isHidden('#acctChip'), 'una cuenta pendiente no debería entrar a la app');
      await ctx.close();
    });

    await correrCaso('login: cuenta rechazada ve "cuenta no habilitada", no entra', async () => {
      const ctx = await nuevoContexto(browser);
      await instalarSimulador(ctx, db);
      const page = await ctx.newPage();
      await saltarOnboarding(page);
      await page.goto(base);
      await esperarArranque(page);
      await page.fill('#nbMail', 'fuera@visitar.test');
      await page.fill('#nbPass', 'Password123!');
      await page.click('#nbGo');
      await page.waitForSelector('h2:has-text("Cuenta no habilitada")', { timeout: 5000 });
      afirmar(await page.isHidden('#acctChip'), 'una cuenta rechazada no debería entrar a la app');
      await ctx.close();
    });
  } finally {
    await browser.close();
    srv.close();
  }
}

await main();
