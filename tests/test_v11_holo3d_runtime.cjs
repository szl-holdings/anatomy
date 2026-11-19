// SPDX-License-Identifier: Apache-2.0
// Behavioral checks against the exact shipped v11 Holo client. No browser, CDN,
// provider calls, secrets, training, or production effects.
"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const SOURCE = fs.readFileSync(path.join(__dirname, "..", "v11_holo3d.js"), "utf8");

class Element {
  constructor(id = "") {
    this.id = id; this.children = []; this.events = new Map();
    this.attributes = {}; this.hidden = false; this.textContent = "";
    this.className = ""; this.style = {}; this.clientWidth = 420; this.clientHeight = 320;
    this.classList = { add: () => {}, remove: () => {} };
  }
  addEventListener(name, cb) { this.events.set(name, cb); }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = [...children]; }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() {}
  querySelector(name) { return name === ".stage" ? this.stage : null; }
}

function handles(kind, count) {
  return Array.from({ length: count }, (_, i) => ({
    nodeId: "frontier:" + (i + (kind === "formula" ? 10 : kind === "loop" ? 20 : 0)).toString(16).padStart(32, "0"),
    contentAccess: "HANDLES_ONLY",
    candidateState: "DISCOVERED_REVIEW_REQUIRED",
    kind,
  }));
}

function state(ready, kind, count) {
  return {ready, content_access:"HANDLES_ONLY", handles:handles(kind,count)};
}

async function mount(feeds) {
  const ids = {};
  for(const id of ["v11-holo-fab", "v11-holo", "v11-holo-close",
                   "v11-holo-canvas", "v11-holo-hud", "v11-holo-offline", "v11-holo-tip"])
    ids[id] = new Element(id);
  ids["v11-holo"].stage = new Element("holo-stage");
  let observedFetches = [];
  const fakeFetch = async (url, opts) => {
    observedFetches.push({url, opts});
    const key = url.includes("/holographic-v7") ? "status"
      : url.includes("/frontier/handles") ? "handles"
      : url.includes("/frontier/formulas") ? "formulas" : "loops";
    const value = feeds[key];
    if (value instanceof Error) throw value;
    if (typeof value === "number") return {
      ok:false, status:value,
      headers:{ get:()=> "application/json" },
      json:async()=>({}),
    };
    return {
      ok:true, status:200,
      headers:{ get:()=>"application/json" },
      json:async()=>value,
    };
  };
  const window = {
    location:{origin:"https://szlholdings-anatomy.hf.space"},
    matchMedia:()=>({matches:false}),
    setTimeout,clearTimeout,
    addEventListener:()=>{},
    THREE:undefined,
  };
  const document = {
    readyState:"complete",
    activeElement:ids["v11-holo-fab"],
    body:{contains:()=>true},
    getElementById:(id)=>ids[id]||null,
    createElement:(tag)=> {
      const elem=new Element();
      const setId=Object.getOwnPropertyDescriptor(elem,"id");
      // ID assigned after append via the script; retrieve it from stage.
      Object.defineProperty(elem,"id",{
        configurable:true,enumerable:true,get(){return this._id||"";},
        set(v){this._id=v;ids[v]=this;}
      });
      return elem;
    },
  };
  const sandbox={window,document,fetch:fakeFetch,AbortController,
    cancelAnimationFrame:()=>{},requestAnimationFrame:()=>0,
    setTimeout,clearTimeout,
  };
  vm.runInNewContext(SOURCE,sandbox,{filename:"v11_holo3d.js",timeout:1000});
  ids["v11-holo-fab"].events.get("click")();
  for(let i=0;i<8;i++) await new Promise(resolve=>setImmediate(resolve));
  const fallback=ids["v11-holo-fallback"];
  const fallbackText=fallback ? fallback.children.map(e=>String(e.textContent || "")).join(" | ") : "";
  const hudText=ids["v11-holo-hud"].children.map(e=>String(e.textContent || "")).join(" | ");
  return { ids, fallback, fallbackText,hudText,observedFetches };
}

const good=()=> ({
  status:{ready:true,frontier:{ready:true}},
  handles:state(true,"source-document",2),
  formulas:state(true,"attributed-formula",3),
  loops:state(true,"source-document",1),
});

test("working four native endpoints and missing WebGL show evidence, not chain down",async()=>{
  const result=await mount(good());
  assert.ok(result.fallback);
  assert.match(result.fallbackText,/3D rendering unavailable/);
  assert.match(result.fallbackText,/handles 2/);
  assert.match(result.fallbackText,/formulas 3/);
  assert.match(result.fallbackText,/loops 1/);
  assert.equal(result.ids["v11-holo-offline"].hidden,true);
  assert.doesNotMatch(result.hudText,/CHAIN UNREACHABLE/);
  assert.ok(result.observedFetches.every(x=>x.opts.credentials==="same-origin" &&
    x.opts.cache==="no-store" && x.opts.redirect==="error"));
});

test("one optional feed failure does not blank healthy Brain and loop handles",async()=>{
  const feeds=good();
  feeds.formulas=new Error("UNAVAILABLE");
  const result=await mount(feeds);
  assert.match(result.fallbackText,/handles 2/);
  assert.match(result.fallbackText,/loops 1/);
  assert.match(result.hudText,/DEGRADED SOURCE FEEDS: formulas/);
  assert.equal(result.ids["v11-holo-offline"].hidden,true);
});

test("source not ready is explicit HOLD and never a green renderer",async()=>{
  const feeds=good();feeds.status={ready:false,frontier:{ready:false}};
  const result=await mount(feeds);
  assert.match(result.hudText,/SOURCE STATUS HOLD/);
  assert.match(result.fallbackText,/Source status unverified/);
  assert.doesNotMatch(result.hudText,/handles 2/);
});

test("all feeds unavailable remain fail closed",async()=>{
  const feeds={status:new Error("unavailable"),handles:new Error("unavailable"),
    formulas:new Error("unavailable"),loops:new Error("unavailable")};
  const result=await mount(feeds);
  assert.equal(result.ids["v11-holo-offline"].hidden,false);
  assert.match(result.hudText,/SOURCE FEEDS UNAVAILABLE/);
  assert.match(result.fallbackText,/no data fabricated/);
});

test("untrusted body row and model output never enter fallback",async()=>{
  const feeds=good();
  feeds.handles.handles.push({
    nodeId:"frontier:"+"9".repeat(32),
    contentAccess:"RAW_CONTENT",
    content:"NEVER_RENDER_THIS_PRIVATE_DATA",
  });
  const result=await mount(feeds);
  assert.match(result.fallbackText,/handles 2/);
  assert.doesNotMatch(result.fallbackText,/NEVER_RENDER_THIS_PRIVATE_DATA/);
});

test("native formula and Ouroboros handles envelope is parsed",async()=>{
  const result=await mount(good());
  assert.match(result.fallbackText,/formulas 3/);
  assert.match(result.fallbackText,/loops 1/);
  assert.equal(result.observedFetches.length,4);
});