/* =====================================================================
   v4_holo.js — SZL Living Anatomy · v4 RECEIPT HOLOGRAM (Λ·HOLO)
   =====================================================================
   The receipt hologram: the public receipt chain rendered as a living
   organism. Every receipt file in SZLHOLDINGS/frontier-54-runs becomes a
   light cell whose position, color and shimmer are DETERMINISTIC functions
   of its file-name hash — the same chain always renders the same organism.
   The picture is the hash.

   Honest rules (same doctrine as every instrument in this atlas):
   - Only the six pinned battery receipts carry a measured score; their
     pulse is driven by the score AS MEASURED in the receipt itself.
   - Every other cell is name-bound only and is labeled exactly that way.
   - WebGL2 missing or init failure => UNSUPPORTED. Chain unreachable =>
     UNREACHABLE. Nothing is cached beyond 60s, nothing is fabricated.
   - Handles only, read-only, no key sent; public surfaces only.
   - Techniques (hex-lattice domains, cosine palettes, volumetric glow,
     hash-deterministic placement) are re-derived here in self-contained
     GLSL — zero CDN, zero third-party code.
   ===================================================================== */
(function (root) {
  'use strict';

  var DATASET = 'https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs';
  var API = 'https://huggingface.co/api/datasets/SZLHOLDINGS/frontier-54-runs';
  var TREES = ['benchmark', 'mesh', 'receipts'];

  /* Pinned receipt set — the 2026-11-15 frontier wave (same pins as the
     FLEET v3 panel): fetched live, typed-checked, shown AS MEASURED. */
  var PINNED_BATTERY = [
    { label: 'abstention-doctrine-r1', path: 'benchmark/mass-battery-abstention_doctrine_r1_trained.json' },
    { label: 'doctrine-math-r1', path: 'benchmark/mass-battery-doctrine_math_r1_trained.json' },
    { label: 'receiptagent-v3 steward_root', path: 'benchmark/mass-battery-szl_receiptagent_qwen35_0_8b_v3_steward_root.json' },
    { label: 'receiptagent-v3 lane5_final', path: 'benchmark/mass-battery-szl_receiptagent_qwen35_0_8b_v3_lane5_final.json' },
    { label: 'a11oy-code-r1', path: 'benchmark/mass-battery-a11oy_code_r1_trained.json' },
    { label: 'doctrine-corpus-r1', path: 'benchmark/mass-battery-doctrine_corpus_r1_trained.json' }
  ];

  var ROSTER = [
    { lane: 'Massed szl-frontier-gate-1', gpu: 'A6000', role: 'training + battery gate lane' },
    { lane: 'Salad alloyscape', gpu: '4090 / 5090 workers', role: 'fleet training workers' },
    { lane: 'box198', gpu: 'A6000 x2', role: 'inference deployments' }
  ];

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function head(s, n) { s = String(s == null ? '' : s); return s.length <= n ? s : s.slice(0, n) + '...'; }
  function chip(text, cls) { return '<span class="v4h-chip ' + (cls || '') + '">' + text + '</span>'; }

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

  /* ---------------- deterministic hashing: the organism IS the chain --- */
  function fnv1a(str) {
    var h = 0x811c9dc5;
    str = String(str);
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = (h * 0x01000193) >>> 0;
    }
    return h >>> 0;
  }
  function h01(h, salt) {
    var x = (h ^ Math.imul(salt, 0x9e3779b1)) >>> 0;
    x ^= x >>> 16; x = Math.imul(x, 0x21f0aaad) >>> 0;
    x ^= x >>> 15; x = Math.imul(x, 0x735a2d97) >>> 0;
    x ^= x >>> 15;
    return x / 4294967296;
  }

  function trefoil(t) {
    var s = 0.62;
    return [s * (Math.sin(t) + 2 * Math.sin(2 * t)),
            s * (Math.cos(t) - 2 * Math.cos(2 * t)),
            s * (-Math.sin(3 * t))];
  }

  function treePalette(tree, h) {
    var b = 0.55 + 0.45 * h;
    if (tree === 'benchmark') return [0.16 * b + 0.10, 0.85 * b, 0.95 * b];
    if (tree === 'receipts') return [0.25 * b, 0.95 * b, 0.55 * b];
    return [0.55 * b, 0.38 * b, 0.98 * b];
  }

  function cellFor(name, tree) {
    var h = fnv1a(name);
    var t = h01(h, 1) * Math.PI * 2;
    var base = trefoil(t);
    var spread = tree === 'benchmark' ? 0.17 : (tree === 'receipts' ? 0.34 : 0.62);
    var p = [base[0] + (h01(h, 2) - 0.5) * spread,
             base[1] + (h01(h, 3) - 0.5) * spread,
             base[2] + (h01(h, 4) - 0.5) * spread];
    if (tree === 'mesh') {
      var grow = 1.0 + h01(h, 5) * 0.35;
      p = [p[0] * grow, p[1] * grow, p[2] * grow];
    }
    var col = treePalette(tree, h01(h, 6));
    var size = 1.5 + h01(h, 7) * 1.3;
    return { name: name, tree: tree, pos: p, col: col, size: size, pulse: 0.06, meta: null, h: h };
  }

  /* ---------------- data load (60s cache, fail-closed) ----------------- */
  var cache = { at: 0, data: null };
  var CACHE_MS = 60000;

  function loadHolo() {
    var now = Date.now();
    if (cache.data && now - cache.at < CACHE_MS) return Promise.resolve(cache.data);
    var trees = TREES.map(function (dir) {
      return fetchBounded(API + '/tree/main/' + dir, 12000)
        .then(function (entries) {
          var files = (entries || []).filter(function (e) { return e && e.type === 'file'; });
          return { dir: dir, count: files.length, ok: true,
                   names: files.map(function (e) { return String(e.path || '').split('/').pop(); }) };
        })
        .catch(function () { return { dir: dir, count: 0, ok: false, names: [] }; });
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

  /* ---------------- GLSL (re-derived, self-contained) ------------------ */
  var VS_POINTS = [
    '#version 300 es',
    'precision highp float;',
    'layout(location=0) in vec3 aPos;',
    'layout(location=1) in vec3 aCol;',
    'layout(location=2) in vec3 aMeta;',
    'uniform mat4 uVP;',
    'uniform float uT;',
    'out vec3 vCol;',
    'out float vFlick;',
    'void main(){',
    '  vec3 p = aPos * (1.0 + 0.045 * sin(uT * 0.4 + aMeta.y * 6.2831));',
    '  vFlick = 0.72 + 0.28 * sin(uT * (1.6 + aMeta.z * 3.0) + aMeta.y * 37.0);',
    '  vCol = aCol;',
    '  gl_Position = uVP * vec4(p, 1.0);',
    '  float w = max(0.15, gl_Position.w);',
    '  float pulse = 1.0 + (aMeta.z > 0.05 ? 0.45 * aMeta.z * sin(uT * (2.2 + aMeta.z * 2.0) + aMeta.y * 9.0) : 0.0);',
    '  gl_PointSize = clamp(aMeta.x * pulse * (260.0 / w), 1.0, 96.0);',
    '}'
  ].join('\n');

  var FS_POINTS = [
    '#version 300 es',
    'precision highp float;',
    'in vec3 vCol;',
    'in float vFlick;',
    'out vec4 fragColor;',
    'void main(){',
    '  vec2 q = gl_PointCoord * 2.0 - 1.0;',
    '  float d = dot(q, q);',
    '  if (d > 1.0) discard;',
    '  float core = exp(-d * 4.5);',
    '  float rim = exp(-d * 1.9) * 0.32;',
    '  vec3 c = vCol * core + vCol.zxy * rim;',
    '  c *= vFlick;',
    '  fragColor = vec4(c, core + rim);',
    '}'
  ].join('\n');

  var FS_BACK = [
    '#version 300 es',
    'precision highp float;',
    'uniform vec2 uRes;',
    'uniform float uT;',
    'out vec4 fragColor;',
    'float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }',
    'float hexEdge(vec2 p){',
    '  vec2 s = vec2(1.0, 1.7320508);',
    '  vec2 a = mod(p, s) - s * 0.5;',
    '  vec2 b = mod(p - s * 0.5, s) - s * 0.5;',
    '  vec2 g = dot(a, a) < dot(b, b) ? a : b;',
    '  return 0.5 - max(dot(g, normalize(vec2(1.0, 1.7320508))), g.x);',
    '}',
    'void main(){',
    '  vec2 uv = (gl_FragCoord.xy * 2.0 - uRes) / uRes.y;',
    '  float r = length(uv);',
    '  vec2 hp = uv * 3.2 + vec2(0.0, uT * 0.015);',
    '  float e = hexEdge(hp);',
    '  float hex = smoothstep(0.045, 0.0, e);',
    '  float fog = 0.5 + 0.5 * sin(r * 2.3 + uT * 0.11) * sin(r * 0.7 - uT * 0.05);',
    '  float ring = exp(-pow(abs(r - 0.85), 2.0) * 6.0) * fog;',
    '  vec3 col = vec3(0.010, 0.026, 0.060);',
    '  col += vec3(0.045, 0.14, 0.19) * hex * (0.45 + 0.55 * h21(floor(hp * 7.0)));',
    '  col += vec3(0.09, 0.20, 0.28) * ring;',
    '  col *= smoothstep(1.9, 0.25, r);',
    '  col *= 0.93 + 0.07 * sin(gl_FragCoord.y * 1.7);',
    '  fragColor = vec4(col, 1.0);',
    '}'
  ].join('\n');

  var VS_BACK = [
    '#version 300 es',
    'void main(){',
    '  vec2 v = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);',
    '  gl_Position = vec4(v * 2.0 - 1.0, 0.0, 1.0);',
    '}'
  ].join('\n');

  /* ---------------- tiny mat4 (column-major) ---------------------------- */
  function persp(fov, asp, n, f) {
    var t = 1 / Math.tan(fov / 2);
    return [t / asp, 0, 0, 0,
            0, t, 0, 0,
            0, 0, (f + n) / (n - f), -1,
            0, 0, 2 * f * n / (n - f), 0];
  }
  function lookAt(e, c, up) {
    var z = [e[0] - c[0], e[1] - c[1], e[2] - c[2]];
    var zl = Math.hypot(z[0], z[1], z[2]) || 1;
    z = [z[0] / zl, z[1] / zl, z[2] / zl];
    var x = [up[1] * z[2] - up[2] * z[1], up[2] * z[0] - up[0] * z[2], up[0] * z[1] - up[1] * z[0]];
    var xl = Math.hypot(x[0], x[1], x[2]) || 1;
    x = [x[0] / xl, x[1] / xl, x[2] / xl];
    var y = [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]];
    return [x[0], y[0], z[0], 0,
            x[1], y[1], z[1], 0,
            x[2], y[2], z[2], 0,
            -(x[0] * e[0] + x[1] * e[1] + x[2] * e[2]),
            -(y[0] * e[0] + y[1] * e[1] + y[2] * e[2]),
            -(z[0] * e[0] + z[1] * e[1] + z[2] * e[2]), 1];
  }
  function mul(a, b) {
    var o = new Array(16);
    for (var c = 0; c < 4; c++) {
      for (var r = 0; r < 4; r++) {
        o[c * 4 + r] = a[r] * b[c * 4] + a[4 + r] * b[c * 4 + 1] + a[8 + r] * b[c * 4 + 2] + a[12 + r] * b[c * 4 + 3];
      }
    }
    return o;
  }

  /* ---------------- overlay UI ------------------------------------------ */
  var overlay = null, btn = null, tip = null, raf = 0, gl = null, lastFocus = null;
  var cells = [];
  var cam = { yaw: 0.6, pitch: 0.35, dist: 5.4 };
  var drag = null, idleAt = 0;
  var reduceMotion = false;
  try { reduceMotion = root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

  function ensureStyles() {
    if (document.getElementById('v4h-style')) return;
    var css = ''
      + '.v4h-btn{position:fixed;right:14px;bottom:14px;z-index:60;font:600 12px/1.4 system-ui,sans-serif;color:#ffe9b0;background:rgba(30,22,8,.9);border:1px solid #8a6d2f;border-radius:10px;padding:8px 12px;cursor:pointer}'
      + '.v4h-btn:focus-visible{outline:2px solid #ffd479;outline-offset:2px}'
      + '#v4holo{position:fixed;inset:0;z-index:70;display:none;background:radial-gradient(120% 120% at 50% 45%, rgba(4,10,24,.94), rgba(1,4,10,.985))}'
      + '#v4holo.open{display:block}'
      + '.v4h-canvas{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:grab}'
      + '.v4h-canvas.dragging{cursor:grabbing}'
      + '.v4h-scan{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(180deg, rgba(255,255,255,.03) 0 1px, transparent 1px 3px);mix-blend-mode:screen}'
      + '.v4h-panel{position:absolute;top:14px;right:14px;width:min(372px,92vw);max-height:min(78vh,660px);overflow:auto;color:#d8e6ff;background:rgba(8,16,34,.93);border:1px solid #3b5b8f;border-radius:12px;padding:14px 16px;font:13px/1.5 system-ui,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.5)}'
      + '.v4h-h{font-weight:700;letter-spacing:.04em;margin:2px 0 6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}'
      + '.v4h-sec{margin:10px 0;padding-top:8px;border-top:1px solid rgba(120,160,220,.25)}'
      + '.v4h-sec:first-child{border-top:none}'
      + '.v4h-line{margin:4px 0}'
      + '.v4h-dim{opacity:.72;font-size:12px}'
      + '.v4h-chip{font:600 10px/1.2 system-ui,sans-serif;padding:2px 7px;border-radius:999px;border:1px solid rgba(160,190,230,.4)}'
      + '.v4h-chip.ok{color:#8affc1;border-color:#2f7d4f;background:rgba(20,60,35,.6)}'
      + '.v4h-chip.warn{color:#ffd479;border-color:#8a6d2f;background:rgba(70,55,15,.5)}'
      + '.v4h-chip.bad{color:#ff9d9d;border-color:#8f3b3b;background:rgba(70,20,20,.5)}'
      + '.v4h-tbl{border-collapse:collapse;width:100%;font-size:12px}'
      + '.v4h-tbl th,.v4h-tbl td{border:1px solid rgba(120,160,220,.25);padding:4px 6px;text-align:left;vertical-align:top}'
      + '.v4h-tip{position:absolute;z-index:2;pointer-events:none;font:11px/1.4 system-ui,sans-serif;color:#eaf2ff;background:rgba(6,12,26,.92);border:1px solid rgba(140,170,220,.5);border-radius:8px;padding:5px 8px;max-width:300px;display:none}'
      + '.v4h-cap{position:absolute;left:14px;bottom:12px;font:11px/1.5 system-ui,sans-serif;color:rgba(216,230,255,.75);pointer-events:none;max-width:46ch}'
      + '.v4h-x{position:absolute;top:12px;left:12px;z-index:2;font:600 14px/1 system-ui,sans-serif;color:#d8e6ff;background:rgba(10,20,40,.9);border:1px solid #3b5b8f;border-radius:10px;padding:6px 12px;cursor:pointer}'
      + '.v4h-x:focus-visible{outline:2px solid #8fb8ff;outline-offset:2px}'
      + '.v4h-unsupported{color:#ff9d9d}'
      + '.v4h-foot{margin-top:12px;font-size:11px;opacity:.8;border-top:1px solid rgba(120,160,220,.25);padding-top:8px}';
    var st = document.createElement('style');
    st.id = 'v4h-style';
    st.textContent = css;
    document.head.appendChild(st);
  }

  function scoreFrac(o) {
    var m = /^([0-9]+)\s*\/\s*([0-9]+)$/.exec(String(o && o.score || ''));
    if (!m || !+m[2]) return 0;
    return Math.min(1, +m[1] / +m[2]);
  }

  function buildCells(data) {
    var out = [];
    var pinByFile = {};
    data.receipts.forEach(function (r) { pinByFile[r.pin.path.split('/').pop()] = r; });
    data.trees.forEach(function (t) {
      if (!t.ok) return;
      t.names.forEach(function (name) {
        var c = cellFor(name, t.dir);
        var pin = pinByFile[name];
        if (pin) {
          c.meta = pin;
          if (pin.ok && pin.valid) {
            c.col = [1.0, 0.78, 0.32];
            c.size = 5.4;
            c.pulse = 0.35 + scoreFrac(pin.receipt) * 0.65;
          } else {
            c.col = [0.55, 0.18, 0.18];
            c.size = 4.2;
            c.pulse = 0.10;
          }
        }
        out.push(c);
      });
    });
    for (var i = 0; i < 512; i++) {
      var t = (i / 512) * Math.PI * 2;
      var p = trefoil(t);
      out.push({ name: '(spine)', tree: 'spine', pos: p, col: [0.30, 0.24, 0.08], size: 1.25, pulse: 0.02, meta: null });
    }
    return out;
  }

  function panelHTML(data, webglOk) {
    var treeOk = data.trees.filter(function (t) { return t.ok; });
    var total = data.trees.reduce(function (a, t) { return a + t.count; }, 0);
    var measured = data.receipts.filter(function (r) { return r.ok && r.valid; });

    var h = '';
    h += '<div class="v4h-sec"><div class="v4h-h">Λ·HOLO — THE RECEIPT HOLOGRAM ' + (webglOk ? chip('LIVE', 'ok') : chip('UNSUPPORTED', 'bad')) + '</div>';
    h += '<div class="v4h-line">Every light cell is one receipt file in the public chain. Position, color and shimmer are deterministic functions of the file-name hash: <b>the same chain always renders the same organism</b> — the picture is the hash.</div>';
    h += '<div class="v4h-line v4h-dim">benchmark = cyan organ ring · receipts = green memory ring · mesh = violet halo · the six gold cells are the battery wave. Drag to orbit, scroll to zoom.</div>';
    h += '</div>';

    h += '<div class="v4h-sec"><div class="v4h-h">RECEIPT ORGANISM ' + (treeOk.length ? chip(treeOk.length + '/3 TREES MEASURED', 'ok') : chip('UNREACHABLE', 'bad')) + '</div>';
    if (treeOk.length) {
      h += '<div class="v4h-line">' + total + ' receipt cells live from ' + treeOk.map(function (t) { return t.dir + ' ' + t.count; }).join(' / ') + ' — counted and placed from the public chain.</div>';
    } else {
      h += '<div class="v4h-line">The chain is unreachable from this browser. Fail-closed: no cells are fabricated, the organism stays dark.</div>';
    }
    h += '<div class="v4h-line v4h-dim">Name-bound cells are not measurements — only the six pinned cells below carry a measured score, and their pulse is driven by it AS MEASURED.</div>';
    h += '</div>';

    h += '<div class="v4h-sec"><div class="v4h-h">BATTERY WAVE — GOLD CELLS ' + chip(measured.length + '/6 MEASURED', measured.length === 6 ? 'ok' : 'warn') + '</div>';
    h += '<table class="v4h-tbl"><tr><th>candidate</th><th>score</th><th>node / gpu</th></tr>';
    data.receipts.forEach(function (r) {
      if (r.ok && r.valid) {
        h += '<tr><td>' + esc(r.pin.label) + '</td><td>' + esc(r.receipt.score) + '</td><td>' + esc(head(r.receipt.node, 22)) + ' / ' + esc(head(r.receipt.gpu, 16)) + '</td></tr>';
      } else if (r.ok && !r.valid) {
        h += '<tr><td>' + esc(r.pin.label) + '</td><td colspan="2">' + chip('INVALID', 'bad') + ' fetched but failed the typed receipt contract</td></tr>';
      } else {
        h += '<tr><td>' + esc(r.pin.label) + '</td><td colspan="2">' + chip('UNREACHABLE', 'bad') + '</td></tr>';
      }
    });
    h += '</table>';
    h += '<div class="v4h-line v4h-dim">Scores AS MEASURED — 6 probes (3 answerable + 3 unanswerable). The battery is the gate, not the promotion: candidate promotion stays owner-gated.</div>';
    h += '</div>';

    h += '<div class="v4h-sec"><div class="v4h-h">FLEET ROSTER ' + chip('DECLARED', 'warn') + '</div>';
    ROSTER.forEach(function (r) {
      h += '<div class="v4h-line"><b>' + esc(r.lane) + '</b> — ' + esc(r.gpu) + ' — ' + esc(r.role) + '</div>';
    });
    h += '<div class="v4h-line v4h-dim">Roster entries are declared in source, not measured. Measured facts come from the receipts themselves.</div>';
    h += '</div>';

    h += '<div class="v4h-foot">Doctrine v11 LOCKED unchanged: locked-proven stays exactly 8. Λ = Conjecture 1. Handles only, read-only, no key sent. Fetched ' + esc(data.fetchedAt) + '.</div>';
    return h;
  }

  /* ---------------- WebGL2 core ------------------------------------------ */
  function compile(gl2, type, src) {
    var sh = gl2.createShader(type);
    gl2.shaderSource(sh, src);
    gl2.compileShader(sh);
    if (!gl2.getShaderParameter(sh, gl2.COMPILE_STATUS)) {
      throw new Error('shader: ' + gl2.getShaderInfoLog(sh));
    }
    return sh;
  }
  function program(gl2, vs, fs) {
    var p = gl2.createProgram();
    gl2.attachShader(p, compile(gl2, gl2.VERTEX_SHADER, vs));
    gl2.attachShader(p, compile(gl2, gl2.FRAGMENT_SHADER, fs));
    gl2.linkProgram(p);
    if (!gl2.getProgramParameter(p, gl2.LINK_STATUS)) {
      throw new Error('link: ' + gl2.getProgramInfoLog(p));
    }
    return p;
  }

  function startGL(canvas, cellList) {
    var gl2 = canvas.getContext('webgl2', { antialias: true, alpha: false });
    if (!gl2) return null;

    var pPoints = program(gl2, VS_POINTS, FS_POINTS);
    var pBack = program(gl2, VS_BACK, FS_BACK);

    var n = cellList.length;
    var stride = 9;
    var arr = new Float32Array(n * stride);
    for (var i = 0; i < n; i++) {
      var c = cellList[i];
      var o = i * stride;
      arr[o] = c.pos[0]; arr[o + 1] = c.pos[1]; arr[o + 2] = c.pos[2];
      arr[o + 3] = c.col[0]; arr[o + 4] = c.col[1]; arr[o + 5] = c.col[2];
      arr[o + 6] = c.size; arr[o + 7] = h01(c.h || 1, 9); arr[o + 8] = c.pulse;
    }
    var buf = gl2.createBuffer();
    gl2.bindBuffer(gl2.ARRAY_BUFFER, buf);
    gl2.bufferData(gl2.ARRAY_BUFFER, arr, gl2.STATIC_DRAW);

    var vao = gl2.createVertexArray();
    gl2.bindVertexArray(vao);
    gl2.bindBuffer(gl2.ARRAY_BUFFER, buf);
    gl2.enableVertexAttribArray(0);
    gl2.vertexAttribPointer(0, 3, gl2.FLOAT, false, stride * 4, 0);
    gl2.enableVertexAttribArray(1);
    gl2.vertexAttribPointer(1, 3, gl2.FLOAT, false, stride * 4, 12);
    gl2.enableVertexAttribArray(2);
    gl2.vertexAttribPointer(2, 3, gl2.FLOAT, false, stride * 4, 24);
    gl2.bindVertexArray(null);

    var vaoBack = gl2.createVertexArray();

    return {
      gl: gl2, n: n, vao: vao, vaoBack: vaoBack,
      pPoints: pPoints, pBack: pBack,
      uVP: gl2.getUniformLocation(pPoints, 'uVP'),
      uT: gl2.getUniformLocation(pPoints, 'uT'),
      uResB: gl2.getUniformLocation(pBack, 'uRes'),
      uTB: gl2.getUniformLocation(pBack, 'uT')
    };
  }

  function resize(canvas, gl2) {
    var dpr = Math.min(2, root.devicePixelRatio || 1);
    var w = Math.max(1, Math.floor(canvas.clientWidth * dpr));
    var h = Math.max(1, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
      gl2.viewport(0, 0, w, h);
    }
  }

  function drawFrame(state, tSec) {
    var gl2 = state.gl, canvas = state.canvas;
    resize(canvas, gl2);
    var asp = canvas.width / Math.max(1, canvas.height);
    var proj = persp(0.9, asp, 0.1, 40);
    var cp = Math.cos(cam.pitch), sp2 = Math.sin(cam.pitch);
    var eye = [cam.dist * cp * Math.sin(cam.yaw), cam.dist * sp2, cam.dist * cp * Math.cos(cam.yaw)];
    var view = lookAt(eye, [0, 0, 0], [0, 1, 0]);
    var vp = mul(proj, view);
    state.vp = vp;

    gl2.clearColor(0.008, 0.02, 0.05, 1);
    gl2.clear(gl2.COLOR_BUFFER_BIT);

    gl2.useProgram(state.pBack);
    gl2.bindVertexArray(state.vaoBack);
    gl2.uniform2f(state.uResB, canvas.width, canvas.height);
    gl2.uniform1f(state.uTB, tSec);
    gl2.drawArrays(gl2.TRIANGLES, 0, 3);

    gl2.useProgram(state.pPoints);
    gl2.bindVertexArray(state.vao);
    gl2.enable(gl2.BLEND);
    gl2.blendFunc(gl2.ONE, gl2.ONE);
    gl2.uniformMatrix4fv(state.uVP, false, vp);
    gl2.uniform1f(state.uT, tSec);
    gl2.drawArrays(gl2.POINTS, 0, state.n);
    gl2.disable(gl2.BLEND);
    gl2.bindVertexArray(null);
  }

  function projectCell(state, c, w, h) {
    var vp = state.vp;
    if (!vp) return null;
    var x = c.pos[0], y = c.pos[1], z = c.pos[2];
    var cx = vp[0] * x + vp[4] * y + vp[8] * z + vp[12];
    var cy = vp[1] * x + vp[5] * y + vp[9] * z + vp[13];
    var cw = vp[3] * x + vp[7] * y + vp[11] * z + vp[15];
    if (cw <= 0.01) return null;
    return [((cx / cw) * 0.5 + 0.5) * w, (1 - ((cy / cw) * 0.5 + 0.5)) * h];
  }

  function tipText(c) {
    if (c.tree === 'spine') return 'Λ spine — the trefoil the organism grows along (declared geometry)';
    if (c.meta) {
      if (c.meta.ok && c.meta.valid) return c.name + ' — ' + c.meta.receipt.score + ' AS MEASURED (' + head(c.meta.receipt.node, 24) + ')';
      if (c.meta.ok) return c.name + ' — INVALID: fetched but failed the typed receipt contract';
      return c.name + ' — UNREACHABLE from this browser (fail-closed)';
    }
    return c.name + ' — name-bound cell (' + c.tree + ' tree). Position = hash of the name; not a measurement.';
  }

  function closeHolo() {
    if (raf) { cancelAnimationFrame(raf); raf = 0; }
    if (overlay) { overlay.remove(); overlay = null; }
    if (btn) { btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
    cells = [];
    gl = null;
  }

  function openHolo() {
    ensureStyles();
    overlay = el('div', null);
    overlay.id = 'v4holo';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-label', 'Lambda HOLO v4 - the receipt hologram');
    var canvas = el('canvas', 'v4h-canvas');
    var scan = el('div', 'v4h-scan');
    tip = el('div', 'v4h-tip');
    var panelEl = el('div', 'v4h-panel');
    panelEl.innerHTML = '<div class="v4h-line">Loading the live receipt chain...</div>';
    var cap = el('div', 'v4h-cap', 'Λ·HOLO v4 — the receipt hologram. Every cell is one receipt. drag to orbit · scroll to zoom · ESC to close');
    var x = el('button', 'v4h-x', '× close');
    x.type = 'button';
    x.setAttribute('aria-label', 'Close the receipt hologram');
    x.addEventListener('click', closeHolo);
    overlay.appendChild(canvas);
    overlay.appendChild(scan);
    overlay.appendChild(tip);
    overlay.appendChild(panelEl);
    overlay.appendChild(cap);
    overlay.appendChild(x);
    document.body.appendChild(overlay);
    overlay.classList.add('open');
    btn.setAttribute('aria-expanded', 'true');
    x.focus();

    var state = { canvas: canvas, vp: null };
    var webglOk = true;

    loadHolo().then(function (data) {
      if (!overlay) return;
      cells = buildCells(data);
      try {
        var s = startGL(canvas, cells);
        if (!s) { webglOk = false; }
        else {
          gl = s.gl;
          state.n = s.n; state.vao = s.vao; state.vaoBack = s.vaoBack;
          state.pPoints = s.pPoints; state.pBack = s.pBack;
          state.uVP = s.uVP; state.uT = s.uT; state.uResB = s.uResB; state.uTB = s.uTB;
          state.gl = s.gl;
        }
      } catch (e) {
        webglOk = false;
      }
      panelEl.innerHTML = panelHTML(data, webglOk);
      if (!webglOk) {
        canvas.style.display = 'none';
        return;
      }
      var t0 = performance.now();
      var loop = function () {
        if (!overlay) return;
        var t = (performance.now() - t0) / 1000;
        if (!reduceMotion && !drag && performance.now() - idleAt > 4000) { cam.yaw += 0.0016; }
        drawFrame(state, reduceMotion ? 0 : t);
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
    }).catch(function (e) {
      if (!overlay) return;
      panelEl.innerHTML = '<div class="v4h-line">' + chip('UNREACHABLE', 'bad') + ' The receipt chain could not be read from this browser. Fail-closed: nothing is rendered that was not measured. (' + esc(String(e && e.message || e)) + ')</div>';
    });

    var px = 0, py = 0;
    canvas.addEventListener('pointerdown', function (ev) {
      drag = { x: ev.clientX, y: ev.clientY, yaw: cam.yaw, pitch: cam.pitch };
      canvas.classList.add('dragging');
      canvas.setPointerCapture && canvas.setPointerCapture(ev.pointerId);
    });
    canvas.addEventListener('pointermove', function (ev) {
      if (drag) {
        cam.yaw = drag.yaw + (ev.clientX - drag.x) * 0.006;
        cam.pitch = Math.max(-1.35, Math.min(1.35, drag.pitch + (ev.clientY - drag.y) * 0.005));
      }
      px = ev.clientX; py = ev.clientY;
      idleAt = performance.now();
      if (!tip || !cells.length || !state.gl) return;
      var w = canvas.clientWidth, h = canvas.clientHeight;
      var best = null, bd = 18 * 18;
      for (var i = 0; i < cells.length; i++) {
        var p = projectCell(state, cells[i], w, h);
        if (!p) continue;
        var dx = p[0] - px, dy = p[1] - py;
        var d2 = dx * dx + dy * dy;
        if (d2 < bd) { bd = d2; best = cells[i]; }
      }
      if (best) {
        tip.style.display = 'block';
        tip.style.left = Math.min(px + 14, w - 220) + 'px';
        tip.style.top = Math.max(8, py - 34) + 'px';
        tip.textContent = tipText(best);
      } else {
        tip.style.display = 'none';
      }
    });
    var endDrag = function () { drag = null; canvas.classList.remove('dragging'); idleAt = performance.now(); };
    canvas.addEventListener('pointerup', endDrag);
    canvas.addEventListener('pointerleave', function () { endDrag(); if (tip) tip.style.display = 'none'; });
    canvas.addEventListener('wheel', function (ev) {
      ev.preventDefault();
      cam.dist = Math.max(2.4, Math.min(10, cam.dist * (1 + (ev.deltaY > 0 ? 0.08 : -0.08))));
      idleAt = performance.now();
    }, { passive: false });
    canvas.addEventListener('dblclick', function () { cam = { yaw: 0.6, pitch: 0.35, dist: 5.4 }; });
    canvas.addEventListener('webglcontextlost', function (ev) { ev.preventDefault(); if (raf) cancelAnimationFrame(raf); raf = 0; });
  }

  function mount() {
    if (document.getElementById('v4h-btn')) return;
    ensureStyles();
    btn = el('button', 'v4h-btn', 'Λ · HOLO v4');
    btn.id = 'v4h-btn';
    btn.type = 'button';
    btn.setAttribute('aria-controls', 'v4holo');
    btn.setAttribute('aria-expanded', 'false');
    btn.title = 'Lambda HOLO v4 - the receipt hologram: the public chain rendered as a living organism, deterministic from the hash';
    btn.addEventListener('click', function () { if (overlay) closeHolo(); else openHolo(); });
    document.body.appendChild(btn);
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && overlay) { closeHolo(); }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }

  root.SZLHoloV4 = { loadHolo: loadHolo, panelHTML: panelHTML, cellFor: cellFor, fnv1a: fnv1a };
}(typeof window !== 'undefined' ? window : this));
