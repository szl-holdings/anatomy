/* =============================================================================
 * live-body.js — SZL Living Anatomy · LIVE BODY VIEW of the agentic GPU mind
 * =============================================================================
 * The agentic GPU (RTX 5000 @ betterwithage) is the MIND; the six round9 ORGAN
 * formulas are the BODY. This page reads each organ's REAL endpoint and lights
 * the organ up with its honest live status. When the GPU mind runs a proactive
 * cycle (immune -> brain -> run -> heart/blood -> nervous) the organs pulse in
 * that order so you can watch the mind act.
 *
 * DOCTRINE (never violated, honest by design):
 *   - sovereign:true is shown ONLY when /api/a11oy/code/healthz reports it. The
 *     half-state (banner sovereign while a router serves) is the ONE
 *     unacceptable outcome, so we read `sovereign` straight from healthz and
 *     never synthesize it.
 *   - Energy / joules are labeled SAMPLE until a real meter is wired.
 *   - Λ is shown as Conjecture 1 (the skeleton's killer formula is intentionally
 *     a conjecture), pulled from /api/a11oy/v1/honest, never hardcoded as proven.
 *   - Unreachable endpoint => honest "unknown / unreachable" empty-state. We
 *     never fabricate a green light for an organ we could not reach.
 *   - Read-only. No key is sent. open-weight only.
 *
 * No build step, no framework, no CDN — a plain ES module that runs as a static
 * SDK page at the .static.hf.space URL, exactly like index.html.
 * ============================================================================ */
"use strict";

/* ---- endpoint hosts (read-only, real) ------------------------------------ */
const HOST = {
  amaru: "https://szlholdings-amaru.hf.space",
  sentra: "https://szlholdings-sentra.hf.space",
  a11oy: "https://szlholdings-a11oy.hf.space",
};

/* The GPU-mind posture endpoint (verified live: returns sovereign/backend/mode). */
const MIND_HEALTHZ = HOST.a11oy + "/api/a11oy/code/healthz";
/* The doctrine/Λ posture (verified live: Λ=Conjecture 1, locked-8, axioms/sorries). */
const DOCTRINE_HONEST = HOST.a11oy + "/api/a11oy/v1/honest";

/* ---- the six organs, each a proven round9 formula + its live endpoint ------ */
/* `pulseOrder` is the proactive-cycle order: immune -> brain -> run ->
 * heart/blood -> nervous. `summarize` turns a raw JSON body into a short honest
 * status line; it must tolerate partial/odd shapes (degrade, never throw). */
const ORGANS = [
  {
    id: "immune", name: "IMMUNE", glyph: "⛨", pulseOrder: 0,
    color: "var(--gate)",
    formula: "ImmuneNeymanPearson — deny-by-default gates (most-powerful test)",
    role: "rejects unsafe / overclaiming work before the mind acts",
    url: HOST.sentra + "/api/sentra/v1/gates",
    summarize: (j) => {
      const gates = j.gates || j.items || (Array.isArray(j) ? j : null);
      if (Array.isArray(gates)) return `${gates.length} deny-by-default gates armed`;
      if (typeof j.count === "number") return `${j.count} gates armed`;
      return "gates responding";
    },
  },
  {
    id: "brain", name: "BRAIN", glyph: "✸", pulseOrder: 1,
    color: "var(--brain)",
    formula: "BrainBeliefUpdate — PAC-Bayes McAllester generalization bound",
    role: "decides which proactive work to admit under uncertainty",
    url: HOST.amaru + "/api/amaru/v1/formulas",
    summarize: (j) => {
      const fs = j.formulas || j.items || (Array.isArray(j) ? j : null);
      const hasPac = JSON.stringify(j).toLowerCase().includes("pac_bayes");
      if (Array.isArray(fs)) return `${fs.length} formulas · pac_bayes ${hasPac ? "present" : "—"}`;
      return hasPac ? "pac_bayes_mcallester present" : "formulas responding";
    },
  },
  {
    id: "heart", name: "HEART", glyph: "❤", pulseOrder: 3,
    color: "var(--heart)",
    formula: "HeartReceiptSigma — σ-algebra receipt bus",
    role: "pumps a verifiable receipt for every GPU action (the heartbeat)",
    url: HOST.amaru + "/api/amaru/receipts",
    summarize: (j) => {
      const rs = j.receipts || j.items || (Array.isArray(j) ? j : null);
      if (Array.isArray(rs)) return `${rs.length} receipts on the bus`;
      if (typeof j.count === "number") return `${j.count} receipts`;
      return "receipt bus beating";
    },
  },
  {
    id: "blood", name: "BLOOD", glyph: "🜂", pulseOrder: 4,
    color: "var(--blood)",
    formula: "BloodDSSEMerkle — Cardano-anchored DSSE provenance",
    role: "signs + carries provenance to every organ",
    /* /khipu/sign is a write/POST endpoint; we only health-probe its host
     * read-only here (a GET returns method-not-allowed/health, never signs). */
    url: HOST.sentra + "/api/sentra/khipu/ledger",
    summarize: (j) => {
      const l = j.ledger || j.entries || j.items || (Array.isArray(j) ? j : null);
      if (Array.isArray(l)) return `${l.length} signed entries in the khipu`;
      return "provenance signer reachable";
    },
  },
  {
    id: "skeleton", name: "SKELETON", glyph: "⊟", pulseOrder: -1,
    color: "var(--skel)",
    formula: "SkeletonLambdaSpine — the Lean kernel (Λ = Conjecture 1)",
    role: "the proof spine — every claim traces here; Λ stays a conjecture",
    url: HOST.amaru + "/api/amaru/v1/math/lean/theorems",
    summarize: (j) => {
      const t = j.theorems || j.items || (Array.isArray(j) ? j : null);
      if (Array.isArray(t)) return `${t.length} kernel theorems · Λ = Conjecture 1`;
      return "lean spine reachable · Λ = Conjecture 1";
    },
  },
  {
    id: "nervous", name: "NERVOUS", glyph: "⌁", pulseOrder: 5,
    color: "var(--nerve)",
    formula: "NervousShannonAlarm — Λ-signed OTEL drift alarm",
    role: "senses drift / half-state and fires the self-heal alarm",
    url: HOST.amaru + "/api/amaru/overwatch/snapshot",
    summarize: (j) => {
      const drift = j.drift ?? j.alarm ?? null;
      if (drift === true) return "DRIFT detected — self-heal armed";
      if (drift === false) return "no drift · posture steady";
      if (j.status) return `overwatch: ${String(j.status)}`;
      return "proprioception reachable";
    },
  },
];

/* ---- status vocabulary ---------------------------------------------------- */
const STATUS = {
  LIVE: "live",         // endpoint answered 2xx with usable JSON
  UNREACHABLE: "unreachable", // network / non-2xx / not-JSON — honest unknown
  PENDING: "pending",   // not yet polled
};

/* fetch one organ endpoint, honestly. Never throws; returns a status record.
 * No credentials, no custom headers (keeps it a simple CORS GET, sends no key). */
async function probeOrgan(organ, timeoutMs = 9000) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(organ.url, {
      method: "GET", mode: "cors", credentials: "omit",
      signal: ctl.signal, cache: "no-store",
    });
    clearTimeout(t);
    if (!res.ok) {
      return { status: STATUS.UNREACHABLE, detail: `HTTP ${res.status}`, raw: null };
    }
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("json")) {
      // HF returns its own HTML 404 page for unrouted spaces — honest unknown.
      return { status: STATUS.UNREACHABLE, detail: "no JSON (space unrouted?)", raw: null };
    }
    const j = await res.json();
    let detail;
    try { detail = organ.summarize(j); }
    catch { detail = "responding (shape unrecognized)"; }
    return { status: STATUS.LIVE, detail, raw: j };
  } catch (e) {
    clearTimeout(t);
    const why = (e && e.name === "AbortError") ? "timeout" : "network/CORS";
    return { status: STATUS.UNREACHABLE, detail: why, raw: null };
  }
}

/* fetch the GPU-mind posture (sovereign/backend/mode). Honest: sovereign is
 * whatever healthz says, defaulting to FALSE (never claim sovereignty we can't
 * confirm — that is the half-state we must never show). */
async function probeMind(timeoutMs = 9000) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(MIND_HEALTHZ, {
      method: "GET", mode: "cors", credentials: "omit",
      signal: ctl.signal, cache: "no-store",
    });
    clearTimeout(t);
    if (!res.ok) return { reachable: false, sovereign: false, detail: `HTTP ${res.status}` };
    const j = await res.json();
    return {
      reachable: true,
      sovereign: j.sovereign === true,   // strict: only the literal true
      backend: j.backend || j.inference || "unknown",
      mode: j.mode || "unknown",
      doctrine: j.doctrine || "",
      raw: j,
    };
  } catch (e) {
    clearTimeout(t);
    const why = (e && e.name === "AbortError") ? "timeout" : "network/CORS";
    return { reachable: false, sovereign: false, detail: why };
  }
}

/* fetch the doctrine / Λ posture for the honesty strip. */
async function probeDoctrine(timeoutMs = 9000) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(DOCTRINE_HONEST, {
      method: "GET", mode: "cors", credentials: "omit",
      signal: ctl.signal, cache: "no-store",
    });
    clearTimeout(t);
    if (!res.ok) return { reachable: false };
    const j = await res.json();
    const lk = j.doctrine_lock || {};
    return {
      reachable: true,
      lambda: lk.lambda || "Conjecture 1",
      commit: lk.commit || "",
      lockedCount: lk.locked_formula_count ?? 8,
      axioms: lk.axioms, sorries: lk.sorries, declarations: lk.declarations,
      doctrine: lk.doctrine || "",
    };
  } catch {
    clearTimeout(t);
    return { reachable: false };
  }
}

/* expose the engine for the page + for the (browser-only) self-check */
const LiveBody = {
  HOST, MIND_HEALTHZ, DOCTRINE_HONEST, ORGANS, STATUS,
  probeOrgan, probeMind, probeDoctrine,
  /* the canonical proactive-cycle order, by organ id, for the pulse animation */
  proactiveCycle() {
    return ORGANS
      .filter((o) => o.pulseOrder >= 0)
      .sort((a, b) => a.pulseOrder - b.pulseOrder)
      .map((o) => o.id);
  },
};

/* ESM + global, so live-body.html can use it either way without a bundler. */
if (typeof window !== "undefined") window.LiveBody = LiveBody;
export default LiveBody;
export { HOST, ORGANS, STATUS, probeOrgan, probeMind, probeDoctrine };
