'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)]
  .map(match => match[1]).find(source => source.includes("dock.id = 'anatomy-instruments'"));

test('Anatomy opts out of injected navigation while retaining its native controls', () => {
  assert.match(html, /<html[^>]*\bdata-szl-holo-no-rail[\s>]/);
  for (const id of ['ux-toolbar', 'ux-tabbar', 'ux-more-menu']) {
    assert.match(html, new RegExp('id="' + id + '"'));
  }
});

for (const missing of [null, 'nq7-launcher']) {
  test(`dock moves existing controls without replacing behavior (${missing || 'all available'})`, () => {
    let start;
    let clicks = 0;
    const ids = ['fa-launch', 'nq7-launcher', 'szl-v7-launcher', 'yachay-sb'];
    const originals = Object.fromEntries(ids.filter(id => id !== missing)
      .map(id => [id, { id, click: () => clicks++ }]));
    const body = [];
    vm.runInNewContext(script, {
      window: { addEventListener(event, callback, options) {
        assert.equal(event, 'load'); assert.equal(options.once, true); start = callback;
      } },
      document: {
        getElementById: id => originals[id] || null,
        createElement: () => ({ children: [], setAttribute() {}, appendChild(node) { this.children.push(node); } }),
        body: { appendChild: node => body.push(node) }
      }
    });
    assert.equal(body.length, 0, 'wait until deferred instruments are mounted');
    start();
    assert.equal(body.length, 1);
    assert.deepEqual(body[0].children, Object.values(originals));
    for (const control of body[0].children) control.click();
    assert.equal(clicks, Object.keys(originals).length);
  });
}

test('verifier actions retain offline verification and do not revive the retired Space', () => {
  const ui = fs.readFileSync(path.join(root, 'frontier_anatomy.js'), 'utf8');
  const server = fs.readFileSync(path.join(root, 'server.py'), 'utf8');
  assert.match(ui, /href="https:\/\/a-11-oy.com\/verify"[^>]*>Public receipt verifier/);
  assert.match(ui, /href="https:\/\/github.com\/szl-holdings\/governed-receipt-spec"[^>]*>Independent offline verifier/);
  assert.doesNotMatch(server, /"id": "receipt-verifier.space"/);
  assert.doesNotMatch(server, /https:\/\/szlholdings-governed-receipt-verifier.static.hf.space\//);
});
