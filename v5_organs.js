/* =====================================================================
   v5_organs.js — v5 (EVOLVES v4) additive overlays for the Living Anatomy.

   Self-contained, vendored-free, 0-CDN. Reads only the SZL a11oy origin
   (in the page CSP connect-src allow-list), READ-ONLY, credentials omitted.
   Adds, all honestly labeled (LIVE / MEASURED / MODELED / SAMPLE / ROADMAP):

     1. WILLAY  — conscience / immune-gate: 5 inspectable signed-refusal
        classifiers (trust ceiling 0.97). Tamper-EVIDENT, not tamper-proof.
     2. SOVEREIGN MESH — circulatory upgrade: live per-node up/DOWN from
        /govern/health. A node that is offline reads DOWN — never a
        fabricated green light. VRAM-fusion is ROADMAP.
     3. Buyer-verifiable receipt in-scene — "Verify offline" reuses Tier-1
        WebCrypto ECDSA-P256 against /cosign.pub, plus a live ledger
        bloodstream counter (total_receipts + sha3_256 chain head).
     4. 8 locked-proven → organ map (verbatim Lean statement + #print axioms,
        "kernel-verified sorry-free @ c7c0ba17"). Λ = heart-gate, advisory,
        Conjecture 1. Khipu BFT = Conjecture 2.
     5. AI-Assurance (WDP/CDAO) overlay — organ → assurance artifact with
        honest LIVE / PARTIAL / ROADMAP status chips.
     6. yarqa CFD + thermal-PINN physics layer — composed "physics-governed"
        overlay, labeled MODELED (not measured), bounded error.
     7. GPU-Sovereign Stack (SUBSTRATE) — the VERTICAL compute anatomy:
        owned GPU fabric → runtime → sovereign mesh → open-weight model →
        native governance → buyer-verifiable receipts. Live layers read
        /govern/health and degrade to DOWN, never a fabricated green light.

   Doctrine v11 LOCKED is unchanged: locked-proven stays EXACTLY 8; Λ is
   never a theorem; nothing here is folded into the locked-8.
   ===================================================================== */
(function(root){
  'use strict';
  if(!root.SZL_ANATOMY) return;
  var D = root.SZL_ANATOMY;
  var EP = D.V5_ENDPOINTS || {};

  /* ---------------- small DOM + fetch helpers ---------------- */
  function el(tag, attrs, html){ var e=document.createElement(tag); if(attrs){for(var k in attrs){ if(k==='class')e.className=attrs[k]; else e.setAttribute(k,attrs[k]); }} if(html!=null)e.innerHTML=html; return e; }
  function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
  function getJSON(url){ return fetch(url,{mode:'cors',credentials:'omit',cache:'no-store'}).then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); }); }
  function getText(url){ return fetch(url,{mode:'cors',credentials:'omit',cache:'no-store'}).then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.text(); }); }

  /* ---------------- styles (theme-consistent, inline-CSP-allowed) ---------------- */
  var css = [
    '#v5panel{position:fixed;z-index:41;top:0;left:0;height:100%;width:min(440px,94vw);background:linear-gradient(180deg,rgba(10,14,26,.99),rgba(6,9,16,.98));border-right:1px solid var(--border,rgba(255,255,255,.1));box-shadow:8px 0 40px rgba(0,0,0,.5);transform:translateX(-102%);transition:transform .32s cubic-bezier(.2,.7,.2,1);display:flex;flex-direction:column;pointer-events:auto}',
    '#v5panel.open{transform:translateX(0)}',
    '#v5panel .v5ph{padding:20px 22px 14px;border-bottom:1px solid var(--border,rgba(255,255,255,.1));position:sticky;top:0;background:rgba(8,11,20,.96)}',
    '#v5panel .v5ph .eyebrow{font-family:var(--font-m,monospace);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--text-dim,#8aa)}',
    '#v5panel .v5ph h2{font-size:21px;font-weight:700;margin:6px 0 0;line-height:1.1}',
    '#v5panel .v5pb{padding:16px 22px 90px;overflow:auto}',
    '#v5panel .v5close{position:absolute;top:14px;right:14px;background:none;border:1px solid var(--border,rgba(255,255,255,.18));color:var(--text,#dfe);border-radius:8px;width:30px;height:30px;cursor:pointer;font-size:16px;line-height:1}',
    '.v5-chip{font-family:var(--font-m,monospace);font-size:9.5px;letter-spacing:.06em;border:1px solid currentColor;border-radius:6px;padding:1px 6px;white-space:nowrap}',
    '.v5-chip.live{color:#5ad1ff}.v5-chip.down{color:#ff7eb6}.v5-chip.partial{color:#ffd166}.v5-chip.roadmap{color:#9ea7c0}.v5-chip.modeled{color:#c9a0ff}.v5-chip.locked{color:#ffd166}',
    '.v5-card{border:1px solid var(--border,rgba(255,255,255,.12));border-radius:12px;padding:13px 14px;margin:11px 0;background:rgba(255,255,255,.02)}',
    '.v5-card .v5-h{display:flex;align-items:center;gap:8px;justify-content:space-between;font-weight:700;font-size:13.5px}',
    '.v5-card .v5-sub{font-size:11.5px;color:var(--text-muted,#aab);margin-top:3px;font-family:var(--font-m,monospace)}',
    '.v5-card p{font-size:12.5px;line-height:1.55;color:var(--text,#dfe);opacity:.92;margin:8px 0 0}',
    '.v5-lean{font-family:var(--font-m,monospace);font-size:11px;background:rgba(0,0,0,.34);border-left:2px solid var(--skel,#ffd166);border-radius:6px;padding:8px 10px;margin-top:8px;white-space:pre-wrap;word-break:break-word;color:#e7ecff}',
    '.v5-note{border:1px solid var(--warn,#ff7eb6);background:rgba(255,126,182,.08);border-radius:10px;padding:11px 13px;margin:12px 0;font-size:12px;line-height:1.5}',
    '.v5-note .nh{font-family:var(--font-m,monospace);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--warn,#ff7eb6);margin-bottom:6px}',
    '.v5-btn{pointer-events:auto;font-family:var(--font-m,monospace);font-size:11px;letter-spacing:.03em;color:var(--text,#dfe);background:rgba(255,255,255,.04);border:1px solid var(--border,rgba(255,255,255,.18));border-radius:9px;padding:8px 12px;cursor:pointer}',
    '.v5-btn:hover{border-color:#39d8c8;color:#39d8c8}',
    '#v5-blood{position:fixed;z-index:21;top:12px;left:50%;transform:translateX(-50%);pointer-events:auto;cursor:pointer;font-family:var(--font-m,monospace);font-size:10.5px;letter-spacing:.04em;color:#ff8fb0;background:rgba(8,11,20,.82);border:1px solid rgba(255,59,92,.4);border-radius:999px;padding:5px 13px;backdrop-filter:blur(6px);display:flex;gap:9px;align-items:center}',
    '#v5-blood .bdot{width:7px;height:7px;border-radius:50%;background:#3a4456;box-shadow:none;animation:none}',
    '#v5-blood[data-evidence="source-reported"] .bdot{background:#ffd166}',
    '@keyframes v5beat{0%,100%{transform:scale(.8);opacity:.7}50%{transform:scale(1.3);opacity:1}}',
    '.v5-verify{border:1px solid #39d8c8;background:rgba(57,216,200,.07);border-radius:12px;padding:13px 14px;margin:16px 0}',
    '.v5-verify .vh{font-family:var(--font-m,monospace);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#39d8c8;margin-bottom:8px}',
    '.v5-verify .vres{font-family:var(--font-m,monospace);font-size:11.5px;margin-top:9px;line-height:1.5;word-break:break-all}',
    '.v5-verify .pass{color:#5ad1ff;font-weight:700}.v5-verify .fail{color:#ff7eb6;font-weight:700}',
    '@media (max-width:720px){#v5panel{width:100vw}#v5-blood{font-size:9.5px;top:8px}}'
  ].join('\n');
  document.head.appendChild(el('style',null,css));

  /* ---------------- shared left panel ---------------- */
  var panel = el('div',{id:'v5panel','aria-hidden':'true',role:'dialog','aria-label':'v5 overlay'});
  var head  = el('div',{class:'v5ph'});
  var eyebrow = el('div',{class:'eyebrow'},'SZL Agent Body · v5 (evolves v4)');
  var titleEl = el('h2',null,'');
  var closeBtn = el('button',{class:'v5close','aria-label':'close'},'×');
  head.appendChild(eyebrow); head.appendChild(titleEl); head.appendChild(closeBtn);
  var body = el('div',{class:'v5pb'});
  panel.appendChild(head); panel.appendChild(body);
  document.body.appendChild(panel);
  var openView=null;
  function closePanel(){ panel.classList.remove('open'); panel.setAttribute('aria-hidden','true'); openView=null; syncButtons(); }
  closeBtn.addEventListener('click',closePanel);
  document.addEventListener('keydown',function(e){ if(e.key==='Escape' && panel.classList.contains('open')) closePanel(); });
  function openPanel(view,title,render){
    if(openView===view){ closePanel(); return; }
    openView=view; titleEl.textContent=title; body.innerHTML='<div class="v5-sub">loading live data…</div>';
    panel.classList.add('open'); panel.setAttribute('aria-hidden','false'); panel.scrollTop=0;
    syncButtons();
    try{ render(body); }catch(err){ body.innerHTML='<div class="v5-note"><div class="nh">error</div>'+esc(String(err))+'</div>'; }
  }
  function emptyState(msg){ return '<div class="v5-note"><div class="nh">honest empty-state</div>'+esc(msg)+'</div>'; }

  /* ---- fail-closed public observations: HTTP 200 is not operational proof ----
   These pure classifiers never verify model identity, signatures, freshness or
   execution. They are safe inputs to the SOURCE-REPORTED visual plane only. */
  function meshObservation(d){
    if (!d || typeof d !== "object" || !Array.isArray(d.mesh) || d.mesh.length > 64 ||
        !Number.isSafeInteger(d.engines_live) || !Number.isSafeInteger(d.engines_total) ||
        d.engines_live < 0 || d.engines_total < 0 || d.engines_live > d.engines_total ||
        d.mesh.some(function(n){ return !n || typeof n !== "object" || typeof n.live !== "boolean"; })){
      return { valid: false, state: "UNAVAILABLE", reason: "INVALID_MESH_REPORT" };
    }
    var observedUp = d.mesh.filter(function(n){ return n.live === true; }).length;
    if (d.engines_live === 0 && observedUp > 0){
      return { valid: false, state: "UNAVAILABLE", reason: "INCONSISTENT_MESH_REPORT" };
    }
    return { valid: true, state: d.engines_live > 0 ? "SOURCE_REPORTED_ACTIVE" : "SOURCE_REPORTED_DOWN",
      enginesLive: d.engines_live, enginesTotal: d.engines_total,
      nodesUp: observedUp, nodesTotal: d.mesh.length };
  }
  function ledgerObservation(d){
    if (!d || typeof d !== "object" || !Number.isSafeInteger(d.total_receipts) ||
        d.total_receipts < 0 || typeof d.chain_alg !== "string" ||
        !/^[a-zA-Z0-9_-]{1,48}$/.test(d.chain_alg)){
      return { valid: false, state: "UNAVAILABLE", reason: "INVALID_LEDGER_REPORT" };
    }
    return { valid: true, state: "SOURCE_REPORTED", count: d.total_receipts,
      algorithm: d.chain_alg, signatureVerified: false, chainVerified: false };
  }

  /* ===================================================================
     1. WILLAY — conscience / immune-gate (live classifiers)
     =================================================================== */
  function renderWillay(b){
    getJSON(EP.willay).then(function(d){
      var cs=d&&d.classifiers;
      if (!Array.isArray(cs) || cs.length > 64){
        b.innerHTML=emptyState("WILLAY catalog invalid or unavailable; no classifier readiness inferred.");
        return;
      }
      var tc=d&&d.trust_ceiling;
      var h='';
      h+='<div class="v5-card"><div class="v5-h">Inspectable classifier catalog <span class="v5-chip partial">SOURCE-REPORTED</span></div>';
      h+='<div class="v5-sub">trust ceiling '+esc(tc!=null?tc:'UNAVAILABLE')+' · '+esc(cs.length)+' declared classifiers</div>';
      h+='<p>'+esc((d&&d.honest_note)||'')+'</p></div>';
      h+='<div class="v5-note"><div class="nh">operational boundary</div>Catalog retrieval proves neither classifier execution nor a signed refusal. Independent signed-turn verification is NOT PERFORMED by this panel.</div>';
      cs.forEach(function(c){
        if(!c || typeof c!=="object") return;
        h+='<div class="v5-card"><div class="v5-h">'+esc(c.title||c.category)+' <span class="v5-chip partial">'+esc((c.category||'').toUpperCase())+'</span></div>';
        h+='<div class="v5-sub">fires on: '+esc(c.fires_on||'')+'</div>';
        h+='<p>'+esc(c.rationale||'')+'</p>';
        h+='<div class="v5-sub" style="margin-top:7px">lineage: '+esc(c.lineage||'')+'</div></div>';
      });
      b.innerHTML=h;
    }).catch(function(e){ b.innerHTML=emptyState('WILLAY classifiers endpoint unreachable ('+e.message+'). No classifiers fabricated. Try again when '+EP.willay+' answers.'); });
  }

  /* ===================================================================
     2. SOVEREIGN MESH — circulatory upgrade (live per-node up/DOWN)
     =================================================================== */
  function renderMesh(b){
    getJSON(EP.mesh).then(function(d){
      var report=meshObservation(d);
      if(!report.valid){
        b.innerHTML=emptyState('Mesh observation rejected: '+report.reason+'. No model or node is marked live.');
        return;
      }
      var nodes=d.mesh;
      var h='';
      h+='<div class="v5-card"><div class="v5-h">Governed inference mesh <span class="v5-chip partial">'+(report.enginesLive>0?'SOURCE-REPORTED ACTIVE':'SOURCE-REPORTED DOWN')+'</span></div>';
      h+='<div class="v5-sub">engines reported '+esc(report.enginesLive)+' / '+esc(report.enginesTotal)+' · nodes reported '+esc(report.nodesUp)+' / '+esc(report.nodesTotal)+' · governance '+esc(d.governance||'UNAVAILABLE')+'</div>';
      h+='<p>This is upstream inventory metadata, not measured GPU inference, source freshness, artifact identity or independently verified signed turns. F11 is a formal reference, not a live network witness.</p></div>';
      nodes.forEach(function(n){
        var up=n.live===true;
        h+='<div class="v5-card"><div class="v5-h">'+esc(n.name||n.model||'node')+' <span class="v5-chip '+(up?'partial':'down')+'">'+(up?'REPORTED UP':'REPORTED DOWN')+'</span></div>';
        h+='<div class="v5-sub">model '+esc(n.model||'—')+' · tier '+esc(n.tier||'—')+' · effort '+esc(n.effort||'—')+'</div>';
        h+='<div class="v5-sub" style="margin-top:5px">F11 reference is not proof of reachability or admitted inference.</div></div>';
      });
      var glm=d.glm;
      if(glm && typeof glm==="object"){
        var glmUp=glm.on_metal_live===true;
        h+='<div class="v5-card"><div class="v5-h">GLM engine <span class="v5-chip '+(glmUp?'partial':'down')+'">'+(glmUp?'REPORTED UP':'REPORTED DOWN')+'</span></div>';
        h+='<div class="v5-sub">'+esc(glm.model_tag||'')+'</div><p>'+esc(glm.note||'')+(glm.remote_provider_enabled===true?'':' Remote provider not enabled.')+'</p></div>';
      }
      h+='<div class="v5-note"><div class="nh">independent admission missing</div>Zero signed inference turns verified here. VRAM fusion is ROADMAP; energy joules are UNAVAILABLE without a measured meter. '+esc(d.meter_fresh_live===true?'Meter status is source-reported, not independently metered.':'No fresh meter reported.')+'</div>';
      b.innerHTML=h;
    }).catch(function(e){ b.innerHTML=emptyState('Mesh /govern/health unreachable ('+e.message+'). No node is shown as up. Try again when '+EP.mesh+' answers.'); });
  }

  /* ===================================================================
     3a. Ledger bloodstream counter (live) + 3b. buyer-verifiable receipt
     =================================================================== */
  var bloodHUD = el('div',{id:'v5-blood',title:'Receipt ledger count — source-reported only; click to inspect and verify offline.','role':'button','tabindex':'0','data-evidence':'unavailable'},
    '<span class="bdot" aria-hidden="true"></span><span id="v5-blood-txt" role="status" aria-live="polite">ledger · awaiting source</span>');
  document.body.appendChild(bloodHUD);
  function refreshBlood(){
    getJSON(EP.ledger).then(function(d){
      var report=ledgerObservation(d);
      var target=document.getElementById('v5-blood-txt');
      if(!report.valid){
        bloodHUD.setAttribute('data-evidence','unavailable');
        target.textContent='bloodstream · UNAVAILABLE ('+report.reason+')';
        return;
      }
      bloodHUD.setAttribute('data-evidence','source-reported');
      target.textContent='bloodstream · '+report.count+' SOURCE-REPORTED entries · signature NOT VERIFIED';
    }).catch(function(){
      bloodHUD.setAttribute('data-evidence','unavailable');
      document.getElementById('v5-blood-txt').textContent='bloodstream · UNREACHABLE · no verified pulse';
    });
  }
  bloodHUD.addEventListener('click',function(){ openPanel('ledger','Receipt bloodstream — unified ledger',renderLedger); });
  bloodHUD.addEventListener('keydown',function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); bloodHUD.click(); } });

  function renderLedger(b){
    getJSON(EP.ledger).then(function(d){
      var report=ledgerObservation(d);
      if(!report.valid){ b.innerHTML=emptyState('Ledger observation rejected: '+report.reason); return; }
      var head='', idx='';
      if(d.organs && typeof d.organs==='object'){
        for(var k in d.organs){
          if(Object.prototype.hasOwnProperty.call(d.organs,k) && d.organs[k] && typeof d.organs[k]==='object'){
            head=d.organs[k].chain_head||''; idx=d.organs[k].chain_index; break;
          }
        }
      }
      var h='';
      h+='<div class="v5-card"><div class="v5-h">Unified ledger <span class="v5-chip partial">SOURCE-REPORTED</span></div>';
      h+='<div class="v5-sub">reported entries '+esc(report.count)+' · chain algorithm '+esc(report.algorithm)+' · schema '+esc(d.schema||'UNAVAILABLE')+'</div>';
      h+='<div class="v5-lean">reported chain head: '+esc(head||'UNAVAILABLE')+'\nreported index: '+esc(idx==null?'UNAVAILABLE':idx)+'</div>';
      h+='<p>No full-chain replay, independent signer provenance, source freshness or DSSE signature is verified by this read-only ledger count. Inspect an individual receipt below; do not treat a successful HTTP response as admission.</p></div>';
      h+=verifyCardHTML();
      b.innerHTML=h;
      wireVerify(b.querySelector('.v5-verify'));
    }).catch(function(e){ b.innerHTML=emptyState('Ledger /api/lake/v1/health unreachable ('+e.message+'). Counter not fabricated.'); });
  }

  function verifyCardHTML(){
    return '<div class="v5-verify"><div class="vh">Buyer-verifiable receipt — verify offline</div>'+
      '<div class="v5-sub">Tier-1 WebCrypto ECDSA-P256-SHA256 over the DSSE PAE, against cosign.pub. Runs entirely in your browser — no key sent, no trust in us required.</div>'+
      '<button class="v5-btn" style="margin-top:10px">✓ Verify a live receipt offline</button>'+
      '<div class="vres" aria-live="polite"></div></div>';
  }

  /* --- WebCrypto DSSE ECDSA-P256 verify (ported, tested in Node) --- */
  function b64ToBytes(b64){ var bin=atob(b64.replace(/-/g,'+').replace(/_/g,'/')); var u=new Uint8Array(bin.length); for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i); return u; }
  function cat(){ var arrs=[].slice.call(arguments),n=0,i; for(i=0;i<arrs.length;i++)n+=arrs[i].length; var o=new Uint8Array(n),p=0; for(i=0;i<arrs.length;i++){o.set(arrs[i],p);p+=arrs[i].length;} return o; }
  function derToRaw(der){
    var i=0; if(der[i++]!==0x30) throw new Error('bad DER (no SEQUENCE)'); var sl=der[i++]; if(sl&0x80){var n=sl&0x7f; while(n--)i++;}
    function rdInt(){ if(der[i++]!==0x02) throw new Error('bad DER (no INTEGER)'); var len=der[i++]; var v=der.slice(i,i+len); i+=len; while(v.length>1&&v[0]===0)v=v.slice(1); return v; }
    var r=rdInt(), s=rdInt(); var out=new Uint8Array(64); out.set(r,32-r.length); out.set(s,64-s.length); return out;
  }
  function importCosign(pem){
    var b64=pem.replace(/-----[^-]+-----/g,'').replace(/\s+/g,'');
    return crypto.subtle.importKey('spki', b64ToBytes(b64), {name:'ECDSA',namedCurve:'P-256'}, false, ['verify']);
  }
  function verifyDSSE(env, key){
    var enc=new TextEncoder();
    var payload=b64ToBytes(env.payload);
    var type=env.payloadType||'';
    var pae=cat(enc.encode('DSSEv1 '), enc.encode(String(enc.encode(type).length)+' '), enc.encode(type), enc.encode(' '+String(payload.length)+' '), payload);
    var rawSig=derToRaw(b64ToBytes(env.signatures[0].sig));
    return crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'}, key, rawSig, pae).then(function(ok){ return {ok:ok,pae:pae,type:type}; });
  }
  function wireVerify(card){
    if(!card) return; var btn=card.querySelector('.v5-btn'), out=card.querySelector('.vres');
    btn.addEventListener('click',function(){
      out.innerHTML='verifying…'; btn.disabled=true;
      Promise.all([ getJSON(EP.receipts), getText(EP.cosign) ]).then(function(res){
        var rec=res[0]&&res[0].results&&res[0].results[0];
        var env=rec&&rec.receipt&&rec.receipt.dsse;
        if(!env||!env.payload||!env.signatures){ out.innerHTML=emptyState('No signed DSSE receipt available to verify yet.'); btn.disabled=false; return; }
        return importCosign(res[1]).then(function(key){ return verifyDSSE(env,key); }).then(function(v){
          var headHash=rec.chain_hash||'';
          out.innerHTML='<div class="'+(v.ok?'pass':'fail')+'">'+(v.ok?'✓ SIGNATURE VALID':'✗ SIGNATURE INVALID')+'</div>'+
            'alg: ECDSA-P256-SHA256 over DSSE PAE<br>'+
            'payloadType: '+esc(env.payloadType)+'<br>'+
            'keyid: '+esc((env.signatures[0]||{}).keyid||'—')+'<br>'+
            'chain head: '+esc(headHash.slice(0,32))+'…<br>'+
            'chain index: '+esc(rec.chain_index)+
            '<div class="v5-sub" style="margin-top:8px">Verified locally with the browser WebCrypto API against cosign.pub — '+(v.ok?'this receipt is unaltered from the signer.':'do NOT trust this receipt.')+'</div>';
          btn.disabled=false;
        });
      }).catch(function(e){ out.innerHTML=emptyState('Verify unavailable ('+e.message+'). Endpoints read-only; nothing fabricated.'); btn.disabled=false; });
    });
  }

  /* in-scene: inject "Verify offline" into the open organ panel for
     receipt-emitting organs (heart gate, bus, conscience, mesh, write, crown) */
  var RECEIPT_ORGANS={yuyay:1,yawar:1,willay:1,sovereign_mesh:1,ruway:1,hatun:1,sentra:1};
  root.addEventListener('szl:organ-open',function(ev){
    var o=ev.detail; if(!o||!RECEIPT_ORGANS[o.key]) return;
    var pb=document.getElementById('p-body'); if(!pb) return;
    if(pb.querySelector('.v5-verify')) return;
    var wrap=el('div'); wrap.innerHTML=verifyCardHTML(); var card=wrap.firstChild;
    pb.appendChild(card); wireVerify(card);
  });

  /* ===================================================================
     4. 8 locked-proven → organ map (verbatim Lean + axioms)
     =================================================================== */
  function leanStatement(fid){
    var f=D.FORMULAS&&D.FORMULAS[fid]; if(!f) return fid;
    return fid+'  '+(f.name||'')+'\n'+(f.latex||'')+'\n#print axioms: '+(f.axioms||'');
  }
  function renderProofs(b){
    var M=D.LEAN_MAP||{}; var h='';
    h+='<div class="v5-card"><div class="v5-h">8 locked-proven → organs <span class="v5-chip locked">LOCKED</span></div>';
    h+='<div class="v5-sub">'+esc(M.verified_note||'')+' · exactly 8 {F1,F4,F7,F11,F12,F18,F19,F22}</div>';
    h+='<p>Presentational map only — it does NOT change the locked set. Each statement below is kernel-verified sorry-free at '+esc(M.kernel_sha||'c7c0ba17')+'.</p></div>';
    (M.organs||[]).forEach(function(row){
      h+='<div class="v5-card"><div class="v5-h"><span style="color:'+esc(row.color)+'">'+esc(row.organ)+'</span> <span class="v5-chip locked">'+esc(row.formulas.join(' + '))+'</span></div>';
      h+='<p>'+esc(row.why)+'</p>';
      row.formulas.forEach(function(fid){ h+='<div class="v5-lean">'+esc(leanStatement(fid))+'</div>'; });
      h+='</div>';
    });
    h+='<div class="v5-note"><div class="nh">Λ honesty · Conjecture 1</div>'+esc(M.lambda||'')+'</div>';
    h+='<div class="v5-note"><div class="nh">Khipu BFT · Conjecture 2</div>'+esc(M.khipu||'')+'</div>';
    b.innerHTML=h;
  }

  /* ===================================================================
     5. AI-Assurance (WDP/CDAO) overlay
     =================================================================== */
  function statusClass(s){ return s==='LIVE'?'live':(s==='PARTIAL'?'partial':'roadmap'); }
  function renderAssurance(b){
    var A=D.ASSURANCE_MAP||{}; var h='';
    h+='<div class="v5-card"><div class="v5-h">AI-Assurance map (WDP / CDAO)</div>';
    h+='<p>'+esc(A.note||'')+' <a href="'+esc(A.surface||'#')+'" target="_blank" rel="noopener" style="color:#39d8c8">live /assurance surface ↗</a></p></div>';
    (A.rows||[]).forEach(function(r){
      h+='<div class="v5-card"><div class="v5-h">'+esc(r.organ)+' <span class="v5-chip '+statusClass(r.status)+'">'+esc(r.status)+'</span></div>';
      h+='<div class="v5-sub">artifact: '+esc(r.artifact)+'</div><p>'+esc(r.detail)+'</p></div>';
    });
    h+='<div class="v5-note"><div class="nh">honest chips</div>LIVE = artifact exists and is reachable · PARTIAL = exists but incomplete / sampled · ROADMAP = planned, not yet real. No status is inflated.</div>';
    b.innerHTML=h;
  }

  /* ===================================================================
     6. yarqa CFD + thermal-PINN physics overlay (MODELED)
     =================================================================== */
  function renderPhysics(b){
    var P=D.PHYSICS_OVERLAY||{}; var h='';
    h+='<div class="v5-card"><div class="v5-h">'+esc(P.headline||'physics-governed layer')+' <span class="v5-chip modeled">'+esc(P.label||'MODELED')+'</span></div>';
    h+='<p>'+esc(P.honest||'')+'</p></div>';
    (P.components||[]).forEach(function(c){
      h+='<div class="v5-card"><div class="v5-h">'+esc(c.name)+' <span class="v5-chip modeled">'+esc(c.kind)+'</span></div><p>'+esc(c.detail)+'</p></div>';
    });
    h+='<div class="v5-note"><div class="nh">bounded error</div>'+esc(P.bounded_error||'')+'</div>';
    h+='<div class="v5-note"><div class="nh">never</div>'+esc(P.never||'')+'</div>';
    h+='<div class="v5-sub" style="margin-top:8px">Composes with the existing yarqa flow-compartments overlay in the v4 dissection dock (off by default). data.js stays the single source of truth; locked-proven count unchanged at 8.</div>';
    b.innerHTML=h;
  }

  /* ===================================================================
     7. GPU-SOVEREIGN STACK (SUBSTRATE) — vertical compute anatomy.
        Static layer model from D.STACK_LAYER; live layers (runtime, mesh)
        light up from EP.mesh /govern/health and degrade to DOWN when
        unreachable — never a fabricated green light. The frontier layer is
        buyer-verifiable in-scene via the shared WebCrypto verify card.
     =================================================================== */
  function renderStack(b){
    var S=D.STACK_LAYER||{};
    if(!S.layers){ b.innerHTML=emptyState('Stack-layer data not loaded.'); return; }
    function paint(mesh, ledger){
      var m=meshObservation(mesh), l=ledgerObservation(ledger);
      var engLive=m.valid?m.enginesLive:null, engTot=m.valid?m.enginesTotal:null;
      var nodes=m.valid?m.nodesTotal:0, nodesLive=m.valid?m.nodesUp:0;
      var meshUp=m.valid && m.enginesLive>0;
      var rcpt=l.valid?l.count:null, rcptAlg=l.valid?l.algorithm:'UNAVAILABLE', rcptHead='';
      if(l.valid && ledger.organs && typeof ledger.organs==='object'){
        for(var k in ledger.organs){
          if(Object.prototype.hasOwnProperty.call(ledger.organs,k)){
            var ch=ledger.organs[k]&&ledger.organs[k].chain_head;
            if(typeof ch==='string' && ch.length<=128 && ch){rcptHead=ch;break;}
          }
        }
      }
      var h='';
      h+='<div class="v5-card"><div class="v5-h">'+esc(S.headline||'GPU-Sovereign Stack')+' <span class="v5-chip partial">SCHEMATIC</span></div>';
      h+='<p>'+esc(S.thesis||'')+'</p></div>';
      (S.layers||[]).forEach(function(L){
        var chip=L.chip||'roadmap', posture=String(L.posture||''), extra='';
        if(chip==='live'){chip='partial';posture='DECLARED · '+posture;}
        if(L.live_key){
          if(!m.valid){ chip='down'; posture='UNAVAILABLE · '+m.reason; }
          else if(L.live_key==='mesh'){ chip=meshUp?'partial':'down'; posture=meshUp?('SOURCE-REPORTED · '+esc(nodesLive)+'/'+esc(nodes)+' nodes'):('REPORTED DOWN · '+esc(nodesLive)+'/'+esc(nodes)+' nodes'); }
          else if(L.live_key==='engine'){ chip=(engLive>0)?'partial':'down'; posture=(engLive>0)?('SOURCE-REPORTED · '+esc(engLive)+'/'+esc(engTot)+' engines'):'REPORTED DOWN'; }
        }
        if(L.receipt_key==='ledger'){
          if(l.valid){ chip='partial'; posture='SOURCE-REPORTED · '+esc(rcpt)+' entries (unverified)'; extra='ledger metadata · '+esc(rcpt)+' entries · '+esc(rcptAlg)+(rcptHead?' · reported head '+esc(rcptHead.slice(0,12))+'…':'')+' · NOT signature/chain verified; verify an individual receipt below'; }
          else { chip='down'; posture='UNAVAILABLE'; extra='ledger source rejected or unreachable; no receipt proof inferred'; }
        }
        h+='<div class="v5-card"><div class="v5-h"><span><span style="opacity:.55;font-family:var(--font-m,monospace);font-size:11px">'+esc(L.tier)+'</span> '+esc(L.name)+'</span> <span class="v5-chip '+chip+'">'+posture+'</span></div>';
        h+='<div class="v5-sub">leaders: '+esc(L.leaders||'')+'</div>';
        h+='<p>'+esc(L.szl||'')+'</p>';
        if(extra) h+='<div class="v5-sub" style="margin-top:6px;color:var(--ok,#39d98a)">'+extra+'</div>';
        if(L.honest) h+='<div class="v5-sub" style="margin-top:7px;color:var(--warn,#ff7eb6)">honest · '+esc(L.honest)+'</div>';
        h+='</div>';
      });
      h+='<div class="v5-note"><div class="nh">push the frontier</div>'+esc(S.frontier||'')+'</div>';
      h+='<div class="v5-note"><div class="nh">never</div>'+esc(S.never||'')+'</div>';
      h+=verifyCardHTML();
      b.innerHTML=h;
      wireVerify(b.querySelector('.v5-verify'));
    }
    Promise.all([ getJSON(EP.mesh).catch(function(){return null;}), getJSON(EP.ledger).catch(function(){return null;}) ])
      .then(function(r){ paint(r[0], r[1]); });
  }

  /* ---------------- buttons (wired to ids placed in index.html) ---------------- */
  var BTNS=[
    {id:'btn-v5-willay',    view:'willay',    title:'WILLAY — conscience / immune-gate', render:renderWillay},
    {id:'btn-v5-mesh',      view:'mesh',      title:'Sovereign Mesh — circulatory upgrade', render:renderMesh},
    {id:'btn-v5-proofs',    view:'proofs',    title:'8 locked-proven → organs', render:renderProofs},
    {id:'btn-v5-assurance', view:'assurance', title:'AI-Assurance (WDP / CDAO)', render:renderAssurance},
    {id:'btn-v5-physics',   view:'physics',   title:'yarqa CFD + thermal PINN (MODELED)', render:renderPhysics},
    {id:'btn-v5-stack',     view:'stack',     title:'SUBSTRATE — GPU-Sovereign Stack', render:renderStack}
  ];
  function syncButtons(){ BTNS.forEach(function(cfg){ var btn=document.getElementById(cfg.id); if(btn){ var on=openView===cfg.view; btn.classList.toggle('active',on); btn.setAttribute('aria-expanded',on?'true':'false'); } }); }
  function wireButtons(){ BTNS.forEach(function(cfg){ var btn=document.getElementById(cfg.id); if(btn) btn.addEventListener('click',function(){ openPanel(cfg.view,cfg.title,cfg.render); }); }); }

  /* ---------------- init ---------------- */
  function init(){ wireButtons(); refreshBlood(); setInterval(refreshBlood, 30000); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();

})(window);
