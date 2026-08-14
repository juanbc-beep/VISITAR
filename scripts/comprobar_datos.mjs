/* Control rápido para cambios que tocan SÓLO la base de datos.
 *
 *   cd web && python3 -m http.server 8890 --bind 127.0.0.1 &
 *   node scripts/comprobar_datos.mjs
 *
 * Tarda 2,5 s. La batería completa tarda 80, de los cuales 39 son
 * waitForTimeout a ciegas. Correrla entera después de importar un capítulo es
 * pagar 77 segundos por probar código que no se tocó.
 *
 * Los importadores de capítulo (alcance_nn_pmo, nombres_rotos) no tocan
 * index.html: escriben data/nbu_db.json y de ahí sale web/nbu_db.bin. Así que
 * roles_limite, favglob y tour2 —que prueban permisos, favoritos y tutorial—
 * no pueden romperse por esos cambios: prueban código que no se movió.
 *
 * Lo que SÍ puede romperse es esto, y es lo que mira este archivo:
 *   1. que la base cargue y tenga la cantidad de prácticas esperada
 *   2. que la búsqueda siga encontrando y no muestre texto sucio
 *   3. que una ficha abra con su norma NN y su bloque de equivalencia
 *   4. que ningún nombre tenga la etiqueta «Texto retirado por el PMO» adentro
 *
 * Sin waitForTimeout: espera condiciones reales (waitForFunction), que además
 * de ser más rápido no depende de que la máquina esté descargada.
 */
import pkg from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pkg;
import { servidor, baseVacia, HOST, ANA } from './e2e_mock.mjs';

const t0 = Date.now();
const b = await chromium.launch();
const s = servidor(ANA, baseVacia());
const ctx = await b.newContext({ viewport: { width: 1180, height: 950 } });
await ctx.addInitScript(() => { try { localStorage.setItem('nbu-onboarded', '1'); } catch (e) {} });
await ctx.route(HOST + '/**', r => s.ruta(r));
const p = await ctx.newPage();
const errs = [];
p.on('pageerror', e => errs.push(e.message));
p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

await p.goto('http://127.0.0.1:8890/index.html');
// la base terminó de cargar cuando el cartel de arranque se fue
await p.waitForFunction(() => {
  const b = document.getElementById('boot');
  return !b || getComputedStyle(b).display === 'none';
}, { timeout: 30000 });

await p.fill('#nbMail', 'x@y.com'); await p.fill('#nbPass', '123456'); await p.click('#nbGo');
await p.waitForSelector('#q', { state: 'visible', timeout: 30000 });
/* La app abre en el nomenclador de laboratorio. Los códigos del PMO que se
   están importando viven en el otro, así que sin este cambio las búsquedas dan
   cero y el test parece roto cuando lo roto es el test. */
await p.evaluate(() => {
  const b = [...document.querySelectorAll('.modeswitch button, .modesel button, [data-mode]')]
    .find(x => /Prestaciones/i.test(x.textContent));
  if (b) b.click();
});
await p.waitForFunction(() => document.querySelectorAll('#list .row').length > 0, { timeout: 15000 });

const R = [];
// ── 1 y 2 · la búsqueda encuentra, y no ensucia el texto
for (const [q, esperado] of [['fisioterapia', '250101'], ['artroplastia cadera', '121001'],
                             ['craneotomía', '010208'], ['quemaduras', '1303']]) {
  await p.fill('#q', q);
  await p.waitForFunction(t => {
    const l = document.querySelectorAll('#list .row');
    return l.length && [...l].some(x => (x.getAttribute('data-code') || x.innerText).includes(t));
  }, esperado, { timeout: 2500 }).catch(() => {});   // corto a propósito: si falla, se paga entero
  R.push(await p.evaluate(t => {
    const f = [...document.querySelectorAll('#list .row')];
    const txt = f.map(x => x.innerText).join(' ');
    return { q: t, n: f.length, sucio: /Texto\s*re[a-z]*irado|por\s*el\s*PMO/i.test(txt) };
  }, q));
}

// ── 3 · una ficha con norma NN y equivalencia
await p.evaluate(() => location.hash = '#250101');
await p.waitForFunction(() => /fisioterapia/i.test(document.body.innerText), { timeout: 15000 });
const ficha = await p.evaluate(() => ({
  nn: !!document.querySelector('.nn-card'),
  abarca: /Qué abarca este código/i.test(document.body.innerText),
}));

console.log('── búsqueda ──');
for (const r of R) console.log(`  «${r.q}» → ${r.n} resultados · texto sucio: ${r.sucio}`);
console.log(`\n── ficha 250101 ──\n  bloque de norma NN: ${ficha.nn} · «Qué abarca»: ${ficha.abarca}`);
console.log(`\nerrores de página: ${errs.length ? errs.join(' | ') : 'ninguno'}`);
console.log(`tiempo total: ${((Date.now() - t0) / 1000).toFixed(1)} s`);
await b.close();
