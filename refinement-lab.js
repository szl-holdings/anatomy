"use strict";
const $ = (id) => document.getElementById(id);
const short = (value, n=16) => value ? `${String(value).slice(0,n)}…` : "—";
const pct = (value) => `${(Number(value||0)*100).toFixed(1)}%`;
function setText(id,value){$(id).textContent=String(value)}
function card(handle){
  const article=document.createElement("article");
  const title=document.createElement("h3"); title.textContent=handle.error_code; article.append(title);
  const dl=document.createElement("dl");
  const rows=[
    ["Attempts",handle.repair_attempts],
    ["Verified repair",pct(handle.verified_repair_rate)],
    ["Regression",pct(handle.regression_rate)],
    ["Audit confidence",pct(handle.mean_audit_confidence)],
    ["Pair digest",short(handle.model_pair_sha256)],
    ["Handle",handle.id],
  ];
  for(const [name,value] of rows){const dt=document.createElement("dt");dt.textContent=name;const dd=document.createElement("dd");dd.textContent=String(value);dl.append(dt,dd)}
  article.append(dl); return article;
}
async function readJson(path){const response=await fetch(path,{cache:"no-store",headers:{Accept:"application/json"}});let body={};try{body=await response.json()}catch{}return {response,body}}
async function refresh(){
  const code=$("error-code").value.trim();
  const suffix=code?`?limit=100&error_code=${encodeURIComponent(code)}`:"?limit=100";
  const [statusResult,patternResult]=await Promise.all([
    readJson("/api/anatomy/v1/refinement/status"),
    readJson(`/api/anatomy/v1/refinement/patterns${suffix}`),
  ]);
  const status=statusResult.body||{}; const patterns=patternResult.body||{};
  setText("state",`${status.state||"UNAVAILABLE"} · ${status.ready?"source-bound":"fail-closed"}`);
  $("state-dot").className=`dot ${status.ready?"ready":"blocked"}`;
  setText("revision",short(status.source_revision,20)); setText("receipts",status.receipt_count??"—");
  setText("patterns",status.pattern_count??"—"); setText("digest",short(status.state_sha256,20));
  const handles=Array.isArray(patterns.handles)?patterns.handles:[]; setText("returned",`${handles.length} returned`);
  const cards=$("cards"); cards.replaceChildren(...handles.map(card)); $("empty").hidden=handles.length>0;
}
$("refresh").addEventListener("click",()=>refresh().catch((error)=>setText("state",`UNAVAILABLE · ${error.name}`)));
refresh().catch((error)=>setText("state",`UNAVAILABLE · ${error.name}`));
