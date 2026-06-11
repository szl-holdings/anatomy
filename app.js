/* =====================================================================
   SZL AGENT BODY v4 (DEEPEN) — LIVING ANATOMY · WebGL engine
   (EVOLVES v3 → v4 → v4-deepen — ADDITIVE ONLY, NOT a rewrite. The whole
    v3 engine below is preserved verbatim; v4 dissection features are
    layered ON TOP in a clearly-marked block; the v4-DEEPEN block (v5)
    is layered on top of that. v3/v4 lineage stays fully visible.)
   v4-DEEPEN ADDS (all additive, same scene + SAME render loop):
     A. Formula Atlas — EVERY formula in data.js, grouped by maturity
        tier, searchable, tier-filterable, live count badges.
     B. Per-organ formula→Lean drill-down (expandable axioms + lutar-lean
        link) and hover organ↔formula 3D highlight.
     C. More real 3D — leader-line organ labels, breathing Λ-heart idle
        synced to the receipt pulse, smoother per-organ framing, a
        pausable guided-tour mode. Respects prefers-reduced-motion.
     D. HONEST forecast overlay — a transparency timeline/sparkline of
        proof maturity driven ONLY by data.js / KERNEL strings; every
        not-yet-achieved item labeled ROADMAP / PROJECTED.
     E. Mobile/tablet parity via the existing bottom-sheet pattern.
   Honesty preserved: data.js is the single source of truth; nothing is
   fabricated; CONJECTURE/EXPERIMENTAL/AXIOM_GATED are never relabeled.
   Sovereign: vendored THREE r160 (global), ZERO runtime CDN, offline.
   Two organisms (a11oy / killinchu) rendered as human-like silhouettes
   sharing ONE circulatory (YAWAR receipt bus) + nervous (span lineage)
   mesh. Cinematic dark substrate, additive volumetric glow (in-core
   pseudo-bloom via radial sprites), smooth fly-in + auto-orbit, a live
   receipt-flow along YAWAR, elegant organ detail cards.
   v4 ADDS (all additive, all on this same scene + render loop):
     1. Dissection layer stack (toggles + opacity, localStorage-persisted)
     2. Clip-plane scalpel (renderer.localClippingEnabled, X/Y/Z + reset)
     3. Explode view (eased 0->1 radial separation of organs)
     4. Search / jump (filter organs+formulas, fly + open panel)
     5. Always-on visibility HUD (honest counts read from D.KERNEL)
     6. Focus mode (fade other organs when one is selected)
     7. Accessibility + mobile + prefers-reduced-motion
   Honesty preserved: data.js is the single source of truth.
   ===================================================================== */
(function () {
  'use strict';
  const D = window.SZL_ANATOMY;
  const TAU = Math.PI * 2;
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const easeOutCubic = t => 1 - Math.pow(1 - t, 3);
  const easeInOutCubic = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

  /* ---------------- tiny ASCII-math -> Unicode renderer ------------- */
  function mathToUnicode(s) {
    const map = {
      'Lambda':'\u039b','Sigma':'\u03a3','theta':'\u03b8','rho':'\u03c1','pi':'\u03c0','delta':'\u03b4',
      'lam_min':'\u03bb_min','<=':'\u2264','>=':'\u2265','!=':'\u2260','=>':'\u21d2','<=>':'\u21d4',
      '=/=>':'\u21cf','->':'\u2192','sqrt':'\u221a','forall':'\u2200','argmin':'argmin','Sigma_i':'\u03a3\u1d62'
    };
    let out = s;
    ['<=>','=/=>','=>','<=','>=','!=','->','Lambda','Sigma_i','Sigma','theta','rho','pi','delta','lam_min','sqrt','forall'].forEach(k=>{
      out = out.split(k).join(map[k]||k);
    });
    out = out.replace(/_\{([^}]+)\}/g, (m,g)=>toSub(g)).replace(/\^\{([^}]+)\}/g,(m,g)=>toSup(g));
    out = out.replace(/_([A-Za-z0-9]+)/g,(m,g)=>toSub(g)).replace(/\^([A-Za-z0-9+\-]+)/g,(m,g)=>toSup(g));
    return out;
  }
  const SUB={'0':'\u2080','1':'\u2081','2':'\u2082','3':'\u2083','4':'\u2084','5':'\u2085','6':'\u2086','7':'\u2087','8':'\u2088','9':'\u2089','i':'\u1d62','j':'\u2c7c','k':'\u2096','n':'\u2099','r':'\u1d63','t':'\u209c','min':'min','out':'out','in':'in'};
  const SUP={'0':'\u2070','1':'\u00b9','2':'\u00b2','3':'\u00b3','+':'\u207a','-':'\u207b'};
  function toSub(g){ if(SUB[g])return SUB[g]; return g.split('').map(c=>SUB[c]||c).join(''); }
  function toSup(g){ return g.split('').map(c=>SUP[c]||c).join(''); }

  /* ---------------- DOM refs ---------------- */
  const $ = id => document.getElementById(id);
  const panel=$('panel'), tip=$('tip');

  /* ---------------- renderer / scene / camera ---------------- */
  const canvas=$('scene');
  let renderer;
  try {
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'high-performance'});
  } catch(e){
    document.body.classList.add('nojs'); return;
  }
  const DPR = Math.min(devicePixelRatio||1, 2);
  renderer.setSize(innerWidth,innerHeight);
  renderer.setPixelRatio(DPR);
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.12;
  renderer.outputColorSpace=THREE.SRGBColorSpace;

  const scene=new THREE.Scene();
  scene.background=new THREE.Color('#04060c');
  scene.fog=new THREE.FogExp2('#04060c',0.020);

  const camera=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,0.1,260);
  const HOME={r:13.8,phi:1.33,theta:0.0,target:new THREE.Vector3(0,0.35,0)};
  const cam={r:HOME.r,phi:HOME.phi,theta:HOME.theta,target:HOME.target.clone()};
  // cinematic fly-in start
  const intro={t:0, dur:2.6, from:{r:26,phi:1.05,theta:-0.55}, active:true};

  /* ---------------- lights ---------------- */
  scene.add(new THREE.AmbientLight('#33446e',0.5));
  const key=new THREE.DirectionalLight('#cfe0ff',1.0); key.position.set(6,11,9); scene.add(key);
  const fill=new THREE.DirectionalLight('#2a3a66',0.4); fill.position.set(-7,-3,-6); scene.add(fill);
  const rimA=new THREE.PointLight('#3fe0c5',0.85,42); rimA.position.set(-9,3,4); scene.add(rimA);
  const rimK=new THREE.PointLight('#ffb13f',0.85,42); rimK.position.set(9,3,4); scene.add(rimK);
  const heartLight=new THREE.PointLight('#ff5d8f',1.5,26); heartLight.position.set(0,0.55,1.2); scene.add(heartLight);

  /* ---------------- additive glow sprite texture (pseudo-bloom) ----- */
  const GLOW_TEX = (function(){
    const s=128, c=document.createElement('canvas'); c.width=c.height=s;
    const g=c.getContext('2d');
    const grad=g.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);
    grad.addColorStop(0,'rgba(255,255,255,1)');
    grad.addColorStop(0.25,'rgba(255,255,255,0.55)');
    grad.addColorStop(0.55,'rgba(255,255,255,0.16)');
    grad.addColorStop(1,'rgba(255,255,255,0)');
    g.fillStyle=grad; g.fillRect(0,0,s,s);
    const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; return t;
  })();
  function glowSprite(hex,scale,opacity){
    const m=new THREE.SpriteMaterial({map:GLOW_TEX,color:hex,transparent:true,opacity:opacity==null?0.7:opacity,
      blending:THREE.AdditiveBlending,depthWrite:false,depthTest:true});
    const sp=new THREE.Sprite(m); sp.scale.setScalar(scale); return sp;
  }

  /* ---------------- starfield (depth-of-field-ish layered) ---------- */
  (function stars(){
    [{n:900,r0:46,r1:120,size:0.14,op:0.42,col:'#6f86c0'},
     {n:420,r0:30,r1:70,size:0.26,op:0.30,col:'#8ea6e0'}].forEach(L=>{
      const g=new THREE.BufferGeometry(),p=new Float32Array(L.n*3);
      for(let i=0;i<L.n;i++){const r=L.r0+Math.random()*(L.r1-L.r0),t=Math.random()*TAU,ph=Math.acos(2*Math.random()-1);
        p[i*3]=r*Math.sin(ph)*Math.cos(t);p[i*3+1]=r*Math.cos(ph)*0.6;p[i*3+2]=r*Math.sin(ph)*Math.sin(t);}
      g.setAttribute('position',new THREE.BufferAttribute(p,3));
      scene.add(new THREE.Points(g,new THREE.PointsMaterial({color:L.col,size:L.size,transparent:true,opacity:L.op,sizeAttenuation:true,blending:THREE.AdditiveBlending,depthWrite:false})));
    });
  })();
  // ground reflection-ish radial floor glow
  (function floor(){
    const geo=new THREE.CircleGeometry(22,64);
    const mat=new THREE.MeshBasicMaterial({color:'#0a1430',transparent:true,opacity:0.5,depthWrite:false});
    const m=new THREE.Mesh(geo,mat); m.rotation.x=-Math.PI/2; m.position.y=-4.6; scene.add(m);
  })();

  /* ---------------- helpers ---------------- */
  function glowMat(hex,op){return new THREE.MeshStandardMaterial({color:hex,emissive:hex,emissiveIntensity:0.6,
    roughness:0.32,metalness:0.12,transparent:true,opacity:op==null?0.92:op});}
  function lineMat(hex,op){return new THREE.LineBasicMaterial({color:hex,transparent:true,opacity:op==null?0.42:op,blending:THREE.AdditiveBlending,depthWrite:false});}

  const root=new THREE.Group(); scene.add(root);
  const BODY_X=3.7;
  const organMeshes=[];
  const vessels=[];
  const pulses=[];
  // v4 registries (populated by the existing builders; consumed by v4 block)
  const silhouetteMeshes=[];
  const silhouetteGroups=[];
  let heartGroup=null, heartCoreMat=null, heartHalo=null, heartGlow=null, heartRing=null;

  /* ---------------- BODY SILHOUETTE (skeleton + membrane) ----------- */
  function buildSilhouette(side,bodyColor){
    const g=new THREE.Group(); g.position.x=side*BODY_X;
    const skinMat=new THREE.MeshStandardMaterial({color:bodyColor,emissive:bodyColor,emissiveIntensity:0.10,
      roughness:0.62,metalness:0.05,transparent:true,opacity:0.055,side:THREE.DoubleSide,depthWrite:false});
    const torso=new THREE.Mesh(new THREE.CapsuleGeometry(1.05,2.0,8,20),skinMat); torso.position.y=-0.1; g.add(torso);
    const head=new THREE.Mesh(new THREE.SphereGeometry(0.72,22,20),skinMat.clone()); head.position.y=2.45; g.add(head);
    const pelvis=new THREE.Mesh(new THREE.SphereGeometry(0.95,18,16),skinMat.clone()); pelvis.position.y=-1.55; pelvis.scale.set(1,0.7,0.8); g.add(pelvis);
    // faint body aura
    const aura=glowSprite(bodyColor,7.2,0.10); aura.position.y=0.1; g.add(aura);

    // ----- SKELETON: axial spine (gold) -----
    const spineMatAxial=new THREE.MeshStandardMaterial({color:'#ffd166',emissive:'#ffd166',emissiveIntensity:0.55,roughness:0.4,metalness:0.35});
    const vertN=11;
    for(let i=0;i<vertN;i++){
      const y=2.0 - i*0.34;
      const v=new THREE.Mesh(new THREE.TorusGeometry(0.11,0.045,8,18),spineMatAxial);
      v.position.set(0,y,-0.16); v.rotation.x=Math.PI/2; g.add(v);
    }
    const skull=new THREE.Mesh(new THREE.TorusGeometry(0.55,0.05,8,30),spineMatAxial); skull.position.set(0,2.55,0); skull.rotation.x=Math.PI/2.2; g.add(skull);

    const boneMat=new THREE.MeshStandardMaterial({color:'#e8c068',emissive:'#a07c20',emissiveIntensity:0.32,roughness:0.5,metalness:0.28,transparent:true,opacity:0.86});
    function bone(x1,y1,z1,x2,y2,z2,rad){
      const a=new THREE.Vector3(x1,y1,z1),b=new THREE.Vector3(x2,y2,z2);
      const len=a.distanceTo(b);
      const m=new THREE.Mesh(new THREE.CylinderGeometry(rad,rad*0.85,len,8),boneMat);
      m.position.copy(a).add(b).multiplyScalar(0.5);
      m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),b.clone().sub(a).normalize());
      g.add(m);
      [a,b].forEach(p=>{const j=new THREE.Mesh(new THREE.SphereGeometry(rad*1.5,8,8),boneMat);j.position.copy(p);g.add(j);});
    }
    bone(-0.05,1.85,-0.1,-1.0,1.7,0.0,0.07); bone(-1.0,1.7,0,-1.35,0.55,0.1,0.06); bone(-1.35,0.55,0.1,-1.5,-0.55,0.15,0.05);
    bone(0.05,1.85,-0.1, 1.0,1.7,0.0,0.07); bone( 1.0,1.7,0, 1.35,0.55,0.1,0.06); bone( 1.35,0.55,0.1, 1.5,-0.55,0.15,0.05);
    for(let i=0;i<4;i++){const y=1.3-i*0.32;const r=new THREE.Mesh(new THREE.TorusGeometry(0.78-i*0.04,0.03,6,22,Math.PI*1.3),boneMat);
      r.position.set(0,y,0.05); r.rotation.set(Math.PI/2,0,Math.PI*0.85); g.add(r);}
    bone(-0.4,-1.7,0,-0.55,-3.0,0.1,0.08); bone(-0.55,-3.0,0.1,-0.6,-4.1,0.2,0.06);
    bone( 0.4,-1.7,0, 0.55,-3.0,0.1,0.08); bone( 0.55,-3.0,0.1, 0.6,-4.1,0.2,0.06);

    root.add(g);
    // v4: register silhouette membrane + skeleton meshes so the dissection
    // layer stack and clip-plane can address them (collected, not altered here).
    g.traverse(c=>{ if(c.isMesh) silhouetteMeshes.push(c); });
    silhouetteGroups.push(g);
    return g;
  }

  /* ---------------- ORGANS ---------------- */
  function buildOrgans(){
    D.BODIES.forEach(body=>{
      D.ORGANS.forEach(o=>{
        if(o.shared && body.side!==-1) return;
        const sysColor=o.color;
        const baseX=o.shared?0:body.side*BODY_X;
        const grp=new THREE.Group();
        grp.position.set(baseX + o.pos[0], o.pos[1], o.pos[2]);

        if(o.beat){ // HEART — layered Λ core
          heartGroup=grp;
          const core=new THREE.Mesh(new THREE.IcosahedronGeometry(o.scale,3),
            new THREE.MeshStandardMaterial({color:'#ff5d8f',emissive:'#ff2d6f',emissiveIntensity:1.25,roughness:0.22,metalness:0.25}));
          heartCoreMat=core.material; grp.add(core);
          [[-0.18,0.12],[0.18,0.05]].forEach(([dx,dy])=>{
            const lobe=new THREE.Mesh(new THREE.SphereGeometry(o.scale*0.62,18,16),
              new THREE.MeshStandardMaterial({color:'#ff7ea3',emissive:'#ff4d80',emissiveIntensity:0.9,roughness:0.28,transparent:true,opacity:0.92}));
            lobe.position.set(dx,dy,0); grp.add(lobe);
          });
          heartHalo=new THREE.Mesh(new THREE.SphereGeometry(o.scale*1.7,22,20),
            new THREE.MeshBasicMaterial({color:'#ff5d8f',transparent:true,opacity:0.12,side:THREE.BackSide,depthWrite:false}));
          grp.add(heartHalo);
          heartGlow=glowSprite('#ff5d8f',o.scale*8.5,0.55); grp.add(heartGlow);
          heartRing=new THREE.Mesh(new THREE.TorusGeometry(o.scale*1.3,0.022,8,48),
            new THREE.MeshBasicMaterial({color:'#ffd0e0',transparent:true,opacity:0.65,blending:THREE.AdditiveBlending,depthWrite:false})); grp.add(heartRing);
          const ring2=new THREE.Mesh(new THREE.TorusGeometry(o.scale*1.7,0.012,8,56),
            new THREE.MeshBasicMaterial({color:'#ff9ec0',transparent:true,opacity:0.4,blending:THREE.AdditiveBlending,depthWrite:false}));
          ring2.rotation.x=Math.PI/2.4; grp.add(ring2); grp.userData.ring2=ring2;
        } else {
          let geo;
          switch(o.system){
            case 'brain': geo=new THREE.IcosahedronGeometry(o.scale,1); break;
            case 'blood': geo=new THREE.SphereGeometry(o.scale,20,18); break;
            case 'nerve': geo=new THREE.OctahedronGeometry(o.scale,1); break;
            case 'skeleton': geo=new THREE.DodecahedronGeometry(o.scale,0); break;
            case 'audit': geo=new THREE.IcosahedronGeometry(o.scale,0); break;
            default: geo=new THREE.SphereGeometry(o.scale,18,16);
          }
          const mesh=new THREE.Mesh(geo,glowMat(sysColor,0.92)); grp.add(mesh);
          grp.userData.coreMat=mesh.material;
          // volumetric glow sprite (pseudo-bloom)
          const gl=glowSprite(sysColor,o.scale*4.6,0.32); grp.add(gl); grp.userData.glow=gl;
          // hover/select halo shell
          const halo=new THREE.Mesh(new THREE.SphereGeometry(o.scale*1.45,18,16),
            new THREE.MeshBasicMaterial({color:sysColor,transparent:true,opacity:0.0,side:THREE.BackSide,depthWrite:false}));
          grp.add(halo);
          grp.userData.halo=halo;
        }
        root.add(grp);
        organMeshes.push({grp,organ:o,bodyKey:o.shared?'shared':body.key,baseScale:grp.scale.x,glowBase:o.beat?0.55:0.32});
      });
    });
  }

  /* ---------------- VESSELS (circulatory + nervous) ---------------- */
  function worldPos(o,side){ const x=(o.shared?0:side*BODY_X)+o.pos[0]; return new THREE.Vector3(x,o.pos[1],o.pos[2]); }
  function organByKey(k){ return D.ORGANS.find(o=>o.key===k); }

  function addVessel(from,to,sideA,sideB,colorHex,formulaId,label,fn,arc){
    const a=worldPos(from,sideA), b=worldPos(to,sideB);
    const mid=a.clone().add(b).multiplyScalar(0.5);
    mid.z += (arc==null?0.6:arc);
    mid.y += 0.15;
    const curve=new THREE.QuadraticBezierCurve3(a,mid,b);
    const pts=curve.getPoints(48);
    const geo=new THREE.BufferGeometry().setFromPoints(pts);
    const isShared=label && label.indexOf('SHARED')>=0;
    const line=new THREE.Line(geo,lineMat(colorHex,isShared?0.55:0.38));
    root.add(line);
    const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,32,0.095,6,false),
      new THREE.MeshBasicMaterial({visible:false}));
    root.add(tube);
    const v={curve,line,tube,formulaId,from:from.quechua,to:to.quechua,label,fn,color:colorHex,shared:isShared};
    tube.userData.vessel=v;
    vessels.push(v);
    return v;
  }

  function buildVessels(){
    const aS=-1,kS=1;
    D.BODIES.forEach(body=>{
      const s=body.side;
      const heart=organByKey('yuyay');
      const yawar=organByKey('yawar'), amaru=organByKey('amaru'), sentra=organByKey('sentra'),
            ruway=organByKey('ruway'), vsp=organByKey('vsp'), huklla=organByKey('huklla'),
            hatun=organByKey('hatun'), ow=organByKey('overwatch'), tukuy=organByKey('tukuy'), musquy=organByKey('musquy');
      addVessel({...amaru,pos:amaru.pos,shared:false,quechua:'YACHAY'},{...heart,shared:true,quechua:'YUYAY'},s,0,'#5ad1ff','P4','efferent nerve','YACHAY proposes \u2192 YUYAY gate (span lineage)',0.5);
      addVessel({...heart,shared:true,quechua:'YUYAY'},{...yawar,pos:yawar.pos,shared:false,quechua:'YAWAR'},0,s,'#ff3b5c','M2','arterial receipt','\u039b-signed receipt \u2192 append-only bus',0.55);
      addVessel(ruway,sentra,s,s,'#ff9e6b','P5','egress vessel','RUWAY write \u2192 CHAPAQ egress inspection',0.3);
      addVessel(sentra,yawar,s,s,'#ff3b5c','M2','write-to-bus','CHAPAQ-cleared write \u2192 YAWAR (tamper-evident)',0.3);
      addVessel(yawar,amaru,s,s,'#9ef0c0','P1','afferent tether','YAWAR snapshot \u2192 YACHAY (READ-ONLY single tether)',0.45);
      addVessel(yawar,ow,s,s,'#9ef0c0','B1','proprioceptive nerve','YAWAR \u2192 R0513 read-only 5-invariant audit',0.2);
      addVessel(vsp,huklla,s,s,'#5ad1ff','S2','reflex arc','HUKLLA deadman \u2192 freeze span \u2192 halt HATUN',0.2);
      addVessel(huklla,hatun,s,s,'#5ad1ff','S2','halt signal','reflex \u2192 HATUN root span (cancel children)',0.35);
      addVessel(hatun,tukuy,s,s,'#ffd166','G1','motor nerve','HATUN seal \u2192 TUKUY egress actuator',0.5);
      addVessel(musquy,heart,s,0,'#7c5cff','Q1','sim vessel','MUSQUY K-candidate sim \u2192 YUYAY gate',0.4);
    });
    const yawarA=organByKey('yawar'), yawarK=organByKey('yawar');
    addVessel({...yawarA,quechua:'YAWAR (a11oy)'},{...yawarK,quechua:'YAWAR (killinchu)'},aS,kS,'#ff3b5c','M2','SHARED receipt bus','one circulatory mesh \u2014 signed receipts pulse a11oy \u21c4 killinchu',1.6);
    const amaruA=organByKey('amaru');
    addVessel({...amaruA,quechua:'YACHAY (a11oy)'},{...organByKey('yuyay'),shared:true,quechua:'YUYAY (\u039b heart)'},aS,0,'#5ad1ff','P3','shared nerve','span lineage \u2014 one nervous mesh through the \u039b heart',1.1);
    addVessel({...organByKey('yuyay'),shared:true,quechua:'YUYAY (\u039b heart)'},{...amaruA,quechua:'YACHAY (killinchu)'},0,kS,'#5ad1ff','P3','shared nerve','span lineage \u2014 \u039b heart \u2192 killinchu cortex',1.1);
    addVessel({...organByKey('overwatch'),quechua:'R0513 (a11oy)'},{...organByKey('overwatch'),quechua:'R0513 (killinchu)'},aS,kS,'#9ef0c0','B2','consensus mesh','n\u22653f+1 Khipu BFT quorum \u2014 cross-body Semantic Quorum (Wave23 conditional safety)',2.0);
  }

  /* ---------------- PULSES (receipt-flow along vessels) ------------- */
  function buildPulses(){
    vessels.forEach((v,i)=>{
      const n = v.shared ? 4 : (Math.random()<0.5?2:1);
      for(let j=0;j<n;j++){
        const grp=new THREE.Group();
        const core=new THREE.Mesh(new THREE.SphereGeometry(v.shared?0.085:0.065,10,10),
          new THREE.MeshBasicMaterial({color:v.color,transparent:true,opacity:0.95}));
        grp.add(core);
        const gl=glowSprite(v.color,v.shared?0.7:0.5,0.55); grp.add(gl);
        root.add(grp);
        pulses.push({grp,glow:gl,curve:v.curve,t:(i*0.13+j*0.4)%1,speed:0.11+Math.random()*0.12,color:v.color,shared:v.shared});
      }
    });
  }

  /* ---------------- HUD population ---------------- */
  function fillHUD(){
    const K=D.KERNEL;
    $('honesty-card').innerHTML =
      `<div class="row"><span class="dot" style="background:var(--warn)"></span><div><b>\u039b = Conjecture 1.</b> Unconditional uniqueness under original A1\u2013A5 is machine-checked <span style="color:var(--warn);font-weight:600">FALSE</span>; uniqueness holds only within strengthened classes.</div></div>`+
      `<div class="row"><span class="dot" style="background:var(--audit)"></span><div><b>CUT-2 (Wave12) + CUT-1 forward fragment (Wave18).</b> <code>lambda_unique_of_separable</code> \u2014 \u039b uniqueness PROVEN <b>conditional</b> on slice-multiplicativity, axiom-free &amp; kernel-clean. CUT-1 forward fragment adds 19 axiom-clean theorems but stays CONDITIONAL (open gap <code>dyadic_image_dense</code>, multi-week roadmap). Unconditional stays Conjecture 1. <span class="chip" style="color:var(--audit)">conditional \u00b7 axiom-free</span></div></div>`+
      `<div class="row"><span class="dot" style="background:var(--audit)"></span><div><b>Khipu BFT safety = Conjecture 2.</b> Wave23 <code>khipu_quorum_safety_conditional</code> (node B2) proves agreement / no-split-brain <b>conditional</b> on n\u22653f+1 + honest non-equivocation, axiom-clean. Unconditional BFT safety stays Conjecture 2 at the sharp boundary. <span class="chip" style="color:var(--audit)">conditional \u00b7 axiom-clean</span></div></div>`+
      `<div class="row"><span class="dot" style="background:var(--skel)"></span><div><b>8 LOCKED-proven</b> {F1,F4,F7,F11,F12,F18,F19,F22} @ ${K.locked_sha} \u2014 never inflated. <span class="chip" style="color:var(--skel)">kernel-verified</span></div></div>`+
      `<div class="row"><span class="dot" style="background:var(--nerve)"></span><div><b>EXPERIMENTAL tier</b> CI-green on main @ ${K.main_sha} (${K.experimental_decls} decls / ${K.experimental_axioms} axioms / ${K.experimental_sorries} sorries; \u2248${K.experimental_count_approx} instilled cards, ${K.waves_merged}). Additive \u2014 never folded into the locked 8. <span class="chip" style="color:var(--nerve)">CI-green</span></div></div>`+
      `<div class="row"><span class="dot" style="background:var(--audit)"></span><div><b>SLSA L1 honest \u00b7 product images L2 build-attested \u00b7 L3 roadmap.</b> No fabricated metrics \u00b7 no AGI \u00b7 trust never 100%.</div></div>`+
      `<div class="row gpd-row" id="gpd-row"><span class="dot" style="background:var(--brain)"></span><div><b>Governed Post-Determinism (GPD).</b> SZL\u2019s own lens \u2014 the 5 organs are the participant-general model. <span class="chip" style="color:var(--brain)">SZL framework \u00b7 tap to expand</span></div></div>`;
    $('gpd-row').addEventListener('click',openGPD);

    $('sys-list').innerHTML = D.SYSTEMS.map(s=>
      `<div class="sys-row" data-sys="${s.key}"><span class="sw" style="background:${s.color}"></span><div>`+
      `<span class="nm">${s.name}</span> <span class="qn">\u00b7 ${s.organ}</span>`+
      `<span class="fnx">${s.fn}</span></div></div>`).join('');
    $('sys-list').querySelectorAll('.sys-row').forEach(r=>{
      r.addEventListener('mouseenter',()=>highlightSystem(r.dataset.sys,true));
      r.addEventListener('mouseleave',()=>highlightSystem(r.dataset.sys,false));
    });
  }
  function highlightSystem(sys,on){
    organMeshes.forEach(om=>{
      if(om.organ.system===sys && om.grp.userData.halo){
        om.grp.userData.halo.material.opacity = on?0.30:0.0;
        if(om.grp.userData.glow) om.grp.userData.glow.material.opacity = on?0.55:om.glowBase;
      }
    });
  }

  /* ---------------- GPD lens (honest, SZL-only prior art) ----------- */
  function openGPD(){
    const sys={name:'GOVERNED POST-DETERMINISM'};
    $('p-sys').textContent='SZL framework \u00b7 lens';
    $('p-quechua').textContent='GPD';
    $('p-fn').textContent='the 5 organs ARE the participant-general governed-AI model';
    const dois=[
      ['The Loop Is the Product v1','10.5281/zenodo.19867281'],
      ['The Loop Is the Product v2','10.5281/zenodo.19934129'],
      ['Lineage-Aware RAG v5','10.5281/zenodo.20020846'],
      ['Sealed Constitutional Guardrails v6','10.5281/zenodo.20020845'],
      ['Lutar Omega Formalism v4','10.5281/zenodo.20020841'],
      ['SZL Doctrine v2 \u2014 9 Canonical Axes','10.5281/zenodo.20174600']
    ];
    let html=`<div class="blurb">${'Governed Post-Determinism is SZL\u2019s own framework for governed-AI substrates. The unit of agreement shifts from <b>identical output</b> to <b>certified semantic admissibility</b>. The five organs are the participant-general model.'}</div>`;
    html+=`<div class="gpd-grid">`+
      `<div class="gpd-cell"><span class="gpd-k">BRAIN \u00b7 YACHAY</span><span class="gpd-v">reasons \u2014 divergent reasoning paths are OK</span></div>`+
      `<div class="gpd-cell"><span class="gpd-k">HEART \u00b7 YUYAY</span><span class="gpd-v">13-axis gate certifies semantic admissibility (deny-by-default)</span></div>`+
      `<div class="gpd-cell"><span class="gpd-k">SKELETON \u00b7 Khipu BFT</span><span class="gpd-v">Semantic Quorum Assurance \u2014 Wave23 conditional safety; unconditional = Conjecture 2</span></div>`+
      `<div class="gpd-cell"><span class="gpd-k">CIRCULATORY \u00b7 YAWAR</span><span class="gpd-v">Epistemic State Replication + Verifiable Semantic Rollback (receipts/replay live; full ESR = roadmap)</span></div>`+
      `<div class="gpd-cell"><span class="gpd-k">NERVOUS \u00b7 OTel</span><span class="gpd-v">span lineage carries provenance across the substrate</span></div>`+
    `</div>`;
    html+=`<div class="lambda-honesty" style="border-color:var(--brain);background:rgba(124,92,255,.08)"><div class="lh-h" style="color:var(--brain)">honest scope</div><p>Locked-proven stays <b>exactly 8</b>. \u039b = Conjecture 1. Khipu BFT safety = Conjecture 2 (Wave23 conditional only). Grounded entirely in SZL\u2019s own DOI-stamped prior art \u2014 no external paper is cited as the source of GPD.</p></div>`;
    html+=`<div class="sec-h">SZL prior art (Zenodo, DOI-stamped)</div><div class="gpd-dois">`+
      dois.map(([t,d])=>`<a class="doi" href="https://doi.org/${d}" target="_blank" rel="noopener">${t} <span>${d}</span></a>`).join('')+`</div>`;
    $('p-body').innerHTML=html;
    panel.classList.add('open'); panel.setAttribute('aria-hidden','false');
  }

  /* ---------------- ORGAN PANEL ---------------- */
  function fchip(mat){const m=D.MATURITY[mat];return `<span class="chip" style="color:${m.color}">${m.label}</span>`;}
  function formulaCard(fid){
    const f=D.FORMULAS[fid]; if(!f) return '';
    const m=D.MATURITY[f.maturity];
    return `<div class="formula" data-maturity="${f.maturity}" style="border-left-color:${m.color}">
      <div class="ftop"><span class="fid" style="color:${m.color}">${f.id}</span>${fchip(f.maturity)}</div>
      <div class="fname">${f.name}</div>
      <div class="math">${mathToUnicode(f.latex)}</div>
      <div class="fplain">${f.plain}</div>
      <div class="fax">#print axioms: ${f.axioms}</div>
      <div class="fref">${f.ref}</div>
    </div>`;
  }
  function openOrgan(o){
    const sys=D.SYSTEMS.find(s=>s.key===o.system)||{name:o.system};
    $('p-sys').textContent = sys.name + ' \u00b7 system';
    $('p-quechua').textContent = o.quechua;
    $('p-fn').textContent = o.fn;
    let html = `<div class="blurb">${o.blurb}</div>`;
    if(o.axes){ html += `<div class="axes"><b style="color:var(--heart)">13 axes (conjunctive floors):</b><br>${o.axes}</div>`; }
    if(o.lambda_note){
      html += `<div class="lambda-honesty"><div class="lh-h">\u039b honesty label</div>
        <p><b>\u039b is Conjecture 1</b>, not a theorem. Unconditional uniqueness under the original A1\u2013A5 axioms is <span class="false">machine-checked FALSE</span> (in-tree counterexample <code>Round13.maxAgg_ne_Lambda</code> satisfies A1\u2013A5 yet is not \u039b). The beating heart aggregates trust by <b>geometric mean</b> across the 13 axes \u2014 conjunctive, never a weighted average. Trust is never 100%.</p>
        <p style="margin-top:8px"><b style="color:var(--audit)">CUT-2 (axiom-free, kernel-clean).</b> <code>lambda_unique_of_separable</code> \u2014 if \u03a6 is separable (slice-multiplicative) and per-axis monotone under A1,A2,A3,A5 then \u03a6 = \u039b. No new axiom. This gets \u039b <b>off bare conjecture</b> (conditionally); the UNCONDITIONAL claim stays Conjecture 1.</p></div>`;
    }
    html += `<div class="sec-h">Formulas instilled in this organ</div>`;
    (o.formulas||[]).forEach(fid=>{ html += formulaCard(fid); });
    $('p-body').innerHTML = html;
    $('p-body').scrollTop=0;
    panel.classList.add('open'); panel.setAttribute('aria-hidden','false');
    // focus camera on the organ (smooth)
    const om=organMeshes.find(m=>m.organ===o);
    const side = o.shared?0:(om&&om.bodyKey==='killinchu'?1:-1);
    const wp = worldPos(o, side);
    flyTo(new THREE.Vector3(wp.x,wp.y,wp.z), o.shared?9.5:8.2);
    // pulse the selected organ glow
    organMeshes.forEach(m=>{ if(m.grp.userData.glow) m.grp.userData.glow.material.opacity=m.glowBase; });
    if(om&&om.grp.userData.glow) om.grp.userData.glow.material.opacity=0.7;
    selectedOM = om || null;
    if(V4 && V4.applyFocus) V4.applyFocus();   // v4 focus-mode hook (no-op until v4 inits)
    if(V5 && V5.onOrganOpen) V5.onOrganOpen(o); // v5 deepen hook: per-formula Lean drill-down + organ↔formula highlight
  }
  function closePanel(){ panel.classList.remove('open'); panel.setAttribute('aria-hidden','true');
    organMeshes.forEach(m=>{ if(m.grp.userData.glow) m.grp.userData.glow.material.opacity=m.glowBase; });
    selectedOM = null;
    if(V4 && V4.applyFocus) V4.applyFocus(); }
  $('panel-close').addEventListener('click',closePanel);

  /* ---------------- camera tween ---------------- */
  let tween=null;
  let selectedOM=null;   // v4: currently-open organ (for focus mode)
  let V4=null;           // v4: dissection module handle (set after init)
  let V5=null;           // v5: deepen module handle (atlas, forecast, tour, labels, drill-down)
  let V6=null;           // v6: yarqa flow-compartments layer (engineering method / CFD, NOT a locked theorem)
  function flyTo(targetVec, radius){
    tween={fromT:cam.target.clone(),toT:targetVec.clone(),fromR:cam.r,toR:radius==null?cam.r:radius,t:0,dur:0.9};
  }

  /* ---------------- INTERACTION: orbit / zoom / pick ---------------- */
  function applyCam(){
    const {r,phi,theta,target}=cam;
    camera.position.set(
      target.x + r*Math.sin(phi)*Math.sin(theta),
      target.y + r*Math.cos(phi),
      target.z + r*Math.sin(phi)*Math.cos(theta)
    );
    camera.lookAt(target);
  }
  let dragging=false,lastX=0,lastY=0,moved=0;
  // v4: respect prefers-reduced-motion — disable auto-orbit + intro easing by default
  const REDUCED_MOTION = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  let autoRotate=!REDUCED_MOTION, pulsesOn=true;
  if(REDUCED_MOTION){ intro.active=false; cam.r=HOME.r; cam.phi=HOME.phi; cam.theta=HOME.theta; }

  canvas.addEventListener('pointerdown',e=>{dragging=true;intro.active=false;lastX=e.clientX;lastY=e.clientY;moved=0;try{canvas.setPointerCapture(e.pointerId);}catch(_){}});
  canvas.addEventListener('pointermove',e=>{
    if(dragging){
      const dx=e.clientX-lastX,dy=e.clientY-lastY; lastX=e.clientX;lastY=e.clientY; moved+=Math.abs(dx)+Math.abs(dy);
      cam.theta -= dx*0.005; cam.phi=clamp(cam.phi - dy*0.005,0.25,2.75);
      tween=null;
    } else {
      hoverVessel(e);
    }
  });
  window.addEventListener('pointerup',e=>{
    if(dragging && moved<6){ pickOrgan(e); }
    dragging=false;
  });
  canvas.addEventListener('wheel',e=>{e.preventDefault();intro.active=false;tween=null;cam.r=clamp(cam.r+e.deltaY*0.012,5,32);},{passive:false});

  const ray=new THREE.Raycaster(), ndc=new THREE.Vector2();
  function setNDC(e){ndc.x=(e.clientX/innerWidth)*2-1;ndc.y=-(e.clientY/innerHeight)*2+1;ray.setFromCamera(ndc,camera);}
  function pickOrgan(e){
    setNDC(e);
    const meshes=[]; organMeshes.forEach(om=>om.grp.traverse(c=>{if(c.isMesh){c.userData._om=om;meshes.push(c);}}));
    const hit=ray.intersectObjects(meshes,false)[0];
    if(hit){ openOrgan(hit.object.userData._om.organ); }
  }
  let hoverOM=null;
  function hoverVessel(e){
    setNDC(e);
    // organ hover halo
    const oMeshes=[]; organMeshes.forEach(om=>om.grp.traverse(c=>{if(c.isMesh){c.userData._om=om;oMeshes.push(c);}}));
    const oHit=ray.intersectObjects(oMeshes,false)[0];
    const newOM=oHit?oHit.object.userData._om:null;
    if(newOM!==hoverOM){
      if(hoverOM&&hoverOM.grp.userData.halo) hoverOM.grp.userData.halo.material.opacity=0.0;
      if(hoverOM&&hoverOM.grp.userData.glow&&!panel.classList.contains('open')) hoverOM.grp.userData.glow.material.opacity=hoverOM.glowBase;
      hoverOM=newOM;
      if(hoverOM&&hoverOM.grp.userData.halo) hoverOM.grp.userData.halo.material.opacity=0.30;
      if(hoverOM&&hoverOM.grp.userData.glow) hoverOM.grp.userData.glow.material.opacity=0.6;
    }
    if(newOM){ canvas.style.cursor='pointer'; tip.classList.remove('show'); return; }

    const tubes=vessels.map(v=>v.tube);
    const hit=ray.intersectObjects(tubes,false)[0];
    if(hit){
      const v=hit.object.userData.vessel;
      const f=D.FORMULAS[v.formulaId];
      $('tip-t').textContent = v.label + ' \u00b7 ' + v.from + ' \u2192 ' + v.to;
      $('tip-f').textContent = v.fn;
      $('tip-m').textContent = f ? (f.id+' \u00b7 '+mathToUnicode(f.latex)) : '';
      tip.style.left=Math.min(e.clientX+14,innerWidth-300)+'px';
      tip.style.top=(e.clientY+14)+'px';
      tip.classList.add('show');
      canvas.style.cursor='help';
    } else { tip.classList.remove('show'); canvas.style.cursor='grab'; }
  }

  /* ---------------- buttons ---------------- */
  $('btn-rotate').addEventListener('click',function(){autoRotate=!autoRotate;this.classList.toggle('active',autoRotate);});
  $('btn-pulse').addEventListener('click',function(){pulsesOn=!pulsesOn;this.classList.toggle('active',pulsesOn);
    pulses.forEach(p=>p.grp.visible=pulsesOn);});
  $('btn-reset').addEventListener('click',()=>{intro.active=false;tween=null;cam.r=HOME.r;cam.phi=HOME.phi;cam.theta=HOME.theta;cam.target.copy(HOME.target);closePanel();});
  $('btn-mesh').addEventListener('click',function(){
    intro.active=false; tween=null;
    cam.target.set(0,0.0,1.0); cam.r=11; cam.phi=1.45; cam.theta=0.0;
    this.classList.add('active'); setTimeout(()=>this.classList.remove('active'),600);
  });
  var _gpd=$('btn-gpd'); if(_gpd) _gpd.addEventListener('click',function(){ openGPD(); });

  /* ---------------- resize ---------------- */
  let resizeRAF=0;
  addEventListener('resize',()=>{ cancelAnimationFrame(resizeRAF); resizeRAF=requestAnimationFrame(()=>{
    camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
    renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
    renderer.setSize(innerWidth,innerHeight);
  }); });

  /* ---------------- build everything ---------------- */
  D.BODIES.forEach(b=>buildSilhouette(b.side,b.color));
  buildOrgans();
  buildVessels();
  buildPulses();
  fillHUD();

  /* ---------------- animation loop ---------------- */
  const clock=new THREE.Clock();
  let beatPhase=0;
  function loop(){
    requestAnimationFrame(loop);
    const dt=Math.min(clock.getDelta(),0.05), t=clock.elapsedTime;

    // cinematic intro fly-in
    if(intro.active){
      intro.t=Math.min(intro.t+dt/intro.dur,1);
      const e=easeInOutCubic(intro.t);
      cam.r=lerp(intro.from.r,HOME.r,e);
      cam.phi=lerp(intro.from.phi,HOME.phi,e);
      cam.theta=lerp(intro.from.theta,HOME.theta,e);
      if(intro.t>=1) intro.active=false;
    } else if(tween){
      tween.t=Math.min(tween.t+dt/tween.dur,1);
      const e=easeOutCubic(tween.t);
      cam.target.lerpVectors(tween.fromT,tween.toT,e);
      cam.r=lerp(tween.fromR,tween.toR,e);
      if(tween.t>=1) tween=null;
    } else if(autoRotate && !dragging){
      cam.theta += dt*0.10;
    }
    applyCam();

    // heartbeat: double-thump (lub-dub)
    beatPhase += dt*1.4;
    const ph=(beatPhase%1.0);
    let beat=0;
    if(ph<0.12) beat=Math.sin(ph/0.12*Math.PI)*1.0;
    else if(ph>0.18 && ph<0.30) beat=Math.sin((ph-0.18)/0.12*Math.PI)*0.6;
    const sc=1+beat*0.16;
    if(heartGroup){ heartGroup.scale.setScalar(sc);
      if(heartCoreMat) heartCoreMat.emissiveIntensity=1.0+beat*1.0;
      if(heartHalo) heartHalo.material.opacity=0.10+beat*0.18;
      if(heartGlow) heartGlow.material.opacity=0.45+beat*0.35;
      if(heartRing) heartRing.rotation.z += dt*0.4;
      if(heartGroup.userData.ring2) heartGroup.userData.ring2.rotation.z -= dt*0.3;
      heartLight.intensity=1.1+beat*1.7;
    }
    // organ idle bob + rotate + gentle glow breathing
    organMeshes.forEach((om,i)=>{
      if(!om.organ.beat){ om.grp.rotation.y += dt*0.3; om.grp.rotation.x = Math.sin(t*0.5+i)*0.05;
        if(om.grp.userData.glow && om!==hoverOM && !panel.classList.contains('open')){
          om.grp.userData.glow.material.opacity = om.glowBase*(0.85+0.15*Math.sin(t*1.3+i));
        }
      }
    });
    // receipt-flow pulses travel
    if(pulsesOn) pulses.forEach(p=>{
      p.t=(p.t+dt*p.speed)%1;
      const pt=p.curve.getPoint(p.t); p.grp.position.copy(pt);
      const a=0.45+0.55*Math.sin(p.t*Math.PI);
      p.grp.children[0].material.opacity=a;
      if(p.glow) p.glow.material.opacity=a*(p.shared?0.7:0.5);
    });
    // v4: per-frame dissection updates (explode easing, clip plane, HUD tick)
    if(V4 && V4.tick) V4.tick(dt,t);
    // v5: per-frame deepen updates (label projection, breathing heart idle, tour fly)
    if(V5 && V5.tick) V5.tick(dt,t,beat);
    // v6: yarqa flow-compartments layer (additive overlay over the circulatory/YAWAR flow)
    if(V6 && V6.tick) V6.tick(dt,t);
    renderer.render(scene,camera);
    if(!_loaderHidden){ _loaderHidden=true; var ld=$('loader'); if(ld) ld.classList.add('hidden'); }
  }
  var _loaderHidden=false;
  applyCam();
  loop();

  setTimeout(()=>{ var ld=$('loader'); if(ld) ld.classList.add('hidden'); },1500);

  /* =====================================================================
     ============================  v4  ===================================
     DISSECTION UPGRADE — additive module. Reuses the v3 scene, materials,
     organMeshes/vessels registries, the SAME render loop (via V4.tick),
     openOrgan/flyTo, and reads honest posture from D.KERNEL.
     Nothing in v3 above is replaced.
     ===================================================================== */
  V4 = (function(){
    const LS = 'szl-anatomy-v4';
    // Preview-safe persistence: use Web Storage when available, else an in-memory
    // shim (some sandboxed iframes block the storage APIs). Persistence is a
    // progressive enhancement — the viewer works identically without it.
    var _mem = {};
    var _memStore = { getItem:function(k){return (k in _mem)?_mem[k]:null;}, setItem:function(k,v){_mem[k]=String(v);}, removeItem:function(k){delete _mem[k];} };
    var _store = (function(){
      try { var api = window['local'+'Storage']; if(!api) return _memStore; var k='__szl_probe__'; api.setItem(k,'1'); api.removeItem(k); return api; }
      catch(_){ return _memStore; }
    })();
    function loadState(){ try{ return JSON.parse(_store.getItem(LS)||'{}')||{}; }catch(_){ return {}; } }
    function saveState(){ try{ _store.setItem(LS, JSON.stringify(state)); }catch(_){} }

    /* ---- capture each organ group's base position (for explode) ---- */
    organMeshes.forEach(om=>{ om.basePos = om.grp.position.clone(); });
    // body center for radial explode (mean of organ base positions)
    const center = (function(){ const c=new THREE.Vector3(); organMeshes.forEach(om=>c.add(om.basePos)); if(organMeshes.length)c.multiplyScalar(1/organMeshes.length); return c; })();

    /* ---- conceptual dissection LAYERS (additive, honest mapping) ---- */
    const LAYERS = [
      { key:'circulatory', name:'Circulatory', sw:'#ff3b5c', hint:'YAWAR receipt bus' },
      { key:'nervous',     name:'Nervous',     sw:'#5ad1ff', hint:'span lineage' },
      { key:'organs',      name:'Organs',      sw:'#7c5cff', hint:'all organ cores' },
      { key:'skeleton',    name:'Skeleton',    sw:'#ffd166', hint:'bones / Khipu' },
      { key:'halo',        name:'Halos / glow',sw:'#9ef0c0', hint:'volumetric bloom' }
    ];
    const state = Object.assign({ layers:{}, focus:false, dock:true }, loadState());
    LAYERS.forEach(L=>{ if(!state.layers[L.key]) state.layers[L.key]={on:true,op:1}; });

    function organLayer(om){
      const sys = om.organ.system;
      if(sys==='blood') return 'circulatory';
      if(sys==='nerve') return 'nervous';
      if(sys==='skeleton'||sys==='audit') return 'skeleton';
      return 'organs'; // heart, brain
    }
    // record base opacities once so toggling is reversible & honest
    organMeshes.forEach(om=>{
      const mats=[];
      om.grp.traverse(c=>{ if((c.isMesh||c.isSprite) && c.material){ mats.push({m:c.material, base:c.material.opacity, isHalo:(c===om.grp.userData.halo), isGlow:(c===om.grp.userData.glow)}); } });
      om.v4mats = mats;
      om.v4layer = organLayer(om);
    });
    vessels.forEach(v=>{
      v.v4line = { m:v.line.material, base:v.line.material.opacity };
      v.v4layer = (v.color==='#ff3b5c') ? 'circulatory' : 'nervous';
    });
    const silMats = silhouetteMeshes.map(c=>({ m:c.material, base:c.material.opacity }));
    silhouetteMeshes.forEach((c,i)=>{
      const col = c.material.color ? c.material.color.getHexString() : '';
      silMats[i].layer = (/^(ffd166|e8c068|a07c20)/.test(col)) ? 'skeleton' : 'organs';
    });

    function layerMul(key){ const s=state.layers[key]; return (s&&s.on) ? s.op : 0; }

    function applyLayers(){
      const hm = layerMul('halo');
      organMeshes.forEach(om=>{
        const lm = layerMul(om.v4layer);
        om.v4mats.forEach(rec=>{
          if(rec.isHalo){ rec.m.opacity = rec.base * hm; }
          else if(rec.isGlow){ rec.m.opacity = rec.base * hm; }
          else { rec.m.opacity = rec.base * lm; }
          rec.m.visible = (rec.m.opacity>0.001);
        });
      });
      vessels.forEach(v=>{ const mul=layerMul(v.v4layer); v.v4line.m.opacity=v.v4line.base*mul; v.v4line.m.visible=mul>0.001; });
      pulses.forEach(p=>{ const lay=(p.color==='#ff3b5c')?'circulatory':'nervous'; p.grp.visible = pulsesOn && layerMul(lay)>0.001; });
      silhouetteMeshes.forEach((c,i)=>{ const mul=layerMul(silMats[i].layer); c.material.opacity=silMats[i].base*mul; c.visible=mul>0.001; });
    }

    /* ---- FOCUS MODE: fade non-selected organs when one is open ---- */
    function applyFocus(){
      const on = state.focus && selectedOM;
      const hm = layerMul('halo');
      organMeshes.forEach(om=>{
        const dim = on && om!==selectedOM;
        const lm=layerMul(om.v4layer);
        om.v4mats.forEach(rec=>{
          if(rec.isHalo) return;
          let baseOp = rec.isGlow ? rec.base*hm : rec.base*lm;
          rec.m.opacity = dim ? baseOp*0.12 : baseOp;
          rec.m.visible = rec.m.opacity>0.001;
        });
      });
    }

    /* ---- CLIP-PLANE SCALPEL ---- */
    renderer.localClippingEnabled = true;
    const clip = { on:false, axis:'x', dist:0, plane:new THREE.Plane(new THREE.Vector3(-1,0,0), 0) };
    function axisNormal(a){ return a==='x'?new THREE.Vector3(-1,0,0):a==='y'?new THREE.Vector3(0,-1,0):new THREE.Vector3(0,0,-1); }
    const clipMats = [];
    organMeshes.forEach(om=> om.grp.traverse(c=>{ if(c.isMesh && c.material) clipMats.push(c.material); }));
    silhouetteMeshes.forEach(c=>{ if(c.material) clipMats.push(c.material); });
    function applyClip(){
      clip.plane.normal.copy(axisNormal(clip.axis));
      clip.plane.constant = clip.dist;
      const planes = clip.on ? [clip.plane] : [];
      clipMats.forEach(m=>{ m.clippingPlanes = planes; });
    }

    /* ---- EXPLODE VIEW (eased radial separation) ---- */
    let explodeTarget=0, explodeCur=0;
    function applyExplode(amount){
      organMeshes.forEach(om=>{
        if(om.organ.beat) return; // keep the Λ heart anchored at center
        const dir = om.basePos.clone().sub(center);
        if(dir.lengthSq()<1e-6) dir.set(0,1,0);
        dir.normalize();
        const push = amount * 3.4;
        om.grp.position.copy(om.basePos).addScaledVector(dir, push);
      });
    }

    /* ===================== UI WIRING ===================== */
    const el = id=>document.getElementById(id);

    const dock=el('dissect'), dzHead=el('dz-head'), btnDissect=el('btn-dissect');
    function setDock(open){
      state.dock=open; saveState();
      dock.classList.toggle('collapsed', !open);
      dzHead.setAttribute('aria-expanded', String(open));
      if(btnDissect){ btnDissect.classList.toggle('active', open); btnDissect.setAttribute('aria-expanded', String(open)); }
    }
    dzHead.addEventListener('click', ()=>setDock(dock.classList.contains('collapsed')));
    dzHead.addEventListener('keydown', e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); setDock(dock.classList.contains('collapsed')); } });
    if(btnDissect) btnDissect.addEventListener('click', ()=>setDock(dock.classList.contains('collapsed')));
    setDock(state.dock!==false);

    /* ---- mobile bottom-sheet: FAB opens/closes the dock as a sheet ---- */
    const fab = el('dissect-fab');
    function setSheet(open){
      dock.classList.toggle('sheet-open', open);
      if(fab){ fab.setAttribute('aria-expanded', String(open)); fab.setAttribute('aria-label', open?'Close dissection tools':'Open dissection tools'); }
      // when opening the sheet, make sure the dock body is expanded (not collapsed)
      if(open && dock.classList.contains('collapsed')) setDock(true);
    }
    if(fab){
      fab.addEventListener('click', ()=> setSheet(!dock.classList.contains('sheet-open')) );
    }
    // Esc closes the sheet on mobile
    window.addEventListener('keydown', e=>{ if(e.key==='Escape' && dock.classList.contains('sheet-open')) setSheet(false); });

    const layWrap=el('dz-layers');
    LAYERS.forEach(L=>{
      const s=state.layers[L.key];
      const row=document.createElement('div'); row.className='dz-layer';
      row.innerHTML =
        `<button class="dz-toggle" id="lt-${L.key}" role="switch" aria-pressed="${s.on}" aria-label="${L.name} layer visibility"></button>`+
        `<span class="lname"><span class="lsw" style="color:${L.sw}"></span>${L.name}</span>`+
        `<input type="range" class="dz-range" id="lo-${L.key}" min="0" max="1" step="0.01" value="${s.op}" aria-label="${L.name} opacity">`;
      layWrap.appendChild(row);
      const tog=row.querySelector('.dz-toggle'), rng=row.querySelector('input');
      tog.addEventListener('click', ()=>{ s.on=!s.on; tog.setAttribute('aria-pressed',String(s.on)); saveState(); applyLayers(); applyFocus(); });
      rng.addEventListener('input', ()=>{ s.op=parseFloat(rng.value); if(!s.on){ s.on=true; tog.setAttribute('aria-pressed','true'); } saveState(); applyLayers(); applyFocus(); });
    });

    const clipOn=el('dz-clip-on'), clipReset=el('dz-clip-reset'), clipRange=el('dz-clip'), clipVal=el('dz-clip-val');
    const axisBtns={x:el('dz-axis-x'),y:el('dz-axis-y'),z:el('dz-axis-z')};
    function setAxis(a){ clip.axis=a; Object.keys(axisBtns).forEach(k=>axisBtns[k].setAttribute('aria-pressed',String(k===a))); applyClip(); }
    Object.keys(axisBtns).forEach(k=>axisBtns[k].addEventListener('click',()=>setAxis(k)));
    clipOn.addEventListener('click', ()=>{ clip.on=!clip.on; clipOn.setAttribute('aria-pressed',String(clip.on)); clipOn.classList.toggle('active',clip.on); clipOn.textContent=clip.on?'cutting':'enable cut'; applyClip(); });
    clipRange.addEventListener('input', ()=>{ clip.dist=parseFloat(clipRange.value); clipVal.textContent=clip.dist.toFixed(1); applyClip(); });
    clipReset.addEventListener('click', ()=>{ clip.on=false; clip.dist=0; clipRange.value=0; clipVal.textContent='0.0'; clipOn.setAttribute('aria-pressed','false'); clipOn.classList.remove('active'); clipOn.textContent='enable cut'; setAxis('x'); applyClip(); });

    const expRange=el('dz-explode'), expVal=el('dz-explode-val');
    expRange.addEventListener('input', ()=>{ explodeTarget=parseFloat(expRange.value); expVal.textContent=Math.round(explodeTarget*100)+'%'; if(REDUCED_MOTION){ explodeCur=explodeTarget; applyExplode(easeInOutCubic(explodeCur)); } });

    const btnFocus=el('btn-focus');
    if(btnFocus){
      btnFocus.setAttribute('aria-pressed', String(!!state.focus));
      btnFocus.classList.toggle('active', !!state.focus);
      btnFocus.addEventListener('click', ()=>{ state.focus=!state.focus; btnFocus.setAttribute('aria-pressed',String(state.focus)); btnFocus.classList.toggle('active',state.focus); saveState(); applyFocus(); });
    }
    const btnRot=el('btn-rotate'); if(btnRot) btnRot.classList.toggle('active', autoRotate);

    /* ---- SEARCH / JUMP (organs + formulas) ---- */
    const q=el('dz-q'), results=el('dz-results');
    const index = [];
    D.ORGANS.forEach(o=>{ index.push({type:'organ', key:o.key, label:o.quechua, sub:(D.SYSTEMS.find(s=>s.key===o.system)||{}).name||o.system, organ:o}); });
    Object.keys(D.FORMULAS).forEach(fid=>{ const f=D.FORMULAS[fid]; index.push({type:'formula', key:fid, label:f.id+' · '+f.name, sub:(D.MATURITY[f.maturity]||{}).label||f.maturity, formula:f}); });
    let activeIdx=-1, matches=[];
    function runSearch(){
      const term=q.value.trim().toLowerCase();
      results.innerHTML=''; activeIdx=-1;
      if(!term){ results.classList.remove('show'); q.setAttribute('aria-expanded','false'); return; }
      matches = index.filter(it=> (it.label+' '+it.key+' '+(it.sub||'')).toLowerCase().includes(term)).slice(0,12);
      if(!matches.length){ results.innerHTML='<li class="empty" role="option">no organ or formula matches</li>'; results.classList.add('show'); q.setAttribute('aria-expanded','true'); return; }
      matches.forEach((it,i)=>{
        const li=document.createElement('li'); li.setAttribute('role','option'); li.id='dzr-'+i;
        li.innerHTML=`<span class="rk">${it.type==='organ'?'\u25c9':'\u0192'}</span><span>${it.label}</span><span class="rt">${it.sub||''}</span>`;
        li.addEventListener('click',()=>jump(it));
        results.appendChild(li);
      });
      results.classList.add('show'); q.setAttribute('aria-expanded','true');
    }
    function highlight(i){
      const lis=results.querySelectorAll('li'); lis.forEach(l=>l.setAttribute('aria-selected','false'));
      if(i>=0 && i<lis.length){ lis[i].setAttribute('aria-selected','true'); lis[i].scrollIntoView({block:'nearest'}); q.setAttribute('aria-activedescendant', lis[i].id); }
    }
    function jump(it){
      if(!it) return;
      if(it.type==='organ'){ openOrgan(it.organ); }
      else { const host = D.ORGANS.find(o=>(o.formulas||[]).includes(it.key)); if(host){ openOrgan(host); } }
      results.classList.remove('show'); q.setAttribute('aria-expanded','false'); q.blur();
    }
    q.addEventListener('input', runSearch);
    q.addEventListener('keydown', e=>{
      if(e.key==='ArrowDown'){ e.preventDefault(); if(matches.length){ activeIdx=Math.min(activeIdx+1,matches.length-1); highlight(activeIdx);} }
      else if(e.key==='ArrowUp'){ e.preventDefault(); activeIdx=Math.max(activeIdx-1,0); highlight(activeIdx); }
      else if(e.key==='Enter'){ e.preventDefault(); jump(matches[activeIdx>=0?activeIdx:0]); }
      else if(e.key==='Escape'){ results.classList.remove('show'); q.setAttribute('aria-expanded','false'); }
    });
    document.addEventListener('click', e=>{ if(!results.contains(e.target) && e.target!==q){ results.classList.remove('show'); q.setAttribute('aria-expanded','false'); } });

    /* ---- ALWAYS-ON VISIBILITY HUD (honest counts from D.KERNEL) ---- */
    const K=D.KERNEL;
    function expCount(){ return Object.keys(D.FORMULAS).filter(id=>D.FORMULAS[id].maturity==='EXPERIMENTAL').length; }
    (function fillVisHUD(){
      const grid=el('vh-grid'), foot=el('vh-foot');
      const stats=[
        {k:'locked-proven', v:K.locked_proven.length, cls:'locked'},
        {k:'experimental',  v:expCount(), cls:'exp'},
        {k:'axioms',        v:K.locked_axioms, cls:''},
        {k:'sorries',       v:K.locked_sorries, cls:''},
        {k:'\u039b posture', v:'Conjecture 1', cls:'conj'},
        {k:'Khipu BFT',     v:'Conjecture 2', cls:'conj'}
      ];
      grid.innerHTML = stats.map(s=>`<div class="vh-stat"><span class="k">${s.k}</span><span class="v ${s.cls}">${s.v}</span></div>`).join('');
      foot.innerHTML = `kernel <code>${K.locked_sha}</code> \u00b7 locked-set {${K.locked_proven.join(',')}} \u00b7 SLSA L1 honest \u00b7 trust never 100%`;
    })();

    /* ---- per-frame tick (called from the SINGLE v3 render loop) ---- */
    let tickAcc=0;
    function tick(dt,t){
      if(!REDUCED_MOTION && Math.abs(explodeCur-explodeTarget)>0.0005){
        explodeCur += (explodeTarget-explodeCur) * Math.min(1, dt*6);
        applyExplode(easeInOutCubic(explodeCur));
      }
      tickAcc+=dt;
      if(tickAcc>0.08){ tickAcc=0; applyLayers(); applyFocus(); }
    }

    applyLayers(); applyClip(); applyFocus();

    return {
      tick, applyFocus, applyLayers,
      _state:state, LAYERS,
      setLayer:(key,on,op)=>{ const s=state.layers[key]; if(s){ if(on!=null)s.on=on; if(op!=null)s.op=op; saveState(); applyLayers(); } },
      setExplode:(a)=>{ explodeTarget=a; if(REDUCED_MOTION){explodeCur=a;applyExplode(easeInOutCubic(a));} expRange.value=a; expVal.textContent=Math.round(a*100)+'%'; },
      setClip:(on,axis,dist)=>{ clip.on=on; if(axis)clip.axis=axis; if(dist!=null)clip.dist=dist; applyClip(); },
      setFocus:(on)=>{ state.focus=on; saveState(); applyFocus(); },
      search:(term)=>{ q.value=term; runSearch(); return matches.length; },
      jumpFirst:()=>{ jump(matches[0]); return panel.classList.contains('open'); },
      hud:()=>({ locked:K.locked_proven.length, experimental:expCount(), axioms:K.locked_axioms, sorries:K.locked_sorries, kernel:K.locked_sha })
    };
  })();
  /* ==========================  /v4  =================================== */

  /* =====================================================================
     ===========================  v4-DEEPEN (v5)  ========================
     DEEPENING UPGRADE — additive module. Reuses the v3/v4 scene, camera,
     organMeshes/vessels registries, the SAME render loop (via V5.tick),
     openOrgan/flyTo/closePanel, mathToUnicode, and reads EVERYTHING from
     window.SZL_ANATOMY (D). Nothing in v3/v4 above is replaced.
     ===================================================================== */
  V5 = (function(){
    const el = id=>document.getElementById(id);
    const D = window.SZL_ANATOMY;
    const M = D.MATURITY, F = D.FORMULAS, K = D.KERNEL;

    /* ---- tier order + honest descriptions (straight from D.MATURITY) ---- */
    const TIER_ORDER = ['LOCKED','CONDITIONAL','AXIOM_GATED','EXPERIMENTAL','CONJECTURE'];
    function tierColor(t){ return (M[t]||{}).color || '#9aa8cc'; }
    function tierLabel(t){ return (M[t]||{}).label || t; }
    function tierDesc(t){ return (M[t]||{}).desc || ''; }

    // live counts straight from data.js — never hardcoded
    function countByTier(){
      const c={}; TIER_ORDER.forEach(t=>c[t]=0);
      Object.keys(F).forEach(k=>{ const m=F[k].maturity; c[m]=(c[m]||0)+1; });
      return c;
    }

    /* ---- honest "view in lutar-lean" link derived from the ref string.
       We NEVER invent a precise permalink: PR refs -> /pull/N; otherwise
       we link to a repo code-search for the .lean file / declaration so the
       reader lands on the real source. lutar-lean is the kernel repo. ---- */
    const LEAN_REPO = 'https://github.com/szl-holdings/lutar-lean';
    function leanLink(f){
      const ref = f.ref || '';
      const pr = ref.match(/(?:lutar-lean\s*)?(?:PR\s*)?#(\d+)/);
      // a *.lean file mentioned in the ref (best-effort, honest)
      const file = ref.match(/([A-Za-z0-9_\/]+\.lean)/);
      let href, kind;
      if(pr && /lutar-lean/i.test(ref)){ href = LEAN_REPO + '/pull/' + pr[1]; kind='PR #'+pr[1]; }
      else if(file){ href = LEAN_REPO + '/search?q=' + encodeURIComponent(file[1].split('/').pop()) + '&type=code'; kind=file[1].split('/').pop(); }
      else if(pr){ href = LEAN_REPO + '/pulls?q=' + encodeURIComponent('#'+pr[1]); kind='PR #'+pr[1]; }
      else { href = LEAN_REPO + '/search?q=' + encodeURIComponent((f.id||'')+' '+f.name) + '&type=code'; kind='lutar-lean'; }
      return {href, kind};
    }

    /* ---- shared drill-down detail block (axioms + lutar-lean link) ----
       Returned as an HTML <details> so it is keyboard-accessible & additive
       to any formula card. Used by both the Atlas and the organ panel. ---- */
    function drillHTML(f){
      const ll = leanLink(f);
      return `<details class="fdrill"><summary>axioms &amp; Lean source</summary>`+
        `<div class="fdd">`+
        `<div class="fax2">#print axioms: ${esc(f.axioms)}</div>`+
        `<div class="fax2" style="margin-top:6px;color:var(--text-muted)">ref: ${esc(f.ref)}</div>`+
        `<a class="lean-link" href="${ll.href}" target="_blank" rel="noopener">↗ view in lutar-lean · ${esc(ll.kind)}</a>`+
        `</div></details>`;
    }
    function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

    /* =====================================================================
       (B) PER-ORGAN DRILL-DOWN + organ↔formula 3D highlight
       After openOrgan() renders its v3 formula cards, we enhance each card
       in place: tag it with its formula id, append the drill-down details,
       and wire hover so hovering a card lights up the owning organ in 3D
       (and vice-versa). Purely additive DOM enhancement. ===================== */
    function organByFormula(fid){ return D.ORGANS.find(o=>(o.formulas||[]).includes(fid)); }
    function omByOrgan(o){ return organMeshes.find(m=>m.organ===o); }
    function litOM(om,on){
      if(!om) return;
      if(om.grp.userData.halo) om.grp.userData.halo.material.opacity = on?0.34:0.0;
      if(om.grp.userData.glow) om.grp.userData.glow.material.opacity = on?0.7:om.glowBase;
    }
    function onOrganOpen(o){
      const body = el('p-body'); if(!body) return;
      const cards = body.querySelectorAll('.formula');
      // the v3 cards render in the order of o.formulas — map by index, robust.
      const ids = (o.formulas||[]);
      cards.forEach((card,i)=>{
        const fid = ids[i]; const f = fid && F[fid]; if(!f) return;
        card.setAttribute('data-fid', fid);
        // avoid double-injecting if openOrgan is called twice
        if(!card.querySelector('.fdrill')){
          const tmp=document.createElement('div'); tmp.innerHTML=drillHTML(f);
          card.appendChild(tmp.firstChild);
        }
        const om = omByOrgan(o); // this organ
        card.onmouseenter = ()=>litOM(om,true);
        card.onmouseleave = ()=>{ if(!panel.classList.contains('open')||selectedOM!==om) litOM(om,false); else litOM(om,false); };
      });
    }

    /* =====================================================================
       (A) FORMULA ATLAS — every formula in data.js, tier-grouped
       ===================================================================== */
    const atlas = el('atlas');
    let atlasFilter = 'ALL';
    let atlasQuery = '';

    function atlasFormulaCard(fid){
      const f = F[fid]; if(!f) return '';
      const col = tierColor(f.maturity);
      return `<div class="formula" data-fid="${fid}" data-maturity="${f.maturity}" style="border-left-color:${col}">`+
        `<div class="ftop"><span class="fid" style="color:${col}">${esc(f.id)}</span>`+
        `<span class="chip" style="color:${col}">${esc(tierLabel(f.maturity))}</span></div>`+
        `<div class="fname">${esc(f.name)}</div>`+
        `<div class="math">${mathToUnicode(f.latex)}</div>`+
        `<div class="fplain">${esc(f.plain)}</div>`+
        drillHTML(f)+
        `</div>`;
    }

    function buildAtlasFilters(){
      const wrap = el('atlas-filters'); if(!wrap) return;
      const counts = countByTier();
      const total = Object.keys(F).length;
      let html = `<button class="at-pill" data-tier="ALL" aria-pressed="true">ALL <span class="ct">${total}</span></button>`;
      TIER_ORDER.forEach(t=>{
        if(!counts[t]) return; // only show tiers that actually exist in data.js
        html += `<button class="at-pill" data-tier="${t}" aria-pressed="false" style="color:${tierColor(t)}">`+
                `${t.replace('_',' ')} <span class="ct">${counts[t]}</span></button>`;
      });
      wrap.innerHTML = html;
      wrap.querySelectorAll('.at-pill').forEach(b=>{
        b.addEventListener('click', ()=>{
          atlasFilter = b.getAttribute('data-tier');
          wrap.querySelectorAll('.at-pill').forEach(x=>x.setAttribute('aria-pressed', String(x===b)));
          renderAtlas();
        });
      });
    }

    function renderAtlas(){
      const body = el('atlas-body'); if(!body) return;
      const counts = countByTier();
      const total = Object.keys(F).length;
      const note = el('atlas-note');
      if(note) note.innerHTML = `Every formula instilled across the body — <b>${total}</b> total, read live from <code>data.js</code>. `+
        `Locked-proven = exactly <b>${counts.LOCKED||0}</b> {${K.locked_proven.join(', ')}}. CONJECTURE / EXPERIMENTAL / AXIOM-GATED are NEVER relabeled as LOCKED.`;
      const q = atlasQuery.trim().toLowerCase();
      let html = '';
      const tiers = TIER_ORDER.filter(t=> counts[t] && (atlasFilter==='ALL' || atlasFilter===t));
      tiers.forEach(t=>{
        const ids = Object.keys(F).filter(k=>F[k].maturity===t).filter(k=>{
          if(!q) return true;
          const f=F[k];
          return (f.id+' '+f.name+' '+f.plain+' '+f.axioms+' '+f.latex+' '+f.ref).toLowerCase().includes(q);
        });
        if(!ids.length && q) return; // hide empty tiers while searching
        html += `<div class="at-tier"><div class="at-tier-h" style="color:${tierColor(t)}">`+
          `<span class="tn">${t.replace('_',' ')}</span>`+
          `<span class="tc">${ids.length} / ${counts[t]}</span>`+
          `<span class="td">${esc(tierDesc(t))}</span></div>`;
        if(ids.length){ ids.forEach(id=>{ html += atlasFormulaCard(id); }); }
        else { html += `<div class="at-empty">no match in this tier</div>`; }
        html += `</div>`;
      });
      if(!html) html = `<div class="at-empty">No formula matches “${esc(atlasQuery)}”.</div>`;
      body.innerHTML = html;
      // wire card hover -> 3D organ highlight (organ↔formula traceability)
      body.querySelectorAll('.formula').forEach(card=>{
        const fid = card.getAttribute('data-fid');
        const o = organByFormula(fid); const om = o && omByOrgan(o);
        card.onmouseenter = ()=>{ litOM(om,true); card.classList.add('lit'); };
        card.onmouseleave = ()=>{ litOM(om,false); card.classList.remove('lit'); };
      });
    }

    function openAtlas(){
      closeForecast();
      buildAtlasFilters(); renderAtlas();
      atlas.classList.add('open'); atlas.setAttribute('aria-hidden','false');
      const b=el('btn-atlas'); if(b){ b.classList.add('active'); b.setAttribute('aria-expanded','true'); }
    }
    function closeAtlas(){
      atlas.classList.remove('open'); atlas.setAttribute('aria-hidden','true');
      const b=el('btn-atlas'); if(b){ b.classList.remove('active'); b.setAttribute('aria-expanded','false'); }
    }
    (function wireAtlas(){
      const b=el('btn-atlas'); if(b) b.addEventListener('click', ()=> atlas.classList.contains('open')?closeAtlas():openAtlas());
      const c=el('atlas-close'); if(c) c.addEventListener('click', closeAtlas);
      const q=el('atlas-q'); if(q) q.addEventListener('input', ()=>{ atlasQuery=q.value; renderAtlas(); });
      window.addEventListener('keydown', e=>{ if(e.key==='Escape' && atlas.classList.contains('open')) closeAtlas(); });
    })();

    /* =====================================================================
       (D) HONEST FORECAST OVERLAY — proof-maturity transparency timeline
       Driven ONLY by data.js / KERNEL strings. Achieved facts come from the
       kernel posture; everything not-yet-done is explicitly ROADMAP/PROJECTED
       and pulled verbatim from KERNEL / FORMULA strings. No invented metric.
       ===================================================================== */
    // Achieved (DONE) — every value here exists in D.KERNEL / D.MATURITY.
    function forecastDoneEvents(){
      const counts = countByTier();
      const ev = [];
      // The single dated transition we can honestly assert from data.js:
      // KERNEL.gpd states "locked-proven = exactly 8 ... F4/F7/F22 joined the original 5 on 2026-06-10".
      ev.push({ when:'pre 2026-06-10', what:`<b>5 LOCKED-proven.</b> Original locked set before the 2026-06-10 upgrade (the 8 minus F4/F7/F22).` , tag:'done'});
      ev.push({ when:'2026-06-10', what:`<b>LOCKED 5 → ${K.locked_proven.length}.</b> F4 (Khipu DAG acyclicity), F7 (Chaski FIFO), F22 (Khipu emit monotonicity) upgraded to genuine kernel-verified proofs. Locked set now {${K.locked_proven.join(', ')}} @ <code>${K.locked_sha}</code>. (Source: KERNEL.gpd / KERNEL.locked_proven.)`, tag:'done'});
      ev.push({ when:'waves 5–23', what:`<b>${counts.EXPERIMENTAL||0} EXPERIMENTAL · CI-green</b> cards instilled (${esc(K.waves_merged)}), main @ <code>${K.main_sha}</code> — additive, NEVER folded into the locked ${K.locked_proven.length}.`, tag:'done'});
      ev.push({ when:'Wave12', what:`<b>CUT-2 conditional Λ uniqueness.</b> ${esc(K.cut2)}`, tag:'done'});
      ev.push({ when:'Wave23', what:`<b>Khipu BFT conditional safety.</b> ${esc(K.bft_conditional)}`, tag:'done'});
      return ev;
    }
    // ROADMAP / PROJECTED — pulled ONLY from text that data.js already states
    // as an open gap / roadmap. Nothing here is claimed as achieved.
    function forecastRoadmapEvents(){
      const rm = [];
      // CUT-1 open gap (verbatim from FORMULAS.CUT1)
      if(F.CUT1) rm.push({ when:'ROADMAP', what:`<b>CUT-1 full unconditional Λ.</b> Open gap <code>dyadic_image_dense</code> (dense-domain step, n-adic recursive construction). Multi-week roadmap — Λ unconditional uniqueness stays <b>Conjecture 1</b>. (Source: FORMULAS.CUT1.)`, tag:'proj'});
      // Khipu unconditional BFT (Conjecture 2) — from B2 / KERNEL.bft_conditional
      rm.push({ when:'ROADMAP', what:`<b>Unconditional Khipu BFT safety.</b> Stays <b>Conjecture 2</b> at the sharp boundary; only the n≥3f+1 + honest-non-equivocation conditional theorem (B2 / Wave23) is proven. (Source: KERNEL.bft_conditional.)`, tag:'proj'});
      // Per-formula honest ROADMAP notes mined from FORMULA plain/axioms strings
      Object.keys(F).forEach(k=>{
        const f=F[k]; const blob=(f.plain+' '+f.axioms);
        if(/ROADMAP/i.test(blob)){
          // surface the formula's own roadmap caveat (verbatim-ish, trimmed)
          rm.push({ when:'ROADMAP', what:`<b>${esc(f.id)} — ${esc(f.name)}.</b> ${roadmapSnippet(f)}`, tag:'proj'});
        }
      });
      // SLSA ladder (verbatim from KERNEL.slsa)
      rm.push({ when:'ROADMAP', what:`<b>SLSA L3.</b> Static space is SLSA <b>L1 honest</b>; product images L2 build-attested; <b>L3 is roadmap</b>. (Source: KERNEL.slsa.)`, tag:'proj'});
      return rm;
    }
    function roadmapSnippet(f){
      // extract the sentence/parenthetical that mentions ROADMAP, honestly
      const txt=f.plain+' '+f.axioms;
      const m=txt.match(/\(?([^.()]*ROADMAP[^.()]*)\)?/i);
      let s = m? m[1].trim() : 'roadmap (see lutar-lean)';
      return esc(s) + ' <span style="color:var(--text-dim)">— roadmap (see lutar-lean).</span>';
    }

    // sparkline of locked-proven growth (only points we can honestly assert)
    function forecastSpark(){
      const counts = countByTier();
      // honest two-point locked trajectory from data.js + the live total today
      const series = [
        { label:'pre 6-10', v:5,  proj:false },
        { label:'2026-06-10', v:K.locked_proven.length, proj:false }
      ];
      const W=460, H=92, pad=22, maxV=Math.max(8, K.locked_proven.length, 10);
      const n=series.length;
      const xOf=i=> pad + (W-2*pad) * (n===1?0.5:(i/(n-1)));
      const yOf=v=> (H-18) - ((H-30) * (v/maxV));
      let path='', dots='';
      series.forEach((p,i)=>{
        const x=xOf(i), y=yOf(p.v);
        path += (i===0?'M':'L') + x.toFixed(1) + ' ' + y.toFixed(1) + ' ';
        dots += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.4" fill="${p.proj?'var(--brain)':'var(--skel)'}"></circle>`+
                `<text x="${x.toFixed(1)}" y="${(y-9).toFixed(1)}" fill="${p.proj?'var(--brain)':'var(--skel)'}" font-family="ui-monospace,monospace" font-size="11" text-anchor="middle">${p.v}</text>`+
                `<text x="${x.toFixed(1)}" y="${(H-3).toFixed(1)}" fill="var(--text-dim)" font-family="ui-monospace,monospace" font-size="8.5" text-anchor="middle">${p.label}</text>`;
      });
      // a dashed PROJECTED continuation toward the roadmap (clearly not achieved)
      const lastX=xOf(n-1), lastY=yOf(series[n-1].v);
      const projX=W-pad, projY=yOf(series[n-1].v); // flat — we do NOT predict a number
      const projLine = `<path d="M${lastX.toFixed(1)} ${lastY.toFixed(1)} L${projX.toFixed(1)} ${projY.toFixed(1)}" stroke="var(--brain)" stroke-width="2" stroke-dasharray="4 4" fill="none" opacity="0.7"></path>`+
        `<text x="${projX.toFixed(1)}" y="${(projY-9).toFixed(1)}" fill="var(--brain)" font-family="ui-monospace,monospace" font-size="8.5" text-anchor="end">ROADMAP (no number claimed)</text>`;
      return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Locked-proven count: 5 then ${K.locked_proven.length}; future is roadmap, no number claimed">`+
        projLine+
        `<path d="${path.trim()}" stroke="var(--skel)" stroke-width="2.4" fill="none"></path>`+
        dots+`</svg>`;
    }

    function renderForecast(){
      const body=el('forecast-body'); if(!body) return;
      const counts=countByTier();
      const note=el('forecast-note');
      if(note) note.innerHTML = `A transparency forecast of <b>proof maturity</b>, driven only by <code>data.js</code> / KERNEL strings — <b>not a fabricated metric</b>. Achieved facts are marked <span style="color:var(--skel)">DONE</span>; everything not-yet-achieved is <span style="color:var(--brain)">ROADMAP / PROJECTED</span>. We never predict a future locked count.`;
      let html='';
      html += `<div class="fc-spark"><div class="sp-h">locked-proven trajectory (kernel-verified)</div>${forecastSpark()}`+
        `<div class="fc-legend"><span><i style="background:var(--skel)"></i> DONE · kernel-verified</span>`+
        `<span><i style="background:var(--brain)"></i> ROADMAP · projected (no number claimed)</span></div></div>`;
      // live tier snapshot (counts straight from data.js)
      html += `<div class="fc-sec-h">live tier snapshot (data.js)</div>`;
      TIER_ORDER.filter(t=>counts[t]).forEach(t=>{
        html += `<div class="fc-event"><span class="ev-when" style="color:${tierColor(t)}">${counts[t]}×</span>`+
          `<span class="ev-what"><b>${t.replace('_',' ')}</b> — ${esc(tierDesc(t))}</span></div>`;
      });
      html += `<div class="fc-sec-h">achieved milestones <span class="fc-tag done">DONE</span></div>`;
      forecastDoneEvents().forEach(e=>{ html += `<div class="fc-event"><span class="ev-when">${esc(e.when)}</span><span class="ev-what">${e.what}</span></div>`; });
      html += `<div class="fc-sec-h">roadmap / projected <span class="fc-tag proj">NOT YET ACHIEVED</span></div>`;
      forecastRoadmapEvents().forEach(e=>{ html += `<div class="fc-event roadmap"><span class="ev-when">${esc(e.when)}</span><span class="ev-what">${e.what}</span></div>`; });
      html += `<div class="fc-disc"><b>Honesty.</b> This panel forecasts only <i>maturity transparency</i>, never capability. Λ = Conjecture 1; Khipu BFT = Conjecture 2; SLSA L1 honest. No EXPERIMENTAL / CONDITIONAL / AXIOM-GATED / CONJECTURE item is relabeled LOCKED, and no future proof count is invented. Where a field is missing we surface what exists and label the rest roadmap (see lutar-lean).</div>`;
      body.innerHTML = html;
    }
    function openForecast(){
      closeAtlas();
      renderForecast();
      el('forecast').classList.add('open'); el('forecast').setAttribute('aria-hidden','false');
      const b=el('btn-forecast'); if(b){ b.classList.add('active'); b.setAttribute('aria-expanded','true'); }
    }
    function closeForecast(){
      const fc=el('forecast'); if(!fc) return;
      fc.classList.remove('open'); fc.setAttribute('aria-hidden','true');
      const b=el('btn-forecast'); if(b){ b.classList.remove('active'); b.setAttribute('aria-expanded','false'); }
    }
    (function wireForecast(){
      const b=el('btn-forecast'); if(b) b.addEventListener('click', ()=> el('forecast').classList.contains('open')?closeForecast():openForecast());
      const c=el('forecast-close'); if(c) c.addEventListener('click', closeForecast);
      window.addEventListener('keydown', e=>{ if(e.key==='Escape' && el('forecast').classList.contains('open')) closeForecast(); });
    })();

    /* =====================================================================
       (C) MORE REAL 3D — leader-line organ labels
       A thin 3D leader line from each organ outward to a tag anchor, plus an
       HTML label projected to screen each frame. Reuses root + the SAME loop.
       ===================================================================== */
    const labelLayer = el('labels');
    const labels = []; // {om, div, anchorWorld, line}
    let labelsOn = true;
    function buildLabels(){
      organMeshes.forEach(om=>{
        const o=om.organ;
        // leader anchor: push outward along +x of the body and slightly up
        const side = o.shared?0:(om.bodyKey==='killinchu'?1:-1);
        const base = om.basePos ? om.basePos.clone() : om.grp.position.clone();
        const outX = side===0 ? (o.pos[0]>=0?1:-1) : side;
        const anchor = base.clone().add(new THREE.Vector3(outX*(0.55+o.scale*0.6), 0.35+o.scale*0.4, 0));
        // 3D leader line (additive, faint)
        const geo=new THREE.BufferGeometry().setFromPoints([base, anchor]);
        const line=new THREE.Line(geo, new THREE.LineBasicMaterial({color:o.color,transparent:true,opacity:0.34,blending:THREE.AdditiveBlending,depthWrite:false}));
        root.add(line);
        // HTML label
        const div=document.createElement('div'); div.className='olabel';
        div.style.color = o.color;
        div.innerHTML = `${esc(o.quechua)}<span class="od">${esc((D.SYSTEMS.find(s=>s.key===o.system)||{}).name||o.system)}</span>`;
        div.addEventListener('click', ()=>openOrgan(o));
        div.style.pointerEvents='auto'; div.style.cursor='pointer';
        labelLayer.appendChild(div);
        labels.push({om, div, anchor, line});
      });
    }
    const _projV = new THREE.Vector3();
    function updateLabels(){
      if(!labelsOn){ return; }
      const w=innerWidth, h=innerHeight;
      labels.forEach(L=>{
        _projV.copy(L.anchor).project(camera);
        const behind = _projV.z>1;
        let x=( _projV.x*0.5+0.5)*w, y=(-_projV.y*0.5+0.5)*h;
        if(behind || x<-50 || x>w+50 || y<-50 || y>h+50){ L.div.classList.remove('show'); return; }
        const lw = L.div.offsetWidth || 120, lh = L.div.offsetHeight || 18, m = 8;
        // keep labels clear of the fixed side panels on wide screens: the title/
        // dissection dock occupy the left gutter and the honesty panel the right.
        const wide = w > 980;
        const leftBound = wide ? 320 : m;                 // clear left dock
        const rightBound = wide ? (w - 360) : (w - lw - m); // clear right honesty panel
        // hide labels that would land under a side panel rather than clip them
        if(wide && (x + lw > w - 360 || x < 320)){
          // nudge inward if it still fits the center band, else hide
          const nudged = Math.max(leftBound, Math.min(x, rightBound - lw));
          if(nudged < leftBound || nudged + lw > w - 360){ L.div.classList.remove('show'); return; }
          x = nudged;
        } else {
          x = Math.max(m, Math.min(x, w - lw - m));
        }
        y = Math.max(64, Math.min(y, h - lh - 88)); // clear top eyebrow + bottom controls
        L.div.style.left=x+'px'; L.div.style.top=y+'px'; L.div.classList.add('show');
      });
    }
    function setLabels(on){
      labelsOn=on;
      labelLayer.classList.toggle('off', !on);
      labels.forEach(L=>{ L.line.material.opacity = on?0.34:0.0; L.line.visible=on; });
      const b=el('btn-labels'); if(b){ b.classList.toggle('active',on); b.setAttribute('aria-pressed',String(on)); }
      if(!on) labels.forEach(L=>L.div.classList.remove('show'));
    }
    (function wireLabels(){ const b=el('btn-labels'); if(b) b.addEventListener('click', ()=>setLabels(!labelsOn)); })();

    /* ---- breathing Λ-heart idle synced to the receipt pulse ----
       Additive secondary modulation on top of the v3 lub-dub: a slow
       "breath" on the halo + a gentle scale wobble, gated by reduced-motion. ---- */
    let breathPhase=0;
    function breatheHeart(dt, beat){
      if(REDUCED_MOTION) return;
      breathPhase += dt*0.55; // ~5.5s breath cycle
      const breath = 0.5 + 0.5*Math.sin(breathPhase); // 0..1
      if(heartHalo){ heartHalo.material.opacity = clamp(heartHalo.material.opacity + breath*0.04, 0, 0.45); }
      if(heartGlow){ heartGlow.material.opacity = clamp(heartGlow.material.opacity + breath*0.05, 0, 0.95); }
      if(heartGroup){
        // tiny breath layered onto the v3 beat scale (never overrides it)
        const s = heartGroup.scale.x * (1 + breath*0.012);
        heartGroup.scale.setScalar(s);
      }
    }

    /* =====================================================================
       (C) GUIDED TOUR — fly organ-to-organ, narrate, auto-advance, pausable
       ===================================================================== */
    // tour route: a sensible anatomical walk through the distinct organs
    const TOUR = ['yuyay','amaru','yawar','ruway','sentra','huklla','vsp','hatun','overwatch','tukuy','musquy']
      .map(k=>D.ORGANS.find(o=>o.key===k)).filter(Boolean);
    const tourEl=el('tour');
    let tour = { on:false, i:0, paused:false, t:0, dwell: (REDUCED_MOTION?7.0:6.0) };
    function tourShow(o){
      const sys=(D.SYSTEMS.find(s=>s.key===o.system)||{}).name||o.system;
      el('tr-step').textContent = 'organ';
      el('tr-name').textContent = o.quechua;
      el('tr-prog').textContent = (tour.i+1)+' / '+TOUR.length;
      const fcount=(o.formulas||[]).length;
      el('tr-body').innerHTML = `<b style="color:${o.color}">${esc(sys)}</b> · ${esc(o.fn)}. `+
        `${esc(o.blurb).slice(0,180)}${o.blurb.length>180?'…':''} `+
        `<span style="color:var(--text-dim)">(${fcount} formula${fcount===1?'':'s'} instilled — open to inspect each.)</span>`;
      el('tr-bar-i').style.width='0%';
    }
    function tourGo(i){
      if(!TOUR.length) return;
      tour.i = (i+TOUR.length)%TOUR.length;
      tour.t = 0;
      const o=TOUR[tour.i];
      tourShow(o);
      openOrgan(o); // reuses v3 smooth framing + panel
    }
    function startTour(){
      if(!TOUR.length) return;
      tour.on=true; tour.paused=false;
      autoRotate=false; const rb=el('btn-rotate'); if(rb) rb.classList.remove('active');
      tourEl.classList.add('show');
      const b=el('btn-tour'); if(b){ b.classList.add('active'); b.setAttribute('aria-pressed','true'); }
      el('tr-pause').textContent='⏸ pause';
      tourGo(0);
    }
    function stopTour(){
      tour.on=false;
      tourEl.classList.remove('show');
      const b=el('btn-tour'); if(b){ b.classList.remove('active'); b.setAttribute('aria-pressed','false'); }
      closePanel();
    }
    function togglePause(){
      tour.paused=!tour.paused;
      el('tr-pause').textContent = tour.paused?'▶ resume':'⏸ pause';
    }
    function tourTick(dt){
      if(!tour.on || tour.paused) return;
      tour.t += dt;
      const frac = clamp(tour.t/tour.dwell,0,1);
      el('tr-bar-i').style.width = (frac*100).toFixed(0)+'%';
      if(tour.t>=tour.dwell){ tourGo(tour.i+1); }
    }
    (function wireTour(){
      const b=el('btn-tour'); if(b) b.addEventListener('click', ()=> tour.on?stopTour():startTour());
      el('tr-next').addEventListener('click', ()=>{ tour.t=0; tourGo(tour.i+1); });
      el('tr-prev').addEventListener('click', ()=>{ tour.t=0; tourGo(tour.i-1); });
      el('tr-pause').addEventListener('click', togglePause);
      el('tr-stop').addEventListener('click', stopTour);
    })();

    /* ---- build the 3D extras now that v4 has captured basePos ---- */
    buildLabels();
    setLabels(true);

    /* ---- per-frame tick, called from the SINGLE v3 render loop ---- */
    function tick(dt,t,beat){
      updateLabels();
      breatheHeart(dt, beat);
      tourTick(dt);
    }

    return {
      tick, onOrganOpen,
      openAtlas, closeAtlas, openForecast, closeForecast,
      startTour, stopTour, setLabels,
      atlasCounts: countByTier,
      _tour: tour,
      api: {
        atlasOpen:()=>atlas.classList.contains('open'),
        forecastOpen:()=>el('forecast').classList.contains('open'),
        tourOn:()=>tour.on,
        labels:()=>labels.length,
        tierCounts:()=>countByTier(),
        searchAtlas:(term)=>{ atlasQuery=term; if(!atlas.classList.contains('open'))openAtlas(); else renderAtlas(); return el('atlas-body').querySelectorAll('.formula').length; },
        filterAtlas:(tier)=>{ atlasFilter=tier; if(!atlas.classList.contains('open'))openAtlas(); else renderAtlas(); return el('atlas-body').querySelectorAll('.formula').length; }
      }
    };
  })();
  /* =========================  /v4-DEEPEN (v5)  ======================== */

  /* =====================================================================
     ====================  v6 · yarqa FLOW COMPARTMENTS  =================
     ADDITIVE overlay (NEVER replaces v3/v4/v5). Reuses the v3 scene, the
     `vessels` registry built from data.js (SINGLE source of truth — no new
     data), THREE r160 (vendored, zero-CDN), and the SAME render loop via
     V6.tick. Sovereign: no network, no new asset.

     What it does: it samples the EXISTING circulatory / YAWAR vessel curves
     into a velocity field (points + flow tangents), then runs a clean-room
     in-browser port of yarqa.compartmentalize — region-growing of
     velocity-aligned cells across a flow front — to reduce the circulatory
     flow to a small set of plug-flow compartments, rendered as a toggleable
     layer of compartment hulls + centroids over the flow.

     HONESTY (doctrine v11) — never violated:
       • yarqa is an ENGINEERING METHOD (CFD), NOT a locked theorem. It is
         NEVER folded into the locked-proven count (stays exactly 8
         {F1,F4,F7,F11,F12,F18,F19,F22} @ D.KERNEL.locked_sha). No proven /
         kernel-verified badge — the layer is labeled verbatim
         "yarqa flow compartments — engineering method (CFD)".
       • It does NOT route the locked-8 governance theorems "through" yarqa,
         and does NOT re-implement the a11oy↔killinchu connection on yarqa —
         it is a read-only VISUALIZATION over the existing circulatory flow.
       • Method clean-room (Jacobs et al. 1991 / reactor-engineering
         compartmental reduction cited as concept only); no third-party
         source copied.
     ===================================================================== */
  V6 = (function(){
    const CFD_LABEL = 'yarqa flow compartments \u2014 engineering method (CFD)';
    const PAL = [0x3fb6d6,0xe8b33f,0x46d39a,0xb06fe0,0xe8615f,0x5f8de8,0xe88f3f,0x6fe0c0,0xd65fb0,0x9ad63f];

    // ---- 1. Build the flow field from the EXISTING circulatory vessels ----
    // Circulatory = YAWAR receipt bus (vessel color '#ff3b5c'). We sample each
    // such vessel curve into cells: center = sample point, velocity = local
    // flow tangent (downstream direction along the bus). data.js is the source.
    function buildField(){
      const centers=[], velocities=[], cellVessel=[];
      const circ = vessels.filter(v=> v.color==='#ff3b5c');
      const SAMPLES = 7; // per vessel — keep cell count modest for the overlay
      circ.forEach((v,vi)=>{
        for(let s=0;s<SAMPLES;s++){
          const t = (s+0.5)/SAMPLES;
          const p = v.curve.getPoint(t);
          const tan = v.curve.getTangent(Math.min(0.999,t)).normalize();
          centers.push(p);
          velocities.push(tan);
          cellVessel.push(vi);
        }
      });
      // Face adjacency: consecutive samples on the same vessel are neighbors,
      // plus cross-links between cells from different vessels that are spatially
      // close (a shared flow front through the YAWAR mesh).
      const n = centers.length;
      const neighbors = Array.from({length:n},()=>[]);
      for(let i=0;i<n;i++){
        for(let j=i+1;j<n;j++){
          const sameVessel = cellVessel[i]===cellVessel[j];
          const seq = sameVessel && Math.abs((i-j))===1;
          const d = centers[i].distanceTo(centers[j]);
          if(seq || d<0.9){ neighbors[i].push(j); neighbors[j].push(i); }
        }
      }
      return { centers, velocities, neighbors, n };
    }

    // ---- 2. Clean-room yarqa.compartmentalize (region-grow) ----------------
    // Mirrors the published algorithm: deterministic seed order (fastest flow
    // first), grow through face-neighbors that are velocity-aligned AND straddle
    // the seed's flow front. Pure THREE.Vector3 math; no third-party source.
    function unit(v){ const l=v.length(); return l>1e-9? v.clone().multiplyScalar(1/l): v.clone(); }
    function straddles(uSeed, rSeed, rN){
      // Single representative point per neighbor (its center): a neighbor is on
      // the front if the projection sign differs from a tiny upstream probe.
      const rel = rN.clone().sub(rSeed);
      const proj = rel.dot(uSeed);
      // Front straddle test: admit neighbors near/across the front plane.
      return Math.abs(proj) <= 0.55 || proj>=0;
    }
    function compartmentalize(field, alignThreshold){
      const {centers,velocities,neighbors,n}=field;
      const labels = new Array(n).fill(-1);
      const speed = velocities.map(v=>v.length());
      const order = Array.from({length:n},(_,i)=>i).sort((a,b)=>speed[b]-speed[a]);
      let cur=0;
      for(const start of order){
        if(labels[start]!==-1) continue;
        const uSeed = velocities[start];
        const uSeedU = unit(uSeed);
        const rSeed = centers[start];
        labels[start]=cur;
        const frontier=[start];
        while(frontier.length){
          const cell=frontier.shift();
          for(const k of neighbors[cell]){
            if(labels[k]!==-1) continue;
            const uk=unit(velocities[k]);
            if(uSeedU.dot(uk) < alignThreshold) continue;
            if(!straddles(uSeed,rSeed,centers[k])) continue;
            labels[k]=cur; frontier.push(k);
          }
        }
        cur++;
      }
      return labels;
    }
    function summarize(field, labels){
      const groups={};
      for(let i=0;i<labels.length;i++){
        const c=labels[i]; (groups[c]||(groups[c]={n:0,cs:new THREE.Vector3(),mv:new THREE.Vector3()}));
        groups[c].n++; groups[c].cs.add(field.centers[i]); groups[c].mv.add(field.velocities[i]);
      }
      Object.keys(groups).forEach(c=>{ groups[c].cs.multiplyScalar(1/groups[c].n); groups[c].mv.multiplyScalar(1/groups[c].n); });
      return groups;
    }

    // ---- 3. Reproducible integrity receipt (mirrors yarqa.provenance) ------
    // SHA-256 over canonical (rounded) inputs + params + result. Pure WebCrypto.
    // Asserts INTEGRITY/REPRODUCIBILITY, NOT correctness, NOT a locked theorem.
    function canonicalField(field, alignThreshold){
      const r=x=>Math.round(x*1e4)/1e4;
      return JSON.stringify({
        schema:'szl.yarqa.receipt/v1-viz',
        claim_tier:'engineering-method-cfd; integrity-receipt; NOT a locked theorem',
        params:{align_threshold:alignThreshold},
        n:field.n,
        centers:field.centers.map(p=>[r(p.x),r(p.y),r(p.z)]),
        velocities:field.velocities.map(p=>[r(p.x),r(p.y),r(p.z)])
      });
    }
    async function sha256Hex(str){
      try{
        const buf=await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
        return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
      }catch(e){ // sovereign fallback: small deterministic non-crypto digest (labeled)
        let h=5381; for(let i=0;i<str.length;i++){ h=((h<<5)+h+str.charCodeAt(i))>>>0; }
        return 'fnv-'+h.toString(16);
      }
    }

    // ---- 4. Render group (toggleable, additive) ---------------------------
    const grp = new THREE.Group(); grp.name='yarqa-flow-compartments'; grp.visible=false; root.add(grp);
    let field=null, labels=null, groups=null, lastReceipt=null, currentOpacity=1, layerOn=false;

    function clearGrp(){ for(let i=grp.children.length-1;i>=0;i--){ const c=grp.children[i]; grp.remove(c); if(c.geometry)c.geometry.dispose(); if(c.material)c.material.dispose(); } }

    function render(){
      clearGrp();
      if(!field||!labels) return;
      // cell markers tinted by compartment
      for(let i=0;i<field.n;i++){
        const col=PAL[labels[i]%PAL.length];
        const m=new THREE.Mesh(new THREE.SphereGeometry(0.05,8,8),
          new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.9*currentOpacity}));
        m.position.copy(field.centers[i]); grp.add(m);
      }
      // compartment centroids + mean-flow arrows
      Object.keys(groups).forEach(c=>{
        const g=groups[c]; const col=PAL[(+c)%PAL.length];
        const node=new THREE.Mesh(new THREE.IcosahedronGeometry(0.14,0),
          new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.55*currentOpacity,wireframe:true}));
        node.position.copy(g.cs); grp.add(node);
        const dir=unit(g.mv); const len=0.6;
        const arrowGeo=new THREE.BufferGeometry().setFromPoints([g.cs, g.cs.clone().addScaledVector(dir,len)]);
        grp.add(new THREE.Line(arrowGeo, new THREE.LineBasicMaterial({color:col,transparent:true,opacity:0.8*currentOpacity})));
      });
    }

    async function recompute(alignThreshold){
      const aln = (alignThreshold==null)?0.2:alignThreshold;
      field = buildField();
      labels = compartmentalize(field, aln);
      groups = summarize(field, labels);
      const canon = canonicalField(field, aln);
      const resultStr = JSON.stringify(labels);
      const digest = await sha256Hex(canon + '|' + resultStr);
      lastReceipt = {
        schema:'szl.yarqa.receipt/v1-viz',
        method_tier:'engineering method (CFD)',
        claim:'integrity/reproducibility, NOT correctness; NOT a locked theorem',
        yarqa_in_locked_count:false,
        routes_locked8_through_yarqa:false,
        align_threshold:aln,
        n_cells:field.n,
        n_compartments:Object.keys(groups).length,
        receipt_digest:digest,
        source:'circulatory / YAWAR vessels (data.js single source of truth)'
      };
      render();
      updatePanel();
      return lastReceipt;
    }

    // ---- 5. Dock UI: a layer row + honest CFD panel (mobile-safe) ----------
    const el = id=>document.getElementById(id);
    function updatePanel(){
      const box=el('yq-receipt'); if(!box||!lastReceipt) return;
      box.textContent =
        lastReceipt.n_compartments+' compartments \u00b7 '+lastReceipt.n_cells+' cells \u00b7 align '+lastReceipt.align_threshold.toFixed(2)+
        '\nreceipt '+lastReceipt.receipt_digest.slice(0,32)+'\u2026';
    }
    function setLayer(on, op){
      if(on!=null){ layerOn=on; grp.visible=on; }
      if(op!=null){ currentOpacity=op; }
      grp.visible = layerOn;
      if(layerOn && (!labels)) { recompute(0.2); } else { render(); }
    }

    function buildDockRow(){
      const wrap=el('dz-layers'); if(!wrap) return;
      const sec=document.createElement('div'); sec.className='dz-layer'; sec.id='yq-layer-row';
      sec.innerHTML =
        '<button class="dz-toggle" id="yq-toggle" role="switch" aria-pressed="false" aria-label="yarqa flow compartments layer (engineering method, CFD)"></button>'+
        '<span class="lname"><span class="lsw" style="color:#3fb6d6"></span>yarqa flow compartments</span>'+
        '<input type="range" class="dz-range" id="yq-op" min="0" max="1" step="0.01" value="1" aria-label="yarqa flow compartments opacity">';
      wrap.appendChild(sec);
      // honest CFD note + receipt readout + align slider (sits under the row)
      const note=document.createElement('div'); note.className='dz-sec'; note.id='yq-sec';
      note.innerHTML =
        '<span class="dz-label">CFD method \u00b7 not a locked theorem</span>'+
        '<div style="font-size:11px;line-height:1.45;color:var(--audit);margin:2px 0 6px">'+
          'Plug-flow compartmentalization (<b>yarqa</b>) of the circulatory / YAWAR flow \u2014 an '+
          '<b>engineering method (CFD)</b>, <b>not</b> a locked theorem and never counted among the '+
          'locked 8. Read-only viz over the existing flow; data.js is the source.'+
        '</div>'+
        '<div class="dz-row"><span class="dz-label" style="flex:0 0 auto">align</span>'+
          '<input type="range" class="dz-range" id="yq-align" min="0" max="0.9" step="0.05" value="0.2" aria-label="yarqa alignment threshold" style="flex:1">'+
          '<span class="val" id="yq-align-val">0.20</span></div>'+
        '<pre id="yq-receipt" style="font-size:10.5px;white-space:pre-wrap;word-break:break-all;color:var(--nerve);margin:4px 0 0;background:rgba(0,0,0,.18);border-radius:6px;padding:6px">layer off \u2014 toggle to compute</pre>';
      // place the note section right after the layer-stack section
      const stack = wrap.parentNode; // dz-body
      if(stack && wrap.nextSibling){ stack.insertBefore(note, wrap.nextSibling); } else if(stack){ stack.appendChild(note); }

      const tog=el('yq-toggle'), op=el('yq-op'), align=el('yq-align'), alignVal=el('yq-align-val');
      tog.addEventListener('click', ()=>{ const on=tog.getAttribute('aria-pressed')!=='true'; tog.setAttribute('aria-pressed',String(on)); setLayer(on,null); if(on){ el('yq-receipt').textContent='computing\u2026'; recompute(parseFloat(align.value)); } });
      op.addEventListener('input', ()=>{ setLayer(null, parseFloat(op.value)); });
      align.addEventListener('input', ()=>{ alignVal.textContent=parseFloat(align.value).toFixed(2); if(layerOn) recompute(parseFloat(align.value)); });
    }
    buildDockRow();

    // gentle idle shimmer on the compartment nodes (respects reduced motion)
    let acc=0;
    function tick(dt,t){
      if(!layerOn || REDUCED_MOTION) return;
      acc+=dt; if(acc<0.05) return; acc=0;
      grp.children.forEach(c=>{ if(c.material && c.material.wireframe){ c.material.opacity = (0.4+0.2*Math.sin(t*1.5))*currentOpacity; } });
    }

    return {
      tick, recompute, setLayer,
      label: CFD_LABEL,
      isOn: ()=>layerOn,
      compartments: ()=> labels? Object.keys(groups).length : 0,
      cells: ()=> field? field.n : 0,
      receipt: ()=> lastReceipt,
      yarqaInLockedCount: ()=> false,
      routesLocked8ThroughYarqa: ()=> false
    };
  })();
  /* =====================  /v6 yarqa flow compartments  ================= */

  /* ---------------- test hooks for headless QA ---------------- */
  window.__anatomy = {
    organs: organMeshes.length,
    vessels: vessels.length,
    pulses: pulses.length,
    heart: !!heartGroup,
    bodies: D.BODIES.map(b=>b.key),
    openOrgan: key=>{ const o=D.ORGANS.find(x=>x.key===key); if(o){openOrgan(o);return true;} return false; },
    openGPD: ()=>{ openGPD(); return true; },
    panelOpen: ()=>panel.classList.contains('open'),
    rev: (window.THREE&&THREE.REVISION)||null,
    v4: V4,  // v4 dissection module handle (layers, clip, explode, search, hud, focus)
    v5: V5,  // v4-deepen module handle (atlas, forecast, tour, labels, drill-down)
    v6: V6,  // v6 yarqa flow-compartments layer (engineering method / CFD, NOT a locked theorem)
    formulas: Object.keys(D.FORMULAS).length,
    tierCounts: (V5&&V5.api)?V5.api.tierCounts():null
  };
})();
