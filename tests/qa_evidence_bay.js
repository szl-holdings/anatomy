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
  await page.goto(BASE+'/', {waitUntil:'networkidle'});
  await page.waitForSelector('#fa-launch');
  await page.click('#fa-launch');
  await page.waitForSelector('#fa-panel.open');

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
  await page.waitForSelector('.fa-dep');
  const dependencyCount = await page.locator('.fa-dep').count();
  const dependencyStates = await page.locator('.fa-dep-state').allInnerTexts();

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
  if (!verification.includes('STRUCTURAL-ONLY')) throw new Error(vp.name+' receipt verdict '+verification);
  return {viewport:vp.name, overview, capabilityCount, dependencyCount, dependencyStates, verification};
}

(async()=>{
  const browser = await chromium.launch({executablePath:EDGE,headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
  const results=[];
  for (const vp of VIEWPORTS) results.push(await run(browser,vp));
  await browser.close();
  console.log(JSON.stringify(results,null,2));
})().catch(err=>{ console.error(err); process.exit(1); });
