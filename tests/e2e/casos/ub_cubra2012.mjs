// Caso "ub_cubra2012": a 100 códigos del NBU que no tenían U.B. del nomenclador se les cargó
// la del PDF «NBU CUBRA 2012» (data/nbu_ub_cubra2012.json). Donde la base YA tenía una U.B.
// no se cambió nada: la de la base (v2012 con actualización 2016) es más nueva que la del PDF
// (decisión del usuario). Lo que tiene que pasar en la ficha:
//   · la U.B. VIGENTE —lo que la app muestra y multiplica— no cambia;
//   · el valor cargado se rotula «CUBRA 2012», no «base v2016» (sería falso);
//   · los códigos que ya tenían U.B. siguen diciendo «base v2016» con su valor de siempre;
//   · lo mismo del lado del Único (su ficha cita la U.B. del NBU equivalente).
//
//   660044 (ub vacía, PDF 6, vigente 5)  -> «CUBRA 2012: 6»
//   660005 (ub 15, PDF 10, vigente 20)   -> sigue «base v2016: 15» (el PDF NO se aplicó)

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';
import { readFileSync } from 'node:fs';

const PUERTO = 8642;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('ub cubra 2012: la ficha rotula el valor aplicado y no toca la vigente', async () => {
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
    await page.evaluate(() => { const p = document.getElementById('pista'); if (p) p.classList.remove('on'); });

    const valorizacion = async (hash) => {
      await page.evaluate((h) => { location.hash = h; }, hash);
      await page.waitForFunction((h) => document.getElementById('drawer').classList.contains('on') &&
        document.getElementById('drawer').textContent.includes('Valorización'), hash, { timeout: 5000 });
      const t = await page.locator('#drawer .valcard').first().textContent();
      await page.evaluate(() => document.getElementById('closeDrawer').click());
      return t.replace(/\s+/g, ' ');
    };

    const cargado = await valorizacion('660044');
    afirmar(cargado.includes('vigente') && cargado.includes('5'), `la U.B. vigente (5) tiene que seguir ahí, vino: ${cargado}`);
    afirmar(cargado.includes('CUBRA 2012: 6'), `el valor cargado tiene que decir «CUBRA 2012: 6», vino: ${cargado}`);
    afirmar(!cargado.includes('base v2016'), 'no puede rotular de 2016 un valor de CUBRA 2012');

    // Ya tenía U.B.: el PDF dice 10 y la base 15, y la base es más nueva -> no se toca.
    const intacto = await valorizacion('660005');
    afirmar(intacto.includes('base v2016: 15'), `el 660005 conserva la U.B. de la base («base v2016: 15»), vino: ${intacto}`);
    afirmar(!intacto.includes('CUBRA 2012') && !intacto.includes(': 10'), 'y no menciona el valor del PDF');

    // Un código que no está en el PDF tampoco cambia.
    const fuera = await valorizacion('660001');
    afirmar(fuera.includes('base v2016: 3'), `un código fuera del PDF sigue diciendo «base v2016: 3», vino: ${fuera}`);

    // Del lado del Único: su ficha cita la U.B. del NBU equivalente (U64660044 = 660044).
    const unico = await valorizacion('U64660044');
    afirmar(unico.includes('CUBRA 2012: 6'), `la ficha del Único tiene que citar «CUBRA 2012: 6», vino: ${unico}`);

    afirmar(csp.length === 0, 'sin violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'sin errores de JS: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('ub cubra 2012: se completó lo que faltaba y no se cambió ninguna U.B. que ya estaba', async () => {
    const raiz = new URL('../../../', import.meta.url);
    const cur = JSON.parse(readFileSync(new URL('data/nbu_ub_cubra2012.json', raiz), 'utf8'));
    const db = JSON.parse(readFileSync(new URL('data/nbu_db.json', raiz), 'utf8')).codigos;
    const nbu = Object.fromEntries(Object.values(db).filter(v => v.nomenclador === 'NBU').map(v => [v.code, v]));
    const malos = Object.entries(cur.valores).filter(([c, ub]) => !nbu[c] || nbu[c].valor.ub !== ub || nbu[c].valor.ub_fuente !== cur.rotulo);
    afirmar(malos.length === 0, `${malos.length} código(s) no tienen la U.B. del archivo curado: ${malos.slice(0, 5).map(m => m[0])}`);
    afirmar(Object.keys(cur.valores).length === 100, `esperaba 100 códigos completados, hay ${Object.keys(cur.valores).length}`);
    const sinFuente = Object.values(nbu).filter(v => v.valor.ub_fuente && !(v.code in cur.valores));
    afirmar(sinFuente.length === 0, 'sólo los 100 completados llevan «ub_fuente»');
    // Los 114 que difieren siguen con la U.B. de la base.
    afirmar(Object.keys(cur.no_aplicadas).length === 114, `esperaba 114 sin aplicar, hay ${Object.keys(cur.no_aplicadas).length}`);
    for (const [c, e] of Object.entries(cur.no_aplicadas)) {
      afirmar(nbu[c].valor.ub === e.ub_base && !nbu[c].valor.ub_fuente, `el ${c} no se tenía que haber tocado (base ${e.ub_base})`);
    }
    afirmar(Object.keys(cur.valores).every(c => nbu[c].valor.ub_vigente != null), 'todos los completados conservan su U.B. vigente');
  });

  await browser.close();
  srv.close();
}

await main();
