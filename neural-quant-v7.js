/* SPDX-License-Identifier: Apache-2.0
 * SZL Living Anatomy — YACHAY Neural Quant v7
 * Read-only, handles-only, same-origin observation surface.
 */
(() => {
  "use strict";

  const ENDPOINT = "/api/anatomy/v1/brain/neural-quant-v7?k=24";
  const STYLE_HREF = "./neural-quant-v7.css";
  const SVG_NS = "http://www.w3.org/2000/svg";
  const PANEL_ID = "nq7-panel";
  const TABS = [
    ["overview", "Overview"],
    ["formulas", "Formulas"],
    ["quant", "Quant"],
    ["ouroboros", "Ouroboros"],
  ];
  const state = {
    payload: null,
    loading: false,
    activeTab: "overview",
    previousFocus: null,
    abortController: null,
  };

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  };

  const svgEl = (tag, attributes = {}) => {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attributes).forEach(([key, value]) => {
      node.setAttribute(key, String(value));
    });
    return node;
  };

  const bounded = (value, fallback = 0) => {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  };

  const shortDigest = (value) => {
    const text = typeof value === "string" ? value : "";
    return text.length >= 16 ? `${text.slice(0, 8)}…${text.slice(-8)}` : "UNAVAILABLE";
  };

  const titleize = (value) => String(value || "unknown")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

  const ensureStyles = () => {
    if (document.querySelector(`link[href="${STYLE_HREF}"]`)) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = STYLE_HREF;
    link.dataset.neuralQuantV7 = "true";
    document.head.append(link);
  };

  const safeSourceUrl = (handle) => {
    const repository = String(handle?.sourceRepository || "");
    const revision = String(handle?.sourceRevision || "");
    const path = String(handle?.sourcePath || "");
    if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) return null;
    if (!/^[0-9a-f]{40}$/.test(revision)) return null;
    if (!path || path.startsWith("/") || path.includes("..")) return null;
    const encodedPath = path.split("/").map(encodeURIComponent).join("/");
    return `https://github.com/${repository}/blob/${revision}/${encodedPath}`;
  };

  const makeChip = (text, chipState = "measured") => {
    const chip = el("span", "nq7-chip", text);
    chip.dataset.state = chipState;
    return chip;
  };

  const makeMetricCard = (label, value, note) => {
    const card = el("div", "nq7-card");
    card.append(
      el("div", "nq7-card-label", label),
      el("div", "nq7-card-value", value),
      el("div", "nq7-card-note", note),
    );
    return card;
  };

  const makeHandleItem = (handle) => {
    const item = el("article", "nq7-item");
    const copy = el("div");
    copy.append(
      el("div", "nq7-item-title", handle?.note || handle?.nodeId || "Untitled handle"),
      el(
        "div",
        "nq7-item-meta",
        [
          handle?.sourceKind || "source",
          handle?.quantDomain || null,
          handle?.candidateState || "REVIEW_REQUIRED",
          shortDigest(handle?.sha256),
        ].filter(Boolean).join(" · "),
      ),
    );
    item.append(copy);
    const sourceUrl = safeSourceUrl(handle);
    if (sourceUrl) {
      const link = el("a", "nq7-item-link", "SRC");
      link.href = sourceUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.setAttribute("aria-label", `Open source for ${handle?.note || handle?.nodeId || "candidate"}`);
      item.append(link);
    }
    return item;
  };

  const makeHandleList = (handles, emptyText) => {
    const list = el("div", "nq7-list");
    const safeHandles = Array.isArray(handles) ? handles : [];
    if (!safeHandles.length) {
      list.append(el("div", "nq7-empty", emptyText));
      return list;
    }
    safeHandles.forEach((handle) => list.append(makeHandleItem(handle)));
    return list;
  };

  const setNodeText = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = String(value);
  };

  const setPanelState = (open) => {
    const panel = document.getElementById(PANEL_ID);
    const backdrop = document.getElementById("nq7-backdrop");
    const launcher = document.getElementById("nq7-launcher");
    if (!panel || !backdrop || !launcher) return;
    panel.dataset.open = open ? "true" : "false";
    backdrop.dataset.open = open ? "true" : "false";
    launcher.setAttribute("aria-expanded", open ? "true" : "false");
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    if (open) {
      state.previousFocus = document.activeElement;
      window.setTimeout(() => document.getElementById("nq7-close")?.focus(), 0);
      if (!state.payload && !state.loading) loadData();
    } else if (state.previousFocus instanceof HTMLElement) {
      state.previousFocus.focus();
    }
  };

  const activateTab = (tabId) => {
    state.activeTab = tabId;
    TABS.forEach(([id]) => {
      const tab = document.getElementById(`nq7-tab-${id}`);
      const section = document.getElementById(`nq7-section-${id}`);
      const active = id === tabId;
      if (tab) {
        tab.setAttribute("aria-selected", active ? "true" : "false");
        tab.tabIndex = active ? 0 : -1;
      }
      if (section) section.hidden = !active;
    });
  };

  const focusableNodes = () => {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) return [];
    return [...panel.querySelectorAll(
      'button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
    )].filter((node) => !node.hasAttribute("hidden"));
  };

  const handleGlobalKeydown = (event) => {
    const panel = document.getElementById(PANEL_ID);
    if (!panel || panel.dataset.open !== "true") return;
    if (event.key === "Escape") {
      event.preventDefault();
      setPanelState(false);
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = focusableNodes();
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
  };

  const buildShell = () => {
    if (document.getElementById(PANEL_ID)) return;
    ensureStyles();

    const launcher = el("button");
    launcher.id = "nq7-launcher";
    launcher.type = "button";
    launcher.setAttribute("aria-controls", PANEL_ID);
    launcher.setAttribute("aria-expanded", "false");
    launcher.setAttribute("aria-label", "Open YACHAY Neural Quant v7");
    launcher.append(
      el("span", "nq7-launcher-mark"),
      el("span", "nq7-launcher-label", "Neural Quant v7"),
    );

    const backdrop = el("div");
    backdrop.id = "nq7-backdrop";
    backdrop.dataset.open = "false";

    const panel = el("aside");
    panel.id = PANEL_ID;
    panel.dataset.open = "false";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "true");
    panel.setAttribute("aria-hidden", "true");
    panel.setAttribute("aria-labelledby", "nq7-title");

    const header = el("header", "nq7-header");
    const sigil = el("div", "nq7-sigil", "Y7");
    sigil.setAttribute("aria-hidden", "true");
    const heading = el("div", "nq7-heading");
    heading.append(
      el("div", "nq7-eyebrow", "YACHAY · source-bound intelligence organ"),
    );
    const title = el("h2", "nq7-title", "Neural Quant v7");
    title.id = "nq7-title";
    heading.append(title);
    const close = el("button", "nq7-icon-button", "×");
    close.id = "nq7-close";
    close.type = "button";
    close.setAttribute("aria-label", "Close Neural Quant v7");
    header.append(sigil, heading, close);

    const status = el("div", "nq7-statusbar");
    status.id = "nq7-statusbar";
    status.setAttribute("aria-live", "polite");
    status.append(
      makeChip("Loading source state", "review"),
      makeChip("Handles only", "measured"),
      makeChip("Authority none", "measured"),
    );

    const viz = el("section", "nq7-viz");
    viz.setAttribute("aria-label", "Neural Quant formula-domain topology");
    const graph = svgEl("svg", {
      id: "nq7-graph",
      viewBox: "0 0 640 340",
      role: "img",
      "aria-labelledby": "nq7-graph-title nq7-graph-desc",
    });
    const graphTitle = svgEl("title", { id: "nq7-graph-title" });
    graphTitle.textContent = "YACHAY neural quant topology";
    const graphDesc = svgEl("desc", { id: "nq7-graph-desc" });
    graphDesc.textContent = "A read-only brain-shaped map of quant domains and source-bound evidence handles.";
    graph.append(graphTitle, graphDesc);
    viz.append(graph);
    const metrics = el("div", "nq7-viz-meta");
    metrics.id = "nq7-viz-meta";
    viz.append(metrics);

    const body = el("div", "nq7-body");
    const tabs = el("div", "nq7-tabs");
    tabs.setAttribute("role", "tablist");
    tabs.setAttribute("aria-label", "Neural Quant views");
    TABS.forEach(([id, label], index) => {
      const tab = el("button", "nq7-tab", label);
      tab.id = `nq7-tab-${id}`;
      tab.type = "button";
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-controls", `nq7-section-${id}`);
      tab.setAttribute("aria-selected", index === 0 ? "true" : "false");
      tab.tabIndex = index === 0 ? 0 : -1;
      tab.addEventListener("click", () => activateTab(id));
      tabs.append(tab);
    });
    const content = el("div", "nq7-content");
    TABS.forEach(([id]) => {
      const section = el("section", "nq7-section");
      section.id = `nq7-section-${id}`;
      section.setAttribute("role", "tabpanel");
      section.setAttribute("aria-labelledby", `nq7-tab-${id}`);
      section.hidden = id !== "overview";
      section.append(el("div", "nq7-empty", "Loading source-bound observation…"));
      content.append(section);
    });
    body.append(tabs, content);

    const footer = el("footer", "nq7-footer");
    const receipt = el("div", "nq7-receipt", "Waiting for exact source receipt.");
    receipt.id = "nq7-receipt";
    const refresh = el("button", "nq7-refresh", "Refresh");
    refresh.id = "nq7-refresh";
    refresh.type = "button";
    footer.append(receipt, refresh);

    panel.append(header, status, viz, body, footer);
    document.body.append(backdrop, launcher, panel);

    launcher.addEventListener("click", () => setPanelState(true));
    close.addEventListener("click", () => setPanelState(false));
    backdrop.addEventListener("click", () => setPanelState(false));
    refresh.addEventListener("click", () => loadData(true));
    document.addEventListener("keydown", handleGlobalKeydown);
  };

  const drawBrain = (payload) => {
    const svg = document.getElementById("nq7-graph");
    if (!svg) return;
    [...svg.children].slice(2).forEach((node) => node.remove());

    const left = svgEl("path", {
      class: "nq7-brain-outline",
      d: "M315 65 C270 24 188 38 150 83 C112 128 119 199 159 225 C145 275 205 311 258 284 C278 314 314 291 315 258 Z",
    });
    const right = svgEl("path", {
      class: "nq7-brain-outline",
      d: "M325 65 C370 24 452 38 490 83 C528 128 521 199 481 225 C495 275 435 311 382 284 C362 314 326 291 325 258 Z",
    });
    svg.append(left, right);

    [
      "M315 92 C275 76 248 102 253 134 C214 131 196 167 213 194 C183 217 206 253 244 247 C252 278 287 274 315 249",
      "M325 92 C365 76 392 102 387 134 C426 131 444 167 427 194 C457 217 434 253 396 247 C388 278 353 274 325 249",
      "M315 124 C282 113 270 145 282 167 C252 176 255 213 284 219 C281 242 300 251 315 241",
      "M325 124 C358 113 370 145 358 167 C388 176 385 213 356 219 C359 242 340 251 325 241",
    ].forEach((path) => svg.append(svgEl("path", { class: "nq7-lobe-line", d: path })));

    const domains = Array.isArray(payload?.quant?.domains) ? payload.quant.domains : [];
    const centerX = 320;
    const centerY = 172;
    const radiusX = 226;
    const radiusY = 122;
    const domainGroup = svgEl("g", { "aria-hidden": "true" });
    domains.slice(0, 9).forEach((domain, index) => {
      const angle = -Math.PI / 2 + (Math.PI * 2 * index) / Math.max(1, domains.length);
      const x = centerX + Math.cos(angle) * radiusX;
      const y = centerY + Math.sin(angle) * radiusY;
      domainGroup.append(svgEl("line", {
        class: "nq7-domain-line",
        x1: centerX,
        y1: centerY,
        x2: x,
        y2: y,
      }));
      domainGroup.append(svgEl("circle", {
        class: "nq7-domain-node",
        cx: x,
        cy: y,
        r: 10 + Math.min(7, bounded(domain?.candidate_count, 1)),
      }));
      domainGroup.append(svgEl("circle", {
        class: "nq7-domain-node-core",
        cx: x,
        cy: y,
        r: 2.8,
      }));
      const text = svgEl("text", {
        class: "nq7-domain-label",
        x: x + (x >= centerX ? 16 : -16),
        y: y + 3,
        "text-anchor": x >= centerX ? "start" : "end",
      });
      text.textContent = titleize(domain?.id).slice(0, 28);
      domainGroup.append(text);
    });
    const core = svgEl("circle", {
      class: "nq7-domain-node",
      cx: centerX,
      cy: centerY,
      r: 30,
    });
    const coreDot = svgEl("circle", {
      class: "nq7-domain-node-core",
      cx: centerX,
      cy: centerY,
      r: 7,
    });
    const lambda = svgEl("text", {
      class: "nq7-domain-label",
      x: centerX,
      y: centerY + 4,
      "text-anchor": "middle",
    });
    lambda.textContent = "Λ";
    svg.append(domainGroup, core, coreDot, lambda);

    const meta = document.getElementById("nq7-viz-meta");
    if (meta) {
      meta.replaceChildren();
      [
        ["Brain", bounded(payload?.brain?.chunk_count)],
        ["Frontier", bounded(payload?.brain?.frontier_candidate_count)],
        ["Formula", bounded(payload?.formulas?.attributed)],
        ["Quant", bounded(payload?.quant?.domain_count)],
      ].forEach(([label, value]) => {
        const metric = el("div", "nq7-viz-metric");
        metric.append(document.createTextNode(`${label} `));
        metric.append(el("strong", "", value));
        meta.append(metric);
      });
    }
  };

  const renderOverview = (payload) => {
    const section = document.getElementById("nq7-section-overview");
    if (!section) return;
    section.replaceChildren();
    section.append(
      el("h3", "nq7-section-title", "One source-bound nervous system"),
      el(
        "p",
        "nq7-copy",
        "Living Anatomy now observes the governed 575-chunk Second Brain, its review-gated public frontier, the attributed formula/quant atlas, and bounded Ouroboros loop metadata through one handles-only interface.",
      ),
    );
    const grid = el("div", "nq7-grid");
    grid.append(
      makeMetricCard(
        "Public memory",
        bounded(payload?.brain?.chunk_count).toLocaleString(),
        "Governed retrieval chunks · not weights",
      ),
      makeMetricCard(
        "Review frontier",
        bounded(payload?.brain?.frontier_candidate_count).toLocaleString(),
        "Content-addressed candidates · review required",
      ),
      makeMetricCard(
        "Formula system",
        `${bounded(payload?.formulas?.attributed)} + ${bounded(payload?.formulas?.executable)}`,
        "Attributed records + executable kernels",
      ),
      makeMetricCard(
        "Quant domains",
        bounded(payload?.quant?.domain_count),
        "Explicit constraint and research domains",
      ),
    );
    section.append(grid);
    section.append(
      el("h3", "nq7-section-title", "Authority boundary"),
      el(
        "p",
        "nq7-copy",
        "Public output contains handles and digests only. Training, promotion, execution, merge, and provider mutation remain NONE. The private graph is not loaded. Lambda remains Conjecture 1, advisory only.",
      ),
      el("h3", "nq7-section-title", "Source receipt"),
      el(
        "p",
        "nq7-copy",
        `Second Brain ${shortDigest(payload?.source_revision)} · candidate set ${shortDigest(payload?.candidate_set_sha256)} · view ${shortDigest(payload?.view_sha256)}`,
      ),
    );
  };

  const renderFormulas = (payload) => {
    const section = document.getElementById("nq7-section-formulas");
    if (!section) return;
    section.replaceChildren();
    section.append(
      el("h3", "nq7-section-title", "Formula authority — separated, never inflated"),
      el(
        "p",
        "nq7-copy",
        `${bounded(payload?.formulas?.attributed)} attributed records · ${bounded(payload?.formulas?.executable)} executable kernels · ${bounded(payload?.formulas?.locked_proven)} locked-proven. F-number mapping: ${payload?.formulas?.mapping || "UNKNOWN_NOT_INFERRED"}.`,
      ),
    );
    const locked = Array.isArray(payload?.formulas?.locked_proven_ids)
      ? payload.formulas.locked_proven_ids.join(" · ")
      : "UNAVAILABLE";
    section.append(
      makeMetricCard("Locked-proven IDs", locked, "Exactly eight · machine-enforced upstream"),
      el("h3", "nq7-section-title", "Source handles"),
      makeHandleList(payload?.formulas?.handles, "No formula handles are available."),
    );
  };

  const renderQuant = (payload) => {
    const section = document.getElementById("nq7-section-quant");
    if (!section) return;
    section.replaceChildren();
    section.append(
      el("h3", "nq7-section-title", "Quant domain lattice"),
      el(
        "p",
        "nq7-copy",
        "Nine explicit domains organize formula and research candidates as reference or constraint inputs. A domain assignment does not establish proof, fitness, or execution authority.",
      ),
    );
    const domainList = el("div", "nq7-domain-list");
    const domains = Array.isArray(payload?.quant?.domains) ? payload.quant.domains : [];
    domains.forEach((domain) => {
      domainList.append(
        el(
          "span",
          "nq7-domain-pill",
          `${titleize(domain?.id)} · ${bounded(domain?.candidate_count)}`,
        ),
      );
    });
    section.append(domainList);
    section.append(
      el("h3", "nq7-section-title", "Quant evidence handles"),
      makeHandleList(payload?.quant?.handles, "No quant handles are available."),
    );
  };

  const renderOuroboros = (payload) => {
    const section = document.getElementById("nq7-section-ouroboros");
    if (!section) return;
    section.replaceChildren();
    const contract = payload?.ouroboros?.loop_contract || {};
    section.append(
      el("h3", "nq7-section-title", "Bounded frontier loop"),
      el(
        "p",
        "nq7-copy",
        "Ouroboros observes bounded iteration, terminal state, loop tax, and receipt closure. Codex is advisory review only; recommendations are not executed by this surface.",
      ),
    );
    const grid = el("div", "nq7-grid");
    grid.append(
      makeMetricCard("Bounded", contract.bounded === true ? "YES" : "NO", "Finite step budget required"),
      makeMetricCard("Terminating", contract.terminating === true ? "YES" : "NO", "Terminal exit required"),
      makeMetricCard("Receipt closed", contract.receipt_closed === true ? "YES" : "NO", "One trace in · one trace out"),
      makeMetricCard("Codex role", contract.codex_role || "UNAVAILABLE", "Advisory · no execution"),
    );
    section.append(grid);
    section.append(
      el("h3", "nq7-section-title", "Ouroboros source handles"),
      makeHandleList(payload?.ouroboros?.handles, "No Ouroboros handles are available."),
    );
  };

  const renderStatus = (payload) => {
    const statusbar = document.getElementById("nq7-statusbar");
    if (!statusbar) return;
    statusbar.replaceChildren();
    const measured = payload?.ready === true;
    statusbar.append(
      makeChip(measured ? "Measured v7" : "Unavailable", measured ? "measured" : "failed"),
      makeChip(
        `${bounded(payload?.brain?.frontier_candidate_count)} review candidates`,
        "review",
      ),
      makeChip(`${bounded(payload?.formulas?.locked_proven)} locked-proven`, "measured"),
      makeChip("Λ Conjecture 1", "review"),
      makeChip("Authority none", "measured"),
    );
  };

  const render = (payload) => {
    state.payload = payload;
    renderStatus(payload);
    drawBrain(payload);
    renderOverview(payload);
    renderFormulas(payload);
    renderQuant(payload);
    renderOuroboros(payload);
    setNodeText(
      "nq7-receipt",
      `source ${shortDigest(payload?.source_revision)} · frontier ${shortDigest(payload?.candidate_set_sha256)} · view ${shortDigest(payload?.view_sha256)}`,
    );
    activateTab(state.activeTab);
  };

  const renderError = (message) => {
    const statusbar = document.getElementById("nq7-statusbar");
    if (statusbar) {
      statusbar.replaceChildren(
        makeChip("Source unavailable", "failed"),
        makeChip("No green synthesized", "review"),
      );
    }
    TABS.forEach(([id]) => {
      const section = document.getElementById(`nq7-section-${id}`);
      if (!section) return;
      section.replaceChildren(
        el(
          "div",
          "nq7-error",
          `${message} Living Anatomy remains visible, but Neural Quant v7 is not labeled ready without exact source-bound evidence.`,
        ),
      );
    });
    setNodeText("nq7-receipt", "Exact v7 source receipt unavailable.");
  };

  const loadData = async (force = false) => {
    if (state.loading) return;
    state.loading = true;
    const refresh = document.getElementById("nq7-refresh");
    if (refresh) {
      refresh.disabled = true;
      refresh.textContent = "Loading…";
    }
    if (state.abortController) state.abortController.abort();
    state.abortController = new AbortController();
    const timeout = window.setTimeout(() => state.abortController.abort(), 12000);
    try {
      const url = force ? `${ENDPOINT}&refresh=${Date.now()}` : ENDPOINT;
      const response = await fetch(url, {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: state.abortController.signal,
      });
      const payload = await response.json();
      if (!response.ok || payload?.ready !== true) {
        throw new Error(`v7 endpoint returned ${response.status}`);
      }
      const serialized = JSON.stringify(payload).toLowerCase();
      if (serialized.includes('"content"') || serialized.includes('"text"')) {
        throw new Error("handles-only boundary failed");
      }
      render(payload);
    } catch (error) {
      const reason = error?.name === "AbortError"
        ? "The source-bound request timed out."
        : "The source-bound request failed.";
      renderError(reason);
    } finally {
      window.clearTimeout(timeout);
      state.loading = false;
      if (refresh) {
        refresh.disabled = false;
        refresh.textContent = "Refresh";
      }
    }
  };

  const init = () => {
    buildShell();
    const panel = document.getElementById(PANEL_ID);
    if (panel && window.location.hash === "#neural-quant-v7") {
      setPanelState(true);
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
