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
    this.id = id; this.tagName = id; this.children = []; this.events = new Map();
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
  querySelectorAll(name) {
    if (name !== "a[href], button:not([disabled])") return [];
    return this.children.filter(e => e.tagName === "a" || e.tagName === "button");
  }
}

function handles(kind, count) {
  return Array.from({ length: count }, (_, i) => ({
    nodeId: "frontier:" + (i + (kind === "formula" ? 10 : kind === "loop" ? 20 : 0)).toString(16).padStart(32, "0"),
    contentAccess: "HANDLES_ONLY",
    candidateState: "DISCOVERED_REVIEW_REQUIRED",
    kind,
  }));
}

const SOURCE_REVISION = "a".repeat(40);
const CANDIDATE_DIGEST = "b".repeat(64);

function state(ready, kind, count) {
  return {
    schema:"szl.anatomy.frontier-handles/v1",state:"REVIEW_REQUIRED",
    ready,content_access:"HANDLES_ONLY",anatomy_surface:"HOLOGRAPHIC_V7",
    execution_authority:"NONE",promotion_authority:"NONE",training_authority:"NONE",
    candidate_set_sha256:CANDIDATE_DIGEST,returned_count:count,
    handles:handles(kind,count),
  };
}

function witness() {
  return {
    schema:"szl.anatomy.frontier-status/v1",state:"SOURCE_BOUND_REVIEW_MEMORY",
    ready:true,authority:"READ_ONLY",content_access:"HANDLES_ONLY",
    anatomy_surface:"HOLOGRAPHIC_V7",execution_authority:"NONE",
    promotion_authority:"NONE",training_authority:"NONE",
    second_brain_source_repository:"szl-holdings/szl-second-brain",
    second_brain_source_revision:SOURCE_REVISION,
    candidate_set_sha256:CANDIDATE_DIGEST,candidate_count:144,
  };
}

async function mount(feeds) {
  const ids = {};
  for(const id of ["v11-holo-fab", "v11-holo", "v11-holo-close",
                   "v11-holo-canvas", "v11-holo-hud", "v11-holo-offline", "v11-holo-tip"])
    ids[id] = new Element(id);
  ids["v11-holo"].stage = new Element("holo-stage");
  let observedFetches = [];
  let scheduledFrames = 0;
  const fakeFetch = async (url, opts) => {
    observedFetches.push({url, opts});
    const key = url.includes("/holographic-v7") ? "status"
      : url.includes("/frontier/status") ? "witness"
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
      const elem=new Element(tag);

      // ID assigned after append via the script; retrieve it from stage.
      Object.defineProperty(elem,"id",{
        configurable:true,enumerable:true,get(){return this._id||"";},
        set(v){this._id=v;ids[v]=this;}
      });
      return elem;
    },
  };
  const sandbox={window,document,fetch:fakeFetch,AbortController,
    cancelAnimationFrame:()=>{},requestAnimationFrame:()=>++scheduledFrames,
    setTimeout,clearTimeout,
  };
  vm.runInNewContext(SOURCE,sandbox,{filename:"v11_holo3d.js",timeout:1000});
  ids["v11-holo-fab"].events.get("click")();
  for(let i=0;i<8;i++) await new Promise(resolve=>setImmediate(resolve));
  const fallback=ids["v11-holo-fallback"];
  const fallbackText=fallback ? fallback.children.map(e=>String(e.textContent || "")).join(" | ") : "";
  const hudText=ids["v11-holo-hud"].children.map(e=>String(e.textContent || "")).join(" | ");
  return { ids, fallback, fallbackText,hudText,observedFetches,
    document, window, sandbox, frames:()=>scheduledFrames };
}

const good=()=> ({
  status:{
    schema:"szl.anatomy.holographic-v7/v1",state:"SOURCE_BOUND_READ_ONLY",
    ready:true,claims:{claim_promoted:false,content_exposed:false,
      execution_performed:false,weights_trained:false},
    frontier:witness(),
  },
  witness:witness(),
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
  assert.match(result.fallbackText,/handles 0/);
  assert.doesNotMatch(result.fallbackText,/frontier:/);
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
  assert.match(result.fallbackText,/handles 0/);
  assert.match(result.hudText,/DEGRADED SOURCE FEEDS: handles/);
  assert.doesNotMatch(result.fallbackText,/NEVER_RENDER_THIS_PRIVATE_DATA/);
});

test("extra opaque fields on valid handles are not surfaced",async()=>{
  const feeds=good();
  feeds.handles.handles[0].privateCandidate="DO_NOT_EXPOSE_SOURCE_TEXT";
  const result=await mount(feeds);
  assert.match(result.fallbackText,/handles 2/);
  assert.match(result.hudText,/SOURCE SNAPSHOTS MATCH/);
  assert.doesNotMatch(result.fallbackText,/DO_NOT_EXPOSE_SOURCE_TEXT/);
  assert.doesNotMatch(result.hudText,/DO_NOT_EXPOSE_SOURCE_TEXT/);
});

test("non-string handle identities are rejected even when coerced to safe text",async()=>{
  const feeds=good();
  feeds.handles.handles[0].nodeId=new String("frontier:"+"f".repeat(32));
  const result=await mount(feeds);
  assert.match(result.hudText,/DEGRADED SOURCE FEEDS: handles/);
  assert.match(result.fallbackText,/handles 0/);
});

test("native formula and Ouroboros handles envelope is parsed",async()=>{
  const result=await mount(good());
  assert.match(result.fallbackText,/formulas 3/);
  assert.match(result.fallbackText,/loops 1/);
  assert.equal(result.observedFetches.length,5);
});

test("HTTP 200 with invalid formula feed remains degraded, not green",async()=>{
  const feeds=good();
  feeds.formulas={ready:false,content_access:"HANDLES_ONLY",handles:handles("attributed-formula",3)};
  const result=await mount(feeds);
  assert.match(result.hudText,/DEGRADED SOURCE FEEDS: formulas/);
  assert.match(result.fallbackText,/formulas 0/);
  assert.match(result.fallbackText,/handles 2/);
  assert.equal(result.ids["v11-holo-offline"].hidden,true);
});
test("paired source metadata agrees, without signing or model claims",async()=>{
  const result=await mount(good());
  assert.match(result.hudText,/SOURCE SNAPSHOTS MATCH/);
  assert.match(result.hudText,/unsigned metadata/);
  assert.doesNotMatch(result.hudText,/SIGNED_MODEL_READY|PRODUCTION_READY/);
  assert.ok(result.observedFetches.some(x=>x.url==="/api/anatomy/v1/frontier/status"));
});

test("revision, digest, count, schema and authority drift each fail closed",async(t)=>{
  const corruptions=[
    ["revision",(f)=>{f.witness.second_brain_source_revision="c".repeat(40);}],
    ["candidate set digest",(f)=>{f.witness.candidate_set_sha256="d".repeat(64);}],
    ["candidate count",(f)=>{f.witness.candidate_count+=1;}],
    ["schema",(f)=>{f.witness.schema="untrusted";}],
    ["authority",(f)=>{f.witness.authority="EXECUTE";}],
    ["malformed revision",(f)=>{f.witness.second_brain_source_revision="invalid";}],
    ["unready witness",(f)=>{f.witness.ready=false;}],
    ["unexpected training claim",(f)=>{f.witness.training_authority="TRAIN";}],
    ["promoted source claim",(f)=>{f.status.claims.claim_promoted=true;}],
  ];
  for(const [label,mutate] of corruptions){
    await t.test(label,async()=>{
      const feeds=good();mutate(feeds);
      const result=await mount(feeds);
      assert.match(result.hudText,/SOURCE COHERENCE HOLD/);
      assert.match(result.fallbackText,/Source snapshots unavailable or inconsistent/);
      assert.match(result.fallbackText,/handles 0/);
      assert.doesNotMatch(result.fallbackText,/frontier:/);
      assert.equal(result.frames(),0);
    });
  }
});

test("HTTP 503, missing or malformed witness never implies source recovery",async(t)=>{
  for(const witnessFailure of [503,new Error("UNAVAILABLE"),undefined,{ready:true}]){
    await t.test(String(witnessFailure),async()=>{
      const feeds=good();feeds.witness=witnessFailure;
      const result=await mount(feeds);
      assert.match(result.hudText,/SOURCE COHERENCE HOLD/);
      assert.match(result.fallbackText,/handles 0/);
      assert.equal(result.frames(),0);
    });
  }
});

test("duplicate handle IDs never survive the per-feed admission gate",async()=>{
  const feeds=good();
  feeds.formulas.handles[1].nodeId=feeds.formulas.handles[0].nodeId;
  const result=await mount(feeds);
  assert.match(result.hudText,/DEGRADED SOURCE FEEDS: formulas/);
  assert.match(result.fallbackText,/handles 2/);
  assert.match(result.fallbackText,/formulas 0/);
  assert.match(result.fallbackText,/loops 1/);
});

test("stale optional feed digest is isolated, with valid feeds retained",async()=>{
  const feeds=good();feeds.formulas.candidate_set_sha256="d".repeat(64);
  const result=await mount(feeds);
  assert.match(result.hudText,/DEGRADED SOURCE FEEDS: formulas/);
  assert.match(result.hudText,/SOURCE SNAPSHOTS MATCH/);
  assert.match(result.fallbackText,/handles 2/);
  assert.match(result.fallbackText,/formulas 0/);
  assert.match(result.fallbackText,/loops 1/);
});

test("matching candidate digest cannot launder malformed optional handle data",async()=>{
  const feeds=good();feeds.loops.handles[0].contentAccess="RAW_CONTENT";
  feeds.loops.handles[0].secret="UNTRUSTED_NEVER_RENDER";
  const result=await mount(feeds);
  assert.match(result.hudText,/DEGRADED SOURCE FEEDS: loops/);
  assert.match(result.fallbackText,/handles 2/);
  assert.match(result.fallbackText,/loops 0/);
  assert.doesNotMatch(result.fallbackText,/UNTRUSTED_NEVER_RENDER/);
});

test("fallback keyboard trap reaches evidence link and retry, not WebGL canvas",async()=>{
  const {ids,fallback,document}=await mount(good());
  const close=ids["v11-holo-close"], canvas=ids["v11-holo-canvas"];
  const link=fallback.children.find(e=>e.tagName==="a");
  const retry=fallback.children.find(e=>e.tagName==="button");
  assert.ok(link && retry);
  let focused=null;
  for(const el of [close,canvas,link,retry]) el.focus=()=>{focused=el;};
  const keydown=ids["v11-holo"].events.get("keydown");
  const tab=()=>keydown({key:"Tab",shiftKey:false,preventDefault(){}});
  document.activeElement=close;tab();assert.equal(focused,link);
  document.activeElement=link;tab();assert.equal(focused,retry);
  document.activeElement=retry;tab();assert.equal(focused,close);
  assert.notEqual(focused,canvas);
});

function threeStub() {
  const metrics={resizes:0};
  class Object3D {
    constructor(){this.children=[];this.rotation={x:0,y:0};this.position={set(){}};}
    add(node){this.children.push(node);}
  }
  class Renderer {setPixelRatio(){} setSize(){metrics.resizes++;} dispose(){} render(){}}
  class Camera extends Object3D {updateProjectionMatrix(){}}
  class Geometry {setAttribute(){}}
  class Material {constructor(opts){this.uniforms=opts?.uniforms||{};}}
  const Simple=class {};
  return {metrics,
    WebGLRenderer:Renderer,Scene:Object3D,PerspectiveCamera:Camera,
    Group:Object3D,Color:Simple,BufferGeometry:Geometry,BufferAttribute:Simple,
    ShaderMaterial:Material,Points:Simple,LineSegments:Simple,
    LineBasicMaterial:Simple,Mesh:Simple,IcosahedronGeometry:Simple,
    MeshBasicMaterial:Simple,AdditiveBlending:1};
}

test("retry after WebGL recovers sizes and schedules the renderer",async()=>{
  const result=await mount(good());
  assert.ok(result.fallback);
  assert.equal(result.frames(),0);
  const stub=threeStub();
  result.window.THREE=stub;
  result.sandbox.THREE=stub;
  result.fallback.children.find(e=>e.tagName==="button").events.get("click")();
  for(let i=0;i<12;i++) await new Promise(resolve=>setImmediate(resolve));
  assert.ok(stub.metrics.resizes>0,"Recovered renderer must have nonzero-size initialization");
  assert.ok(result.frames()>0,"Recovered renderer must have a render-loop request");
});
