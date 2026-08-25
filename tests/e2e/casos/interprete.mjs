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
    // del placeholder del cuadro de texto) y uno inventado que no debería
    // encontrar nada.
    await page.fill('#intTexto', 'Hemograma\nGlucemia\nRx torax f y p\nxyzqwerty inventado sin sentido');
    await page.click('#intGo');
    await page.waitForSelector('.int-item', { timeout: 5000 });

    const items = await page.locator('.int-item').count();
    afirmar(items === 4, `esperaba 4 renglones interpretados, vinieron ${items}`);

    // El primer renglón (Hemograma) tiene que traer 660475 entre los candidatos.
    const cand660475 = page.locator('.int-cand[data-int-code="660475"]');
    afirmar(await cand660475.count() >= 1, 'Hemograma debería traer 660475 entre los candidatos');

    // «Rx torax f y p»: buscar() exige que TODOS los términos coincidan, y
    // «f»/«y»/«p» sueltos (abreviatura de posición, no del nombre) tirarían
    // abajo el renglón entero si no se reintentara sin ellos — ver
    // candidatosParaItem() en web/index.html.
    afirmar(await page.locator('.int-item:has-text("Rx torax f y p") .int-cand').count() >= 1,
      '«Rx torax f y p» debería encontrar candidatos reintentando sin los términos sueltos de 1-2 letras');

    // El tercer renglón (inventado) no debería traer ningún candidato.
    const sinCoincidencias = await page.locator('.int-item:has-text("xyzqwerty") .int-sin').count();
    afirmar(sinCoincidencias === 1, 'un renglón sin coincidencias tendría que decirlo, no inventar un candidato');

    // Elegir 660475 (Hemograma) y buscar+elegir 660412 (Glucemia) entre sus candidatos.
    afirmar(await page.isHidden('#intResumen'), 'sin nada elegido todavía, el resumen no debería mostrarse');
    await cand660475.click();
    const cand660412 = page.locator('.int-cand[data-int-code="660412"]');
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
