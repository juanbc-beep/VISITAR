/* Manual Inteligente — VISITAR SRL
   Service worker: hace que la app funcione sin internet y que se actualice sola
   cuando el administrador publica una versión nueva.

   Criterio: la app es un archivo grande y estático, así que se sirve siempre desde
   la caché (arranca al instante, incluso sin señal) y en paralelo se revisa si hay
   una versión nueva. Si la hay, se avisa a la pantalla en vez de recargar de golpe:
   nadie quiere que la app se reinicie con un afiliado enfrente.

   Diseñado por Juan Pablo Besada. */

const VERSION = 'nbu-2026-07-31';
const CACHE   = 'manual-nbu-' + VERSION;

/* «nbu_db.bin» es la base de códigos, que desde ahora viaja aparte del index.html.
   Va en la instalación y no en la primera navegación: si esperáramos a que alguien
   la pida, la primera vez sin señal la app abriría sin datos. */
const SHELL = [
  '.', 'index.html', 'nbu_db.bin', 'manifest.webmanifest',
  'icons/icon-32.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    // Uno por uno: si un icono faltara, no queremos que se caiga toda la instalación.
    await Promise.all(SHELL.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const viejas = (await caches.keys()).filter(k => k.startsWith('manual-nbu-') && k !== CACHE);
    await Promise.all(viejas.map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

/* Sólo tocamos lo nuestro. Todo lo que va a Supabase (otro origen, y además POST)
   pasa de largo: cachear respuestas de la base sería servir datos viejos. */
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const enCache = await cache.match(req, { ignoreSearch: true })
                 || (req.mode === 'navigate' ? await cache.match('index.html') : null);

    /* La copia se saca ACÁ, antes de devolver «enCache» más abajo. Al devolverlo,
       el navegador consume su cuerpo, y clonar una respuesta ya leída lanza
       excepción: el .catch() de más abajo se la tragaba y el aviso de versión
       nueva no salía nunca. La actualización llegaba igual, pero en silencio y
       recién en la apertura siguiente. */
    const copiaVieja = enCache ? enCache.clone() : null;

    const red = fetch(req).then(async r => {
      if (r && r.ok) {
        await cache.put(req, r.clone());
        if (copiaVieja && req.mode === 'navigate') {
          const viejo = await copiaVieja.text();
          const nuevo = await r.clone().text();
          if (viejo.length !== nuevo.length) avisar('nueva-version');
        }
      }
      return r;
    }).catch(() => null);

    return enCache || (await red) || new Response(
      '<meta charset="utf-8"><p style="font:15px system-ui;padding:40px">Sin conexión y sin copia guardada todavía. Abrí la app una vez con internet.</p>',
      { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  })());
});

async function avisar(tipo) {
  const cs = await self.clients.matchAll({ type: 'window' });
  cs.forEach(c => c.postMessage({ tipo }));
}

self.addEventListener('message', e => {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
  if (e.data === 'VERSION') e.source && e.source.postMessage({ tipo: 'version', version: VERSION });
});
