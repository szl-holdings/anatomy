/* SZL Living Anatomy · YACHAY Second Brain instrument.
 * Source-bound public projection; handles only; read-only; zero CDN.
 * Private graph nodes and corpus text never cross this boundary.
 */
(function (root) {
  "use strict";

  var API = {
    health: "/api/anatomy/v1/brain/health",
    search: "/api/anatomy/v1/brain/search",
    context: "/api/anatomy/v1/brain/context",
    living: "/api/anatomy/v1/living-health"
  };
  var SOURCE = "https://github.com/szl-holdings/szl-second-brain";
  var DATASET = "https://huggingface.co/datasets/SZLHOLDINGS/szl-second-brain-inrepo";
  var PRODUCT = "https://a-11-oy.com/living-anatomy";

  var css = [
    "#yachay-sb{position:fixed;z-index:24;right:clamp(8px,2vw,18px);bottom:clamp(8px,2vw,18px);",
    "width:min(390px,calc(100vw - 16px));font-family:ui-monospace,SFMono-Regular,Consolas,monospace;",
    "font-size:11px;line-height:1.48;color:#eef7f5;background:linear-gradient(145deg,rgba(6,11,20,.94),rgba(7,24,31,.9));",
    "border:1px solid rgba(58,244,200,.38);border-radius:15px;box-shadow:0 18px 65px rgba(0,0,0,.48),inset 0 1px rgba(255,255,255,.04);",
    "backdrop-filter:blur(14px);overflow:hidden;pointer-events:auto}",
    "#yachay-sb *{box-sizing:border-box}#yachay-sb button,#yachay-sb input{font:inherit}",
    "#yachay-sb .yh{display:flex;align-items:center;gap:9px;padding:10px 11px;border-bottom:1px solid rgba(58,244,200,.16)}",
    "#yachay-sb .orb{width:10px;height:10px;border-radius:50%;background:#758797;box-shadow:0 0 16px rgba(117,135,151,.65);flex:0 0 auto}",
    "#yachay-sb[data-state=ready] .orb{background:#3af4c8;box-shadow:0 0 18px rgba(58,244,200,.95)}",
    "#yachay-sb[data-state=failed] .orb{background:#ff6b7a;box-shadow:0 0 18px rgba(255,107,122,.8)}",
    "#yachay-sb .title{font-weight:800;letter-spacing:.09em;color:#f7fffd;flex:1}",
    "#yachay-sb .state{font-size:9px;letter-spacing:.07em;color:#8fa7b5}",
    "#yachay-sb .toggle{border:0;background:transparent;color:#9bb2bf;cursor:pointer;padding:6px 8px;border-radius:8px}",
    "#yachay-sb .toggle:focus-visible,#yachay-sb a:focus-visible,#yachay-sb input:focus-visible,#yachay-sb .go:focus-visible{outline:2px solid #3af4c8;outline-offset:2px}",
    "#yachay-sb .body{padding:11px}#yachay-sb[data-collapsed=true] .body{display:none}",
    "#yachay-sb .meta{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:9px}",
    "#yachay-sb .metric{padding:7px 8px;border:1px solid rgba(143,167,181,.13);border-radius:9px;background:rgba(255,255,255,.025)}",
    "#yachay-sb .metric b{display:block;color:#3af4c8;font-size:12px}#yachay-sb .metric span{color:#8fa7b5;font-size:9px}",
    "#yachay-sb form{display:flex;gap:6px;margin:8px 0}#yachay-sb input{min-width:0;flex:1;border:1px solid rgba(58,244,200,.25);",
    "border-radius:9px;background:rgba(0,0,0,.24);color:#eef7f5;padding:9px 10px}",
    "#yachay-sb input::placeholder{color:#728895}#yachay-sb .go{border:1px solid rgba(58,244,200,.42);border-radius:9px;",
    "background:rgba(58,244,200,.12);color:#77ffe0;padding:8px 11px;cursor:pointer;font-weight:800}",
    "#yachay-sb .results{max-height:190px;overflow:auto;margin-top:7px}#yachay-sb .hit{padding:7px 2px;border-top:1px solid rgba(143,167,181,.12)}",
    "#yachay-sb .hit:first-child{border-top:0}#yachay-sb .hit strong{display:block;color:#eafffa;font-weight:650}",
    "#yachay-sb .hit small{color:#7f98a7}#yachay-sb .honesty{margin-top:8px;color:#8097a5;font-size:9px}",
    "#yachay-sb .links{display:flex;flex-wrap:wrap;gap:9px;margin-top:9px}#yachay-sb a{color:#57f3cf;text-decoration:none}",
    "#yachay-sb .error{color:#ff9ca6}#yachay-sb .busy{color:#ffd48a}",
    "@media(max-width:520px){#yachay-sb{right:8px;bottom:8px}.yachay-hide-mobile{display:none}}",
    "@media(prefers-reduced-motion:reduce){#yachay-sb *{scroll-behavior:auto!important;transition:none!important;animation:none!important}}"
  ].join("");

  function node(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text != null) el.textContent = text;
    return el;
  }

  function cleanRevision(value) {
    return typeof value === "string" && value.length === 40 ? value.slice(0, 9) : "unbound";
  }

  function build() {
    var box = node("aside");
    box.id = "yachay-sb";
    box.dataset.state = "loading";
    box.dataset.collapsed = "false";
    box.setAttribute("aria-label", "YACHAY Second Brain instrument");

    var head = node("div", "yh");
    head.appendChild(node("span", "orb"));
    head.appendChild(node("div", "title", "YACHAY · SECOND BRAIN"));
    var state = node("span", "state", "CONNECTING");
    state.setAttribute("aria-live", "polite");
    head.appendChild(state);
    var toggle = node("button", "toggle", "–");
    toggle.type = "button";
    toggle.setAttribute("aria-label", "Collapse Second Brain instrument");
    head.appendChild(toggle);
    box.appendChild(head);

    var body = node("div", "body");
    var meta = node("div", "meta");
    var chunks = node("div", "metric");
    var chunksValue = node("b", "", "—");
    chunks.appendChild(chunksValue);
    chunks.appendChild(node("span", "", "PUBLIC HANDLES"));
    var revision = node("div", "metric");
    var revisionValue = node("b", "", "—");
    revision.appendChild(revisionValue);
    revision.appendChild(node("span", "", "SOURCE SHA"));
    meta.appendChild(chunks);
    meta.appendChild(revision);
    body.appendChild(meta);

    var form = document.createElement("form");
    form.setAttribute("role", "search");
    var input = document.createElement("input");
    input.type = "search";
    input.maxLength = 500;
    input.placeholder = "Ask the public Second Brain…";
    input.setAttribute("aria-label", "Search Second Brain public handles");
    var go = node("button", "go", "GROUND");
    go.type = "submit";
    form.appendChild(input);
    form.appendChild(go);
    body.appendChild(form);

    var results = node("div", "results");
    results.setAttribute("aria-live", "polite");
    results.appendChild(node("div", "honesty", "Loading the source-bound public projection…"));
    body.appendChild(results);

    var links = node("div", "links");
    [
      ["Living Anatomy", PRODUCT],
      ["Source", SOURCE],
      ["Dataset", DATASET]
    ].forEach(function (pair) {
      var a = node("a", "", pair[0] + " ↗");
      a.href = pair[1];
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      links.appendChild(a);
    });
    body.appendChild(links);
    body.appendChild(node(
      "div",
      "honesty",
      "READ-ONLY · HANDLES ONLY · lexical relevance ≠ correctness · private graph excluded · Λ remains Conjecture 1."
    ));
    box.appendChild(body);

    toggle.addEventListener("click", function () {
      var collapsed = box.dataset.collapsed === "true";
      box.dataset.collapsed = collapsed ? "false" : "true";
      toggle.textContent = collapsed ? "–" : "+";
      toggle.setAttribute(
        "aria-label",
        collapsed ? "Collapse Second Brain instrument" : "Expand Second Brain instrument"
      );
    });

    function renderHits(payload) {
      while (results.firstChild) results.removeChild(results.firstChild);
      var handles = payload && Array.isArray(payload.handles) ? payload.handles : [];
      if (!handles.length) {
        results.appendChild(node("div", "honesty", "No public handle matched. Nothing fabricated."));
        return;
      }
      handles.forEach(function (handle, index) {
        var row = node("div", "hit");
        row.appendChild(node("strong", "", handle.note || handle.nodeId || "Untitled handle"));
        row.appendChild(node(
          "small",
          "",
          (handle.source || "unknown") + " · " +
          (handle.nodeId || "no-id") + " · score " +
          (payload.scores && payload.scores[index] != null ? payload.scores[index] : "—")
        ));
        results.appendChild(row);
      });
    }

    function setFailure(message) {
      box.dataset.state = "failed";
      state.textContent = "UNAVAILABLE";
      while (results.firstChild) results.removeChild(results.firstChild);
      results.appendChild(node("div", "error", message || "Second Brain contract unavailable."));
    }

    function health() {
      fetch(API.health, {cache: "no-store", headers: {"Accept": "application/json"}})
        .then(function (response) {
          if (!response.ok) throw new Error("health " + response.status);
          return response.json();
        })
        .then(function (payload) {
          if (!payload.ready) throw new Error(payload.load_error || "snapshot not ready");
          box.dataset.state = "ready";
          state.textContent = "SOURCE-BOUND";
          chunksValue.textContent = String(payload.chunk_count);
          revisionValue.textContent = cleanRevision(payload.source_revision);
          while (results.firstChild) results.removeChild(results.firstChild);
          results.appendChild(node(
            "div",
            "honesty",
            "Brain organ ready. Search returns public source handles, not hidden text."
          ));
        })
        .catch(function (error) {
          setFailure("Brain organ unavailable: " + error.message);
        });
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var query = input.value.trim();
      if (!query) return;
      while (results.firstChild) results.removeChild(results.firstChild);
      results.appendChild(node("div", "busy", "Grounding public handles…"));
      fetch(API.search + "?q=" + encodeURIComponent(query) + "&k=6", {
        cache: "no-store",
        headers: {"Accept": "application/json"}
      })
        .then(function (response) {
          if (!response.ok) throw new Error("search " + response.status);
          return response.json();
        })
        .then(renderHits)
        .catch(function (error) {
          setFailure("Search unavailable: " + error.message);
        });
    });

    return {box: box, health: health};
  }

  function mount() {
    if (!document.body || document.getElementById("yachay-sb")) return;
    var instrument = build();
    document.body.appendChild(instrument.box);
    instrument.health();
  }

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount, {once: true});
  } else {
    mount();
  }

  root.SZL_YACHAY_SECOND_BRAIN = {
    kind: "SOFTWARE",
    authority: "READ_ONLY",
    contentAccess: "HANDLES_ONLY",
    endpoints: API,
    source: SOURCE,
    dataset: DATASET,
    product: PRODUCT
  };
})(typeof window !== "undefined" ? window : this);
