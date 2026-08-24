// Caso "favs": la lista de favoritos que publica el administrador
// (ajustes.contenido.equipo.favoritos, ver HANDOFF.md 4.4 ter) tiene que
// llegar a la pantalla de otra cuenta. Es justo la clase de regresión que no
// se nota mirando la app: si algo rompe la lectura de ese JSON anidado, la
// solapa "Del equipo" simplemente queda vacía y nadie lo asocia con un bug.
//
// Se siembra la lista directo en el simulador (lo que en producción hace el
// botón «👥 Compartir con el equipo» del administrador) y se verifica que
// una SEGUNDA cuenta, sin ningún favorito propio, la ve al entrar. El interés
// del test es la lectura/el render, que es la parte frágil.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8613;
// ACTO BIOQUÍMICO — código NBU real y estable (data/nbu_db.json), no inventado,
// para que el test de verdad ejercite BYCODE con datos que existen.
const CODIGO_NBU = '660001';

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('favs: el favorito publicado por el admin aparece en otra cuenta', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Sin Favoritos', email: 'sinfavs@visitar.test', password: 'Password123!', rol: 'usuario', estado: 'activo' });
    db.ajustes.contenido = { equipo: { favoritos: [CODIGO_NBU] } };

    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    await page.fill('#nbMail', 'sinfavs@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });

    // cargarContenidoNube() se dispara después de mostrar la app (ver
    // web/index.html, enterProfile): esperar a que la solapa exista, no un
    // tiempo fijo.
    await page.waitForSelector('#rapidos button[data-rap="eq"]', { timeout: 8000 });
    await page.click('#rapidos button[data-rap="eq"]');
    await page.waitForSelector(`#rapidos .rcard[data-code="${CODIGO_NBU}"]`, { timeout: 5000 });

    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

await main();
