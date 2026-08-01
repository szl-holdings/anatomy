// End-to-end UI contract for the Anatomy Evidence Bay.
// Requires the real Python server to be running; does not mock evidence APIs.
const { chromium } = require('playwright');
const path = require('path');

const BASE = process.env.ANATOMY_BASE_URL || 'http://127.0.0.1:7860';
const EDGE = process.env.PLAYWRIGHT_EXECUTABLE_PATH || undefined;
const OUT = process.env.ANATOMY_QA_OUTPUT || __dirname;
const VIEWPORTS = [
  { name:'desktop', width:1440, height:900 },
  { name:'mobile', width:390, height:844 },
];

async function run(browser, vp) {
  const page = await browser.newPage({viewport:{width:vp.width,height:vp.height}});
  const errors = [];
  page.on('console', msg => { if (msg.type()==='error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push('PAGEERROR: '+err.message));
  const initialEvidence = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === '/api/anatomy/v1/evidence' && response.request().method() === 'GET';
  }, {timeout:45000});
  await page.goto(BASE+'/', {waitUntil:'networkidle'});
  await page.waitForSelector('#fa-launch');
  await page.click('#fa-launch');
  await page.waitForSelector('#fa-panel.open');
  const initialEvidenceResponse = await initialEvidence;
  if (initialEvidenceResponse.status() !== 200) throw new Error(vp.name+' initial evidence HTTP '+initialEvidenceResponse.status());

  const overview = await page.evaluate(() => ({
    title: document.querySelector('.fa-title')?.textContent,
    dimensions: [...document.querySelectorAll('.fa-dim-value')].map(x=>x.textContent),
    launcher: getComputedStyle(document.getElementById('fa-launch')).display,
    panelWidth: document.getElementById('fa-panel').getBoundingClientRect().width,
    viewport: window.innerWidth,
  }));

  await page.click('[data-tab="capabilities"]');
  const capabilityCount = await page.locator('.fa-cap').count();
  // textContent covers the complete declarative shell even when the browser
  // collapses detail descendants during layout/animation.
  const shellText = await page.locator('.fa-cap').first().textContent();

  await page.click('[data-tab="evidence"]');
  try {
    await page.waitForSelector('.fa-dep');
  } catch (error) {
    const activeTab = await page.locator('.fa-tab.active').innerText({timeout:2000}).catch(()=>'missing');
    const evidenceBody = await page.locator('#fa-body').innerText({timeout:2000}).catch(()=>'missing');
    throw new Error(vp.name+' evidence panel timeout; active='+activeTab+'; body='+evidenceBody+'; console='+errors.join(' | ')+'; '+error.message);
  }
  const dependencyCount = await page.locator('.fa-dep').count();
  const dependencyStates = await page.locator('.fa-dep-state').allInnerTexts();

  await page.click('[data-tab="reproduce"]');
  const endpointTexts = await page.locator('.fa-endpoint a').allInnerTexts();
  const [versionResponse, evidenceResponse] = await Promise.all([
    page.request.get(BASE+'/version'),
    page.request.get(BASE+'/evidence'),
  ]);
  const contracts = {
    versionStatus: versionResponse.status(),
    evidenceStatus: evidenceResponse.status(),
    version: await versionResponse.json(),
    evidence: await evidenceResponse.json(),
  };

  await page.click('[data-tab="overview"]');
  await page.click('#fa-verify-bundle');
  await page.waitForSelector('.fa-output.good');
  const verification = await page.locator('.fa-output').innerText();

  await page.screenshot({path:path.join(OUT,'anatomy-evidence-'+vp.name+'.png'),fullPage:true});
  await page.close();

  if (errors.length) throw new Error(vp.name+' console errors: '+errors.join(' | '));
  if (overview.title !== 'Evidence Bay') throw new Error(vp.name+' missing Evidence Bay title');
  if (overview.panelWidth > overview.viewport + 1) throw new Error(vp.name+' panel overflows viewport');
  if (capabilityCount < 5) throw new Error(vp.name+' capability count '+capabilityCount);
  for (const field of ['Purpose','Try','Evidence','Limits','Reproduce']) {
    if (!shellText.includes(field)) throw new Error(vp.name+' missing '+field+' shell');
  }
  if (dependencyCount !== 4) throw new Error(vp.name+' dependency count '+dependencyCount);
  if (!endpointTexts.some(text => text.includes('/version'))) throw new Error(vp.name+' missing /version discovery');
  if (!endpointTexts.some(text => text.includes('/evidence'))) throw new Error(vp.name+' missing /evidence discovery');
  if (contracts.version.schemaVersion !== 'szl.vertical-conformance.version.v1') throw new Error(vp.name+' version schema failed');
  if (contracts.evidence.schemaVersion !== 'szl.vertical-conformance.evidence.v1') throw new Error(vp.name+' evidence schema failed');
  if (contracts.version.evidenceState === 'MEASURED' ? contracts.versionStatus !== 200 : contracts.versionStatus !== 503) throw new Error(vp.name+' version transport/state mismatch');
  if (contracts.evidence.evidenceState === 'PARTIAL' ? contracts.evidenceStatus !== 200 : contracts.evidenceStatus !== 503) throw new Error(vp.name+' evidence transport/state mismatch');
  if (!['MEASURED','UNAVAILABLE'].includes(contracts.version.evidenceState)) throw new Error(vp.name+' unexpected version evidence state '+contracts.version.evidenceState);
  if (!['PARTIAL','UNAVAILABLE'].includes(contracts.evidence.evidenceState)) throw new Error(vp.name+' unexpected evidence state '+contracts.evidence.evidenceState);
  if (!verification.includes('STRUCTURAL-ONLY')) throw new Error(vp.name+' receipt verdict '+verification);
  return {viewport:vp.name, overview, capabilityCount, dependencyCount, dependencyStates, endpointTexts, contracts, verification};
}

(async()=>{
  const browser = await chromium.launch({executablePath:EDGE,headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
  try {
    const results=[];
    for (const vp of VIEWPORTS) results.push(await run(browser,vp));
    console.log(JSON.stringify(results,null,2));
  } finally {
    await browser.close();
  }
})().catch(err=>{ console.error(err); process.exit(1); });
