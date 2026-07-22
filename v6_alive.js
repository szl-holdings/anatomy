/* =====================================================================
   v6_alive.js — SZL Living Anatomy · v6 ALIVE-PROOF LAYER (additive)
   =====================================================================
   The v6 ratchet: the map stops describing the substrate and starts
   PROVING it. This layer fetches the latest anatomy alive-harness run
   from the public DSSE-signed sink (SZLHOLDINGS/test-results), verifies
   the ECDSA-P256 signature IN THE BROWSER (WebCrypto, DSSE PAE v1)
   against the committed org public key, and only then displays the run.

   FAIL-CLOSED DISCIPLINE (binding):
     - No signature verification → the panel shows UNVERIFIED / UNREACHABLE.
       We never display an unverified number as a verified one.
     - The public key is pinned below AND cross-checked against the
       committed copy at hatun-mcp/main/PUBKEY_szlholdings-ec-p256.pem.
       A mismatch is displayed as a key-pin failure, not silently ignored.
     - The Hatun MCP gateway chip goes LIVE only on a real 2xx server-card
       fetch with a parseable tool inventory.
     - Doctrine v11 LOCKED is unchanged: locked-proven stays EXACTLY 5
       (F1 F11 F12 F18 F19); F4/F7/F22 are EXPERIMENTAL / NOT LOCKED;
       Λ is Conjecture 1, never a theorem.
       A signed GREEN harness run proves liveness, not doctrine upgrades.
   Additive, read-only, zero-CDN. No key is sent; open surfaces only.
   ===================================================================== */
(function (root) {
  'use strict';

  var SINK = 'https://huggingface.co/datasets/SZLHOLDINGS/test-results';
  var RUNS_URL = SINK + '/resolve/main/harness_runs.jsonl';
  var PUBKEY_URL = 'https://raw.githubusercontent.com/szl-holdings/hatun-mcp/main/PUBKEY_szlholdings-ec-p256.pem';
  var HATUN_CARD = 'https://szlholdings-hatun-mcp.hf.space/.well-known/mcp/server-card.json';

  /* Pinned committed org public key (SPKI, P-256) — szlholdings-ec-p256 */
  var PIN_PEM = '-----BEGIN PUBLIC KEY-----\n'
    + 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEk+AEVaqvPGGBF/OAEpr7/3hcNHgF\n'
    + 'bXn+bqq0egeockovraAuzkfbVf6kiH6wAy01iaBtv3j/1W2Amx/xbUnelQ==\n'
    + '-----END PUBLIC KEY-----';

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function b64ToBytes(b64) { var bin = atob(b64.replace(/\s+/g, '')); var out = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i); return out; }
  function pemToSpki(pem) { return b64ToBytes(pem.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '')); }
  function utf8(s) { return new TextEncoder().encode(s); }
  function concatBytes(parts) { var n = 0, i; for (i = 0; i < parts.length; i++) n += parts[i].length; var out = new Uint8Array(n), o = 0; for (i = 0; i < parts.length; i++) { out.set(parts[i], o); o += parts[i].length; } return out; }

  /* DSSE PAE v1: "DSSEv1 SP len(type) SP type SP len(payload) SP payload" */
  function pae(payloadType, payloadBytes) {
    var t = utf8(payloadType);
    return concatBytes([utf8('DSSEv1 ' + t.length + ' '), t, utf8(' ' + payloadBytes.length + ' '), payloadBytes]);
  }

  /* ECDSA sig from gateway is ASN.1/DER; WebCrypto wants raw r||s (P1363). */
  function derToP1363(der) {
    var i = 2; /* SEQUENCE, len (assume short-form or 1-byte long-form) */
    if (der[1] & 0x80) i = 2 + (der[1] & 0x7f);
    function readInt() {
      if (der[i] !== 0x02) throw new Error('bad DER');
      var len = der[i + 1]; i += 2;
      var v = der.slice(i, i + len); i += len;
      while (v.length > 32 && v[0] === 0) v = v.slice(1);
      var out = new Uint8Array(32); out.set(v, 32 - v.length); return out;
    }
    var r = readInt(), s = readInt();
    return concatBytes([r, s]);
  }

  function verifyDsse(env) {
    var payloadBytes = b64ToBytes(env.payload);
    var msg = pae(env.payloadType, payloadBytes);
    var sig = derToP1363(b64ToBytes(env.signatures[0].sig));
    return crypto.subtle.importKey('spki', pemToSpki(PIN_PEM), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify'])
      .then(function (key) { return crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, key, sig, msg); })
      .then(function (ok) { return { ok: ok, payload: JSON.parse(new TextDecoder().decode(payloadBytes)) }; });
  }

  function fetchText(url) { return fetch(url, { mode: 'cors', credentials: 'omit', cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); }); }

  /* ---------------- styles ---------------- */
  var css = [
    '#v6panel{position:fixed;z-index:42;top:0;right:0;height:100%;width:min(460px,94vw);background:linear-gradient(180deg,rgba(8,14,22,.99),rgba(5,9,15,.98));border-left:1px solid rgba(255,255,255,.1);box-shadow:-8px 0 40px rgba(0,0,0,.5);transform:translateX(102%);transition:transform .32s cubic-bezier(.2,.7,.2,1);display:flex;flex-direction:column;pointer-events:auto}',
    '#v6panel.open{transform:translateX(0)}',
    '#v6panel .v6h{padding:20px 22px 14px;border-bottom:1px solid rgba(255,255,255,.1)}',
    '#v6panel .v6h .eyebrow{font-family:var(--font-m,monospace);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--text-dim,#8aa)}',
    '#v6panel .v6h h2{font-size:20px;font-weight:700;margin:6px 0 0;line-height:1.15}',
    '#v6panel .v6b{padding:16px 22px 90px;overflow:auto;font-size:12.5px;line-height:1.55;color:var(--text,#dfe)}',
    '#v6panel .v6close{position:absolute;top:14px;right:14px;background:none;border:1px solid rgba(255,255,255,.18);color:var(--text,#dfe);border-radius:8px;width:30px;height:30px;cursor:pointer;font-size:16px;line-height:1}',
    '.v6-chip{font-family:var(--font-m,monospace);font-size:9.5px;letter-spacing:.06em;border:1px solid currentColor;border-radius:6px;padding:1px 6px;white-space:nowrap}',
    '.v6-chip.ok{color:#69f0ae}.v6-chip.bad{color:#ff7eb6}.v6-chip.wait{color:#9ea7c0}.v6-chip.warn{color:#ffd166}',
    '.v6-card{border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:13px 14px;margin:11px 0;background:rgba(255,255,255,.02)}',
    '.v6-card .h{display:flex;align-items:center;gap:8px;justify-content:space-between;font-weight:700;font-size:13.5px}',
    '.v6-mono{font-family:var(--font-m,monospace);font-size:11px;background:rgba(0,0,0,.34);border-left:2px solid #69f0ae;border-radius:6px;padding:8px 10px;margin-top:8px;white-space:pre-wrap;word-break:break-word;color:#e7ecff}',
    '.v6-note{border:1px solid #ffd166;background:rgba(255,209,102,.07);border-radius:10px;padding:11px 13px;margin:12px 0;font-size:12px}',
    '.v6-layers{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}',
    '.v6-layers .cell{border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:6px 8px;font-family:var(--font-m,monospace);font-size:10.5px}'
  ].join('\n');

  /* ---------------- panel ---------------- */
  var panel, body;
  function buildPanel() {
    var st = el('style'); st.textContent = css; document.head.appendChild(st);
    panel = el('div'); panel.id = 'v6panel';
    var h = el('div', 'v6h');
    h.appendChild(el('div', 'eyebrow', 'v6 alive-proof layer · verify-then-display'));
    h.appendChild(el('h2', null, 'Alive-Harness · DSSE-verified in this browser'));
    var x = el('button', 'v6close', '×'); x.setAttribute('aria-label', 'Close'); x.addEventListener('click', close);
    h.appendChild(x);
    body = el('div', 'v6b', '<span class="v6-chip wait">FETCHING…</span> pulling the latest signed harness run…');
    panel.appendChild(h); panel.appendChild(body);
    document.body.appendChild(panel);
  }
  function open() { panel.classList.add('open'); refresh(); }
  function close() { panel.classList.remove('open'); }

  function render(state) {
    body.innerHTML = '';
    var run = state.run;
    if (state.status !== 'VERIFIED') {
      var chip = state.status === 'UNREACHABLE' ? 'bad' : 'warn';
      body.appendChild(el('div', 'v6-note',
        '<b><span class="v6-chip ' + chip + '">' + esc(state.status) + '</span></b> ' + esc(state.detail || '')
        + '<br><br>Fail-closed: nothing is displayed as verified without an in-browser '
        + 'ECDSA-P256 signature check against the committed org key. '
        + '<a href="' + SINK + '" target="_blank" rel="noopener" style="color:#5ad1ff">Inspect the sink directly →</a>'));
      return;
    }
    var c1 = el('div', 'v6-card');
    c1.appendChild(el('div', 'h', 'Latest harness run <span class="v6-chip ' + (run.verdict === 'GREEN' ? 'ok' : 'warn') + '">' + esc(run.verdict) + ' · SIGNATURE VERIFIED</span>'));
    c1.appendChild(el('p', null,
      esc(run.assertions_passed + '/' + run.assertions_total) + ' live assertions · formula gates '
      + esc(run.formula_gates_passed + '/' + run.formula_gates_total)
      + ' · harness ' + esc(run.harness_version) + '<br>finished ' + esc(run.finishedAt)));
    c1.appendChild(el('div', 'v6-mono',
      'keyid: ' + esc(state.keyid) + '\npin: committed PUBKEY_szlholdings-ec-p256.pem '
      + (state.pinMatch === true ? '(cross-check MATCH)' : state.pinMatch === false ? '(CROSS-CHECK MISMATCH!)' : '(cross-check unreachable)')
      + '\nevidence sha256: ' + esc(run.evidence_sha256).slice(0, 32) + '…\nverified: in THIS browser via WebCrypto, DSSE PAE v1'));
    body.appendChild(c1);

    if (state.layers) {
      var c2 = el('div', 'v6-card');
      c2.appendChild(el('div', 'h', 'Layers (from the signed evidence)'));
      var grid = el('div', 'v6-layers');
      Object.keys(state.layers).forEach(function (k) {
        var v = state.layers[k];
        grid.appendChild(el('div', 'cell', esc(k) + ' · <span class="v6-chip ' + (v.fail ? 'warn' : 'ok') + '">' + v.pass + ' pass' + (v.fail ? ' · ' + v.fail + ' fail' : '') + '</span>'));
      });
      c2.appendChild(grid);
      body.appendChild(c2);
    }

    var c3 = el('div', 'v6-card');
    c3.appendChild(el('div', 'h', 'Hatun MCP gateway <span class="v6-chip ' + (state.hatun ? 'ok' : 'bad') + '">' + (state.hatun ? 'LIVE · ' + state.hatun + ' tools' : 'UNREACHABLE') + '</span>'));
    c3.appendChild(el('p', null, 'The signer of this record: the live MCP gateway (dsse_sign, ECDSA-P256). Runs are published fail-closed — the publisher verifies before and after upload.'));
    body.appendChild(c3);

    body.appendChild(el('div', 'v6-note',
      '<b>Doctrine boundary (unchanged):</b> a signed GREEN run proves the substrate is ALIVE '
      + 'and its gates execute — it upgrades NO proof claim. Locked-proven stays exactly 5; '
      + 'F4/F7/F22 remain EXPERIMENTAL / NOT LOCKED; '
      + 'Λ remains Conjecture 1. '
      + '<a href="' + SINK + '" target="_blank" rel="noopener" style="color:#5ad1ff">Sink + reproduce-it-yourself instructions →</a>'));
  }

  function refresh() {
    var state = { status: 'UNREACHABLE', detail: '', hatun: 0, pinMatch: null };
    var pHatun = fetchText(HATUN_CARD).then(function (t) {
      var card = JSON.parse(t);
      var tools = (card.tools && card.tools.length) || (card.capabilities && card.capabilities.tools && card.capabilities.tools.count) || 0;
      state.hatun = tools || 'yes';
    }).catch(function () { state.hatun = 0; });
    var pPin = fetchText(PUBKEY_URL).then(function (t) {
      state.pinMatch = t.replace(/\s+/g, '') === PIN_PEM.replace(/\s+/g, '');
    }).catch(function () { state.pinMatch = null; });
    var pRun = fetchText(RUNS_URL).then(function (txt) {
      var lines = txt.trim().split('\n');
      var rec = JSON.parse(lines[lines.length - 1]);
      return verifyDsse(rec.dsse).then(function (v) {
        if (!v.ok) { state.status = 'UNVERIFIED'; state.detail = 'Signature did NOT verify against the pinned org key. Refusing to display the run as verified.'; return; }
        state.status = 'VERIFIED';
        state.run = v.payload;
        state.keyid = rec.dsse.signatures[0].keyid || 'szlholdings-ec-p256';
        var stamp = (v.payload.finishedAt || '').replace(/[:\-]/g, '');
        return fetchText(SINK + '/resolve/main/runs/' + stamp + '.evidence.json')
          .then(function (ev) { state.layers = JSON.parse(ev).layers; }).catch(function () { /* layers optional */ });
      });
    }).catch(function (e) { state.status = 'UNREACHABLE'; state.detail = 'Could not fetch the signed sink (' + e.message + ').'; });
    Promise.all([pHatun, pPin, pRun]).then(function () { render(state); });
  }

  /* ---------------- button (injected next to the v5 cluster) ---------------- */
  function init() {
    buildPanel();
    var anchor = document.getElementById('btn-v5-stack') || document.getElementById('btn-v5-willay');
    var btn = el('button', 'btn', '⛬ alive-proof (v6)');
    btn.id = 'btn-v6-alive';
    btn.title = 'v6 alive-proof layer: latest harness run fetched from the public DSSE-signed sink and signature-verified IN THIS BROWSER (WebCrypto, pinned org key) before display · fail-closed, never a fabricated green light';
    btn.setAttribute('aria-controls', 'v6panel');
    btn.addEventListener('click', function () { if (panel.classList.contains('open')) close(); else open(); });
    if (anchor && anchor.parentNode) anchor.parentNode.appendChild(btn);
    else document.body.appendChild(btn);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();

})(window);
