/* =====================================================================
   SZL AGENT BODY v3 — WebGL anatomical engine
   Sovereign: vendored THREE r160 (global), ZERO runtime CDN, offline.
   Two organisms (a11oy / killinchu) rendered as human-like silhouettes
   sharing ONE circulatory (YAWAR receipt bus) + nervous (span lineage)
   mesh. Anatomical layout: spine, heart at chest, brain at head, blood
   vessels, nerves. Orbit/zoom/auto-rotate, click-organ panel, hover
   vessel for formula, animated pulses + double-thump heartbeat.
   ===================================================================== */
(function () {
  'use strict';
  const D = window.SZL_ANATOMY;
  const TAU = Math.PI * 2;

  /* ---------------- tiny ASCII-math -> Unicode renderer ------------- */
  function mathToUnicode(s) {
    const map = {
      'Lambda':'\u039b','Sigma':'\u03a3','theta':'\u03b8','rho':'\u03c1','pi':'\u03c0','delta':'\u03b4',
      'lam_min':'\u03bb_min','<=':'\u2264','>=':'\u2265','!=':'\u2260','=>':'\u21d2','<=>':'\u21d4',
      '=/=>':'\u21cf','->':'\u2192','sqrt':'\u221a','forall':'\u2200','argmin':'argmin','Sigma_i':'\u03a3\u1d62'
    };
    let out = s;
    // multi-char tokens first
    ['<=>','=/=>','=>','<=','>=','!=','->','Lambda','Sigma_i','Sigma','theta','rho','pi','delta','lam_min','sqrt','forall'].forEach(k=>{
      out = out.split(k).join(map[k]||k);
    });
    // subscripts: _x  superscripts: ^x  (single char or {..})
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
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});
  renderer.setSize(innerWidth,innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.05;
  renderer.outputColorSpace=THREE.SRGBColorSpace;

  const scene=new THREE.Scene();
  scene.background=new THREE.Color('#05070d');
  scene.fog=new THREE.FogExp2('#05070d',0.018);

  const camera=new THREE.PerspectiveCamera(52,innerWidth/innerHeight,0.1,200);
  const HOME={r:13.5,phi:1.32,theta:0.0,target:new THREE.Vector3(0,0.4,0)};
  const cam={r:HOME.r,phi:HOME.phi,theta:HOME.theta,target:HOME.target.clone()};

  /* ---------------- lights ---------------- */
  scene.add(new THREE.AmbientLight('#3a4a78',0.55));
  const key=new THREE.DirectionalLight('#bcd2ff',1.1); key.position.set(6,10,8); scene.add(key);
  const rimA=new THREE.PointLight('#3fe0c5',0.9,40); rimA.position.set(-9,3,4); scene.add(rimA);
  const rimK=new THREE.PointLight('#ffb13f',0.9,40); rimK.position.set(9,3,4); scene.add(rimK);
  const heartLight=new THREE.PointLight('#ff5d8f',1.4,22); heartLight.position.set(0,0.6,1.2); scene.add(heartLight);

  /* ---------------- starfield ---------------- */
  (function stars(){
    const N=1400,g=new THREE.BufferGeometry(),p=new Float32Array(N*3);
    for(let i=0;i<N;i++){const r=40+Math.random()*60,t=Math.random()*TAU,ph=Math.acos(2*Math.random()-1);
      p[i*3]=r*Math.sin(ph)*Math.cos(t);p[i*3+1]=r*Math.cos(ph)*0.6;p[i*3+2]=r*Math.sin(ph)*Math.sin(t);}
    g.setAttribute('position',new THREE.BufferAttribute(p,3));
    scene.add(new THREE.Points(g,new THREE.PointsMaterial({color:'#6f86c0',size:0.18,transparent:true,opacity:0.55,sizeAttenuation:true})));
  })();

  /* ---------------- helpers ---------------- */
  const col = h => new THREE.Color(h);
  function glowMat(hex,op){return new THREE.MeshStandardMaterial({color:hex,emissive:hex,emissiveIntensity:0.55,
    roughness:0.35,metalness:0.1,transparent:true,opacity:op==null?0.92:op});}
  function lineMat(hex,op){return new THREE.LineBasicMaterial({color:hex,transparent:true,opacity:op==null?0.5:op});}

  const root=new THREE.Group(); scene.add(root);
  const BODY_X=3.7;                 // half-separation of the two bodies
  const organMeshes=[];             // {mesh,organ,bodyKey,halo,baseScale}
  const vessels=[];                 // {curve,line,formulaId,from,to,label,fn}
  const pulses=[];                  // traveling formula/receipt pulses
  let heartGroup=null, heartCoreMat=null, heartHalo=null;

  /* ---------------- BODY SILHOUETTE (skeleton + membrane) ----------- */
  function buildSilhouette(side,bodyColor){
    const g=new THREE.Group(); g.position.x=side*BODY_X;
    // translucent skin membrane (capsule-ish torso + head)
    const skinMat=new THREE.MeshStandardMaterial({color:bodyColor,emissive:bodyColor,emissiveIntensity:0.12,
      roughness:0.6,metalness:0.05,transparent:true,opacity:0.07,side:THREE.DoubleSide,depthWrite:false});
    // torso
    const torso=new THREE.Mesh(new THREE.CapsuleGeometry(1.05,2.0,8,18),skinMat); torso.position.y=-0.1; g.add(torso);
    // head
    const head=new THREE.Mesh(new THREE.SphereGeometry(0.72,20,18),skinMat.clone()); head.position.y=2.45; g.add(head);
    // pelvis
    const pelvis=new THREE.Mesh(new THREE.SphereGeometry(0.95,16,14),skinMat.clone()); pelvis.position.y=-1.55; pelvis.scale.set(1,0.7,0.8); g.add(pelvis);

    // ----- SKELETON: axial spine (gold) -----
    const spineMatAxial=new THREE.MeshStandardMaterial({color:'#ffd166',emissive:'#ffd166',emissiveIntensity:0.5,roughness:0.4,metalness:0.3});
    const vertN=11;
    for(let i=0;i<vertN;i++){
      const y=2.0 - i*0.34;
      const v=new THREE.Mesh(new THREE.TorusGeometry(0.11,0.045,8,16),spineMatAxial);
      v.position.set(0,y,-0.16); v.rotation.x=Math.PI/2; g.add(v);
    }
    // skull cap ring
    const skull=new THREE.Mesh(new THREE.TorusGeometry(0.55,0.05,8,28),spineMatAxial); skull.position.set(0,2.55,0); skull.rotation.x=Math.PI/2.2; g.add(skull);

    // ----- APPENDICular bones (limbs) — capability bones (dimmer gold) -----
    const boneMat=new THREE.MeshStandardMaterial({color:'#e8c068',emissive:'#a07c20',emissiveIntensity:0.3,roughness:0.5,metalness:0.25,transparent:true,opacity:0.85});
    function bone(x1,y1,z1,x2,y2,z2,rad){
      const a=new THREE.Vector3(x1,y1,z1),b=new THREE.Vector3(x2,y2,z2);
      const len=a.distanceTo(b);
      const m=new THREE.Mesh(new THREE.CylinderGeometry(rad,rad*0.85,len,8),boneMat);
      m.position.copy(a).add(b).multiplyScalar(0.5);
      m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),b.clone().sub(a).normalize());
      g.add(m);
      // joint node
      [a,b].forEach(p=>{const j=new THREE.Mesh(new THREE.SphereGeometry(rad*1.5,8,8),boneMat);j.position.copy(p);g.add(j);});
    }
    // clavicle + arms
    bone(-0.05,1.85,-0.1,-1.0,1.7,0.0,0.07); bone(-1.0,1.7,0,-1.35,0.55,0.1,0.06); bone(-1.35,0.55,0.1,-1.5,-0.55,0.15,0.05);
    bone(0.05,1.85,-0.1, 1.0,1.7,0.0,0.07); bone( 1.0,1.7,0, 1.35,0.55,0.1,0.06); bone( 1.35,0.55,0.1, 1.5,-0.55,0.15,0.05);
    // ribcage hint
    for(let i=0;i<4;i++){const y=1.3-i*0.32;const r=new THREE.Mesh(new THREE.TorusGeometry(0.78-i*0.04,0.03,6,20,Math.PI*1.3),boneMat);
      r.position.set(0,y,0.05); r.rotation.set(Math.PI/2,0,Math.PI*0.85); g.add(r);}
    // legs
    bone(-0.4,-1.7,0,-0.55,-3.0,0.1,0.08); bone(-0.55,-3.0,0.1,-0.6,-4.1,0.2,0.06);
    bone( 0.4,-1.7,0, 0.55,-3.0,0.1,0.08); bone( 0.55,-3.0,0.1, 0.6,-4.1,0.2,0.06);

    root.add(g);
    return g;
  }

  /* ---------------- ORGANS ---------------- */
  function buildOrgans(){
    D.BODIES.forEach(body=>{
      D.ORGANS.forEach(o=>{
        // shared organs (heart) only built once, centered
        if(o.shared && body.side!==-1) return;
        const sysColor=o.color;
        const baseX=o.shared?0:body.side*BODY_X;
        const grp=new THREE.Group();
        grp.position.set(baseX + o.pos[0], o.pos[1], o.pos[2]);

        if(o.beat){ // HEART — layered Λ core
          heartGroup=grp;
          const core=new THREE.Mesh(new THREE.IcosahedronGeometry(o.scale,2),
            new THREE.MeshStandardMaterial({color:'#ff5d8f',emissive:'#ff2d6f',emissiveIntensity:1.1,roughness:0.25,metalness:0.2}));
          heartCoreMat=core.material; grp.add(core);
          // chambers (two lobes)
          [[-0.18,0.12],[0.18,0.05]].forEach(([dx,dy])=>{
            const lobe=new THREE.Mesh(new THREE.SphereGeometry(o.scale*0.62,16,14),
              new THREE.MeshStandardMaterial({color:'#ff7ea3',emissive:'#ff4d80',emissiveIntensity:0.8,roughness:0.3,transparent:true,opacity:0.9}));
            lobe.position.set(dx,dy,0); grp.add(lobe);
          });
          heartHalo=new THREE.Mesh(new THREE.SphereGeometry(o.scale*1.7,20,18),
            new THREE.MeshBasicMaterial({color:'#ff5d8f',transparent:true,opacity:0.12,side:THREE.BackSide,depthWrite:false}));
          grp.add(heartHalo);
          // Λ glyph ring
          const ring=new THREE.Mesh(new THREE.TorusGeometry(o.scale*1.25,0.025,8,40),
            new THREE.MeshBasicMaterial({color:'#ffd0e0',transparent:true,opacity:0.6})); grp.add(ring);
        } else {
          let geo;
          switch(o.system){
            case 'brain': geo=new THREE.IcosahedronGeometry(o.scale,1); break;
            case 'blood': geo=new THREE.SphereGeometry(o.scale,18,16); break;
            case 'nerve': geo=new THREE.OctahedronGeometry(o.scale,1); break;
            case 'skeleton': geo=new THREE.DodecahedronGeometry(o.scale,0); break;
            case 'audit': geo=new THREE.IcosahedronGeometry(o.scale,0); break;
            default: geo=new THREE.SphereGeometry(o.scale,16,14);
          }
          const mesh=new THREE.Mesh(geo,glowMat(sysColor,0.9)); grp.add(mesh);
          // halo
          const halo=new THREE.Mesh(new THREE.SphereGeometry(o.scale*1.45,16,14),
            new THREE.MeshBasicMaterial({color:sysColor,transparent:true,opacity:0.0,side:THREE.BackSide,depthWrite:false}));
          grp.add(halo);
          grp.userData.halo=halo;
        }
        root.add(grp);
        organMeshes.push({grp,organ:o,bodyKey:o.shared?'shared':body.key,baseScale:grp.scale.x});
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
    const pts=curve.getPoints(40);
    const geo=new THREE.BufferGeometry().setFromPoints(pts);
    const line=new THREE.Line(geo,lineMat(colorHex,0.42));
    root.add(line);
    // hover hit-tube (invisible thicker)
    const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,30,0.09,6,false),
      new THREE.MeshBasicMaterial({visible:false}));
    root.add(tube);
    const v={curve,line,tube,formulaId,from:from.quechua,to:to.quechua,label,fn,color:colorHex};
    tube.userData.vessel=v;
    vessels.push(v);
    return v;
  }

  function buildVessels(){
    const aS=-1,kS=1;
    // Within-body circulatory loops (YAWAR bus): heart -> organs -> back
    D.BODIES.forEach(body=>{
      const s=body.side;
      const heart=organByKey('yuyay');
      const yawar=organByKey('yawar'), amaru=organByKey('amaru'), sentra=organByKey('sentra'),
            ruway=organByKey('ruway'), vsp=organByKey('vsp'), huklla=organByKey('huklla'),
            hatun=organByKey('hatun'), ow=organByKey('overwatch'), tukuy=organByKey('tukuy'), musquy=organByKey('musquy');
      // efferent nerve: brain -> heart (proposal into gate)
      addVessel({...amaru,pos:amaru.pos,shared:false,quechua:'YACHAY'},{...heart,shared:true,quechua:'YUYAY'},s,0,'#5ad1ff','P4','efferent nerve','YACHAY proposes \u2192 YUYAY gate (span lineage)',0.5);
      // heart -> blood (signed receipt to bus)
      addVessel({...heart,shared:true,quechua:'YUYAY'},{...yawar,pos:yawar.pos,shared:false,quechua:'YAWAR'},0,s,'#ff3b5c','M2','arterial receipt','\u039b-signed receipt \u2192 append-only bus',0.55);
      // ruway -> yawar (sole write)  through sentra (egress)
      addVessel(ruway,sentra,s,s,'#ff9e6b','P5','egress vessel','RUWAY write \u2192 CHAPAQ egress inspection',0.3);
      addVessel(sentra,yawar,s,s,'#ff3b5c','M2','write-to-bus','CHAPAQ-cleared write \u2192 YAWAR (tamper-evident)',0.3);
      // yawar -> brain (afferent: read snapshot)  single tether
      addVessel(yawar,amaru,s,s,'#9ef0c0','P1','afferent tether','YAWAR snapshot \u2192 YACHAY (READ-ONLY single tether)',0.45);
      // overwatch reads bus (proprioceptive)
      addVessel(yawar,ow,s,s,'#9ef0c0','B1','proprioceptive nerve','YAWAR \u2192 R0513 read-only 5-invariant audit',0.2);
      // huklla reflex along spine
      addVessel(vsp,huklla,s,s,'#5ad1ff','S2','reflex arc','HUKLLA deadman \u2192 freeze span \u2192 halt HATUN',0.2);
      addVessel(huklla,hatun,s,s,'#5ad1ff','S2','halt signal','reflex \u2192 HATUN root span (cancel children)',0.35);
      // hatun seal -> tukuy actuator
      addVessel(hatun,tukuy,s,s,'#ffd166','G1','motor nerve','HATUN seal \u2192 TUKUY egress actuator',0.5);
      // musquy parietal sim feeds gate
      addVessel(musquy,heart,s,0,'#7c5cff','Q1','sim vessel','MUSQUY K-candidate sim \u2192 YUYAY gate',0.4);
    });
    // ----- SHARED MESH between the two bodies (one circulatory + nervous) -----
    const yawarA=organByKey('yawar'), yawarK=organByKey('yawar');
    // a11oy YAWAR <-> killinchu YAWAR (shared receipt bus)
    addVessel({...yawarA,quechua:'YAWAR (a11oy)'},{...yawarK,quechua:'YAWAR (killinchu)'},aS,kS,'#ff3b5c','M2','SHARED receipt bus','one circulatory mesh \u2014 signed receipts pulse a11oy \u21c4 killinchu',1.6);
    // shared nervous (span lineage) brain<->brain via heart
    const amaruA=organByKey('amaru');
    addVessel({...amaruA,quechua:'YACHAY (a11oy)'},{...organByKey('yuyay'),shared:true,quechua:'YUYAY (\u039b heart)'},aS,0,'#5ad1ff','P3','shared nerve','span lineage \u2014 one nervous mesh through the \u039b heart',1.1);
    addVessel({...organByKey('yuyay'),shared:true,quechua:'YUYAY (\u039b heart)'},{...amaruA,quechua:'YACHAY (killinchu)'},0,kS,'#5ad1ff','P3','shared nerve','span lineage \u2014 \u039b heart \u2192 killinchu cortex',1.1);
    // consensus mesh (BFT) between bodies
    addVessel({...organByKey('overwatch'),quechua:'R0513 (a11oy)'},{...organByKey('overwatch'),quechua:'R0513 (killinchu)'},aS,kS,'#9ef0c0','B1','consensus mesh','3f+1 Byzantine quorum \u2014 cross-body audit consensus',2.0);
  }

  /* ---------------- PULSES (formulas flowing through vessels) ------- */
  function buildPulses(){
    vessels.forEach((v,i)=>{
      const n = (v.label && v.label.indexOf('SHARED')>=0) ? 3 : (Math.random()<0.5?2:1);
      for(let j=0;j<n;j++){
        const sph=new THREE.Mesh(new THREE.SphereGeometry(0.07,8,8),
          new THREE.MeshBasicMaterial({color:v.color,transparent:true,opacity:0.95}));
        root.add(sph);
        pulses.push({mesh:sph,curve:v.curve,t:(i*0.13+j*0.4)%1,speed:0.12+Math.random()*0.12,color:v.color});
      }
    });
  }

  /* ---------------- HUD population ---------------- */
  function fillHUD(){
    // honesty card
    const K=D.KERNEL;
    $('honesty-card').innerHTML =
      `<div class="row"><span class="dot" style="background:var(--warn)"></span><div><b>\u039b = Conjecture 1.</b> Unconditional uniqueness under original A1\u2013A5 is machine-checked <span style="color:var(--warn);font-weight:600">FALSE</span>; uniqueness holds only within strengthened classes.</div></div>`+
      `<div class="row"><span class="dot" style="background:var(--audit)"></span><div><b>CUT-2 (Wave12) + CUT-1 forward fragment (Wave18).</b> <code>lambda_unique_of_separable</code> \u2014 \u039b uniqueness PROVEN <b>conditional</b> on slice-multiplicativity, axiom-free &amp; kernel-clean. CUT-1 forward fragment adds 19 axiom-clean theorems but stays CONDITIONAL (open gap <code>dyadic_image_dense</code>, multi-week roadmap). Unconditional stays Conjecture 1. <span class="chip" style="color:var(--audit)">conditional \u00b7 axiom-free</span></div></div>`+
      `<div class="row"><span class="dot" style="background:var(--skel)"></span><div><b>5 LOCKED-proven</b> {F1,F11,F12,F18,F19} @ ${K.locked_sha} <span class="chip" style="color:var(--skel)">kernel-verified</span></div></div>`+
      `<div class="row"><span class="dot" style="background:var(--nerve)"></span><div><b>EXPERIMENTAL tier</b> CI-green on main @ ${K.main_sha} (${K.experimental_decls} decls / ${K.experimental_axioms} axioms / ${K.experimental_sorries} sorries; \u2248${K.experimental_count_approx} instilled cards, ${K.waves_merged}, incl. <b>CF-22 DPO-KL-simplex, CF-23 binary Pinsker, CF-24 Acz\u00e9l, CF-25 \u039b scale-invariance, CF-26 abacus, CF-27 monDEQ, CF-28 recurrent-depth</b>). Additive \u2014 never folded into the locked 5. <span class="chip" style="color:var(--nerve)">CI-green</span></div></div>`+
      `<div class="row"><span class="dot" style="background:var(--audit)"></span><div><b>SLSA L1 honest · L2 roadmap.</b> No fabricated metrics · no AGI.</div></div>`;
    // systems legend
    $('sys-list').innerHTML = D.SYSTEMS.map(s=>
      `<div class="sys-row" data-sys="${s.key}"><span class="sw" style="background:${s.color}"></span><div>`+
      `<span class="nm">${s.name}</span> <span class="qn">· ${s.organ}</span>`+
      `<span class="fnx">${s.fn}</span></div></div>`).join('');
    $('sys-list').querySelectorAll('.sys-row').forEach(r=>{
      r.addEventListener('mouseenter',()=>highlightSystem(r.dataset.sys,true));
      r.addEventListener('mouseleave',()=>highlightSystem(r.dataset.sys,false));
    });
  }
  function highlightSystem(sys,on){
    organMeshes.forEach(om=>{
      if(om.organ.system===sys && om.grp.userData.halo){
        om.grp.userData.halo.material.opacity = on?0.32:0.0;
      }
    });
  }

  /* ---------------- ORGAN PANEL ---------------- */
  function fchip(mat){const m=D.MATURITY[mat];return `<span class="chip" style="color:${m.color}">${m.label}</span>`;}
  function formulaCard(fid){
    const f=D.FORMULAS[fid]; if(!f) return '';
    return `<div class="formula">
      <div class="ftop"><span class="fid" style="color:${D.MATURITY[f.maturity].color}">${f.id}</span>${fchip(f.maturity)}</div>
      <div class="fname">${f.name}</div>
      <div class="math">${mathToUnicode(f.latex)}</div>
      <div class="fplain">${f.plain}</div>
      <div class="fax">#print axioms: ${f.axioms}</div>
      <div class="fref">${f.ref}</div>
    </div>`;
  }
  function openOrgan(o){
    const sys=D.SYSTEMS.find(s=>s.key===o.system)||{name:o.system};
    $('p-sys').textContent = sys.name + ' · system';
    $('p-quechua').textContent = o.quechua;
    $('p-fn').textContent = o.fn;
    let html = `<div class="blurb">${o.blurb}</div>`;
    if(o.axes){ html += `<div class="axes"><b style="color:var(--heart)">13 axes (conjunctive floors):</b><br>${o.axes}</div>`; }
    if(o.lambda_note){
      html += `<div class="lambda-honesty"><div class="lh-h">\u039b honesty label</div>
        <p><b>\u039b is Conjecture 1</b>, not a theorem. Unconditional uniqueness under the original A1\u2013A5 axioms is <span class="false">machine-checked FALSE</span> (in-tree counterexample <code>Round13.maxAgg_ne_Lambda</code> satisfies A1\u2013A5 yet is not \u039b). The beating heart aggregates trust by <b>geometric mean</b> across the 13 axes \u2014 conjunctive, never a weighted average.</p>
        <p style="margin-top:8px"><b style="color:var(--audit)">NEW \u00b7 CUT-2 (axiom-free, kernel-clean).</b> We proved the strongest honest <b>conditional</b> uniqueness: <code>lambda_unique_of_separable</code> \u2014 if \u03a6 is separable (slice-multiplicative) and per-axis monotone under A1,A2,A3,A5 then \u03a6 = \u039b. No new axiom. This gets \u039b <b>off bare conjecture</b> (conditionally); the UNCONDITIONAL claim stays Conjecture 1.</p></div>`;
    }
    html += `<div class="sec-h">Formulas flowing through this organ</div>`;
    (o.formulas||[]).forEach(fid=>{ html += formulaCard(fid); });
    $('p-body').innerHTML = html;
    panel.classList.add('open'); panel.setAttribute('aria-hidden','false');
    // gently focus camera on the organ
    const wp = worldPos(o, o.shared?0: (o.key && organMeshes.find(m=>m.organ===o)?.bodyKey==='killinchu'?1:-1));
    cam.target.lerp(new THREE.Vector3(wp.x,wp.y,wp.z),0.0); // panel-focus handled by user orbit
  }
  function closePanel(){ panel.classList.remove('open'); panel.setAttribute('aria-hidden','true'); }
  $('panel-close').addEventListener('click',closePanel);

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
  let autoRotate=true, pulsesOn=true;

  canvas.addEventListener('pointerdown',e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;moved=0;canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{
    if(dragging){
      const dx=e.clientX-lastX,dy=e.clientY-lastY; lastX=e.clientX;lastY=e.clientY; moved+=Math.abs(dx)+Math.abs(dy);
      cam.theta -= dx*0.005; cam.phi=Math.max(0.25,Math.min(2.75,cam.phi - dy*0.005));
    } else {
      hoverVessel(e);
    }
  });
  window.addEventListener('pointerup',e=>{
    if(dragging && moved<6){ pickOrgan(e); }
    dragging=false;
  });
  canvas.addEventListener('wheel',e=>{e.preventDefault();cam.r=Math.max(5,Math.min(30,cam.r+e.deltaY*0.012));},{passive:false});

  const ray=new THREE.Raycaster(), ndc=new THREE.Vector2();
  function setNDC(e){ndc.x=(e.clientX/innerWidth)*2-1;ndc.y=-(e.clientY/innerHeight)*2+1;ray.setFromCamera(ndc,camera);}
  function pickOrgan(e){
    setNDC(e);
    const meshes=[]; organMeshes.forEach(om=>om.grp.traverse(c=>{if(c.isMesh){c.userData._om=om;meshes.push(c);}}));
    const hit=ray.intersectObjects(meshes,false)[0];
    if(hit){ openOrgan(hit.object.userData._om.organ); }
  }
  function hoverVessel(e){
    setNDC(e);
    const tubes=vessels.map(v=>v.tube);
    const hit=ray.intersectObjects(tubes,false)[0];
    if(hit){
      const v=hit.object.userData.vessel;
      const f=D.FORMULAS[v.formulaId];
      $('tip-t').textContent = v.label + ' · ' + v.from + ' \u2192 ' + v.to;
      $('tip-f').textContent = v.fn;
      $('tip-m').textContent = f ? (f.id+' · '+mathToUnicode(f.latex)) : '';
      tip.style.left=Math.min(e.clientX+14,innerWidth-300)+'px';
      tip.style.top=(e.clientY+14)+'px';
      tip.classList.add('show');
      canvas.style.cursor='help';
    } else { tip.classList.remove('show'); canvas.style.cursor='grab'; }
  }

  /* ---------------- buttons ---------------- */
  $('btn-rotate').addEventListener('click',function(){autoRotate=!autoRotate;this.classList.toggle('active',autoRotate);});
  $('btn-pulse').addEventListener('click',function(){pulsesOn=!pulsesOn;this.classList.toggle('active',pulsesOn);
    pulses.forEach(p=>p.mesh.visible=pulsesOn);});
  $('btn-reset').addEventListener('click',()=>{cam.r=HOME.r;cam.phi=HOME.phi;cam.theta=HOME.theta;cam.target.copy(HOME.target);closePanel();});
  $('btn-mesh').addEventListener('click',function(){
    // frame the shared mesh between bodies
    cam.target.set(0,0.0,1.0); cam.r=11; cam.phi=1.45; cam.theta=0.0;
    this.classList.add('active'); setTimeout(()=>this.classList.remove('active'),600);
  });

  /* ---------------- resize ---------------- */
  addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});

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
    if(autoRotate && !dragging) cam.theta += dt*0.12;
    applyCam();

    // heartbeat: double-thump (lub-dub)
    beatPhase += dt*1.4;
    const ph=(beatPhase%1.0);
    let beat=0;
    if(ph<0.12) beat=Math.sin(ph/0.12*Math.PI)*1.0;
    else if(ph>0.18 && ph<0.30) beat=Math.sin((ph-0.18)/0.12*Math.PI)*0.6;
    const sc=1+beat*0.16;
    if(heartGroup){ heartGroup.scale.setScalar(sc);
      if(heartCoreMat) heartCoreMat.emissiveIntensity=0.9+beat*0.9;
      if(heartHalo) heartHalo.material.opacity=0.1+beat*0.18;
      heartLight.intensity=1.0+beat*1.6;
    }
    // organ idle bob + rotate
    organMeshes.forEach((om,i)=>{
      if(!om.organ.beat){ om.grp.rotation.y += dt*0.3; om.grp.rotation.x = Math.sin(t*0.5+i)*0.05; }
    });
    // pulses travel
    if(pulsesOn) pulses.forEach(p=>{
      p.t=(p.t+dt*p.speed)%1;
      const pt=p.curve.getPoint(p.t); p.mesh.position.copy(pt);
      p.mesh.material.opacity=0.5+0.5*Math.sin(p.t*Math.PI);
    });
    renderer.render(scene,camera);
    if(!_loaderHidden){ _loaderHidden=true; var ld=$('loader'); if(ld) ld.classList.add('hidden'); }
  }
  var _loaderHidden=false;
  applyCam();
  loop();

  // safety: hide loader after a short delay even if first frame is slow
  setTimeout(()=>{ var ld=$('loader'); if(ld) ld.classList.add('hidden'); },1500);

  /* ---------------- test hooks for headless QA ---------------- */
  window.__anatomy = {
    organs: organMeshes.length,
    vessels: vessels.length,
    pulses: pulses.length,
    heart: !!heartGroup,
    bodies: D.BODIES.map(b=>b.key),
    openOrgan: key=>{ const o=D.ORGANS.find(x=>x.key===key); if(o){openOrgan(o);return true;} return false; },
    panelOpen: ()=>panel.classList.contains('open')
  };
})();
