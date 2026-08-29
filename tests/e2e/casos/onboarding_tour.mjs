// Caso "onboarding_tour": el recorrido guiado (▶ Ver tutorial / NBUProfile.tour())
// tenía un bug real reportado por el usuario en mobile: al tocar «← Atrás» en
// algunos pasos, en vez de retroceder se sentía como si el paso "se bugeara" o
// como si "se cerrara el menú hamburguesa".
//
// Causa: cada paso puede traer un `antes()` que prepara la pantalla (abrir el
// cajón de filtros, abrir una ficha, cerrarla) y, si el elemento a señalar
// sigue sin encontrarse después de eso, pintarPaso() saltea el paso — pero
// SIEMPRE sumaba (tIdx++), sin importar si se estaba yendo para adelante o
// para atrás. Yendo para atrás, ese salto en la dirección equivocada volvía
// a caer en el paso SIGUIENTE, cuyo `antes()` podía deshacer lo que el paso
// de atrás acababa de preparar (cerrar el cajón que se acababa de abrir, por
// ejemplo) — de ahí la sensación de que "Atrás" no funciona.
//
// Este caso reproduce el camino exacto que reportó el usuario en el recorrido
// completo (rol admin, mobile: 390×844): parado en el paso "Vistas" (el que
// sigue a "Filtros, en tres bloques"), tocar «← Atrás» tiene que volver
// mostrando el cajón de filtros ABIERTO con contenido adentro — no rebotar
// de nuevo hacia "Vistas".
//
// También cubre el otro síntoma reportado, más adelante en el mismo
// recorrido: parado en "La respuesta corta" (que abre una ficha), volver
// atrás a "Cada resultado, y qué significa el color" tiene que cerrar esa
// ficha y mostrar el listado, no reabrir la ficha de nuevo.
//
// Y un tercer bug relacionado, encontrado al investigar el reporte: en
// "Buscar en todo" (modo ALL) NINGÚN filtro aplica —ni sección, ni tipo de
// Único, ni grupo, ni "reglas y estados"— así que el cajón de filtros queda
// completamente vacío. En mobile el botón de filtros seguía visible igual,
// invitando a abrir un cajón en blanco sin ninguna explicación.
//
// Regla nueva del usuario (28/8/2026): el recorrido SIEMPRE arranca en
// Laboratorio (NBU), sin importar en qué modo se haya quedado la persona la
// última vez — startOnboard() fuerza el modo antes de pintar el primer
// paso. Esto elimina de raíz el disparador más realista del bug de arriba
// (arrancar el recorrido en modo ALL): ya no se puede llegar a ese estado
// por la vía pública (NBUProfile.tour()/maybeOnboard()), así que el caso
// que lo reproducía forzando el modo antes de llamar a tour() quedó retirado
// —su premisa ya no ocurre—. El arreglo de dirección (tDir) en pintarPaso()
// se mantiene de todos modos: sigue siendo la corrección correcta para
// cualquier otro paso que en el futuro quede inalcanzable por otro motivo
// (un rol, un elemento oculto), no sólo para el modo ALL.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8651;
const MOBILE = { width: 390, height: 844 };

async function sinOverlays(page) {
  await page.evaluate(() => {
    const p = document.getElementById('pista'); if (p) p.classList.remove('on');
    const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on');
  });
}

async function loguear(page, email) {
  await page.fill('#nbMail', email);
  await page.fill('#nbPass', 'Password123!');
  await page.click('#nbGo');
  await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
  await sinOverlays(page);
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('onboarding_tour: "← Atrás" desde "La respuesta corta" cierra la ficha en vez de reabrirla de nuevo', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'onb2@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await ctx.setDefaultTimeout(10000);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await page.setViewportSize(MOBILE);
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await loguear(page, 'onb2@visitar.test');

    await page.evaluate(() => window.NBUProfile.tour());
    await page.waitForSelector('#tourTip h4', { timeout: 5000 });
    let titulo = '';
    for (let i = 0; i < 12; i++) {
      titulo = (await page.locator('#tourTip h4').textContent()) || '';
      if (titulo.includes('respuesta corta')) break;
      await page.click('#tNext');
      await page.waitForTimeout(180);
    }
    afirmar(titulo.includes('respuesta corta'), `no se llegó a "La respuesta corta"; quedó en "${titulo}"`);
    afirmar(await page.locator('.drawer').evaluate(n => n.classList.contains('on')),
      'el paso "La respuesta corta" debería abrir una ficha');

    await page.click('#tPrev');
    await page.waitForTimeout(220);
    const tituloAtras = (await page.locator('#tourTip h4').textContent()) || '';
    afirmar(tituloAtras.includes('Cada resultado'), `"← Atrás" debería volver a "Cada resultado, y qué significa el color"; quedó en "${tituloAtras}"`);
    afirmar(!(await page.locator('.drawer').evaluate(n => n.classList.contains('on'))),
      '"← Atrás" a "Cada resultado" debería cerrar la ficha y mostrar el listado');

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await correrCaso('onboarding_tour: el recorrido siempre arranca en Laboratorio (NBU), aunque se haya quedado en "Buscar en todo"', async () => {
    // Regla del usuario: si el recorrido arranca en "Buscar en todo" varios
    // pasos se saltean o quedan a medio explicar (Filtros, U.B., Árbol de
    // módulos no aplican ahí). startOnboard() ahora fuerza el modo a NBU
    // antes de pintar el primer paso, sin importar en qué modo se haya
    // quedado la persona la última vez.
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'onb5@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await page.setViewportSize(MOBILE);
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await loguear(page, 'onb5@visitar.test');

    await page.selectOption('#modeSel', 'ALL');
    await page.waitForTimeout(120);
    afirmar((await page.locator('#modeSel').inputValue()) === 'ALL', 'el modo debería haber quedado en ALL antes de arrancar el recorrido');

    await page.evaluate(() => window.NBUProfile.tour());
    await page.waitForSelector('#tourTip h4', { timeout: 5000 });
    afirmar((await page.locator('#modeSel').inputValue()) === 'NBU',
      'el recorrido debería haber pasado el modo a NBU (Laboratorio) al arrancar, aunque estuviera en "Buscar en todo"');

    // Y el paso de Filtros, que en modo ALL era inalcanzable, ahora aparece
    // de verdad, con contenido, sin tener que saltearlo.
    let titulo = '';
    for (let i = 0; i < 10; i++) {
      titulo = (await page.locator('#tourTip h4').textContent()) || '';
      if (titulo.includes('Filtros')) break;
      await page.click('#tNext');
      await page.waitForTimeout(160);
    }
    afirmar(titulo.includes('Filtros'), `el paso de Filtros debería aparecer en el recorrido; quedó en "${titulo}"`);
    afirmar(await page.locator('#fFlags .opt').count() > 0, 'el paso de Filtros debería mostrar opciones reales, no quedar vacío');

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await correrCaso('onboarding_tour: "Buscar en todo" oculta el botón de filtros en mobile (no hay ningún filtro que mostrar)', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'onb3@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    const page = await ctx.newPage();
    await page.setViewportSize(MOBILE);
    await instalarSimulador(ctx, db);
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await loguear(page, 'onb3@visitar.test');

    // En NBU (modo de arranque habitual) el botón de filtros está visible.
    // En mobile el selector de nomenclador es <select id="modeSel"> (las
    // tarjetas .modebtn quedan display:none!important debajo de 900px).
    afirmar(await page.locator('#filterToggle').isVisible(), 'en modo NBU el botón de filtros debería verse');

    await page.selectOption('#modeSel', 'ALL');
    await page.waitForTimeout(150);
    afirmar(!(await page.locator('#filterToggle').isVisible()),
      'en "Buscar en todo" el botón de filtros no debería verse: no hay ningún filtro que mostrar');

    // Volver a un modo con filtros lo trae de vuelta.
    await page.selectOption('#modeSel', 'NBU');
    await page.waitForTimeout(150);
    afirmar(await page.locator('#filterToggle').isVisible(), 'al volver a NBU el botón de filtros debería reaparecer');

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await correrCaso('onboarding_tour: el paso "Mesa de trabajo" queda entero a la vista en mobile (la tira de vistas scrollea al costado)', async () => {
    // En 390px de ancho, la tira ".viewtabs" (Listado/Árbol/Mesa de trabajo/
    // Intérprete) desborda y scrollea horizontal — medido: scrollWidth 621 vs
    // clientWidth 360. La pestaña "Mesa de trabajo" arranca parcialmente fuera
    // del viewport (su borde derecho cae más allá de innerWidth). El motor de
    // scroll del recorrido (planScroll/transicion) sólo entendía contenedores
    // verticales, así que el resalte de este paso podía quedar recortado sobre
    // una pestaña a medio tapar por el borde de la pantalla.
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'onb4@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await ctx.setDefaultTimeout(10000);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await page.setViewportSize(MOBILE);
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await loguear(page, 'onb4@visitar.test');

    await page.evaluate(() => window.NBUProfile.tour());
    await page.waitForSelector('#tourTip h4', { timeout: 5000 });
    let titulo = '';
    for (let i = 0; i < 20; i++) {
      titulo = (await page.locator('#tourTip h4').textContent()) || '';
      if (titulo.includes('Mesa de trabajo')) break;
      await page.click('#tNext');
      await page.waitForTimeout(160);
    }
    afirmar(titulo.includes('Mesa de trabajo'), `no se llegó al paso "Mesa de trabajo"; quedó en "${titulo}"`);
    await page.waitForTimeout(300); // termina la transición de scroll

    const rect = await page.locator('.vtab[data-view="validator"]').evaluate(n => {
      const r = n.getBoundingClientRect();
      return { left: r.left, right: r.right };
    });
    afirmar(rect.left >= 0 && rect.right <= 390,
      `la pestaña "Mesa de trabajo" debería quedar entera dentro del viewport (390px); quedó left=${rect.left} right=${rect.right}`);

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

  await browser.close();
  await new Promise((resolve) => srv.close(resolve));
}

main().then(() => process.exit(process.exitCode || 0));
