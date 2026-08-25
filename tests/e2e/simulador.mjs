// Simulador de Supabase para los tests de interfaz (tests/e2e).
//
// Esto NO reemplaza a tests/rls/: ahí se prueban las reglas de acceso contra un
// PostgreSQL real, con RLS, triggers y todo lo que implica. Acá el objetivo es
// otro — probar que la INTERFAZ hace lo correcto asumiendo que el servidor
// cumple sus reglas —, así que este simulador es deliberadamente permisivo:
// no reproduce RLS ni decide quién puede hacer qué. Eso está cubierto aparte.
//
// La identidad de cada pedido sale del token Bearer, no de un valor fijado al
// instalar el simulador. Con un valor fijo, dos sesiones en la misma corrida
// (por ejemplo "el administrador" y "el administrativo" en tests/e2e/casos/)
// terminan viendo la misma identidad y la prueba miente sin fallar — es
// exactamente el motivo por el que HANDOFF.md marca esto como el error a no
// repetir. Acá la base (`db`) es compartida entre navegadores/contextos si
// hace falta simular dos personas a la vez, y cada uno mantiene su propio
// token.

import crypto from 'node:crypto';

export const SUPABASE_HOST = 'https://gavfxnoigomxbteagneu.supabase.co';

export function crearDB() {
  return {
    users: new Map(),         // email -> {id, email, password, nombre}
    tokens: new Map(),        // access_token -> uid
    refresh: new Map(),       // refresh_token -> uid
    perfiles: new Map(),      // id -> fila de public.perfiles
    correcciones: new Map(),  // codigo -> fila
    verificaciones: new Map(),// codigo -> fila
    propuestas: new Map(),    // id (uuid) -> fila, como la tabla real
    observaciones: new Map(), // codigo -> fila
    ajustes: { contenido: {} },
    recovers: [],             // correos que pidieron recuperar contraseña (para el caso "recup")
    factores: new Map(),      // uid -> [{id, factor_type:'totp', status, friendly_name}]
    desafios: new Map(),      // challenge_id -> {uid, factorId}
    sugerenciasPedidaComo: new Map(), // id (uuid) -> fila, como la tabla real
  };
}

// Da de alta una cuenta ya aprobada (o no) sin pasar por el flujo de alta —
// para sembrar el escenario de cada test sin repetir el formulario cada vez.
export function altaUsuario(db, { nombre, email, password, rol = 'usuario', estado = 'activo', id } = {}) {
  const uid = id || crypto.randomUUID();
  db.users.set(email, { id: uid, email, password, nombre });
  db.perfiles.set(uid, {
    id: uid, nombre, rol, estado,
    favoritos: [], notas: {}, recientes: [], ub: null,
    creado: new Date().toISOString(), actualizado: new Date().toISOString(),
  });
  return uid;
}

// Da de alta una cuenta que ya tiene la verificación en dos pasos activada
// desde antes, para los casos que prueban el candado del login sin tener
// que pasar primero por el alta desde la app.
export function activarMFA(db, uid, { factorId, friendlyName = 'Administrador' } = {}) {
  const id = factorId || crypto.randomUUID();
  const lista = db.factores.get(uid) || [];
  lista.push({ id, factor_type: 'totp', status: 'verified', friendly_name: friendlyName });
  db.factores.set(uid, lista);
  return id;
}

// Deja un factor SIN verificar, como el que queda cuando un alta anterior
// se corta a mitad de camino (se recargó la página, el QR no llegó a
// mostrarse). Sirve para reproducir el bloqueo real de producción del
// 25/8/2026 y probar que NUBE.enrolarTOTP() lo limpia solo.
export function dejarFactorPendiente(db, uid, { friendlyName = 'Administrador' } = {}) {
  const id = crypto.randomUUID();
  const lista = db.factores.get(uid) || [];
  lista.push({ id, factor_type: 'totp', status: 'unverified', friendly_name: friendlyName });
  db.factores.set(uid, lista);
  return id;
}

// Único código que el simulador acepta como válido en /verify — no hace TOTP
// de verdad, sólo necesita distinguir "código correcto" de "código incorrecto"
// para probar los dos caminos del candado.
const MFA_CODE_OK = '123456';

function emitirTokens(db, uid) {
  const t = 'tok_' + crypto.randomBytes(12).toString('hex');
  const r = 'ref_' + crypto.randomBytes(12).toString('hex');
  db.tokens.set(t, uid);
  db.refresh.set(r, uid);
  return { access_token: t, refresh_token: r };
}

function identidad(db, req) {
  const auth = req.headers()['authorization'] || '';
  const t = auth.replace(/^Bearer\s+/i, '');
  const uid = db.tokens.get(t);
  return uid ? db.perfiles.get(uid) : null;
}

function leerCuerpo(req) {
  try { return JSON.parse(req.postData() || '{}'); } catch (e) { return {}; }
}

function responder(route, status, body) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: body === undefined ? '' : JSON.stringify(body),
  });
}

// Sólo entiende "columna=eq.valor", que es lo único que usa el cliente
// (ver web/index.html, módulo NUBE): no hace falta un parser de PostgREST completo.
function filtroEq(url, columna) {
  const v = url.searchParams.get(columna);
  const m = v && v.match(/^eq\.(.*)$/);
  return m ? decodeURIComponent(m[1]) : null;
}

function esMinimal(req) {
  return /return=minimal/i.test(req.headers()['prefer'] || '');
}

export async function instalarSimulador(context, db) {
  await context.route(SUPABASE_HOST + '/**', async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname;
    const method = req.method();

    // ---------------- AUTH ----------------
    if (path === '/auth/v1/token') {
      const grant = url.searchParams.get('grant_type');
      const body = leerCuerpo(req);
      if (grant === 'password') {
        const u = db.users.get(body.email);
        if (!u || u.password !== body.password)
          return responder(route, 400, { error_description: 'Invalid login credentials' });
        const { access_token, refresh_token } = emitirTokens(db, u.id);
        return responder(route, 200, {
          access_token, refresh_token, expires_in: 3600, token_type: 'bearer',
          user: { id: u.id, email: u.email },
        });
      }
      if (grant === 'refresh_token') {
        const uid = db.refresh.get(body.refresh_token);
        if (!uid) return responder(route, 400, { error_description: 'Invalid Refresh Token' });
        const u = [...db.users.values()].find(x => x.id === uid);
        const { access_token, refresh_token } = emitirTokens(db, uid);
        return responder(route, 200, {
          access_token, refresh_token, expires_in: 3600, token_type: 'bearer',
          user: { id: uid, email: u ? u.email : '' },
        });
      }
      return responder(route, 400, { error_description: 'grant_type no soportado por el simulador' });
    }

    if (path === '/auth/v1/signup') {
      const body = leerCuerpo(req);
      if (db.users.has(body.email))
        return responder(route, 400, { error_description: 'User already registered' });
      const nombre = (body.data && body.data.nombre) || body.email.split('@')[0];
      altaUsuario(db, { nombre, email: body.email, password: body.password, rol: 'usuario', estado: 'pendiente' });
      return responder(route, 200, { user: { email: body.email } });
    }

    if (path === '/auth/v1/recover') {
      const body = leerCuerpo(req);
      db.recovers.push(body.email);
      return responder(route, 200, {}); // Supabase contesta lo mismo exista o no la cuenta
    }

    if (path === '/auth/v1/user' && method === 'PUT') {
      const yo = identidad(db, req);
      const body = leerCuerpo(req);
      const auth = req.headers()['authorization'] || '';
      const t = auth.replace(/^Bearer\s+/i, '');
      const uid = yo ? yo.id : db.tokens.get(t);
      if (!uid) return responder(route, 401, { error_description: 'JWT inválido' });
      const u = [...db.users.values()].find(x => x.id === uid);
      if (u && body.password) u.password = body.password;
      return responder(route, 200, { id: uid });
    }

    if (path === '/auth/v1/logout') {
      const auth = req.headers()['authorization'] || '';
      db.tokens.delete(auth.replace(/^Bearer\s+/i, ''));
      return responder(route, 204);
    }

    // ---------------- AUTH: verificación en dos pasos (TOTP) ----------------
    // GET /auth/v1/user siempre existe en la API real (no sólo el PUT de acá
    // arriba, que sólo entiende cambiar la contraseña): trae el usuario con sus
    // factores, lo pida o no la cuenta. Antes de sumar esto, un login como
    // administrador contra el simulador quedaba con un 404 silencioso — el
    // candado (ver web/index.html, continuarLogin()) lo dejaba pasar igual
    // porque falla abierto, pero el 404 quedaba en la consola y rompía la
    // aserción "sin errores de JS" de otros casos que no tienen nada que ver
    // con esto.
    if (path === '/auth/v1/user' && method === 'GET') {
      const yo = identidad(db, req);
      if (!yo) return responder(route, 401, { error_description: 'JWT inválido' });
      const u = [...db.users.values()].find(x => x.id === yo.id);
      return responder(route, 200, {
        id: yo.id, email: u ? u.email : '',
        factors: db.factores.get(yo.id) || [],
      });
    }
    if (path === '/auth/v1/factors' && method === 'POST') {
      const yo = identidad(db, req);
      if (!yo) return responder(route, 401, { error_description: 'JWT inválido' });
      const body = leerCuerpo(req);
      const lista = db.factores.get(yo.id) || [];
      // Mismo rechazo que la API real (visto en producción el 25/8/2026): un
      // factor sin verificar de un intento anterior bloquea el alta hasta
      // que se lo borra — es lo que NUBE.enrolarTOTP() tiene que evitar solo.
      const nombre = body.friendly_name || 'totp';
      if (lista.some(f => f.friendly_name === nombre))
        return responder(route, 422, { error_description: `A factor with the friendly name "${nombre}" for this user already exists` });
      const id = crypto.randomUUID();
      lista.push({ id, factor_type: 'totp', status: 'unverified', friendly_name: nombre });
      db.factores.set(yo.id, lista);
      return responder(route, 200, {
        id, type: 'totp', friendly_name: body.friendly_name || 'totp',
        totp: {
          // SVG crudo, sin el prefijo "data:" — es lo que manda la API real
          // (encontrado el 25/8/2026 al ver que el QR no se mostraba en
          // producción; ver qrComoImagen() en web/index.html). Con un
          // rectángulo visible, para que un screenshot de prueba se note si
          // alguna vez deja de envolverse en el data URI.
          qr_code: '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><rect width="120" height="120" fill="#fff"/><rect x="10" y="10" width="100" height="100" fill="#000"/></svg>',
          secret: 'SIMULADOR2FASECRETODEPRUEBA',
          uri: `otpauth://totp/VISITAR:${encodeURIComponent(yo.id)}?secret=SIMULADOR2FASECRETODEPRUEBA&issuer=VISITAR`,
        },
      });
    }
    {
      const mChallenge = path.match(/^\/auth\/v1\/factors\/([^/]+)\/challenge$/);
      if (mChallenge && method === 'POST') {
        const yo = identidad(db, req);
        if (!yo) return responder(route, 401, { error_description: 'JWT inválido' });
        const factorId = mChallenge[1];
        const desafioId = crypto.randomUUID();
        db.desafios.set(desafioId, { uid: yo.id, factorId });
        return responder(route, 200, { id: desafioId, expires_at: Math.floor(Date.now() / 1000) + 60 });
      }
      const mVerify = path.match(/^\/auth\/v1\/factors\/([^/]+)\/verify$/);
      if (mVerify && method === 'POST') {
        const yo = identidad(db, req);
        if (!yo) return responder(route, 401, { error_description: 'JWT inválido' });
        const factorId = mVerify[1];
        const body = leerCuerpo(req);
        const desafio = db.desafios.get(body.challenge_id);
        if (!desafio || desafio.uid !== yo.id || desafio.factorId !== factorId)
          return responder(route, 400, { error_description: 'Challenge no encontrado o vencido' });
        db.desafios.delete(body.challenge_id);
        // Como no hay TOTP de verdad, el simulador acepta un único código fijo
        // — alcanza para probar el camino bueno y el de código incorrecto.
        if (body.code !== MFA_CODE_OK)
          return responder(route, 400, { error_description: 'Invalid TOTP code entered' });
        const lista = db.factores.get(yo.id) || [];
        const f = lista.find(x => x.id === factorId);
        if (f) f.status = 'verified';
        const { access_token, refresh_token } = emitirTokens(db, yo.id);
        const u = [...db.users.values()].find(x => x.id === yo.id);
        return responder(route, 200, {
          access_token, refresh_token, expires_in: 3600, token_type: 'bearer',
          user: { id: yo.id, email: u ? u.email : '' },
        });
      }
      const mDelete = path.match(/^\/auth\/v1\/factors\/([^/]+)$/);
      if (mDelete && method === 'DELETE') {
        const yo = identidad(db, req);
        if (!yo) return responder(route, 401, { error_description: 'JWT inválido' });
        const factorId = mDelete[1];
        const lista = db.factores.get(yo.id) || [];
        db.factores.set(yo.id, lista.filter(x => x.id !== factorId));
        return responder(route, 200, {});
      }
    }

    // ---------------- REST: perfiles ----------------
    if (path === '/rest/v1/perfiles') {
      if (method === 'GET') {
        const id = filtroEq(url, 'id');
        const lista = [...db.perfiles.values()];
        const filas = id ? lista.filter(p => p.id === id) : lista.slice().sort(
          (a, b) => (a.estado + a.nombre).localeCompare(b.estado + b.nombre));
        return responder(route, 200, filas);
      }
      if (method === 'PATCH') {
        const id = filtroEq(url, 'id');
        const p = db.perfiles.get(id);
        if (!p) return responder(route, 200, esMinimal(req) ? undefined : []);
        Object.assign(p, leerCuerpo(req), { actualizado: new Date().toISOString() });
        return responder(route, esMinimal(req) ? 204 : 200, esMinimal(req) ? undefined : [p]);
      }
      if (method === 'DELETE') {
        const id = filtroEq(url, 'id');
        db.perfiles.delete(id);
        return responder(route, 204);
      }
    }

    if (path === '/rest/v1/rpc/equipo' && method === 'POST') {
      return responder(route, 200, [...db.perfiles.values()]
        .map(p => ({ id: p.id, nombre: p.nombre, rol: p.rol, estado: p.estado })));
    }
    // Mismas claves que la función real (docs/supabase.sql, sección 8): el
    // cliente (contarPendientes()) es el que traduce a v/pr/cu — acá no.
    if (path === '/rest/v1/rpc/pendientes' && method === 'POST') {
      const verificaciones = [...db.verificaciones.values()].filter(x => x.estado === 'pendiente').length;
      const propuestas = [...db.propuestas.values()].filter(x => x.estado === 'pendiente').length;
      const cuentas = [...db.perfiles.values()].filter(x => x.estado === 'pendiente').length;
      return responder(route, 200, { cuentas, verificaciones, propuestas });
    }
    if (path === '/rest/v1/rpc/transferir_admin' && method === 'POST') {
      const yo = identidad(db, req);
      const { nuevo } = leerCuerpo(req);
      const destino = db.perfiles.get(nuevo);
      if (yo && destino) { yo.rol = 'usuario'; destino.rol = 'admin'; }
      return responder(route, 200, {});
    }

    // ---------------- REST: correcciones ----------------
    if (path === '/rest/v1/correcciones') {
      if (method === 'GET') return responder(route, 200, [...db.correcciones.values()]);
      if (method === 'POST') {
        const body = leerCuerpo(req);
        db.correcciones.set(body.codigo, body);
        return responder(route, esMinimal(req) ? 201 : 200, esMinimal(req) ? undefined : [body]);
      }
      if (method === 'DELETE') {
        db.correcciones.delete(filtroEq(url, 'codigo'));
        return responder(route, 204);
      }
    }

    // ---------------- REST: verificaciones ----------------
    if (path === '/rest/v1/verificaciones') {
      if (method === 'GET') return responder(route, 200, [...db.verificaciones.values()]);
      if (method === 'DELETE') {
        db.verificaciones.delete(filtroEq(url, 'codigo'));
        return responder(route, 204);
      }
    }
    // Mismo atajo que la función real: si quien pide ya es admin, queda
    // validada de una (docs/supabase.sql, pedir_verificacion).
    if (path === '/rest/v1/rpc/pedir_verificacion' && method === 'POST') {
      const yo = identidad(db, req);
      const { p_codigo } = leerCuerpo(req);
      const admin = !!(yo && yo.rol === 'admin');
      db.verificaciones.set(p_codigo, {
        codigo: p_codigo, estado: admin ? 'validada' : 'pendiente',
        solicitada_por: yo && yo.id, solicitada_en: new Date().toISOString(),
        validada_por: admin ? (yo && yo.id) : null,
        validada_en: admin ? new Date().toISOString() : null,
      });
      return responder(route, 200, {});
    }
    if (path === '/rest/v1/rpc/validar_verificacion' && method === 'POST') {
      const yo = identidad(db, req);
      const { p_codigo } = leerCuerpo(req);
      const v = db.verificaciones.get(p_codigo) || { codigo: p_codigo };
      Object.assign(v, {
        estado: 'validada', validada_por: yo && yo.id, validada_en: new Date().toISOString(),
      });
      db.verificaciones.set(p_codigo, v);
      return responder(route, 200, {});
    }

    // ---------------- REST: propuestas ----------------
    if (path === '/rest/v1/propuestas') {
      if (method === 'GET') {
        const estado = filtroEq(url, 'estado');
        let filas = [...db.propuestas.values()];
        if (estado) filas = filas.filter(p => p.estado === estado);
        filas = filas.slice().sort((a, b) => (b.creada || '').localeCompare(a.creada || ''));
        return responder(route, 200, filas);
      }
      if (method === 'POST') {
        const body = leerCuerpo(req);
        const fila = Object.assign({
          id: crypto.randomUUID(), estado: 'pendiente', creada: new Date().toISOString(),
        }, body);
        db.propuestas.set(fila.id, fila);
        return responder(route, esMinimal(req) ? 201 : 200, esMinimal(req) ? undefined : [fila]);
      }
      if (method === 'PATCH') {
        const id = filtroEq(url, 'id');
        const p = db.propuestas.get(id);
        if (p) Object.assign(p, leerCuerpo(req));
        return responder(route, esMinimal(req) ? 204 : 200, esMinimal(req) ? undefined : [p]);
      }
    }

    // ---------------- REST: sugerencias_pedida_como (Intérprete de orden) ----
    if (path === '/rest/v1/sugerencias_pedida_como') {
      if (method === 'GET') {
        const estado = filtroEq(url, 'estado');
        let filas = [...db.sugerenciasPedidaComo.values()];
        if (estado) filas = filas.filter(s => s.estado === estado);
        filas = filas.slice().sort((a, b) => (b.creada || '').localeCompare(a.creada || ''));
        return responder(route, 200, filas);
      }
      if (method === 'POST') {
        const body = leerCuerpo(req);
        const fila = Object.assign({
          id: crypto.randomUUID(), estado: 'pendiente', creada: new Date().toISOString(),
        }, body);
        db.sugerenciasPedidaComo.set(fila.id, fila);
        return responder(route, esMinimal(req) ? 201 : 200, esMinimal(req) ? undefined : [fila]);
      }
      if (method === 'PATCH') {
        const id = filtroEq(url, 'id');
        const s = db.sugerenciasPedidaComo.get(id);
        if (s) Object.assign(s, leerCuerpo(req));
        return responder(route, esMinimal(req) ? 204 : 200, esMinimal(req) ? undefined : [s]);
      }
    }

    // ---------------- REST: observaciones ----------------
    if (path === '/rest/v1/observaciones') {
      if (method === 'GET') {
        const filas = [...db.observaciones.values()].slice()
          .sort((a, b) => (b.actualizada || '').localeCompare(a.actualizada || ''));
        return responder(route, 200, filas);
      }
      if (method === 'POST') {
        const body = leerCuerpo(req);
        db.observaciones.set(body.codigo, body);
        return responder(route, esMinimal(req) ? 201 : 200, esMinimal(req) ? undefined : [body]);
      }
      if (method === 'DELETE') {
        db.observaciones.delete(filtroEq(url, 'codigo'));
        return responder(route, 204);
      }
    }

    // ---------------- REST: ajustes ----------------
    if (path === '/rest/v1/ajustes') {
      if (method === 'GET') return responder(route, 200, [{ contenido: db.ajustes.contenido }]);
      if (method === 'PATCH') {
        const body = leerCuerpo(req);
        if (body.contenido) db.ajustes.contenido = body.contenido;
        return responder(route, esMinimal(req) ? 204 : 200, esMinimal(req) ? undefined : [db.ajustes]);
      }
    }

    // Cualquier otra cosa: 404 explícito, para que un endpoint nuevo que el
    // simulador todavía no conoce falle ruidoso en vez de colgarse.
    return responder(route, 404, { error_description: `El simulador no conoce ${method} ${path}` });
  });
}
