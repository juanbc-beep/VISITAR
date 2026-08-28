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

  await correrCaso('onboarding_tour: en "Buscar en todo", "← Atrás" desde "Vistas" sigue retrocediendo (no rebota a "Vistas" de nuevo)', async () => {
    // Reproduce el caso real que reportó el usuario: hizo el recorrido estando
    // en modo "Buscar en todo" (ALL), donde NINGÚN filtro aplica (ni sección,
    // ni tipo de Único, ni grupo, ni "reglas y estados" — ver applyMode() y
    // buildGroups()). El paso "Filtros, en tres bloques" nunca puede mostrar
    // nada en ese modo: yendo para adelante eso lo salta correctamente, pero
    // yendo para atrás el bug lo hacía rebotar de nuevo hacia "Vistas" en vez
    // de seguir retrocediendo — de ahí "parece que se cierra el menú
    // hamburguesa": el cajón se abre (antes() de "Filtros") y se cierra en el
    // mismo instante (antes() de "Vistas", al rebotar), en cada intento.
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'onb1@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await ctx.setDefaultTimeout(10000);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await page.setViewportSize(MOBILE);
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);
    await loguear(page, 'onb1@visitar.test');

    await page.selectOption('#modeSel', 'ALL');
    await page.waitForTimeout(120);

    // Arrancar el recorrido completo y avanzar hasta "Vistas" (el paso
    // siguiente a "Filtros, en tres bloques", que en modo ALL es inalcanzable
    // y se saltea solo yendo para adelante).
    await page.evaluate(() => window.NBUProfile.tour());
    await page.waitForSelector('#tourTip h4', { timeout: 5000 });
    let titulo = '';
    for (let i = 0; i < 10; i++) {
      titulo = (await page.locator('#tourTip h4').textContent()) || '';
      if (titulo.includes('Vistas')) break;
      await page.click('#tNext');
      await page.waitForTimeout(180);
    }
    afirmar(titulo.includes('Vistas'), `no se llegó al paso "Vistas"; quedó en "${titulo}"`);
    // El paso anterior visible en el recorrido es "Valor de la Unidad
    // Bioquímica" (el de "Filtros" no aplica en modo ALL y se salteó solo).
    const pasoPrevioEsperado = 'Unidad Bioquímica';

    // El bug: tocar "← Atrás" debería retroceder hasta el paso anterior de
    // verdad (saltando "Filtros", que sigue sin aplicar), no quedarse
    // rebotando entre "Vistas" y el cajón abriéndose/cerrándose en el mismo
    // lugar.
    await page.click('#tPrev');
    await page.waitForTimeout(250);
    const tituloAtras = (await page.locator('#tourTip h4').textContent()) || '';
    afirmar(!tituloAtras.includes('Vistas'),
      `"← Atrás" desde "Vistas" no debería rebotar de nuevo a "Vistas" (bug: se comporta "como si se cerrara el menú hamburguesa")`);
    afirmar(tituloAtras.includes(pasoPrevioEsperado),
      `"← Atrás" desde "Vistas" en modo ALL debería llegar a "${pasoPrevioEsperado}"; quedó en "${tituloAtras}"`);

    afirmar(csp.length === 0, 'no debe haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debe haber errores de JS: ' + errores.join(' | '));
  });

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
