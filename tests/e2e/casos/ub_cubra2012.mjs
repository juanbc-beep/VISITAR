// Caso "ub_cubra2012": a 205 códigos del NBU se les aplicó la U.B. del PDF «NBU CUBRA 2012»
// (data/nbu_ub_cubra2012.json). Lo que tiene que pasar en la ficha:
//   · la U.B. VIGENTE —lo que la app muestra y multiplica— no cambia;
//   · el valor aplicado se rotula «CUBRA 2012», no «base v2016» (sería falso);
//   · los códigos a los que no se les aplicó nada siguen diciendo «base v2016»;
//   · lo mismo del lado del Único (su ficha cita la U.B. del NBU equivalente);
//   · los 9 excluidos (el PDF describe otra práctica) no se tocan.
//
//   660005 ACIDO BASE (EAB): base tenía 15, PDF 10, vigente 20  -> «CUBRA 2012: 10»
//   660001 ACTO BIOQUÍMICO: no está en el PDF, ub 3, vigente 6    -> «base v2016: 3»
//   660417: excluido (el PDF es G6PD y la base glucosa en orina)   -> no se toca

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

    const aplicado = await valorizacion('660005');
    afirmar(aplicado.includes('vigente') && aplicado.includes('20'), `la U.B. vigente (20) tiene que seguir ahí, vino: ${aplicado}`);
    afirmar(aplicado.includes('CUBRA 2012: 10'), `el valor aplicado tiene que decir «CUBRA 2012: 10», vino: ${aplicado}`);
    afirmar(!aplicado.includes('base v2016: 10'), 'no puede rotular de 2016 un valor de CUBRA 2012');

    const sinTocar = await valorizacion('660001');
    afirmar(sinTocar.includes('base v2016: 3'), `un código fuera del PDF sigue diciendo «base v2016: 3», vino: ${sinTocar}`);
    afirmar(!sinTocar.includes('CUBRA 2012'), 'y no menciona CUBRA 2012');

    // Del lado del Único: su ficha cita la U.B. del NBU equivalente (U61660005 = 660005).
    const unico = await valorizacion('U61660005');
    afirmar(unico.includes('CUBRA 2012: 10'), `la ficha del Único tiene que citar «CUBRA 2012: 10», vino: ${unico}`);

    afirmar(csp.length === 0, 'sin violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'sin errores de JS: ' + errores.join(' | '));
    await ctx.close();
  });

  await correrCaso('ub cubra 2012: los datos aplicados coinciden con el archivo curado y los excluidos no se tocaron', async () => {
    const raiz = new URL('../../../', import.meta.url);
    const cur = JSON.parse(readFileSync(new URL('data/nbu_ub_cubra2012.json', raiz), 'utf8'));
    const db = JSON.parse(readFileSync(new URL('data/nbu_db.json', raiz), 'utf8')).codigos;
    const nbu = Object.fromEntries(Object.values(db).filter(v => v.nomenclador === 'NBU').map(v => [v.code, v]));
    const malos = Object.entries(cur.valores).filter(([c, ub]) => !nbu[c] || nbu[c].valor.ub !== ub || nbu[c].valor.ub_fuente !== cur.rotulo);
    afirmar(malos.length === 0, `${malos.length} código(s) no tienen la U.B. del archivo curado: ${malos.slice(0, 5).map(m => m[0])}`);
    afirmar(Object.keys(cur.valores).length === 205, `esperaba 205 códigos aplicados, hay ${Object.keys(cur.valores).length}`);
    for (const [c, e] of Object.entries(cur.excluidos)) {
      afirmar(nbu[c].valor.ub === e.ub_base && !nbu[c].valor.ub_fuente, `el ${c} está excluido y no se tiene que haber tocado`);
    }
    const vig = Object.keys(cur.valores).filter(c => nbu[c].valor.ub_vigente == null);
    afirmar(vig.length === 0, 'todos los aplicados conservan su U.B. vigente');
  });

  await browser.close();
  srv.close();
}

await main();
