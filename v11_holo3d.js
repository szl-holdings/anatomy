// SPDX-License-Identifier: Apache-2.0
// Living Anatomy Holographic v11 (holo3d) — fully 3D holographic constellation of the
// governed frontier, rendered same-origin from the repo-vendored three.min.js.
// Doctrine: handles only (SAFE_HANDLE / HANDLES_ONLY — candidate text never crosses
// the public API); procedural layout is ILLUSTRATIVE, never claimed as measured
// topology; fails closed when the chain is unreachable; same-origin, non-persistent.
// Leader patterns leveraged (2026-11-15 sweep): spatial-hud instanced-particle GLSL,
// HOLO.SYS scanline+fresnel holo shaders, Brain-Storm measured-vs-rendered labelling.
(() => {
  "use strict";

  const ORIGIN = window.location.origin;
  const FAB_ID = "v11-holo-fab";
  const PANEL_ID = "v11-holo";
  const CANVAS_ID = "v11-holo-canvas";
  const TIP_ID = "v11-holo-tip";
  const HUD_ID = "v11-holo-hud";
  const OFFLINE_ID = "v11-holo-offline";

  const ENDPOINTS = Object.freeze({
    status: "/api/anatomy/v1/holographic-v7",
    handles: "/api/anatomy/v1/frontier/handles?q=second%20brain%20anatomy%20evidence%20receipts&k=24",
    formulas: "/api/anatomy/v1/frontier/formulas?k=48",
    loops: "/api/anatomy/v1/frontier/ouroboros?k=24",
  });

  const SAFE_HANDLE = /^frontier:[0-9a-f]{32}$/;
  const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const state = {
    built: false,
    building: false,
    open: false,
    feeds: { handles: [], formulas: [], loops: [], status: null },
    raf: 0,
    renderer: null,
    scene: null,
    camera: null,
    group: null,
    nodes: [],
    rotX: 0.18,
    rotY: 0,
    zoom: 14,
    dragging: false,
    lastX: 0,
    lastY: 0,
    lastFocus: null,
    resizeObserver: null,
    feedUnavailable: [],
    sourceReady: false,
  };

  const $ = (id) => document.getElementById(id);
  const shortDigest = (v, w = 12) => {
    const t = String(v ?? "");
    return SAFE_HANDLE.test(t) ? t.slice(9, 9 + w) + "…" : "UNAVAILABLE";
  };

  function chip(text, cls) {
    const hud = $(HUD_ID);
    if (!hud) return;
    const span = document.createElement("span");
    span.className = "v11-chip" + (cls ? " " + cls : "");
    span.textContent = text;
    hud.appendChild(span);
  }

  async function fetchJson(url) {
    // Same-origin only: relative paths on this origin; anything else is rejected.
    if (!(url.startsWith("/") && !url.startsWith("//")) && !url.startsWith(ORIGIN)) {
      throw new Error("CROSS_ORIGIN_REJECTED");
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 9000);
    try {
      const res = await fetch(url, {
        headers: { accept: "application/json" },
        redirect: "error",
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      if (!res.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
        throw new Error("NOT_JSON");
      }
      return await res.json();
    } finally {
      window.clearTimeout(timer);
    }
  }

  function acceptHandles(payload) {
    if (!payload || payload.ready !== true || payload.content_access !== "HANDLES_ONLY") return [];
    const rows = Array.isArray(payload)
      ? payload
      : Array.isArray(payload && (payload.handles || payload.items || payload.results))
        ? payload.handles || payload.items || payload.results
        : [];
    return rows.filter((h) => h && typeof h === "object" &&
      SAFE_HANDLE.test(String(h.nodeId ?? "")) &&
      String(h.contentAccess ?? "") === "HANDLES_ONLY");
  }

  function acceptRows(payload) {
    if (!payload || payload.ready !== true || payload.content_access !== "HANDLES_ONLY") return [];
    // The live formulas + Ouroboros APIs use the same handles[] envelope as the
    // Brain search API, not separate formulas[]/loops[] arrays. Reuse the exact
    // safe-handle predicate so no free-form source text can enter the renderer.
    return acceptHandles(payload);
  }

  function fib(i, n, r) {
    const phi = Math.acos(1 - 2 * (i + 0.5) / n);
    const th = Math.PI * (1 + Math.sqrt(5)) * (i + 0.5);
    return [r * Math.sin(phi) * Math.cos(th), r * Math.cos(phi) * 0.72, r * Math.sin(phi) * Math.sin(th)];
  }

  function buildScene() {
    const canvas = $(CANVAS_ID);
    if (!canvas || !window.THREE) return false;
    state.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    state.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    state.scene = new THREE.Scene();
    state.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
    state.camera.position.set(0, 0.6, state.zoom);
    state.group = new THREE.Group();
    state.scene.add(state.group);

    const TEAL = new THREE.Color(0x5ad1ff), GOLD = new THREE.Color(0xffd166), ROSE = new THREE.Color(0xff5d8f);
    const rows = [
      ...state.feeds.handles.map((h) => ({ t: "handle", id: h.nodeId })),
      ...state.feeds.formulas.map((h) => ({ t: "formula", id: h.nodeId || h.id || h.name })),
      ...state.feeds.loops.map((h) => ({ t: "loop", id: h.nodeId || h.id || h.name })),
    ];
    if (!rows.length) return false;
    const n = rows.length;
    const pos = new Float32Array(n * 3), seed = new Float32Array(n);
    rows.forEach((row, i) => {
      const p = fib(i, n, 5.4);
      pos[i * 3] = p[0]; pos[i * 3 + 1] = p[1]; pos[i * 3 + 2] = p[2];
      seed[i] = Math.random();
      state.nodes.push({ row, p });
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("aSeed", new THREE.BufferAttribute(seed, 1));
    const mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 }, uTeal: { value: TEAL }, uGold: { value: GOLD }, uRose: { value: ROSE }, uSize: { value: 3.4 } },
      vertexShader:
        "attribute float aSeed; uniform float uTime; uniform float uSize; varying float vSeed; varying vec3 vPos;" +
        "void main(){ vSeed=aSeed; vPos=position; vec4 mv=modelViewMatrix*vec4(position,1.0);" +
        "float w=0.75+0.25*sin(uTime*2.0+aSeed*6.2831); gl_PointSize=uSize*w*(130.0/max(0.001,-mv.z)); gl_Position=projectionMatrix*mv; }",
      fragmentShader:
        "uniform float uTime; uniform vec3 uTeal; uniform vec3 uGold; uniform vec3 uRose; varying float vSeed; varying vec3 vPos;" +
        "void main(){ vec2 c=gl_PointCoord-0.5; float d=length(c); float a=smoothstep(0.5,0.04,d);" +
        "float scan=0.82+0.18*sin(vPos.y*9.0-uTime*5.0);" +
        "vec3 col=vSeed<0.5?mix(uTeal,uGold,vSeed*2.0):mix(uGold,uRose,(vSeed-0.5)*2.0);" +
        "float alpha=a*scan*(0.55+0.45*sin(uTime*1.7+vSeed*12.566));" +
        "if(alpha<0.015) discard; gl_FragColor=vec4(col,alpha); }",
    });
    state.group.add(new THREE.Points(geo, mat));

    const lp = [];
    for (let i = 0; i < n - 1; i++) {
      lp.push(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2], pos[(i + 1) * 3], pos[(i + 1) * 3 + 1], pos[(i + 1) * 3 + 2]);
    }
    const lg = new THREE.BufferGeometry();
    lg.setAttribute("position", new THREE.BufferAttribute(new Float32Array(lp), 3));
    state.group.add(new THREE.LineSegments(lg, new THREE.LineBasicMaterial({
      color: 0x5ad1ff, transparent: true, opacity: 0.14, blending: THREE.AdditiveBlending })));
    state.group.add(new THREE.Mesh(new THREE.IcosahedronGeometry(6.6, 1),
      new THREE.MeshBasicMaterial({ color: 0x5ad1ff, wireframe: true, transparent: true, opacity: 0.05 })));
    return true;
  }

  function sizeRenderer() {
    const panel = $(PANEL_ID), canvas = $(CANVAS_ID);
    if (!panel || !canvas || !state.renderer) return;
    const w = panel.clientWidth, h = panel.clientHeight;
    state.renderer.setSize(w, h, false);
    state.camera.aspect = Math.max(0.2, w / Math.max(1, h));
    state.camera.position.set(0, 0.6, state.zoom);
    state.camera.updateProjectionMatrix();
  }

  const ray = window.THREE ? new THREE.Raycaster() : null;
  const mouse = { x: 0, y: 0 };
  function onMove(e) {
    const panel = $(PANEL_ID);
    if (!panel) return;
    const r = panel.getBoundingClientRect();
    mouse.x = ((e.clientX - r.left) / Math.max(1, r.width)) * 2 - 1;
    mouse.y = -((e.clientY - r.top) / Math.max(1, r.height)) * 2 + 1;
  }

  function frame(now) {
    if (!state.open || !state.renderer) return;
    const t = now / 1000;
    if (!REDUCED_MOTION && !state.dragging) state.rotY += 0.0022;
    state.group.rotation.y = state.rotY;
    state.group.rotation.x = state.rotX;
    const pts = state.group.children[0];
    if (pts && pts.material && pts.material.uniforms) pts.material.uniforms.uTime.value = t;
    if (ray && state.nodes.length) {
      ray.setFromCamera(mouse, state.camera);
      const hits = ray.intersectObject(pts);
      const tip = $(TIP_ID);
      if (hits.length && tip) {
        const node = state.nodes[hits[0].index];
        if (node) {
          tip.textContent = node.row.t.toUpperCase() + " · " + shortDigest(node.row.id);
          tip.style.left = (((mouse.x * 0.5) + 0.5) * 100) + "%";
          tip.style.top = (((-mouse.y * 0.5) + 0.5) * 100) + "%";
          tip.style.opacity = 1;
        }
      } else if (tip) tip.style.opacity = 0;
    }
    state.renderer.render(state.scene, state.camera);
    state.raf = requestAnimationFrame(frame);
  }

  // Only public handle IDs and aggregate counts are used in this DOM fallback.
  // Missing WebGL is a *renderer* condition, never an outage of the source chain.
  function showFallback(code) {
    const panel = $(PANEL_ID);
    const stage = panel?.querySelector(".stage");
    if (!stage) return;
    let region = $("v11-holo-fallback");
    if (!region) {
      region = document.createElement("div");
      region.id = "v11-holo-fallback";
      region.setAttribute("role", "region");
      region.setAttribute("aria-label", "Holographic source evidence without WebGL");
      stage.appendChild(region);
    }
    region.replaceChildren();
    const heading = document.createElement("strong");
    heading.textContent = code === "RENDERER_UNAVAILABLE"
      ? "3D rendering unavailable; observed read-only source handles remain accessible"
      : code === "SOURCE_STATUS_HOLD"
        ? "Source status unverified; showing no operational green"
        : "Source handle feeds unavailable; no data fabricated";
    region.appendChild(heading);
    const summary = document.createElement("p");
    summary.textContent = "Read-only review memory · handles " + state.feeds.handles.length
      + " · formulas " + state.feeds.formulas.length
      + " · loops " + state.feeds.loops.length
      + " · inaccessible feeds " + state.feedUnavailable.join(", ");
    region.appendChild(summary);
    const evidence = document.createElement("p");
    evidence.textContent = "Candidate content and private graph remain controller-only. No training, model, or production claim.";
    region.appendChild(evidence);
    const sample = document.createElement("ul");
    for (const handle of state.feeds.handles.slice(0, 12)) {
      const li = document.createElement("li");
      li.textContent = String(handle.nodeId); // exact SAFE_HANDLE-filtered ID only
      sample.appendChild(li);
    }
    region.appendChild(sample);
    const source = document.createElement("a");
    source.href = ENDPOINTS.handles;
    source.textContent = "Inspect same-origin source handles";
    region.appendChild(source);
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "Retry source + renderer";
    retry.addEventListener("click", () => {
      if (state.building) return;
      state.built = false;
      region.hidden = true;
      // A successful retry must actually start the recovered 3D renderer.
      void build().then(resumeRenderer);
    });
    region.appendChild(retry);
    region.hidden = false;
  }

  async function build() {
    if (state.built || state.building) return;
    state.building = true;
    state.feeds = { status: null, handles: [], formulas: [], loops: [] };
    state.feedUnavailable = [];
    $(HUD_ID)?.replaceChildren();
    const offline = $(OFFLINE_ID);
    if (offline) offline.hidden = true;
    const prior = $("v11-holo-fallback");
    if (prior) prior.hidden = true;
    try {
      const labels = ["status", "handles", "formulas", "loops"];
      const endpoints = [ENDPOINTS.status, ENDPOINTS.handles, ENDPOINTS.formulas, ENDPOINTS.loops];
      // One failed optional feed must not take a healthy Second Brain down.
      const results = await Promise.allSettled(endpoints.map((url) => fetchJson(url)));
      const values = results.map((item, index) => {
        if (item.status === "fulfilled") return item.value;
        state.feedUnavailable.push(labels[index]);
        return null;
      });
      const [status, handles, formulas, loops] = values;
      // A 200 response with a failed/non-handle source contract is not a
      // healthy feed. Keep other independently valid source feeds available.
      for (let i = 1; i < values.length; i++) {
        if (results[i].status === "fulfilled" &&
            (!values[i] || values[i].ready !== true ||
              values[i].content_access !== "HANDLES_ONLY")) {
          state.feedUnavailable.push(labels[i]);
        }
      }
      if (results[0].status === "rejected") {
        if (offline) {
          offline.hidden = false;
          offline.textContent = "SOURCE STATUS UNAVAILABLE — failing closed";
        }
        chip("SOURCE FEEDS UNAVAILABLE — no invented data", "off");
        showFallback("SOURCE_FEEDS_UNAVAILABLE");
        return;
      }
      state.feeds.status = status;
      state.feeds.handles = acceptHandles(handles);
      state.feeds.formulas = acceptRows(formulas);
      state.feeds.loops = acceptRows(loops);
      const ready = Boolean(status?.ready === true && status?.frontier?.ready === true);
      state.sourceReady = ready;
      if (!ready) {
        // The status gate is authoritative: discard independently received
        // handles rather than showing them under an unverified source.
        state.feeds = { status, handles: [], formulas: [], loops: [] };
        chip("SOURCE STATUS HOLD — not production proof", "off");
        showFallback("SOURCE_STATUS_HOLD");
        state.built = true;
        return;
      }
      const available = state.feeds.handles.length + state.feeds.formulas.length + state.feeds.loops.length;
      if (!available) throw new Error("SOURCE_FEEDS_UNAVAILABLE");
      if (state.feedUnavailable.length) {
        chip("DEGRADED SOURCE FEEDS: " + state.feedUnavailable.join(", "), "off");
      }
      try {
        if (!buildScene()) throw new Error("RENDERER_UNAVAILABLE");
      } catch (_rendererError) {
        if (state.renderer) {
          try { state.renderer.dispose(); } catch (_) {}
        }
        state.renderer = null;
        state.nodes = [];
        state.group = null;
        showFallback("RENDERER_UNAVAILABLE");
        chip("3D RENDERER UNAVAILABLE — read-only evidence fallback", "note");
        state.built = true;
        return;
      }
      state.built = true;
      chip("handles " + state.feeds.handles.length, "ok");
      chip("formulas " + state.feeds.formulas.length, "ok");
      chip("loops " + state.feeds.loops.length, "ok");
      chip("REVIEW MEMORY ONLY — not model or release readiness", "note");
      chip("PROCEDURAL LAYOUT — handles only; positions illustrative, not measured", "note");
    } catch (_error) {
      if (offline) {
        offline.hidden = false;
        offline.textContent = "SOURCE HANDLES UNAVAILABLE — failing closed";
      }
      chip("SOURCE FEEDS UNAVAILABLE — no invented data", "off");
      showFallback("SOURCE_FEEDS_UNAVAILABLE");
    } finally {
      state.building = false;
    }
  }

  function resumeRenderer() {
    if (!state.open || !state.renderer) return;
    sizeRenderer();
    cancelAnimationFrame(state.raf);
    state.raf = requestAnimationFrame(frame);
  }

  function openPanel() {
    const panel = $(PANEL_ID);
    if (!panel) return;
    state.open = true;
    state.lastFocus = document.activeElement;
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    void build().then(resumeRenderer);
    const closeBtn = $("v11-holo-close");
    if (closeBtn) closeBtn.focus({ preventScroll: true });
  }

  function closePanel() {
    const panel = $(PANEL_ID);
    if (!panel) return;
    state.open = false;
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
    cancelAnimationFrame(state.raf);
    if (state.lastFocus && document.body.contains(state.lastFocus)) {
      state.lastFocus.focus({ preventScroll: true });
    }
  }

  function wire() {
    const fab = $(FAB_ID);
    const panel = $(PANEL_ID);
    if (!fab || !panel) return;
    fab.addEventListener("click", () => (state.open ? closePanel() : openPanel()));
    $("v11-holo-close").addEventListener("click", closePanel);
    panel.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { closePanel(); return; }
      if (e.key === "Tab") {
        const closeBtn = $("v11-holo-close");
        // When WebGL is unavailable, the evidence link and retry button
        // must be reachable by keyboard; the hidden canvas is not useful.
        const fallback = $("v11-holo-fallback");
        const controls = fallback && !fallback.hidden
          ? Array.from(fallback.querySelectorAll("a[href], button:not([disabled])"))
          : [$(CANVAS_ID)];
        const focusables = [closeBtn, ...controls].filter(Boolean);
        if (!focusables.length) return;
        const idx = focusables.indexOf(document.activeElement);
        e.preventDefault();
        const next = idx < 0
          ? (e.shiftKey ? focusables[focusables.length - 1] : focusables[0])
          : e.shiftKey
            ? focusables[(idx - 1 + focusables.length) % focusables.length]
            : focusables[(idx + 1) % focusables.length];
        next.focus({ preventScroll: true });
      }
    });
    const canvas = $(CANVAS_ID);
    canvas.addEventListener("pointerdown", (e) => {
      state.dragging = true; state.lastX = e.clientX; state.lastY = e.clientY;
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener("pointerup", (e) => {
      state.dragging = false;
      try { canvas.releasePointerCapture(e.pointerId); } catch (_) {}
    });
    canvas.addEventListener("pointermove", (e) => {
      onMove(e);
      if (!state.dragging) return;
      state.rotY += (e.clientX - state.lastX) * 0.005;
      state.rotX = Math.max(-1.2, Math.min(1.2, state.rotX + (e.clientY - state.lastY) * 0.005));
      state.lastX = e.clientX; state.lastY = e.clientY;
    });
    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      state.zoom = Math.max(7, Math.min(26, state.zoom + e.deltaY * 0.01));
      if (state.camera) state.camera.position.set(0, 0.6, state.zoom);
    }, { passive: false });
    if (typeof ResizeObserver === "function") {
      state.resizeObserver = new ResizeObserver(() => { if (state.open) sizeRenderer(); });
      state.resizeObserver.observe(panel);
    } else {
      window.addEventListener("resize", () => { if (state.open) sizeRenderer(); });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire, { once: true });
  } else {
    wire();
  }
})();