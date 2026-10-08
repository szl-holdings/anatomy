// SPDX-License-Identifier: Apache-2.0
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'neural-quant-v7.js'), 'utf8');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.value = ''; }
  set textContent(value) { this.value = String(value); this.children = []; }
  get textContent() { return this.value + this.children.map(child => child.textContent).join(' '); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.value = ''; this.children = children; }
  setAttribute(key, value) { this.attributes[key] = value; }
}

function harness() {
  const sections = Object.fromEntries(['pipeline', 'ouroboros'].map(name => [`nq7-section-${name}`, new Element('section')]));
  let now = Date.parse('2026-10-08T23:00:00Z');
  class Clock extends Date { static now() { return now; } }
  const context = {
    document: {getElementById: id => sections[id] || null, createElement: tag => new Element(tag)},
    Date: Clock,
    fetch() { throw new Error('rendering must not perform a request'); },
  };
  // Expose the real isolated renderers without mounting the unrelated atlas.
  const marker = '  const init = () => {';
  assert.equal(source.split(marker).length, 2);
  vm.runInNewContext(source.replace(marker,
    '  globalThis.renderers = {renderPipeline, renderOuroboros}; return;\n' + marker), context);
  return {sections, renderers: context.renderers, advance: value => { now += value; }};
}

function fixture() {
  return {
    ouroboros: {loop_contract: {bounded: true, terminating: true, receipt_closed: true, codex_role: 'ADVISORY_REVIEW_ONLY'},
      runtime_evidence: {state: 'OBSERVED'}, handles: []},
    pipeline: {source_revision: 'a'.repeat(40), rag: {chunk_count: 575}, upstream: {
      state: 'OBSERVED', reason: 'CURRENT_REVIEW_RECEIPT_VALIDATED', source: {revision: 'b'.repeat(40)},
      ouroboros_observation: {state: 'OBSERVED', freshness: {expires_at: '2026-10-08T23:00:01Z'}},
      dag: {state: 'MODELED_PLAN_ONLY', contract_digest: 'c'.repeat(64), nodes: [
        {id: 'OBSERVE', label: 'Observe public inputs', depends_on: [], control_after: []},
        {id: 'HOLD', label: 'Hold for admission', depends_on: ['OBSERVE'], control_after: []},
      ]},
    }},
  };
}

function allElements(node) { return [node, ...node.children.flatMap(allElements)]; }

test('actual renderers show the source-bound pipeline and expose no execution control', () => {
  const {sections, renderers} = harness();
  const payload = fixture();
  renderers.renderPipeline(payload);
  renderers.renderOuroboros(payload);
  const pipeline = sections['nq7-section-pipeline'];
  assert.match(pipeline.textContent, /575/);
  assert.match(pipeline.textContent, /PLAN ONLY/);
  assert.match(pipeline.textContent, /Hold for admission/);
  assert.match(pipeline.textContent, /Requires: OBSERVE/);
  assert.equal(allElements(pipeline).filter(node => ['button', 'input', 'form'].includes(node.tag)).length, 0);
  const loop = sections['nq7-section-ouroboros'];
  assert.equal(allElements(loop).filter(node => node.className === 'nq7-card-value' && node.textContent === 'YES').length, 3);
});

test('consumer-clock expiry removes successful loop values even if the cached API payload is unchanged', () => {
  const {sections, renderers, advance} = harness();
  const payload = fixture();
  advance(1001);
  renderers.renderPipeline(payload);
  renderers.renderOuroboros(payload);
  assert.match(sections['nq7-section-pipeline'].textContent, /STALE/);
  assert.match(sections['nq7-section-pipeline'].textContent, /OBSERVATION_EXPIRED/);
  const loop = allElements(sections['nq7-section-ouroboros']);
  assert.equal(loop.filter(node => node.className === 'nq7-card-value' && node.textContent === 'UNKNOWN').length, 3);
  assert.equal(loop.filter(node => node.className === 'nq7-card-value' && node.textContent === 'YES').length, 0);
  assert.equal(payload.pipeline.upstream.ouroboros_observation.state, 'OBSERVED', 'preserve the recorded receipt body');
});

test('unavailable metadata cannot create green loop values and labels remain text', () => {
  const {sections, renderers} = harness();
  const payload = fixture();
  payload.ouroboros.runtime_evidence.state = 'UNAVAILABLE';
  payload.pipeline.upstream.dag.nodes[0].label = '<img src=x onerror=execute()>';
  renderers.renderPipeline(payload);
  renderers.renderOuroboros(payload);
  assert.match(sections['nq7-section-pipeline'].textContent, /<img src=x onerror=execute\(\)>/);
  assert.equal(allElements(sections['nq7-section-pipeline']).some(node => node.tag === 'img'), false);
  assert.equal(allElements(sections['nq7-section-ouroboros']).filter(node => node.className === 'nq7-card-value' && node.textContent === 'UNKNOWN').length, 3);
});
