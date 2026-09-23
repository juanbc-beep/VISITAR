// Caso "accesibilidad": axe-core (el motor de reglas de accesibilidad más usado,
// el mismo de Lighthouse) contra las pantallas principales, en tema claro y
// oscuro, con las reglas de WCAG 2.0, 2.1 y 2.2 nivel A y AA. Cualquier
// violación hace fallar el caso: contraste, campos sin etiqueta, controles
// dentro de controles, objetivos táctiles chicos, roles ARIA mal armados…
//
// axe no reemplaza probar con teclado y lector de pantalla, pero atrapa la
// mayoría de las regresiones antes de que lleguen a alguien.
//
// La app bloquea por CSP cualquier script que no sea suyo (bien hecho), así
// que acá el contexto se abre con bypassCSP sólo para poder inyectar axe. Por
// eso este caso NO vigila violaciones de CSP: eso lo hacen todos los demás.

import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, afirmar, correrCaso } from '../arranque.mjs';

const PUERTO = 8645;
const AXE = readFileSync(new URL('../node_modules/axe-core/axe.min.js', import.meta.url), 'utf8');
const REGLAS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];
const GRILLA = [
  'Código,Práctica,Valor',
  '180104 al 180121,Ecografia General Nomenclada,12487.57',
  '999999,Práctica con código inventado,5000',
  ',ECG riesgo quirurgico,18378',
].join('\r\n');

async function auditar(page, donde, dentro) {
  // Medir a mitad de una animación de entrada (la tarjeta del acceso, el fundido
  // de un modal) da colores mezclados que no son los que se ven: se espera a
  // que terminen las finitas. Las infinitas (un pulso de aviso) no se esperan.
  await page.waitForFunction(() => document.getAnimations().every(a =>
    a.playState !== 'running' || a.effect.getComputedTiming().endTime === Infinity), null, { timeout: 5000 }).catch(() => {});
  await page.addScriptTag({ content: AXE });
  const v = await page.evaluate(async ([sel, reglas]) => {
    const r = await axe.run(sel ? { include: [sel] } : document, { runOnly: { type: 'tag', values: reglas } });
    return r.violations.map(x => `${x.id} [${x.impact}] ${x.help} — ${x.nodes.slice(0, 3).map(n => n.target.join(" ") + (n.any[0] && n.any[0].data && n.any[0].data.fgColor ? ` (${n.any[0].data.fgColor} sobre ${n.any[0].data.bgColor} = ${n.any[0].data.contrastRatio}:1)` : "")).join(", ")}`);
  }, [dentro || null, REGLAS]);
  return v.map(x => `${donde}: ${x}`);
}

async function recorrer(browser, base, tema) {
  const db = crearDB();
  altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
  altaUsuario(db, { nombre: 'Sin Aceptar', email: 'nueva@visitar.test', password: 'Password123!', legales: null });
  const ctx = await browser.newContext({ serviceWorkers: 'block', bypassCSP: true, colorScheme: tema });
  await instalarSimulador(ctx, db);
  const page = await ctx.newPage();
  await saltarOnboarding(page);
  const fallas = [];
  const login = async (email) => {
    await page.fill('#nbMail', email); await page.fill('#nbPass', 'Password123!'); await page.click('#nbGo');
  };

  for (const p of ['privacy-policy.html', 'terms-conditions.html', 'cookie-policy.html']) {
    await page.goto(base + p);
    fallas.push(...await auditar(page, p));
  }

  await page.goto(base);
  await esperarArranque(page);
  fallas.push(...await auditar(page, 'acceso'));
  await page.click('#nbNew');
  fallas.push(...await auditar(page, 'crear cuenta'));
  await page.click('#naBack');

  await login('nueva@visitar.test');
  await page.waitForSelector('#lgGo');
  fallas.push(...await auditar(page, 'aceptar términos'));
  await page.click('#lgSalir');
  await page.waitForSelector('#nbMail');

  await login('admin@visitar.test');
  await page.waitForSelector('#acctChip:not([hidden])');
  await page.evaluate(() => { const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on'); });
  for (const modo of ['NBU', 'PMO', 'UNICO']) {
    await page.click(`.modebtn[data-mode="${modo}"]`);
    await page.waitForTimeout(250);
    fallas.push(...await auditar(page, `listado ${modo}`));
    await page.click('.row >> nth=0');
    await page.waitForSelector('#drawer.on');
    fallas.push(...await auditar(page, `ficha ${modo}`, '#drawer'));
    await page.keyboard.press('Escape');
    await page.waitForTimeout(250);
  }
  for (const vista of ['tree', 'validator', 'interprete']) {
    await page.click(`.vtab[data-view="${vista}"]`);
    await page.waitForTimeout(250);
    fallas.push(...await auditar(page, `vista ${vista}`));
  }

  await page.click('#contrBtn');
  await page.setInputFiles('#contrFile', { name: 'grilla.csv', mimeType: 'text/csv', buffer: Buffer.from(GRILLA, 'utf-8') });
  await page.waitForSelector('.contr-tbl');
  fallas.push(...await auditar(page, 'contrataciones', '#contrModal'));
  await page.click('[data-buscar$="|999999"]');
  await page.waitForSelector('#contrBuscaRes');
  fallas.push(...await auditar(page, 'contrataciones: buscador', '#contrModal'));
  await page.click('#contrClose');

  await page.click('#adminBtn');
  await page.waitForSelector('#adminModal .atab');
  const pestañas = await page.locator('#adminModal .atab').count();
  for (let i = 0; i < pestañas; i++) {
    const t = page.locator('#adminModal .atab').nth(i);
    const nombre = (await t.innerText()).trim();
    await t.click();
    await page.waitForTimeout(250);
    fallas.push(...await auditar(page, `administración: ${nombre}`, '#adminModal'));
  }
  await ctx.close();
  return fallas;
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  for (const tema of ['light', 'dark']) {
    await correrCaso(`accesibilidad: sin violaciones de WCAG 2.2 AA en tema ${tema === 'light' ? 'claro' : 'oscuro'}`, async () => {
      const fallas = await recorrer(browser, base, tema);
      afirmar(fallas.length === 0, `${fallas.length} violación(es):\n  ` + fallas.join('\n  '));
    });
  }

  await browser.close();
  srv.close();
}

await main();
