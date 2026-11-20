/* Regression tests exercise the shipped adapter and UI functions, not replicas. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const root = process.env.ANATOMY_LIVE_BODY_ROOT || path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "live-body.js"), "utf8");
const html = fs.readFileSync(path.join(root, "live-body.html"), "utf8");
const NOW = Date.parse("2026-11-16T23:00:00Z");
const stamp = (offset = 0) => new Date(NOW + offset).toISOString();
const response = (payload, options = {}) => new Response(JSON.stringify(payload), {
  headers: { "content-type": "application/json" }, ...options,
});
function harness(fetchImpl) {
  class Clock extends Date { static now() { return NOW; } }
  const context = vm.createContext({
    window: {}, document: { readyState: "loading", addEventListener() {}, getElementById() { return null; } },
    fetch: fetchImpl, AbortController, TextDecoder, setTimeout, clearTimeout, Date: Clock,
  });
  vm.runInContext(source.replace(/export default LiveBody;/, "")
    .replace(/export\s*\{[\s\S]*?\};/, ""), context, { filename: "live-body.js" });
  return { api: context.window.LiveBody, integrity: context.window.probeOrganIntegrity, context };
}
const body = (payload) => harness(async () => response(payload));
const ledger = (overrides = {}) => ({
  state: "live", operational: true, data_kind: "live", count: 1,
  observed_at: stamp(), count_scope: "recent nodes returned; not DAG total",
  chain_verified: null, signature_state: "SIGNED",
  receipts: [{ index: 17, digest: "a".repeat(64), schema: "receipt.sign", signed: true }],
  ...overrides,
});
const lambda = (overrides = {}) => ({
  lambda: 0.92, lambda_floor: 0.90, pass: true, trust_axes: 2,
  axes: [{ name: "one", score: 0.92 }, { name: "two", score: 0.92 }],
  uniqueness: "Conjecture 1 OPEN", ...overrides,
});
const integrity = (overrides = {}) => ({
  surface: "szl-organ-integrity", body: {
    state: "LIVE", live: true, blocked: false, live_count: 1, observed_at: stamp(),
    organs: [{ id: "brain", status: "LIVE" }], ...overrides,
  },
});

for (const [name, payload] of [["empty", {}], ["null", null], ["array", []], ["string", "ok"]]) {
  test(name + " JSON never becomes operational evidence", async () => {
    const h = body(payload);
    for (const organ of h.api.ORGANS) assert.notEqual((await h.api.probeOrgan(organ)).status, "live");
    const l = await h.api.fetchLedger();
    assert.equal(l.count, null);
    assert.equal(l.receipts.length, 0);
    assert.equal((await h.api.fetchDoctrine()).lockedCount, null);
    assert.equal((await h.api.fetchMind()).sovereign, null);
    assert.equal((await h.api.fetchImmune()).intensity, null);
  });
}
for (const state of ["UNAVAILABLE", "UNKNOWN", "BLOCKED", "STALE", "TIMEOUT"]) {
  test("explicit " + state + " is not overridden by successful transport", async () => {
    const h = body(ledger({ state }));
    const result = await h.api.fetchLedger();
    assert.equal(result.reachable, false);
    assert.notEqual(result.status, "live");
    assert.equal(result.count, null);
  });
}
test("current bounded ledger preserves source digest and index, not positional identities", async () => {
  const h = body(ledger()), result = await h.api.fetchLedger();
  assert.equal(result.reachable, true);
  assert.equal(result.status, "live");
  assert.equal(result.receipts[0].id, "a".repeat(64));
  assert.equal(result.receipts[0].seq, 17);
  assert.equal(result.chain_verification, "NOT_EVALUATED_BY_THIS_VIEW");
  assert.match(result.count_scope, /not DAG total/);
  assert.equal(h.api.isFreshLive(result), true);
  assert.equal(h.api.isFreshLive(result, NOW + 60000), false);
});
test("valid empty ledger is zero; missing or invalid ledger is unknown", async () => {
  const h = body(ledger({ count: 0, receipts: [] }));
  assert.equal((await h.api.fetchLedger()).count, 0);
  assert.equal((await body(ledger({ count: 1, receipts: [] })).api.fetchLedger()).count, null);
});
test("ledger never invents absent sequence numbers", async () => {
  const result = await body(ledger({ receipts: [{ digest: "b".repeat(64) }] })).api.fetchLedger();
  assert.equal(result.receipts[0].seq, null);
  assert.equal(result.receipts[0].id, "b".repeat(64));
});
test("unknown schema names do not imply an action origin", async () => {
  const h = body(ledger({ receipts: [{ digest: "x", index: 22, schema: "szl.a11oy.policy_decision/v1" }] }));
  assert.equal((await h.api.fetchLedger()).receipts[0].organ, "receipts");
  assert.equal(h.api.organForAction("lambda.score"), "reasoning");
  assert.equal(h.api.organForAction("gate.evaluate"), "policy");
  assert.equal(h.api.organForAction("operator.approve"), "operator");
  assert.equal(h.api.organForAction("not-really-operator.approve"), "receipts");
  assert.equal(h.api.organForAction("constructor"), "receipts");
  assert.equal(h.api.organForAction("__proto__"), "receipts");
  assert.equal(h.api.isDenied("szl.blockchain.receipt/v1"), false);
  assert.equal(h.api.isDenied("rejection-review/v1"), false);
  assert.equal(h.api.isDenied("deny"), true);
});
test("receipt hub has no fabricated policy path and exhausted pools report no pulse", () => {
  const context = vm.createContext({ vessels: new Map([["policy", { curve: {} }]]), pulseCore: [] });
  const start = html.indexOf("function spawnPulse(");
  const end = html.indexOf("/* ============================ HUD", start);
  vm.runInContext(html.slice(start, end), context);
  assert.equal(vm.runInContext('spawnPulse("receipts")', context), false);
  assert.equal(vm.runInContext('spawnPulse("unknown")', context), false);
  assert.equal(vm.runInContext('spawnPulse("policy")', context), false);
});
test("missing, duplicate or malformed receipt identity is rejected", async () => {
  for (const receipts of [[{}], [{ digest: "" }], [{ digest: "x", index: -1 }],
    [{ digest: "x", index: true }], [{ digest: "x" }, { digest: "x" }],
    [{ digest: "x", index: 2 }, { digest: "y", index: 2 }], [null]]) {
    const r = await body(ledger({ receipts, count: receipts.length })).api.fetchLedger();
    assert.equal(r.reachable, false);
    assert.equal(r.count, null);
  }
});
test("stale, future, malformed and missing source timestamps never enable LIVE", async () => {
  for (const observed_at of [stamp(-60001), stamp(1000), "yesterday", undefined]) {
    const h = body(ledger({ observed_at })), r = await h.api.fetchLedger();
    assert.notEqual(r.status, "live");
    assert.equal(h.api.isFreshLive(r), false);
  }
});
test("synthetic and computed source markers never enable LIVE", async () => {
  for (const data_kind of ["synthetic", "sample", "mock", "computed", "SIMULATED", "ADVISORY", "undocumented"])
    assert.notEqual((await body(ledger({ data_kind })).api.fetchLedger()).status, "live");
  assert.notEqual((await body(ledger({ data_kind: "live", evidence_state: "COMPUTED" })).api.fetchLedger()).status, "live");
});
test("contradictory and unrecognized status or evidence markers cannot become green", async () => {
  for (const patch of [{ evidence_state: "DECLARED" }, { status: "FAILED" },
    { status: " UNKNOWN " }, { status: "ERROR" }, { status: "undocumented" }, { ok: false }]) {
    const r = await body(ledger(patch)).api.fetchLedger();
    assert.notEqual(r.status, "live");
  }
});
test("current static Lambda remains visible as a source declaration, with no measured heartbeat", async () => {
  const h = body(lambda()), r = await h.api.fetchLambda();
  assert.equal(r.reachable, true);
  assert.equal(r.lambda, 0.92);
  assert.equal(r.floor, 0.90);
  assert.equal(r.status, "source-reported");
  assert.equal(h.api.isFreshLive(r), false);
  assert.notEqual((await h.api.probeOrgan(h.api.ORGANS[0])).status, "live");
});
test("explicit measured Lambda requires coherent axes, floor and source time", async () => {
  const h = body(lambda({ evidence_state: "MEASURED", observed_at: stamp() }));
  assert.equal(h.api.isFreshLive(await h.api.fetchLambda()), true);
  for (const patch of [{ lambda_floor: undefined }, { pass: false }, { axes: [] },
    { trust_axes: 13 }, { lambda: "0.92" }, { axes: [{ name: "one", score: 1.1 }] }]) {
    const r = await body(lambda(patch)).api.fetchLambda();
    assert.equal(r.reachable, false);
    assert.equal(r.floor, null);
  }
});
test("readiness distinguishes capability failure from a reachable degraded service", async () => {
  for (const patch of [{ status: "ready_degraded" }, { operator: { ready: false, service_ready: true } },
    { operator: { ready: true, service_ready: true, operator_running: false } }]) {
    const h = body({ status: "ready", operator: { ready: true, service_ready: true }, observed_at: stamp(), ...patch });
    assert.notEqual((await h.api.probeOrgan(h.api.ORGANS[2])).status, "live");
  }
  const h = body({ status: "ready", operator: { ready: true, service_ready: true, operator_running: true }, observed_at: stamp() });
  assert.equal((await h.api.probeOrgan(h.api.ORGANS[2])).status, "live");
});
test("nested operator negatives and missing running evidence override positive outer readiness", async () => {
  for (const patch of [{ state: "UNAVAILABLE" }, { state: "UNKNOWN" }, { state: "FAILED" },
    { state: "undocumented" }, { operator_running: undefined }, { observed_at: stamp(-60001) }]) {
    const h = body({ status: "ready", observed_at: stamp(),
      operator: { ready: true, service_ready: true, operator_running: true, ...patch } });
    assert.notEqual((await h.api.probeOrgan(h.api.ORGANS[2])).status, "live");
  }
});
test("a declared policy lock is not enforcement telemetry", async () => {
  const h = body({ doctrine_lock: { locked_formula_count: 1, locked_formula_ids: ["F12"], state: "LOCKED" }, observed_at: stamp() });
  assert.equal((await h.api.fetchDoctrine()).lockedCount, 1);
  assert.equal((await h.api.probeOrgan(h.api.ORGANS[1])).status, "source-reported");
  assert.equal((await body({ doctrine_lock: { locked_formula_count: 8, locked_formula_ids: [] } }).api.fetchDoctrine()).reachable, false);
});
test("mesh denominator and counts must be evidenced, including individual engine state", async () => {
  for (const payload of [{ engines_total: 0, engines_live: 0, mesh: [] },
    { engines_total: 2, engines_live: 2, mesh: [{ name: "x", live: true }] },
    { engines_total: 1, engines_live: 1, mesh: [{ name: "x", live: false }] }])
    assert.equal((await body(payload).api.fetchImmune()).intensity, null);
  const r = await body({ engines_total: 2, engines_live: 1, mesh: [{ name: "x", live: true }, { name: "y", live: false }], observed_at: stamp() }).api.fetchImmune();
  assert.equal(r.intensity, 0.5);
  assert.equal(r.status, "degraded");
});
test("integrity preserves blocked, unknown and computed advisory results without healthy fallback", async () => {
  for (const patch of [
    { state: "BLOCKED", blocked: true, live: false },
    { state: "UNKNOWN", live: false, live_count: null, organs: [] },
    { state: undefined, verdict: "ADVISORY_BODY", live: undefined },
    { observed_at: stamp(-60001) },
  ]) {
    let calls = 0;
    const h = harness(async () => { calls++; return response(integrity(patch)); });
    const r = await h.integrity();
    assert.equal(calls, 1);
    assert.notEqual(r.status, "live");
  }
});
test("integrity accepts a fresh positive observation and rejects duplicate organs", async () => {
  assert.equal((await body(integrity()).integrity()).status, "live");
  const h = body(integrity({ live_count: 2, organs: [{ id: "x", status: "LIVE" }, { id: "x", status: "LIVE" }] }));
  assert.notEqual((await h.integrity()).status, "live");
});
test("integrity wrapper negatives take precedence over a positive inner body", async () => {
  for (const patch of [{ state: "UNAVAILABLE" }, { blocked: true }, { status: " FAILED " },
    { evidence_state: "COMPUTED" }, { data_kind: "SIMULATED" }, { ok: false }]) {
    let calls = 0;
    const h = harness(async () => { calls++; return response({ ...integrity(), ...patch }); });
    assert.notEqual((await h.integrity()).status, "live");
    assert.equal(calls, 1);
  }
});
test("integrity display expires without another request and refresh can restore it", async () => {
  const h = body(integrity());
  const el = { dataset: {}, textContent: "" };
  h.context.document.getElementById = () => el;
  await h.integrity();
  assert.equal(el.dataset.state, "live");
  h.api.refreshIntegrityView(NOW + 60001);
  assert.equal(el.dataset.state, "stale");
  assert.match(el.textContent, /refresh required/);
  await h.integrity();
  assert.equal(el.dataset.state, "live");
});
test("HTTP failures, HTML, malformed JSON and oversized responses stay unavailable", async () => {
  for (const make of [
    () => new Response("no", { status: 503 }),
    () => new Response("<html>OK</html>", { headers: { "content-type": "text/html" } }),
    () => new Response("{", { headers: { "content-type": "application/json" } }),
    () => response({ pad: "x".repeat(65537) }),
  ]) {
    const r = await harness(async () => make()).api.fetchLedger();
    assert.equal(r.reachable, false);
    assert.equal(r.count, null);
  }
});
test("deadline covers a response body that stalls after headers", async () => {
  const h = harness(async () => new Response(new ReadableStream({ start() {} }), {
    headers: { "content-type": "application/json" },
  }));
  let guard;
  const r = await Promise.race([
    h.api.fetchLedger(10),
    new Promise((resolve) => { guard = setTimeout(() => resolve({ test_guard: true }), 200); }),
  ]);
  clearTimeout(guard);
  assert.equal(r.test_guard, undefined, "adapter must finish without external watchdog");
  assert.equal(r.reachable, false);
  assert.equal(r.why, "timeout");
});
test("integrity fallback probes are bounded and never convert timeout into LIVE", async () => {
  const h = harness(() => new Promise(() => {}));
  let guard;
  const r = await Promise.race([
    h.integrity(10),
    new Promise((resolve) => { guard = setTimeout(() => resolve({ test_guard: true }), 250); }),
  ]);
  clearTimeout(guard);
  assert.equal(r.test_guard, undefined);
  assert.notEqual(r.status, "live");
});
function uiHarness(api) {
  const elements = new Map();
  const $ = (id) => {
    if (!elements.has(id)) elements.set(id, { textContent: "", className: "" });
    return elements.get(id);
  };
  const context = vm.createContext({ LiveBody: api, $, Date });
  const start = html.indexOf("const STATE = ");
  const end = html.indexOf("let seenIds", start);
  vm.runInContext(html.slice(start, end) + "\nglobalThis.state = STATE;", context);
  const fnStart = html.indexOf("async function refreshLambda()");
  const fnEnd = html.indexOf("async function refreshDoctrine()", fnStart);
  vm.runInContext(html.slice(fnStart, fnEnd) + "\nglobalThis.refresh = refreshLambda;", context);
  return { context, elements, $ };
}
test("UI begins without synthetic Lambda and clears a previously measured value on failure", async () => {
  let result = await body(lambda({ evidence_state: "MEASURED", observed_at: stamp() })).api.fetchLambda();
  const api = body({}).api;
  const ui = uiHarness({ ...api, fetchLambda: async () => result });
  assert.equal(ui.context.state.lambda, null);
  assert.equal(ui.context.state.lambdaPass, null);
  await ui.context.refresh();
  assert.equal(ui.context.state.lambda, 0.92);
  result = { reachable: false, status: "unavailable", why: "source unavailable" };
  await ui.context.refresh();
  assert.equal(ui.context.state.lambda, null);
  assert.equal(ui.context.state.lambdaPass, null);
  assert.match(ui.$("lambda-val").textContent, /unavailable/);
});
test("UI shows static Lambda as a declaration while its heartbeat stays disabled", async () => {
  const h = body(lambda()), result = await h.api.fetchLambda();
  const ui = uiHarness({ ...h.api, fetchLambda: async () => result });
  await ui.context.refresh();
  assert.equal(ui.context.state.lambda, null);
  assert.match(ui.$("lambda-val").textContent, /0.92000/);
  assert.match(ui.$("lambda-meta").textContent, /source-reported/);
});

/* Pass-2 consumer proof: exercise the exact shipped WebGL admission function. */
function rendererHarness(Three, ratio = 3) {
  const target = { hidden: false };
  const status = { hidden: true, textContent: "" };
  const context = vm.createContext({
    THREE: Three, target, status, window: { devicePixelRatio: ratio },
    K: { void: "#080c14" },
  });
  const start = html.indexOf("function initializeRenderer(");
  const end = html.indexOf("const renderer = initializeRenderer(", start);
  assert.ok(start > 0 && end > start, "shipped renderer initializer must exist");
  vm.runInContext(html.slice(start, end) +
    "\nglobalThis.result = initializeRenderer(THREE, target, status);", context);
  return { target, status, renderer: context.result };
}
test("WebGL denied leaves an explicit read-only accessible fallback", () => {
  const Three = { WebGLRenderer: class { constructor() { throw new Error("context denied"); } } };
  const r = rendererHarness(Three);
  assert.equal(r.renderer, null);
  assert.equal(r.target.hidden, true);
  assert.equal(r.status.hidden, false);
  assert.match(r.status.textContent, /WebGL unavailable/);
  assert.match(r.status.textContent, /no 3D frame/);
  assert.match(html, /id="renderer-fallback" role="status" aria-live="polite" hidden/);
  assert.match(html, /#scene\[hidden\]\{display:none\}/);
  assert.match(html, /if \(!renderer\) \$\("boot"\)\.style\.display = "none"/);
  assert.match(html, /if \(renderer\) renderer\.render\(scene, camera\)/);
  assert.match(html, /if \(renderer\) renderer\.setSize\(w, h, false\)/);
  assert.match(html, /else setTimeout\(\(\) => animate\(performance\.now\(\)\), 1000\)/);
});
test("a valid WebGL renderer does not display the fallback", () => {
  class GoodRenderer {
    constructor(opts) { this.opts = opts; }
    setPixelRatio(value) { this.ratio = value; }
    setClearColor(color, alpha) { this.alpha = alpha; }
  }
  const r = rendererHarness({ WebGLRenderer: GoodRenderer, Color: class {} });
  assert.ok(r.renderer instanceof GoodRenderer);
  assert.equal(r.renderer.opts.canvas, r.target);
  assert.equal(r.renderer.ratio, 2);
  assert.equal(r.renderer.alpha, 1);
  assert.equal(r.target.hidden, false);
  assert.equal(r.status.hidden, true);
});
test("missing renderer constructor fails closed rather than claiming a 3D frame", () => {
  const r = rendererHarness({});
  assert.equal(r.renderer, null);
  assert.equal(r.target.hidden, true);
  assert.equal(r.status.hidden, false);
});
