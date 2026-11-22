// SPDX-License-Identifier: Apache-2.0
'use strict';
// Pure-source contract: a successful fetch is not proof of an operational organ.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'v5_organs.js'), 'utf8').replace(/\r\n/g, '\n');
const start = source.indexOf('  /* ---- fail-closed public observations');
const end = source.indexOf('  /* ===================================================================\n     1. WILLAY', start);
assert.ok(start > 0 && end > start, 'real v5 evidence classifiers must be present');
const isolated = {};
vm.runInNewContext(source.slice(start, end) +
  '\nglobalThis.observationFunctions = { meshObservation, ledgerObservation };', isolated);
const { meshObservation, ledgerObservation } = isolated.observationFunctions;

function mesh(overrides = {}) {
  return { engines_live: 1, engines_total: 2,
    mesh: [{live:true,name:'first'}, {live:false,name:'second'}], ...overrides };
}
function ledger(overrides = {}) {
  return { total_receipts: 9, chain_alg:'sha3_256', organs: {}, ...overrides };
}

test('a validated inventory is SOURCE-REPORTED, never verified model inference', () => {
  const r = meshObservation(mesh());
  assert.equal(r.valid, true);
  assert.equal(r.state, 'SOURCE_REPORTED_ACTIVE');
  assert.equal(r.nodesUp, 1);
  assert.equal(r.enginesLive, 1);
  assert.equal(r.modelVerified, undefined);
});
test('zero engines and zero up nodes report DOWN, not LIVE', () => {
  const r = meshObservation(mesh({engines_live:0, engines_total:1, mesh:[{live:false}]}));
  assert.equal(r.valid,true);
  assert.equal(r.state,'SOURCE_REPORTED_DOWN');
  assert.equal(r.nodesUp,0);
});
test('HTTP 200 shapes alone cannot make a mesh green', () => {
  for (const p of [null,{},[],{engines_live:1,engines_total:2},
    mesh({engines_live:true}),mesh({engines_live:2,engines_total:1}),
    mesh({engines_live:-1}),mesh({engines_total:NaN}),
    mesh({mesh:[]}),mesh({mesh:[{live:'false'}]}),
    mesh({engines_live:0,mesh:[{live:true}]}),
    mesh({engines_live:1,mesh:[{live:false}]}),
    mesh({engines_total:3}),
    mesh({engines_total:1}),
    mesh({engines_live:0}),
    mesh({engines_live:2}),
    mesh({engines_live:1,mesh:[{live:true},{live:true}]}),
    mesh({engines_live:1,mesh:[{live:false},{live:false}]})]) {
    const r=meshObservation(p);
    assert.equal(r.valid,false, JSON.stringify(p));
    assert.equal(r.state,'UNAVAILABLE');
  }
});
test('adversarial oversized mesh is bounded and fails closed', () => {
  const r=meshObservation(mesh({mesh:Array.from({length:65},()=>({live:true}))}));
  assert.equal(r.valid,false);
});
test('ledger counts do not establish a verified signature or chain', () => {
  const r=ledgerObservation(ledger({signature_verified:true,chain_verified:true}));
  assert.equal(r.valid,true);
  assert.equal(r.state,'SOURCE_REPORTED');
  assert.equal(r.count,9);
  assert.equal(r.signatureVerified,false);
  assert.equal(r.chainVerified,false);
});
test('zero ledger entries is a valid empty source report, not a heartbeat', () => {
  const r=ledgerObservation(ledger({total_receipts:0}));
  assert.equal(r.valid,true);
  assert.equal(r.count,0);
  assert.equal(r.signatureVerified,false);
});
test('missing, negative, string, boolean or malformed ledgers never become source-reported', () => {
  for(const p of [null,{},[],ledger({total_receipts:-1}),ledger({total_receipts:true}),
    ledger({total_receipts:'17'}),ledger({total_receipts:Infinity}),
    ledger({chain_alg:''}),ledger({chain_alg:'<script>'}),
    ledger({total_receipts:Number.MAX_SAFE_INTEGER+1})]){
    const r=ledgerObservation(p);
    assert.equal(r.valid,false,JSON.stringify(p));
    assert.equal(r.state,'UNAVAILABLE');
  }
});
test('actual v5 renderers explicitly separate catalog, mesh, and ledger source from proof', () => {
  const willay=source.slice(source.indexOf('function renderWillay(b){'),source.indexOf('function renderMesh(b){'));
  const meshRenderer=source.slice(source.indexOf('function renderMesh(b){'),source.indexOf('var bloodHUD'));
  const blood=source.slice(source.indexOf('var bloodHUD'),source.indexOf('function verifyCardHTML()'));
  const stack=source.slice(source.indexOf('function renderStack(b){'),source.indexOf('/* ---------------- buttons'));
  assert.match(willay,/classifier catalog/);
  assert.match(willay,/SOURCE-REPORTED/);
  assert.doesNotMatch(willay,/Inspectable signed refusals <span class="v5-chip live">/);
  assert.match(meshRenderer,/meshObservation\(d\)/);
  assert.match(meshRenderer,/REPORTED UP/);
  assert.doesNotMatch(meshRenderer,/var live=!!n\.live/);
  assert.match(blood,/ledgerObservation\(d\)/);
  assert.match(blood,/NOT VERIFIED/);
  assert.doesNotMatch(blood,/\.innerHTML='bloodstream/);
  assert.match(stack,/ledgerObservation\(ledger\)/);
  assert.match(stack,/SOURCE-REPORTED/);
  assert.match(source,/#v5-blood\[data-evidence/); // inline CSS selector
  assert.match(source,/#v5-blood \.bdot\{[^}]*animation:none/);
});

function rendererBody(startMarker, endMarker, reply) {
  const a=source.indexOf(startMarker), b=source.indexOf(endMarker,a);
  assert.ok(a>=0 && b>a);
  const sandbox={ EP:{mesh:'fixture-mesh', ledger:'fixture-ledger'}, meshObservation, ledgerObservation, getJSON:()=>Promise.resolve(reply),
    esc:x=>String(x==null?'':x).replace(/</g,'&lt;'), emptyState:x=>x,
    verifyCardHTML:()=>'<div>OFFLINE VERIFY BUTTON</div>', wireVerify:()=>{} };
  vm.runInNewContext(source.slice(a,b),sandbox);
  return { sandbox, body:{innerHTML:'',querySelector:()=>null} };
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));

test('actual mesh view renders a zero-source node as REPORTED DOWN, never LIVE',async()=>{
  const {sandbox,body}=rendererBody('function renderMesh(b){','/* ===================================================================\n     3a.',mesh({engines_live:0,engines_total:1,mesh:[{name:'engine',live:false}]}));
  sandbox.renderMesh(body);await settle();
  assert.match(body.innerHTML,/SOURCE-REPORTED DOWN/);
  assert.match(body.innerHTML,/REPORTED DOWN/);
  assert.doesNotMatch(body.innerHTML,/class="v5-chip live"/);
});
test('actual mesh view discards contradictory upstream booleans',async()=>{
  const {sandbox,body}=rendererBody('function renderMesh(b){','/* ===================================================================\n     3a.',mesh({engines_live:1,mesh:[{live:'true'}]}));
  sandbox.renderMesh(body);await settle();
  assert.match(body.innerHTML,/INVALID_MESH_REPORT/);
  assert.doesNotMatch(body.innerHTML,/REPORTED UP|class="v5-chip live"/);
});
test('actual mesh view rejects mismatched claimed live and total node counts',async()=>{
  for (const contradictory of [mesh({engines_live:0}), mesh({engines_total:3})]) {
    const {sandbox,body}=rendererBody('function renderMesh(b){','/* ===================================================================\n     3a.',contradictory);
    sandbox.renderMesh(body);await settle();
    assert.match(body.innerHTML,/INCONSISTENT_MESH_REPORT/);
    assert.doesNotMatch(body.innerHTML,/SOURCE-REPORTED ACTIVE|REPORTED UP|class="v5-chip live"/);
  }
});
test('actual ledger view distinguishes source count from a signer/chain verification',async()=>{
  const {sandbox,body}=rendererBody('function renderLedger(b){','function verifyCardHTML()',ledger({total_receipts:13}));
  sandbox.renderLedger(body);await settle();
  assert.match(body.innerHTML,/SOURCE-REPORTED/);
  assert.match(body.innerHTML,/No full-chain replay, independent signer provenance/);
  assert.match(body.innerHTML,/OFFLINE VERIFY BUTTON/);
  assert.doesNotMatch(body.innerHTML,/class="v5-chip live"|every governed decision appends one signed receipt/);
});
