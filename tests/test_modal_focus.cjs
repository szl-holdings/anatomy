// SPDX-License-Identifier: Apache-2.0
// Unit DOM doubles exercise actual source functions. Real browser runs are separate.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {restoreBodyFocus, trapDialogTab, observationHTML} = require('../frontier_anatomy.js');

function fixture() {
  const doc = {activeElement:null};
  const node = (id, options={}) => Object.assign({
    id, disabled:false, tabIndex:0, visible:true, attributes:{},
    getClientRects(){return this.visible ? [{}] : [];},
    focus(options){doc.activeElement=this;this.focusOptions=options;},
    setAttribute(key,value){this.attributes[key]=value;}
  }, options);
  const close=node('fa-close'), refresh=node('fa-refresh'), last=node('last');
  const body={contains(n){return this.children.includes(n);},children:[refresh,last]};
  const panel=node('fa-panel');panel.open=true;
  panel.classList={contains(value){return value==='open' && panel.open;}};
  panel.controls=[close,refresh,last];panel.querySelectorAll=()=>panel.controls;
  const registry={'fa-panel':panel,'fa-close':close,'fa-refresh':refresh,last};
  doc.getElementById=id=>registry[id]||null;doc.activeElement=node('outside');
  global.document=doc;
  return {doc,node,close,refresh,last,body,panel,registry};
}
function event(shiftKey=false,key='Tab') {
  return {key,shiftKey,prevented:false,preventDefault(){this.prevented=true;}};
}

test('restores the corresponding control without scrolling',()=>{
  const f=fixture();restoreBodyFocus(f.body,'fa-refresh');
  assert.equal(f.doc.activeElement,f.refresh);assert.deepEqual(f.refresh.focusOptions,{preventScroll:true});
});
for (const condition of ['missing','disabled','hidden','outside-body','anonymous']) {
  test(`falls back inside the dialog for ${condition} controls`,()=>{
    const f=fixture();let id='fa-refresh';
    if(condition==='missing')delete f.registry[id];
    if(condition==='disabled')f.refresh.disabled=true;
    if(condition==='hidden')f.refresh.visible=false;
    if(condition==='outside-body')f.body.children=[];
    if(condition==='anonymous')id=null;
    restoreBodyFocus(f.body,id);assert.equal(f.doc.activeElement,f.close);
  });
}
for (const condition of ['closed','missing-panel','missing-body']) {
  test(`does not restore into a ${condition} dialog`,()=>{
    const f=fixture(),before=f.doc.activeElement;
    if(condition==='closed')f.panel.open=false;
    if(condition==='missing-panel')delete f.registry['fa-panel'];
    restoreBodyFocus(condition==='missing-body'?null:f.body,'fa-refresh');
    assert.equal(f.doc.activeElement,before);
  });
}
test('keeps an aria-disabled busy control focusable',()=>{
  const f=fixture();f.refresh.setAttribute('aria-disabled','true');
  restoreBodyFocus(f.body,'fa-refresh');assert.equal(f.doc.activeElement,f.refresh);
});
for (const backwards of [false,true]) {
  test(`reenters from external focus (${backwards?'backward':'forward'})`,()=>{
    const f=fixture(),e=event(backwards);trapDialogTab(f.panel,e);
    assert.ok(e.prevented);assert.equal(f.doc.activeElement,backwards?f.last:f.close);
  });
  test(`wraps at the ${backwards?'first':'last'} control`,()=>{
    const f=fixture(),e=event(backwards);f.doc.activeElement=backwards?f.close:f.last;
    trapDialogTab(f.panel,e);assert.ok(e.prevented);assert.equal(f.doc.activeElement,backwards?f.last:f.close);
  });
  test(`lets native traversal handle an interior control (${backwards})`,()=>{
    const f=fixture(),e=event(backwards);f.doc.activeElement=f.refresh;
    trapDialogTab(f.panel,e);assert.equal(e.prevented,false);assert.equal(f.doc.activeElement,f.refresh);
  });
}
for (const options of [{disabled:true},{tabIndex:-1},{visible:false}]) {
  test(`ignores a non-tabbable trailing control ${JSON.stringify(options)}`,()=>{
    const f=fixture(),e=event();f.panel.controls.push(f.node('excluded',options));
    f.doc.activeElement=f.last;trapDialogTab(f.panel,e);assert.ok(e.prevented);assert.equal(f.doc.activeElement,f.close);
  });
}
test('contains focus when there are no controls',()=>{
  const f=fixture(),e=event();f.panel.controls=[];trapDialogTab(f.panel,e);
  assert.ok(e.prevented);assert.equal(f.doc.activeElement,f.panel);assert.equal(f.panel.attributes.tabindex,'-1');
});
test('closed dialogs and non-Tab keys are untouched',()=>{
  const f=fixture(),before=f.doc.activeElement,e=event();f.panel.open=false;
  trapDialogTab(f.panel,e);assert.equal(e.prevented,false);
  f.panel.open=true;const other=event(false,'Enter');trapDialogTab(f.panel,other);
  assert.equal(other.prevented,false);assert.equal(f.doc.activeElement,before);
});
test('actual busy observation markup preserves native keyboard focus',()=>{
  const html=observationHTML({dependencies:[]},Date.now(),true);
  const button=html.match(/<button[^>]*id="fa-refresh"[^>]*>/)?.[0];
  assert.ok(button);assert.match(button,/aria-disabled="true"/);
  assert.doesNotMatch(button,/\sdisabled(?:[\s=>])/);
});
