// Caso "historial_ficha": el administrador general puede ver, desde la propia
// ficha, quién la corrigió, cuándo, y qué decía antes de cada cambio. No es
// una tabla nueva — «auditoria» (docs/supabase.sql) ya registraba esto solo,
// por un trigger, desde antes de que hubiera ninguna pantalla que lo
// mostrara; sólo hacía falta NUBE.historialFicha() y el botón «🕘 Ver
// historial» al lado de «✎ Editar ficha». Sólo lo ve el administrador
// general (misma RLS de «auditoria» de siempre: `es_admin()`), y sólo con la
// nube activa.
//
// Ver web/index.html: NUBE.historialFicha(), diffCorreccion(), y el handler
// de #histFichaBtn. HANDOFF.md, 26/8/2026.

import { chromium } from 'playwright';
import { crearDB, altaUsuario, instalarSimulador } from '../simulador.mjs';
import { servirWeb, saltarOnboarding, esperarArranque, vigilarErrores, afirmar, correrCaso, nuevoContexto } from '../arranque.mjs';

const PUERTO = 8629;
// ACTO BIOQUÍMICO — código NBU real y estable (data/nbu_db.json).
const CODIGO = '660001';

async function sinOverlays(page) {
  await page.evaluate(() => {
    const p = document.getElementById('pista'); if (p) p.classList.remove('on');
    const t = document.getElementById('tratoModal'); if (t) t.classList.remove('on');
  });
}

// #histFichaBtn muestra el panel de una (cont.hidden=false, síncrono) y recién
// después pide NUBE.historialFicha() — mientras tanto dice "Cargando…". Esperar
// sólo a que deje de estar oculto es una carrera: en CI, más lenta que en
// local, se ve perder — el texto se leía a mitad de camino y el caso fallaba
// sin que hubiera nada mal en la pantalla real. Hay que esperar el contenido
// final, no la visibilidad del contenedor.
async function esperarHistorialCargado(page) {
  await page.waitForFunction(() => {
    const el = document.getElementById('dHistorial');
    return !!(el && !el.hidden && el.textContent && !el.textContent.includes('Cargando'));
  }, null, { timeout: 5000 });
}

async function editarNombre(page, nombreNuevo) {
  await page.click('#editFichaBtn');
  await page.waitForSelector('#efNom', { timeout: 5000 });
  await page.fill('#efNom', nombreNuevo);
  await page.click('#efSave');
  await page.waitForSelector('#efNom', { state: 'hidden', timeout: 5000 }); // cierra el modal (closeAdmin())
  await page.waitForTimeout(300); // guardarCorreccion es fire-and-forget
  await sinOverlays(page);
}

async function main() {
  const srv = await servirWeb(PUERTO);
  const base = `http://localhost:${PUERTO}/`;
  const browser = await chromium.launch();

  await correrCaso('historial_ficha: el administrador ve quién corrigió, cuándo, y qué decía antes', async () => {
    const db = crearDB();
    altaUsuario(db, { nombre: 'Admin General', email: 'admin@visitar.test', password: 'Password123!', rol: 'admin', estado: 'activo' });
    const ctx = await nuevoContexto(browser);
    await instalarSimulador(ctx, db);
    const page = await ctx.newPage();
    await saltarOnboarding(page);
    const { errores, csp } = vigilarErrores(page);
    await page.goto(base);
    await esperarArranque(page);

    await page.fill('#nbMail', 'admin@visitar.test');
    await page.fill('#nbPass', 'Password123!');
    await page.click('#nbGo');
    await page.waitForSelector('#acctChip:not([hidden])', { timeout: 5000 });
    await sinOverlays(page);
    await page.click('#editModeBtn'); // "Editar ficha" (y "Ver historial", al lado) sólo aparecen en modo edición

    await page.evaluate((c) => { location.hash = c; }, CODIGO);
    await sinOverlays(page);
    await page.waitForSelector('#histFichaBtn', { timeout: 5000 });

    // Todavía nadie corrigió nada: sin historial.
    await page.click('#histFichaBtn');
    await esperarHistorialCargado(page);
    afirmar((await page.textContent('#dHistorial')).includes('Sin cambios registrados todavía'),
      'sin ninguna corrección hecha todavía, el historial debería decirlo');

    // Primera corrección: es un alta (no había fila en "correcciones" antes).
    await editarNombre(page, 'Acto Bioquímico (revisado)');
    await page.waitForSelector('#histFichaBtn', { timeout: 5000 });
    await page.click('#histFichaBtn');
    await esperarHistorialCargado(page);
    let texto = await page.textContent('#dHistorial');
    afirmar(texto.includes('Admin General'), 'debería decir quién hizo la corrección');
    afirmar(texto.includes('primera vez que se corrige'), 'la primera corrección debería marcarse como alta');
    afirmar(texto.includes('Nombre') && texto.includes('Acto Bioquímico (revisado)'),
      'debería listar "Nombre" entre los campos que cambiaron, con el valor nuevo');
    afirmar(!texto.includes('→'), 'siendo la primera corrección (alta), no debería mostrar un "antes" — no lo hay');

    // Segunda corrección: ahora sí hay "antes" (la fila ya existía).
    await editarNombre(page, 'Acto Bioquímico (revisado 2)');
    await page.waitForSelector('#histFichaBtn', { timeout: 5000 });
    await page.click('#histFichaBtn');
    await esperarHistorialCargado(page);
    texto = await page.textContent('#dHistorial');
    afirmar(!texto.includes('Sin cambios registrados'), 'ya hay dos correcciones, no debería decir que no hay ninguna');
    afirmar(texto.includes('Acto Bioquímico (revisado) → Acto Bioquímico (revisado 2)'),
      'la segunda corrección debería mostrar el nombre anterior y el nuevo, no sólo el nuevo');
    // El orden es del más nuevo al más viejo: la corrección con "antes" real
    // (la segunda) tiene que aparecer ANTES que la de "primera vez" en el texto.
    afirmar(texto.indexOf('Acto Bioquímico (revisado) → Acto Bioquímico (revisado 2)') <
            texto.indexOf('primera vez que se corrige'),
      'el historial debería listarse del cambio más reciente al más viejo');

    afirmar(csp.length === 0, 'no debería haber violaciones de CSP: ' + csp.join(' | '));
    afirmar(errores.length === 0, 'no debería haber errores de JS sin capturar: ' + errores.join(' | '));
    await ctx.close();
  });

  await browser.close();
  srv.close();
}

main();
