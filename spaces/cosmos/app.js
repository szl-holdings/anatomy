/* ============================================================================
 * app.js — SZL COSMOS · Hanan Pacha  (sovereign 3D, vendored Three.js + bloom)
 *
 * CONSOLIDATION: folds three former Spaces into ONE holographic destination —
 *   - org-map            -> the ORG CONSTELLATION layer (live HF Spaces as nodes)
 *   - cathedral          -> the brain-sun + internal capabilities + field node
 *   - khipu-constellation-> the receipt-star constellation + cord arcs (DAG)
 *
 * UPGRADE over cathedral:
 *   - REAL postprocessing bloom (EffectComposer + UnrealBloomPass + OutputPass),
 *     all MIT, VENDORED under ./vendor — still 0 CDN at runtime.
 *   - Holographic shader material: fresnel edge + iridescent hue shift +
 *     scanlines + subtle projection flicker (light, not matter).
 *   - A polar hologram floor grid for depth.
 *
 * HONESTY DOCTRINE v11 (machine-checked against live endpoints):
 *   Λ = Conjecture 1 (advisory, NOT a theorem).  Khipu BFT = Conjecture 2.
 *   locked-proven kernel = EXACTLY 8.  Trust = conformal (never 100%, NOT Hoeffding).
 *   Org constellation = anonymous cached public metadata with provider stages; live health is
 *   polled only for CORS-open endpoints (a11oy, killinchu). Nothing fabricated.
 *
 * Sovereign: Three.js r160 (MIT) + OrbitControls + postprocessing vendored. NO CDN.
 * ========================================================================== */
import * as THREE from 'three';
import { OrbitControls }    from 'three/addons/OrbitControls.js';
import { EffectComposer }   from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }       from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass }  from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass }       from 'three/addons/postprocessing/OutputPass.js';

const REDUCED  = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------- boot safety net (registered FIRST) ----------------------------- */
window.addEventListener('error', function(){
  var b = document.getElementById('boot');
  if (b && !b.classList.contains('hide')){
    b.innerHTML =
      '<div class="b1">SZL COSMOS</div>' +
      '<div class="b2" style="max-width:40ch;margin:12px auto 0">This hologram needs a WebGL-capable browser. The honest live data, proofs &amp; receipts are one tap away.</div>' +
      '<div style="margin-top:16px;font:13px/2 ui-monospace,Menlo,monospace">' +
      '<a href="https://szlholdings-a11oy.hf.space" style="color:#3af4c8;text-decoration:none">a11oy · command platform \u2197</a><br>' +
      '<a href="https://huggingface.co/SZLHOLDINGS" style="color:#3af4c8;text-decoration:none">all SZL Spaces \u2197</a></div>';
  }
});

/* ---------- canonical content (proven anatomy, surfaced honestly) ----------- */
const CAPABILITIES = [
  { id:'reasoning', title:'Reasoning & Provenance', color:0x5cc4bf, angle:0,
    plain:'Grounded reasoning, memory/recall and provenance over a signed knowledge base — an internal a11oy function.',
    functions:['grounded ask (cites its source, refuses to fabricate)','13-axis Trust Score (geometric-mean aggregate, floor 0.90)','knowledge ontology (axioms → theorems → formulas)','model router (5-tier, cost-aware)'],
    proof:['Trust-Score CI from CONFORMAL (W5-3 + W7-4) — distribution-free, anti-overconfidence floor (never 100%, NOT Hoeffding)','Model-Router stability C20 + PAC-Bayes/router envelope W7-5 (min ≤ avg ≤ max)','Ontology label-invariance: F-G2 / F-G4 / F-G6 / W7-1'] },
  { id:'policy', title:'Policy & Compliance', color:0xd7b96b, angle:2.094,
    plain:'Deny-by-default safety gates and full ALLOW/DENY verdicts with signed receipts — an internal a11oy function.',
    functions:['8 deny-by-default safety gates','full verdict (ALLOW / DENY) with signals + receipt hash','30-signature threat corpus (MITRE ATT&CK + CVSS)','readiness / compliance (NIST / STIG / ISO)'],
    proof:['Gate-soundness P2 — no action without BOTH policy AND kernel/doctrine check; a single DENY is absorbing','Agentic-loop P3 non-interference — poisoned input provably cannot flip a DENY into an ALLOW'] },
  { id:'operator', title:'Operator · Ask / Act / Approvals', color:0x5b8dee, angle:4.189,
    plain:'The governed run loop: ask, act with approvals, and emit replayable signed receipts — an internal a11oy function.',
    functions:['governed run loop P1–P6 (sign → gate → chain → memory → replay)','human approvals gate for high-impact actions','replayable, hash-chained receipts (Khipu)','governed agentic coder (P1–P6), open-weight models'],
    proof:['Agentic-loop P1–P6 (PR #188): 28 kernel-verified theorems — run is auditable, gate-sound, injection-resistant end-to-end','P5 replay-determinism gated only by declared hashFn_collision_resistant axiom (named, not a hardness proof)'] }
];

const A11OY = {
  id:'a11oy', title:'a11oy — Command Platform (the brain)',
  plain:'The orchestrating governance substrate: one brain coordinating reasoning, policy and operator capabilities. Every result carries a signed provenance receipt. Live: /healthz · /lambda.',
  functions:['command center + five superpowers + 25-demo Warhacker board (5×5 live)','a11oy Code (governed agentic coder, P1–P6, open-weight router)','one governance substrate (capabilities are internal, no service split)','13-axis Trust Score aggregate (yuyay_v3, geometric mean, floor 0.90)','signed Khipu receipts for every governed action'],
  proof:['Locked proven kernel = 8 {F1,F4,F7,F11,F12,F18,F19,F22} @ c7c0ba17 (749 decl / 14 unique axioms / 163 sorries) — machine-enforced count, never moves','Λ-Aggregator uniqueness (F23) = Conjecture 1 — NOT a theorem; proven CONDITIONAL on separability (CUT-2, axiom-free)','Trust = conformal (never 100%, NOT Hoeffding) · SLSA L1 honest / L2 roadmap'],
  url:'https://szlholdings-a11oy.hf.space'
};
const KILLINCHU = {
  id:'killinchu', title:'killinchu — Field Node (drones & vessels)',
  plain:'Counter-UAS drone & vessel intelligence at the tactical edge — the deployed field node of the substrate. Effectors are SIMULATED. Live: /healthz.',
  functions:['maritime + drone C2 — vessels consolidated into killinchu (/elite fleet group)','OpenDroneID / ASTM F3411 · ADS-B Mode-S 1090ES · MAVLink v1/v2 decoders','counter-UAS A-gate + 13-axis edge Λ verdict (effectors SIMULATED)','signed Khipu receipts (ECDSA-P256 DSSE when signing key present; else UNSIGNED, labelled)'],
  proof:['Edge verdict bound by proven formulas: C20/W7-5 router, W5-3/W7-4 conformal (never 100%)','Same doctrine lock 749/14/163 @ c7c0ba17 · Λ = Conjecture 1 · Khipu BFT = Conjecture 2'],
  url:'https://szlholdings-killinchu.hf.space'
};

/* ---------- live endpoints (real /healthz + live data; CORS open) ----------- */
const ENDPOINTS = {
  a11oy:{ health:'https://szlholdings-a11oy.hf.space/healthz', lambda:'https://szlholdings-a11oy.hf.space/api/a11oy/v1/lambda' },
  killinchu:{ health:'https://szlholdings-killinchu.hf.space/healthz', ledger:'https://szlholdings-killinchu.hf.space/api/killinchu/v1/khipu/ledger' }
};

/* ---------- renderer / scene / camera --------------------------------------- */
const canvas = document.getElementById('scene');
const SMALL  = window.matchMedia('(max-width: 680px)').matches;   // phones: lighter GPU budget
const PR_CAP = SMALL ? 1.5 : 2;                                   // cap pixel ratio (bloom is fill-rate heavy)
const renderer = new THREE.WebGLRenderer({ canvas, antialias:!SMALL, alpha:false, powerPreference:'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, PR_CAP));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x040711, 0.00135);

const camera = new THREE.PerspectiveCamera(56, window.innerWidth/window.innerHeight, 0.1, 8000);
camera.position.set(0, 110, 470);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.06;
controls.minDistance = 90; controls.maxDistance = 1800; controls.enablePan = false;
controls.autoRotate = !REDUCED; controls.autoRotateSpeed = 0.34; controls.target.set(0,0,0);

/* ---------- lighting --------------------------------------------------------- */
scene.add(new THREE.AmbientLight(0x2a3050, 0.9));
const keyLight = new THREE.PointLight(0xffe6a8, 2.4, 2600, 1.4); scene.add(keyLight);
const rim = new THREE.DirectionalLight(0x5fd7ff, 0.5); rim.position.set(-240,150,-180); scene.add(rim);

/* ---------- deep star backdrop ---------------------------------------------- */
const disposables = [];
(function backdrop(){
  const N=SMALL?1400:2800, pos=new Float32Array(N*3);
  for(let i=0;i<N;i++){ const r=1700+Math.random()*2200, t=Math.random()*Math.PI*2, p=Math.acos(2*Math.random()-1);
    pos[i*3]=r*Math.sin(p)*Math.cos(t); pos[i*3+1]=r*Math.cos(p); pos[i*3+2]=r*Math.sin(p)*Math.sin(t); }
  const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.BufferAttribute(pos,3)); disposables.push(g);
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color:0x8a97d0, size:1.6, sizeAttenuation:true, transparent:true, opacity:0.5 })));
})();

/* ---------- polar hologram floor grid (depth) ------------------------------- */
(function grid(){
  const gh = new THREE.PolarGridHelper(760, 16, 10, 96, 0x2f6f8f, 0x18314a);
  gh.position.y = -150; gh.material.transparent = true; gh.material.opacity = 0.16; gh.material.depthWrite = false;
  scene.add(gh);
})();

/* ---------- soft radial glow sprite texture (sovereign, procedural) --------- */
function glowTexture(inner, outer){
  const s=128, c=document.createElement('canvas'); c.width=c.height=s; const ctx=c.getContext('2d');
  const g=ctx.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);
  g.addColorStop(0.0,inner); g.addColorStop(0.35,outer); g.addColorStop(1.0,'rgba(0,0,0,0)');
  ctx.fillStyle=g; ctx.fillRect(0,0,s,s); const tex=new THREE.CanvasTexture(c); tex.anisotropy=2; return tex;
}
const GLOW_TEX = glowTexture('rgba(255,231,168,0.95)','rgba(216,154,46,0.32)');
const HOLO_TEX = glowTexture('rgba(180,244,255,0.95)','rgba(58,180,244,0.30)');

/* ---------- holographic shader material factory ----------------------------
 * fresnel edge + iridescent hue shift + scanlines + subtle projection flicker.
 * Emissive-bright output so the vendored UnrealBloomPass blooms it naturally. */
function holoMaterial(colorA, colorB, opacity){
  return new THREE.ShaderMaterial({
    transparent:true, depthWrite:true, side:THREE.FrontSide,
    uniforms:{
      uTime:{value:0}, uColorA:{value:new THREE.Color(colorA)},
      uColorB:{value:new THREE.Color(colorB!=null?colorB:colorA)}, uOpacity:{value:opacity!=null?opacity:0.62}
    },
    vertexShader:`
      varying vec3 vN; varying vec3 vView; varying vec3 vWorld;
      uniform float uTime;
      void main(){
        vec3 p = position;
        float band = sin(p.y*7.0 + uTime*2.4);
        p += normal * (0.05 * band);                 // subtle holographic jitter
        vec4 world = modelMatrix * vec4(p,1.0); vWorld = world.xyz;
        vN = normalize(normalMatrix * normal);
        vec4 mv = modelViewMatrix * vec4(p,1.0); vView = normalize(-mv.xyz);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader:`
      uniform float uTime; uniform vec3 uColorA; uniform vec3 uColorB; uniform float uOpacity;
      varying vec3 vN; varying vec3 vView; varying vec3 vWorld;
      void main(){
        float fres = pow(1.0 - max(dot(vN,vView),0.0), 2.0);
        float irid = 0.5 + 0.5*sin(fres*6.2831 + uTime*0.6);
        vec3 base = mix(uColorA, uColorB, irid);
        float scan  = 0.78 + 0.22*sin(vWorld.y*2.6 - uTime*5.5);   // projection scanlines
        float flick = 0.94 + 0.06*sin(uTime*36.0 + vWorld.x*8.0);  // faint flicker
        vec3 col = base * (0.42 + 1.8*fres) * scan * flick;
        float alpha = clamp(uOpacity + fres*0.85, 0.0, 1.0);
        gl_FragColor = vec4(col, alpha);
      }`
  });
}
const holoMats = []; // collected so animate() can tick uTime

/* ---------- interactable registry ------------------------------------------- */
const interactables = [];
function registerBody(mesh, data, focusGetter){ mesh.userData.inspect=data; mesh.userData.focus=focusGetter; interactables.push(mesh); }

/* ---------- a11oy — the brain / sun ----------------------------------------- */
const sunGroup = new THREE.Group(); scene.add(sunGroup);
const sunCoreGeo = new THREE.IcosahedronGeometry(36, 5);
const sunMat = new THREE.ShaderMaterial({
  uniforms:{ uTime:{value:0}, uColorHot:{value:new THREE.Color(0xfff0c2)}, uColorCore:{value:new THREE.Color(0xd79a2e)}, uPulse:{value:0.0} },
  vertexShader:`varying vec3 vN; varying vec3 vView;
    void main(){ vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.0); vView=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
  fragmentShader:`uniform float uTime; uniform vec3 uColorHot; uniform vec3 uColorCore; uniform float uPulse; varying vec3 vN; varying vec3 vView;
    void main(){ float fres=pow(1.0-max(dot(vN,vView),0.0),2.2); float shimmer=0.5+0.5*sin(uTime*1.4+vN.y*6.0);
      vec3 col=mix(uColorCore,uColorHot,fres*0.85+0.15*shimmer); float glow=(0.6+0.4*uPulse);
      gl_FragColor=vec4(col*(1.25+fres*1.7)*glow,1.0); }`
});
const sunCore = new THREE.Mesh(sunCoreGeo, sunMat); sunGroup.add(sunCore); disposables.push(sunCoreGeo);
registerBody(sunCore, A11OY, ()=>({ target:sunGroup.position.clone(), dist:180 }));
// translucent glow shell + brain wireframe lattice
const sunGlowGeo = new THREE.SphereGeometry(52,32,32);
const sunGlow = new THREE.Mesh(sunGlowGeo, new THREE.MeshBasicMaterial({ color:0xffd98a, transparent:true, opacity:0.10, side:THREE.BackSide }));
sunGroup.add(sunGlow); disposables.push(sunGlowGeo);
const brainGeo = new THREE.IcosahedronGeometry(45,2);
const brainLattice = new THREE.Mesh(brainGeo, new THREE.MeshBasicMaterial({ color:0xffe6a8, wireframe:true, transparent:true, opacity:0.22 }));
sunGroup.add(brainLattice); disposables.push(brainGeo);
sunGroup.add(makeLabel('a11oy', 0xffe6a8, 66));

/* ---------- 3 internal capabilities orbiting the sun ------------------------ */
const ORBIT_R = 168; const capBodies = [];
CAPABILITIES.forEach((cap)=>{
  const grp = new THREE.Group();
  const geo = new THREE.IcosahedronGeometry(15,2);
  const mat = holoMaterial(cap.color, 0xffffff, 0.5); holoMats.push(mat);
  const mesh = new THREE.Mesh(geo, mat); grp.add(mesh); disposables.push(geo);
  const ringGeo = new THREE.TorusGeometry(22,0.7,8,64);
  const ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color:cap.color, transparent:true, opacity:0.4 }));
  ring.rotation.x = Math.PI/2; grp.add(ring); disposables.push(ringGeo);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map:GLOW_TEX, color:cap.color, transparent:true, opacity:0.3, blending:THREE.AdditiveBlending, depthWrite:false }));
  halo.scale.set(72,72,1); grp.add(halo);
  grp.add(makeLabel(cap.title.split(/[ &·]/)[0], cap.color, 30));
  scene.add(grp);
  const entry = { grp, mesh, cap, baseAngle:cap.angle };
  registerBody(mesh, cap, ()=>({ target:grp.position.clone(), dist:95 }));
  capBodies.push(entry);
  const tether = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3()]),
    new THREE.LineBasicMaterial({ color:cap.color, transparent:true, opacity:0.3 }));
  scene.add(tether); entry.tether = tether;
});

/* ---------- ORG CONSTELLATION — the live HF Spaces (folds in org-map) -------
 * Nodes placed on a fibonacci shell around the substrate. Holographic material,
 * cord to the brain-sun, clickable → honest metadata + open the real Space.
 * a11oy (sun) and killinchu (field node) are represented bespoke, so excluded. */
const orgGroup = new THREE.Group(); scene.add(orgGroup);
const ORG_R = 360; let orgNodes = [];
function fibPoint(i, n, radius){
  const off = 2/n, y = i*off - 1 + off/2;
  const r = Math.sqrt(Math.max(0,1 - y*y)), phi = i * Math.PI * (3 - Math.sqrt(5));
  return new THREE.Vector3(Math.cos(phi)*r*radius, y*radius*0.72, Math.sin(phi)*r*radius);
}
function buildOrgConstellation(data){
  for(const o of orgNodes){ const at=interactables.indexOf(o.mesh); if(at>=0) interactables.splice(at,1); }
  orgGroup.traverse(o=>{ if(o.geometry) o.geometry.dispose(); if(o.material){
    const at=holoMats.indexOf(o.material); if(at>=0) holoMats.splice(at,1);
    if(o.userData.isLabel && o.material.map) o.material.map.dispose(); o.material.dispose(); } });
  orgGroup.clear(); orgNodes=[];
  const list = data.nodes||[];
  list.forEach((n,i)=>{
    const pos = fibPoint(i, list.length, ORG_R);
    const grp = new THREE.Group(); grp.position.copy(pos);
    const online = n.observation_state==='FRESH' && n.runtime_stage==='RUNNING';
    const isSelf = !!n.self;                          // "you are here" — the Cosmos node itself
    const base = n.observation_state!=='FRESH' ? 0x6b6f86 : online ? 0x4fd1ac : /ERROR/.test(n.runtime_stage) ? 0xee716a : /BUILDING|SLEEPING|PAUSED/.test(n.runtime_stage) ? 0xe6c875 : n.kind==='model' ? 0xbb9af7 : n.kind==='dataset' ? 0x7ad7ff : 0x6b6f86;
    const geo = new THREE.IcosahedronGeometry(isSelf?13:9,1);
    const mat = holoMaterial(base, 0xffffff, online?0.6:0.32); holoMats.push(mat);
    const mesh = new THREE.Mesh(geo, mat); grp.add(mesh);
    if(isSelf){ const rg=new THREE.TorusGeometry(21,0.8,8,56);
      const ring=new THREE.Mesh(rg, new THREE.MeshBasicMaterial({ color:0xffe6a8, transparent:true, opacity:0.55 }));
      ring.rotation.x=Math.PI/2.2; grp.add(ring); }
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map:HOLO_TEX, color:base, transparent:true, opacity:isSelf?0.5:(online?0.34:0.14), blending:THREE.AdditiveBlending, depthWrite:false }));
    halo.scale.set(isSelf?66:46,isSelf?66:46,1); grp.add(halo);
    grp.add(makeLabel(n.owner+'/'+n.slug, base, 22));
    orgGroup.add(grp);
    // cord from sun → node (governed-by), holo-blue, faint
    const mid = pos.clone().multiplyScalar(0.5); mid.y += 40;
    const curve = new THREE.QuadraticBezierCurve3(new THREE.Vector3(0,0,0), mid, pos).getPoints(14);
    const cg = new THREE.BufferGeometry().setFromPoints(curve);
    const cord = new THREE.Line(cg, new THREE.LineBasicMaterial({ color:online?0x3ab4f4:0x445069, transparent:true, opacity:online?0.26:0.12 }));
    orgGroup.add(cord);
    registerBody(mesh, {
      id:n.id, title:n.repo_id+(n.self?' · You are here':''),
      plain:'Public Hugging Face '+n.kind+' · '+n.observation_state+' observation. '+(n.kind==='space'?'Provider stage: '+n.runtime_stage+'.':'Catalog metadata; no runtime claim.'),
      functions:['owner: '+n.owner, 'sdk: '+(n.sdk||'not applicable'), 'revision: '+(n.revision||'unknown'), 'runtime revision: '+(n.runtime_revision||'not reported'), 'observed: '+(n.observed_at||'never'), 'likes: '+n.likes],
      proof:['Anonymous public metadata only. Provider RUNNING does not verify app health, inference, training or proof validity.', 'Lines show catalog membership, not verified governance or dependency relationships.'],
      url:n.url
    }, ()=>({ target:grp.getWorldPosition(new THREE.Vector3()), dist:72 }));
    orgNodes.push({ grp, mesh, base, online, i });
  });
}

/* ---------- killinchu — the field node -------------------------------------- */
const fieldGroup = new THREE.Group(); fieldGroup.position.set(420,-60,-150);
const fieldGeo = new THREE.OctahedronGeometry(20,0);
const fieldMat = holoMaterial(0x5c8fd1, 0x9fe0ff, 0.55); holoMats.push(fieldMat);
const fieldNode = new THREE.Mesh(fieldGeo, fieldMat); fieldGroup.add(fieldNode); disposables.push(fieldGeo);
const fieldRingGeo = new THREE.TorusGeometry(30,0.8,8,80);
const fieldRing = new THREE.Mesh(fieldRingGeo, new THREE.MeshBasicMaterial({ color:0x5c8fd1, transparent:true, opacity:0.42 }));
fieldRing.rotation.x = Math.PI/2.4; fieldGroup.add(fieldRing); disposables.push(fieldRingGeo);
const fieldHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map:HOLO_TEX, color:0x8fd0ff, transparent:true, opacity:0.3, blending:THREE.AdditiveBlending, depthWrite:false }));
fieldHalo.scale.set(98,98,1); fieldGroup.add(fieldHalo);
fieldGroup.add(makeLabel('killinchu', 0x8fb6e6, 40)); scene.add(fieldGroup);
registerBody(fieldNode, KILLINCHU, ()=>({ target:fieldGroup.position.clone(), dist:120 }));
const fieldWire = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), fieldGroup.position.clone()]),
  new THREE.LineBasicMaterial({ color:0x5b8dee, transparent:true, opacity:0.4 })); scene.add(fieldWire);

/* ---------- Khipu constellation: receipt stars + cord arcs (DAG) ------------ */
const khipuGroup = new THREE.Group(); scene.add(khipuGroup);
let receiptPoints=null, cordLines=null, receiptData=[]; let cordPulse=0;
const VERDICT_COLOR = { allow:0x4fd18b, advisory:0xd7b96b, deny:0xc0392b };
function verdictOf(l){ return Number.isFinite(l)?(l>=0.9?'allow':(l>=0.5?'advisory':'deny')):'unknown'; }
function seededVec(seed, radius){
  let h=2166136261>>>0; for(let i=0;i<seed.length;i++){ h^=seed.charCodeAt(i); h=Math.imul(h,16777619)>>>0; }
  const a=(h%10000)/10000*Math.PI*2, b=Math.acos(2*(((h>>>13)%10000)/10000)-1), r=radius*(0.55+0.45*(((h>>>7)%10000)/10000));
  return new THREE.Vector3(r*Math.sin(b)*Math.cos(a), r*Math.cos(b), r*Math.sin(b)*Math.sin(a));
}
function seedConstellation(){
  const arr=[]; for(let i=0;i<64;i++){ const id='seed-'+i.toString(16).padStart(4,'0');
    const roll=((i*2654435761)>>>0)%100; const l=roll<80?0.90+(roll%10)/100:(roll<95?0.62+(roll%30)/100:0.30+(roll%20)/100);
    arr.push({ id, prev:i>0&&(i%5!==0)?'seed-'+(i-1).toString(16).padStart(4,'0'):null, lambda:Math.min(0.999,l), source:'SEED' }); }
  return arr;
}
function renderConstellation(nodes, isNew){
  receiptData = nodes;
  if(receiptPoints){ khipuGroup.remove(receiptPoints); receiptPoints.geometry.dispose(); receiptPoints.material.dispose(); }
  if(cordLines){ khipuGroup.remove(cordLines); cordLines.geometry.dispose(); cordLines.material.dispose(); }
  const pos=new Float32Array(nodes.length*3), col=new Float32Array(nodes.length*3), byId={};
  nodes.forEach((n,i)=>{ const v=seededVec(n.id,270); n._v=v; byId[n.id]=v; pos[i*3]=v.x; pos[i*3+1]=v.y; pos[i*3+2]=v.z;
    const c=new THREE.Color(VERDICT_COLOR[verdictOf(n.lambda)]||0x888888); col[i*3]=c.r; col[i*3+1]=c.g; col[i*3+2]=c.b; });
  const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.BufferAttribute(pos,3)); g.setAttribute('color',new THREE.BufferAttribute(col,3));
  receiptPoints=new THREE.Points(g, new THREE.PointsMaterial({ size:5.2, vertexColors:true, transparent:true, opacity:0.95, sizeAttenuation:true, map:GLOW_TEX, blending:THREE.AdditiveBlending, depthWrite:false }));
  khipuGroup.add(receiptPoints);
  const linePos=[], lineCol=[];
  nodes.forEach((n)=>{ if(n.prev&&byId[n.prev]){ const a=byId[n.prev], b=n._v;
    const mid=a.clone().add(b).multiplyScalar(0.5).multiplyScalar(1.18);
    const curve=new THREE.QuadraticBezierCurve3(a,mid,b).getPoints(10);
    const cc=new THREE.Color(VERDICT_COLOR[verdictOf(n.lambda)]||0xc08f2f);
    for(let k=0;k<curve.length-1;k++){ linePos.push(curve[k].x,curve[k].y,curve[k].z, curve[k+1].x,curve[k+1].y,curve[k+1].z); lineCol.push(cc.r,cc.g,cc.b,cc.r,cc.g,cc.b); } }});
  const lg=new THREE.BufferGeometry(); lg.setAttribute('position',new THREE.Float32BufferAttribute(linePos,3)); lg.setAttribute('color',new THREE.Float32BufferAttribute(lineCol,3));
  cordLines=new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ vertexColors:true, transparent:true, opacity:0.34 }));
  khipuGroup.add(cordLines);
  if(isNew && !REDUCED) cordPulse=1.0;
}

/* ---------- floating text label sprites ------------------------------------- */
function makeLabel(text, color, size){
  const c=document.createElement('canvas'); c.width=256; c.height=64; const ctx=c.getContext('2d');
  ctx.font='700 34px ui-monospace, Menlo, Consolas, monospace'; ctx.fillStyle='#'+new THREE.Color(color).getHexString();
  ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.shadowColor='rgba(0,0,0,0.85)'; ctx.shadowBlur=8; ctx.fillText(text,128,34);
  const tex=new THREE.CanvasTexture(c); tex.anisotropy=4;
  const spr=new THREE.Sprite(new THREE.SpriteMaterial({ map:tex, transparent:true, depthWrite:false }));
  spr.scale.set(size*2, size*0.5, 1); spr.position.y=size*0.9; spr.userData.isLabel=true; return spr;
}

/* ---------- camera fly-to choreography -------------------------------------- */
let flying=null;
function flyTo(target, dist){ controls.autoRotate=false; const dir=camera.position.clone().sub(controls.target).normalize();
  const toPos=target.clone().add(dir.multiplyScalar(dist));
  flying={ fromPos:camera.position.clone(), toPos, fromTgt:controls.target.clone(), toTgt:target.clone(), t:0, dur:REDUCED?0.001:1.05 }; }
function easeInOut(x){ return x<0.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2; }

/* ---------- raycasting (click to inspect + fly) ----------------------------- */
const ray=new THREE.Raycaster(); ray.params.Points.threshold=6; const ptr=new THREE.Vector2(); let downXY=null;
function ptrFromEvent(e){ const r=canvas.getBoundingClientRect(); const cx=e.clientX??(e.touches&&e.touches[0].clientX); const cy=e.clientY??(e.touches&&e.touches[0].clientY);
  ptr.x=((cx-r.left)/r.width)*2-1; ptr.y=-((cy-r.top)/r.height)*2+1; }
canvas.addEventListener('pointerdown',(e)=>{ downXY={x:e.clientX,y:e.clientY}; });
canvas.addEventListener('pointerup',(e)=>{ if(!downXY) return; const moved=Math.hypot(e.clientX-downXY.x, e.clientY-downXY.y); downXY=null;
  if(moved>6) return; ptrFromEvent(e); ray.setFromCamera(ptr,camera); const hits=ray.intersectObjects(interactables,false);
  if(hits.length){ const o=hits[0].object; openInspector(o.userData.inspect); if(o.userData.focus){ const f=o.userData.focus(); flyTo(f.target,f.dist); } } });

/* ---------- inspector panel ------------------------------------------------- */
const insp=document.getElementById('inspector');
document.getElementById('insp-close').addEventListener('click',()=>{ insp.classList.remove('show'); controls.autoRotate=!REDUCED; });
function openInspector(d){ if(!d) return;
  const catalogDetails=document.querySelector('#catalog-panel > details'); if(catalogDetails) catalogDetails.open=false;
  document.getElementById('insp-title').textContent=d.title; document.getElementById('insp-plain').textContent=d.plain;
  let html='<div class="ih">Functions</div><ul>'+d.functions.map(f=>`<li>${esc(f)}</li>`).join('')+'</ul>';
  if(d.proof){ html+='<div class="ih">Honest note</div><ul>'+d.proof.map(p=>`<li class="proof">${esc(p)}</li>`).join('')+'</ul>'; }
  if(d.url){ html+=`<div class="ih">Source / destination</div><ul><li><a href="${esc(d.url)}" target="_blank" rel="noopener" style="color:#3af4c8">${esc(d.url)} ↗</a></li></ul>`; }
  document.getElementById('insp-body').innerHTML=html; insp.classList.add('show'); }
function esc(s){ return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

/* ---------- live polling + honest SEED→LIVE promotion ----------------------- */
let liveState={ a11oy:'…', killinchu:'…' }; let feedSource='SEED', lastLambda=null, sunPulseTarget=0.5;
const ticker=[];
async function getJSON(url, ms){ const ctrl=new AbortController(); const t=setTimeout(()=>ctrl.abort(), ms||7000);
  try{ const r=await fetch(url,{ signal:ctrl.signal, headers:{accept:'application/json'} }); if(!r.ok) throw new Error('HTTP '+r.status); return await r.json(); } finally { clearTimeout(t); } }
function pushTicker(line){ ticker.unshift(line); if(ticker.length>4) ticker.pop(); paintTicker(); }
let prevReceiptIds='';
async function poll(){
  let healthy=0;
  await Promise.all(['a11oy','killinchu'].map(async k=>{
    try{ const h=await getJSON(ENDPOINTS[k].health,7000); const ok=h&&h.status==='ok'; liveState[k]=ok?'LIVE':'DEGRADED'; if(ok) healthy++; }
    catch(_){ liveState[k]='UNAVAILABLE'; } }));
  sunPulseTarget=0.30+0.35*healthy;
  let nodes=null, src='SEED · deterministic (no live receipts yet)';
  try{ const led=await getJSON(ENDPOINTS.killinchu.ledger,7000);
    if(led&&Array.isArray(led.nodes)&&led.nodes.length){
      nodes=led.nodes.map((n,i)=>({ id:(n.digest||('k'+i)).slice(0,16), prev:(n.parents&&n.parents[0])?String(n.parents[0]).slice(0,16):null, lambda:Number.isFinite(n.lambda)?n.lambda:null, source:'LIVE' }));
      src='LIVE · killinchu khipu ledger ('+nodes.length+' receipts · '+(led.slsa||'SLSA L1')+')';
    } else if(led&&Array.isArray(led.nodes)){ src='LIVE ledger reachable · 0 receipts (in-memory, non-persistent) · showing SEED'; }
  }catch(_){}
  if(!nodes){ try{ const lam=await getJSON(ENDPOINTS.a11oy.lambda,7000);
    if(lam&&typeof lam.lambda==='number'){ lastLambda=lam.lambda; nodes=seedConstellation().map(n=>({ ...n, lambda:lam.lambda, source:'SEED+liveΛ' }));
      src='SEED positions · LIVE a11oy Λ='+lam.lambda.toFixed(3)+' (13-axis Trust Score, floor '+(lam.lambda_floor??0.9)+')'; }
  }catch(_){} }
  if(!nodes) nodes=seedConstellation();
  feedSource=src;
  const ids=nodes.map(n=>n.id).join('|'); const isNew=ids!==prevReceiptIds&&prevReceiptIds!=='';
  renderConstellation(nodes,isNew);
  if(isNew){ const top=nodes[0]; pushTicker((top.source.startsWith('LIVE')?'◆ LIVE':'◇ seed')+' '+(top.id||'').slice(0,10)+' · Λ '+(Number.isFinite(top.lambda)?top.lambda.toFixed(2):'unknown')+' · '+verdictOf(top.lambda).toUpperCase()); }
  prevReceiptIds=ids; paintHUD();
}
function paintHUD(){
  const rows=[{ label:'a11oy · brain', s:liveState.a11oy },{ label:'killinchu · field', s:liveState.killinchu }];
  let html=rows.map(r=>{ const cls=r.s==='LIVE'?'live':(r.s==='UNAVAILABLE'?'off':'seed');
    return `<div class="row"><span class="dot ${cls}"></span><span>${r.label}</span><span class="meta">${r.s}</span></div>`; }).join('');
  const up = orgNodes.filter(o=>o.online).length;
  if(orgNodes.length){ html+=`<div class="row"><span class="dot cat"></span><span>public catalog</span><span class="meta">${orgNodes.length} visible · ${up} provider RUNNING</span></div>`; }
  document.getElementById('status-rows').innerHTML=html; document.getElementById('feed-src').textContent=feedSource;
}
function paintTicker(){ const el=document.getElementById('ticker-lines'); if(!el) return;
  el.innerHTML=ticker.length?ticker.map(t=>`<div class="tk">${esc(t)}</div>`).join(''):'<div class="tk dim">awaiting receipt stream…</div>'; }

/* ---------- postprocessing: REAL bloom (vendored, no CDN) -------------------- */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), SMALL?0.72:0.85, 0.62, 0.12);
composer.addPass(bloom);
composer.addPass(new OutputPass());

/* ---------- animation loop (delta-clamped, perf-safe) ----------------------- */
const clock=new THREE.Clock(); let acc=0; let sceneBroken=false;
function animate(){
  if(sceneBroken) return; requestAnimationFrame(animate);
  try{
    let dt=clock.getDelta(); if(dt>0.05) dt=0.05; acc+=dt; const t=acc;
    sunMat.uniforms.uTime.value=t;
    for(let i=0;i<holoMats.length;i++) holoMats[i].uniforms.uTime.value=t;
    const pulse=REDUCED?sunPulseTarget:(0.5*sunPulseTarget+0.5*(sunPulseTarget*(0.85+0.15*Math.sin(t*1.6))));
    sunMat.uniforms.uPulse.value+=(pulse-sunMat.uniforms.uPulse.value)*0.05;
    const bp=sunMat.uniforms.uPulse.value; keyLight.intensity=1.7+1.4*bp;
    if(!REDUCED){
      sunCore.rotation.y+=0.0015*dt*60; brainLattice.rotation.y-=0.0011*dt*60; brainLattice.rotation.x+=0.0006*dt*60;
      sunGlow.material.opacity=0.08+0.04*Math.sin(t*2);
      capBodies.forEach((cb,i)=>{ const a=cb.baseAngle+t*0.5; const x=Math.cos(a)*ORBIT_R, z=Math.sin(a)*ORBIT_R, y=Math.sin(a*1.3+i)*24;
        cb.grp.position.set(x,y,z); cb.mesh.rotation.y+=0.01;
        cb.tether.geometry.setFromPoints([new THREE.Vector3(0,0,0),new THREE.Vector3(x,y,z)]); cb.tether.geometry.attributes.position.needsUpdate=true; });
      fieldNode.rotation.y+=0.008; fieldRing.rotation.z+=0.004;
      khipuGroup.rotation.y+=0.0006*dt*60; orgGroup.rotation.y+=0.00035*dt*60;
      orgNodes.forEach(o=>{ o.mesh.rotation.x+=0.006; o.mesh.rotation.y+=0.009; });
    } else {
      capBodies.forEach((cb,i)=>{ const a=cb.baseAngle; const x=Math.cos(a)*ORBIT_R, z=Math.sin(a)*ORBIT_R, y=Math.sin(a*1.3+i)*24;
        cb.grp.position.set(x,y,z); cb.tether.geometry.setFromPoints([new THREE.Vector3(0,0,0),new THREE.Vector3(x,y,z)]); cb.tether.geometry.attributes.position.needsUpdate=true; });
    }
    if(cordPulse>0){ cordPulse=Math.max(0,cordPulse-dt*0.8);
      if(cordLines) cordLines.material.opacity=0.34+0.5*cordPulse; if(receiptPoints) receiptPoints.material.opacity=0.95+0.05*cordPulse; }
    if(flying){ flying.t+=dt/flying.dur; const k=easeInOut(Math.min(1,flying.t));
      camera.position.lerpVectors(flying.fromPos,flying.toPos,k); controls.target.lerpVectors(flying.fromTgt,flying.toTgt,k); if(flying.t>=1){ if(flying.onDone){ flying.onDone(); } flying=null; } }
    controls.update(); composer.render();
  } catch(err){
    sceneBroken=true; console.error('[cosmos] render loop error:', err);
    const b=document.getElementById('boot'); if(b){ b.classList.remove('hide'); b.innerHTML='<div class="b1">SZL COSMOS</div><div class="b2">3D scene unavailable in this browser (WebGL). The honest live data is still reachable via the a11oy / Spaces links.</div>'; }
  }
}

/* ---------- boot ------------------------------------------------------------ */
window.addEventListener('resize',()=>{ camera.aspect=window.innerWidth/window.innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth,window.innerHeight); renderer.setPixelRatio(Math.min(window.devicePixelRatio,PR_CAP));
  composer.setSize(window.innerWidth,window.innerHeight); bloom.setSize(window.innerWidth,window.innerHeight); });

// Subscribe to the independently accessible public catalog, then paint SEED + boot
window.addEventListener('cosmos-catalog', e=>{ buildOrgConstellation(e.detail); paintHUD(); });
window.dispatchEvent(new Event('cosmos-catalog-request'));
renderConstellation(seedConstellation(), false);
paintHUD(); paintTicker();
function hideBoot(){ if(sceneBroken) return; const b=document.getElementById('boot'); if(b) b.classList.add('hide'); }
// cinematic intro: sweep from a high, far establishing pose into the resting frame, then hand back to auto-orbit
if(!REDUCED){
  camera.position.set(-120, 700, 1640);
  controls.autoRotate=false;
  flying={ fromPos:camera.position.clone(), toPos:new THREE.Vector3(0,110,470),
    fromTgt:controls.target.clone(), toTgt:new THREE.Vector3(0,0,0), t:0, dur:2.8,
    onDone:()=>{ controls.autoRotate=!REDUCED; } };
}
animate(); hideBoot(); requestAnimationFrame(hideBoot); setTimeout(hideBoot,1500);
async function pollNext(){ try{ await poll(); } finally { setTimeout(pollNext,30000); } }
pollNext();
controls.addEventListener('start',()=>{ controls.autoRotate=false; });
