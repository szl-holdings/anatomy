// QA — Covenant Cockpit v1 (headless, no browser needed).
// Loads the REAL covenant-cockpit.js pure logic + the bundled receipts.sample.json
// and asserts the honest invariants that back the cockpit:
//   1. receipts normalize from the szl-receipt in-toto bundle (no fabricated nodes)
//   2. the provenance graph binds every decision -> Λ-gate + Lean proof + energy + BFT witnesses
//   3. the verify badge is GENUINE: signed -> verified, unsigned -> UNAVAILABLE, tamper -> failed
//   4. energy is measured joules OR honest UNAVAILABLE (never fabricated)
//   5. empty input -> honest empty graph (zero nodes), never a decorative fallback
//
// Run:  node qa_cockpit.mjs
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));

// covenant-cockpit.js is a browser ES module (export default). Load its pure
// logic here by stripping the two `export` lines and evaluating (it has NO
// top-level `import`, and guards all `window` use), then grabbing the object.
async function loadModule() {
  // covenant-cockpit.js is a valid browser ES module (export default + guarded
  // `window`). Load it in node by copying to a temp .mjs and importing it — no
  // fragile source-stripping, and the real module code is exercised verbatim.
  const src = fs.readFileSync(path.join(ROOT, "covenant-cockpit.js"), "utf8");
  const tmp = path.join(os.tmpdir(), `cc-qa-${process.pid}.mjs`);
  fs.writeFileSync(tmp, src);
  try {
    const mod = await import(pathToFileURL(tmp).href);
    return mod.default;
  } finally {
    try { fs.unlinkSync(tmp); } catch { /* best-effort cleanup */ }
  }
}

let failures = 0;
function ok(cond, msg) {
  console.log((cond ? "  ✓ " : "  ✗ ") + msg);
  if (!cond) failures++;
}
function section(t) { console.log("\n== " + t + " =="); }

const bundle = JSON.parse(fs.readFileSync(path.join(ROOT, "receipts.sample.json"), "utf8"));

(async () => {
  const CC = await loadModule();
  section("normalize the szl-receipt in-toto bundle");
  const { receipts, cosignPub } = CC.normalizeBundle(bundle);
  ok(receipts.length === 4, `normalizes 4 receipts (got ${receipts.length})`);
  ok(!!cosignPub && /BEGIN PUBLIC KEY/.test(cosignPub), "cosign public key present for offline verify");
  ok(receipts.every((r) => r.body && r.body.model_id && r.body.policy_id && r.body.lean_theorem),
     "every receipt decodes model_id + policy_id + lean_theorem");

  section("build the provenance graph (pure)");
  const g = CC.buildGraph(receipts);
  ok(g.stats.decisions === 4, `4 decision nodes (got ${g.stats.decisions})`);
  ok(g.stats.gates >= 1, `≥1 Λ-gate node (got ${g.stats.gates})`);
  ok(g.stats.proofs >= 1, `≥1 Lean proof node (got ${g.stats.proofs})`);
  ok(g.stats.witnesses >= 1, `≥1 BFT witness node (got ${g.stats.witnesses})`);
  ok(g.edges.length > 0, `edges present (got ${g.edges.length})`);
  // every decision must bind to a gate, a proof, an energy node, and >=1 witness
  const decNodes = g.nodes.filter((n) => n.kind === "decision");
  const edgesFrom = (id, kind) => g.edges.filter((e) => e.from === id && kindOf(g, e.to) === kind);
  const kindOf = (gr, id) => (gr.nodes.find((n) => n.id === id) || {}).kind;
  let bound = true;
  for (const d of decNodes) {
    const hasGate = edgesFrom(d.id, "gate").length >= 1;
    const hasProof = edgesFrom(d.id, "proof").length >= 1;
    const hasEnergy = edgesFrom(d.id, "energy").length >= 1;
    const hasWitness = edgesFrom(d.id, "cosigned" /*ignored*/) ; // recompute below
    const wit = g.edges.filter((e) => e.from === d.id && kindOf(g, e.to) === "witness").length;
    if (!(hasGate && hasProof && hasEnergy && wit >= 1)) bound = false;
  }
  ok(bound, "every decision binds → Λ-gate + Lean proof + energy + ≥1 BFT witness");
  ok(g.nodes.every((n) => Array.isArray(n.pos) && n.pos.length === 3 && n.pos.every(Number.isFinite)),
     "every node has a finite 3D position (renderable)");

  section("energy is measured joules OR honest UNAVAILABLE");
  ok(g.stats.energyMeasured === 2 && g.stats.energyUnavailable === 2,
     `2 measured / 2 UNAVAILABLE energy nodes (got ${g.stats.energyMeasured}/${g.stats.energyUnavailable})`);
  const eNodes = g.nodes.filter((n) => n.kind === "energy");
  ok(eNodes.every((n) => n.meta.measured ? typeof n.meta.joules === "number" : n.meta.joules === null),
     "measured energy carries a real joule value; unavailable carries null (never fabricated)");

  section("verify badge is GENUINE (WebCrypto ECDSA-P256 over DSSE PAE)");
  const key = await CC.importCosign(cosignPub);
  const results = [];
  for (const r of receipts) results.push(await CC.verifyEnvelope(r.envelope, key));
  const verified = results.filter((v) => v.status === CC.VERIFY.VERIFIED).length;
  const unavail = results.filter((v) => v.status === CC.VERIFY.UNAVAILABLE).length;
  ok(verified === 3, `3 signed receipts VERIFY (got ${verified})`);
  ok(unavail === 1, `1 unsigned receipt is honest UNAVAILABLE (got ${unavail})`);

  // tamper: flip the verdict on a signed receipt -> must FAIL (never a fake pass)
  const signedIdx = receipts.findIndex((r) => r.envelope.signed === true);
  const t = JSON.parse(JSON.stringify(receipts[signedIdx].envelope));
  const body = JSON.parse(Buffer.from(t.payload, "base64").toString("utf8"));
  body.verdict = body.verdict === "allow" ? "block" : "allow";
  const keys = Object.keys(body).sort();
  const canon = JSON.stringify(body, keys);
  t.payload = Buffer.from(canon, "utf8").toString("base64");
  const vt = await CC.verifyEnvelope(t, key);
  ok(vt.status === CC.VERIFY.FAILED, `tampered receipt FAILS verify (got ${vt.status})`);

  section("honest empty state — never fabricate nodes");
  const empty = CC.buildGraph([]);
  ok(empty.nodes.length === 0 && empty.edges.length === 0, "empty input → zero nodes, zero edges");
  const bad = CC.normalizeBundle({ receipts: [{ id: "x" }, { junk: true }] });
  ok(bad.receipts.length === 0, "entries without a payload are skipped, not turned into fake nodes");

  console.log("\n=== TOTAL FAILURES:", failures, "===");
  process.exit(failures === 0 ? 0 : 1);
})().catch((e) => { console.error("QA FAIL", e); process.exit(1); });
