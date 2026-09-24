const test = require('node:test');
const assert = require('node:assert/strict');
const {observationView, observationHTML, updateObservationFreshness} = require('../frontier_anatomy.js');
const now = Date.parse('2026-09-24T12:00:30Z');
function row(overrides = {}) {
  return {id:'a11oy.organ-integrity', observation_contract:'szl.anatomy-dependency-observation/v1',
    contract_validated:true, contract_state:'AVAILABLE', content_type:'application/json; charset=utf-8',
    transport_state:'REACHABLE', http_status:200, observed_at:'2026-09-24T12:00:00Z',
    posture_state:'UNKNOWN', evidence_state:'UNAVAILABLE',
    measured:{state:'UNKNOWN', live:false, blocked:false, live_count:null, organ_count:0, organs:[]}, ...overrides};
}
test('reachable, valid UNKNOWN response with empty organs never becomes measured live', () => {
  const result=observationView(row(),now);
  assert.equal(result.validated,true); assert.equal(result.evidence,'UNAVAILABLE');
  const html=observationHTML({dependencies:[row()]},now,false);
  assert.match(html,/organ posture is unknown/); assert.match(html,/0 measured observations/);
});
test('legacy HTTP200 and asserted LIVE without typed contract remain unvalidated', () => {
  const result=observationView(row({observation_contract:undefined,evidence_state:'LIVE'}),now);
  assert.equal(result.validated,false); assert.equal(result.evidence,'UNAVAILABLE');
});
test('HTML200 and rate limiting cannot produce validated observations', () => {
  for(const override of [{content_type:'text/html'},{http_status:429,contract_state:'RATE_LIMITED'}]) {
    const result=observationView(row({...override,evidence_state:'MEASURED',posture_state:'REPORTED'}),now);
    assert.equal(result.validated,false); assert.equal(result.evidence,'UNAVAILABLE');
  }
});
test('explicit consistent body observation is LIVE but no inferred organs are admitted', () => {
  const measured={state:'LIVE',live:true,blocked:false,live_count:2,organ_count:2,organs:[{id:'heart',status:'LIVE'},{id:'brain',status:'LIVE'}]};
  const live=row({posture_state:'OBSERVED_LIVE',evidence_state:'LIVE',measured});
  assert.equal(observationView(live,now).evidence,'LIVE');
  for(const bad of [{live:false},{blocked:true},{live_count:0},{live_count:1},{organs:[]},
    {organs:[{id:'heart',status:'LIVE'},{id:'heart',status:'LIVE'}]},
    {organs:[{id:'heart',status:'LIVE'},{id:'brain',status:'DOWN'}]}]) {
    assert.equal(observationView({...live,measured:{...measured,...bad}},now).evidence,'UNAVAILABLE');
  }
});
test('stale observations retain origin time but are excluded from current measured count', () => {
  const stale=row({observed_at:'2026-09-24T11:00:00Z',posture_state:'REPORTED',evidence_state:'MEASURED',measured:{doctrine_state:'LOCKED'}});
  const html=observationHTML({dependencies:[stale]},now,false);
  assert.match(html,/Stale observation/); assert.match(html,/>STALE</); assert.match(html,/0 measured observations/);
  assert.match(html,/2026-09-24T11:00:00Z/);
});
test('observed degraded and blocked bodies remain measured without becoming live', () => {
  for (const posture_state of ['OBSERVED_DEGRADED','BLOCKED']) {
    const dep=row({posture_state,evidence_state:'MEASURED',measured:{state:'DEGRADED',live:false,blocked:posture_state==='BLOCKED',live_count:0,organ_count:1,organs:[{id:'heart',status:'DOWN'}]}});
    assert.equal(observationView(dep,now).evidence,'MEASURED');
    const html=observationHTML({dependencies:[dep]},now,false);
    assert.match(html,/Reported state<\/dt><dd>DEGRADED/);
    assert.doesNotMatch(html,/>LIVE</);
  }
});
test('invalid-input verifier availability is distinct from a verified receipt', () => {
  const verifier=row({id:'a11oy.public-verifier',http_status:400,posture_state:'REPORTED',evidence_state:'MEASURED',measured:{verification_result:'REJECTED_INVALID_INPUT',receipt_verified:false}});
  const html=observationHTML({dependencies:[verifier]},now,false);
  assert.match(html,/No real receipt was verified/); assert.match(html,/Receipt verified<\/dt><dd>false/);
  assert.doesNotMatch(html,/>LIVE</);
});
test('only allowlisted bounded values render; markup is escaped and raw candidate content excluded', () => {
  const candidate=row({id:'<img src=x onerror=alert(1)>',posture_state:'REPORTED',evidence_state:'MEASURED',measured:{doctrine_state:'<script>evil()</script>',private_graph:'SECRET_GRAPH',raw_content:'SECRET_CONTENT'}});
  const html=observationHTML({dependencies:[candidate]},now,false);
  assert.doesNotMatch(html,/<img|<script|SECRET_GRAPH|SECRET_CONTENT/);
  assert.match(html,/&lt;script&gt;/);
});
test('missing and future timestamps do not imply fresh measurements', () => {
  for(const observed_at of [null,'garbage','2026-09-24T13:00:00Z']) {
    assert.equal(observationView(row({observed_at}),now).fresh,false);
  }
});

test('an open observation crosses the freshness boundary without replacing focus or details', () => {
  const dep=row({posture_state:'REPORTED',evidence_state:'MEASURED',measured:{doctrine_state:'LOCKED'}});
  const freshness={textContent:''}, evidence={innerHTML:''}, summary={textContent:''};
  const details={open:true}, focused={id:'origin-summary'};
  const article={details,focused,querySelector(selector){return selector==='.fa-freshness'?freshness:selector==='.fa-evidence-age'?evidence:null;}};
  const host={querySelector(){return summary;},querySelectorAll(){return [article];},
    set innerHTML(value){throw new Error('Clock must not replace the observation DOM');}};
  updateObservationFreshness(host,{dependencies:[dep]},now,false);
  assert.equal(freshness.textContent,'Observed 30s ago');
  assert.match(evidence.innerHTML,/>MEASURED</);
  assert.match(summary.textContent,/1 measured observations within 60s/);
  updateObservationFreshness(host,{dependencies:[dep]},now+31000,false);
  assert.equal(freshness.textContent,'Stale observation');
  assert.match(evidence.innerHTML,/>STALE</);
  assert.match(summary.textContent,/0 measured observations within 60s/);
  assert.equal(article.details,details);assert.equal(details.open,true);
  assert.equal(article.focused,focused);
});

test('malformed typed organ rows cannot crash the panel or become live', () => {
  for(const organ of [null,0,'heart',[],{id:null,status:'LIVE'}]) {
    const dep=row({posture_state:'OBSERVED_LIVE',evidence_state:'LIVE',
      measured:{state:'LIVE',live:true,blocked:false,live_count:1,organ_count:1,organs:[organ]}});
    assert.equal(observationView(dep,now).evidence,'UNAVAILABLE');
    assert.doesNotThrow(()=>observationHTML({dependencies:[dep]},now,false));
  }
});
