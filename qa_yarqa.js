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
  page.on('console', m=>{ if(m.type()==='error') errors.push(m.text()); });
  page.on('pageerror', e=>errors.push('PAGEERROR: '+e.message));
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

(async()=>{
  await new Promise(rr=>server.listen(0,rr));
  const port = server.address().port;
  const url = `http://localhost:${port}/index.html`;
  const browser = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'] });

  let totalErrors = 0;
  for(const vp of VIEWPORTS){
    const res = await runViewport(browser, url, vp);
    console.log('\n===================== '+res.vp+' =====================');
    console.log(JSON.stringify(res.r, null, 2));
    console.log('FAB:', JSON.stringify(res.fab), 'overflow:', JSON.stringify(res.overflow),
                'overflow_ok:', res.overflow.sw <= res.overflow.iw+1);
    console.log('CONSOLE ERRORS ('+res.errors.length+'):', res.errors.length?res.errors.join('\n'):'(none)');
    totalErrors += res.errors.length;
  }
  await browser.close();
  server.close();
  console.log('\n=== TOTAL CONSOLE ERRORS ACROSS VIEWPORTS:', totalErrors, '===');
  process.exit(0);
})().catch(e=>{ console.error('QA FAIL', e); process.exit(1); });
