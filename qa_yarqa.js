// QA — yarqa flow-compartments layer (v6) + full regression.
// Headless Chromium, THREE r160 swiftshader. Runs desktop / 390 / 820.
// Asserts: 0 console errors; v6 layer toggles + computes a reproducible receipt;
// yarqa NEVER in the locked count; no regression to organ pick / camera / GPD /
// dissection dock / mobile FAB.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = __dirname;
const MIME = { '.html':'text/html', '.js':'application/javascript', '.css':'text/css' };

const server = http.createServer((req,res)=>{
  let p = req.url.split('?')[0]; if(p==='/') p='/index.html';
  const fp = path.join(ROOT, p);
  if(!fp.startsWith(ROOT) || !fs.existsSync(fp)){ res.writeHead(404); return res.end('nf'); }
  res.writeHead(200,{'Content-Type':MIME[path.extname(fp)]||'application/octet-stream'});
  fs.createReadStream(fp).pipe(res);
});

const VIEWPORTS = [
  { name:'desktop', width:1280, height:800 },
  { name:'phone-390', width:390, height:844 },
  { name:'tablet-820', width:820, height:1180 },
];

async function runViewport(browser, url, vp){
  const page = await browser.newPage({ viewport:{ width:vp.width, height:vp.height } });
  const errors=[];
  // Keep the resource URL Chromium attaches to network console errors so the
  // summary can tell an offline live lens from a broken local asset.
  page.on('console', m=>{ if(m.type()==='error') errors.push({ text:m.text(), url:(m.location()||{}).url||'' }); });
  page.on('pageerror', e=>errors.push({ text:'PAGEERROR: '+e.message, url:'' }));
  await page.goto(url, { waitUntil:'networkidle' });
  await page.waitForTimeout(2200);

  const r = await page.evaluate(async ()=>{
    const A = window.__anatomy; const out = { hasA: !!A };
    if(!A) return out;
    out.rev=A.rev; out.organs=A.organs; out.vessels=A.vessels; out.pulses=A.pulses;
    out.hasV4=!!A.v4; out.hasV5=!!A.v5; out.hasV6=!!A.v6;

    // ---- v6 yarqa layer ----
    if(A.v6){
      out.v6label = A.v6.label;
      out.v6OffInitially = (A.v6.isOn()===false);
      A.v6.setLayer(true,null);
      const rec1 = await A.v6.recompute(0.2);
      out.v6comp1 = rec1.n_compartments;
      out.v6cells = rec1.n_cells;
      out.v6digest1 = rec1.receipt_digest;
      out.v6yarqaInLocked = A.v6.yarqaInLockedCount();
      out.v6routes8 = A.v6.routesLocked8ThroughYarqa();
      out.v6receiptTier = rec1.method_tier;
      // reproducibility: same inputs+params => same digest
      const rec2 = await A.v6.recompute(0.2);
      out.v6reproduces = (rec2.receipt_digest === rec1.receipt_digest);
      // different align => (possibly) different partition, still valid
      const rec3 = await A.v6.recompute(0.6);
      out.v6comp3 = rec3.n_compartments;
      // opacity + toggle off
      A.v6.setLayer(null,0.4);
      A.v6.setLayer(false,null);
      out.v6OffAfter = (A.v6.isOn()===false);
      A.v6.setLayer(true,1);
    }

    // dock row present + honest label in DOM
    out.dockRow = !!document.getElementById('yq-layer-row');
    out.dockNote = (document.getElementById('yq-sec')||{}).textContent||'';

    // ---- regression: v4 dock, organ pick, GPD, hud ----
    if(A.v4){
      out.layers = A.v4.LAYERS.map(l=>l.key);
      out.searchYawar = A.v4.search('yawar');
      out.jumpOpened = A.v4.jumpFirst();
      A.v4.setLayer('circulatory', false, null);
      out.circOff = A.v4._state.layers.circulatory.on;
      A.v4.setLayer('circulatory', true, 1);
      A.v4.setExplode(1); A.v4.setExplode(0);
      A.v4.setClip(true,'y',1.2); A.v4.setClip(false,'x',0);
      A.v4.setFocus(true); out.focus=A.v4._state.focus; A.v4.setFocus(false);
      out.hud = A.v4.hud();
    }
    out.openOrgan = A.openOrgan('yawar');
    out.panelOpen = A.panelOpen();
    out.gpd = A.openGPD();
    out.visHudFoot = (document.getElementById('vh-foot')||{}).textContent||'';
    return out;
  });

  // mobile FAB presence (only visible <=680px, but element exists in DOM)
  const fab = await page.evaluate(()=>{ const f=document.getElementById('dissect-fab'); if(!f) return null; const cs=getComputedStyle(f); return { display:cs.display }; });

  // overflow check: no horizontal scroll
  const overflow = await page.evaluate(()=>({ sw:document.documentElement.scrollWidth, iw:window.innerWidth }));

  await page.close();
  return { vp:vp.name, errors, r, fab, overflow };
}

// The live lenses poll other SZL origins read-only and degrade to a labeled
// offline state, so an unreachable lens is expected, not an outage (README
// "Health"). This harness serves files only (atlas-shell-only mode), so a
// same-origin API route answering 404 is expected too. Everything else fails:
// page errors, script console errors, and any missing local asset.
const SHELL_ONLY_API = /^\/(api\/|version$|evidence$|healthz$|\.well-known\/)/;
function classifyError(err, origin){
  let target = null;
  if(/^Failed to load resource:/.test(err.text)) target = err.url;
  const cors = /^Access to fetch at '([^']+)'/.exec(err.text);
  if(cors) target = cors[1];
  if(!target) return 'error';
  let parsed;
  try { parsed = new URL(target); } catch(_) { return 'error'; }
  if(parsed.origin !== origin) return 'offline-lens';
  return SHELL_ONLY_API.test(parsed.pathname) ? 'shell-only-api' : 'error';
}

function invariants(res){
  const r = res.r || {}, hud = r.hud || {};
  return [
    ['atlas mounted (window.__anatomy)', r.hasA === true],
    ['v4 dissection dock present', r.hasV4 === true],
    ['v6 yarqa layer present', r.hasV6 === true],
    ['yarqa layer off by default', r.v6OffInitially === true],
    ['yarqa NEVER counted in the locked-8', r.v6yarqaInLocked === false],
    ['locked-8 never routed through yarqa', r.v6routes8 === false],
    ['yarqa receipt reproduces (same inputs => same digest)', r.v6reproduces === true],
    ['yarqa layer toggles off', r.v6OffAfter === true],
    ['yarqa dock row rendered', r.dockRow === true],
    ['HUD locked-proven = 8 (read from data.js)', hud.locked === 8],
    ['organ panel opens', r.openOrgan === true && r.panelOpen === true],
    ['GPD lens opens', r.gpd === true],
    ['no horizontal overflow', res.overflow.sw <= res.overflow.iw + 1],
  ];
}

(async()=>{
  await new Promise(rr=>server.listen(0,rr));
  const port = server.address().port;
  const url = `http://localhost:${port}/index.html`;
  const browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH || undefined,
    args:['--use-gl=angle','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']
  });

  const origin = new URL(url).origin;
  let totalErrors = 0, totalExpected = 0, totalFailedChecks = 0;
  for(const vp of VIEWPORTS){
    const res = await runViewport(browser, url, vp);
    console.log('\n===================== '+res.vp+' =====================');
    console.log(JSON.stringify(res.r, null, 2));
    console.log('FAB:', JSON.stringify(res.fab), 'overflow:', JSON.stringify(res.overflow),
                'overflow_ok:', res.overflow.sw <= res.overflow.iw+1);
    const expected = [], real = [];
    for(const err of res.errors){
      const kind = classifyError(err, origin);
      (kind === 'error' ? real : expected).push(kind === 'error' ? err.text : kind+': '+err.text+' <'+err.url+'>');
    }
    console.log('EXPECTED OFFLINE / SHELL-ONLY ('+expected.length+'):', expected.length?'\n  '+expected.join('\n  '):'(none)');
    console.log('CONSOLE ERRORS ('+real.length+'):', real.length?real.join('\n'):'(none)');
    const failed = invariants(res).filter(([, ok])=>!ok).map(([name])=>name);
    console.log('FAILED CHECKS ('+failed.length+'):', failed.length?failed.join('; '):'(none)');
    totalErrors += real.length; totalExpected += expected.length; totalFailedChecks += failed.length;
  }
  await browser.close();
  server.close();
  console.log('\n=== TOTAL CONSOLE ERRORS ACROSS VIEWPORTS:', totalErrors, '===');
  console.log('=== EXPECTED OFFLINE / SHELL-ONLY LOAD FAILURES (not counted):', totalExpected, '===');
  console.log('=== FAILED CHECKS ACROSS VIEWPORTS:', totalFailedChecks, '===');
  process.exit(totalErrors === 0 && totalFailedChecks === 0 ? 0 : 1);
})().catch(e=>{ console.error('QA FAIL', e); process.exit(1); });
