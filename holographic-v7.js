// SPDX-License-Identifier: Apache-2.0
// Living Anatomy Holographic v7 — same-origin, handles-only Brain/Formula/Loop HUD.
// Candidate text never crosses the public API. This client renders source handles,
// revision receipts, quant domains, and review-state topology only.
(() => {
  "use strict";

  const ROOT_ID = "szl-v7-hud";
  const LAUNCHER_ID = "szl-v7-launcher";
  const GRAPH_ID = "szl-v7-graph";
  const ENDPOINTS = Object.freeze({
    status: "/api/anatomy/v1/holographic-v7",
    brain: "/api/anatomy/v1/frontier/handles?q=second%20brain%20anatomy%20evidence%20receipts&k=24",
    formulas: "/api/anatomy/v1/frontier/formulas?k=48",
    loops: "/api/anatomy/v1/frontier/ouroboros?k=24",
  });
  const TABS = Object.freeze([
    { id: "brain", label: "Brain" },
    { id: "formulas", label: "Formula atlas" },
    { id: "quant", label: "Quant domains" },
    { id: "loops", label: "Ouroboros loops" },
  ]);
  const SAFE_HANDLE = /^frontier:[0-9a-f]{32}$/;
  const SAFE_SHA = /^[0-9a-f]{40,64}$/;
  const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)");

  const state = {
    open: false,
    activeTab: "brain",
    status: null,
    feeds: {
      brain: null,
      formulas: null,
      loops: null,
    },
    loading: false,
    lastFocus: null,
    pollTimer: null,
    graphFrame: 0,
    graphObserver: null,
  };

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const shortDigest = (value, width = 14) => {
    const text = String(value ?? "");
    if (!SAFE_SHA.test(text)) return "UNAVAILABLE";
    return `${text.slice(0, width)}…${text.slice(-6)}`;
  };

  const compactRepository = (value) => {
    const text = String(value ?? "");
    return text.startsWith("szl-holdings/") ? text.slice("szl-holdings/".length) : text;
  };

  const acceptedHandle = (handle) => {
    if (!handle || typeof handle !== "object") return false;
    if (!SAFE_HANDLE.test(String(handle.nodeId ?? ""))) return false;
    if (String(handle.contentAccess ?? "") !== "HANDLES_ONLY") return false;
    if (String(handle.candidateState ?? "") !== "DISCOVERED_REVIEW_REQUIRED") return false;
    if (String(handle.authority ?? "NONE") !== "NONE") return false;
    return true;
  };

  const boundedHandles = (payload) => {
    if (!payload || typeof payload !== "object") return [];
    if (payload.content_access !== "HANDLES_ONLY") return [];
    if (!Array.isArray(payload.handles)) return [];
    return payload.handles.filter(acceptedHandle).slice(0, 48);
  };

  async function fetchJson(path) {
    const url = new URL(path, window.location.origin);
    if (url.origin !== window.location.origin) {
      throw new Error("CROSS_ORIGIN_REJECTED");
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 9000);
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP_${response.status}`);
      const value = await response.json();
      if (!value || typeof value !== "object" || Array.isArray(value)) {
        throw new Error("INVALID_JSON_OBJECT");
      }
      return value;
    } finally {
      window.clearTimeout(timer);
    }
  }

  function createMarkup() {
    const launcher = document.createElement("button");
    launcher.id = LAUNCHER_ID;
    launcher.type = "button";
    launcher.setAttribute("aria-controls", ROOT_ID);
    launcher.setAttribute("aria-expanded", "false");
    launcher.setAttribute("aria-label", "Open Living Anatomy holographic v7");
    launcher.textContent = "Brain v7";

    const hud = document.createElement("section");
    hud.id = ROOT_ID;
    hud.hidden = true;
    hud.setAttribute("role", "dialog");
    hud.setAttribute("aria-modal", "true");
    hud.setAttribute("aria-labelledby", "szl-v7-title");
    hud.setAttribute("aria-describedby", "szl-v7-subtitle");
    hud.innerHTML = `
      <button class="szl-v7__dismiss" type="button" tabindex="-1" aria-label="Close holographic v7"></button>
      <article class="szl-v7__panel">
        <div class="szl-v7__content">
          <header class="szl-v7__header">
            <div>
              <p class="szl-v7__eyebrow">Source-bound living substrate · v7</p>
              <h2 class="szl-v7__title" id="szl-v7-title">Brain, formulas and loops—one observable body.</h2>
              <p class="szl-v7__subtitle" id="szl-v7-subtitle">Exact public source handles and review-state receipts. No candidate content, private graph, weight training or execution authority.</p>
            </div>
            <button class="szl-v7__close" type="button" aria-label="Close holographic v7">×</button>
          </header>
          <div class="szl-v7__status-grid" aria-label="Holographic v7 status">
            <div class="szl-v7__metric"><span class="szl-v7__metric-label">Second Brain</span><strong class="szl-v7__metric-value" data-metric="brain">Loading</strong></div>
            <div class="szl-v7__metric"><span class="szl-v7__metric-label">Attributed math</span><strong class="szl-v7__metric-value" data-metric="formula">—</strong></div>
            <div class="szl-v7__metric"><span class="szl-v7__metric-label">Quant domains</span><strong class="szl-v7__metric-value" data-metric="quant">—</strong></div>
            <div class="szl-v7__metric"><span class="szl-v7__metric-label">Authority</span><strong class="szl-v7__metric-value" data-metric="authority">Read only</strong></div>
          </div>
          <div class="szl-v7__graph-shell">
            <canvas id="${GRAPH_ID}" role="img" aria-label="Source-handle topology linking Second Brain, formula authority, quant domains and Ouroboros review loops"></canvas>
            <div class="szl-v7__graph-label">Review-state topology</div>
          </div>
          <div class="szl-v7__stream">
            <nav class="szl-v7__tabs" role="tablist" aria-label="Holographic v7 instruments">
              ${TABS.map((tab, index) => `<button class="szl-v7__tab" type="button" role="tab" id="szl-v7-tab-${tab.id}" aria-controls="szl-v7-panel-${tab.id}" aria-selected="${index === 0}" tabindex="${index === 0 ? 0 : -1}" data-tab="${tab.id}">${escapeHtml(tab.label)}</button>`).join("")}
            </nav>
            <section id="szl-v7-panel" role="tabpanel" aria-labelledby="szl-v7-tab-brain" tabindex="0">
              <div class="szl-v7__empty">Opening the exact source-bound instrument…</div>
            </section>
          </div>
          <footer class="szl-v7__footer">
            <span><i class="szl-v7__live-dot" data-live-dot></i><span data-live-label>Loading exact receipt</span></span>
            <span class="szl-v7__digest" data-digest>Candidate set: UNAVAILABLE</span>
          </footer>
        </div>
      </article>`;

    document.body.append(launcher, hud);
    return { launcher, hud };
  }

  function metric(name, value, status = "") {
    const element = document.querySelector(`[data-metric="${name}"]`);
    if (!element) return;
    element.textContent = String(value);
    if (status) element.dataset.state = status;
    else delete element.dataset.state;
  }

  function updateStatusUi() {
    const hud = document.getElementById(ROOT_ID);
    if (!hud) return;
    const payload = state.status;
    const frontier = payload && typeof payload.frontier === "object" ? payload.frontier : null;
    const formula = frontier && typeof frontier.formula_atlas === "object" ? frontier.formula_atlas : null;
    const ready = Boolean(payload?.ready && frontier?.ready);

    metric("brain", ready ? `${frontier.candidate_count ?? 0} handles` : "Unavailable", ready ? "live" : "warn");
    metric("formula", ready ? `${formula?.attributed_formula_count ?? 0} + ${formula?.executable_formula_count ?? 0}` : "—", ready ? "live" : "warn");
    metric("quant", ready ? `${formula?.quant_domain_count ?? 0} domains` : "—", ready ? "live" : "warn");
    metric("authority", ready ? "Read only" : "Held", ready ? "live" : "warn");

    const liveDot = hud.querySelector("[data-live-dot]");
    const liveLabel = hud.querySelector("[data-live-label]");
    const digest = hud.querySelector("[data-digest]");
    if (liveDot) liveDot.dataset.state = ready ? "live" : "offline";
    if (liveLabel) liveLabel.textContent = ready ? "Exact snapshot loaded · review required" : "Snapshot unavailable · no green synthesized";
    if (digest) digest.textContent = `Candidate set: ${shortDigest(frontier?.candidate_set_sha256)}`;
  }

  function renderCard(handle) {
    const domain = handle.quantDomain ? `<span>${escapeHtml(handle.quantDomain)}</span>` : "";
    return `
      <article class="szl-v7__card">
        <div>
          <h3 class="szl-v7__card-title">${escapeHtml(handle.title || handle.nodeId)}</h3>
          <div class="szl-v7__card-meta">
            <span>${escapeHtml(compactRepository(handle.repository))}</span>
            <span>${escapeHtml(handle.kind)}</span>
            ${domain}
            <span>${escapeHtml(shortDigest(handle.revision, 9))}</span>
            <span>${escapeHtml(shortDigest(handle.sha256, 9))}</span>
          </div>
        </div>
        <span class="szl-v7__tag">Review required</span>
      </article>`;
  }

  function quantGroups(handles) {
    const groups = new Map();
    for (const handle of handles) {
      const domain = String(handle.quantDomain || "unclassified_reference");
      const current = groups.get(domain) || [];
      current.push(handle);
      groups.set(domain, current);
    }
    return [...groups.entries()].sort(([left], [right]) => left.localeCompare(right));
  }

  function activeHandles() {
    if (state.activeTab === "brain") return boundedHandles(state.feeds.brain);
    if (state.activeTab === "formulas" || state.activeTab === "quant") return boundedHandles(state.feeds.formulas);
    if (state.activeTab === "loops") return boundedHandles(state.feeds.loops);
    return [];
  }

  function renderPanel() {
    const panel = document.getElementById("szl-v7-panel");
    if (!panel) return;
    const selectedTab = TABS.find((tab) => tab.id === state.activeTab) || TABS[0];
    panel.setAttribute("aria-labelledby", `szl-v7-tab-${selectedTab.id}`);

    if (state.loading) {
      panel.innerHTML = '<div class="szl-v7__empty">Resolving same-origin source handles and digest receipts…</div>';
      return;
    }
    const handles = activeHandles();
    if (!handles.length) {
      panel.innerHTML = '<div class="szl-v7__empty">No verified handles are available for this instrument. The view remains unavailable rather than inventing data.</div>';
      return;
    }
    if (state.activeTab === "quant") {
      panel.innerHTML = `<div class="szl-v7__cards">${quantGroups(handles)
        .map(([domain, rows]) => `
          <article class="szl-v7__card">
            <div>
              <h3 class="szl-v7__card-title">${escapeHtml(domain.replaceAll("_", " "))}</h3>
              <div class="szl-v7__card-meta"><span>${rows.length} source handles</span><span>constraint input only</span><span>Λ Conjecture 1</span></div>
            </div>
            <span class="szl-v7__tag">Quant domain</span>
          </article>`)
        .join("")}</div>`;
      return;
    }
    panel.innerHTML = `<div class="szl-v7__cards">${handles.map(renderCard).join("")}</div>`;
  }

  function stringHash(value) {
    let hash = 2166136261;
    for (let index = 0; index < value.length; index += 1) {
      hash ^= value.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function graphNodes() {
    const handles = activeHandles().slice(0, 28);
    const roots = [
      { id: "brain", label: "BRAIN", kind: "root", angle: -Math.PI / 2 },
      { id: "formula", label: "FORMULA", kind: "root", angle: 0 },
      { id: "loop", label: "OUROBOROS", kind: "root", angle: Math.PI / 2 },
      { id: "anatomy", label: "ANATOMY", kind: "root", angle: Math.PI },
    ];
    const sourceNodes = handles.map((handle, index) => ({
      id: handle.nodeId,
      label: String(handle.quantDomain || handle.kind || "HANDLE").toUpperCase().slice(0, 18),
      kind: "handle",
      angle: (Math.PI * 2 * index) / Math.max(1, handles.length) + ((stringHash(handle.nodeId) % 31) / 180) * Math.PI,
      handle,
    }));
    return { roots, sourceNodes };
  }

  function drawGraph(timestamp = 0) {
    const canvas = document.getElementById(GRAPH_ID);
    if (!canvas) return;
    const parent = canvas.parentElement;
    const width = Math.max(1, parent.clientWidth);
    const height = Math.max(1, parent.clientHeight);
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const nextWidth = Math.floor(width * ratio);
    const nextHeight = Math.floor(height * ratio);
    if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
      canvas.width = nextWidth;
      canvas.height = nextHeight;
    }
    const context = canvas.getContext("2d");
    if (!context) return;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2 + 5;
    const rootRadius = Math.min(width, height) * 0.23;
    const handleRadius = Math.min(width, height) * 0.4;
    const pulse = REDUCED_MOTION.matches ? 0 : Math.sin(timestamp / 1100) * 2;
    const { roots, sourceNodes } = graphNodes();
    const rootPositions = new Map();

    context.lineWidth = 1;
    for (const root of roots) {
      const x = centerX + Math.cos(root.angle) * rootRadius;
      const y = centerY + Math.sin(root.angle) * rootRadius;
      rootPositions.set(root.id, { x, y });
      context.strokeStyle = "rgba(78,228,207,.24)";
      context.beginPath();
      context.moveTo(centerX, centerY);
      context.lineTo(x, y);
      context.stroke();
    }

    for (const node of sourceNodes) {
      const radiusJitter = ((stringHash(node.id) % 19) - 9) * 0.8;
      const x = centerX + Math.cos(node.angle) * (handleRadius + radiusJitter);
      const y = centerY + Math.sin(node.angle) * (handleRadius + radiusJitter) * 0.68;
      const kind = String(node.handle.kind || "");
      const target = kind.includes("formula") || kind === "quant-domain"
        ? rootPositions.get("formula")
        : node.handle.repository === "szl-holdings/ouroboros"
          ? rootPositions.get("loop")
          : node.handle.repository === "szl-holdings/anatomy"
            ? rootPositions.get("anatomy")
            : rootPositions.get("brain");
      if (target) {
        context.strokeStyle = "rgba(148,170,168,.14)";
        context.beginPath();
        context.moveTo(target.x, target.y);
        context.lineTo(x, y);
        context.stroke();
      }
      context.fillStyle = kind === "quant-domain" ? "#d6bb78" : "#4ee4cf";
      context.beginPath();
      context.arc(x, y, 2.2, 0, Math.PI * 2);
      context.fill();
    }

    context.fillStyle = "rgba(5,18,24,.96)";
    context.strokeStyle = "rgba(78,228,207,.62)";
    context.lineWidth = 1.2;
    context.beginPath();
    context.arc(centerX, centerY, 20 + pulse, 0, Math.PI * 2);
    context.fill();
    context.stroke();
    context.fillStyle = "#edf7f5";
    context.font = "700 8px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText("HOLD", centerX, centerY);

    for (const root of roots) {
      const position = rootPositions.get(root.id);
      context.fillStyle = "rgba(8,24,31,.96)";
      context.strokeStyle = "rgba(78,228,207,.42)";
      context.beginPath();
      context.arc(position.x, position.y, 13, 0, Math.PI * 2);
      context.fill();
      context.stroke();
      context.fillStyle = "#94aaa8";
      context.font = "700 7px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
      context.fillText(root.label.slice(0, 8), position.x, position.y);
    }

    if (state.open && !REDUCED_MOTION.matches) {
      state.graphFrame = window.requestAnimationFrame(drawGraph);
    }
  }

  function restartGraph() {
    window.cancelAnimationFrame(state.graphFrame);
    state.graphFrame = window.requestAnimationFrame(drawGraph);
  }

  async function loadFeeds({ quiet = false } = {}) {
    if (state.loading) return;
    state.loading = true;
    if (!quiet) renderPanel();
    const results = await Promise.allSettled([
      fetchJson(ENDPOINTS.status),
      fetchJson(ENDPOINTS.brain),
      fetchJson(ENDPOINTS.formulas),
      fetchJson(ENDPOINTS.loops),
    ]);
    state.status = results[0].status === "fulfilled" ? results[0].value : null;
    state.feeds.brain = results[1].status === "fulfilled" ? results[1].value : null;
    state.feeds.formulas = results[2].status === "fulfilled" ? results[2].value : null;
    state.feeds.loops = results[3].status === "fulfilled" ? results[3].value : null;
    state.loading = false;
    updateStatusUi();
    renderPanel();
    restartGraph();
  }

  function setActiveTab(tabId, { focus = false } = {}) {
    if (!TABS.some((tab) => tab.id === tabId)) return;
    state.activeTab = tabId;
    for (const button of document.querySelectorAll(".szl-v7__tab")) {
      const selected = button.dataset.tab === tabId;
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
      if (selected && focus) button.focus();
    }
    renderPanel();
    restartGraph();
  }

  function focusableElements(hud) {
    return [...hud.querySelectorAll('button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])')]
      .filter((element) => !element.hidden && element.getClientRects().length > 0);
  }

  function openHud() {
    if (state.open) return;
    const hud = document.getElementById(ROOT_ID);
    const launcher = document.getElementById(LAUNCHER_ID);
    if (!hud || !launcher) return;
    state.lastFocus = document.activeElement;
    state.open = true;
    hud.hidden = false;
    launcher.setAttribute("aria-expanded", "true");
    document.documentElement.style.overflow = "hidden";
    const close = hud.querySelector(".szl-v7__close");
    close?.focus();
    loadFeeds();
    restartGraph();
  }

  function closeHud() {
    if (!state.open) return;
    const hud = document.getElementById(ROOT_ID);
    const launcher = document.getElementById(LAUNCHER_ID);
    state.open = false;
    window.cancelAnimationFrame(state.graphFrame);
    if (hud) hud.hidden = true;
    if (launcher) launcher.setAttribute("aria-expanded", "false");
    document.documentElement.style.overflow = "";
    if (state.lastFocus instanceof HTMLElement) state.lastFocus.focus();
    else launcher?.focus();
  }

  function bindEvents(launcher, hud) {
    launcher.addEventListener("click", openHud);
    hud.querySelector(".szl-v7__close")?.addEventListener("click", closeHud);
    hud.querySelector(".szl-v7__dismiss")?.addEventListener("click", closeHud);
    hud.addEventListener("click", (event) => {
      const tab = event.target.closest?.("[data-tab]");
      if (tab) setActiveTab(tab.dataset.tab, { focus: false });
    });
    hud.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeHud();
        return;
      }
      const current = event.target.closest?.("[data-tab]");
      if (current && ["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
        event.preventDefault();
        const index = TABS.findIndex((tab) => tab.id === current.dataset.tab);
        let next = index;
        if (event.key === "ArrowLeft") next = (index - 1 + TABS.length) % TABS.length;
        if (event.key === "ArrowRight") next = (index + 1) % TABS.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = TABS.length - 1;
        setActiveTab(TABS[next].id, { focus: true });
        return;
      }
      if (event.key === "Tab") {
        const items = focusableElements(hud);
        if (!items.length) return;
        const first = items[0];
        const last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible" && state.open) loadFeeds({ quiet: true });
    });
    state.graphObserver = new ResizeObserver(() => restartGraph());
    const graph = document.querySelector(".szl-v7__graph-shell");
    if (graph) state.graphObserver.observe(graph);
    REDUCED_MOTION.addEventListener?.("change", restartGraph);
  }

  function boot() {
    if (document.getElementById(ROOT_ID) || document.getElementById(LAUNCHER_ID)) return;
    const { launcher, hud } = createMarkup();
    bindEvents(launcher, hud);
    state.pollTimer = window.setInterval(() => {
      if (state.open && document.visibilityState === "visible") loadFeeds({ quiet: true });
    }, 120_000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
