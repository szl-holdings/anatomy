/* =============================================================================
 * live-body.js — SZL Living Anatomy · BODY v1 ENGINE (the living face)
 * =============================================================================
 * The Sovereign Org rendered as ONE living governed organism. This module is the
 * HONEST DATA SPINE for live-body.html's Three.js scene. It reads the SAME live
 * a11oy endpoints the unified console reads and exposes them as honest records.
 *
 * CRITICAL DISCIPLINE (binding — honest by construction, never a screensaver):
 *   - Every pulse travelling a vessel refers to a source-identified node in the
 *     bounded ledger response. This view does not verify signatures or the chain.
 *   - Transport success is not operational evidence. LIVE requires a validated,
 *     explicitly positive observation with a fresh source timestamp.
 *   - sovereign:true is shown ONLY when /code/healthz reports the literal true.
 *   - Λ is advisory and its uniqueness is Conjecture 1 — pulled live from
 *     /v1/lambda + /v1/honest, never hardcoded as proven.
 *   - Verticals (insurance/defense/finance/realestate), SLSA skeletal integrity,
 *     and drift have NO live endpoint on this Space today, so they render in an
 *     explicit ROADMAP / N-A state — limbs do NOT fake-pulse and the skeleton does
 *     NOT claim a verified SLSA level. Honest absence over decorative motion.
 *   - Read-only. No key is sent. open-weight only.
 *
 * No build step, no framework, no CDN — a plain ES module that runs as a static
 * SDK page at the .static.hf.space URL, exactly like index.html.
 * ============================================================================ */
"use strict";

/* ---- the upstream host; reachability and evidence are checked separately --- */
const HOST = "https://szlholdings-a11oy.hf.space";

/* Read-only endpoint contracts (not a claim about current runtime health):
 *   /api/a11oy/v1/ledger      -> bounded recent nodes, not a whole-chain count
 *   /api/a11oy/v1/lambda      -> {trust_axes,axes[],lambda,lambda_floor,pass,uniqueness}
 *   /api/a11oy/code/healthz   -> {sovereign,backend,mode,doctrine_state,...}
 *   /api/a11oy/v1/honest      -> {doctrine_lock:{lambda,locked_formula_ids,...}}
 *   /api/a11oy/readyz         -> {status,operator:{operator_running,...}}
 *   /api/a11oy/v1/govern/health-> {engines_live,engines_total,mesh[]}            */
const EP = {
  ledger:  HOST + "/api/a11oy/v1/ledger",
  lambda:  HOST + "/api/a11oy/v1/lambda",
  healthz: HOST + "/api/a11oy/code/healthz",
  honest:  HOST + "/api/a11oy/v1/honest",
  readyz:  HOST + "/api/a11oy/readyz",
  govern:  HOST + "/api/a11oy/v1/govern/health",
  integrity: HOST + "/api/a11oy/v1/organs/integrity",
};

/* ---- KANCHAY palette (canonical brand · purple BANNED) -------------------- */
const KANCHAY = {
  void:    "#080c14",
  proof:   "#3af4c8",   // teal — proven / live
  lattice: "#5b8dee",   // blue — structure / vessels
  gold:    "#d7b96b",   // gold — Λ / heartbeat accent
  warn:    "#e0795b",   // ember — denied / down
  dim:     "#3a4456",   // honest unreachable / dormant
  text:    "#e9eef7",
};

/* ---- status vocabulary ---------------------------------------------------- */
const STATUS = {
  LIVE: "live",              // validated positive observation with fresh source time
  REPORTED: "source-reported", // valid declaration; no fresh operational evidence
  UNKNOWN: "unknown",
  UNAVAILABLE: "unavailable",
  BLOCKED: "blocked",
  DEGRADED: "degraded",
  STALE: "stale",
  UNREACHABLE: "unreachable", // network / non-2xx / not-JSON — honest unknown
  PENDING: "pending",         // not yet polled
};

/* ---- the 4 console organs, each a REAL probe ------------------------------ *
 * These are the organs the unified console shows (Reasoning/Policy/Operator/
 * Receipts). Each maps to an endpoint whose schema and evidence are checked.
 * Valid declarations remain source-reported. `pos` is a normalized
 * body-space anchor [x,y,z] the scene uses to place the organ. */
const ORGANS = [
  {
    id: "reasoning", name: "REASONING", glyph: "✸", color: KANCHAY.proof,
    pos: [0, 1.15, 0],
    probe: "lambda",
    role: "scores Λ (13-axis) + recommends the decision under uncertainty",
    actions: ["lambda.score", "decision.recommend"],
    summarize: (j) => {
      if (typeof j.lambda === "number")
        return `Λ ${j.lambda.toFixed(5)} ${j.pass ? "≥" : "<"} floor ${j.lambda_floor} · ${j.trust_axes || (j.axes||[]).length}-axis`;
      return "reasoning responding";
    },
  },
  {
    id: "policy", name: "POLICY", glyph: "⛨", color: KANCHAY.gold,
    pos: [-1.15, 0.15, 0.1],
    probe: "honest",
    role: "the deny-by-default gate (F12) — rejects unsafe / overclaiming work",
    actions: ["gate.evaluate"],
    summarize: (j) => {
      const lk = j.doctrine_lock || {};
      const ids = lk.locked_formula_ids || [];
      const f12 = ids.includes("F12");
      return `${lk.locked_formula_count ?? ids.length} declared locked · F12 ${f12 ? "listed" : "not listed"}`;
    },
  },
  {
    id: "operator", name: "OPERATOR", glyph: "⌁", color: KANCHAY.lattice,
    pos: [1.15, 0.15, 0.1],
    probe: "readyz",
    role: "approves + executes admitted work; the hands of the organism",
    actions: ["operator.approve"],
    summarize: (j) => {
      const op = j.operator || {};
      if (op.operator_running === true) return `operator running · ${j.status || "ready"}`;
      if (j.status) return `status: ${j.status}`;
      return "operator responding";
    },
  },
  {
    id: "receipts", name: "RECEIPTS", glyph: "❤", color: KANCHAY.warn,
    pos: [0, -1.15, 0],
    probe: "ledger",
    role: "signs + replays a verifiable receipt for every action (the heartbeat)",
    actions: ["receipt.sign", "replay.verify"],
    summarize: (j) => {
      const rs = j.receipts || j.items || (Array.isArray(j) ? j : null);
      const n = Array.isArray(rs) ? rs.length : (typeof j.count === "number" ? j.count : null);
      return n != null ? `${n} recent nodes returned · chain verification not evaluated` : "receipt evidence unavailable";
    },
  },
];

/* Schematic routes for explicit known action names. Unknown schemas/actions
 * remain at the receipt hub; substring matches do not establish an origin. */
const ACTION_SOURCE = {
  "gate.evaluate": "policy",
  "lambda.score": "reasoning",
  "decision.recommend": "reasoning",
  "operator.approve": "operator",
  "receipt.sign": "receipts",
  "replay.verify": "receipts",
};
function organForAction(action) {
  if (!action) return "receipts";
  const a = String(action).toLowerCase();
  if (Object.hasOwn(ACTION_SOURCE, a)) return ACTION_SOURCE[a];
  return "receipts";
}
/* An action is a DENIAL (rejected pulse) only when it honestly says so. */
function isDenied(action) {
  const a = String(action || "").trim().toLowerCase();
  // A schema containing "blockchain" or "rejection" is not a denial outcome.
  return ["deny", "denied", "reject", "rejected", "block", "blocked"].includes(a);
}

/* The 4 verticals = limbs. NO live throughput endpoint exists on this Space, so
 * they render in an honest ROADMAP state and only pulse if a real receipt with a
 * "<vertical>|<action>" verb appears on the chain. Never fake-pulsed. */
const VERTICALS = [
  { id: "insurance",  name: "INSURANCE",  pos: [-1.7, -0.7, 0.0], color: KANCHAY.proof },
  { id: "defense",    name: "DEFENSE",    pos: [ 1.7, -0.7, 0.0], color: KANCHAY.lattice },
  { id: "finance",    name: "FINANCE",    pos: [-1.7,  0.9, 0.0], color: KANCHAY.gold },
  { id: "realestate", name: "REALESTATE", pos: [ 1.7,  0.9, 0.0], color: KANCHAY.warn },
];

/* ---- bounded, read-only observations ------------------------------------- */
const MAX_AGE_MS = 60000;
const MAX_JSON_BYTES = 65536;
const isObject = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const textValue = (v) => typeof v === "string" && v.trim().length > 0;
const countValue = (v) => Number.isSafeInteger(v) && v >= 0;
const unitValue = (v) => typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= 1;

function negativeState(j) {
  const states = [j.state, j.status, j.evidence_state, j.verdict]
    .filter(textValue).map((x) => x.trim().toUpperCase());
  if (j.blocked === true || states.includes("BLOCKED")) return STATUS.BLOCKED;
  if (j.operational === false || j.ok === false || states.some((s) =>
      ["UNAVAILABLE", "DOWN", "NOT_READY", "TIMEOUT", "FAILED", "FAIL", "ERROR"].includes(s))) return STATUS.UNAVAILABLE;
  if (states.includes("STALE")) return STATUS.STALE;
  if (states.some((s) => ["DEGRADED", "READY_DEGRADED"].includes(s))) return STATUS.DEGRADED;
  if (states.some((s) => ["UNKNOWN", "UNVERIFIED", "NOT_EVALUATED", "PENDING"].includes(s))) return STATUS.UNKNOWN;
  return null;
}

function observation(j, positive = false) {
  const denied = negativeState(j);
  const at = j.observed_at ?? j.measured_at;
  const parsed = typeof at === "string" && /^\d{4}-\d\d-\d\dT.*(?:Z|[+-]\d\d:\d\d)$/.test(at)
    ? Date.parse(at) : NaN;
  const age = Date.now() - parsed;
  // Positive evidence uses an allowlist. A new or contradictory marker cannot
  // silently become green until its semantics have been explicitly supported.
  const positiveStates = ["LIVE", "READY", "MEASURED", "OK"];
  const sourceStates = [j.state, j.status, j.evidence_state, j.verdict].filter((s) => s !== undefined);
  const positiveMarkers = sourceStates.every((s) => textValue(s) && positiveStates.includes(s.trim().toUpperCase())) &&
    (j.data_kind === undefined || (textValue(j.data_kind) && ["LIVE", "MEASURED"].includes(j.data_kind.trim().toUpperCase())));
  let status = denied || STATUS.REPORTED;
  if (!denied && at !== undefined && (!Number.isFinite(parsed) || age < 0)) status = STATUS.UNKNOWN;
  else if (!denied && Number.isFinite(parsed) && age > MAX_AGE_MS) status = STATUS.STALE;
  else if (!denied && positive && positiveMarkers && Number.isFinite(parsed)) status = STATUS.LIVE;
  return {
    status,
    source_observed_at: Number.isFinite(parsed) ? at : null,
    fresh_until: Number.isFinite(parsed) ? parsed + MAX_AGE_MS : null,
  };
}

function unavailable(why, status = STATUS.UNAVAILABLE) {
  return { reachable: false, status, why, raw: null, fresh_until: null };
}

/* The deadline covers headers AND body consumption. JSON shape is checked by
 * the endpoint adapter, and an oversized or stalled body cannot hang refresh. */
async function getJSON(url, timeoutMs = 9000) {
  const ctl = new AbortController();
  let timer;
  const deadline = new Promise((_, reject) => {
    timer = setTimeout(() => { ctl.abort(); reject(new Error("timeout")); }, timeoutMs);
  });
  try {
    return await Promise.race([deadline, (async () => {
      const res = await fetch(url, {
        method: "GET", mode: url.startsWith("/") ? "same-origin" : "cors",
        credentials: "omit", signal: ctl.signal, cache: "no-store",
      });
      if (!res.ok) return { ok: false, why: "HTTP " + res.status };
      if (!/\b(?:application\/json|[^;\s]+\/[^;\s]+\+json)\b/i.test(res.headers.get("content-type") || ""))
        return { ok: false, why: "no JSON (route unmatched?)" };
      const reader = res.body?.getReader();
      if (!reader) return { ok: false, why: "missing response body" };
      const decoder = new TextDecoder("utf-8", { fatal: true });
      let body = "", bytes = 0;
      try {
        while (true) {
          const chunk = await reader.read();
          if (chunk.done) break;
          bytes += chunk.value.byteLength;
          if (bytes > MAX_JSON_BYTES) { ctl.abort(); return { ok: false, why: "response too large" }; }
          body += decoder.decode(chunk.value, { stream: true });
        }
        body += decoder.decode();
      } finally { reader.cancel().catch(() => {}); }
      let json;
      try { json = JSON.parse(body); }
      catch { return { ok: false, why: "malformed JSON" }; }
      if (!isObject(json)) return { ok: false, why: "expected JSON object" };
      return { ok: true, json };
    })()]);
  } catch (e) {
    return { ok: false, why: ctl.signal.aborted ? "timeout" : "network/CORS or invalid body" };
  } finally { clearTimeout(timer); }
}

async function readObservation(endpoint, timeoutMs, adapt) {
  const r = await getJSON(endpoint, timeoutMs);
  if (!r.ok) return unavailable(r.why, STATUS.UNREACHABLE);
  const denied = negativeState(r.json);
  if (denied && !["degraded"].includes(denied))
    return { ...unavailable("source reports " + denied, denied), raw: r.json };
  return adapt(r.json);
}

function ledgerObservation(j) {
  if (!Array.isArray(j.receipts) || j.receipts.length > 32 || !countValue(j.count) ||
      j.count !== j.receipts.length || j.operational !== true || String(j.state).toLowerCase() !== "live")
    return unavailable("unrecognized ledger observation");
  const receipts = [], ids = new Set(), seqs = new Set();
  for (const row of j.receipts) {
    if (!isObject(row)) return unavailable("malformed receipt");
    const id = row.receipt_id ?? row.id ?? row.digest ?? row.hash;
    const seq = row.seq ?? row.index ?? null;
    if (!textValue(id) || ids.has(id) || (seq !== null && (!countValue(seq) || seqs.has(seq))))
      return unavailable("missing or duplicate receipt identity / invalid sequence");
    if (seq !== null) seqs.add(seq);
    ids.add(id);
    const action = row.action ?? row.verb ?? row.kind ?? row.schema ?? "receipt";
    if (!textValue(action)) return unavailable("malformed receipt action");
    receipts.push({ id, seq, action, organ: organForAction(action), denied: isDenied(action) });
  }
  return {
    reachable: true, ...observation(j, true), count: j.count, receipts,
    count_scope: textValue(j.count_scope) ? j.count_scope : "recent nodes returned; not the chain total",
    chain_verification: "NOT_EVALUATED_BY_THIS_VIEW", raw: j,
  };
}

function lambdaObservation(j) {
  if (!unitValue(j.lambda) || !unitValue(j.lambda_floor) || typeof j.pass !== "boolean" ||
      j.pass !== (j.lambda >= j.lambda_floor) || !Array.isArray(j.axes) || !j.axes.length ||
      j.axes.length > 64 || j.axes.some((a) => !isObject(a) || !textValue(a.name) || !unitValue(a.score)) ||
      new Set(j.axes.map((a) => a.name)).size !== j.axes.length ||
      (j.trust_axes !== undefined && j.trust_axes !== j.axes.length))
    return unavailable("unrecognized Lambda declaration");
  return {
    reachable: true, ...observation(j, j.evidence_state === "MEASURED"),
    lambda: j.lambda, floor: j.lambda_floor, pass: j.pass, axes: j.axes,
    aggregate: textValue(j.aggregate) ? j.aggregate : "",
    uniqueness: textValue(j.uniqueness) ? j.uniqueness : "status unavailable", raw: j,
  };
}

function doctrineObservation(j) {
  const lk = j.doctrine_lock;
  if (!isObject(lk) || !countValue(lk.locked_formula_count) ||
      !Array.isArray(lk.locked_formula_ids) || lk.locked_formula_count !== lk.locked_formula_ids.length ||
      lk.locked_formula_ids.some((id) => !textValue(id)) ||
      new Set(lk.locked_formula_ids).size !== lk.locked_formula_ids.length)
    return unavailable("unrecognized doctrine declaration");
  return {
    reachable: true, ...observation(j), lambda: lk.lambda || j.lambda_status || "status unavailable",
    commit: textValue(lk.commit) ? lk.commit : "", lockedCount: lk.locked_formula_count,
    declarations: lk.declarations ?? null, axioms: lk.axioms ?? null, sorries: lk.sorries ?? null,
    lockedIds: lk.locked_formula_ids, state: textValue(lk.state) ? lk.state : "unknown", raw: j,
  };
}

function readyObservation(j) {
  const op = j.operator;
  if (!isObject(op) || typeof op.ready !== "boolean" || typeof op.service_ready !== "boolean" ||
      !["ready", "ready_degraded", "not_ready"].includes(j.status))
    return unavailable("unrecognized operator readiness");
  const denied = negativeState(op);
  if (denied) return { ...unavailable("operator reports " + denied, denied), raw: j };
  const ready = j.status === "ready" && op.ready && op.service_ready && op.operator_running === true;
  if (!ready) return { ...unavailable("operator capability is not ready", STATUS.DEGRADED), raw: j };
  const obs = observation(j, true);
  const operatorObs = observation({ ...op, observed_at: op.observed_at ?? j.observed_at }, true);
  if (obs.status === STATUS.LIVE && operatorObs.status !== STATUS.LIVE) obs.status = operatorObs.status;
  if (Number.isFinite(operatorObs.fresh_until) && Number.isFinite(obs.fresh_until))
    obs.fresh_until = Math.min(obs.fresh_until, operatorObs.fresh_until);
  return { reachable: true, ...obs, raw: j };
}

/* Endpoint reachability alone never enables an organ glow. */
async function probeOrgan(organ, timeoutMs = 9000) {
  const adapters = { lambda: lambdaObservation, honest: doctrineObservation, readyz: readyObservation, ledger: ledgerObservation };
  if (!adapters[organ.probe]) return { status: STATUS.UNKNOWN, detail: "unknown probe", raw: null };
  const r = await readObservation(EP[organ.probe], timeoutMs, adapters[organ.probe]);
  return {
    ...r,
    detail: r.reachable ? r.status + " · " + organ.summarize(r.raw) : r.why,
  };
}

async function fetchLedger(timeoutMs = 9000) {
  const r = await readObservation(EP.ledger, timeoutMs, ledgerObservation);
  return { count: null, receipts: [], ...r };
}
async function fetchLambda(timeoutMs = 9000) {
  const r = await readObservation(EP.lambda, timeoutMs, lambdaObservation);
  return { lambda: null, floor: null, pass: null, axes: [], ...r };
}
async function fetchMind(timeoutMs = 9000) {
  const r = await readObservation(EP.healthz, timeoutMs, (j) => {
    if (typeof j.sovereign !== "boolean") return unavailable("missing sovereign declaration");
    return {
      reachable: true, ...observation(j), sovereign: j.sovereign,
      backend: textValue(j.backend) ? j.backend : (textValue(j.inference) ? j.inference : "unknown"),
      mode: textValue(j.mode) ? j.mode : "unknown",
      doctrine: [j.doctrine, j.doctrine_state].filter(textValue).join(" "), raw: j,
    };
  });
  return { sovereign: null, ...r };
}
async function fetchDoctrine(timeoutMs = 9000) {
  const r = await readObservation(EP.honest, timeoutMs, doctrineObservation);
  return { lockedCount: null, lockedIds: [], ...r };
}
async function fetchImmune(timeoutMs = 9000) {
  const r = await readObservation(EP.govern, timeoutMs, (j) => {
    const total = j.engines_total, live = j.engines_live;
    if (!countValue(total) || total === 0 || !countValue(live) || live > total ||
        !Array.isArray(j.mesh) || j.mesh.length !== total ||
        j.mesh.some((m) => !isObject(m) || !textValue(m.name) || typeof m.live !== "boolean") ||
        new Set(j.mesh.map((m) => m.name)).size !== total ||
        j.mesh.filter((m) => m.live).length !== live)
      return unavailable("missing or inconsistent mesh observation");
    const obs = observation(j, true), down = total - live;
    return {
      reachable: true, ...obs,
      status: down && obs.status === STATUS.LIVE ? STATUS.DEGRADED : obs.status,
      intensity: down / total, down, live, total,
      detail: down + "/" + total + " engines reported down · " + obs.status,
    };
  });
  return { intensity: null, down: null, live: null, total: null, ...r };
}

/* A single freshness predicate also gates animations after a successful poll. */
function isFreshLive(record, now = Date.now()) {
  return record?.status === STATUS.LIVE && Number.isFinite(record.fresh_until) && now < record.fresh_until;
}

/* ---- the engine surface --------------------------------------------------- */
const LiveBody = {
  HOST, EP, KANCHAY, STATUS, ORGANS, VERTICALS,
  organForAction, isDenied,
  probeOrgan, fetchLedger, fetchLambda, fetchMind, fetchDoctrine, fetchImmune, isFreshLive, refreshIntegrityView,
};

if (typeof window !== "undefined") window.LiveBody = LiveBody;
export default LiveBody;
export {
  HOST, EP, KANCHAY, STATUS, ORGANS, VERTICALS,
  organForAction, isDenied,
  probeOrgan, fetchLedger, fetchLambda, fetchMind, fetchDoctrine, fetchImmune, isFreshLive, refreshIntegrityView,
};


/* Five-organ overlay: a valid negative answer is authoritative. Fallbacks are
 * only for transport/schema failures, never to hunt for a greener answer. */
function integrityObservation(j) {
  const ev = j.body;
  if (j.surface !== "szl-organ-integrity" || !isObject(ev) ||
      !Array.isArray(ev.organs) || ev.organs.length > 32 ||
      typeof ev.blocked !== "boolean" ||
      ev.organs.some((o) => !isObject(o) || !textValue(o.id) ||
        !["LIVE", "DOWN", "UNKNOWN", "UNAVAILABLE"].includes(o.status)) ||
      new Set(ev.organs.map((o) => o.id)).size !== ev.organs.length ||
      (ev.live_count !== null && (!countValue(ev.live_count) ||
        ev.live_count !== ev.organs.filter((o) => o.status === "LIVE").length)))
    return unavailable("unrecognized organ-integrity observation");
  const state = ev.state || ev.verdict;
  if (!["UNKNOWN", "LIVE", "BLOCKED", "DEGRADED", "ADVISORY_BODY"].includes(state))
    return unavailable("missing organ-integrity state");
  const positive = state === "LIVE" && ev.live === true && !ev.blocked &&
    ev.organs.length > 0 && ev.live_count === ev.organs.length;
  const obs = observation({
    ...j, ...ev, state,
    observed_at: ev.observed_at ?? j.observed_at ?? ev.checked_at,
  }, positive);
  // The envelope is an evidence boundary too: a positive body cannot erase an
  // unavailable/blocked wrapper or its explicit non-live evidence marker.
  const outer = observation(j, positive);
  if (negativeState(j)) obs.status = outer.status;
  else if ([j.state, j.status, j.evidence_state, j.data_kind].some((s) => s !== undefined) &&
      outer.status !== STATUS.LIVE && obs.status === STATUS.LIVE) obs.status = STATUS.REPORTED;
  if (state === "LIVE" && !positive && obs.status === STATUS.REPORTED) obs.status = STATUS.UNKNOWN;
  return {
    reachable: true, ...obs, blocked: ev.blocked, organs: ev.organs,
    detail: obs.status + " · " + (ev.live_count === null ? "unknown" : ev.live_count) +
      "/" + ev.organs.length + " reported LIVE · energy UNAVAILABLE · Conjecture 1 OPEN",
  };
}
/* Expose only the validated upstream observation clock, never a render tick.
 * A source timestamp is still only reported evidence, not a verified signature. */
function updateIntegritySourceTime(rec) {
  const el = typeof document !== "undefined" && document.getElementById("integrity-observed");
  if (!el) return;
  const at = rec?.source_observed_at;
  const millis = typeof at === "string" ? Date.parse(at) : NaN;
  const source = Number.isFinite(millis) ? new Date(millis).toISOString() : null;
  const state = String(rec?.status || STATUS.UNAVAILABLE).toUpperCase();
  const label = source
    ? "source observed at " + source + " (" + state + "; not signature-verified)"
    : "source observed at UNAVAILABLE (" + state + "; not signature-verified)";
  if (el.textContent !== label) el.textContent = label;
}
async function probeOrganIntegrity(timeoutMs = 9000) {
  let rec = { ...unavailable("no observation"), blocked: null, organs: [], endpoint: null };
  for (const url of [
    "/api/anatomy/v1/organs/integrity",
    "https://a-11-oy.com/api/a11oy/v1/organs/integrity",
    EP.integrity,
  ]) {
    const r = await getJSON(url, timeoutMs);
    if (!r.ok) { rec = { ...rec, why: r.why }; continue; }
    const adapted = integrityObservation(r.json);
    if (!adapted.reachable) { rec = { ...rec, why: adapted.why }; continue; }
    rec = { ...adapted, endpoint: url };
    break;
  }
  if (!rec.reachable) rec.detail = "organ-integrity UNAVAILABLE — " + rec.why;
  if (typeof window !== "undefined") window.__szlOrganIntegrity = rec;
  const el = typeof document !== "undefined" && document.getElementById("integrity-strip");
  if (el) { el.dataset.state = rec.status; el.textContent = rec.detail; }
  updateIntegritySourceTime(rec);
  return rec;
}
function refreshIntegrityView(now = Date.now()) {
  const rec = typeof window !== "undefined" && window.__szlOrganIntegrity;
  if (rec?.status === STATUS.LIVE && !isFreshLive(rec, now)) {
    rec.status = STATUS.STALE;
    rec.detail = "stale observation · refresh required; previous " + rec.detail;
    const el = typeof document !== "undefined" && document.getElementById("integrity-strip");
    if (el) { el.dataset.state = rec.status; el.textContent = rec.detail; }
  }
  updateIntegritySourceTime(rec);
  return rec || null;
}
if (typeof window !== "undefined" && typeof document !== "undefined") {
  window.probeOrganIntegrity = probeOrganIntegrity;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => { probeOrganIntegrity(); });
  } else {
    probeOrganIntegrity();
  }
}
