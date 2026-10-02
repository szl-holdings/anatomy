'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'source-verification.js'), 'utf8');
async function render(payload, ok = true) {
  const elements = Object.fromEntries(['fw-source', 'fw-rev', 'fw-source-command'].map(id => [id, {
    textContent: '', removeAttribute(name) { delete this[name]; }
  }]));
  vm.runInNewContext(script, {
    document: {getElementById: id => elements[id]},
    fetch: async (url, options) => {
      assert.equal(url, '/.well-known/szl-source.json');
      assert.equal(options.cache, 'no-store');
      return {ok, json: async () => payload};
    }
  });
  await new Promise(resolve => setImmediate(resolve));
  return elements;
}
const good = {alignment_state: 'SOURCE_BOUND_LOCAL_BYTES', source: {
  repository: 'szl-holdings/anatomy', path: 'spaces/cosmos', commit: 'a'.repeat(40)
}};
test('verification uses the same-origin endpoint and immutable canonical commit', async () => {
  const nodes = await render(good);
  assert.equal(nodes['fw-source'].href, 'https://github.com/szl-holdings/anatomy/tree/' + 'a'.repeat(40) + '/spaces/cosmos');
  assert.match(nodes['fw-source-command'].textContent, /anatomy\/a{40}\/spaces\/cosmos\/index.html/);
});
test('unknown, malformed, wrong identity and failed responses never expose a source link', async () => {
  for (const [payload, ok] of [[null, true], [{}, true], [{...good, alignment_state:'UNKNOWN_SOURCE_RELATION'}, true],
    [{...good, source:{...good.source, repository:'untrusted/other'}}, true],
    [{...good, source:{...good.source, commit:'main'}}, true], [good, false]]) {
    const nodes = await render(payload, ok);
    assert.equal(nodes['fw-source'].href, undefined);
    assert.equal(nodes['fw-source'].textContent, 'UNKNOWN_SOURCE_RELATION');
  }
});
test('social image metadata points to a published asset', () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  for (const tag of ['og:image', 'twitter:image']) {
    const match = html.match(new RegExp('(?:property|name)="' + tag + '" content="https://betterwithage-cosmos.hf.space/([^"]+)"'));
    assert.ok(match);
    assert.ok(fs.statSync(path.join(root, match[1])).isFile());
  }
  assert.ok(html.includes('src="./source-verification.js"'));
});
