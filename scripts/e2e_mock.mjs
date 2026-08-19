import pkg from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pkg;
const HOST='https://gavfxnoigomxbteagneu.supabase.co';
const ANA={id:'aaaa1111-0000-4000-8000-000000000001',nombre:'Ana Gomez',rol:'usuario',estado:'activo'};
const JUAN={id:'bbbb2222-0000-4000-8000-000000000002',nombre:'Juan Pablo Besada',rol:'admin',estado:'activo'};

function baseVacia(){return {correcciones:[],verificaciones:[],propuestas:[],observaciones:[],ajustes:{contenido:{}},perfilExtra:{}};}
// La base es compartida; la identidad es de cada sesion, como en la vida real.
function servidor(yo,db){
  db=db||baseVacia();
  const llamadas=[];
  return {db,llamadas,async ruta(route){
    const req=route.request(), u=new URL(req.url()), m=req.method(), path=u.pathname;
    const cors={'access-control-allow-origin':'*','access-control-allow-headers':'*','access-control-allow-methods':'*','access-control-expose-headers':'*'};
    if(m==='OPTIONS')return route.fulfill({status:204,headers:cors});
    const ok=(b)=>route.fulfill({status:200,headers:Object.assign({'content-type':'application/json'},cors),body:JSON.stringify(b===undefined?null:b)});
    let cuerpo=null; try{cuerpo=req.postDataJSON();}catch(e){}
    llamadas.push(m+' '+path+(u.search||''));

    if(path==='/auth/v1/token')return ok({access_token:'t',refresh_token:'r',expires_in:3600,user:{id:yo.id,email:'x@y.com'}});
    if(path==='/auth/v1/recover'){ db.correosEnviados=(db.correosEnviados||[]); db.correosEnviados.push(cuerpo.email); return ok({}); }
    if(path==='/auth/v1/user' && m==='PUT'){ db.passCambiada={token:(req.headers()['authorization']||'').slice(7), pass:cuerpo.password}; return ok({id:yo.id}); }
    if(path==='/rest/v1/perfiles'){
      if(m==='GET'){ const mio=Object.assign({},yo,db.perfilExtra&&db.perfilExtra[yo.id]||{});
        return ok(u.searchParams.get('id')?[mio]:[JUAN,ANA]); }
      if(m==='PATCH'){ db.perfilExtra=db.perfilExtra||{};
        db.perfilExtra[yo.id]=Object.assign(db.perfilExtra[yo.id]||{},cuerpo); return ok(null); }
      return ok(null);
    }
    // equipo(): id, nombre y rol, sin notas ni favoritos ni U.B. Es lo
    // que pide la app para atribuir autoria, y lo unico que la base le contesta
    // a quien no es administrador (ver docs/supabase.sql). Se devuelven solo
    // esas columnas a proposito: si alguna vez la app volviera a depender de un
    // campo personal, el mock tiene que fallar igual que fallaria el servidor.
    if(path==='/rest/v1/rpc/equipo')
      return ok([JUAN,ANA].map(({id,nombre,rol,estado})=>({id,nombre,rol,estado})));
    if(path==='/rest/v1/rpc/pendientes')return ok({cuentas:0,verificaciones:db.verificaciones.filter(v=>v.estado==='pendiente').length,propuestas:db.propuestas.length});
    if(path==='/rest/v1/rpc/pedir_verificacion'){
      const admin=yo.rol==='admin', c=cuerpo.p_codigo;
      const fila={codigo:c,estado:admin?'validada':'pendiente',solicitada_por:yo.id,solicitada_en:new Date().toISOString(),
                  validada_por:admin?yo.id:null,validada_en:admin?new Date().toISOString():null};
      const i=db.verificaciones.findIndex(v=>v.codigo===c);
      if(i>=0)db.verificaciones[i]=fila; else db.verificaciones.push(fila);
      return ok(null);
    }
    if(path==='/rest/v1/rpc/validar_verificacion'){
      if(yo.rol!=='admin')return route.fulfill({status:400,headers:Object.assign({'content-type':'application/json'},cors),body:JSON.stringify({message:'Sólo el administrador valida una verificación.'})});
      const v=db.verificaciones.find(v=>v.codigo===cuerpo.p_codigo);
      if(v){v.estado='validada';v.validada_por=yo.id;v.validada_en=new Date().toISOString();}
      return ok(null);
    }
    if(path==='/rest/v1/verificaciones'){
      if(m==='GET')return ok(db.verificaciones);
      if(m==='DELETE'){const c=decodeURIComponent((u.searchParams.get('codigo')||'').replace('eq.',''));
        db.verificaciones=db.verificaciones.filter(v=>v.codigo!==c);return ok(null);}
    }
    if(path==='/rest/v1/propuestas'){
      if(m==='GET')return ok(db.propuestas.filter(p=>p.estado==='pendiente'));
      if(m==='POST'){db.propuestas.push(Object.assign({id:'p'+(db.propuestas.length+1),estado:'pendiente',creada:new Date().toISOString()},cuerpo));return ok(null);}
      if(m==='PATCH'){const id=decodeURIComponent((u.searchParams.get('id')||'').replace('eq.',''));
        const p=db.propuestas.find(x=>x.id===id); if(p)Object.assign(p,cuerpo); return ok(null);}
    }
    if(path==='/rest/v1/correcciones'){
      if(m==='GET')return ok(db.correcciones);
      if(m==='POST'){const i=db.correcciones.findIndex(c=>c.codigo===cuerpo.codigo);
        if(i>=0)db.correcciones[i]=cuerpo; else db.correcciones.push(cuerpo); return ok(null);}
      if(m==='DELETE'){const c=decodeURIComponent((u.searchParams.get('codigo')||'').replace('eq.',''));
        db.correcciones=db.correcciones.filter(x=>x.codigo!==c);return ok(null);}
    }
    if(path==='/rest/v1/observaciones'){
      if(m==='GET')return ok(db.observaciones||[]);
      if(m==='POST'){ db.observaciones=db.observaciones||[];
        const i=db.observaciones.findIndex(o=>o.codigo===cuerpo.codigo);
        if(i>=0)db.observaciones[i]=cuerpo; else db.observaciones.push(cuerpo); return ok(null); }
      if(m==='DELETE'){ const c=decodeURIComponent((u.searchParams.get('codigo')||'').replace('eq.',''));
        db.observaciones=(db.observaciones||[]).filter(o=>o.codigo!==c); return ok(null); }
    }
    if(path==='/rest/v1/ajustes'){
      if(m==='GET')return ok([db.ajustes]);
      if(m==='PATCH'){db.ajustes.contenido=cuerpo.contenido;return ok(null);}
    }
    return ok(null);
  }};
}

async function sesion(browser,yo){
  const s=servidor(yo);
  const ctx=await browser.newContext();
  await ctx.route(HOST+'/**',r=>s.ruta(r));
  const p=await ctx.newPage();
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto('file:///home/user/VISITAR/web/index.html');
  await p.waitForTimeout(2500);
  await p.fill('#nbMail','x@y.com'); await p.fill('#nbPass','123456');
  await p.click('#nbGo'); await p.waitForTimeout(2000);
  return {p,ctx,errs,s};
}
export {servidor,baseVacia,sesion,HOST,ANA,JUAN};
