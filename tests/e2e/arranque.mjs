// Utilidades compartidas por los casos de tests/e2e/casos/*.mjs.
//
// «Servir por http, no file://»: el service worker no corre en file:// y sin
// él la primera carga se comporta distinto a producción. «Un puerto por
// variante»: cada caso levanta su propio servidor en un puerto propio para
// que el service worker de una corrida anterior no le sirva una copia vieja
// a la siguiente (ver HANDOFF.md, sección de Testing).

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const WEB_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../web');

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json', '.bin': 'application/octet-stream',
  '.webmanifest': 'application/manifest+json', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8',
};

export function servirWeb(puerto) {
  return new Promise((resolve, reject) => {
    const srv = createServer(async (req, res) => {
      let p = decodeURIComponent((req.url || '/').split('?')[0]);
      if (p === '/') p = '/index.html';
      const full = path.join(WEB_DIR, p);
      if (!full.startsWith(WEB_DIR)) { res.writeHead(403); res.end(); return; }
      try {
        const data = await readFile(full);
        res.writeHead(200, { 'Content-Type': MIME[path.extname(full)] || 'application/octet-stream' });
        res.end(data);
      } catch (e) {
        res.writeHead(404); res.end('no encontrado: ' + p);
      }
    });
    srv.on('error', reject);
    srv.listen(puerto, () => resolve(srv));
  });
}

// El service worker de la app se actualiza solo y, al tomar el control
// (evento "controllerchange"), la propia app se recarga (ver web/index.html,
// función recargar()) — comportamiento correcto en producción, pero en este
// entorno de pruebas el registro de service workers puede persistir entre
// contextos y disparar esa recarga a mitad de un caso, sin que haya pasado
// nada raro. No es lo que estos casos prueban (para eso haría falta un
// escenario dedicado a la PWA), así que se bloquea de raíz.
export function nuevoContexto(browser) {
  return browser.newContext({ serviceWorkers: 'block' });
}

// Onboarding fuera del camino: sin esto, el recorrido guiado (#tour) intercepta
// todos los clics y ningún selector de la app responde (ver HANDOFF.md, 3.2).
export async function saltarOnboarding(page) {
  await page.addInitScript(() => {
    try { localStorage.setItem('nbu-onboarded', '1'); } catch (e) {}
  });
}

// Espera a que la base termine de cargar: #boot se saca recién ahí (ver
// web/index.html). Sin esto cualquier prueba puede "andar" contra una
// pantalla que todavía dice «Cargando base…».
export async function esperarArranque(page, ms = 30000) {
  await page.waitForFunction(() => !document.getElementById('boot'), null, { timeout: ms });
}

// Junta los errores de JS sin capturar y las violaciones de CSP durante toda
// la vida de la página. Se arma ANTES de navegar — un error del primer
// segundo (que es justo cuando más puede fallar algo) no se pierde.
export function vigilarErrores(page) {
  const errores = [];
  const csp = [];
  page.on('pageerror', e => errores.push(String(e)));
  page.on('console', msg => {
    if (msg.type() !== 'error') return;
    const t = msg.text();
    if (/Content Security Policy|Refused to/i.test(t)) csp.push(t);
    else errores.push(t);
  });
  return { errores, csp };
}

export function afirmar(cond, mensaje) {
  if (!cond) throw new Error(mensaje);
}

// Corre un caso, imprime el resultado con el mismo formato que tests/rls/
// (ERROR: <qué falló>) y fija el código de salida. Centralizado para que cada
// caso sea sólo la lógica del escenario, no repetir el try/catch.
export async function correrCaso(nombre, fn) {
  try {
    await fn();
    console.log(`OK   ${nombre}`);
  } catch (e) {
    console.error(`ERROR ${nombre}: ${e.message}`);
    process.exitCode = 1;
  }
}
