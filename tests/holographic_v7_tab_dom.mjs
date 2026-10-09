// Executes holographic-v7.js against a small DOM and checks tab relationships.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const source = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "holographic-v7.js"), "utf8");

class El {
  constructor(tag) {
    this.tagName = String(tag || "div").toUpperCase();
    this.children = [];
    this.attrs = {};
    this.parent = null;
    this.listeners = {};
    this.hidden = false;
    this._tabIndex = 0;
    this.dataset = {};
    this.style = {};
    this.className = "";
    this.id = "";
    this.text = "";
  }
  setAttribute(name, value) {
    const key = String(name);
    const text = String(value);
    this.attrs[key] = text;
    if (key === "id") this.id = text;
    if (key === "class") this.className = text;
    if (key === "hidden") this.hidden = true;
    if (key === "tabindex") this._tabIndex = Number(text);
    if (key.startsWith("data-")) this.dataset[key.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = text;
  }
  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null;
  }
  removeAttribute(name) {
    delete this.attrs[name];
    if (name === "hidden") this.hidden = false;
  }
  get tabIndex() {
    return this._tabIndex;
  }
  set tabIndex(value) {
    this._tabIndex = value;
    this.attrs.tabindex = String(value);
  }
  append(...nodes) {
    for (const node of nodes) {
      node.parent = this;
      this.children.push(node);
    }
  }
  set textContent(value) {
    this.text = String(value);
    this.children = [];
  }
  get textContent() {
    return this.text + this.children.map((child) => child.textContent).join("");
  }
  set innerHTML(html) {
    const parsed = parseHtml(html);
    this.children = parsed.children;
    for (const child of this.children) child.parent = this;
  }
  addEventListener(type, fn) {
    (this.listeners[type] ||= []).push(fn);
  }
  querySelector(selector) {
    return walk(this).find((node) => matches(node, selector)) || null;
  }
  querySelectorAll(selector) {
    return walk(this).filter((node) => matches(node, selector));
  }
  closest(selector) {
    let node = this;
    while (node) {
      if (matches(node, selector)) return node;
      node = node.parent;
    }
    return null;
  }
  focus() {
    document.activeElement = this;
  }
  getClientRects() {
    return this.hidden ? [] : [{}];
  }
}

function walk(node, acc = []) {
  acc.push(node);
  for (const child of node.children) walk(child, acc);
  return acc;
}

function matches(node, selector) {
  if (selector.includes(",")) return selector.split(",").some((part) => matches(node, part.trim()));
  let rest = selector;
  let ok = true;
  if (rest.startsWith(".")) {
    const cls = rest.slice(1);
    ok = node.className.split(/\s+/).includes(cls);
  } else if (rest.startsWith("[")) {
    ok = attrMatch(node, rest);
  } else if (rest.startsWith("button")) {
    ok = node.tagName === "BUTTON";
    rest = rest.slice("button".length);
    if (rest.startsWith(":not([disabled])")) ok = ok && node.getAttribute("disabled") === null;
  } else if (rest.startsWith("[href]")) {
    ok = node.getAttribute("href") !== null;
  } else {
    ok = false;
  }
  return ok;
}

function attrMatch(node, selector) {
  const named = selector.match(/^\[([^\=\]]+)(?:="([^"]*)")?\](?::not\(\[([^\=\]]+)(?:="([^"]*)")?\]\))?$/);
  if (!named) return false;
  const [, name, value, notName, notValue] = named;
  const actual = node.getAttribute(name);
  if (value === undefined ? actual === null : actual !== value) return false;
  if (!notName) return true;
  const negated = node.getAttribute(notName);
  if (notValue === undefined) return negated === null;
  return negated !== notValue;
}

function parseHtml(html) {
  const root = new El("fragment");
  const stack = [root];
  const re = /<!--[\s\S]*?-->|<\/([a-zA-Z0-9]+)>|<([a-zA-Z0-9]+)([^>]*?)\/?>|([^<]+)/g;
  let match;
  while ((match = re.exec(html))) {
    if (match[1]) {
      const name = match[1].toUpperCase();
      while (stack.length > 1 && stack.at(-1).tagName !== name) stack.pop();
      if (stack.length > 1) stack.pop();
      continue;
    }
    if (match[2]) {
      const el = new El(match[2]);
      for (const attr of match[3].matchAll(/([^\s=\/]+)(?:="([^"]*)")?/g)) {
        el.setAttribute(attr[1], attr[2] ?? "");
      }
      stack.at(-1).append(el);
      const selfClose = match[0].endsWith("/>") || ["BR", "IMG", "INPUT", "CANVAS"].includes(el.tagName);
      if (!selfClose) stack.push(el);
      continue;
    }
    if (match[4] && match[4].trim()) stack.at(-1).text += match[4];
  }
  return root;
}

function byId(id, root) {
  return walk(root).find((node) => node.id === id) || null;
}

const document = {
  readyState: "complete",
  visibilityState: "visible",
  activeElement: null,
  documentElement: new El("html"),
  body: new El("body"),
  addEventListener() {},
  createElement(tag) {
    return new El(tag);
  },
  getElementById(id) {
    return byId(id, document.body);
  },
  querySelector(selector) {
    return document.body.querySelector(selector);
  },
  querySelectorAll(selector) {
    return document.body.querySelectorAll(selector);
  },
};

const windowStub = {
  document,
  matchMedia() {
    return { matches: false, addEventListener() {} };
  },
  setTimeout() {
    return 1;
  },
  clearTimeout() {},
  setInterval() {
    return 1;
  },
  requestAnimationFrame() {
    return 1;
  },
  cancelAnimationFrame() {},
  devicePixelRatio: 1,
  location: { origin: "https://example.test" },
};
windowStub.window = windowStub;
globalThis.window = windowStub;
globalThis.document = document;
globalThis.ResizeObserver = class {
  observe() {}
  disconnect() {}
};

vm.runInThisContext(source, { filename: "holographic-v7.js" });

const tabs = document.querySelectorAll(".szl-v7__tab");
const controls = tabs.map((tab) => ({
  id: tab.id,
  label: tab.textContent.trim(),
  controls: tab.getAttribute("aria-controls"),
  selected: tab.getAttribute("aria-selected"),
  tabIndex: tab.tabIndex,
  role: tab.getAttribute("role"),
  targetExists: document.getElementById(tab.getAttribute("aria-controls")) !== null,
  targetRole: document.getElementById(tab.getAttribute("aria-controls"))?.getAttribute("role") || null,
  targetLabel: document.getElementById(tab.getAttribute("aria-controls"))?.getAttribute("aria-labelledby") || null,
  targetHidden: document.getElementById(tab.getAttribute("aria-controls"))?.hidden === true,
}));

function press(key, tab) {
  const hud = document.getElementById("szl-v7-hud");
  const event = { key, target: tab, preventDefault() { this.defaultPrevented = true; } };
  for (const fn of hud.listeners.keydown || []) fn(event);
}

press("ArrowRight", tabs[0]);
const afterRight = document.querySelectorAll(".szl-v7__tab").map((tab) => ({
  id: tab.id,
  selected: tab.getAttribute("aria-selected"),
  tabIndex: tab.tabIndex,
  focused: document.activeElement === tab,
  panelHidden: document.getElementById(tab.getAttribute("aria-controls")).hidden,
  panelLabel: document.getElementById(tab.getAttribute("aria-controls")).getAttribute("aria-labelledby"),
}));
press("End", document.querySelectorAll(".szl-v7__tab")[1]);
const afterEnd = document.querySelectorAll(".szl-v7__tab").map((tab) => ({
  id: tab.id,
  selected: tab.getAttribute("aria-selected"),
  focused: document.activeElement === tab,
}));
press("Home", document.querySelectorAll(".szl-v7__tab").at(-1));
const afterHome = document.querySelectorAll(".szl-v7__tab")[0];

const report = {
  tablist: document.body.querySelector('[role="tablist"]') !== null,
  orphanPanelAbsent: document.getElementById("szl-v7-panel") === null,
  controls,
  everyTargetExists: controls.every((item) => item.targetExists && item.targetRole === "tabpanel"),
  afterRight,
  afterEnd,
  homeSelected: afterHome.getAttribute("aria-selected") === "true" && document.activeElement === afterHome,
};
const failures = [];
if (!report.tablist) failures.push("missing tablist");
if (!report.orphanPanelAbsent) failures.push("legacy panel id still exists");
if (!report.everyTargetExists) failures.push("aria-controls target missing");
if (controls.length !== 4) failures.push("expected four tabs");
if (controls.some((item) => item.role !== "tab")) failures.push("tab role missing");
if (afterRight[1].selected !== "true" || !afterRight[1].focused || afterRight[1].panelHidden) failures.push("arrow selection failed");
if (afterRight[1].panelLabel !== "szl-v7-tab-formulas") failures.push("panel name was not updated");
if (afterRight.filter((item) => !item.panelHidden).length !== 1) failures.push("more than one panel visible");
if (afterEnd.at(-1).selected !== "true" || !afterEnd.at(-1).focused) failures.push("end key failed");
if (!report.homeSelected) failures.push("home key failed");
if (failures.length) {
  console.error(JSON.stringify({ failures, report }, null, 2));
  process.exit(1);
}
console.log(JSON.stringify(report));
