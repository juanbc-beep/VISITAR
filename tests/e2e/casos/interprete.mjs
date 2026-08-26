// Caso "interprete": Intérprete de orden médica — pegar el texto de una
// orden y que devuelva los códigos candidatos, renglón por renglón, con la
// opción de mandar los elegidos a la Mesa de trabajo. Ver web/index.html:
// partirOrden(), initInterprete(), correrInterprete(), renderIntResumen().
//
// 660475 (HEMOGRAMA) y 660412 (GLUCEMIA (C/U)) son códigos reales del NBU —
// los mismos que ya usa el placeholder de la Mesa de trabajo como ejemplo.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8619;

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('interprete: encuentra candidatos por renglón y los manda a la Mesa de trabajo', async () => {
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

    await page.click('.vtab[data-view="interprete"]');
    await page.waitForSelector('#intTexto', { timeout: 5000 });

    // Dos renglones reales, uno con sueltos de una letra (el propio ejemplo
    // del placeholder del cuadro de texto), uno con una sigla compuesta de dos
    // palabras (SINONIMOS_COMPUESTOS), uno con una sigla amplia (TAC: decenas
    // de variantes reales, tiene que activar «ver más») y uno inventado que no
    // debería encontrar nada.
    await page.fill('#intTexto', 'Hemograma\nGlucemia\nRx torax f y p\nanti ro\ntac\nxyzqwerty inventado sin sentido');
    await page.click('#intGo');
    await page.waitForSelector('.int-item', { timeout: 5000 });

    const items = await page.locator('.int-item').count();
    afirmar(items === 6, `esperaba 6 renglones interpretados, vinieron ${items}`);

    // Cada renglón se ubica por su propio texto de origen (.int-src), no por
    // cualquier texto del ítem entero: desde que el Intérprete muestra las
    // etiquetas y observaciones de cada candidato en la vista previa (ver
    // HANDOFF.md, 26/8/2026), alguna etiqueta puede traer por casualidad la
    // misma subcadena que el texto de otro renglón —p.ej. «Prestaciones
    // Médicas» contiene «tac»— y buscar con :has-text() sobre el ítem
    // entero dejaba de ser inequívoco.
    const renglon=texto=>page.locator('.int-item').filter({has:page.locator('.int-src',{hasText:texto})});

    // «tac» sola tiene muchas más de 5 variantes reales en la base (por
    // región, con/sin contraste, en los tres nomencladores): antes se
    // cortaba en 5 sin forma de ver el resto — ver candidatosParaItem() y
    // HANDOFF.md, 25/8/2026 (aviso del usuario sobre el Intérprete).
    const renglonTac = renglon('tac').first();
    afirmar(await renglonTac.locator('.int-cand:visible').count() === 5, 'con «tac» deberían verse 5 candidatos antes de tocar «ver más»');
    const masTac = renglonTac.locator('[data-int-toggle]');
    afirmar(await masTac.count() === 1, 'con más de 5 candidatos reales, «tac» debería mostrar el botón «ver más»');
    await masTac.click();
    afirmar(await renglonTac.locator('.int-cand:visible').count() > 5, 'tocar «ver más» debería revelar más de 5 candidatos');
    afirmar((await masTac.textContent()).trim() === 'Mostrar menos', 'tocado «ver más», el botón debería pasar a «Mostrar menos»');

    // «anti ro» es una sigla de dos palabras: 668905 (NBU "Ro, Ac. Anti-
    // (Ro/SSA)") tiene que aparecer —como candidato principal o como chip
    // "también en" de su equivalente del Único, según cuál puntúe más—, y
    // NO 666956/666958/666965 (Legionella Pneumophila, Ac. Anti), que sin
    // el borde de palabra (\b) en SINONIMOS_COMPUESTOS coincidían por
    // casualidad — ver puntuar() en web/index.html y HANDOFF.md, 25/8/2026
    // (segunda tanda).
    const renglonAntiRo = renglon('anti ro');
    afirmar(await renglonAntiRo.locator('[data-int-code="668905"]').count() >= 1,
      '«anti ro» debería traer 668905 (Ro, Ac. Anti) entre los candidatos');
    afirmar(await renglonAntiRo.locator('[data-int-code="666956"]').count() === 0,
      '«anti ro» NO debería traer Legionella (666956) por la coincidencia parcial de "...la, Ac. Anti"');

    // El primer renglón (Hemograma) tiene que traer 660475 entre los
    // candidatos — como principal o como chip "también en" de su
    // equivalente del Único, según cuál del grupo puntúe más.
    const cand660475 = page.locator('[data-int-code="660475"]');
    afirmar(await cand660475.count() >= 1, 'Hemograma debería traer 660475 entre los candidatos');

    // «Rx torax f y p»: buscar() exige que TODOS los términos coincidan, y
    // «f»/«y»/«p» sueltos (abreviatura de posición, no del nombre) tirarían
    // abajo el renglón entero si no se reintentara sin ellos — ver
    // candidatosParaItem() en web/index.html.
    const renglonTorax = renglon('Rx torax f y p');
    afirmar(await renglonTorax.locator('.int-grupo').count() >= 1,
      '«Rx torax f y p» debería encontrar candidatos reintentando sin los términos sueltos de 1-2 letras');

    // «F y P» pide dos exposiciones: si el candidato principal tiene su
    // propia exposición adicional (340302, ligado a 340301 por
    // exposicion_siguiente en la base), tiene que aparecer COLGADA del
    // mismo bloque —un solo <div class="int-grupo"> por práctica, no una
    // tarjeta aparte— como chip dentro de «.int-cand-comp», con su
    // nomenclador y todo (340302 del PMO y su equivalente del Único).
    // Ver candidatosParaItem() y HANDOFF.md, 26/8/2026 (aviso del usuario:
    // «rx torax f y p» → 340301 y 340302; y después, «demasiado espacio» /
    // «un solo bloque»).
    const notaComp = renglonTorax.locator('.int-cand-comp').first();
    afirmar(await notaComp.locator('[data-int-code="340302"]').count() === 1,
      '«Rx torax f y p» debería agregar 340302 (exposición de perfil, PMO) como chip dentro de la nota de exposición adicional');
    afirmar((await notaComp.textContent()).includes('340301'),
      'la nota de exposición adicional debería explicar de qué código base sale');

    // El tercer renglón (inventado) no debería traer ningún candidato.
    const sinCoincidencias = await renglon('xyzqwerty').locator('.int-sin').count();
    afirmar(sinCoincidencias === 1, 'un renglón sin coincidencias tendría que decirlo, no inventar un candidato');

    // Elegir 660475 (Hemograma) y buscar+elegir 660412 (Glucemia) entre sus candidatos.
    afirmar(await page.isHidden('#intResumen'), 'sin nada elegido todavía, el resumen no debería mostrarse');
    await cand660475.click();
    const cand660412 = page.locator('[data-int-code="660412"]');
    afirmar(await cand660412.count() >= 1, 'Glucemia debería traer 660412 entre los candidatos');
    await cand660412.click();

    await page.waitForSelector('#intResumen:not([hidden])', { timeout: 5000 });
    afirmar(await page.locator('#intResumen .int-chip').count() === 2, 'el resumen debería mostrar los 2 códigos elegidos');

    // Quitar uno desde el resumen: el candidato correspondiente pierde el estado "elegido".
    await page.click('#intResumen [data-int-quitar="660412"]');
    afirmar(await page.locator('#intResumen .int-chip').count() === 1, 'quitar del resumen debería dejar sólo 1 código elegido');
    afirmar(!(await cand660412.evaluate(b => b.classList.contains('on'))), 'al quitarlo del resumen, el candidato ya no debería quedar marcado como elegido');

    // Enviar a la Mesa de trabajo: cambia de vista y el código elegido llega al validador.
    await page.click('#intEnviar');
    await page.waitForSelector('.validator:not([hidden])', { timeout: 5000 });
    const vcodes = await page.inputValue('#vcodes');
    afirmar(vcodes.includes('660475'), `esperaba 660475 en la Mesa de trabajo, vino "${vcodes}"`);
    afirmar(!vcodes.includes('660412'), 'no debería llegar el código que se sacó del resumen');
    await page.waitForSelector('#vresults .vtable, #vresults .finding', { timeout: 5000 });

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
