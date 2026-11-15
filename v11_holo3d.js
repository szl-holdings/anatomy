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
    const res = await fetch(url, {
      headers: { accept: "application/json" },
      redirect: "error",
      credentials: "same-origin",
      cache: "no-store",
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  function acceptHandles(payload) {
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
    const rows = Array.isArray(payload)
      ? payload
      : Array.isArray(payload && (payload.formulas || payload.loops || payload.items))
        ? payload.formulas || payload.loops || payload.items
        : [];
    return rows.filter((h) => h && typeof h === "object" && (h.nodeId || h.id || h.name));
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

  async function build() {
    if (state.built || state.building) return;
    state.building = true;
    try {
      const [status, handles, formulas, loops] = await Promise.all([
        fetchJson(ENDPOINTS.status).catch(() => null),
        fetchJson(ENDPOINTS.handles),
        fetchJson(ENDPOINTS.formulas),
        fetchJson(ENDPOINTS.loops),
      ]);
      state.feeds.status = status;
      state.feeds.handles = acceptHandles(handles);
      state.feeds.formulas = acceptRows(formulas);
      state.feeds.loops = acceptRows(loops);
      if (!state.feeds.handles.length && !state.feeds.formulas.length && !state.feeds.loops.length) {
        throw new Error("no accepted handles");
      }
      if (!buildScene()) throw new Error("renderer unavailable");
      state.built = true;
      chip("handles " + state.feeds.handles.length, "ok");
      chip("formulas " + state.feeds.formulas.length, "ok");
      chip("loops " + state.feeds.loops.length, "ok");
      chip("PROCEDURAL LAYOUT — handles only; positions illustrative, not measured", "note");
    } catch (err) {
      const off = $(OFFLINE_ID);
      if (off) off.hidden = false;
      chip("CHAIN UNREACHABLE — failing closed", "off");
    } finally {
      state.building = false;
    }
  }

  function openPanel() {
    const panel = $(PANEL_ID);
    if (!panel) return;
    state.open = true;
    state.lastFocus = document.activeElement;
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    void build().then(() => {
      sizeRenderer();
      cancelAnimationFrame(state.raf);
      state.raf = requestAnimationFrame(frame);
    });
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
        const focusables = [closeBtn, $(CANVAS_ID)].filter(Boolean);
        const idx = focusables.indexOf(document.activeElement);
        e.preventDefault();
        const next = e.shiftKey
          ? focusables[(idx - 1 + focusables.length) % focusables.length]
          : focusables[(idx + 1) % focusables.length];
        if (next) next.focus({ preventScroll: true });
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
