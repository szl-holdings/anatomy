/* SPDX-License-Identifier: Apache-2.0
 * SZL Living Anatomy v7 · YACHAY Brain / Quant Atlas
 * Same-origin, handles-only visualization. No third-party runtime calls.
 */
(() => {
  "use strict";

  if (document.documentElement.dataset.brainV7Installed === "true") return;
  document.documentElement.dataset.brainV7Installed = "true";

  const ENDPOINTS = Object.freeze({
    all: "/api/anatomy/v1/brain/frontier?limit=48",
    formulas: "/api/anatomy/v1/brain/formulas?limit=48",
    quant: "/api/anatomy/v1/brain/quant?limit=48",
    ouroboros: "/api/anatomy/v1/brain/ouroboros?limit=48",
  });
  const HEALTH_ENDPOINT = "/api/anatomy/v1/frontier-health";
  const TAB_LABELS = Object.freeze({
    all: "Frontier",
    formulas: "Formulas",
    quant: "Quant",
    ouroboros: "Ouroboros",
  });
  const FORBIDDEN_RESPONSE_KEYS = new Set(["content", "text", "documents"]);
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches === true;

  const state = {
    open: false,
    activeTab: "all",
    query: "",
    health: null,
    payloads: new Map(),
    handles: [],
    selectedId: null,
    requestController: null,
    raf: 0,
    lastFocused: null,
  };

  const launcher = document.createElement("button");
  launcher.type = "button";
  launcher.className = "brain-v7-launcher";
  launcher.setAttribute("aria-haspopup", "dialog");
  launcher.setAttribute("aria-controls", "brain-v7-shell");
  launcher.setAttribute("aria-expanded", "false");
  launcher.innerHTML = "<span>YACHAY Brain v7</span>";

  const shell = document.createElement("div");
  shell.id = "brain-v7-shell";
  shell.className = "brain-v7-shell";
  shell.hidden = true;
  shell.innerHTML = `
    <section class="brain-v7-panel" role="dialog" aria-modal="true" aria-labelledby="brain-v7-title" aria-describedby="brain-v7-subtitle">
      <header class="brain-v7-header">
        <div>
          <p class="brain-v7-kicker">Living Anatomy · governed memory instrument</p>
          <h2 class="brain-v7-title" id="brain-v7-title">YACHAY Brain · Formula &amp; Quant Atlas</h2>
          <p class="brain-v7-subtitle" id="brain-v7-subtitle">Exact public-source handles orbit the living substrate. Review required. No silent training, truth promotion, or execution.</p>
        </div>
        <button class="brain-v7-close" type="button" aria-label="Close YACHAY Brain v7">×</button>
      </header>
      <div class="brain-v7-toolbar">
        <input class="brain-v7-search" type="search" maxlength="512" autocomplete="off" spellcheck="false" aria-label="Filter visible Brain handles" placeholder="Filter sources, formulas, quant domains, or Ouroboros…" />
        <div class="brain-v7-tabs" role="tablist" aria-label="Brain v7 data planes"></div>
      </div>
      <div class="brain-v7-main">
        <div class="brain-v7-stage" aria-label="Holographic graph of review-required public source handles">
          <canvas class="brain-v7-canvas"></canvas>
          <div class="brain-v7-stage-label">handles only · review required</div>
        </div>
        <aside class="brain-v7-details" aria-label="Selected Brain handles">
          <div class="brain-v7-metrics" aria-live="polite"></div>
          <div class="brain-v7-list" role="tabpanel" tabindex="0"></div>
        </aside>
      </div>
      <footer class="brain-v7-footer">
        <span class="brain-v7-state" data-ready="false">Loading exact source state…</span>
        <span class="brain-v7-digest" title="Candidate set digest">digest · unavailable</span>
      </footer>
    </section>
  `;

  document.body.append(launcher, shell);

  const panel = shell.querySelector(".brain-v7-panel");
  const closeButton = shell.querySelector(".brain-v7-close");
  const searchInput = shell.querySelector(".brain-v7-search");
  const tabs = shell.querySelector(".brain-v7-tabs");
  const metrics = shell.querySelector(".brain-v7-metrics");
  const list = shell.querySelector(".brain-v7-list");
  const canvas = shell.querySelector(".brain-v7-canvas");
  const stage = shell.querySelector(".brain-v7-stage");
  const statusNode = shell.querySelector(".brain-v7-state");
  const digestNode = shell.querySelector(".brain-v7-digest");
  const context = canvas.getContext("2d", { alpha: true });

  function containsForbiddenKey(value) {
    if (!value || typeof value !== "object") return false;
    if (Array.isArray(value)) return value.some(containsForbiddenKey);
    for (const [key, child] of Object.entries(value)) {
      if (FORBIDDEN_RESPONSE_KEYS.has(key.toLowerCase())) return true;
      if (containsForbiddenKey(child)) return true;
    }
    return false;
  }

  function assertPayload(payload) {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("INVALID_PAYLOAD");
    }
    if (containsForbiddenKey(payload)) throw new Error("CONTENT_BOUNDARY_VIOLATION");
    const handles = Array.isArray(payload.handles) ? payload.handles : [];
    for (const handle of handles) {
      if (!handle || typeof handle !== "object") throw new Error("INVALID_HANDLE");
      if (handle.contentAccess !== "HANDLES_ONLY") throw new Error("HANDLE_ACCESS_DRIFT");
      if (handle.candidateState !== "DISCOVERED_REVIEW_REQUIRED") {
        throw new Error("CANDIDATE_STATE_DRIFT");
      }
      if (!/^frontier:[0-9a-f]{32}$/.test(String(handle.nodeId || ""))) {
        throw new Error("INVALID_HANDLE_ID");
      }
      if (!/^[0-9a-f]{64}$/.test(String(handle.sha256 || ""))) {
        throw new Error("INVALID_HANDLE_DIGEST");
      }
      if (!/^[0-9a-f]{40}$/.test(String(handle.revision || ""))) {
        throw new Error("INVALID_SOURCE_REVISION");
      }
    }
    return payload;
  }

  async function fetchJson(url, signal) {
    const response = await fetch(url, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      redirect: "error",
      headers: { Accept: "application/json" },
      signal,
    });
    if (!response.ok) throw new Error(`HTTP_${response.status}`);
    const type = response.headers.get("content-type") || "";
    if (!type.toLowerCase().includes("application/json")) {
      throw new Error("NON_JSON_RESPONSE");
    }
    return response.json();
  }

  function setStatus(label, ready = false) {
    statusNode.textContent = label;
    statusNode.dataset.ready = ready ? "true" : "false";
  }

  function shortDigest(value, size = 12) {
    const text = String(value || "");
    return text ? `${text.slice(0, size)}…${text.slice(-6)}` : "unavailable";
  }

  function escapeLabel(value, fallback = "UNAVAILABLE") {
    const text = String(value || "").trim();
    return text || fallback;
  }

  function kindBucket(handle) {
    const kind = String(handle.kind || "");
    if (kind.includes("quant") || handle.quantDomain) return "quant";
    if (kind.includes("formula")) return "formula";
    if (String(handle.repository || "").includes("ouroboros")) return "ouroboros";
    if (String(handle.repository || "").includes("anatomy")) return "anatomy";
    if (String(handle.repository || "").includes("second-brain")) return "brain";
    return "source";
  }

  function stableUnit(value) {
    let hash = 2166136261;
    const text = String(value || "");
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0) / 4294967295;
  }

  function activePayload() {
    return state.payloads.get(state.activeTab) || { handles: [] };
  }

  function visibleHandles() {
    const source = Array.isArray(activePayload().handles) ? activePayload().handles : [];
    const query = state.query.trim().toLowerCase();
    if (!query) return source;
    const terms = query.split(/\s+/).filter(Boolean);
    return source.filter((handle) => {
      const haystack = [
        handle.title,
        handle.repository,
        handle.path,
        handle.kind,
        handle.quantDomain,
        handle.admission,
      ]
        .join(" ")
        .toLowerCase();
      return terms.every((term) => haystack.includes(term));
    });
  }

  function renderTabs() {
    tabs.replaceChildren();
    Object.entries(TAB_LABELS).forEach(([id, label], index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "brain-v7-tab";
      button.id = `brain-v7-tab-${id}`;
      button.dataset.tab = id;
      button.setAttribute("role", "tab");
      button.setAttribute("aria-selected", state.activeTab === id ? "true" : "false");
      button.setAttribute("tabindex", state.activeTab === id ? "0" : "-1");
      button.textContent = label;
      button.addEventListener("click", () => selectTab(id));
      button.addEventListener("keydown", (event) => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const buttons = [...tabs.querySelectorAll(".brain-v7-tab")];
        let next = index;
        if (event.key === "ArrowLeft") next = (index - 1 + buttons.length) % buttons.length;
        if (event.key === "ArrowRight") next = (index + 1) % buttons.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = buttons.length - 1;
        buttons[next]?.focus();
        selectTab(buttons[next]?.dataset.tab || "all");
      });
      tabs.append(button);
    });
  }

  function renderMetrics(handles) {
    const formulaCount = handles.filter((handle) => kindBucket(handle) === "formula").length;
    const quantCount = new Set(handles.map((handle) => handle.quantDomain).filter(Boolean)).size;
    const sourceCount = new Set(handles.map((handle) => handle.repository).filter(Boolean)).size;
    const values = [
      [String(handles.length), "visible handles"],
      [String(formulaCount), "formula handles"],
      [String(quantCount || sourceCount), quantCount ? "quant domains" : "source repos"],
    ];
    metrics.replaceChildren();
    for (const [value, label] of values) {
      const metric = document.createElement("div");
      metric.className = "brain-v7-metric";
      const strong = document.createElement("strong");
      const span = document.createElement("span");
      strong.textContent = value;
      span.textContent = label;
      metric.append(strong, span);
      metrics.append(metric);
    }
  }

  function renderList(handles) {
    list.replaceChildren();
    if (!handles.length) {
      const empty = document.createElement("p");
      empty.className = "brain-v7-empty";
      empty.textContent = "No review handles match this view. Nothing is fabricated.";
      list.append(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    for (const handle of handles) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "brain-v7-card";
      card.dataset.kind = kindBucket(handle);
      if (handle.quantDomain) card.dataset.domain = handle.quantDomain;
      card.dataset.nodeId = handle.nodeId;
      card.dataset.active = state.selectedId === handle.nodeId ? "true" : "false";
      card.setAttribute("aria-label", `Focus ${escapeLabel(handle.title)}`);

      const mark = document.createElement("span");
      mark.className = "brain-v7-card-mark";
      mark.setAttribute("aria-hidden", "true");
      const body = document.createElement("span");
      const title = document.createElement("h3");
      const meta = document.createElement("p");
      title.textContent = escapeLabel(handle.title);
      meta.textContent = [
        escapeLabel(handle.kind),
        handle.quantDomain ? `domain ${handle.quantDomain}` : null,
        escapeLabel(handle.repository),
        `rev ${shortDigest(handle.revision, 8)}`,
        `sha ${shortDigest(handle.sha256, 8)}`,
      ]
        .filter(Boolean)
        .join(" · ");
      body.append(title, meta);
      card.append(mark, body);
      card.addEventListener("click", () => {
        state.selectedId = handle.nodeId;
        render();
      });
      fragment.append(card);
    }
    list.append(fragment);
  }

  function resizeCanvas() {
    const rect = stage.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.floor(rect.width * ratio));
    const height = Math.max(1, Math.floor(rect.height * ratio));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    return { width, height, ratio };
  }

  function palette(bucket) {
    const style = getComputedStyle(document.documentElement);
    if (bucket === "quant") return style.getPropertyValue("--brain-v7-gold").trim() || "#e8c985";
    if (bucket === "ouroboros") return style.getPropertyValue("--brain-v7-warn").trim() || "#ffb86c";
    return style.getPropertyValue("--brain-v7-proof").trim() || "#62e8da";
  }

  function nodeLayout(handles, width, height) {
    const center = { x: width * 0.5, y: height * 0.51 };
    const groups = new Map();
    for (const handle of handles) {
      const bucket = kindBucket(handle);
      if (!groups.has(bucket)) groups.set(bucket, []);
      groups.get(bucket).push(handle);
    }
    const groupNames = [...groups.keys()].sort();
    const minDimension = Math.min(width, height);
    const inner = Math.max(70, minDimension * 0.19);
    const outer = Math.max(inner + 40, minDimension * 0.43);
    const nodes = [];
    groupNames.forEach((groupName, groupIndex) => {
      const group = groups.get(groupName);
      const groupAngle = (Math.PI * 2 * groupIndex) / Math.max(1, groupNames.length) - Math.PI / 2;
      group.forEach((handle, itemIndex) => {
        const seed = stableUnit(handle.nodeId);
        const local = group.length > 1 ? (itemIndex / group.length - 0.5) * 0.95 : 0;
        const angle = groupAngle + local + (seed - 0.5) * 0.16;
        const ring = inner + (outer - inner) * (0.35 + 0.65 * seed);
        nodes.push({
          handle,
          bucket: groupName,
          x: center.x + Math.cos(angle) * ring,
          y: center.y + Math.sin(angle) * ring * 0.72,
          radius: handle.nodeId === state.selectedId ? 8 : 4.2 + seed * 2.2,
        });
      });
    });
    return { center, nodes };
  }

  function draw(timestamp = 0) {
    if (!state.open || !context) return;
    const handles = state.handles;
    const { width, height, ratio } = resizeCanvas();
    context.clearRect(0, 0, width, height);
    const layout = nodeLayout(handles, width, height);
    const pulse = reduceMotion ? 0 : (Math.sin(timestamp / 920) + 1) * 0.5;

    context.save();
    context.lineWidth = Math.max(1, ratio * 0.55);
    for (const node of layout.nodes) {
      const selected = node.handle.nodeId === state.selectedId;
      context.beginPath();
      context.moveTo(layout.center.x, layout.center.y);
      context.lineTo(node.x, node.y);
      context.strokeStyle = selected
        ? "rgba(238, 248, 247, 0.62)"
        : "rgba(98, 232, 218, 0.11)";
      context.stroke();
    }

    const centerGlow = context.createRadialGradient(
      layout.center.x,
      layout.center.y,
      0,
      layout.center.x,
      layout.center.y,
      64 * ratio,
    );
    centerGlow.addColorStop(0, "rgba(98, 232, 218, 0.38)");
    centerGlow.addColorStop(0.28, "rgba(98, 232, 218, 0.12)");
    centerGlow.addColorStop(1, "rgba(98, 232, 218, 0)");
    context.fillStyle = centerGlow;
    context.beginPath();
    context.arc(layout.center.x, layout.center.y, 64 * ratio, 0, Math.PI * 2);
    context.fill();

    context.beginPath();
    context.arc(layout.center.x, layout.center.y, (12 + pulse * 2) * ratio, 0, Math.PI * 2);
    context.fillStyle = palette("brain");
    context.shadowColor = palette("brain");
    context.shadowBlur = 18 * ratio;
    context.fill();
    context.shadowBlur = 0;

    for (const node of layout.nodes) {
      const selected = node.handle.nodeId === state.selectedId;
      const color = palette(node.bucket);
      context.beginPath();
      context.arc(node.x, node.y, (node.radius + (selected ? pulse * 2 : 0)) * ratio, 0, Math.PI * 2);
      context.fillStyle = color;
      context.globalAlpha = selected ? 1 : 0.76;
      context.shadowColor = color;
      context.shadowBlur = (selected ? 20 : 8) * ratio;
      context.fill();
      context.globalAlpha = 1;
      context.shadowBlur = 0;
    }
    context.restore();

    if (!reduceMotion) state.raf = requestAnimationFrame(draw);
  }

  function render() {
    state.handles = visibleHandles();
    if (state.selectedId && !state.handles.some((handle) => handle.nodeId === state.selectedId)) {
      state.selectedId = null;
    }
    renderTabs();
    renderMetrics(state.handles);
    renderList(state.handles);
    if (state.open) {
      cancelAnimationFrame(state.raf);
      draw(performance.now());
    }
  }

  async function load() {
    state.requestController?.abort();
    const controller = new AbortController();
    state.requestController = controller;
    const timeout = window.setTimeout(() => controller.abort("TIMEOUT"), 9000);
    setStatus("Resolving exact source state…", false);
    try {
      const [health, ...payloads] = await Promise.all([
        fetchJson(HEALTH_ENDPOINT, controller.signal),
        ...Object.values(ENDPOINTS).map((url) => fetchJson(url, controller.signal)),
      ]);
      if (health.ready !== true || health.state !== "REVIEW_REQUIRED") {
        throw new Error(escapeLabel(health.reason, "FRONTIER_UNAVAILABLE"));
      }
      if (health.content_access !== "HANDLES_ONLY") throw new Error("HEALTH_ACCESS_DRIFT");
      if (health.training_authority !== "NONE") throw new Error("TRAINING_AUTHORITY_DRIFT");
      if (health.promotion_authority !== "NONE") throw new Error("PROMOTION_AUTHORITY_DRIFT");
      if (health.execution_authority !== "NONE") throw new Error("EXECUTION_AUTHORITY_DRIFT");
      state.health = health;
      Object.keys(ENDPOINTS).forEach((id, index) => {
        state.payloads.set(id, assertPayload(payloads[index]));
      });
      digestNode.textContent = `digest · ${shortDigest(health.candidate_set_sha256, 16)}`;
      digestNode.title = `Candidate set SHA-256: ${health.candidate_set_sha256}`;
      setStatus(`${health.candidate_count} candidates · review required · source-bound`, true);
      render();
    } catch (error) {
      state.health = null;
      state.payloads.clear();
      state.handles = [];
      const reason = error instanceof Error ? error.message : "UNAVAILABLE";
      setStatus(`UNAVAILABLE · ${reason}`, false);
      digestNode.textContent = "digest · unavailable";
      list.replaceChildren();
      const message = document.createElement("p");
      message.className = "brain-v7-error";
      message.textContent = "The exact Brain frontier snapshot could not be verified. This instrument refuses to invent nodes or reuse stale content.";
      list.append(message);
      renderMetrics([]);
      cancelAnimationFrame(state.raf);
      draw(performance.now());
    } finally {
      window.clearTimeout(timeout);
      if (state.requestController === controller) state.requestController = null;
    }
  }

  function selectTab(id) {
    if (!(id in ENDPOINTS)) return;
    state.activeTab = id;
    state.selectedId = null;
    render();
  }

  function focusableElements() {
    return [...panel.querySelectorAll(
      'button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
    )].filter((element) => !element.hidden && element.getClientRects().length > 0);
  }

  function openPanel() {
    if (state.open) return;
    state.open = true;
    state.lastFocused = document.activeElement;
    shell.hidden = false;
    launcher.setAttribute("aria-expanded", "true");
    document.body.classList.add("brain-v7-open");
    requestAnimationFrame(() => {
      searchInput.focus();
      draw(performance.now());
    });
    if (!state.health) load();
    else render();
  }

  function closePanel() {
    if (!state.open) return;
    state.open = false;
    shell.hidden = true;
    launcher.setAttribute("aria-expanded", "false");
    document.body.classList.remove("brain-v7-open");
    state.requestController?.abort("PANEL_CLOSED");
    cancelAnimationFrame(state.raf);
    if (state.lastFocused instanceof HTMLElement && document.contains(state.lastFocused)) {
      state.lastFocused.focus();
    } else {
      launcher.focus();
    }
  }

  launcher.addEventListener("click", openPanel);
  closeButton.addEventListener("click", closePanel);
  shell.addEventListener("mousedown", (event) => {
    if (event.target === shell) closePanel();
  });
  searchInput.addEventListener("input", () => {
    state.query = searchInput.value.slice(0, 512);
    state.selectedId = null;
    render();
  });
  window.addEventListener("resize", () => {
    if (state.open) draw(performance.now());
  }, { passive: true });
  document.addEventListener("keydown", (event) => {
    if ((event.altKey || event.metaKey) && event.key.toLowerCase() === "b") {
      event.preventDefault();
      state.open ? closePanel() : openPanel();
      return;
    }
    if (!state.open) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closePanel();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = focusableElements();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  renderTabs();
  renderMetrics([]);
})();
