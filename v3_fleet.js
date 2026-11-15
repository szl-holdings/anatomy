/* =====================================================================
   v3_fleet.js — SZL Living Anatomy · v3 FLEET-WIRED LAYER (additive)
   =====================================================================
   The v3 fleet layer wires the atlas to the estate's actual compute: the
   public receipt chain (SZLHOLDINGS/frontier-54-runs) that every training
   lane and battery gate publishes to — Massed A6000 lanes and the Salad
   4090/5090 worker fleet. The body stops describing the fleet and starts
   READING it.

   FAIL-CLOSED DISCIPLINE (binding):
     - Every number shown is MEASURED: it comes from a receipt fetched live
       from the public dataset, typed-checked (kind/state/score), and only
       then displayed. A receipt that fails the type check renders INVALID.
     - An unreachable dataset renders UNREACHABLE. No fabricated green
       light, no cached fabrication, no synthesized fleet state.
     - The roster is DECLARED, not measured: lanes are declared in source
       here; the receipts' own node/gpu/ts fields are the measured facts.
       The panel cross-references both and never blurs them.
     - Handles only. No raw training content is displayed — only receipt
       metadata (model, score, base, node, gpu, ts, sha256 head).
     - Doctrine v11 LOCKED is unchanged: locked-proven stays EXACTLY 8;
       Lambda remains Conjecture 1; a battery score proves the measured
       run and nothing else. Promotion of any candidate is owner-gated.
   Additive, read-only, zero-CDN. No key is sent; public surfaces only.
   ===================================================================== */
(function (root) {
  'use strict';

  var DATASET = 'https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs';
  var API = 'https://huggingface.co/api/datasets/SZLHOLDINGS/frontier-54-runs';

  /* Pinned receipt set — the 2026-11-15 frontier wave, battery-gated on the
     Massed szl-frontier-gate-1 lane (A6000). Source-bound and deterministic:
     future waves land by pull request, exactly like every other declared
     snapshot in this atlas. Each entry is fetched, typed-checked, and shown
     AS MEASURED — never edited, never re-scored here. */
  var PINNED_BATTERY = [
    { path: 'benchmark/mass-battery-abstention_doctrine_r1_trained.json', label: 'abstention-doctrine-r1 (Qwen3-1.7B)' },
    { path: 'benchmark/mass-battery-doctrine_corpus_r1_trained.json', label: 'doctrine-corpus-r1 (Qwen3.5-0.8B)' },
    { path: 'benchmark/mass-battery-doctrine_math_r1_trained.json', label: 'doctrine-math-r1 (Qwen3-1.7B)' },
    { path: 'benchmark/mass-battery-a11oy_code_r1_trained.json', label: 'a11oy-code-r1 (Qwen2.5-Coder-3B)' },
    { path: 'benchmark/mass-battery-szl_receiptagent_qwen35_0_8b_v3_steward_root.json', label: 'receiptagent-v3 steward_root (Qwen3.5-0.8B)' },
    { path: 'benchmark/mass-battery-szl_receiptagent_qwen35_0_8b_v3_lane5_final.json', label: 'receiptagent-v3 lane5_final (Qwen3.5-0.8B)' }
  ];

  /* Receipt trees counted for the bloodstream — bounded, public, read-only. */
  var TREES = ['benchmark', 'mesh', 'receipts'];

  /* DECLARED fleet roster (not measured): the compute substrate the chain
     is produced on. Measured facts come from receipts, not from here. */
  var ROSTER = [
    { lane: 'szl-frontier-gate-1 (Massed)', gpu: 'RTX A6000 48GB', region: 'us-central-2', role: 'training + battery gate lane (2026-11-15 wave)', state: 'DECLARED' },
    { lane: 'Salad workers (org alloyscape)', gpu: 'RTX 4090 / 5090', region: 'distributed', role: 'perpetual retrain-loop workers (salad_worker v3)', state: 'DECLARED' },
    { lane: 'box198 (Massed 2xA6000)', gpu: '2x RTX A6000', region: 'us-central-1', role: 'inference deployments (not a training lane)', state: 'DECLARED' }
  ];

  var cache = { at: 0, data: null };
  var CACHE_MS = 60000;

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function head(s, n) { s = String(s == null ? '' : s); return s.length <= n ? s : s.slice(0, n) + '...'; }

  function fetchBounded(url, ms) {
    var ctrl = ('AbortController' in root) ? new AbortController() : null;
    var t = setTimeout(function () { if (ctrl) ctrl.abort(); }, ms || 10000);
    return fetch(url, { mode: 'cors', credentials: 'omit', signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) { clearTimeout(t); if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  }

  function isBatteryReceipt(o) {
    return !!(o && typeof o === 'object' &&
      o.kind === 'szl.estate-battery/mass-training' &&
      o.state === 'MEASURED' &&
      typeof o.score === 'string' &&
      typeof o.model === 'string');
  }

  function loadFleet() {
    var now = Date.now();
    if (cache.data && now - cache.at < CACHE_MS) return Promise.resolve(cache.data);
    var trees = TREES.map(function (dir) {
      return fetchBounded(API + '/tree/main/' + dir)
        .then(function (entries) {
          var files = (entries || []).filter(function (e) { return e && e.type === 'file'; });
          return { dir: dir, count: files.length, ok: true };
        })
        .catch(function () { return { dir: dir, count: 0, ok: false }; });
    });
    var receipts = PINNED_BATTERY.map(function (p) {
      return fetchBounded(DATASET + '/resolve/main/' + p.path, 15000)
        .then(function (o) {
          if (!isBatteryReceipt(o)) return { pin: p, ok: true, valid: false, receipt: null };
          return { pin: p, ok: true, valid: true, receipt: o };
        })
        .catch(function (e) { return { pin: p, ok: false, valid: false, receipt: null, error: String(e && e.message || e) }; });
    });
    return Promise.all([Promise.all(trees), Promise.all(receipts)]).then(function (res) {
      cache = { at: now, data: { trees: res[0], receipts: res[1], fetchedAt: new Date(now).toISOString() } };
      return cache.data;
    });
  }

  var panel = null, btn = null, lastFocus = null;

  function chip(text, cls) { return '<span class="v3f-chip ' + (cls || '') + '">' + text + '</span>'; }

  function render(data) {
    var treeOk = data.trees.filter(function (t) { return t.ok; });
    var total = data.trees.reduce(function (a, t) { return a + t.count; }, 0);
    var measured = data.receipts.filter(function (r) { return r.ok && r.valid; });
    var invalid = data.receipts.filter(function (r) { return r.ok && !r.valid; });
    var unreachable = data.receipts.filter(function (r) { return !r.ok; });

    var h = '';
    h += '<div class="v3f-sec"><div class="v3f-h">RECEIPT BLOODSTREAM ' + (treeOk.length ? chip('MEASURED', 'ok') : chip('UNREACHABLE', 'bad')) + '</div>';
    if (treeOk.length) {
      h += '<div class="v3f-line">' + total + ' receipt files across ' + treeOk.map(function (t) { return t.dir + ' ' + t.count; }).join(' / ') + ' — counted live from the public chain.</div>';
    } else {
      h += '<div class="v3f-line">The receipt chain is unreachable from this browser right now. That is the fail-closed result; nothing is cached or fabricated.</div>';
    }
    h += '</div>';

    h += '<div class="v3f-sec"><div class="v3f-h">BATTERY GATE — 2026-11-15 FRONTIER WAVE ' + chip(measured.length + '/6 MEASURED', measured.length === 6 ? 'ok' : 'warn') + '</div>';
    h += '<table class="v3f-tbl"><tr><th>candidate</th><th>score</th><th>node / gpu</th></tr>';
    data.receipts.forEach(function (r) {
      if (r.ok && r.valid) {
        var o = r.receipt;
        h += '<tr><td>' + esc(r.pin.label) + '</td><td>' + esc(o.score) + '</td><td>' + esc(head(o.node, 22)) + ' / ' + esc(head(o.gpu, 16)) + '</td></tr>';
      } else if (r.ok && !r.valid) {
        h += '<tr><td>' + esc(r.pin.label) + '</td><td colspan="2">' + chip('INVALID', 'bad') + ' fetched but failed the typed receipt contract</td></tr>';
      } else {
        h += '<tr><td>' + esc(r.pin.label) + '</td><td colspan="2">' + chip('UNREACHABLE', 'bad') + '</td></tr>';
      }
    });
    h += '</table>';
    h += '<div class="v3f-line v3f-dim">Scores are AS MEASURED — 6 probes (3 answerable + 3 unanswerable). The battery is the gate, not the promotion: candidate promotion stays owner-gated.</div>';
    h += '</div>';

    h += '<div class="v3f-sec"><div class="v3f-h">FLEET ROSTER ' + chip('DECLARED', 'warn') + '</div>';
    ROSTER.forEach(function (r) {
      h += '<div class="v3f-line"><b>' + esc(r.lane) + '</b> — ' + esc(r.gpu) + ' — ' + esc(r.role) + '</div>';
    });
    h += '<div class="v3f-line v3f-dim">Roster entries are declared in source, not measured. The measured facts above come from the receipts themselves (node + gpu fields).</div>';
    h += '</div>';

    h += '<div class="v3f-foot">Doctrine v11 LOCKED unchanged: locked-proven stays exactly 8. Lambda = Conjecture 1. Handles only, read-only, no key sent. Fetched ' + esc(data.fetchedAt) + '.</div>';
    return h;
  }

  function ensureStyles() {
    if (document.getElementById('v3f-style')) return;
    var css = ''
      + '.v3f-btn{position:fixed;left:14px;bottom:14px;z-index:60;font:600 12px/1.4 system-ui,sans-serif;color:#d8e6ff;background:rgba(10,20,40,.88);border:1px solid #3b5b8f;border-radius:10px;padding:8px 12px;cursor:pointer}'
      + '.v3f-btn:focus-visible{outline:2px solid #8fb8ff;outline-offset:2px}'
      + '.v3f-panel{position:fixed;left:14px;bottom:56px;z-index:61;max-width:min(560px,92vw);max-height:72vh;overflow:auto;color:#d8e6ff;background:rgba(8,16,34,.96);border:1px solid #3b5b8f;border-radius:12px;padding:14px 16px;font:13px/1.5 system-ui,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.5)}'
      + '.v3f-h{font-weight:700;letter-spacing:.04em;margin:2px 0 6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}'
      + '.v3f-sec{margin:10px 0;padding-top:8px;border-top:1px solid rgba(120,160,220,.25)}'
      + '.v3f-sec:first-child{border-top:none}'
      + '.v3f-line{margin:4px 0}'
      + '.v3f-dim{opacity:.72;font-size:12px}'
      + '.v3f-chip{font:600 10px/1.2 system-ui,sans-serif;padding:2px 7px;border-radius:999px;border:1px solid rgba(160,190,230,.4)}'
      + '.v3f-chip.ok{color:#8affc1;border-color:#2f7d4f;background:rgba(20,60,35,.6)}'
      + '.v3f-chip.warn{color:#ffd479;border-color:#8a6d2f;background:rgba(70,55,15,.5)}'
      + '.v3f-chip.bad{color:#ff9d9d;border-color:#8f3b3b;background:rgba(70,20,20,.5)}'
      + '.v3f-tbl{border-collapse:collapse;width:100%;font-size:12px}'
      + '.v3f-tbl th,.v3f-tbl td{border:1px solid rgba(120,160,220,.25);padding:4px 6px;text-align:left;vertical-align:top}'
      + '.v3f-foot{margin-top:12px;font-size:11px;opacity:.8;border-top:1px solid rgba(120,160,220,.25);padding-top:8px}';
    var st = document.createElement('style');
    st.id = 'v3f-style';
    st.textContent = css;
    document.head.appendChild(st);
  }

  function closePanel() {
    if (panel) { panel.remove(); panel = null; }
    if (btn) { btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
  }

  function openPanel() {
    ensureStyles();
    lastFocus = document.activeElement;
    panel = el('div', 'v3f-panel');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Frontier Fleet v3 — live receipt chain');
    panel.innerHTML = '<div class="v3f-line">Loading the live receipt chain...</div>';
    document.body.appendChild(panel);
    btn.setAttribute('aria-expanded', 'true');
    loadFleet().then(function (data) {
      if (!panel) return;
      panel.innerHTML = render(data);
      var f = panel.querySelector('button, [tabindex]');
      if (f) f.focus();
    }).catch(function (e) {
      if (!panel) return;
      panel.innerHTML = '<div class="v3f-line">' + chip('UNREACHABLE', 'bad') + ' The receipt chain could not be read from this browser. Fail-closed: nothing is shown that was not measured. (' + esc(String(e && e.message || e)) + ')</div>';
    });
  }

  function mount() {
    if (document.getElementById('v3f-btn')) return;
    ensureStyles();
    btn = el('button', 'v3f-btn', 'FLEET &#183; v3');
    btn.id = 'v3f-btn';
    btn.type = 'button';
    btn.setAttribute('aria-controls', 'v3f-panel');
    btn.setAttribute('aria-expanded', 'false');
    btn.title = 'Frontier Fleet v3 — the atlas wired to the estate compute, reading the public receipt chain';
    btn.addEventListener('click', function () { if (panel) closePanel(); else openPanel(); });
    document.body.appendChild(btn);
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && panel) { closePanel(); }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }

  root.SZLFleetV3 = { loadFleet: loadFleet, render: render };
}(typeof window !== 'undefined' ? window : this));
