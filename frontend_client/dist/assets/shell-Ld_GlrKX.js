(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const i of document.querySelectorAll('link[rel="modulepreload"]'))r(i);new MutationObserver(i=>{for(const s of i)if(s.type==="childList")for(const n of s.addedNodes)n.tagName==="LINK"&&n.rel==="modulepreload"&&r(n)}).observe(document,{childList:!0,subtree:!0});function u(i){const s={};return i.integrity&&(s.integrity=i.integrity),i.referrerPolicy&&(s.referrerPolicy=i.referrerPolicy),i.crossOrigin==="use-credentials"?s.credentials="include":i.crossOrigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function r(i){if(i.ep)return;i.ep=!0;const s=u(i);fetch(i.href,s)}})();var Rn=Object.defineProperty,Nn=(e,t,u)=>t in e?Rn(e,t,{enumerable:!0,configurable:!0,writable:!0,value:u}):e[t]=u,Cu=(e,t,u)=>(Nn(e,typeof t!="symbol"?t+"":t,u),u),Mn=(e,t,u)=>{if(!t.has(e))throw TypeError("Cannot "+u)},$u=(e,t)=>{if(Object(t)!==t)throw TypeError('Cannot use the "in" operator on this value');return e.has(t)},Bt=(e,t,u)=>{if(t.has(e))throw TypeError("Cannot add the same private member more than once");t instanceof WeakSet?t.add(e):t.set(e,u)},ti=(e,t,u)=>(Mn(e,t,"access private method"),u);function Qi(e,t){return Object.is(e,t)}let B=null,At=!1,Kt=1;const uu=Symbol("SIGNAL");function et(e){const t=B;return B=e,t}function jn(){return B}function Ln(){return At}const yr={version:0,lastCleanEpoch:0,dirty:!1,producerNode:void 0,producerLastReadVersion:void 0,producerIndexOfThis:void 0,nextProducerIndex:0,liveConsumerNode:void 0,liveConsumerIndexOfThis:void 0,consumerAllowSignalWrites:!1,consumerIsAlwaysLive:!1,producerMustRecompute:()=>!1,producerRecomputeValue:()=>{},consumerMarkedDirty:()=>{},consumerOnSignalRead:()=>{}};function hu(e){if(At)throw new Error(typeof ngDevMode<"u"&&ngDevMode?"Assertion error: signal read during notification phase":"");if(B===null)return;B.consumerOnSignalRead(e);const t=B.nextProducerIndex++;if(it(B),t<B.producerNode.length&&B.producerNode[t]!==e&&rr(B)){const u=B.producerNode[t];pu(u,B.producerIndexOfThis[t])}B.producerNode[t]!==e&&(B.producerNode[t]=e,B.producerIndexOfThis[t]=rr(B)?es(e,B,t):0),B.producerLastReadVersion[t]=e.version}function Un(){Kt++}function Yi(e){if(!(!e.dirty&&e.lastCleanEpoch===Kt)){if(!e.producerMustRecompute(e)&&!Wn(e)){e.dirty=!1,e.lastCleanEpoch=Kt;return}e.producerRecomputeValue(e),e.dirty=!1,e.lastCleanEpoch=Kt}}function Xi(e){if(e.liveConsumerNode===void 0)return;const t=At;At=!0;try{for(const u of e.liveConsumerNode)u.dirty||qn(u)}finally{At=t}}function Bn(){return B?.consumerAllowSignalWrites!==!1}function qn(e){var t;e.dirty=!0,Xi(e),(t=e.consumerMarkedDirty)==null||t.call(e.wrapper??e)}function Hn(e){return e&&(e.nextProducerIndex=0),et(e)}function Vn(e,t){if(et(t),!(!e||e.producerNode===void 0||e.producerIndexOfThis===void 0||e.producerLastReadVersion===void 0)){if(rr(e))for(let u=e.nextProducerIndex;u<e.producerNode.length;u++)pu(e.producerNode[u],e.producerIndexOfThis[u]);for(;e.producerNode.length>e.nextProducerIndex;)e.producerNode.pop(),e.producerLastReadVersion.pop(),e.producerIndexOfThis.pop()}}function Wn(e){it(e);for(let t=0;t<e.producerNode.length;t++){const u=e.producerNode[t],r=e.producerLastReadVersion[t];if(r!==u.version||(Yi(u),r!==u.version))return!0}return!1}function es(e,t,u){var r;if(xr(e),it(e),e.liveConsumerNode.length===0){(r=e.watched)==null||r.call(e.wrapper);for(let i=0;i<e.producerNode.length;i++)e.producerIndexOfThis[i]=es(e.producerNode[i],e,i)}return e.liveConsumerIndexOfThis.push(u),e.liveConsumerNode.push(t)-1}function pu(e,t){var u;if(xr(e),it(e),typeof ngDevMode<"u"&&ngDevMode&&t>=e.liveConsumerNode.length)throw new Error(`Assertion error: active consumer index ${t} is out of bounds of ${e.liveConsumerNode.length} consumers)`);if(e.liveConsumerNode.length===1){(u=e.unwatched)==null||u.call(e.wrapper);for(let i=0;i<e.producerNode.length;i++)pu(e.producerNode[i],e.producerIndexOfThis[i])}const r=e.liveConsumerNode.length-1;if(e.liveConsumerNode[t]=e.liveConsumerNode[r],e.liveConsumerIndexOfThis[t]=e.liveConsumerIndexOfThis[r],e.liveConsumerNode.length--,e.liveConsumerIndexOfThis.length--,t<e.liveConsumerNode.length){const i=e.liveConsumerIndexOfThis[t],s=e.liveConsumerNode[t];it(s),s.producerIndexOfThis[i]=t}}function rr(e){var t;return e.consumerIsAlwaysLive||(((t=e?.liveConsumerNode)==null?void 0:t.length)??0)>0}function it(e){e.producerNode??(e.producerNode=[]),e.producerIndexOfThis??(e.producerIndexOfThis=[]),e.producerLastReadVersion??(e.producerLastReadVersion=[])}function xr(e){e.liveConsumerNode??(e.liveConsumerNode=[]),e.liveConsumerIndexOfThis??(e.liveConsumerIndexOfThis=[])}function ts(e){if(Yi(e),hu(e),e.value===ir)throw e.error;return e.value}function Jn(e){const t=Object.create(Zn);t.computation=e;const u=()=>ts(t);return u[uu]=t,u}const Eu=Symbol("UNSET"),Au=Symbol("COMPUTING"),ir=Symbol("ERRORED"),Zn={...yr,value:Eu,dirty:!0,error:null,equal:Qi,producerMustRecompute(e){return e.value===Eu||e.value===Au},producerRecomputeValue(e){if(e.value===Au)throw new Error("Detected cycle in computations.");const t=e.value;e.value=Au;const u=Hn(e);let r,i=!1;try{r=e.computation.call(e.wrapper),i=t!==Eu&&t!==ir&&e.equal.call(e.wrapper,t,r)}catch(s){r=ir,e.error=s}finally{Vn(e,u)}if(i){e.value=t;return}e.value=r,e.version++}};function Gn(){throw new Error}let Kn=Gn;function Qn(){Kn()}function Yn(e){const t=Object.create(ta);t.value=e;const u=()=>(hu(t),t.value);return u[uu]=t,u}function Xn(){return hu(this),this.value}function ea(e,t){Bn()||Qn(),e.equal.call(e.wrapper,e.value,t)||(e.value=t,ua(e))}const ta={...yr,equal:Qi,value:void 0};function ua(e){e.version++,Un(),Xi(e)}const Q=Symbol("node");var ge;(e=>{var t,u,r,i;class s{constructor(c,l={}){Bt(this,u),Cu(this,t);const o=Yn(c)[uu];if(this[Q]=o,o.wrapper=this,l){const h=l.equals;h&&(o.equal=h),o.watched=l[e.subtle.watched],o.unwatched=l[e.subtle.unwatched]}}get(){if(!(0,e.isState)(this))throw new TypeError("Wrong receiver type for Signal.State.prototype.get");return Xn.call(this[Q])}set(c){if(!(0,e.isState)(this))throw new TypeError("Wrong receiver type for Signal.State.prototype.set");if(Ln())throw new Error("Writes to signals not permitted during Watcher callback");const l=this[Q];ea(l,c)}}t=Q,u=new WeakSet,e.isState=a=>typeof a=="object"&&$u(u,a),e.State=s;class n{constructor(c,l){Bt(this,i),Cu(this,r);const o=Jn(c)[uu];if(o.consumerAllowSignalWrites=!0,this[Q]=o,o.wrapper=this,l){const h=l.equals;h&&(o.equal=h),o.watched=l[e.subtle.watched],o.unwatched=l[e.subtle.unwatched]}}get(){if(!(0,e.isComputed)(this))throw new TypeError("Wrong receiver type for Signal.Computed.prototype.get");return ts(this[Q])}}r=Q,i=new WeakSet,e.isComputed=a=>typeof a=="object"&&$u(i,a),e.Computed=n,(a=>{var c,l,d,o;function h(w){let y,x=null;try{x=et(null),y=w()}finally{et(x)}return y}a.untrack=h;function p(w){var y;if(!(0,e.isComputed)(w)&&!(0,e.isWatcher)(w))throw new TypeError("Called introspectSources without a Computed or Watcher argument");return((y=w[Q].producerNode)==null?void 0:y.map(x=>x.wrapper))??[]}a.introspectSources=p;function f(w){var y;if(!(0,e.isComputed)(w)&&!(0,e.isState)(w))throw new TypeError("Called introspectSinks without a Signal argument");return((y=w[Q].liveConsumerNode)==null?void 0:y.map(x=>x.wrapper))??[]}a.introspectSinks=f;function b(w){if(!(0,e.isComputed)(w)&&!(0,e.isState)(w))throw new TypeError("Called hasSinks without a Signal argument");const y=w[Q].liveConsumerNode;return y?y.length>0:!1}a.hasSinks=b;function m(w){if(!(0,e.isComputed)(w)&&!(0,e.isWatcher)(w))throw new TypeError("Called hasSources without a Computed or Watcher argument");const y=w[Q].producerNode;return y?y.length>0:!1}a.hasSources=m;class g{constructor(y){Bt(this,l),Bt(this,d),Cu(this,c);let x=Object.create(yr);x.wrapper=this,x.consumerMarkedDirty=y,x.consumerIsAlwaysLive=!0,x.consumerAllowSignalWrites=!1,x.producerNode=[],this[Q]=x}watch(...y){if(!(0,e.isWatcher)(this))throw new TypeError("Called unwatch without Watcher receiver");ti(this,d,o).call(this,y);const x=this[Q];x.dirty=!1;const E=et(x);for(const O of y)hu(O[Q]);et(E)}unwatch(...y){if(!(0,e.isWatcher)(this))throw new TypeError("Called unwatch without Watcher receiver");ti(this,d,o).call(this,y);const x=this[Q];it(x);for(let E=x.producerNode.length-1;E>=0;E--)if(y.includes(x.producerNode[E].wrapper)){pu(x.producerNode[E],x.producerIndexOfThis[E]);const O=x.producerNode.length-1;if(x.producerNode[E]=x.producerNode[O],x.producerIndexOfThis[E]=x.producerIndexOfThis[O],x.producerNode.length--,x.producerIndexOfThis.length--,x.nextProducerIndex--,E<x.producerNode.length){const H=x.producerIndexOfThis[E],ee=x.producerNode[E];xr(ee),ee.liveConsumerIndexOfThis[H]=E}}}getPending(){if(!(0,e.isWatcher)(this))throw new TypeError("Called getPending without Watcher receiver");return this[Q].producerNode.filter(x=>x.dirty).map(x=>x.wrapper)}}c=Q,l=new WeakSet,d=new WeakSet,o=function(w){for(const y of w)if(!(0,e.isComputed)(y)&&!(0,e.isState)(y))throw new TypeError("Called watch/unwatch without a Computed or State argument")},e.isWatcher=w=>$u(l,w),a.Watcher=g;function v(){var w;return(w=jn())==null?void 0:w.wrapper}a.currentComputed=v,a.watched=Symbol("watched"),a.unwatched=Symbol("unwatched")})(e.subtle||(e.subtle={}))})(ge||(ge={}));const ra=Symbol("SignalWatcherBrand"),ia=new FinalizationRegistry((({watcher:e,signal:t})=>{e.unwatch(t)})),ui=new WeakMap;function us(e){return e[ra]===!0?(console.warn("SignalWatcher should not be applied to the same class more than once."),e):class extends e{constructor(){super(...arguments),this._$St=new ge.State(0),this._$Si=!1,this._$So=!0,this._$Sh=new Set}_$Sl(){if(this._$Su!==void 0)return;this._$Sv=new ge.Computed((()=>{this._$St.get(),super.performUpdate()}));const t=this._$Su=new ge.subtle.Watcher((function(){const u=ui.get(this);u!==void 0&&(u._$Si===!1&&u.requestUpdate(),this.watch())}));ui.set(t,this),ia.register(this,{watcher:t,signal:this._$Sv}),t.watch(this._$Sv)}_$Sp(){this._$Su!==void 0&&(this._$Su.unwatch(this._$Sv),this._$Sv=void 0,this._$Su=void 0)}performUpdate(){this.isUpdatePending&&(this._$Sl(),this._$Si=!0,this._$St.set(this._$St.get()+1),this._$Si=!1,this._$Sv.get())}update(t){try{this._$So?(this._$So=!1,super.update(t)):this._$Sh.forEach((u=>u.commit()))}finally{this.isUpdatePending=!1,this._$Sh.clear()}}requestUpdate(t,u,r){this._$So=!0,super.requestUpdate(t,u,r)}connectedCallback(){super.connectedCallback(),this.requestUpdate()}disconnectedCallback(){super.disconnectedCallback(),queueMicrotask((()=>{this.isConnected===!1&&this._$Sp()}))}_(t){this._$Sh.add(t);const u=this._$So;this.requestUpdate(),this._$So=u}m(t){this._$Sh.delete(t)}}}const Mt={ATTRIBUTE:1,CHILD:2},ct=e=>(...t)=>({_$litDirective$:e,values:t});let lt=class{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,u,r){this._$Ct=t,this._$AM=u,this._$Ci=r}_$AS(t,u){return this.update(t,u)}update(t,u){return this.render(...u)}};const vr=globalThis,ri=e=>e,ru=vr.trustedTypes,ii=ru?ru.createPolicy("lit-html",{createHTML:e=>e}):void 0,rs="$lit$",De=`lit$${Math.random().toFixed(9).slice(2)}$`,is="?"+De,sa=`<${is}>`,Ve=document,Tt=()=>Ve.createComment(""),It=e=>e===null||typeof e!="object"&&typeof e!="function",wr=Array.isArray,na=e=>wr(e)||typeof e?.[Symbol.iterator]=="function",Du=`[ 	
\f\r]`,bt=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,si=/-->/g,ni=/>/g,Pe=RegExp(`>|${Du}(?:([^\\s"'>=/]+)(${Du}*=${Du}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),ai=/'/g,oi=/"/g,ss=/^(?:script|style|textarea|title)$/i,aa=e=>(t,...u)=>({_$litType$:e,strings:t,values:u}),k=aa(1),de=Symbol.for("lit-noChange"),$=Symbol.for("lit-nothing"),ci=new WeakMap,Be=Ve.createTreeWalker(Ve,129);function ns(e,t){if(!wr(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return ii!==void 0?ii.createHTML(t):t}const oa=(e,t)=>{const u=e.length-1,r=[];let i,s=t===2?"<svg>":t===3?"<math>":"",n=bt;for(let a=0;a<u;a++){const c=e[a];let l,d,o=-1,h=0;for(;h<c.length&&(n.lastIndex=h,d=n.exec(c),d!==null);)h=n.lastIndex,n===bt?d[1]==="!--"?n=si:d[1]!==void 0?n=ni:d[2]!==void 0?(ss.test(d[2])&&(i=RegExp("</"+d[2],"g")),n=Pe):d[3]!==void 0&&(n=Pe):n===Pe?d[0]===">"?(n=i??bt,o=-1):d[1]===void 0?o=-2:(o=n.lastIndex-d[2].length,l=d[1],n=d[3]===void 0?Pe:d[3]==='"'?oi:ai):n===oi||n===ai?n=Pe:n===si||n===ni?n=bt:(n=Pe,i=void 0);const p=n===Pe&&e[a+1].startsWith("/>")?" ":"";s+=n===bt?c+sa:o>=0?(r.push(l),c.slice(0,o)+rs+c.slice(o)+De+p):c+De+(o===-2?a:p)}return[ns(e,s+(e[u]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),r]};let sr=class as{constructor({strings:t,_$litType$:u},r){let i;this.parts=[];let s=0,n=0;const a=t.length-1,c=this.parts,[l,d]=oa(t,u);if(this.el=as.createElement(l,r),Be.currentNode=this.el.content,u===2||u===3){const o=this.el.content.firstChild;o.replaceWith(...o.childNodes)}for(;(i=Be.nextNode())!==null&&c.length<a;){if(i.nodeType===1){if(i.hasAttributes())for(const o of i.getAttributeNames())if(o.endsWith(rs)){const h=d[n++],p=i.getAttribute(o).split(De),f=/([.?@])?(.*)/.exec(h);c.push({type:1,index:s,name:f[2],strings:p,ctor:f[1]==="."?la:f[1]==="?"?da:f[1]==="@"?fa:bu}),i.removeAttribute(o)}else o.startsWith(De)&&(c.push({type:6,index:s}),i.removeAttribute(o));if(ss.test(i.tagName)){const o=i.textContent.split(De),h=o.length-1;if(h>0){i.textContent=ru?ru.emptyScript:"";for(let p=0;p<h;p++)i.append(o[p],Tt()),Be.nextNode(),c.push({type:2,index:++s});i.append(o[h],Tt())}}}else if(i.nodeType===8)if(i.data===is)c.push({type:2,index:s});else{let o=-1;for(;(o=i.data.indexOf(De,o+1))!==-1;)c.push({type:7,index:s}),o+=De.length-1}s++}}static createElement(t,u){const r=Ve.createElement("template");return r.innerHTML=t,r}};function st(e,t,u=e,r){if(t===de)return t;let i=r!==void 0?u._$Co?.[r]:u._$Cl;const s=It(t)?void 0:t._$litDirective$;return i?.constructor!==s&&(i?._$AO?.(!1),s===void 0?i=void 0:(i=new s(e),i._$AT(e,u,r)),r!==void 0?(u._$Co??=[])[r]=i:u._$Cl=i),i!==void 0&&(t=st(e,i._$AS(e,t.values),i,r)),t}class ca{constructor(t,u){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=u}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:u},parts:r}=this._$AD,i=(t?.creationScope??Ve).importNode(u,!0);Be.currentNode=i;let s=Be.nextNode(),n=0,a=0,c=r[0];for(;c!==void 0;){if(n===c.index){let l;c.type===2?l=new dt(s,s.nextSibling,this,t):c.type===1?l=new c.ctor(s,c.name,c.strings,this,t):c.type===6&&(l=new ha(s,this,t)),this._$AV.push(l),c=r[++a]}n!==c?.index&&(s=Be.nextNode(),n++)}return Be.currentNode=Ve,i}p(t){let u=0;for(const r of this._$AV)r!==void 0&&(r.strings!==void 0?(r._$AI(t,r,u),u+=r.strings.length-2):r._$AI(t[u])),u++}}class dt{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,u,r,i){this.type=2,this._$AH=$,this._$AN=void 0,this._$AA=t,this._$AB=u,this._$AM=r,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const u=this._$AM;return u!==void 0&&t?.nodeType===11&&(t=u.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,u=this){t=st(this,t,u),It(t)?t===$||t==null||t===""?(this._$AH!==$&&this._$AR(),this._$AH=$):t!==this._$AH&&t!==de&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):na(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==$&&It(this._$AH)?this._$AA.nextSibling.data=t:this.T(Ve.createTextNode(t)),this._$AH=t}$(t){const{values:u,_$litType$:r}=t,i=typeof r=="number"?this._$AC(t):(r.el===void 0&&(r.el=sr.createElement(ns(r.h,r.h[0]),this.options)),r);if(this._$AH?._$AD===i)this._$AH.p(u);else{const s=new ca(i,this),n=s.u(this.options);s.p(u),this.T(n),this._$AH=s}}_$AC(t){let u=ci.get(t.strings);return u===void 0&&ci.set(t.strings,u=new sr(t)),u}k(t){wr(this._$AH)||(this._$AH=[],this._$AR());const u=this._$AH;let r,i=0;for(const s of t)i===u.length?u.push(r=new dt(this.O(Tt()),this.O(Tt()),this,this.options)):r=u[i],r._$AI(s),i++;i<u.length&&(this._$AR(r&&r._$AB.nextSibling,i),u.length=i)}_$AR(t=this._$AA.nextSibling,u){for(this._$AP?.(!1,!0,u);t!==this._$AB;){const r=ri(t).nextSibling;ri(t).remove(),t=r}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}}class bu{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,u,r,i,s){this.type=1,this._$AH=$,this._$AN=void 0,this.element=t,this.name=u,this._$AM=i,this.options=s,r.length>2||r[0]!==""||r[1]!==""?(this._$AH=Array(r.length-1).fill(new String),this.strings=r):this._$AH=$}_$AI(t,u=this,r,i){const s=this.strings;let n=!1;if(s===void 0)t=st(this,t,u,0),n=!It(t)||t!==this._$AH&&t!==de,n&&(this._$AH=t);else{const a=t;let c,l;for(t=s[0],c=0;c<s.length-1;c++)l=st(this,a[r+c],u,c),l===de&&(l=this._$AH[c]),n||=!It(l)||l!==this._$AH[c],l===$?t=$:t!==$&&(t+=(l??"")+s[c+1]),this._$AH[c]=l}n&&!i&&this.j(t)}j(t){t===$?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class la extends bu{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===$?void 0:t}}class da extends bu{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==$)}}class fa extends bu{constructor(t,u,r,i,s){super(t,u,r,i,s),this.type=5}_$AI(t,u=this){if((t=st(this,t,u,0)??$)===de)return;const r=this._$AH,i=t===$&&r!==$||t.capture!==r.capture||t.once!==r.once||t.passive!==r.passive,s=t!==$&&(r===$||i);i&&this.element.removeEventListener(this.name,this,r),s&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}let ha=class{constructor(t,u,r){this.element=t,this.type=6,this._$AN=void 0,this._$AM=u,this.options=r}get _$AU(){return this._$AM._$AU}_$AI(t){st(this,t)}};const pa={I:dt},ba=vr.litHtmlPolyfillSupport;ba?.(sr,dt),(vr.litHtmlVersions??=[]).push("3.3.2");const kr=(e,t,u)=>{const r=u?.renderBefore??t;let i=r._$litPart$;if(i===void 0){const s=u?.renderBefore??null;r._$litPart$=i=new dt(t.insertBefore(Tt(),s),s,void 0,u??{})}return i._$AI(e),i};const{I:ma}=pa,li=e=>e,ga=e=>e.strings===void 0,di=()=>document.createComment(""),mt=(e,t,u)=>{const r=e._$AA.parentNode,i=t===void 0?e._$AB:t._$AA;if(u===void 0){const s=r.insertBefore(di(),i),n=r.insertBefore(di(),i);u=new ma(s,n,e,e.options)}else{const s=u._$AB.nextSibling,n=u._$AM,a=n!==e;if(a){let c;u._$AQ?.(e),u._$AM=e,u._$AP!==void 0&&(c=e._$AU)!==n._$AU&&u._$AP(c)}if(s!==i||a){let c=u._$AA;for(;c!==s;){const l=li(c).nextSibling;li(r).insertBefore(c,i),c=l}}}return u},ze=(e,t,u=e)=>(e._$AI(t,u),e),_a={},ya=(e,t=_a)=>e._$AH=t,xa=e=>e._$AH,Su=e=>{e._$AR(),e._$AA.remove()};const Dt=(e,t)=>{const u=e._$AN;if(u===void 0)return!1;for(const r of u)r._$AO?.(t,!1),Dt(r,t);return!0},iu=e=>{let t,u;do{if((t=e._$AM)===void 0)break;u=t._$AN,u.delete(e),e=t}while(u?.size===0)},os=e=>{for(let t;t=e._$AM;e=t){let u=t._$AN;if(u===void 0)t._$AN=u=new Set;else if(u.has(e))break;u.add(e),ka(t)}};function va(e){this._$AN!==void 0?(iu(this),this._$AM=e,os(this)):this._$AM=e}function wa(e,t=!1,u=0){const r=this._$AH,i=this._$AN;if(i!==void 0&&i.size!==0)if(t)if(Array.isArray(r))for(let s=u;s<r.length;s++)Dt(r[s],!1),iu(r[s]);else r!=null&&(Dt(r,!1),iu(r));else Dt(this,e)}const ka=e=>{e.type==Mt.CHILD&&(e._$AP??=wa,e._$AQ??=va)};let Ca=class extends lt{constructor(){super(...arguments),this._$AN=void 0}_$AT(t,u,r){super._$AT(t,u,r),os(this),this.isConnected=t._$AU}_$AO(t,u=!0){t!==this.isConnected&&(this.isConnected=t,t?this.reconnected?.():this.disconnected?.()),u&&(Dt(this,t),iu(this))}setValue(t){if(ga(this._$Ct))this._$Ct._$AI(t,this);else{const u=[...this._$Ct._$AH];u[this._$Ci]=t,this._$Ct._$AI(u,this,0)}}disconnected(){}reconnected(){}};ge.State;ge.Computed;let cs=class extends Event{constructor(t,u,r,i){super("context-request",{bubbles:!0,composed:!0}),this.context=t,this.contextTarget=u,this.callback=r,this.subscribe=i??!1}};let fi=class{constructor(t,u,r,i){if(this.subscribe=!1,this.provided=!1,this.value=void 0,this.t=(s,n)=>{this.unsubscribe&&(this.unsubscribe!==n&&(this.provided=!1,this.unsubscribe()),this.subscribe||this.unsubscribe()),this.value=s,this.host.requestUpdate(),this.provided&&!this.subscribe||(this.provided=!0,this.callback&&this.callback(s,n)),this.unsubscribe=n},this.host=t,u.context!==void 0){const s=u;this.context=s.context,this.callback=s.callback,this.subscribe=s.subscribe??!1}else this.context=u,this.callback=r,this.subscribe=i??!1;this.host.addController(this)}hostConnected(){this.dispatchRequest()}hostDisconnected(){this.unsubscribe&&(this.unsubscribe(),this.unsubscribe=void 0)}dispatchRequest(){this.host.dispatchEvent(new cs(this.context,this.host,this.t,this.subscribe))}};let $a=class{get value(){return this.o}set value(t){this.setValue(t)}setValue(t,u=!1){const r=u||!Object.is(t,this.o);this.o=t,r&&this.updateObservers()}constructor(t){this.subscriptions=new Map,this.updateObservers=()=>{for(const[u,{disposer:r}]of this.subscriptions)u(this.o,r)},t!==void 0&&(this.value=t)}addCallback(t,u,r){if(!r)return void t(this.value);this.subscriptions.has(t)||this.subscriptions.set(t,{disposer:()=>{this.subscriptions.delete(t)},consumerHost:u});const{disposer:i}=this.subscriptions.get(t);t(this.value,i)}clearCallbacks(){this.subscriptions.clear()}};let Ea=class extends Event{constructor(t,u){super("context-provider",{bubbles:!0,composed:!0}),this.context=t,this.contextTarget=u}},hi=class extends $a{constructor(t,u,r){super(u.context!==void 0?u.initialValue:r),this.onContextRequest=i=>{if(i.context!==this.context)return;const s=i.contextTarget??i.composedPath()[0];s!==this.host&&(i.stopPropagation(),this.addCallback(i.callback,s,i.subscribe))},this.onProviderRequest=i=>{if(i.context!==this.context||(i.contextTarget??i.composedPath()[0])===this.host)return;const s=new Set;for(const[n,{consumerHost:a}]of this.subscriptions)s.has(n)||(s.add(n),a.dispatchEvent(new cs(this.context,a,n,!0)));i.stopPropagation()},this.host=t,u.context!==void 0?this.context=u.context:this.context=u,this.attachListeners(),this.host.addController?.(this)}attachListeners(){this.host.addEventListener("context-request",this.onContextRequest),this.host.addEventListener("context-provider",this.onProviderRequest)}hostConnected(){this.host.dispatchEvent(new Ea(this.context,this.host))}};function Aa({context:e}){return(t,u)=>{const r=new WeakMap;if(typeof u=="object")return{get(){return t.get.call(this)},set(i){return r.get(this).setValue(i),t.set.call(this,i)},init(i){return r.set(this,new hi(this,{context:e,initialValue:i})),i}};{t.constructor.addInitializer((n=>{r.set(n,new hi(n,{context:e}))}));const i=Object.getOwnPropertyDescriptor(t,u);let s;if(i===void 0){const n=new WeakMap;s={get(){return n.get(this)},set(a){r.get(this).setValue(a),n.set(this,a)},configurable:!0,enumerable:!0}}else{const n=i.set;s={...i,set(a){r.get(this).setValue(a),n?.call(this,a)}}}return void Object.defineProperty(t,u,s)}}}function Da({context:e,subscribe:t}){return(u,r)=>{typeof r=="object"?r.addInitializer((function(){new fi(this,{context:e,callback:i=>{u.set.call(this,i)},subscribe:t})})):u.constructor.addInitializer((i=>{new fi(i,{context:e,callback:s=>{i[r]=s},subscribe:t})}))}}const Qt=globalThis,Cr=Qt.ShadowRoot&&(Qt.ShadyCSS===void 0||Qt.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,$r=Symbol(),pi=new WeakMap;let ls=class{constructor(t,u,r){if(this._$cssResult$=!0,r!==$r)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=u}get styleSheet(){let t=this.o;const u=this.t;if(Cr&&t===void 0){const r=u!==void 0&&u.length===1;r&&(t=pi.get(u)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),r&&pi.set(u,t))}return t}toString(){return this.cssText}};const mu=e=>new ls(typeof e=="string"?e:e+"",void 0,$r),M=(e,...t)=>{const u=e.length===1?e[0]:t.reduce((r,i,s)=>r+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[s+1],e[0]);return new ls(u,e,$r)},Sa=(e,t)=>{if(Cr)e.adoptedStyleSheets=t.map(u=>u instanceof CSSStyleSheet?u:u.styleSheet);else for(const u of t){const r=document.createElement("style"),i=Qt.litNonce;i!==void 0&&r.setAttribute("nonce",i),r.textContent=u.cssText,e.appendChild(r)}},bi=Cr?e=>e:e=>e instanceof CSSStyleSheet?(t=>{let u="";for(const r of t.cssRules)u+=r.cssText;return mu(u)})(e):e;const{is:Fa,defineProperty:Ta,getOwnPropertyDescriptor:Ia,getOwnPropertyNames:Oa,getOwnPropertySymbols:Pa,getPrototypeOf:za}=Object,gu=globalThis,mi=gu.trustedTypes,Ra=mi?mi.emptyScript:"",Na=gu.reactiveElementPolyfillSupport,St=(e,t)=>e,su={toAttribute(e,t){switch(t){case Boolean:e=e?Ra:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let u=e;switch(t){case Boolean:u=e!==null;break;case Number:u=e===null?null:Number(e);break;case Object:case Array:try{u=JSON.parse(e)}catch{u=null}}return u}},Er=(e,t)=>!Fa(e,t),gi={attribute:!0,type:String,converter:su,reflect:!1,useDefault:!1,hasChanged:Er};Symbol.metadata??=Symbol("metadata"),gu.litPropertyMetadata??=new WeakMap;class Ye extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,u=gi){if(u.state&&(u.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((u=Object.create(u)).wrapped=!0),this.elementProperties.set(t,u),!u.noAccessor){const r=Symbol(),i=this.getPropertyDescriptor(t,r,u);i!==void 0&&Ta(this.prototype,t,i)}}static getPropertyDescriptor(t,u,r){const{get:i,set:s}=Ia(this.prototype,t)??{get(){return this[u]},set(n){this[u]=n}};return{get:i,set(n){const a=i?.call(this);s?.call(this,n),this.requestUpdate(t,a,r)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??gi}static _$Ei(){if(this.hasOwnProperty(St("elementProperties")))return;const t=za(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(St("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(St("properties"))){const u=this.properties,r=[...Oa(u),...Pa(u)];for(const i of r)this.createProperty(i,u[i])}const t=this[Symbol.metadata];if(t!==null){const u=litPropertyMetadata.get(t);if(u!==void 0)for(const[r,i]of u)this.elementProperties.set(r,i)}this._$Eh=new Map;for(const[u,r]of this.elementProperties){const i=this._$Eu(u,r);i!==void 0&&this._$Eh.set(i,u)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const u=[];if(Array.isArray(t)){const r=new Set(t.flat(1/0).reverse());for(const i of r)u.unshift(bi(i))}else t!==void 0&&u.push(bi(t));return u}static _$Eu(t,u){const r=u.attribute;return r===!1?void 0:typeof r=="string"?r:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,u=this.constructor.elementProperties;for(const r of u.keys())this.hasOwnProperty(r)&&(t.set(r,this[r]),delete this[r]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Sa(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,u,r){this._$AK(t,r)}_$ET(t,u){const r=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,r);if(i!==void 0&&r.reflect===!0){const s=(r.converter?.toAttribute!==void 0?r.converter:su).toAttribute(u,r.type);this._$Em=t,s==null?this.removeAttribute(i):this.setAttribute(i,s),this._$Em=null}}_$AK(t,u){const r=this.constructor,i=r._$Eh.get(t);if(i!==void 0&&this._$Em!==i){const s=r.getPropertyOptions(i),n=typeof s.converter=="function"?{fromAttribute:s.converter}:s.converter?.fromAttribute!==void 0?s.converter:su;this._$Em=i;const a=n.fromAttribute(u,s.type);this[i]=a??this._$Ej?.get(i)??a,this._$Em=null}}requestUpdate(t,u,r,i=!1,s){if(t!==void 0){const n=this.constructor;if(i===!1&&(s=this[t]),r??=n.getPropertyOptions(t),!((r.hasChanged??Er)(s,u)||r.useDefault&&r.reflect&&s===this._$Ej?.get(t)&&!this.hasAttribute(n._$Eu(t,r))))return;this.C(t,u,r)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,u,{useDefault:r,reflect:i,wrapped:s},n){r&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,n??u??this[t]),s!==!0||n!==void 0)||(this._$AL.has(t)||(this.hasUpdated||r||(u=void 0),this._$AL.set(t,u)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(u){Promise.reject(u)}const t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[i,s]of this._$Ep)this[i]=s;this._$Ep=void 0}const r=this.constructor.elementProperties;if(r.size>0)for(const[i,s]of r){const{wrapped:n}=s,a=this[i];n!==!0||this._$AL.has(i)||a===void 0||this.C(i,void 0,s,a)}}let t=!1;const u=this._$AL;try{t=this.shouldUpdate(u),t?(this.willUpdate(u),this._$EO?.forEach(r=>r.hostUpdate?.()),this.update(u)):this._$EM()}catch(r){throw t=!1,this._$EM(),r}t&&this._$AE(u)}willUpdate(t){}_$AE(t){this._$EO?.forEach(u=>u.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(u=>this._$ET(u,this[u])),this._$EM()}updated(t){}firstUpdated(t){}}Ye.elementStyles=[],Ye.shadowRootOptions={mode:"open"},Ye[St("elementProperties")]=new Map,Ye[St("finalized")]=new Map,Na?.({ReactiveElement:Ye}),(gu.reactiveElementVersions??=[]).push("2.1.2");const Ar=globalThis;let He=class extends Ye{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const u=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=kr(u,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return de}};He._$litElement$=!0,He.finalized=!0,Ar.litElementHydrateSupport?.({LitElement:He});const Ma=Ar.litElementPolyfillSupport;Ma?.({LitElement:He});(Ar.litElementVersions??=[]).push("4.2.2");const j=e=>(t,u)=>{u!==void 0?u.addInitializer(()=>{customElements.define(e,t)}):customElements.define(e,t)};const ja={attribute:!0,type:String,converter:su,reflect:!1,hasChanged:Er},La=(e=ja,t,u)=>{const{kind:r,metadata:i}=u;let s=globalThis.litPropertyMetadata.get(i);if(s===void 0&&globalThis.litPropertyMetadata.set(i,s=new Map),r==="setter"&&((e=Object.create(e)).wrapped=!0),s.set(u.name,e),r==="accessor"){const{name:n}=u;return{set(a){const c=t.get.call(this);t.set.call(this,a),this.requestUpdate(n,c,e,!0,a)},init(a){return a!==void 0&&this.C(n,void 0,e,a),a}}}if(r==="setter"){const{name:n}=u;return function(a){const c=this[n];t.call(this,a),this.requestUpdate(n,c,e,!0,a)}}throw Error("Unsupported decorator location: "+r)};function A(e){return(t,u)=>typeof u=="object"?La(e,t,u):((r,i,s)=>{const n=i.hasOwnProperty(s);return i.constructor.createProperty(s,r),n?Object.getOwnPropertyDescriptor(i,s):void 0})(e,t,u)}function Le(e){return A({...e,state:!0,attribute:!1})}const Ua=(e,t,u)=>(u.configurable=!0,u.enumerable=!0,Reflect.decorate&&typeof t!="object"&&Object.defineProperty(e,t,u),u);function Ba(e,t){return(u,r,i)=>{const s=n=>n.renderRoot?.querySelector(e)??null;return Ua(u,r,{get(){return s(this)}})}}function*qa(e,t){if(e!==void 0){let u=0;for(const r of e)yield t(r,u++)}}let Fu=!1,nu=new ge.subtle.Watcher(()=>{Fu||(Fu=!0,queueMicrotask(()=>{Fu=!1,Ha()}))});function Ha(){for(const e of nu.getPending())e.get();nu.watch()}function Va(e){let t=new ge.Computed(()=>e());return nu.watch(t),t.get(),()=>{nu.unwatch(t)}}const ds="A2UITheme",Wa=`
  &:not([disabled]) {
    cursor: pointer;
    opacity: var(--opacity, 0);
    transition: opacity var(--speed, 0.2s) cubic-bezier(0, 0, 0.3, 1);

    &:hover,
    &:focus {
      opacity: 1;
    }
  }`,Ja=`
  ${new Array(21).fill(0).map((e,t)=>`.behavior-ho-${t*5} {
          --opacity: ${t/20};
          ${Wa}
        }`).join(`
`)}

  .behavior-o-s {
    overflow: scroll;
  }

  .behavior-o-a {
    overflow: auto;
  }

  .behavior-o-h {
    overflow: hidden;
  }

  .behavior-sw-n {
    scrollbar-width: none;
  }
`,V=4,Za=`
  ${new Array(25).fill(0).map((e,t)=>`
        .border-bw-${t} { border-width: ${t}px; }
        .border-btw-${t} { border-top-width: ${t}px; }
        .border-bbw-${t} { border-bottom-width: ${t}px; }
        .border-blw-${t} { border-left-width: ${t}px; }
        .border-brw-${t} { border-right-width: ${t}px; }

        .border-ow-${t} { outline-width: ${t}px; }
        .border-br-${t} { border-radius: ${t*V}px; overflow: hidden;}`).join(`
`)}

  .border-br-50pc {
    border-radius: 50%;
  }

  .border-bs-s {
    border-style: solid;
  }
`,fs=[0,5,10,15,20,25,30,35,40,50,60,70,80,90,95,98,99,100];function ae(...e){const t={};for(const u of e)for(const[r,i]of Object.entries(u)){const s=r.split("-").with(-1,"").join("-"),n=Object.keys(t).filter(a=>a.startsWith(s));for(const a of n)delete t[a];t[r]=i}return t}function Ga(e,t,...u){const r=structuredClone(e);for(const i of u)for(const s of Object.keys(i)){const n=s.split("-").with(-1,"").join("-");for(const[a,c]of Object.entries(r)){if(t.includes(a))continue;let l=!1;for(let d=0;d<c.length;d++)c[d].startsWith(n)&&(l=!0,c[d]=s);l||c.push(s)}}return r}function he(e){return e.startsWith("nv")?`--nv-${e.slice(2)}`:`--${e[0]}-${e.slice(1)}`}const Ze=e=>`
    ${e.map(t=>{const u=Tu(t);return`.color-bc-${t} { border-color: light-dark(var(${he(t)}), var(${he(u)})); }`}).join(`
`)}

    ${e.map(t=>{const u=Tu(t),r=[`.color-bgc-${t} { background-color: light-dark(var(${he(t)}), var(${he(u)})); }`,`.color-bbgc-${t}::backdrop { background-color: light-dark(var(${he(t)}), var(${he(u)})); }`];for(let i=.1;i<1;i+=.1)r.push(`.color-bbgc-${t}_${(i*100).toFixed(0)}::backdrop {
            background-color: light-dark(oklch(from var(${he(t)}) l c h / calc(alpha * ${i.toFixed(1)})), oklch(from var(${he(u)}) l c h / calc(alpha * ${i.toFixed(1)})) );
          }
        `);return r.join(`
`)}).join(`
`)}

  ${e.map(t=>{const u=Tu(t);return`.color-c-${t} { color: light-dark(var(${he(t)}), var(${he(u)})); }`}).join(`
`)}
  `,Tu=e=>{const t=e.match(/^([a-z]+)(\d+)$/);if(!t)return e;const[,u,r]=t,s=100-parseInt(r,10),n=fs.reduce((a,c)=>Math.abs(c-s)<Math.abs(a-s)?c:a);return`${u}${n}`},Ge=e=>fs.map(t=>`${e}${t}`),Ka=[Ze(Ge("p")),Ze(Ge("s")),Ze(Ge("t")),Ze(Ge("n")),Ze(Ge("nv")),Ze(Ge("e")),`
    .color-bgc-transparent {
      background-color: transparent;
    }

    :host {
      color-scheme: var(--color-scheme);
    }
  `],Qa=`
  .g-icon {
    font-family: "Material Symbols Outlined", "Google Symbols";
    font-weight: normal;
    font-style: normal;
    font-display: optional;
    font-size: 20px;
    width: 1em;
    height: 1em;
    user-select: none;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    -webkit-font-feature-settings: "liga";
    -webkit-font-smoothing: antialiased;
    overflow: hidden;

    font-variation-settings: "FILL" 0, "wght" 300, "GRAD" 0, "opsz" 48,
      "ROND" 100;

    &.filled {
      font-variation-settings: "FILL" 1, "wght" 300, "GRAD" 0, "opsz" 48,
        "ROND" 100;
    }

    &.filled-heavy {
      font-variation-settings: "FILL" 1, "wght" 700, "GRAD" 0, "opsz" 48,
        "ROND" 100;
    }
  }
`,Ya=`
  :host {
    ${new Array(16).fill(0).map((e,t)=>`--g-${t+1}: ${(t+1)*V}px;`).join(`
`)}
  }

  ${new Array(49).fill(0).map((e,t)=>{const u=t-24,r=u<0?`n${Math.abs(u)}`:u.toString();return`
        .layout-p-${r} { --padding: ${u*V}px; padding: var(--padding); }
        .layout-pt-${r} { padding-top: ${u*V}px; }
        .layout-pr-${r} { padding-right: ${u*V}px; }
        .layout-pb-${r} { padding-bottom: ${u*V}px; }
        .layout-pl-${r} { padding-left: ${u*V}px; }

        .layout-m-${r} { --margin: ${u*V}px; margin: var(--margin); }
        .layout-mt-${r} { margin-top: ${u*V}px; }
        .layout-mr-${r} { margin-right: ${u*V}px; }
        .layout-mb-${r} { margin-bottom: ${u*V}px; }
        .layout-ml-${r} { margin-left: ${u*V}px; }

        .layout-t-${r} { top: ${u*V}px; }
        .layout-r-${r} { right: ${u*V}px; }
        .layout-b-${r} { bottom: ${u*V}px; }
        .layout-l-${r} { left: ${u*V}px; }`}).join(`
`)}

  ${new Array(25).fill(0).map((e,t)=>`
        .layout-g-${t} { gap: ${t*V}px; }`).join(`
`)}

  ${new Array(8).fill(0).map((e,t)=>`
        .layout-grd-col${t+1} { grid-template-columns: ${"1fr ".repeat(t+1).trim()}; }`).join(`
`)}

  .layout-pos-a {
    position: absolute;
  }

  .layout-pos-rel {
    position: relative;
  }

  .layout-dsp-none {
    display: none;
  }

  .layout-dsp-block {
    display: block;
  }

  .layout-dsp-grid {
    display: grid;
  }

  .layout-dsp-iflex {
    display: inline-flex;
  }

  .layout-dsp-flexvert {
    display: flex;
    flex-direction: column;
  }

  .layout-dsp-flexhor {
    display: flex;
    flex-direction: row;
  }

  .layout-fw-w {
    flex-wrap: wrap;
  }

  .layout-al-fs {
    align-items: start;
  }

  .layout-al-fe {
    align-items: end;
  }

  .layout-al-c {
    align-items: center;
  }

  .layout-as-n {
    align-self: normal;
  }

  .layout-js-c {
    justify-self: center;
  }

  .layout-sp-c {
    justify-content: center;
  }

  .layout-sp-ev {
    justify-content: space-evenly;
  }

  .layout-sp-bt {
    justify-content: space-between;
  }

  .layout-sp-s {
    justify-content: start;
  }

  .layout-sp-e {
    justify-content: end;
  }

  .layout-ji-e {
    justify-items: end;
  }

  .layout-r-none {
    resize: none;
  }

  .layout-fs-c {
    field-sizing: content;
  }

  .layout-fs-n {
    field-sizing: none;
  }

  .layout-flx-0 {
    flex: 0 0 auto;
  }

  .layout-flx-1 {
    flex: 1 0 auto;
  }

  .layout-c-s {
    contain: strict;
  }

  /** Widths **/

  ${new Array(10).fill(0).map((e,t)=>{const u=(t+1)*10;return`.layout-w-${u} { width: ${u}%; max-width: ${u}%; }`}).join(`
`)}

  ${new Array(16).fill(0).map((e,t)=>{const u=t*V;return`.layout-wp-${t} { width: ${u}px; }`}).join(`
`)}

  /** Heights **/

  ${new Array(10).fill(0).map((e,t)=>{const u=(t+1)*10;return`.layout-h-${u} { height: ${u}%; }`}).join(`
`)}

  ${new Array(16).fill(0).map((e,t)=>{const u=t*V;return`.layout-hp-${t} { height: ${u}px; }`}).join(`
`)}

  .layout-el-cv {
    & img,
    & video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      margin: 0;
    }
  }

  .layout-ar-sq {
    aspect-ratio: 1 / 1;
  }

  .layout-ex-fb {
    margin: calc(var(--padding) * -1) 0 0 calc(var(--padding) * -1);
    width: calc(100% + var(--padding) * 2);
    height: calc(100% + var(--padding) * 2);
  }
`,Xa=`
  ${new Array(21).fill(0).map((e,t)=>`.opacity-el-${t*5} { opacity: ${t/20}; }`).join(`
`)}
`,eo=`
  :host {
    --default-font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    --default-font-family-mono: "Courier New", Courier, monospace;
  }

  .typography-f-s {
    font-family: var(--font-family, var(--default-font-family));
    font-optical-sizing: auto;
    font-variation-settings: "slnt" 0, "wdth" 100, "GRAD" 0;
  }

  .typography-f-sf {
    font-family: var(--font-family-flex, var(--default-font-family));
    font-optical-sizing: auto;
  }

  .typography-f-c {
    font-family: var(--font-family-mono, var(--default-font-family));
    font-optical-sizing: auto;
    font-variation-settings: "slnt" 0, "wdth" 100, "GRAD" 0;
  }

  .typography-v-r {
    font-variation-settings: "slnt" 0, "wdth" 100, "GRAD" 0, "ROND" 100;
  }

  .typography-ta-s {
    text-align: start;
  }

  .typography-ta-c {
    text-align: center;
  }

  .typography-fs-n {
    font-style: normal;
  }

  .typography-fs-i {
    font-style: italic;
  }

  .typography-sz-ls {
    font-size: 11px;
    line-height: 16px;
  }

  .typography-sz-lm {
    font-size: 12px;
    line-height: 16px;
  }

  .typography-sz-ll {
    font-size: 14px;
    line-height: 20px;
  }

  .typography-sz-bs {
    font-size: 12px;
    line-height: 16px;
  }

  .typography-sz-bm {
    font-size: 14px;
    line-height: 20px;
  }

  .typography-sz-bl {
    font-size: 16px;
    line-height: 24px;
  }

  .typography-sz-ts {
    font-size: 14px;
    line-height: 20px;
  }

  .typography-sz-tm {
    font-size: 16px;
    line-height: 24px;
  }

  .typography-sz-tl {
    font-size: 22px;
    line-height: 28px;
  }

  .typography-sz-hs {
    font-size: 24px;
    line-height: 32px;
  }

  .typography-sz-hm {
    font-size: 28px;
    line-height: 36px;
  }

  .typography-sz-hl {
    font-size: 32px;
    line-height: 40px;
  }

  .typography-sz-ds {
    font-size: 36px;
    line-height: 44px;
  }

  .typography-sz-dm {
    font-size: 45px;
    line-height: 52px;
  }

  .typography-sz-dl {
    font-size: 57px;
    line-height: 64px;
  }

  .typography-ws-p {
    white-space: pre-line;
  }

  .typography-ws-nw {
    white-space: nowrap;
  }

  .typography-td-none {
    text-decoration: none;
  }

  /** Weights **/

  ${new Array(9).fill(0).map((e,t)=>{const u=(t+1)*100;return`.typography-w-${u} { font-weight: ${u}; }`}).join(`
`)}
`,Dr=[Ja,Za,Ka,Qa,Ya,Xa,eo].flat(1/0).join(`
`),J=mu(Dr);class to{constructor(){this.registry=new Map}register(t,u,r){if(!/^[a-zA-Z0-9]+$/.test(t))throw new Error(`[Registry] Invalid typeName '${t}'. Must be alphanumeric.`);this.registry.set(t,u);const i=r||`a2ui-custom-${t.toLowerCase()}`,s=customElements.getName(u);if(s){if(s!==i)throw new Error(`Component ${t} is already registered as ${s}, but requested as ${i}.`);return}customElements.get(i)||customElements.define(i,u)}get(t){return this.registry.get(t)}}const _i=new to;var Y=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0},xe=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0};let Z=(()=>{let e=[j("a2ui-root")],t,u=[],r,i=us(He),s=[],n,a=[],c=[],l,d=[],o=[],h,p=[],f=[],b,m=[],g=[],v,w=[],y=[],x,E=[],O=[],H,ee=[],Ee=[],Je;return class extends i{static{r=this}static{const D=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;n=[A()],l=[A()],h=[Da({context:ds})],b=[A({attribute:!1})],v=[A({attribute:!1})],x=[A()],H=[A()],Je=[A()],xe(this,null,n,{kind:"accessor",name:"surfaceId",static:!1,private:!1,access:{has:C=>"surfaceId"in C,get:C=>C.surfaceId,set:(C,_)=>{C.surfaceId=_}},metadata:D},a,c),xe(this,null,l,{kind:"accessor",name:"component",static:!1,private:!1,access:{has:C=>"component"in C,get:C=>C.component,set:(C,_)=>{C.component=_}},metadata:D},d,o),xe(this,null,h,{kind:"accessor",name:"theme",static:!1,private:!1,access:{has:C=>"theme"in C,get:C=>C.theme,set:(C,_)=>{C.theme=_}},metadata:D},p,f),xe(this,null,b,{kind:"accessor",name:"childComponents",static:!1,private:!1,access:{has:C=>"childComponents"in C,get:C=>C.childComponents,set:(C,_)=>{C.childComponents=_}},metadata:D},m,g),xe(this,null,v,{kind:"accessor",name:"processor",static:!1,private:!1,access:{has:C=>"processor"in C,get:C=>C.processor,set:(C,_)=>{C.processor=_}},metadata:D},w,y),xe(this,null,x,{kind:"accessor",name:"dataContextPath",static:!1,private:!1,access:{has:C=>"dataContextPath"in C,get:C=>C.dataContextPath,set:(C,_)=>{C.dataContextPath=_}},metadata:D},E,O),xe(this,null,H,{kind:"accessor",name:"enableCustomElements",static:!1,private:!1,access:{has:C=>"enableCustomElements"in C,get:C=>C.enableCustomElements,set:(C,_)=>{C.enableCustomElements=_}},metadata:D},ee,Ee),xe(this,null,Je,{kind:"setter",name:"weight",static:!1,private:!1,access:{has:C=>"weight"in C,set:(C,_)=>{C.weight=_}},metadata:D},null,s),xe(null,t={value:r},e,{kind:"class",name:r.name,metadata:D},null,u),r=t.value,D&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:D})}#e=(Y(this,s),Y(this,a,null));get surfaceId(){return this.#e}set surfaceId(D){this.#e=D}#u=(Y(this,c),Y(this,d,null));get component(){return this.#u}set component(D){this.#u=D}#r=(Y(this,o),Y(this,p,void 0));get theme(){return this.#r}set theme(D){this.#r=D}#t=(Y(this,f),Y(this,m,null));get childComponents(){return this.#t}set childComponents(D){this.#t=D}#i=(Y(this,g),Y(this,w,null));get processor(){return this.#i}set processor(D){this.#i=D}#a=(Y(this,y),Y(this,E,""));get dataContextPath(){return this.#a}set dataContextPath(D){this.#a=D}#s=(Y(this,O),Y(this,ee,!1));get enableCustomElements(){return this.#s}set enableCustomElements(D){this.#s=D}set weight(D){this.#o=D,this.style.setProperty("--weight",`${D}`)}get weight(){return this.#o}#o=(Y(this,Ee),1);static{this.styles=[J,M`
      :host {
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 80%;
      }
    `]}#n=null;willUpdate(D){D.has("childComponents")&&(this.#n&&this.#n(),this.#n=Va(()=>{const C=this.childComponents??null,_=this.renderComponentTree(C);kr(_,this,{host:this})}))}disconnectedCallback(){super.disconnectedCallback(),this.#n&&this.#n()}renderComponentTree(D){return!D||!Array.isArray(D)?$:k` ${qa(D,C=>{if(this.enableCustomElements){const R=_i.get(C.type)||customElements.get(C.type);if(R){const L=C,te=new R;te.id=L.id,L.slotName&&(te.slot=L.slotName),te.component=L,te.weight=L.weight??"initial",te.processor=this.processor,te.surfaceId=this.surfaceId,te.dataContextPath=L.dataContextPath??"/";for(const[ku,zn]of Object.entries(C.properties))te[ku]=zn;return k`${te}`}}switch(C.type){case"List":{const _=C,R=_.properties.children;return k`<a2ui-list
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .direction=${_.properties.direction??"vertical"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .childComponents=${R}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-list>`}case"Card":{const _=C;let R=_.properties.children;return!R&&_.properties.child&&(R=[_.properties.child]),k`<a2ui-card
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .childComponents=${R}
            .dataContextPath=${_.dataContextPath??""}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-card>`}case"Column":{const _=C;return k`<a2ui-column
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .childComponents=${_.properties.children??null}
            .dataContextPath=${_.dataContextPath??""}
            .alignment=${_.properties.alignment??"stretch"}
            .distribution=${_.properties.distribution??"start"}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-column>`}case"Row":{const _=C;return k`<a2ui-row
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .childComponents=${_.properties.children??null}
            .dataContextPath=${_.dataContextPath??""}
            .alignment=${_.properties.alignment??"stretch"}
            .distribution=${_.properties.distribution??"start"}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-row>`}case"Image":{const _=C;return k`<a2ui-image
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .url=${_.properties.url??null}
            .dataContextPath=${_.dataContextPath??""}
            .usageHint=${_.properties.usageHint}
            .fit=${_.properties.fit}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-image>`}case"Icon":{const _=C;return k`<a2ui-icon
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .name=${_.properties.name??null}
            .dataContextPath=${_.dataContextPath??""}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-icon>`}case"AudioPlayer":{const _=C;return k`<a2ui-audioplayer
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .url=${_.properties.url??null}
            .dataContextPath=${_.dataContextPath??""}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-audioplayer>`}case"Button":{const _=C;return k`<a2ui-button
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath??""}
            .action=${_.properties.action}
            .childComponents=${[_.properties.child]}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-button>`}case"Text":{const _=C;return k`<a2ui-text
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .model=${this.processor}
            .surfaceId=${this.surfaceId}
            .processor=${this.processor}
            .dataContextPath=${_.dataContextPath}
            .text=${_.properties.text}
            .usageHint=${_.properties.usageHint}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-text>`}case"CheckBox":{const _=C;return k`<a2ui-checkbox
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath??""}
            .label=${_.properties.label}
            .value=${_.properties.value}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-checkbox>`}case"DateTimeInput":{const _=C;return k`<a2ui-datetimeinput
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath??""}
            .enableDate=${_.properties.enableDate??!0}
            .enableTime=${_.properties.enableTime??!0}
            .outputFormat=${_.properties.outputFormat}
            .value=${_.properties.value}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-datetimeinput>`}case"Divider":{const _=C;return k`<a2ui-divider
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath}
            .thickness=${_.properties.thickness}
            .axis=${_.properties.axis}
            .color=${_.properties.color}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-divider>`}case"MultipleChoice":{const _=C;return k`<a2ui-multiplechoice
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath}
            .options=${_.properties.options}
            .maxAllowedSelections=${_.properties.maxAllowedSelections}
            .selections=${_.properties.selections}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-multiplechoice>`}case"Slider":{const _=C;return k`<a2ui-slider
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath}
            .value=${_.properties.value}
            .minValue=${_.properties.minValue}
            .maxValue=${_.properties.maxValue}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-slider>`}case"TextField":{const _=C;return k`<a2ui-textfield
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath}
            .label=${_.properties.label}
            .text=${_.properties.text}
            .type=${_.properties.type}
            .validationRegexp=${_.properties.validationRegexp}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-textfield>`}case"Video":{const _=C;return k`<a2ui-video
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath}
            .url=${_.properties.url}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-video>`}case"Tabs":{const _=C,R=[],L=[];if(_.properties.tabItems)for(const te of _.properties.tabItems)R.push(te.title),L.push(te.child);return k`<a2ui-tabs
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath}
            .titles=${R}
            .childComponents=${L}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-tabs>`}case"Modal":{const _=C,R=[_.properties.entryPointChild,_.properties.contentChild];return _.properties.entryPointChild.slotName="entry",k`<a2ui-modal
            id=${_.id}
            slot=${_.slotName?_.slotName:$}
            .component=${_}
            .weight=${_.weight??"initial"}
            .processor=${this.processor}
            .surfaceId=${this.surfaceId}
            .dataContextPath=${_.dataContextPath}
            .childComponents=${R}
            .enableCustomElements=${this.enableCustomElements}
          ></a2ui-modal>`}default:return this.renderCustomComponent(C)}})}`}renderCustomComponent(D){if(!this.enableCustomElements)return;const C=D,R=_i.get(D.type)||customElements.get(D.type);if(!R)return k`Unknown element ${D.type}`;const L=new R;L.id=C.id,C.slotName&&(L.slot=C.slotName),L.component=C,L.weight=C.weight??"initial",L.processor=this.processor,L.surfaceId=this.surfaceId,L.dataContextPath=C.dataContextPath??"/";for(const[te,ku]of Object.entries(D.properties))L[te]=ku;return k`${L}`}render(){return k`<slot></slot>`}static{Y(r,u)}},r})();const T=ct(class extends lt{constructor(e){if(super(e),e.type!==Mt.ATTRIBUTE||e.name!=="class"||e.strings?.length>2)throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.")}render(e){return" "+Object.keys(e).filter(t=>e[t]).join(" ")+" "}update(e,[t]){if(this.st===void 0){this.st=new Set,e.strings!==void 0&&(this.nt=new Set(e.strings.join(" ").split(/\s/).filter(r=>r!=="")));for(const r in t)t[r]&&!this.nt?.has(r)&&this.st.add(r);return this.render(t)}const u=e.element.classList;for(const r of this.st)r in t||(u.remove(r),this.st.delete(r));for(const r in t){const i=!!t[r];i===this.st.has(r)||this.nt?.has(r)||(i?(u.add(r),this.st.add(r)):(u.remove(r),this.st.delete(r)))}return de}});function uo(e){return F(e)&&"key"in e}function hs(e,t){return e==="path"&&typeof t=="string"}function F(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)}function ps(e){return F(e)?"explicitList"in e||"template"in e:!1}function $e(e){return F(e)&&("path"in e||"literal"in e&&typeof e.literal=="string"||"literalString"in e)}function ro(e){return F(e)&&("path"in e||"literal"in e&&typeof e.literal=="number"||"literalNumber"in e)}function io(e){return F(e)&&("path"in e||"literal"in e&&typeof e.literal=="boolean"||"literalBoolean"in e)}function Ce(e){return!(!F(e)||!("id"in e&&"type"in e&&"properties"in e))}function bs(e){return F(e)&&"url"in e&&$e(e.url)}function ms(e){return F(e)&&"child"in e&&Ce(e.child)&&"action"in e}function gs(e){return F(e)?"child"in e?Ce(e.child):"children"in e?Array.isArray(e.children)&&e.children.every(Ce):!1:!1}function _s(e){return F(e)&&"label"in e&&$e(e.label)&&"value"in e&&io(e.value)}function ys(e){return F(e)&&"children"in e&&Array.isArray(e.children)&&e.children.every(Ce)}function xs(e){return F(e)&&"value"in e&&$e(e.value)}function vs(e){return F(e)}function ws(e){return F(e)&&"url"in e&&$e(e.url)}function ks(e){return F(e)&&"name"in e&&$e(e.name)}function Cs(e){return F(e)&&"children"in e&&Array.isArray(e.children)&&e.children.every(Ce)}function $s(e){return F(e)&&"entryPointChild"in e&&Ce(e.entryPointChild)&&"contentChild"in e&&Ce(e.contentChild)}function Es(e){return F(e)&&"selections"in e}function As(e){return F(e)&&"children"in e&&Array.isArray(e.children)&&e.children.every(Ce)}function Ds(e){return F(e)&&"value"in e&&ro(e.value)}function so(e){return F(e)&&"title"in e&&$e(e.title)&&"child"in e&&Ce(e.child)}function Ss(e){return F(e)&&"tabItems"in e&&Array.isArray(e.tabItems)&&e.tabItems.every(so)}function Fs(e){return F(e)&&"text"in e&&$e(e.text)}function Ts(e){return F(e)&&"label"in e&&$e(e.label)}function Is(e){return F(e)&&"url"in e&&$e(e.url)}const no=Object.freeze(Object.defineProperty({__proto__:null,isComponentArrayReference:ps,isObject:F,isPath:hs,isResolvedAudioPlayer:bs,isResolvedButton:ms,isResolvedCard:gs,isResolvedCheckbox:_s,isResolvedColumn:ys,isResolvedDateTimeInput:xs,isResolvedDivider:vs,isResolvedIcon:ks,isResolvedImage:ws,isResolvedList:Cs,isResolvedModal:$s,isResolvedMultipleChoice:Es,isResolvedRow:As,isResolvedSlider:Ds,isResolvedTabs:Ss,isResolvedText:Fs,isResolvedTextField:Ts,isResolvedVideo:Is,isValueMap:uo},Symbol.toStringTag,{value:"Module"}));class N{static{this.DEFAULT_SURFACE_ID="@default"}#e=Map;#u=Array;#r=Set;#t=Object;#i;constructor(t={mapCtor:Map,arrayCtor:Array,setCtor:Set,objCtor:Object}){this.opts=t,this.#u=t.arrayCtor,this.#e=t.mapCtor,this.#r=t.setCtor,this.#t=t.objCtor,this.#i=new t.mapCtor}getSurfaces(){return this.#i}clearSurfaces(){this.#i.clear()}processMessages(t){for(const u of t)u.beginRendering&&this.#b(u.beginRendering,u.beginRendering.surfaceId),u.surfaceUpdate&&this.#m(u.surfaceUpdate,u.surfaceUpdate.surfaceId),u.dataModelUpdate&&this.#g(u.dataModelUpdate,u.dataModelUpdate.surfaceId),u.deleteSurface&&this.#_(u.deleteSurface)}getData(t,u,r=N.DEFAULT_SURFACE_ID){const i=this.#l(r);if(!i)return null;let s;return u==="."||u===""?s=t.dataContextPath??"/":s=this.resolvePath(u,t.dataContextPath),this.#c(i.dataModel,s)}setData(t,u,r,i=N.DEFAULT_SURFACE_ID){if(!t){console.warn("No component node set");return}const s=this.#l(i);if(!s)return;let n;u==="."||u===""?n=t.dataContextPath??"/":n=this.resolvePath(u,t.dataContextPath),this.#o(s.dataModel,n,r)}resolvePath(t,u){return t.startsWith("/")?t:u&&u!=="/"?u.endsWith("/")?`${u}${t}`:`${u}/${t}`:`/${t}`}#a(t){if(typeof t!="string")return t;const u=t.trim();if(u.startsWith("{")&&u.endsWith("}")||u.startsWith("[")&&u.endsWith("]"))try{return JSON.parse(t)}catch(r){return console.warn(`Failed to parse potential JSON string: "${t.substring(0,50)}..."`,r),t}return t}#s(t){const u=new this.#e;for(const r of t){if(!F(r)||!("key"in r))continue;const i=r.key,s=this.#p(r);if(!s)continue;let n=r[s];s==="valueMap"&&Array.isArray(n)?n=this.#s(n):typeof n=="string"&&(n=this.#a(n)),this.#o(u,i,n)}return u}#o(t,u,r){if(Array.isArray(r)&&(r.length===0||F(r[0])&&"key"in r[0]))if(r.length===1&&F(r[0])&&r[0].key==="."){const c=r[0],l=this.#p(c);l?(r=c[l],l==="valueMap"&&Array.isArray(r)?r=this.#s(r):typeof r=="string"&&(r=this.#a(r))):r=this.#s(r)}else r=this.#s(r);const i=this.#n(u).split("/").filter(c=>c);if(i.length===0){if(r instanceof Map||F(r)){!(r instanceof Map)&&F(r)&&(r=new this.#e(Object.entries(r))),t.clear();for(const[c,l]of r.entries())t.set(c,l)}else console.error("Cannot set root of DataModel to a non-Map value.");return}let s=t;for(let c=0;c<i.length-1;c++){const l=i[c];let d;s instanceof Map?d=s.get(l):Array.isArray(s)&&/^\d+$/.test(l)&&(d=s[parseInt(l,10)]),(d===void 0||typeof d!="object"||d===null)&&(d=new this.#e,s instanceof this.#e?s.set(l,d):Array.isArray(s)&&(s[parseInt(l,10)]=d)),s=d}const n=i[i.length-1],a=r;s instanceof this.#e?s.set(n,a):Array.isArray(s)&&/^\d+$/.test(n)&&(s[parseInt(n,10)]=a)}#n(t){return"/"+t.replace(/\[(\d+)\]/g,".$1").split(".").filter(i=>i.length>0).join("/")}#c(t,u){const r=this.#n(u).split("/").filter(s=>s);let i=t;for(const s of r){if(i==null)return null;if(i instanceof Map)i=i.get(s);else if(Array.isArray(i)&&/^\d+$/.test(s))i=i[parseInt(s,10)];else if(F(i))i=i[s];else return null}return i}#l(t){let u=this.#i.get(t);return u||(u=new this.#t({rootComponentId:null,componentTree:null,dataModel:new this.#e,components:new this.#e,styles:new this.#t}),this.#i.set(t,u)),u}#b(t,u){const r=this.#l(u);r.rootComponentId=t.root,r.styles=t.styles??{},this.#f(r)}#m(t,u){const r=this.#l(u);for(const i of t.components)r.components.set(i.id,i);this.#f(r)}#g(t,u){const r=this.#l(u),i=t.path??"/";this.#o(r.dataModel,i,t.contents),this.#f(r)}#_(t){this.#i.delete(t.surfaceId)}#f(t){if(!t.rootComponentId){t.componentTree=null;return}const u=new this.#r;t.componentTree=this.#d(t.rootComponentId,t,u,"/","")}#p(t){return Object.keys(t).find(u=>u.startsWith("value"))}#d(t,u,r,i,s=""){const n=`${t}${s}`,{components:a}=u;if(!a.has(t))return null;if(r.has(n))throw new Error(`Circular dependency for component "${n}".`);r.add(n);const c=a.get(t),l=c.component??{},d=Object.keys(l)[0],o=l[d],h=new this.#t;if(F(o))for(const[f,b]of Object.entries(o))h[f]=this.#h(b,u,r,i,s);r.delete(n);const p={id:n,dataContextPath:i,weight:c.weight??"initial"};switch(d){case"Text":if(!Fs(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Text",properties:h});case"Image":if(!ws(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Image",properties:h});case"Icon":if(!ks(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Icon",properties:h});case"Video":if(!Is(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Video",properties:h});case"AudioPlayer":if(!bs(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"AudioPlayer",properties:h});case"Row":if(!As(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Row",properties:h});case"Column":if(!ys(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Column",properties:h});case"List":if(!Cs(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"List",properties:h});case"Card":if(!gs(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Card",properties:h});case"Tabs":if(!Ss(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Tabs",properties:h});case"Divider":if(!vs(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Divider",properties:h});case"Modal":if(!$s(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Modal",properties:h});case"Button":if(!ms(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Button",properties:h});case"CheckBox":if(!_s(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"CheckBox",properties:h});case"TextField":if(!Ts(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"TextField",properties:h});case"DateTimeInput":if(!xs(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"DateTimeInput",properties:h});case"MultipleChoice":if(!Es(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"MultipleChoice",properties:h});case"Slider":if(!Ds(h))throw new Error(`Invalid data; expected ${d}`);return new this.#t({...p,type:"Slider",properties:h});default:return new this.#t({...p,type:d,properties:h})}}#h(t,u,r,i,s=""){if(typeof t=="string"&&u.components.has(t))return this.#d(t,u,r,i,s);if(ps(t)){if(t.explicitList)return t.explicitList.map(n=>this.#d(n,u,r,i,s));if(t.template){const n=this.resolvePath(t.template.dataBinding,i),a=this.#c(u.dataModel,n),c=t.template;if(Array.isArray(a))return a.map((d,o)=>{const f=`:${[...i.split("/").filter(m=>/^\d+$/.test(m)),o].join(":")}`,b=`${n}/${o}`;return this.#d(c.componentId,u,r,b,f)});const l=this.#e;return a instanceof l?Array.from(a.keys(),d=>{const o=`:${d}`,h=`${n}/${d}`;return this.#d(c.componentId,u,r,h,o)}):new this.#u}}if(Array.isArray(t))return t.map(n=>this.#h(n,u,r,i,s));if(F(t)){const n=new this.#t;for(const[a,c]of Object.entries(t)){let l=c;if(hs(a,c)&&i!=="/"){l=c.replace(/^\.?\/item/,"").replace(/^\.?\/text/,"").replace(/^\.?\/label/,"").replace(/^\.?\//,""),n[a]=l;continue}n[a]=this.#h(l,u,r,i,s)}return n}return t}}const Os="important",ao=" !"+Os,q=ct(class extends lt{constructor(e){if(super(e),e.type!==Mt.ATTRIBUTE||e.name!=="style"||e.strings?.length>2)throw Error("The `styleMap` directive must be used in the `style` attribute and must be the only part in the attribute.")}render(e){return Object.keys(e).reduce((t,u)=>{const r=e[u];return r==null?t:t+`${u=u.includes("-")?u:u.replace(/(?:^(webkit|moz|ms|o)|)(?=[A-Z])/g,"-$&").toLowerCase()}:${r};`},"")}update(e,[t]){const{style:u}=e.element;if(this.ft===void 0)return this.ft=new Set(Object.keys(t)),this.render(t);for(const r of this.ft)t[r]==null&&(this.ft.delete(r),r.includes("-")?u.removeProperty(r):u[r]=null);for(const r in t){const i=t[r];if(i!=null){this.ft.add(r);const s=typeof i=="string"&&i.endsWith(ao);r.includes("-")||s?u.setProperty(r,s?i.slice(0,-11):i,s?Os:""):u[r]=i}}return de}});var yi=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Iu=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-audioplayer")],t,u=[],r,i=Z,s,n=[],a=[];return class extends i{static{r=this}static{const c=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],yi(this,null,s,{kind:"accessor",name:"url",static:!1,private:!1,access:{has:l=>"url"in l,get:l=>l.url,set:(l,d)=>{l.url=d}},metadata:c},n,a),yi(null,t={value:r},e,{kind:"class",name:r.name,metadata:c},null,u),r=t.value,c&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:c})}#e=Iu(this,n,null);get url(){return this.#e}set url(c){this.#e=c}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      audio {
        display: block;
        width: 100%;
      }
    `]}#u(){if(!this.url)return $;if(this.url&&typeof this.url=="object"){if("literalString"in this.url)return k`<audio controls src=${this.url.literalString} />`;if("literal"in this.url)return k`<audio controls src=${this.url.literal} />`;if(this.url&&"path"in this.url&&this.url.path){if(!this.processor||!this.component)return k`(no processor)`;const c=this.processor.getData(this.component,this.url.path,this.surfaceId??N.DEFAULT_SURFACE_ID);return c?typeof c!="string"?k`Invalid audio URL`:k`<audio controls src=${c} />`:k`Invalid audio URL`}}return k`(empty)`}render(){return k`<section
      class=${T(this.theme.components.AudioPlayer)}
      style=${this.theme.additionalStyles?.AudioPlayer?q(this.theme.additionalStyles?.AudioPlayer):$}
    >
      ${this.#u()}
    </section>`}constructor(){super(...arguments),Iu(this,a)}static{Iu(r,u)}},r})();const oo={bubbles:!0,cancelable:!0,composed:!0};class Sr extends CustomEvent{static{this.eventName="a2uiaction"}constructor(t){super(Sr.eventName,{detail:t,...oo}),this.payload=t}}var xi=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Ou=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-button")],t,u=[],r,i=Z,s,n=[],a=[];return class extends i{static{r=this}static{const c=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],xi(this,null,s,{kind:"accessor",name:"action",static:!1,private:!1,access:{has:l=>"action"in l,get:l=>l.action,set:(l,d)=>{l.action=d}},metadata:c},n,a),xi(null,t={value:r},e,{kind:"class",name:r.name,metadata:c},null,u),r=t.value,c&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:c})}#e=Ou(this,n,null);get action(){return this.#e}set action(c){this.#e=c}static{this.styles=[J,M`
      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
      }
    `]}render(){return k`<button
      class=${T(this.theme.components.Button)}
      style=${this.theme.additionalStyles?.Button?q(this.theme.additionalStyles?.Button):$}
      @click=${()=>{if(!this.action)return;const c=new Sr({eventType:"a2ui.action",action:this.action,dataContextPath:this.dataContextPath,sourceComponentId:this.id,sourceComponent:this.component});this.dispatchEvent(c)}}
    >
      <slot></slot>
    </button>`}constructor(){super(...arguments),Ou(this,a)}static{Ou(r,u)}},r})();var co=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},lo=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-card")],t,u=[],r,i=Z;return class extends i{static{r=this}static{const s=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;co(null,t={value:r},e,{kind:"class",name:r.name,metadata:s},null,u),r=t.value,s&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:s})}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      section {
        height: 100%;
        width: 100%;
        min-height: 0;
        overflow: auto;

        ::slotted(*) {
          height: 100%;
          width: 100%;
        }
      }
    `]}render(){return k` <section
      class=${T(this.theme.components.Card)}
      style=${this.theme.additionalStyles?.Card?q(this.theme.additionalStyles?.Card):$}
    >
      <slot></slot>
    </section>`}static{lo(r,u)}},r})();var Pu=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},gt=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-checkbox")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[];return class extends i{static{r=this}static{const o=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],Pu(this,null,s,{kind:"accessor",name:"value",static:!1,private:!1,access:{has:h=>"value"in h,get:h=>h.value,set:(h,p)=>{h.value=p}},metadata:o},n,a),Pu(this,null,c,{kind:"accessor",name:"label",static:!1,private:!1,access:{has:h=>"label"in h,get:h=>h.label,set:(h,p)=>{h.label=p}},metadata:o},l,d),Pu(null,t={value:r},e,{kind:"class",name:r.name,metadata:o},null,u),r=t.value,o&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:o})}#e=gt(this,n,null);get value(){return this.#e}set value(o){this.#e=o}#u=(gt(this,a),gt(this,l,null));get label(){return this.#u}set label(o){this.#u=o}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      input {
        display: block;
        width: 100%;
      }

      .description {
        font-size: 14px;
        margin-bottom: 4px;
      }
    `]}#r(o){!this.value||!this.processor||"path"in this.value&&this.value.path&&this.processor.setData(this.component,this.value.path,o,this.surfaceId??N.DEFAULT_SURFACE_ID)}#t(o){return k` <section
      class=${T(this.theme.components.CheckBox.container)}
      style=${this.theme.additionalStyles?.CheckBox?q(this.theme.additionalStyles?.CheckBox):$}
    >
      <input
        class=${T(this.theme.components.CheckBox.element)}
        autocomplete="off"
        @input=${h=>{h.target instanceof HTMLInputElement&&this.#r(h.target.value)}}
        id="data"
        type="checkbox"
        .value=${o}
      />
      <label class=${T(this.theme.components.CheckBox.label)} for="data"
        >${this.label?.literalString}</label
      >
    </section>`}render(){if(this.value&&typeof this.value=="object"){if("literalBoolean"in this.value&&this.value.literalBoolean)return this.#t(this.value.literalBoolean);if("literal"in this.value&&this.value.literal!==void 0)return this.#t(this.value.literal);if(this.value&&"path"in this.value&&this.value.path){if(!this.processor||!this.component)return k`(no model)`;const o=this.processor.getData(this.component,this.value.path,this.surfaceId??N.DEFAULT_SURFACE_ID);return o===null?k`Invalid label`:typeof o!="boolean"?k`Invalid label`:this.#t(o)}}return $}constructor(){super(...arguments),gt(this,d)}static{gt(r,u)}},r})();var zu=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},_t=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-column")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[];return class extends i{static{r=this}static{const o=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A({reflect:!0,type:String})],c=[A({reflect:!0,type:String})],zu(this,null,s,{kind:"accessor",name:"alignment",static:!1,private:!1,access:{has:h=>"alignment"in h,get:h=>h.alignment,set:(h,p)=>{h.alignment=p}},metadata:o},n,a),zu(this,null,c,{kind:"accessor",name:"distribution",static:!1,private:!1,access:{has:h=>"distribution"in h,get:h=>h.distribution,set:(h,p)=>{h.distribution=p}},metadata:o},l,d),zu(null,t={value:r},e,{kind:"class",name:r.name,metadata:o},null,u),r=t.value,o&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:o})}#e=_t(this,n,"stretch");get alignment(){return this.#e}set alignment(o){this.#e=o}#u=(_t(this,a),_t(this,l,"start"));get distribution(){return this.#u}set distribution(o){this.#u=o}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: flex;
        flex: var(--weight);
      }

      section {
        display: flex;
        flex-direction: column;
        min-width: 100%;
        height: 100%;
      }

      :host([alignment="start"]) section {
        align-items: start;
      }

      :host([alignment="center"]) section {
        align-items: center;
      }

      :host([alignment="end"]) section {
        align-items: end;
      }

      :host([alignment="stretch"]) section {
        align-items: stretch;
      }

      :host([distribution="start"]) section {
        justify-content: start;
      }

      :host([distribution="center"]) section {
        justify-content: center;
      }

      :host([distribution="end"]) section {
        justify-content: end;
      }

      :host([distribution="spaceBetween"]) section {
        justify-content: space-between;
      }

      :host([distribution="spaceAround"]) section {
        justify-content: space-around;
      }

      :host([distribution="spaceEvenly"]) section {
        justify-content: space-evenly;
      }
    `]}render(){return k`<section
      class=${T(this.theme.components.Column)}
      style=${this.theme.additionalStyles?.Column?q(this.theme.additionalStyles?.Column):$}
    >
      <slot></slot>
    </section>`}constructor(){super(...arguments),_t(this,d)}static{_t(r,u)}},r})();var yt=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},ve=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-datetimeinput")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[],o,h=[],p=[],f,b=[],m=[];return class extends i{static{r=this}static{const g=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],o=[A({reflect:!1,type:Boolean})],f=[A({reflect:!1,type:Boolean})],yt(this,null,s,{kind:"accessor",name:"value",static:!1,private:!1,access:{has:v=>"value"in v,get:v=>v.value,set:(v,w)=>{v.value=w}},metadata:g},n,a),yt(this,null,c,{kind:"accessor",name:"label",static:!1,private:!1,access:{has:v=>"label"in v,get:v=>v.label,set:(v,w)=>{v.label=w}},metadata:g},l,d),yt(this,null,o,{kind:"accessor",name:"enableDate",static:!1,private:!1,access:{has:v=>"enableDate"in v,get:v=>v.enableDate,set:(v,w)=>{v.enableDate=w}},metadata:g},h,p),yt(this,null,f,{kind:"accessor",name:"enableTime",static:!1,private:!1,access:{has:v=>"enableTime"in v,get:v=>v.enableTime,set:(v,w)=>{v.enableTime=w}},metadata:g},b,m),yt(null,t={value:r},e,{kind:"class",name:r.name,metadata:g},null,u),r=t.value,g&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:g})}#e=ve(this,n,null);get value(){return this.#e}set value(g){this.#e=g}#u=(ve(this,a),ve(this,l,null));get label(){return this.#u}set label(g){this.#u=g}#r=(ve(this,d),ve(this,h,!0));get enableDate(){return this.#r}set enableDate(g){this.#r=g}#t=(ve(this,p),ve(this,b,!0));get enableTime(){return this.#t}set enableTime(g){this.#t=g}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      input {
        display: block;
        border-radius: 8px;
        padding: 8px;
        border: 1px solid #ccc;
        width: 100%;
      }
    `]}#i(g){!this.value||!this.processor||"path"in this.value&&this.value.path&&this.processor.setData(this.component,this.value.path,g,this.surfaceId??N.DEFAULT_SURFACE_ID)}#a(g){return k`<section
      class=${T(this.theme.components.DateTimeInput.container)}
    >
      <label
        for="data"
        class=${T(this.theme.components.DateTimeInput.label)}
        >${this.#c()}</label
      >
      <input
        autocomplete="off"
        class=${T(this.theme.components.DateTimeInput.element)}
        style=${this.theme.additionalStyles?.DateTimeInput?q(this.theme.additionalStyles?.DateTimeInput):$}
        @input=${v=>{v.target instanceof HTMLInputElement&&this.#i(v.target.value)}}
        id="data"
        name="data"
        .value=${this.#o(g)}
        .placeholder=${this.#c()}
        .type=${this.#s()}
      />
    </section>`}#s(){return this.enableDate&&this.enableTime?"datetime-local":this.enableDate?"date":this.enableTime?"time":"datetime-local"}#o(g){const v=this.#s(),w=g?new Date(g):null;if(!w||isNaN(w.getTime()))return"";const y=this.#n(w.getFullYear()),x=this.#n(w.getMonth()),E=this.#n(w.getDate()),O=this.#n(w.getHours()),H=this.#n(w.getMinutes());return v==="date"?`${y}-${x}-${E}`:v==="time"?`${O}:${H}`:`${y}-${x}-${E}T${O}:${H}`}#n(g){return g.toString().padStart(2,"0")}#c(){const g=this.#s();return g==="date"?"Date":g==="time"?"Time":"Date & Time"}render(){if(this.value&&typeof this.value=="object"){if("literalString"in this.value&&this.value.literalString)return this.#a(this.value.literalString);if("literal"in this.value&&this.value.literal!==void 0)return this.#a(this.value.literal);if(this.value&&"path"in this.value&&this.value.path){if(!this.processor||!this.component)return k`(no model)`;const g=this.processor.getData(this.component,this.value.path,this.surfaceId??N.DEFAULT_SURFACE_ID);return typeof g!="string"?k`(invalid)`:this.#a(g)}}return $}constructor(){super(...arguments),ve(this,m)}static{ve(r,u)}},r})();var fo=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},ho=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-divider")],t,u=[],r,i=Z;return class extends i{static{r=this}static{const s=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;fo(null,t={value:r},e,{kind:"class",name:r.name,metadata:s},null,u),r=t.value,s&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:s})}static{this.styles=[J,M`
      :host {
        display: block;
        min-height: 0;
        overflow: auto;
      }

      hr {
        height: 1px;
        background: #ccc;
        border: none;
      }
    `]}render(){return k`<hr
      class=${T(this.theme.components.Divider)}
      style=${this.theme.additionalStyles?.Divider?q(this.theme.additionalStyles?.Divider):$}
    />`}static{ho(r,u)}},r})();var vi=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Ru=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-icon")],t,u=[],r,i=Z,s,n=[],a=[];return class extends i{static{r=this}static{const c=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],vi(this,null,s,{kind:"accessor",name:"name",static:!1,private:!1,access:{has:l=>"name"in l,get:l=>l.name,set:(l,d)=>{l.name=d}},metadata:c},n,a),vi(null,t={value:r},e,{kind:"class",name:r.name,metadata:c},null,u),r=t.value,c&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:c})}#e=Ru(this,n,null);get name(){return this.#e}set name(c){this.#e=c}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }
    `]}#u(){if(!this.name)return $;const c=l=>(l=l.replace(/([A-Z])/gm,"_$1").toLocaleLowerCase(),k`<span class="g-icon">${l}</span>`);if(this.name&&typeof this.name=="object"){if("literalString"in this.name){const l=this.name.literalString??"";return c(l)}else if("literal"in this.name){const l=this.name.literal??"";return c(l)}else if(this.name&&"path"in this.name&&this.name.path){if(!this.processor||!this.component)return k`(no model)`;const l=this.processor.getData(this.component,this.name.path,this.surfaceId??N.DEFAULT_SURFACE_ID);return l?typeof l!="string"?k`Invalid icon name`:c(l):k`Invalid icon name`}}return k`(empty)`}render(){return k`<section
      class=${T(this.theme.components.Icon)}
      style=${this.theme.additionalStyles?.Icon?q(this.theme.additionalStyles?.Icon):$}
    >
      ${this.#u()}
    </section>`}constructor(){super(...arguments),Ru(this,a)}static{Ru(r,u)}},r})();const Te=(e=null)=>new ge.State(e,{equals:()=>!1}),po=new Set([Symbol.iterator,"concat","entries","every","filter","find","findIndex","flat","flatMap","forEach","includes","indexOf","join","keys","lastIndexOf","map","reduce","reduceRight","slice","some","values"]),bo=new Set(["fill","push","unshift"]);function wi(e){if(typeof e=="symbol")return null;const t=Number(e);return isNaN(t)?null:t%1===0?t:null}class qe{static from(t,u,r){return u?new qe(Array.from(t,u,r)):new qe(Array.from(t))}static of(...t){return new qe(t)}constructor(t=[]){let u=t.slice(),r=this,i=new Map,s=!1;return new Proxy(u,{get(n,a){let c=wi(a);if(c!==null)return r.#r(c),r.#e.get(),n[c];if(a==="length")return s?s=!1:r.#e.get(),n[a];if(bo.has(a)&&(s=!0),po.has(a)){let l=i.get(a);return l===void 0&&(l=(...d)=>(r.#e.get(),n[a](...d)),i.set(a,l)),l}return n[a]},set(n,a,c){n[a]=c;let l=wi(a);return l!==null?(r.#t(l),r.#e.set(null)):a==="length"&&r.#e.set(null),!0},getPrototypeOf(){return qe.prototype}})}#e=Te();#u=new Map;#r(t){let u=this.#u.get(t);u===void 0&&(u=Te(),this.#u.set(t,u)),u.get()}#t(t){const u=this.#u.get(t);u&&u.set(null)}}Object.setPrototypeOf(qe.prototype,Array.prototype);class Ps{collection=Te();storages=new Map;vals;readStorageFor(t){const{storages:u}=this;let r=u.get(t);r===void 0&&(r=Te(),u.set(t,r)),r.get()}dirtyStorageFor(t){const u=this.storages.get(t);u&&u.set(null)}constructor(t){this.vals=t?new Map(t):new Map}get(t){return this.readStorageFor(t),this.vals.get(t)}has(t){return this.readStorageFor(t),this.vals.has(t)}entries(){return this.collection.get(),this.vals.entries()}keys(){return this.collection.get(),this.vals.keys()}values(){return this.collection.get(),this.vals.values()}forEach(t){this.collection.get(),this.vals.forEach(t)}get size(){return this.collection.get(),this.vals.size}[Symbol.iterator](){return this.collection.get(),this.vals[Symbol.iterator]()}get[Symbol.toStringTag](){return this.vals[Symbol.toStringTag]}set(t,u){return this.dirtyStorageFor(t),this.collection.set(null),this.vals.set(t,u),this}delete(t){return this.dirtyStorageFor(t),this.collection.set(null),this.vals.delete(t)}clear(){this.storages.forEach(t=>t.set(null)),this.collection.set(null),this.vals.clear()}}Object.setPrototypeOf(Ps.prototype,Map.prototype);class au{static fromEntries(t){return new au(Object.fromEntries(t))}#e=new Map;#u=Te();constructor(t={}){let u=Object.getPrototypeOf(t),r=Object.getOwnPropertyDescriptors(t),i=Object.create(u);for(let n in r)Object.defineProperty(i,n,r[n]);let s=this;return new Proxy(i,{get(n,a,c){return s.#r(a),Reflect.get(n,a,c)},has(n,a){return s.#r(a),a in n},ownKeys(n){return s.#u.get(),Reflect.ownKeys(n)},set(n,a,c,l){let d=Reflect.set(n,a,c,l);return s.#t(a),s.#i(),d},deleteProperty(n,a){return a in n&&(delete n[a],s.#t(a),s.#i()),!0},getPrototypeOf(){return au.prototype}})}#r(t){let u=this.#e.get(t);u===void 0&&(u=Te(),this.#e.set(t,u)),u.get()}#t(t){const u=this.#e.get(t);u&&u.set(null)}#i(){this.#u.set(null)}}const mo=au;class zs{collection=Te();storages=new Map;vals;storageFor(t){const u=this.storages;let r=u.get(t);return r===void 0&&(r=Te(),u.set(t,r)),r}dirtyStorageFor(t){const u=this.storages.get(t);u&&u.set(null)}constructor(t){this.vals=new Set(t)}has(t){return this.storageFor(t).get(),this.vals.has(t)}entries(){return this.collection.get(),this.vals.entries()}keys(){return this.collection.get(),this.vals.keys()}values(){return this.collection.get(),this.vals.values()}forEach(t){this.collection.get(),this.vals.forEach(t)}get size(){return this.collection.get(),this.vals.size}[Symbol.iterator](){return this.collection.get(),this.vals[Symbol.iterator]()}get[Symbol.toStringTag](){return this.vals[Symbol.toStringTag]}add(t){return this.dirtyStorageFor(t),this.collection.set(null),this.vals.add(t),this}delete(t){return this.dirtyStorageFor(t),this.collection.set(null),this.vals.delete(t)}clear(){this.storages.forEach(t=>t.set(null)),this.collection.set(null),this.vals.clear()}}Object.setPrototypeOf(zs.prototype,Set.prototype);function go(){return new N({arrayCtor:qe,mapCtor:Ps,objCtor:mo,setCtor:zs})}const _o={createSignalA2uiMessageProcessor:go,A2uiMessageProcessor:N,Guards:no};var qt=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Re=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-image")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[],o,h=[],p=[];return class extends i{static{r=this}static{const f=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],o=[A()],qt(this,null,s,{kind:"accessor",name:"url",static:!1,private:!1,access:{has:b=>"url"in b,get:b=>b.url,set:(b,m)=>{b.url=m}},metadata:f},n,a),qt(this,null,c,{kind:"accessor",name:"usageHint",static:!1,private:!1,access:{has:b=>"usageHint"in b,get:b=>b.usageHint,set:(b,m)=>{b.usageHint=m}},metadata:f},l,d),qt(this,null,o,{kind:"accessor",name:"fit",static:!1,private:!1,access:{has:b=>"fit"in b,get:b=>b.fit,set:(b,m)=>{b.fit=m}},metadata:f},h,p),qt(null,t={value:r},e,{kind:"class",name:r.name,metadata:f},null,u),r=t.value,f&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:f})}#e=Re(this,n,null);get url(){return this.#e}set url(f){this.#e=f}#u=(Re(this,a),Re(this,l,null));get usageHint(){return this.#u}set usageHint(f){this.#u=f}#r=(Re(this,d),Re(this,h,null));get fit(){return this.#r}set fit(f){this.#r=f}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      img {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: var(--object-fit, fill);
      }
    `]}#t(){if(!this.url)return $;const f=b=>k`<img src=${b} />`;if(this.url&&typeof this.url=="object"){if("literalString"in this.url){const b=this.url.literalString??"";return f(b)}else if("literal"in this.url){const b=this.url.literal??"";return f(b)}else if(this.url&&"path"in this.url&&this.url.path){if(!this.processor||!this.component)return k`(no model)`;const b=this.processor.getData(this.component,this.url.path,this.surfaceId??N.DEFAULT_SURFACE_ID);return b?typeof b!="string"?k`Invalid image URL`:f(b):k`Invalid image URL`}}return k`(empty)`}render(){const f=ae(this.theme.components.Image.all,this.usageHint?this.theme.components.Image[this.usageHint]:{});return k`<section
      class=${T(f)}
      style=${q({...this.theme.additionalStyles?.Image??{},"--object-fit":this.fit??"fill"})}
    >
      ${this.#t()}
    </section>`}constructor(){super(...arguments),Re(this,p)}static{Re(r,u)}},r})();var ki=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Nu=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-list")],t,u=[],r,i=Z,s,n=[],a=[];return class extends i{static{r=this}static{const c=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A({reflect:!0,type:String})],ki(this,null,s,{kind:"accessor",name:"direction",static:!1,private:!1,access:{has:l=>"direction"in l,get:l=>l.direction,set:(l,d)=>{l.direction=d}},metadata:c},n,a),ki(null,t={value:r},e,{kind:"class",name:r.name,metadata:c},null,u),r=t.value,c&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:c})}#e=Nu(this,n,"vertical");get direction(){return this.#e}set direction(c){this.#e=c}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      :host([direction="vertical"]) section {
        display: grid;
      }

      :host([direction="horizontal"]) section {
        display: flex;
        max-width: 100%;
        overflow-x: scroll;
        overflow-y: hidden;
        scrollbar-width: none;

        > ::slotted(*) {
          flex: 1 0 fit-content;
          max-width: min(80%, 400px);
        }
      }
    `]}render(){return k`<section
      class=${T(this.theme.components.List)}
      style=${this.theme.additionalStyles?.List?q(this.theme.additionalStyles?.List):$}
    >
      <slot></slot>
    </section>`}constructor(){super(...arguments),Nu(this,a)}static{Nu(r,u)}},r})();function nr(e,t,u,r){if(e!==null&&typeof e=="object"){if("literalString"in e)return e.literalString??"";if("literal"in e&&e.literal!==void 0)return e.literal??"";if(e&&"path"in e&&e.path){if(!u||!t)return"(no model)";const i=u.getData(t,e.path,r??N.DEFAULT_SURFACE_ID);return i===null||typeof i!="string"?"":i}}return""}function yo(e,t,u,r){if(e!==null&&typeof e=="object"){if("literalNumber"in e)return e.literalNumber??0;if("literal"in e&&e.literal!==void 0)return e.literal??0;if(e&&"path"in e&&e.path){if(!u||!t)return-1;let i=u.getData(t,e.path,r??N.DEFAULT_SURFACE_ID);return typeof i=="string"&&(i=Number.parseInt(i,10),Number.isNaN(i)&&(i=null)),i===null||typeof i!="number"?-1:i}}return 0}var Ht=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Ne=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-multiplechoice")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[],o,h=[],p=[];return class extends i{static{r=this}static{const f=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],o=[A()],Ht(this,null,s,{kind:"accessor",name:"description",static:!1,private:!1,access:{has:b=>"description"in b,get:b=>b.description,set:(b,m)=>{b.description=m}},metadata:f},n,a),Ht(this,null,c,{kind:"accessor",name:"options",static:!1,private:!1,access:{has:b=>"options"in b,get:b=>b.options,set:(b,m)=>{b.options=m}},metadata:f},l,d),Ht(this,null,o,{kind:"accessor",name:"selections",static:!1,private:!1,access:{has:b=>"selections"in b,get:b=>b.selections,set:(b,m)=>{b.selections=m}},metadata:f},h,p),Ht(null,t={value:r},e,{kind:"class",name:r.name,metadata:f},null,u),r=t.value,f&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:f})}#e=Ne(this,n,null);get description(){return this.#e}set description(f){this.#e=f}#u=(Ne(this,a),Ne(this,l,[]));get options(){return this.#u}set options(f){this.#u=f}#r=(Ne(this,d),Ne(this,h,[]));get selections(){return this.#r}set selections(f){this.#r=f}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      select {
        width: 100%;
      }

      .description {
      }
    `]}#t(f){console.log(f),!(!this.selections||!this.processor)&&"path"in this.selections&&this.selections.path&&this.processor.setData(this.component,this.selections.path,f,this.surfaceId??N.DEFAULT_SURFACE_ID)}willUpdate(f){if(!f.has("options")||!this.processor||!this.component||Array.isArray(this.selections))return;this.selections;const m=this.processor.getData(this.component,this.selections.path,this.surfaceId??N.DEFAULT_SURFACE_ID);Array.isArray(m)&&this.#t(m)}render(){return k`<section class=${T(this.theme.components.MultipleChoice.container)}>
      <label class=${T(this.theme.components.MultipleChoice.label)} for="data">${this.description??"Select an item"}</div>
      <select
        name="data"
        id="data"
        class=${T(this.theme.components.MultipleChoice.element)}
        style=${this.theme.additionalStyles?.MultipleChoice?q(this.theme.additionalStyles?.MultipleChoice):$}
        @change=${f=>{f.target instanceof HTMLSelectElement&&this.#t([f.target.value])}}
      >
        ${this.options.map(f=>{const b=nr(f.label,this.component,this.processor,this.surfaceId);return k`<option ${f.value}>${b}</option>`})}
      </select>
    </section>`}constructor(){super(...arguments),Ne(this,p)}static{Ne(r,u)}},r})();const Mu=new WeakMap,xo=ct(class extends Ca{render(e){return $}update(e,[t]){const u=t!==this.G;return u&&this.G!==void 0&&this.rt(void 0),(u||this.lt!==this.ct)&&(this.G=t,this.ht=e.options?.host,this.rt(this.ct=e.element)),$}rt(e){if(this.isConnected||(e=void 0),typeof this.G=="function"){const t=this.ht??globalThis;let u=Mu.get(t);u===void 0&&(u=new WeakMap,Mu.set(t,u)),u.get(this.G)!==void 0&&this.G.call(this.ht,void 0),u.set(this.G,e),e!==void 0&&this.G.call(this.ht,e)}else this.G.value=e}get lt(){return typeof this.G=="function"?Mu.get(this.ht??globalThis)?.get(this.G):this.G?.value}disconnected(){this.lt===this.ct&&this.rt(void 0)}reconnected(){this.rt(this.ct)}});var ju=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},xt=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0},Vt=function(e,t,u){return typeof t=="symbol"&&(t=t.description?"[".concat(t.description,"]"):""),Object.defineProperty(e,"name",{configurable:!0,value:u?"".concat(u," ",t):t})};(()=>{let e=[j("a2ui-modal")],t,u=[],r,i=Z,s,n=[],a=[],c,l,d=[],o=[],h;return class extends i{static{r=this}static{const p=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[Le()],l=[Ba("dialog")],ju(this,c={get:Vt(function(){return this.#e},"#showModal","get"),set:Vt(function(f){this.#e=f},"#showModal","set")},s,{kind:"accessor",name:"#showModal",static:!1,private:!0,access:{has:f=>#u in f,get:f=>f.#u,set:(f,b)=>{f.#u=b}},metadata:p},n,a),ju(this,h={get:Vt(function(){return this.#r},"#modalRef","get"),set:Vt(function(f){this.#r=f},"#modalRef","set")},l,{kind:"accessor",name:"#modalRef",static:!1,private:!0,access:{has:f=>#t in f,get:f=>f.#t,set:(f,b)=>{f.#t=b}},metadata:p},d,o),ju(null,t={value:r},e,{kind:"class",name:r.name,metadata:p},null,u),r=t.value,p&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:p})}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      dialog {
        padding: 0 0 0 0;
        border: none;
        background: none;

        & section {
          & #controls {
            display: flex;
            justify-content: end;
            margin-bottom: 4px;

            & button {
              padding: 0;
              background: none;
              width: 20px;
              height: 20px;
              pointer: cursor;
              border: none;
              cursor: pointer;
            }
          }
        }
      }
    `]}#e=xt(this,n,!1);get#u(){return c.get.call(this)}set#u(p){return c.set.call(this,p)}#r=(xt(this,a),xt(this,d,null));get#t(){return h.get.call(this)}set#t(p){return h.set.call(this,p)}#i(){this.#t&&(this.#t.open&&this.#t.close(),this.#u=!1)}render(){return this.#u?k`<dialog
      class=${T(this.theme.components.Modal.backdrop)}
      @click=${p=>{const[f]=p.composedPath();f instanceof HTMLDialogElement&&this.#i()}}
      ${xo(p=>{requestAnimationFrame(()=>{!(p&&p instanceof HTMLDialogElement)||p.open||p.showModal()})})}
    >
      <section
        class=${T(this.theme.components.Modal.element)}
        style=${this.theme.additionalStyles?.Modal?q(this.theme.additionalStyles?.Modal):$}
      >
        <div id="controls">
          <button
            @click=${()=>{this.#i()}}
          >
            <span class="g-icon">close</span>
          </button>
        </div>
        <slot></slot>
      </section>
    </dialog>`:k`<section
        @click=${()=>{this.#u=!0}}
      >
        <slot name="entry"></slot>
      </section>`}constructor(){super(...arguments),xt(this,o)}static{xt(r,u)}},r})();var Lu=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},vt=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-row")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[];return class extends i{static{r=this}static{const o=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A({reflect:!0,type:String})],c=[A({reflect:!0,type:String})],Lu(this,null,s,{kind:"accessor",name:"alignment",static:!1,private:!1,access:{has:h=>"alignment"in h,get:h=>h.alignment,set:(h,p)=>{h.alignment=p}},metadata:o},n,a),Lu(this,null,c,{kind:"accessor",name:"distribution",static:!1,private:!1,access:{has:h=>"distribution"in h,get:h=>h.distribution,set:(h,p)=>{h.distribution=p}},metadata:o},l,d),Lu(null,t={value:r},e,{kind:"class",name:r.name,metadata:o},null,u),r=t.value,o&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:o})}#e=vt(this,n,"stretch");get alignment(){return this.#e}set alignment(o){this.#e=o}#u=(vt(this,a),vt(this,l,"start"));get distribution(){return this.#u}set distribution(o){this.#u=o}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: flex;
        flex: var(--weight);
      }

      section {
        display: flex;
        flex-direction: row;
        width: 100%;
        min-height: 100%;
      }

      :host([alignment="start"]) section {
        align-items: start;
      }

      :host([alignment="center"]) section {
        align-items: center;
      }

      :host([alignment="end"]) section {
        align-items: end;
      }

      :host([alignment="stretch"]) section {
        align-items: stretch;
      }

      :host([distribution="start"]) section {
        justify-content: start;
      }

      :host([distribution="center"]) section {
        justify-content: center;
      }

      :host([distribution="end"]) section {
        justify-content: end;
      }

      :host([distribution="spaceBetween"]) section {
        justify-content: space-between;
      }

      :host([distribution="spaceAround"]) section {
        justify-content: space-around;
      }

      :host([distribution="spaceEvenly"]) section {
        justify-content: space-evenly;
      }
    `]}render(){return k`<section
      class=${T(this.theme.components.Row)}
      style=${this.theme.additionalStyles?.Row?q(this.theme.additionalStyles?.Row):$}
    >
      <slot></slot>
    </section>`}constructor(){super(...arguments),vt(this,d)}static{vt(r,u)}},r})();var Ke=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},le=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-slider")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[],o,h=[],p=[],f,b=[],m=[],g,v=[],w=[];return class extends i{static{r=this}static{const y=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],o=[A()],f=[A()],g=[A()],Ke(this,null,s,{kind:"accessor",name:"value",static:!1,private:!1,access:{has:x=>"value"in x,get:x=>x.value,set:(x,E)=>{x.value=E}},metadata:y},n,a),Ke(this,null,c,{kind:"accessor",name:"minValue",static:!1,private:!1,access:{has:x=>"minValue"in x,get:x=>x.minValue,set:(x,E)=>{x.minValue=E}},metadata:y},l,d),Ke(this,null,o,{kind:"accessor",name:"maxValue",static:!1,private:!1,access:{has:x=>"maxValue"in x,get:x=>x.maxValue,set:(x,E)=>{x.maxValue=E}},metadata:y},h,p),Ke(this,null,f,{kind:"accessor",name:"label",static:!1,private:!1,access:{has:x=>"label"in x,get:x=>x.label,set:(x,E)=>{x.label=E}},metadata:y},b,m),Ke(this,null,g,{kind:"accessor",name:"inputType",static:!1,private:!1,access:{has:x=>"inputType"in x,get:x=>x.inputType,set:(x,E)=>{x.inputType=E}},metadata:y},v,w),Ke(null,t={value:r},e,{kind:"class",name:r.name,metadata:y},null,u),r=t.value,y&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:y})}#e=le(this,n,null);get value(){return this.#e}set value(y){this.#e=y}#u=(le(this,a),le(this,l,0));get minValue(){return this.#u}set minValue(y){this.#u=y}#r=(le(this,d),le(this,h,0));get maxValue(){return this.#r}set maxValue(y){this.#r=y}#t=(le(this,p),le(this,b,null));get label(){return this.#t}set label(y){this.#t=y}#i=(le(this,m),le(this,v,null));get inputType(){return this.#i}set inputType(y){this.#i=y}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
      }

      input {
        display: block;
        width: 100%;
      }

      .description {
      }
    `]}#a(y){!this.value||!this.processor||"path"in this.value&&this.value.path&&this.processor.setData(this.component,this.value.path,y,this.surfaceId??N.DEFAULT_SURFACE_ID)}#s(y){return k`<section
      class=${T(this.theme.components.Slider.container)}
    >
      <label class=${T(this.theme.components.Slider.label)} for="data">
        ${this.label?.literalString??""}
      </label>
      <input
        autocomplete="off"
        class=${T(this.theme.components.Slider.element)}
        style=${this.theme.additionalStyles?.Slider?q(this.theme.additionalStyles?.Slider):$}
        @input=${x=>{x.target instanceof HTMLInputElement&&this.#a(x.target.value)}}
        id="data"
        name="data"
        .value=${y}
        type="range"
        min=${this.minValue??"0"}
        max=${this.maxValue??"0"}
      />
      <span class=${T(this.theme.components.Slider.label)}
        >${this.value?yo(this.value,this.component,this.processor,this.surfaceId):"0"}</span
      >
    </section>`}render(){if(this.value&&typeof this.value=="object"){if("literalNumber"in this.value&&this.value.literalNumber)return this.#s(this.value.literalNumber);if("literal"in this.value&&this.value.literal!==void 0)return this.#s(this.value.literal);if(this.value&&"path"in this.value&&this.value.path){if(!this.processor||!this.component)return k`(no processor)`;const y=this.processor.getData(this.component,this.value.path,this.surfaceId??N.DEFAULT_SURFACE_ID);return y===null?k`Invalid value`:typeof y!="string"&&typeof y!="number"?k`Invalid value`:this.#s(y)}}return $}constructor(){super(...arguments),le(this,w)}static{le(r,u)}},r})();var Wt=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Me=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-surface")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[],o,h=[],p=[];return class extends i{static{r=this}static{const f=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],o=[A()],Wt(this,null,s,{kind:"accessor",name:"surfaceId",static:!1,private:!1,access:{has:b=>"surfaceId"in b,get:b=>b.surfaceId,set:(b,m)=>{b.surfaceId=m}},metadata:f},n,a),Wt(this,null,c,{kind:"accessor",name:"surface",static:!1,private:!1,access:{has:b=>"surface"in b,get:b=>b.surface,set:(b,m)=>{b.surface=m}},metadata:f},l,d),Wt(this,null,o,{kind:"accessor",name:"processor",static:!1,private:!1,access:{has:b=>"processor"in b,get:b=>b.processor,set:(b,m)=>{b.processor=m}},metadata:f},h,p),Wt(null,t={value:r},e,{kind:"class",name:r.name,metadata:f},null,u),r=t.value,f&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:f})}#e=Me(this,n,null);get surfaceId(){return this.#e}set surfaceId(f){this.#e=f}#u=(Me(this,a),Me(this,l,null));get surface(){return this.#u}set surface(f){this.#u=f}#r=(Me(this,d),Me(this,h,null));get processor(){return this.#r}set processor(f){this.#r=f}static{this.styles=[M`
      :host {
        display: flex;
        min-height: 0;
        max-height: 100%;
        flex-direction: column;
        gap: 16px;
      }

      #surface-logo {
        display: flex;
        justify-content: center;

        & img {
          width: 50%;
          max-width: 220px;
        }
      }

      a2ui-root {
        flex: 1;
      }
    `]}#t(){return this.surface?.styles.logoUrl?k`<div id="surface-logo">
      <img src=${this.surface.styles.logoUrl} />
    </div>`:$}#i(){const f={};if(this.surface?.styles)for(const[b,m]of Object.entries(this.surface.styles));return k`<a2ui-root
      style=${q(f)}
      .surfaceId=${this.surfaceId}
      .processor=${this.processor}
      .childComponents=${this.surface?.componentTree?[this.surface.componentTree]:null}
    ></a2ui-root>`}render(){return this.surface?k`${[this.#t(),this.#i()]}`:$}constructor(){super(...arguments),Me(this,p)}static{Me(r,u)}},r})();const Ci=(e,t,u)=>{const r=new Map;for(let i=t;i<=u;i++)r.set(e[i],i);return r},Yt=ct(class extends lt{constructor(e){if(super(e),e.type!==Mt.CHILD)throw Error("repeat() can only be used in text expressions")}dt(e,t,u){let r;u===void 0?u=t:t!==void 0&&(r=t);const i=[],s=[];let n=0;for(const a of e)i[n]=r?r(a,n):n,s[n]=u(a,n),n++;return{values:s,keys:i}}render(e,t,u){return this.dt(e,t,u).values}update(e,[t,u,r]){const i=xa(e),{values:s,keys:n}=this.dt(t,u,r);if(!Array.isArray(i))return this.ut=n,s;const a=this.ut??=[],c=[];let l,d,o=0,h=i.length-1,p=0,f=s.length-1;for(;o<=h&&p<=f;)if(i[o]===null)o++;else if(i[h]===null)h--;else if(a[o]===n[p])c[p]=ze(i[o],s[p]),o++,p++;else if(a[h]===n[f])c[f]=ze(i[h],s[f]),h--,f--;else if(a[o]===n[f])c[f]=ze(i[o],s[f]),mt(e,c[f+1],i[o]),o++,f--;else if(a[h]===n[p])c[p]=ze(i[h],s[p]),mt(e,i[o],i[h]),h--,p++;else if(l===void 0&&(l=Ci(n,p,f),d=Ci(a,o,h)),l.has(a[o]))if(l.has(a[h])){const b=d.get(n[p]),m=b!==void 0?i[b]:null;if(m===null){const g=mt(e,i[o]);ze(g,s[p]),c[p]=g}else c[p]=ze(m,s[p]),mt(e,i[o],m),i[b]=null;p++}else Su(i[h]),h--;else Su(i[o]),o++;for(;p<=f;){const b=mt(e,c[f+1]);ze(b,s[p]),c[p++]=b}for(;o<=h;){const b=i[o++];b!==null&&Su(b)}return this.ut=n,ya(e,c),de}});var Uu=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},wt=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-tabs")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[];return class extends i{static{r=this}static{const o=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],Uu(this,null,s,{kind:"accessor",name:"titles",static:!1,private:!1,access:{has:h=>"titles"in h,get:h=>h.titles,set:(h,p)=>{h.titles=p}},metadata:o},n,a),Uu(this,null,c,{kind:"accessor",name:"selected",static:!1,private:!1,access:{has:h=>"selected"in h,get:h=>h.selected,set:(h,p)=>{h.selected=p}},metadata:o},l,d),Uu(null,t={value:r},e,{kind:"class",name:r.name,metadata:o},null,u),r=t.value,o&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:o})}#e=wt(this,n,null);get titles(){return this.#e}set titles(o){this.#e=o}#u=(wt(this,a),wt(this,l,0));get selected(){return this.#u}set selected(o){this.#u=o}static{this.styles=[J,M`
      :host {
        display: block;
        flex: var(--weight);
      }
    `]}willUpdate(o){if(super.willUpdate(o),o.has("selected")){for(const p of this.children)p.removeAttribute("slot");const h=this.children[this.selected];if(!h)return;h.slot="current"}}#r(){return this.titles?k`<div
      id="buttons"
      class=${T(this.theme.components.Tabs.element)}
    >
      ${Yt(this.titles,(o,h)=>{let p="";if("literalString"in o&&o.literalString)p=o.literalString;else if("literal"in o&&o.literal!==void 0)p=o.literal;else if(o&&"path"in o&&o.path){if(!this.processor||!this.component)return k`(no model)`;const b=this.processor.getData(this.component,o.path,this.surfaceId??N.DEFAULT_SURFACE_ID);if(typeof b!="string")return k`(invalid)`;p=b}let f;return this.selected===h?f=ae(this.theme.components.Tabs.controls.all,this.theme.components.Tabs.controls.selected):f={...this.theme.components.Tabs.controls.all},k`<button
          ?disabled=${this.selected===h}
          class=${T(f)}
          @click=${()=>{this.selected=h}}
        >
          ${p}
        </button>`})}
    </div>`:$}#t(){return k`<slot name="current"></slot>`}render(){return k`<section
      class=${T(this.theme.components.Tabs.container)}
      style=${this.theme.additionalStyles?.Tabs?q(this.theme.additionalStyles?.Tabs):$}
    >
      ${[this.#r(),this.#t()]}
    </section>`}constructor(){super(...arguments),wt(this,d)}static{wt(r,u)}},r})();var Jt=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},je=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-textfield")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[],o,h=[],p=[];return class extends i{static{r=this}static{const f=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A()],o=[A()],Jt(this,null,s,{kind:"accessor",name:"text",static:!1,private:!1,access:{has:b=>"text"in b,get:b=>b.text,set:(b,m)=>{b.text=m}},metadata:f},n,a),Jt(this,null,c,{kind:"accessor",name:"label",static:!1,private:!1,access:{has:b=>"label"in b,get:b=>b.label,set:(b,m)=>{b.label=m}},metadata:f},l,d),Jt(this,null,o,{kind:"accessor",name:"inputType",static:!1,private:!1,access:{has:b=>"inputType"in b,get:b=>b.inputType,set:(b,m)=>{b.inputType=m}},metadata:f},h,p),Jt(null,t={value:r},e,{kind:"class",name:r.name,metadata:f},null,u),r=t.value,f&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:f})}#e=je(this,n,null);get text(){return this.#e}set text(f){this.#e=f}#u=(je(this,a),je(this,l,null));get label(){return this.#u}set label(f){this.#u=f}#r=(je(this,d),je(this,h,null));get inputType(){return this.#r}set inputType(f){this.#r=f}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: flex;
        flex: var(--weight);
      }

      input {
        display: block;
        width: 100%;
      }

      label {
        display: block;
        margin-bottom: 4px;
      }
    `]}#t(f){!this.text||!this.processor||"path"in this.text&&this.text.path&&this.processor.setData(this.component,this.text.path,f,this.surfaceId??N.DEFAULT_SURFACE_ID)}#i(f,b){return k` <section
      class=${T(this.theme.components.TextField.container)}
    >
      ${b&&b!==""?k`<label
            class=${T(this.theme.components.TextField.label)}
            for="data"
            >${b}</label
          >`:$}
      <input
        autocomplete="off"
        class=${T(this.theme.components.TextField.element)}
        style=${this.theme.additionalStyles?.TextField?q(this.theme.additionalStyles?.TextField):$}
        @input=${m=>{m.target instanceof HTMLInputElement&&this.#t(m.target.value)}}
        name="data"
        id="data"
        .value=${f}
        .placeholder=${"Please enter a value"}
        type=${this.inputType==="number"?"number":"text"}
      />
    </section>`}render(){const f=nr(this.label,this.component,this.processor,this.surfaceId),b=nr(this.text,this.component,this.processor,this.surfaceId);return this.#i(b,f)}constructor(){super(...arguments),je(this,p)}static{je(r,u)}},r})();class ar extends lt{constructor(t){if(super(t),this.it=$,t.type!==Mt.CHILD)throw Error(this.constructor.directiveName+"() can only be used in child bindings")}render(t){if(t===$||t==null)return this._t=void 0,this.it=t;if(t===de)return t;if(typeof t!="string")throw Error(this.constructor.directiveName+"() called with a non-string value");if(t===this.it)return this._t;this.it=t;const u=[t];return u.raw=u,this._t={_$litType$:this.constructor.resultType,strings:u,values:[]}}}ar.directiveName="unsafeHTML",ar.resultType=1;const vo=ct(ar),$i={};function wo(e){let t=$i[e];if(t)return t;t=$i[e]=[];for(let u=0;u<128;u++){const r=String.fromCharCode(u);t.push(r)}for(let u=0;u<e.length;u++){const r=e.charCodeAt(u);t[r]="%"+("0"+r.toString(16).toUpperCase()).slice(-2)}return t}function nt(e,t){typeof t!="string"&&(t=nt.defaultChars);const u=wo(t);return e.replace(/(%[a-f0-9]{2})+/gi,function(r){let i="";for(let s=0,n=r.length;s<n;s+=3){const a=parseInt(r.slice(s+1,s+3),16);if(a<128){i+=u[a];continue}if((a&224)===192&&s+3<n){const c=parseInt(r.slice(s+4,s+6),16);if((c&192)===128){const l=a<<6&1984|c&63;l<128?i+="��":i+=String.fromCharCode(l),s+=3;continue}}if((a&240)===224&&s+6<n){const c=parseInt(r.slice(s+4,s+6),16),l=parseInt(r.slice(s+7,s+9),16);if((c&192)===128&&(l&192)===128){const d=a<<12&61440|c<<6&4032|l&63;d<2048||d>=55296&&d<=57343?i+="���":i+=String.fromCharCode(d),s+=6;continue}}if((a&248)===240&&s+9<n){const c=parseInt(r.slice(s+4,s+6),16),l=parseInt(r.slice(s+7,s+9),16),d=parseInt(r.slice(s+10,s+12),16);if((c&192)===128&&(l&192)===128&&(d&192)===128){let o=a<<18&1835008|c<<12&258048|l<<6&4032|d&63;o<65536||o>1114111?i+="����":(o-=65536,i+=String.fromCharCode(55296+(o>>10),56320+(o&1023))),s+=9;continue}}i+="�"}return i})}nt.defaultChars=";/?:@&=+$,#";nt.componentChars="";const Ei={};function ko(e){let t=Ei[e];if(t)return t;t=Ei[e]=[];for(let u=0;u<128;u++){const r=String.fromCharCode(u);/^[0-9a-z]$/i.test(r)?t.push(r):t.push("%"+("0"+u.toString(16).toUpperCase()).slice(-2))}for(let u=0;u<e.length;u++)t[e.charCodeAt(u)]=e[u];return t}function jt(e,t,u){typeof t!="string"&&(u=t,t=jt.defaultChars),typeof u>"u"&&(u=!0);const r=ko(t);let i="";for(let s=0,n=e.length;s<n;s++){const a=e.charCodeAt(s);if(u&&a===37&&s+2<n&&/^[0-9a-f]{2}$/i.test(e.slice(s+1,s+3))){i+=e.slice(s,s+3),s+=2;continue}if(a<128){i+=r[a];continue}if(a>=55296&&a<=57343){if(a>=55296&&a<=56319&&s+1<n){const c=e.charCodeAt(s+1);if(c>=56320&&c<=57343){i+=encodeURIComponent(e[s]+e[s+1]),s++;continue}}i+="%EF%BF%BD";continue}i+=encodeURIComponent(e[s])}return i}jt.defaultChars=";/?:@&=+$,-_.!~*'()#";jt.componentChars="-_.!~*'()";function Fr(e){let t="";return t+=e.protocol||"",t+=e.slashes?"//":"",t+=e.auth?e.auth+"@":"",e.hostname&&e.hostname.indexOf(":")!==-1?t+="["+e.hostname+"]":t+=e.hostname||"",t+=e.port?":"+e.port:"",t+=e.pathname||"",t+=e.search||"",t+=e.hash||"",t}function ou(){this.protocol=null,this.slashes=null,this.auth=null,this.port=null,this.hostname=null,this.hash=null,this.search=null,this.pathname=null}const Co=/^([a-z0-9.+-]+:)/i,$o=/:[0-9]*$/,Eo=/^(\/\/?(?!\/)[^\?\s]*)(\?[^\s]*)?$/,Ao=["<",">",'"',"`"," ","\r",`
`,"	"],Do=["{","}","|","\\","^","`"].concat(Ao),So=["'"].concat(Do),Ai=["%","/","?",";","#"].concat(So),Di=["/","?","#"],Fo=255,Si=/^[+a-z0-9A-Z_-]{0,63}$/,To=/^([+a-z0-9A-Z_-]{0,63})(.*)$/,Fi={javascript:!0,"javascript:":!0},Ti={http:!0,https:!0,ftp:!0,gopher:!0,file:!0,"http:":!0,"https:":!0,"ftp:":!0,"gopher:":!0,"file:":!0};function Tr(e,t){if(e&&e instanceof ou)return e;const u=new ou;return u.parse(e,t),u}ou.prototype.parse=function(e,t){let u,r,i,s=e;if(s=s.trim(),!t&&e.split("#").length===1){const l=Eo.exec(s);if(l)return this.pathname=l[1],l[2]&&(this.search=l[2]),this}let n=Co.exec(s);if(n&&(n=n[0],u=n.toLowerCase(),this.protocol=n,s=s.substr(n.length)),(t||n||s.match(/^\/\/[^@\/]+@[^@\/]+/))&&(i=s.substr(0,2)==="//",i&&!(n&&Fi[n])&&(s=s.substr(2),this.slashes=!0)),!Fi[n]&&(i||n&&!Ti[n])){let l=-1;for(let f=0;f<Di.length;f++)r=s.indexOf(Di[f]),r!==-1&&(l===-1||r<l)&&(l=r);let d,o;l===-1?o=s.lastIndexOf("@"):o=s.lastIndexOf("@",l),o!==-1&&(d=s.slice(0,o),s=s.slice(o+1),this.auth=d),l=-1;for(let f=0;f<Ai.length;f++)r=s.indexOf(Ai[f]),r!==-1&&(l===-1||r<l)&&(l=r);l===-1&&(l=s.length),s[l-1]===":"&&l--;const h=s.slice(0,l);s=s.slice(l),this.parseHost(h),this.hostname=this.hostname||"";const p=this.hostname[0]==="["&&this.hostname[this.hostname.length-1]==="]";if(!p){const f=this.hostname.split(/\./);for(let b=0,m=f.length;b<m;b++){const g=f[b];if(g&&!g.match(Si)){let v="";for(let w=0,y=g.length;w<y;w++)g.charCodeAt(w)>127?v+="x":v+=g[w];if(!v.match(Si)){const w=f.slice(0,b),y=f.slice(b+1),x=g.match(To);x&&(w.push(x[1]),y.unshift(x[2])),y.length&&(s=y.join(".")+s),this.hostname=w.join(".");break}}}}this.hostname.length>Fo&&(this.hostname=""),p&&(this.hostname=this.hostname.substr(1,this.hostname.length-2))}const a=s.indexOf("#");a!==-1&&(this.hash=s.substr(a),s=s.slice(0,a));const c=s.indexOf("?");return c!==-1&&(this.search=s.substr(c),s=s.slice(0,c)),s&&(this.pathname=s),Ti[u]&&this.hostname&&!this.pathname&&(this.pathname=""),this};ou.prototype.parseHost=function(e){let t=$o.exec(e);t&&(t=t[0],t!==":"&&(this.port=t.substr(1)),e=e.substr(0,e.length-t.length)),e&&(this.hostname=e)};const Io=Object.freeze(Object.defineProperty({__proto__:null,decode:nt,encode:jt,format:Fr,parse:Tr},Symbol.toStringTag,{value:"Module"})),Rs=/[\0-\uD7FF\uE000-\uFFFF]|[\uD800-\uDBFF][\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?:[^\uD800-\uDBFF]|^)[\uDC00-\uDFFF]/,Ns=/[\0-\x1F\x7F-\x9F]/,Oo=/[\xAD\u0600-\u0605\u061C\u06DD\u070F\u0890\u0891\u08E2\u180E\u200B-\u200F\u202A-\u202E\u2060-\u2064\u2066-\u206F\uFEFF\uFFF9-\uFFFB]|\uD804[\uDCBD\uDCCD]|\uD80D[\uDC30-\uDC3F]|\uD82F[\uDCA0-\uDCA3]|\uD834[\uDD73-\uDD7A]|\uDB40[\uDC01\uDC20-\uDC7F]/,Ir=/[!-#%-\*,-\/:;\?@\[-\]_\{\}\xA1\xA7\xAB\xB6\xB7\xBB\xBF\u037E\u0387\u055A-\u055F\u0589\u058A\u05BE\u05C0\u05C3\u05C6\u05F3\u05F4\u0609\u060A\u060C\u060D\u061B\u061D-\u061F\u066A-\u066D\u06D4\u0700-\u070D\u07F7-\u07F9\u0830-\u083E\u085E\u0964\u0965\u0970\u09FD\u0A76\u0AF0\u0C77\u0C84\u0DF4\u0E4F\u0E5A\u0E5B\u0F04-\u0F12\u0F14\u0F3A-\u0F3D\u0F85\u0FD0-\u0FD4\u0FD9\u0FDA\u104A-\u104F\u10FB\u1360-\u1368\u1400\u166E\u169B\u169C\u16EB-\u16ED\u1735\u1736\u17D4-\u17D6\u17D8-\u17DA\u1800-\u180A\u1944\u1945\u1A1E\u1A1F\u1AA0-\u1AA6\u1AA8-\u1AAD\u1B5A-\u1B60\u1B7D\u1B7E\u1BFC-\u1BFF\u1C3B-\u1C3F\u1C7E\u1C7F\u1CC0-\u1CC7\u1CD3\u2010-\u2027\u2030-\u2043\u2045-\u2051\u2053-\u205E\u207D\u207E\u208D\u208E\u2308-\u230B\u2329\u232A\u2768-\u2775\u27C5\u27C6\u27E6-\u27EF\u2983-\u2998\u29D8-\u29DB\u29FC\u29FD\u2CF9-\u2CFC\u2CFE\u2CFF\u2D70\u2E00-\u2E2E\u2E30-\u2E4F\u2E52-\u2E5D\u3001-\u3003\u3008-\u3011\u3014-\u301F\u3030\u303D\u30A0\u30FB\uA4FE\uA4FF\uA60D-\uA60F\uA673\uA67E\uA6F2-\uA6F7\uA874-\uA877\uA8CE\uA8CF\uA8F8-\uA8FA\uA8FC\uA92E\uA92F\uA95F\uA9C1-\uA9CD\uA9DE\uA9DF\uAA5C-\uAA5F\uAADE\uAADF\uAAF0\uAAF1\uABEB\uFD3E\uFD3F\uFE10-\uFE19\uFE30-\uFE52\uFE54-\uFE61\uFE63\uFE68\uFE6A\uFE6B\uFF01-\uFF03\uFF05-\uFF0A\uFF0C-\uFF0F\uFF1A\uFF1B\uFF1F\uFF20\uFF3B-\uFF3D\uFF3F\uFF5B\uFF5D\uFF5F-\uFF65]|\uD800[\uDD00-\uDD02\uDF9F\uDFD0]|\uD801\uDD6F|\uD802[\uDC57\uDD1F\uDD3F\uDE50-\uDE58\uDE7F\uDEF0-\uDEF6\uDF39-\uDF3F\uDF99-\uDF9C]|\uD803[\uDEAD\uDF55-\uDF59\uDF86-\uDF89]|\uD804[\uDC47-\uDC4D\uDCBB\uDCBC\uDCBE-\uDCC1\uDD40-\uDD43\uDD74\uDD75\uDDC5-\uDDC8\uDDCD\uDDDB\uDDDD-\uDDDF\uDE38-\uDE3D\uDEA9]|\uD805[\uDC4B-\uDC4F\uDC5A\uDC5B\uDC5D\uDCC6\uDDC1-\uDDD7\uDE41-\uDE43\uDE60-\uDE6C\uDEB9\uDF3C-\uDF3E]|\uD806[\uDC3B\uDD44-\uDD46\uDDE2\uDE3F-\uDE46\uDE9A-\uDE9C\uDE9E-\uDEA2\uDF00-\uDF09]|\uD807[\uDC41-\uDC45\uDC70\uDC71\uDEF7\uDEF8\uDF43-\uDF4F\uDFFF]|\uD809[\uDC70-\uDC74]|\uD80B[\uDFF1\uDFF2]|\uD81A[\uDE6E\uDE6F\uDEF5\uDF37-\uDF3B\uDF44]|\uD81B[\uDE97-\uDE9A\uDFE2]|\uD82F\uDC9F|\uD836[\uDE87-\uDE8B]|\uD83A[\uDD5E\uDD5F]/,Ms=/[\$\+<->\^`\|~\xA2-\xA6\xA8\xA9\xAC\xAE-\xB1\xB4\xB8\xD7\xF7\u02C2-\u02C5\u02D2-\u02DF\u02E5-\u02EB\u02ED\u02EF-\u02FF\u0375\u0384\u0385\u03F6\u0482\u058D-\u058F\u0606-\u0608\u060B\u060E\u060F\u06DE\u06E9\u06FD\u06FE\u07F6\u07FE\u07FF\u0888\u09F2\u09F3\u09FA\u09FB\u0AF1\u0B70\u0BF3-\u0BFA\u0C7F\u0D4F\u0D79\u0E3F\u0F01-\u0F03\u0F13\u0F15-\u0F17\u0F1A-\u0F1F\u0F34\u0F36\u0F38\u0FBE-\u0FC5\u0FC7-\u0FCC\u0FCE\u0FCF\u0FD5-\u0FD8\u109E\u109F\u1390-\u1399\u166D\u17DB\u1940\u19DE-\u19FF\u1B61-\u1B6A\u1B74-\u1B7C\u1FBD\u1FBF-\u1FC1\u1FCD-\u1FCF\u1FDD-\u1FDF\u1FED-\u1FEF\u1FFD\u1FFE\u2044\u2052\u207A-\u207C\u208A-\u208C\u20A0-\u20C0\u2100\u2101\u2103-\u2106\u2108\u2109\u2114\u2116-\u2118\u211E-\u2123\u2125\u2127\u2129\u212E\u213A\u213B\u2140-\u2144\u214A-\u214D\u214F\u218A\u218B\u2190-\u2307\u230C-\u2328\u232B-\u2426\u2440-\u244A\u249C-\u24E9\u2500-\u2767\u2794-\u27C4\u27C7-\u27E5\u27F0-\u2982\u2999-\u29D7\u29DC-\u29FB\u29FE-\u2B73\u2B76-\u2B95\u2B97-\u2BFF\u2CE5-\u2CEA\u2E50\u2E51\u2E80-\u2E99\u2E9B-\u2EF3\u2F00-\u2FD5\u2FF0-\u2FFF\u3004\u3012\u3013\u3020\u3036\u3037\u303E\u303F\u309B\u309C\u3190\u3191\u3196-\u319F\u31C0-\u31E3\u31EF\u3200-\u321E\u322A-\u3247\u3250\u3260-\u327F\u328A-\u32B0\u32C0-\u33FF\u4DC0-\u4DFF\uA490-\uA4C6\uA700-\uA716\uA720\uA721\uA789\uA78A\uA828-\uA82B\uA836-\uA839\uAA77-\uAA79\uAB5B\uAB6A\uAB6B\uFB29\uFBB2-\uFBC2\uFD40-\uFD4F\uFDCF\uFDFC-\uFDFF\uFE62\uFE64-\uFE66\uFE69\uFF04\uFF0B\uFF1C-\uFF1E\uFF3E\uFF40\uFF5C\uFF5E\uFFE0-\uFFE6\uFFE8-\uFFEE\uFFFC\uFFFD]|\uD800[\uDD37-\uDD3F\uDD79-\uDD89\uDD8C-\uDD8E\uDD90-\uDD9C\uDDA0\uDDD0-\uDDFC]|\uD802[\uDC77\uDC78\uDEC8]|\uD805\uDF3F|\uD807[\uDFD5-\uDFF1]|\uD81A[\uDF3C-\uDF3F\uDF45]|\uD82F\uDC9C|\uD833[\uDF50-\uDFC3]|\uD834[\uDC00-\uDCF5\uDD00-\uDD26\uDD29-\uDD64\uDD6A-\uDD6C\uDD83\uDD84\uDD8C-\uDDA9\uDDAE-\uDDEA\uDE00-\uDE41\uDE45\uDF00-\uDF56]|\uD835[\uDEC1\uDEDB\uDEFB\uDF15\uDF35\uDF4F\uDF6F\uDF89\uDFA9\uDFC3]|\uD836[\uDC00-\uDDFF\uDE37-\uDE3A\uDE6D-\uDE74\uDE76-\uDE83\uDE85\uDE86]|\uD838[\uDD4F\uDEFF]|\uD83B[\uDCAC\uDCB0\uDD2E\uDEF0\uDEF1]|\uD83C[\uDC00-\uDC2B\uDC30-\uDC93\uDCA0-\uDCAE\uDCB1-\uDCBF\uDCC1-\uDCCF\uDCD1-\uDCF5\uDD0D-\uDDAD\uDDE6-\uDE02\uDE10-\uDE3B\uDE40-\uDE48\uDE50\uDE51\uDE60-\uDE65\uDF00-\uDFFF]|\uD83D[\uDC00-\uDED7\uDEDC-\uDEEC\uDEF0-\uDEFC\uDF00-\uDF76\uDF7B-\uDFD9\uDFE0-\uDFEB\uDFF0]|\uD83E[\uDC00-\uDC0B\uDC10-\uDC47\uDC50-\uDC59\uDC60-\uDC87\uDC90-\uDCAD\uDCB0\uDCB1\uDD00-\uDE53\uDE60-\uDE6D\uDE70-\uDE7C\uDE80-\uDE88\uDE90-\uDEBD\uDEBF-\uDEC5\uDECE-\uDEDB\uDEE0-\uDEE8\uDEF0-\uDEF8\uDF00-\uDF92\uDF94-\uDFCA]/,js=/[ \xA0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000]/,Po=Object.freeze(Object.defineProperty({__proto__:null,Any:Rs,Cc:Ns,Cf:Oo,P:Ir,S:Ms,Z:js},Symbol.toStringTag,{value:"Module"})),zo=new Uint16Array('ᵁ<Õıʊҝջאٵ۞ޢߖࠏ੊ઑඡ๭༉༦჊ረዡᐕᒝᓃᓟᔥ\0\0\0\0\0\0ᕫᛍᦍᰒᷝ὾⁠↰⊍⏀⏻⑂⠤⤒ⴈ⹈⿎〖㊺㘹㞬㣾㨨㩱㫠㬮ࠀEMabcfglmnoprstu\\bfms¦³¹ÈÏlig耻Æ䃆P耻&䀦cute耻Á䃁reve;䄂Āiyx}rc耻Â䃂;䐐r;쀀𝔄rave耻À䃀pha;䎑acr;䄀d;橓Āgp¡on;䄄f;쀀𝔸plyFunction;恡ing耻Å䃅Ācs¾Ãr;쀀𝒜ign;扔ilde耻Ã䃃ml耻Ä䃄ЀaceforsuåûþėĜĢħĪĀcrêòkslash;或Ŷöø;櫧ed;挆y;䐑ƀcrtąċĔause;戵noullis;愬a;䎒r;쀀𝔅pf;쀀𝔹eve;䋘còēmpeq;扎܀HOacdefhilorsuōőŖƀƞƢƵƷƺǜȕɳɸɾcy;䐧PY耻©䂩ƀcpyŝŢźute;䄆Ā;iŧŨ拒talDifferentialD;慅leys;愭ȀaeioƉƎƔƘron;䄌dil耻Ç䃇rc;䄈nint;戰ot;䄊ĀdnƧƭilla;䂸terDot;䂷òſi;䎧rcleȀDMPTǇǋǑǖot;抙inus;抖lus;投imes;抗oĀcsǢǸkwiseContourIntegral;戲eCurlyĀDQȃȏoubleQuote;思uote;怙ȀlnpuȞȨɇɕonĀ;eȥȦ户;橴ƀgitȯȶȺruent;扡nt;戯ourIntegral;戮ĀfrɌɎ;愂oduct;成nterClockwiseContourIntegral;戳oss;樯cr;쀀𝒞pĀ;Cʄʅ拓ap;才րDJSZacefiosʠʬʰʴʸˋ˗ˡ˦̳ҍĀ;oŹʥtrahd;椑cy;䐂cy;䐅cy;䐏ƀgrsʿ˄ˇger;怡r;憡hv;櫤Āayː˕ron;䄎;䐔lĀ;t˝˞戇a;䎔r;쀀𝔇Āaf˫̧Ācm˰̢riticalȀADGT̖̜̀̆cute;䂴oŴ̋̍;䋙bleAcute;䋝rave;䁠ilde;䋜ond;拄ferentialD;慆Ѱ̽\0\0\0͔͂\0Ѕf;쀀𝔻ƀ;DE͈͉͍䂨ot;惜qual;扐blèCDLRUVͣͲ΂ϏϢϸontourIntegraìȹoɴ͹\0\0ͻ»͉nArrow;懓Āeo·ΤftƀARTΐΖΡrrow;懐ightArrow;懔eåˊngĀLRΫτeftĀARγιrrow;柸ightArrow;柺ightArrow;柹ightĀATϘϞrrow;懒ee;抨pɁϩ\0\0ϯrrow;懑ownArrow;懕erticalBar;戥ǹABLRTaВЪаўѿͼrrowƀ;BUНОТ憓ar;椓pArrow;懵reve;䌑eft˒к\0ц\0ѐightVector;楐eeVector;楞ectorĀ;Bљњ憽ar;楖ightǔѧ\0ѱeeVector;楟ectorĀ;BѺѻ懁ar;楗eeĀ;A҆҇护rrow;憧ĀctҒҗr;쀀𝒟rok;䄐ࠀNTacdfglmopqstuxҽӀӄӋӞӢӧӮӵԡԯԶՒ՝ՠեG;䅊H耻Ð䃐cute耻É䃉ƀaiyӒӗӜron;䄚rc耻Ê䃊;䐭ot;䄖r;쀀𝔈rave耻È䃈ement;戈ĀapӺӾcr;䄒tyɓԆ\0\0ԒmallSquare;旻erySmallSquare;斫ĀgpԦԪon;䄘f;쀀𝔼silon;䎕uĀaiԼՉlĀ;TՂՃ橵ilde;扂librium;懌Āci՗՚r;愰m;橳a;䎗ml耻Ë䃋Āipժկsts;戃onentialE;慇ʀcfiosօֈ֍ֲ׌y;䐤r;쀀𝔉lledɓ֗\0\0֣mallSquare;旼erySmallSquare;斪Ͱֺ\0ֿ\0\0ׄf;쀀𝔽All;戀riertrf;愱cò׋؀JTabcdfgorstר׬ׯ׺؀ؒؖ؛؝أ٬ٲcy;䐃耻>䀾mmaĀ;d׷׸䎓;䏜reve;䄞ƀeiy؇،ؐdil;䄢rc;䄜;䐓ot;䄠r;쀀𝔊;拙pf;쀀𝔾eater̀EFGLSTصلَٖٛ٦qualĀ;Lؾؿ扥ess;招ullEqual;执reater;檢ess;扷lantEqual;橾ilde;扳cr;쀀𝒢;扫ЀAacfiosuڅڋږڛڞڪھۊRDcy;䐪Āctڐڔek;䋇;䁞irc;䄤r;愌lbertSpace;愋ǰگ\0ڲf;愍izontalLine;攀Āctۃۅòکrok;䄦mpńېۘownHumðįqual;扏܀EJOacdfgmnostuۺ۾܃܇܎ܚܞܡܨ݄ݸދޏޕcy;䐕lig;䄲cy;䐁cute耻Í䃍Āiyܓܘrc耻Î䃎;䐘ot;䄰r;愑rave耻Ì䃌ƀ;apܠܯܿĀcgܴܷr;䄪inaryI;慈lieóϝǴ݉\0ݢĀ;eݍݎ戬Āgrݓݘral;戫section;拂isibleĀCTݬݲomma;恣imes;恢ƀgptݿރވon;䄮f;쀀𝕀a;䎙cr;愐ilde;䄨ǫޚ\0ޞcy;䐆l耻Ï䃏ʀcfosuެ޷޼߂ߐĀiyޱ޵rc;䄴;䐙r;쀀𝔍pf;쀀𝕁ǣ߇\0ߌr;쀀𝒥rcy;䐈kcy;䐄΀HJacfosߤߨ߽߬߱ࠂࠈcy;䐥cy;䐌ppa;䎚Āey߶߻dil;䄶;䐚r;쀀𝔎pf;쀀𝕂cr;쀀𝒦րJTaceflmostࠥࠩࠬࡐࡣ঳সে্਷ੇcy;䐉耻<䀼ʀcmnpr࠷࠼ࡁࡄࡍute;䄹bda;䎛g;柪lacetrf;愒r;憞ƀaeyࡗ࡜ࡡron;䄽dil;䄻;䐛Āfsࡨ॰tԀACDFRTUVarࡾࢩࢱࣦ࣠ࣼयज़ΐ४Ānrࢃ࢏gleBracket;柨rowƀ;BR࢙࢚࢞憐ar;懤ightArrow;懆eiling;挈oǵࢷ\0ࣃbleBracket;柦nǔࣈ\0࣒eeVector;楡ectorĀ;Bࣛࣜ懃ar;楙loor;挊ightĀAV࣯ࣵrrow;憔ector;楎Āerँगeƀ;AVउऊऐ抣rrow;憤ector;楚iangleƀ;BEतथऩ抲ar;槏qual;抴pƀDTVषूौownVector;楑eeVector;楠ectorĀ;Bॖॗ憿ar;楘ectorĀ;B॥०憼ar;楒ightáΜs̀EFGLSTॾঋকঝঢভqualGreater;拚ullEqual;扦reater;扶ess;檡lantEqual;橽ilde;扲r;쀀𝔏Ā;eঽা拘ftarrow;懚idot;䄿ƀnpw৔ਖਛgȀLRlr৞৷ਂਐeftĀAR০৬rrow;柵ightArrow;柷ightArrow;柶eftĀarγਊightáοightáϊf;쀀𝕃erĀLRਢਬeftArrow;憙ightArrow;憘ƀchtਾੀੂòࡌ;憰rok;䅁;扪Ѐacefiosuਗ਼੝੠੷੼અઋ઎p;椅y;䐜Ādl੥੯iumSpace;恟lintrf;愳r;쀀𝔐nusPlus;戓pf;쀀𝕄cò੶;䎜ҀJacefostuણધભીଔଙඑ඗ඞcy;䐊cute;䅃ƀaey઴હાron;䅇dil;䅅;䐝ƀgswે૰଎ativeƀMTV૓૟૨ediumSpace;怋hiĀcn૦૘ë૙eryThiî૙tedĀGL૸ଆreaterGreateòٳessLesóੈLine;䀊r;쀀𝔑ȀBnptଢନଷ଺reak;恠BreakingSpace;䂠f;愕ڀ;CDEGHLNPRSTV୕ୖ୪୼஡௫ఄ౞಄ದ೘ൡඅ櫬Āou୛୤ngruent;扢pCap;扭oubleVerticalBar;戦ƀlqxஃஊ஛ement;戉ualĀ;Tஒஓ扠ilde;쀀≂̸ists;戄reater΀;EFGLSTஶஷ஽௉௓௘௥扯qual;扱ullEqual;쀀≧̸reater;쀀≫̸ess;批lantEqual;쀀⩾̸ilde;扵umpń௲௽ownHump;쀀≎̸qual;쀀≏̸eĀfsఊధtTriangleƀ;BEచఛడ拪ar;쀀⧏̸qual;括s̀;EGLSTవశ఼ౄోౘ扮qual;扰reater;扸ess;쀀≪̸lantEqual;쀀⩽̸ilde;扴estedĀGL౨౹reaterGreater;쀀⪢̸essLess;쀀⪡̸recedesƀ;ESಒಓಛ技qual;쀀⪯̸lantEqual;拠ĀeiಫಹverseElement;戌ghtTriangleƀ;BEೋೌ೒拫ar;쀀⧐̸qual;拭ĀquೝഌuareSuĀbp೨೹setĀ;E೰ೳ쀀⊏̸qual;拢ersetĀ;Eഃആ쀀⊐̸qual;拣ƀbcpഓതൎsetĀ;Eഛഞ쀀⊂⃒qual;抈ceedsȀ;ESTലള഻െ抁qual;쀀⪰̸lantEqual;拡ilde;쀀≿̸ersetĀ;E൘൛쀀⊃⃒qual;抉ildeȀ;EFT൮൯൵ൿ扁qual;扄ullEqual;扇ilde;扉erticalBar;戤cr;쀀𝒩ilde耻Ñ䃑;䎝܀Eacdfgmoprstuvලෂ෉෕ෛ෠෧෼ขภยา฿ไlig;䅒cute耻Ó䃓Āiy෎ීrc耻Ô䃔;䐞blac;䅐r;쀀𝔒rave耻Ò䃒ƀaei෮ෲ෶cr;䅌ga;䎩cron;䎟pf;쀀𝕆enCurlyĀDQฎบoubleQuote;怜uote;怘;橔Āclวฬr;쀀𝒪ash耻Ø䃘iŬื฼de耻Õ䃕es;樷ml耻Ö䃖erĀBP๋๠Āar๐๓r;怾acĀek๚๜;揞et;掴arenthesis;揜Ҁacfhilors๿ງຊຏຒດຝະ໼rtialD;戂y;䐟r;쀀𝔓i;䎦;䎠usMinus;䂱Āipຢອncareplanåڝf;愙Ȁ;eio຺ູ໠໤檻cedesȀ;EST່້໏໚扺qual;檯lantEqual;扼ilde;找me;怳Ādp໩໮uct;戏ortionĀ;aȥ໹l;戝Āci༁༆r;쀀𝒫;䎨ȀUfos༑༖༛༟OT耻"䀢r;쀀𝔔pf;愚cr;쀀𝒬؀BEacefhiorsu༾གྷཇའཱིྦྷྪྭ႖ႩႴႾarr;椐G耻®䂮ƀcnrཎནབute;䅔g;柫rĀ;tཛྷཝ憠l;椖ƀaeyཧཬཱron;䅘dil;䅖;䐠Ā;vླྀཹ愜erseĀEUྂྙĀlq྇ྎement;戋uilibrium;懋pEquilibrium;楯r»ཹo;䎡ghtЀACDFTUVa࿁࿫࿳ဢဨၛႇϘĀnr࿆࿒gleBracket;柩rowƀ;BL࿜࿝࿡憒ar;懥eftArrow;懄eiling;按oǵ࿹\0စbleBracket;柧nǔည\0နeeVector;楝ectorĀ;Bဝသ懂ar;楕loor;挋Āerိ၃eƀ;AVဵံြ抢rrow;憦ector;楛iangleƀ;BEၐၑၕ抳ar;槐qual;抵pƀDTVၣၮၸownVector;楏eeVector;楜ectorĀ;Bႂႃ憾ar;楔ectorĀ;B႑႒懀ar;楓Āpuႛ႞f;愝ndImplies;楰ightarrow;懛ĀchႹႼr;愛;憱leDelayed;槴ڀHOacfhimoqstuფჱჷჽᄙᄞᅑᅖᅡᅧᆵᆻᆿĀCcჩხHcy;䐩y;䐨FTcy;䐬cute;䅚ʀ;aeiyᄈᄉᄎᄓᄗ檼ron;䅠dil;䅞rc;䅜;䐡r;쀀𝔖ortȀDLRUᄪᄴᄾᅉownArrow»ОeftArrow»࢚ightArrow»࿝pArrow;憑gma;䎣allCircle;战pf;쀀𝕊ɲᅭ\0\0ᅰt;戚areȀ;ISUᅻᅼᆉᆯ斡ntersection;抓uĀbpᆏᆞsetĀ;Eᆗᆘ抏qual;抑ersetĀ;Eᆨᆩ抐qual;抒nion;抔cr;쀀𝒮ar;拆ȀbcmpᇈᇛሉላĀ;sᇍᇎ拐etĀ;Eᇍᇕqual;抆ĀchᇠህeedsȀ;ESTᇭᇮᇴᇿ扻qual;檰lantEqual;扽ilde;承Tháྌ;我ƀ;esሒሓሣ拑rsetĀ;Eሜም抃qual;抇et»ሓրHRSacfhiorsሾቄ቉ቕ቞ቱቶኟዂወዑORN耻Þ䃞ADE;愢ĀHc቎ቒcy;䐋y;䐦Ābuቚቜ;䀉;䎤ƀaeyብቪቯron;䅤dil;䅢;䐢r;쀀𝔗Āeiቻ኉ǲኀ\0ኇefore;戴a;䎘Ācn኎ኘkSpace;쀀  Space;怉ldeȀ;EFTካኬኲኼ戼qual;扃ullEqual;扅ilde;扈pf;쀀𝕋ipleDot;惛Āctዖዛr;쀀𝒯rok;䅦ૡዷጎጚጦ\0ጬጱ\0\0\0\0\0ጸጽ፷ᎅ\0᏿ᐄᐊᐐĀcrዻጁute耻Ú䃚rĀ;oጇገ憟cir;楉rǣጓ\0጖y;䐎ve;䅬Āiyጞጣrc耻Û䃛;䐣blac;䅰r;쀀𝔘rave耻Ù䃙acr;䅪Ādiፁ፩erĀBPፈ፝Āarፍፐr;䁟acĀekፗፙ;揟et;掵arenthesis;揝onĀ;P፰፱拃lus;抎Āgp፻፿on;䅲f;쀀𝕌ЀADETadps᎕ᎮᎸᏄϨᏒᏗᏳrrowƀ;BDᅐᎠᎤar;椒ownArrow;懅ownArrow;憕quilibrium;楮eeĀ;AᏋᏌ报rrow;憥ownáϳerĀLRᏞᏨeftArrow;憖ightArrow;憗iĀ;lᏹᏺ䏒on;䎥ing;䅮cr;쀀𝒰ilde;䅨ml耻Ü䃜ҀDbcdefosvᐧᐬᐰᐳᐾᒅᒊᒐᒖash;披ar;櫫y;䐒ashĀ;lᐻᐼ抩;櫦Āerᑃᑅ;拁ƀbtyᑌᑐᑺar;怖Ā;iᑏᑕcalȀBLSTᑡᑥᑪᑴar;戣ine;䁼eparator;杘ilde;所ThinSpace;怊r;쀀𝔙pf;쀀𝕍cr;쀀𝒱dash;抪ʀcefosᒧᒬᒱᒶᒼirc;䅴dge;拀r;쀀𝔚pf;쀀𝕎cr;쀀𝒲Ȁfiosᓋᓐᓒᓘr;쀀𝔛;䎞pf;쀀𝕏cr;쀀𝒳ҀAIUacfosuᓱᓵᓹᓽᔄᔏᔔᔚᔠcy;䐯cy;䐇cy;䐮cute耻Ý䃝Āiyᔉᔍrc;䅶;䐫r;쀀𝔜pf;쀀𝕐cr;쀀𝒴ml;䅸ЀHacdefosᔵᔹᔿᕋᕏᕝᕠᕤcy;䐖cute;䅹Āayᕄᕉron;䅽;䐗ot;䅻ǲᕔ\0ᕛoWidtè૙a;䎖r;愨pf;愤cr;쀀𝒵௡ᖃᖊᖐ\0ᖰᖶᖿ\0\0\0\0ᗆᗛᗫᙟ᙭\0ᚕ᚛ᚲᚹ\0ᚾcute耻á䃡reve;䄃̀;Ediuyᖜᖝᖡᖣᖨᖭ戾;쀀∾̳;房rc耻â䃢te肻´̆;䐰lig耻æ䃦Ā;r²ᖺ;쀀𝔞rave耻à䃠ĀepᗊᗖĀfpᗏᗔsym;愵èᗓha;䎱ĀapᗟcĀclᗤᗧr;䄁g;樿ɤᗰ\0\0ᘊʀ;adsvᗺᗻᗿᘁᘇ戧nd;橕;橜lope;橘;橚΀;elmrszᘘᘙᘛᘞᘿᙏᙙ戠;榤e»ᘙsdĀ;aᘥᘦ戡ѡᘰᘲᘴᘶᘸᘺᘼᘾ;榨;榩;榪;榫;榬;榭;榮;榯tĀ;vᙅᙆ戟bĀ;dᙌᙍ抾;榝Āptᙔᙗh;戢»¹arr;捼Āgpᙣᙧon;䄅f;쀀𝕒΀;Eaeiop዁ᙻᙽᚂᚄᚇᚊ;橰cir;橯;扊d;手s;䀧roxĀ;e዁ᚒñᚃing耻å䃥ƀctyᚡᚦᚨr;쀀𝒶;䀪mpĀ;e዁ᚯñʈilde耻ã䃣ml耻ä䃤Āciᛂᛈoninôɲnt;樑ࠀNabcdefiklnoprsu᛭ᛱᜰ᜼ᝃᝈ᝸᝽០៦ᠹᡐᜍ᤽᥈ᥰot;櫭Ācrᛶ᜞kȀcepsᜀᜅᜍᜓong;扌psilon;䏶rime;怵imĀ;e᜚᜛戽q;拍Ŷᜢᜦee;抽edĀ;gᜬᜭ挅e»ᜭrkĀ;t፜᜷brk;掶Āoyᜁᝁ;䐱quo;怞ʀcmprtᝓ᝛ᝡᝤᝨausĀ;eĊĉptyv;榰séᜌnoõēƀahwᝯ᝱ᝳ;䎲;愶een;扬r;쀀𝔟g΀costuvwឍឝឳេ៕៛៞ƀaiuបពរðݠrc;旯p»፱ƀdptឤឨឭot;樀lus;樁imes;樂ɱឹ\0\0ើcup;樆ar;昅riangleĀdu៍្own;施p;斳plus;樄eåᑄåᒭarow;植ƀako៭ᠦᠵĀcn៲ᠣkƀlst៺֫᠂ozenge;槫riangleȀ;dlr᠒᠓᠘᠝斴own;斾eft;旂ight;斸k;搣Ʊᠫ\0ᠳƲᠯ\0ᠱ;斒;斑4;斓ck;斈ĀeoᠾᡍĀ;qᡃᡆ쀀=⃥uiv;쀀≡⃥t;挐Ȁptwxᡙᡞᡧᡬf;쀀𝕓Ā;tᏋᡣom»Ꮜtie;拈؀DHUVbdhmptuvᢅᢖᢪᢻᣗᣛᣬ᣿ᤅᤊᤐᤡȀLRlrᢎᢐᢒᢔ;敗;敔;敖;敓ʀ;DUduᢡᢢᢤᢦᢨ敐;敦;敩;敤;敧ȀLRlrᢳᢵᢷᢹ;敝;敚;敜;教΀;HLRhlrᣊᣋᣍᣏᣑᣓᣕ救;敬;散;敠;敫;敢;敟ox;槉ȀLRlrᣤᣦᣨᣪ;敕;敒;攐;攌ʀ;DUduڽ᣷᣹᣻᣽;敥;敨;攬;攴inus;抟lus;択imes;抠ȀLRlrᤙᤛᤝ᤟;敛;敘;攘;攔΀;HLRhlrᤰᤱᤳᤵᤷ᤻᤹攂;敪;敡;敞;攼;攤;攜Āevģ᥂bar耻¦䂦Ȁceioᥑᥖᥚᥠr;쀀𝒷mi;恏mĀ;e᜚᜜lƀ;bhᥨᥩᥫ䁜;槅sub;柈Ŭᥴ᥾lĀ;e᥹᥺怢t»᥺pƀ;Eeįᦅᦇ;檮Ā;qۜۛೡᦧ\0᧨ᨑᨕᨲ\0ᨷᩐ\0\0᪴\0\0᫁\0\0ᬡᬮ᭍᭒\0᯽\0ᰌƀcpr᦭ᦲ᧝ute;䄇̀;abcdsᦿᧀᧄ᧊᧕᧙戩nd;橄rcup;橉Āau᧏᧒p;橋p;橇ot;橀;쀀∩︀Āeo᧢᧥t;恁îړȀaeiu᧰᧻ᨁᨅǰ᧵\0᧸s;橍on;䄍dil耻ç䃧rc;䄉psĀ;sᨌᨍ橌m;橐ot;䄋ƀdmnᨛᨠᨦil肻¸ƭptyv;榲t脀¢;eᨭᨮ䂢räƲr;쀀𝔠ƀceiᨽᩀᩍy;䑇ckĀ;mᩇᩈ朓ark»ᩈ;䏇r΀;Ecefms᩟᩠ᩢᩫ᪤᪪᪮旋;槃ƀ;elᩩᩪᩭ䋆q;扗eɡᩴ\0\0᪈rrowĀlr᩼᪁eft;憺ight;憻ʀRSacd᪒᪔᪖᪚᪟»ཇ;擈st;抛irc;抚ash;抝nint;樐id;櫯cir;槂ubsĀ;u᪻᪼晣it»᪼ˬ᫇᫔᫺\0ᬊonĀ;eᫍᫎ䀺Ā;qÇÆɭ᫙\0\0᫢aĀ;t᫞᫟䀬;䁀ƀ;fl᫨᫩᫫戁îᅠeĀmx᫱᫶ent»᫩eóɍǧ᫾\0ᬇĀ;dኻᬂot;橭nôɆƀfryᬐᬔᬗ;쀀𝕔oäɔ脀©;sŕᬝr;愗Āaoᬥᬩrr;憵ss;朗Ācuᬲᬷr;쀀𝒸Ābpᬼ᭄Ā;eᭁᭂ櫏;櫑Ā;eᭉᭊ櫐;櫒dot;拯΀delprvw᭠᭬᭷ᮂᮬᯔ᯹arrĀlr᭨᭪;椸;椵ɰ᭲\0\0᭵r;拞c;拟arrĀ;p᭿ᮀ憶;椽̀;bcdosᮏᮐᮖᮡᮥᮨ截rcap;橈Āauᮛᮞp;橆p;橊ot;抍r;橅;쀀∪︀Ȁalrv᮵ᮿᯞᯣrrĀ;mᮼᮽ憷;椼yƀevwᯇᯔᯘqɰᯎ\0\0ᯒreã᭳uã᭵ee;拎edge;拏en耻¤䂤earrowĀlrᯮ᯳eft»ᮀight»ᮽeäᯝĀciᰁᰇoninôǷnt;戱lcty;挭ঀAHabcdefhijlorstuwz᰸᰻᰿ᱝᱩᱵᲊᲞᲬᲷ᳻᳿ᴍᵻᶑᶫᶻ᷆᷍rò΁ar;楥Ȁglrs᱈ᱍ᱒᱔ger;怠eth;愸òᄳhĀ;vᱚᱛ怐»ऊūᱡᱧarow;椏aã̕Āayᱮᱳron;䄏;䐴ƀ;ao̲ᱼᲄĀgrʿᲁr;懊tseq;橷ƀglmᲑᲔᲘ耻°䂰ta;䎴ptyv;榱ĀirᲣᲨsht;楿;쀀𝔡arĀlrᲳᲵ»ࣜ»သʀaegsv᳂͸᳖᳜᳠mƀ;oș᳊᳔ndĀ;ș᳑uit;晦amma;䏝in;拲ƀ;io᳧᳨᳸䃷de脀÷;o᳧ᳰntimes;拇nø᳷cy;䑒cɯᴆ\0\0ᴊrn;挞op;挍ʀlptuwᴘᴝᴢᵉᵕlar;䀤f;쀀𝕕ʀ;emps̋ᴭᴷᴽᵂqĀ;d͒ᴳot;扑inus;戸lus;戔quare;抡blebarwedgåúnƀadhᄮᵝᵧownarrowóᲃarpoonĀlrᵲᵶefôᲴighôᲶŢᵿᶅkaro÷གɯᶊ\0\0ᶎrn;挟op;挌ƀcotᶘᶣᶦĀryᶝᶡ;쀀𝒹;䑕l;槶rok;䄑Ādrᶰᶴot;拱iĀ;fᶺ᠖斿Āah᷀᷃ròЩaòྦangle;榦Āci᷒ᷕy;䑟grarr;柿ऀDacdefglmnopqrstuxḁḉḙḸոḼṉṡṾấắẽỡἪἷὄ὎὚ĀDoḆᴴoôᲉĀcsḎḔute耻é䃩ter;橮ȀaioyḢḧḱḶron;䄛rĀ;cḭḮ扖耻ê䃪lon;払;䑍ot;䄗ĀDrṁṅot;扒;쀀𝔢ƀ;rsṐṑṗ檚ave耻è䃨Ā;dṜṝ檖ot;檘Ȁ;ilsṪṫṲṴ檙nters;揧;愓Ā;dṹṺ檕ot;檗ƀapsẅẉẗcr;䄓tyƀ;svẒẓẕ戅et»ẓpĀ1;ẝẤĳạả;怄;怅怃ĀgsẪẬ;䅋p;怂ĀgpẴẸon;䄙f;쀀𝕖ƀalsỄỎỒrĀ;sỊị拕l;槣us;橱iƀ;lvỚớở䎵on»ớ;䏵ȀcsuvỪỳἋἣĀioữḱrc»Ḯɩỹ\0\0ỻíՈantĀglἂἆtr»ṝess»Ṻƀaeiἒ἖Ἒls;䀽st;扟vĀ;DȵἠD;橸parsl;槥ĀDaἯἳot;打rr;楱ƀcdiἾὁỸr;愯oô͒ĀahὉὋ;䎷耻ð䃰Āmrὓὗl耻ë䃫o;悬ƀcipὡὤὧl;䀡sôծĀeoὬὴctatioîՙnentialåչৡᾒ\0ᾞ\0ᾡᾧ\0\0ῆῌ\0ΐ\0ῦῪ \0 ⁚llingdotseñṄy;䑄male;晀ƀilrᾭᾳ῁lig;耀ﬃɩᾹ\0\0᾽g;耀ﬀig;耀ﬄ;쀀𝔣lig;耀ﬁlig;쀀fjƀaltῙ῜ῡt;晭ig;耀ﬂns;斱of;䆒ǰ΅\0ῳf;쀀𝕗ĀakֿῷĀ;vῼ´拔;櫙artint;樍Āao‌⁕Ācs‑⁒α‚‰‸⁅⁈\0⁐β•‥‧‪‬\0‮耻½䂽;慓耻¼䂼;慕;慙;慛Ƴ‴\0‶;慔;慖ʴ‾⁁\0\0⁃耻¾䂾;慗;慜5;慘ƶ⁌\0⁎;慚;慝8;慞l;恄wn;挢cr;쀀𝒻ࢀEabcdefgijlnorstv₂₉₟₥₰₴⃰⃵⃺⃿℃ℒℸ̗ℾ⅒↞Ā;lٍ₇;檌ƀcmpₐₕ₝ute;䇵maĀ;dₜ᳚䎳;檆reve;䄟Āiy₪₮rc;䄝;䐳ot;䄡Ȁ;lqsؾق₽⃉ƀ;qsؾٌ⃄lanô٥Ȁ;cdl٥⃒⃥⃕c;檩otĀ;o⃜⃝檀Ā;l⃢⃣檂;檄Ā;e⃪⃭쀀⋛︀s;檔r;쀀𝔤Ā;gٳ؛mel;愷cy;䑓Ȁ;Eajٚℌℎℐ;檒;檥;檤ȀEaesℛℝ℩ℴ;扩pĀ;p℣ℤ檊rox»ℤĀ;q℮ℯ檈Ā;q℮ℛim;拧pf;쀀𝕘Āci⅃ⅆr;愊mƀ;el٫ⅎ⅐;檎;檐茀>;cdlqr׮ⅠⅪⅮⅳⅹĀciⅥⅧ;檧r;橺ot;拗Par;榕uest;橼ʀadelsↄⅪ←ٖ↛ǰ↉\0↎proø₞r;楸qĀlqؿ↖lesó₈ií٫Āen↣↭rtneqq;쀀≩︀Å↪ԀAabcefkosy⇄⇇⇱⇵⇺∘∝∯≨≽ròΠȀilmr⇐⇔⇗⇛rsðᒄf»․ilôکĀdr⇠⇤cy;䑊ƀ;cwࣴ⇫⇯ir;楈;憭ar;意irc;䄥ƀalr∁∎∓rtsĀ;u∉∊晥it»∊lip;怦con;抹r;쀀𝔥sĀew∣∩arow;椥arow;椦ʀamopr∺∾≃≞≣rr;懿tht;戻kĀlr≉≓eftarrow;憩ightarrow;憪f;쀀𝕙bar;怕ƀclt≯≴≸r;쀀𝒽asè⇴rok;䄧Ābp⊂⊇ull;恃hen»ᱛૡ⊣\0⊪\0⊸⋅⋎\0⋕⋳\0\0⋸⌢⍧⍢⍿\0⎆⎪⎴cute耻í䃭ƀ;iyݱ⊰⊵rc耻î䃮;䐸Ācx⊼⊿y;䐵cl耻¡䂡ĀfrΟ⋉;쀀𝔦rave耻ì䃬Ȁ;inoܾ⋝⋩⋮Āin⋢⋦nt;樌t;戭fin;槜ta;愩lig;䄳ƀaop⋾⌚⌝ƀcgt⌅⌈⌗r;䄫ƀelpܟ⌏⌓inåގarôܠh;䄱f;抷ed;䆵ʀ;cfotӴ⌬⌱⌽⍁are;愅inĀ;t⌸⌹戞ie;槝doô⌙ʀ;celpݗ⍌⍐⍛⍡al;抺Āgr⍕⍙eróᕣã⍍arhk;樗rod;樼Ȁcgpt⍯⍲⍶⍻y;䑑on;䄯f;쀀𝕚a;䎹uest耻¿䂿Āci⎊⎏r;쀀𝒾nʀ;EdsvӴ⎛⎝⎡ӳ;拹ot;拵Ā;v⎦⎧拴;拳Ā;iݷ⎮lde;䄩ǫ⎸\0⎼cy;䑖l耻ï䃯̀cfmosu⏌⏗⏜⏡⏧⏵Āiy⏑⏕rc;䄵;䐹r;쀀𝔧ath;䈷pf;쀀𝕛ǣ⏬\0⏱r;쀀𝒿rcy;䑘kcy;䑔Ѐacfghjos␋␖␢␧␭␱␵␻ppaĀ;v␓␔䎺;䏰Āey␛␠dil;䄷;䐺r;쀀𝔨reen;䄸cy;䑅cy;䑜pf;쀀𝕜cr;쀀𝓀஀ABEHabcdefghjlmnoprstuv⑰⒁⒆⒍⒑┎┽╚▀♎♞♥♹♽⚚⚲⛘❝❨➋⟀⠁⠒ƀart⑷⑺⑼rò৆òΕail;椛arr;椎Ā;gঔ⒋;檋ar;楢ॣ⒥\0⒪\0⒱\0\0\0\0\0⒵Ⓔ\0ⓆⓈⓍ\0⓹ute;䄺mptyv;榴raîࡌbda;䎻gƀ;dlࢎⓁⓃ;榑åࢎ;檅uo耻«䂫rЀ;bfhlpst࢙ⓞⓦⓩ⓫⓮⓱⓵Ā;f࢝ⓣs;椟s;椝ë≒p;憫l;椹im;楳l;憢ƀ;ae⓿─┄檫il;椙Ā;s┉┊檭;쀀⪭︀ƀabr┕┙┝rr;椌rk;杲Āak┢┬cĀek┨┪;䁻;䁛Āes┱┳;榋lĀdu┹┻;榏;榍Ȁaeuy╆╋╖╘ron;䄾Ādi═╔il;䄼ìࢰâ┩;䐻Ȁcqrs╣╦╭╽a;椶uoĀ;rนᝆĀdu╲╷har;楧shar;楋h;憲ʀ;fgqs▋▌উ◳◿扤tʀahlrt▘▤▷◂◨rrowĀ;t࢙□aé⓶arpoonĀdu▯▴own»њp»०eftarrows;懇ightƀahs◍◖◞rrowĀ;sࣴࢧarpoonó྘quigarro÷⇰hreetimes;拋ƀ;qs▋ও◺lanôবʀ;cdgsব☊☍☝☨c;檨otĀ;o☔☕橿Ā;r☚☛檁;檃Ā;e☢☥쀀⋚︀s;檓ʀadegs☳☹☽♉♋pproøⓆot;拖qĀgq♃♅ôউgtò⒌ôছiíলƀilr♕࣡♚sht;楼;쀀𝔩Ā;Eজ♣;檑š♩♶rĀdu▲♮Ā;l॥♳;楪lk;斄cy;䑙ʀ;achtੈ⚈⚋⚑⚖rò◁orneòᴈard;楫ri;旺Āio⚟⚤dot;䅀ustĀ;a⚬⚭掰che»⚭ȀEaes⚻⚽⛉⛔;扨pĀ;p⛃⛄檉rox»⛄Ā;q⛎⛏檇Ā;q⛎⚻im;拦Ѐabnoptwz⛩⛴⛷✚✯❁❇❐Ānr⛮⛱g;柬r;懽rëࣁgƀlmr⛿✍✔eftĀar০✇ightá৲apsto;柼ightá৽parrowĀlr✥✩efô⓭ight;憬ƀafl✶✹✽r;榅;쀀𝕝us;樭imes;樴š❋❏st;戗áፎƀ;ef❗❘᠀旊nge»❘arĀ;l❤❥䀨t;榓ʀachmt❳❶❼➅➇ròࢨorneòᶌarĀ;d྘➃;業;怎ri;抿̀achiqt➘➝ੀ➢➮➻quo;怹r;쀀𝓁mƀ;egল➪➬;檍;檏Ābu┪➳oĀ;rฟ➹;怚rok;䅂萀<;cdhilqrࠫ⟒☹⟜⟠⟥⟪⟰Āci⟗⟙;檦r;橹reå◲mes;拉arr;楶uest;橻ĀPi⟵⟹ar;榖ƀ;ef⠀भ᠛旃rĀdu⠇⠍shar;楊har;楦Āen⠗⠡rtneqq;쀀≨︀Å⠞܀Dacdefhilnopsu⡀⡅⢂⢎⢓⢠⢥⢨⣚⣢⣤ઃ⣳⤂Dot;戺Ȁclpr⡎⡒⡣⡽r耻¯䂯Āet⡗⡙;時Ā;e⡞⡟朠se»⡟Ā;sျ⡨toȀ;dluျ⡳⡷⡻owîҌefôएðᏑker;斮Āoy⢇⢌mma;権;䐼ash;怔asuredangle»ᘦr;쀀𝔪o;愧ƀcdn⢯⢴⣉ro耻µ䂵Ȁ;acdᑤ⢽⣀⣄sôᚧir;櫰ot肻·Ƶusƀ;bd⣒ᤃ⣓戒Ā;uᴼ⣘;横ţ⣞⣡p;櫛ò−ðઁĀdp⣩⣮els;抧f;쀀𝕞Āct⣸⣽r;쀀𝓂pos»ᖝƀ;lm⤉⤊⤍䎼timap;抸ఀGLRVabcdefghijlmoprstuvw⥂⥓⥾⦉⦘⧚⧩⨕⨚⩘⩝⪃⪕⪤⪨⬄⬇⭄⭿⮮ⰴⱧⱼ⳩Āgt⥇⥋;쀀⋙̸Ā;v⥐௏쀀≫⃒ƀelt⥚⥲⥶ftĀar⥡⥧rrow;懍ightarrow;懎;쀀⋘̸Ā;v⥻ే쀀≪⃒ightarrow;懏ĀDd⦎⦓ash;抯ash;抮ʀbcnpt⦣⦧⦬⦱⧌la»˞ute;䅄g;쀀∠⃒ʀ;Eiop඄⦼⧀⧅⧈;쀀⩰̸d;쀀≋̸s;䅉roø඄urĀ;a⧓⧔普lĀ;s⧓ସǳ⧟\0⧣p肻 ଷmpĀ;e௹ఀʀaeouy⧴⧾⨃⨐⨓ǰ⧹\0⧻;橃on;䅈dil;䅆ngĀ;dൾ⨊ot;쀀⩭̸p;橂;䐽ash;怓΀;Aadqsxஒ⨩⨭⨻⩁⩅⩐rr;懗rĀhr⨳⨶k;椤Ā;oᏲᏰot;쀀≐̸uiöୣĀei⩊⩎ar;椨í஘istĀ;s஠டr;쀀𝔫ȀEest௅⩦⩹⩼ƀ;qs஼⩭௡ƀ;qs஼௅⩴lanô௢ií௪Ā;rஶ⪁»ஷƀAap⪊⪍⪑rò⥱rr;憮ar;櫲ƀ;svྍ⪜ྌĀ;d⪡⪢拼;拺cy;䑚΀AEadest⪷⪺⪾⫂⫅⫶⫹rò⥦;쀀≦̸rr;憚r;急Ȁ;fqs఻⫎⫣⫯tĀar⫔⫙rro÷⫁ightarro÷⪐ƀ;qs఻⪺⫪lanôౕĀ;sౕ⫴»శiíౝĀ;rవ⫾iĀ;eచథiäඐĀpt⬌⬑f;쀀𝕟膀¬;in⬙⬚⬶䂬nȀ;Edvஉ⬤⬨⬮;쀀⋹̸ot;쀀⋵̸ǡஉ⬳⬵;拷;拶iĀ;vಸ⬼ǡಸ⭁⭃;拾;拽ƀaor⭋⭣⭩rȀ;ast୻⭕⭚⭟lleì୻l;쀀⫽⃥;쀀∂̸lint;樔ƀ;ceಒ⭰⭳uåಥĀ;cಘ⭸Ā;eಒ⭽ñಘȀAait⮈⮋⮝⮧rò⦈rrƀ;cw⮔⮕⮙憛;쀀⤳̸;쀀↝̸ghtarrow»⮕riĀ;eೋೖ΀chimpqu⮽⯍⯙⬄୸⯤⯯Ȁ;cerല⯆ഷ⯉uå൅;쀀𝓃ortɭ⬅\0\0⯖ará⭖mĀ;e൮⯟Ā;q൴൳suĀbp⯫⯭å೸åഋƀbcp⯶ⰑⰙȀ;Ees⯿ⰀഢⰄ抄;쀀⫅̸etĀ;eഛⰋqĀ;qണⰀcĀ;eലⰗñസȀ;EesⰢⰣൟⰧ抅;쀀⫆̸etĀ;e൘ⰮqĀ;qൠⰣȀgilrⰽⰿⱅⱇìௗlde耻ñ䃱çృiangleĀlrⱒⱜeftĀ;eచⱚñదightĀ;eೋⱥñ೗Ā;mⱬⱭ䎽ƀ;esⱴⱵⱹ䀣ro;愖p;怇ҀDHadgilrsⲏⲔⲙⲞⲣⲰⲶⳓⳣash;抭arr;椄p;쀀≍⃒ash;抬ĀetⲨⲬ;쀀≥⃒;쀀>⃒nfin;槞ƀAetⲽⳁⳅrr;椂;쀀≤⃒Ā;rⳊⳍ쀀<⃒ie;쀀⊴⃒ĀAtⳘⳜrr;椃rie;쀀⊵⃒im;쀀∼⃒ƀAan⳰⳴ⴂrr;懖rĀhr⳺⳽k;椣Ā;oᏧᏥear;椧ቓ᪕\0\0\0\0\0\0\0\0\0\0\0\0\0ⴭ\0ⴸⵈⵠⵥ⵲ⶄᬇ\0\0ⶍⶫ\0ⷈⷎ\0ⷜ⸙⸫⸾⹃Ācsⴱ᪗ute耻ó䃳ĀiyⴼⵅrĀ;c᪞ⵂ耻ô䃴;䐾ʀabios᪠ⵒⵗǈⵚlac;䅑v;樸old;榼lig;䅓Ācr⵩⵭ir;榿;쀀𝔬ͯ⵹\0\0⵼\0ⶂn;䋛ave耻ò䃲;槁Ābmⶈ෴ar;榵Ȁacitⶕ⶘ⶥⶨrò᪀Āir⶝ⶠr;榾oss;榻nå๒;槀ƀaeiⶱⶵⶹcr;䅍ga;䏉ƀcdnⷀⷅǍron;䎿;榶pf;쀀𝕠ƀaelⷔ⷗ǒr;榷rp;榹΀;adiosvⷪⷫⷮ⸈⸍⸐⸖戨rò᪆Ȁ;efmⷷⷸ⸂⸅橝rĀ;oⷾⷿ愴f»ⷿ耻ª䂪耻º䂺gof;抶r;橖lope;橗;橛ƀclo⸟⸡⸧ò⸁ash耻ø䃸l;折iŬⸯ⸴de耻õ䃵esĀ;aǛ⸺s;樶ml耻ö䃶bar;挽ૡ⹞\0⹽\0⺀⺝\0⺢⺹\0\0⻋ຜ\0⼓\0\0⼫⾼\0⿈rȀ;astЃ⹧⹲຅脀¶;l⹭⹮䂶leìЃɩ⹸\0\0⹻m;櫳;櫽y;䐿rʀcimpt⺋⺏⺓ᡥ⺗nt;䀥od;䀮il;怰enk;怱r;쀀𝔭ƀimo⺨⺰⺴Ā;v⺭⺮䏆;䏕maô੶ne;明ƀ;tv⺿⻀⻈䏀chfork»´;䏖Āau⻏⻟nĀck⻕⻝kĀ;h⇴⻛;愎ö⇴sҀ;abcdemst⻳⻴ᤈ⻹⻽⼄⼆⼊⼎䀫cir;樣ir;樢Āouᵀ⼂;樥;橲n肻±ຝim;樦wo;樧ƀipu⼙⼠⼥ntint;樕f;쀀𝕡nd耻£䂣Ԁ;Eaceinosu່⼿⽁⽄⽇⾁⾉⾒⽾⾶;檳p;檷uå໙Ā;c໎⽌̀;acens່⽙⽟⽦⽨⽾pproø⽃urlyeñ໙ñ໎ƀaes⽯⽶⽺pprox;檹qq;檵im;拨iíໟmeĀ;s⾈ຮ怲ƀEas⽸⾐⽺ð⽵ƀdfp໬⾙⾯ƀals⾠⾥⾪lar;挮ine;挒urf;挓Ā;t໻⾴ï໻rel;抰Āci⿀⿅r;쀀𝓅;䏈ncsp;怈̀fiopsu⿚⋢⿟⿥⿫⿱r;쀀𝔮pf;쀀𝕢rime;恗cr;쀀𝓆ƀaeo⿸〉〓tĀei⿾々rnionóڰnt;樖stĀ;e【】䀿ñἙô༔઀ABHabcdefhilmnoprstux぀けさすムㄎㄫㅇㅢㅲㆎ㈆㈕㈤㈩㉘㉮㉲㊐㊰㊷ƀartぇおがròႳòϝail;検aròᱥar;楤΀cdenqrtとふへみわゔヌĀeuねぱ;쀀∽̱te;䅕iãᅮmptyv;榳gȀ;del࿑らるろ;榒;榥å࿑uo耻»䂻rր;abcfhlpstw࿜ガクシスゼゾダッデナp;極Ā;f࿠ゴs;椠;椳s;椞ë≝ð✮l;楅im;楴l;憣;憝Āaiパフil;椚oĀ;nホボ戶aló༞ƀabrョリヮrò៥rk;杳ĀakンヽcĀekヹ・;䁽;䁝Āes㄂㄄;榌lĀduㄊㄌ;榎;榐Ȁaeuyㄗㄜㄧㄩron;䅙Ādiㄡㄥil;䅗ì࿲âヺ;䑀Ȁclqsㄴㄷㄽㅄa;椷dhar;楩uoĀ;rȎȍh;憳ƀacgㅎㅟངlȀ;ipsླྀㅘㅛႜnåႻarôྩt;断ƀilrㅩဣㅮsht;楽;쀀𝔯ĀaoㅷㆆrĀduㅽㅿ»ѻĀ;l႑ㆄ;楬Ā;vㆋㆌ䏁;䏱ƀgns㆕ㇹㇼht̀ahlrstㆤㆰ㇂㇘㇤㇮rrowĀ;t࿜ㆭaéトarpoonĀduㆻㆿowîㅾp»႒eftĀah㇊㇐rrowó࿪arpoonóՑightarrows;應quigarro÷ニhreetimes;拌g;䋚ingdotseñἲƀahm㈍㈐㈓rò࿪aòՑ;怏oustĀ;a㈞㈟掱che»㈟mid;櫮Ȁabpt㈲㈽㉀㉒Ānr㈷㈺g;柭r;懾rëဃƀafl㉇㉊㉎r;榆;쀀𝕣us;樮imes;樵Āap㉝㉧rĀ;g㉣㉤䀩t;榔olint;樒arò㇣Ȁachq㉻㊀Ⴜ㊅quo;怺r;쀀𝓇Ābu・㊊oĀ;rȔȓƀhir㊗㊛㊠reåㇸmes;拊iȀ;efl㊪ၙᠡ㊫方tri;槎luhar;楨;愞ൡ㋕㋛㋟㌬㌸㍱\0㍺㎤\0\0㏬㏰\0㐨㑈㑚㒭㒱㓊㓱\0㘖\0\0㘳cute;䅛quï➺Ԁ;Eaceinpsyᇭ㋳㋵㋿㌂㌋㌏㌟㌦㌩;檴ǰ㋺\0㋼;檸on;䅡uåᇾĀ;dᇳ㌇il;䅟rc;䅝ƀEas㌖㌘㌛;檶p;檺im;择olint;樓iíሄ;䑁otƀ;be㌴ᵇ㌵担;橦΀Aacmstx㍆㍊㍗㍛㍞㍣㍭rr;懘rĀhr㍐㍒ë∨Ā;oਸ਼਴t耻§䂧i;䀻war;椩mĀin㍩ðnuóñt;朶rĀ;o㍶⁕쀀𝔰Ȁacoy㎂㎆㎑㎠rp;景Āhy㎋㎏cy;䑉;䑈rtɭ㎙\0\0㎜iäᑤaraì⹯耻­䂭Āgm㎨㎴maƀ;fv㎱㎲㎲䏃;䏂Ѐ;deglnprካ㏅㏉㏎㏖㏞㏡㏦ot;橪Ā;q኱ኰĀ;E㏓㏔檞;檠Ā;E㏛㏜檝;檟e;扆lus;樤arr;楲aròᄽȀaeit㏸㐈㐏㐗Āls㏽㐄lsetmé㍪hp;樳parsl;槤Ādlᑣ㐔e;挣Ā;e㐜㐝檪Ā;s㐢㐣檬;쀀⪬︀ƀflp㐮㐳㑂tcy;䑌Ā;b㐸㐹䀯Ā;a㐾㐿槄r;挿f;쀀𝕤aĀdr㑍ЂesĀ;u㑔㑕晠it»㑕ƀcsu㑠㑹㒟Āau㑥㑯pĀ;sᆈ㑫;쀀⊓︀pĀ;sᆴ㑵;쀀⊔︀uĀbp㑿㒏ƀ;esᆗᆜ㒆etĀ;eᆗ㒍ñᆝƀ;esᆨᆭ㒖etĀ;eᆨ㒝ñᆮƀ;afᅻ㒦ְrť㒫ֱ»ᅼaròᅈȀcemt㒹㒾㓂㓅r;쀀𝓈tmîñiì㐕aræᆾĀar㓎㓕rĀ;f㓔ឿ昆Āan㓚㓭ightĀep㓣㓪psiloîỠhé⺯s»⡒ʀbcmnp㓻㕞ሉ㖋㖎Ҁ;Edemnprs㔎㔏㔑㔕㔞㔣㔬㔱㔶抂;櫅ot;檽Ā;dᇚ㔚ot;櫃ult;櫁ĀEe㔨㔪;櫋;把lus;檿arr;楹ƀeiu㔽㕒㕕tƀ;en㔎㕅㕋qĀ;qᇚ㔏eqĀ;q㔫㔨m;櫇Ābp㕚㕜;櫕;櫓c̀;acensᇭ㕬㕲㕹㕻㌦pproø㋺urlyeñᇾñᇳƀaes㖂㖈㌛pproø㌚qñ㌗g;晪ڀ123;Edehlmnps㖩㖬㖯ሜ㖲㖴㗀㗉㗕㗚㗟㗨㗭耻¹䂹耻²䂲耻³䂳;櫆Āos㖹㖼t;檾ub;櫘Ā;dሢ㗅ot;櫄sĀou㗏㗒l;柉b;櫗arr;楻ult;櫂ĀEe㗤㗦;櫌;抋lus;櫀ƀeiu㗴㘉㘌tƀ;enሜ㗼㘂qĀ;qሢ㖲eqĀ;q㗧㗤m;櫈Ābp㘑㘓;櫔;櫖ƀAan㘜㘠㘭rr;懙rĀhr㘦㘨ë∮Ā;oਫ਩war;椪lig耻ß䃟௡㙑㙝㙠ዎ㙳㙹\0㙾㛂\0\0\0\0\0㛛㜃\0㜉㝬\0\0\0㞇ɲ㙖\0\0㙛get;挖;䏄rë๟ƀaey㙦㙫㙰ron;䅥dil;䅣;䑂lrec;挕r;쀀𝔱Ȁeiko㚆㚝㚵㚼ǲ㚋\0㚑eĀ4fኄኁaƀ;sv㚘㚙㚛䎸ym;䏑Ācn㚢㚲kĀas㚨㚮pproø዁im»ኬsðኞĀas㚺㚮ð዁rn耻þ䃾Ǭ̟㛆⋧es膀×;bd㛏㛐㛘䃗Ā;aᤏ㛕r;樱;樰ƀeps㛡㛣㜀á⩍Ȁ;bcf҆㛬㛰㛴ot;挶ir;櫱Ā;o㛹㛼쀀𝕥rk;櫚á㍢rime;怴ƀaip㜏㜒㝤dåቈ΀adempst㜡㝍㝀㝑㝗㝜㝟ngleʀ;dlqr㜰㜱㜶㝀㝂斵own»ᶻeftĀ;e⠀㜾ñम;扜ightĀ;e㊪㝋ñၚot;旬inus;樺lus;樹b;槍ime;樻ezium;揢ƀcht㝲㝽㞁Āry㝷㝻;쀀𝓉;䑆cy;䑛rok;䅧Āio㞋㞎xô᝷headĀlr㞗㞠eftarro÷ࡏightarrow»ཝऀAHabcdfghlmoprstuw㟐㟓㟗㟤㟰㟼㠎㠜㠣㠴㡑㡝㡫㢩㣌㣒㣪㣶ròϭar;楣Ācr㟜㟢ute耻ú䃺òᅐrǣ㟪\0㟭y;䑞ve;䅭Āiy㟵㟺rc耻û䃻;䑃ƀabh㠃㠆㠋ròᎭlac;䅱aòᏃĀir㠓㠘sht;楾;쀀𝔲rave耻ù䃹š㠧㠱rĀlr㠬㠮»ॗ»ႃlk;斀Āct㠹㡍ɯ㠿\0\0㡊rnĀ;e㡅㡆挜r»㡆op;挏ri;旸Āal㡖㡚cr;䅫肻¨͉Āgp㡢㡦on;䅳f;쀀𝕦̀adhlsuᅋ㡸㡽፲㢑㢠ownáᎳarpoonĀlr㢈㢌efô㠭ighô㠯iƀ;hl㢙㢚㢜䏅»ᏺon»㢚parrows;懈ƀcit㢰㣄㣈ɯ㢶\0\0㣁rnĀ;e㢼㢽挝r»㢽op;挎ng;䅯ri;旹cr;쀀𝓊ƀdir㣙㣝㣢ot;拰lde;䅩iĀ;f㜰㣨»᠓Āam㣯㣲rò㢨l耻ü䃼angle;榧ހABDacdeflnoprsz㤜㤟㤩㤭㦵㦸㦽㧟㧤㧨㧳㧹㧽㨁㨠ròϷarĀ;v㤦㤧櫨;櫩asèϡĀnr㤲㤷grt;榜΀eknprst㓣㥆㥋㥒㥝㥤㦖appá␕othinçẖƀhir㓫⻈㥙opô⾵Ā;hᎷ㥢ïㆍĀiu㥩㥭gmá㎳Ābp㥲㦄setneqĀ;q㥽㦀쀀⊊︀;쀀⫋︀setneqĀ;q㦏㦒쀀⊋︀;쀀⫌︀Āhr㦛㦟etá㚜iangleĀlr㦪㦯eft»थight»ၑy;䐲ash»ံƀelr㧄㧒㧗ƀ;beⷪ㧋㧏ar;抻q;扚lip;拮Ābt㧜ᑨaòᑩr;쀀𝔳tré㦮suĀbp㧯㧱»ജ»൙pf;쀀𝕧roð໻tré㦴Ācu㨆㨋r;쀀𝓋Ābp㨐㨘nĀEe㦀㨖»㥾nĀEe㦒㨞»㦐igzag;榚΀cefoprs㨶㨻㩖㩛㩔㩡㩪irc;䅵Ādi㩀㩑Ābg㩅㩉ar;機eĀ;qᗺ㩏;扙erp;愘r;쀀𝔴pf;쀀𝕨Ā;eᑹ㩦atèᑹcr;쀀𝓌ૣណ㪇\0㪋\0㪐㪛\0\0㪝㪨㪫㪯\0\0㫃㫎\0㫘ៜ៟tré៑r;쀀𝔵ĀAa㪔㪗ròσrò৶;䎾ĀAa㪡㪤ròθrò৫að✓is;拻ƀdptឤ㪵㪾Āfl㪺ឩ;쀀𝕩imåឲĀAa㫇㫊ròώròਁĀcq㫒ីr;쀀𝓍Āpt៖㫜ré។Ѐacefiosu㫰㫽㬈㬌㬑㬕㬛㬡cĀuy㫶㫻te耻ý䃽;䑏Āiy㬂㬆rc;䅷;䑋n耻¥䂥r;쀀𝔶cy;䑗pf;쀀𝕪cr;쀀𝓎Ācm㬦㬩y;䑎l耻ÿ䃿Ԁacdefhiosw㭂㭈㭔㭘㭤㭩㭭㭴㭺㮀cute;䅺Āay㭍㭒ron;䅾;䐷ot;䅼Āet㭝㭡træᕟa;䎶r;쀀𝔷cy;䐶grarr;懝pf;쀀𝕫cr;쀀𝓏Ājn㮅㮇;怍j;怌'.split("").map(e=>e.charCodeAt(0))),Ro=new Uint16Array("Ȁaglq	\x1Bɭ\0\0p;䀦os;䀧t;䀾t;䀼uot;䀢".split("").map(e=>e.charCodeAt(0)));var Bu;const No=new Map([[0,65533],[128,8364],[130,8218],[131,402],[132,8222],[133,8230],[134,8224],[135,8225],[136,710],[137,8240],[138,352],[139,8249],[140,338],[142,381],[145,8216],[146,8217],[147,8220],[148,8221],[149,8226],[150,8211],[151,8212],[152,732],[153,8482],[154,353],[155,8250],[156,339],[158,382],[159,376]]),Mo=(Bu=String.fromCodePoint)!==null&&Bu!==void 0?Bu:function(e){let t="";return e>65535&&(e-=65536,t+=String.fromCharCode(e>>>10&1023|55296),e=56320|e&1023),t+=String.fromCharCode(e),t};function jo(e){var t;return e>=55296&&e<=57343||e>1114111?65533:(t=No.get(e))!==null&&t!==void 0?t:e}var K;(function(e){e[e.NUM=35]="NUM",e[e.SEMI=59]="SEMI",e[e.EQUALS=61]="EQUALS",e[e.ZERO=48]="ZERO",e[e.NINE=57]="NINE",e[e.LOWER_A=97]="LOWER_A",e[e.LOWER_F=102]="LOWER_F",e[e.LOWER_X=120]="LOWER_X",e[e.LOWER_Z=122]="LOWER_Z",e[e.UPPER_A=65]="UPPER_A",e[e.UPPER_F=70]="UPPER_F",e[e.UPPER_Z=90]="UPPER_Z"})(K||(K={}));const Lo=32;var Fe;(function(e){e[e.VALUE_LENGTH=49152]="VALUE_LENGTH",e[e.BRANCH_LENGTH=16256]="BRANCH_LENGTH",e[e.JUMP_TABLE=127]="JUMP_TABLE"})(Fe||(Fe={}));function or(e){return e>=K.ZERO&&e<=K.NINE}function Uo(e){return e>=K.UPPER_A&&e<=K.UPPER_F||e>=K.LOWER_A&&e<=K.LOWER_F}function Bo(e){return e>=K.UPPER_A&&e<=K.UPPER_Z||e>=K.LOWER_A&&e<=K.LOWER_Z||or(e)}function qo(e){return e===K.EQUALS||Bo(e)}var G;(function(e){e[e.EntityStart=0]="EntityStart",e[e.NumericStart=1]="NumericStart",e[e.NumericDecimal=2]="NumericDecimal",e[e.NumericHex=3]="NumericHex",e[e.NamedEntity=4]="NamedEntity"})(G||(G={}));var Se;(function(e){e[e.Legacy=0]="Legacy",e[e.Strict=1]="Strict",e[e.Attribute=2]="Attribute"})(Se||(Se={}));class Ho{constructor(t,u,r){this.decodeTree=t,this.emitCodePoint=u,this.errors=r,this.state=G.EntityStart,this.consumed=1,this.result=0,this.treeIndex=0,this.excess=1,this.decodeMode=Se.Strict}startEntity(t){this.decodeMode=t,this.state=G.EntityStart,this.result=0,this.treeIndex=0,this.excess=1,this.consumed=1}write(t,u){switch(this.state){case G.EntityStart:return t.charCodeAt(u)===K.NUM?(this.state=G.NumericStart,this.consumed+=1,this.stateNumericStart(t,u+1)):(this.state=G.NamedEntity,this.stateNamedEntity(t,u));case G.NumericStart:return this.stateNumericStart(t,u);case G.NumericDecimal:return this.stateNumericDecimal(t,u);case G.NumericHex:return this.stateNumericHex(t,u);case G.NamedEntity:return this.stateNamedEntity(t,u)}}stateNumericStart(t,u){return u>=t.length?-1:(t.charCodeAt(u)|Lo)===K.LOWER_X?(this.state=G.NumericHex,this.consumed+=1,this.stateNumericHex(t,u+1)):(this.state=G.NumericDecimal,this.stateNumericDecimal(t,u))}addToNumericResult(t,u,r,i){if(u!==r){const s=r-u;this.result=this.result*Math.pow(i,s)+parseInt(t.substr(u,s),i),this.consumed+=s}}stateNumericHex(t,u){const r=u;for(;u<t.length;){const i=t.charCodeAt(u);if(or(i)||Uo(i))u+=1;else return this.addToNumericResult(t,r,u,16),this.emitNumericEntity(i,3)}return this.addToNumericResult(t,r,u,16),-1}stateNumericDecimal(t,u){const r=u;for(;u<t.length;){const i=t.charCodeAt(u);if(or(i))u+=1;else return this.addToNumericResult(t,r,u,10),this.emitNumericEntity(i,2)}return this.addToNumericResult(t,r,u,10),-1}emitNumericEntity(t,u){var r;if(this.consumed<=u)return(r=this.errors)===null||r===void 0||r.absenceOfDigitsInNumericCharacterReference(this.consumed),0;if(t===K.SEMI)this.consumed+=1;else if(this.decodeMode===Se.Strict)return 0;return this.emitCodePoint(jo(this.result),this.consumed),this.errors&&(t!==K.SEMI&&this.errors.missingSemicolonAfterCharacterReference(),this.errors.validateNumericCharacterReference(this.result)),this.consumed}stateNamedEntity(t,u){const{decodeTree:r}=this;let i=r[this.treeIndex],s=(i&Fe.VALUE_LENGTH)>>14;for(;u<t.length;u++,this.excess++){const n=t.charCodeAt(u);if(this.treeIndex=Vo(r,i,this.treeIndex+Math.max(1,s),n),this.treeIndex<0)return this.result===0||this.decodeMode===Se.Attribute&&(s===0||qo(n))?0:this.emitNotTerminatedNamedEntity();if(i=r[this.treeIndex],s=(i&Fe.VALUE_LENGTH)>>14,s!==0){if(n===K.SEMI)return this.emitNamedEntityData(this.treeIndex,s,this.consumed+this.excess);this.decodeMode!==Se.Strict&&(this.result=this.treeIndex,this.consumed+=this.excess,this.excess=0)}}return-1}emitNotTerminatedNamedEntity(){var t;const{result:u,decodeTree:r}=this,i=(r[u]&Fe.VALUE_LENGTH)>>14;return this.emitNamedEntityData(u,i,this.consumed),(t=this.errors)===null||t===void 0||t.missingSemicolonAfterCharacterReference(),this.consumed}emitNamedEntityData(t,u,r){const{decodeTree:i}=this;return this.emitCodePoint(u===1?i[t]&~Fe.VALUE_LENGTH:i[t+1],r),u===3&&this.emitCodePoint(i[t+2],r),r}end(){var t;switch(this.state){case G.NamedEntity:return this.result!==0&&(this.decodeMode!==Se.Attribute||this.result===this.treeIndex)?this.emitNotTerminatedNamedEntity():0;case G.NumericDecimal:return this.emitNumericEntity(0,2);case G.NumericHex:return this.emitNumericEntity(0,3);case G.NumericStart:return(t=this.errors)===null||t===void 0||t.absenceOfDigitsInNumericCharacterReference(this.consumed),0;case G.EntityStart:return 0}}}function Ls(e){let t="";const u=new Ho(e,r=>t+=Mo(r));return function(i,s){let n=0,a=0;for(;(a=i.indexOf("&",a))>=0;){t+=i.slice(n,a),u.startEntity(s);const l=u.write(i,a+1);if(l<0){n=a+u.end();break}n=a+l,a=l===0?n+1:n}const c=t+i.slice(n);return t="",c}}function Vo(e,t,u,r){const i=(t&Fe.BRANCH_LENGTH)>>7,s=t&Fe.JUMP_TABLE;if(i===0)return s!==0&&r===s?u:-1;if(s){const c=r-s;return c<0||c>=i?-1:e[u+c]-1}let n=u,a=n+i-1;for(;n<=a;){const c=n+a>>>1,l=e[c];if(l<r)n=c+1;else if(l>r)a=c-1;else return e[c+i]}return-1}const Wo=Ls(zo);Ls(Ro);function Us(e,t=Se.Legacy){return Wo(e,t)}function Jo(e){return Object.prototype.toString.call(e)}function Or(e){return Jo(e)==="[object String]"}const Zo=Object.prototype.hasOwnProperty;function Go(e,t){return Zo.call(e,t)}function _u(e){return Array.prototype.slice.call(arguments,1).forEach(function(u){if(u){if(typeof u!="object")throw new TypeError(u+"must be object");Object.keys(u).forEach(function(r){e[r]=u[r]})}}),e}function Bs(e,t,u){return[].concat(e.slice(0,t),u,e.slice(t+1))}function Pr(e){return!(e>=55296&&e<=57343||e>=64976&&e<=65007||(e&65535)===65535||(e&65535)===65534||e>=0&&e<=8||e===11||e>=14&&e<=31||e>=127&&e<=159||e>1114111)}function cu(e){if(e>65535){e-=65536;const t=55296+(e>>10),u=56320+(e&1023);return String.fromCharCode(t,u)}return String.fromCharCode(e)}const qs=/\\([!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~])/g,Ko=/&([a-z#][a-z0-9]{1,31});/gi,Qo=new RegExp(qs.source+"|"+Ko.source,"gi"),Yo=/^#((?:x[a-f0-9]{1,8}|[0-9]{1,8}))$/i;function Xo(e,t){if(t.charCodeAt(0)===35&&Yo.test(t)){const r=t[1].toLowerCase()==="x"?parseInt(t.slice(2),16):parseInt(t.slice(1),10);return Pr(r)?cu(r):e}const u=Us(e);return u!==e?u:e}function ec(e){return e.indexOf("\\")<0?e:e.replace(qs,"$1")}function at(e){return e.indexOf("\\")<0&&e.indexOf("&")<0?e:e.replace(Qo,function(t,u,r){return u||Xo(t,r)})}const tc=/[&<>"]/,uc=/[&<>"]/g,rc={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"};function ic(e){return rc[e]}function Ie(e){return tc.test(e)?e.replace(uc,ic):e}const sc=/[.?*+^$[\]\\(){}|-]/g;function nc(e){return e.replace(sc,"\\$&")}function P(e){switch(e){case 9:case 32:return!0}return!1}function Ot(e){if(e>=8192&&e<=8202)return!0;switch(e){case 9:case 10:case 11:case 12:case 13:case 32:case 160:case 5760:case 8239:case 8287:case 12288:return!0}return!1}function Pt(e){return Ir.test(e)||Ms.test(e)}function zt(e){switch(e){case 33:case 34:case 35:case 36:case 37:case 38:case 39:case 40:case 41:case 42:case 43:case 44:case 45:case 46:case 47:case 58:case 59:case 60:case 61:case 62:case 63:case 64:case 91:case 92:case 93:case 94:case 95:case 96:case 123:case 124:case 125:case 126:return!0;default:return!1}}function yu(e){return e=e.trim().replace(/\s+/g," "),"ẞ".toLowerCase()==="Ṿ"&&(e=e.replace(/ẞ/g,"ß")),e.toLowerCase().toUpperCase()}const ac={mdurl:Io,ucmicro:Po},oc=Object.freeze(Object.defineProperty({__proto__:null,arrayReplaceAt:Bs,assign:_u,escapeHtml:Ie,escapeRE:nc,fromCodePoint:cu,has:Go,isMdAsciiPunct:zt,isPunctChar:Pt,isSpace:P,isString:Or,isValidEntityCode:Pr,isWhiteSpace:Ot,lib:ac,normalizeReference:yu,unescapeAll:at,unescapeMd:ec},Symbol.toStringTag,{value:"Module"}));function cc(e,t,u){let r,i,s,n;const a=e.posMax,c=e.pos;for(e.pos=t+1,r=1;e.pos<a;){if(s=e.src.charCodeAt(e.pos),s===93&&(r--,r===0)){i=!0;break}if(n=e.pos,e.md.inline.skipToken(e),s===91){if(n===e.pos-1)r++;else if(u)return e.pos=c,-1}}let l=-1;return i&&(l=e.pos),e.pos=c,l}function lc(e,t,u){let r,i=t;const s={ok:!1,pos:0,str:""};if(e.charCodeAt(i)===60){for(i++;i<u;){if(r=e.charCodeAt(i),r===10||r===60)return s;if(r===62)return s.pos=i+1,s.str=at(e.slice(t+1,i)),s.ok=!0,s;if(r===92&&i+1<u){i+=2;continue}i++}return s}let n=0;for(;i<u&&(r=e.charCodeAt(i),!(r===32||r<32||r===127));){if(r===92&&i+1<u){if(e.charCodeAt(i+1)===32)break;i+=2;continue}if(r===40&&(n++,n>32))return s;if(r===41){if(n===0)break;n--}i++}return t===i||n!==0||(s.str=at(e.slice(t,i)),s.pos=i,s.ok=!0),s}function dc(e,t,u,r){let i,s=t;const n={ok:!1,can_continue:!1,pos:0,str:"",marker:0};if(r)n.str=r.str,n.marker=r.marker;else{if(s>=u)return n;let a=e.charCodeAt(s);if(a!==34&&a!==39&&a!==40)return n;t++,s++,a===40&&(a=41),n.marker=a}for(;s<u;){if(i=e.charCodeAt(s),i===n.marker)return n.pos=s+1,n.str+=at(e.slice(t,s)),n.ok=!0,n;if(i===40&&n.marker===41)return n;i===92&&s+1<u&&s++,s++}return n.can_continue=!0,n.str+=at(e.slice(t,s)),n}const fc=Object.freeze(Object.defineProperty({__proto__:null,parseLinkDestination:lc,parseLinkLabel:cc,parseLinkTitle:dc},Symbol.toStringTag,{value:"Module"})),_e={};_e.code_inline=function(e,t,u,r,i){const s=e[t];return"<code"+i.renderAttrs(s)+">"+Ie(s.content)+"</code>"};_e.code_block=function(e,t,u,r,i){const s=e[t];return"<pre"+i.renderAttrs(s)+"><code>"+Ie(e[t].content)+`</code></pre>
`};_e.fence=function(e,t,u,r,i){const s=e[t],n=s.info?at(s.info).trim():"";let a="",c="";if(n){const d=n.split(/(\s+)/g);a=d[0],c=d.slice(2).join("")}let l;if(u.highlight?l=u.highlight(s.content,a,c)||Ie(s.content):l=Ie(s.content),l.indexOf("<pre")===0)return l+`
`;if(n){const d=s.attrIndex("class"),o=s.attrs?s.attrs.slice():[];d<0?o.push(["class",u.langPrefix+a]):(o[d]=o[d].slice(),o[d][1]+=" "+u.langPrefix+a);const h={attrs:o};return`<pre><code${i.renderAttrs(h)}>${l}</code></pre>
`}return`<pre><code${i.renderAttrs(s)}>${l}</code></pre>
`};_e.image=function(e,t,u,r,i){const s=e[t];return s.attrs[s.attrIndex("alt")][1]=i.renderInlineAsText(s.children,u,r),i.renderToken(e,t,u)};_e.hardbreak=function(e,t,u){return u.xhtmlOut?`<br />
`:`<br>
`};_e.softbreak=function(e,t,u){return u.breaks?u.xhtmlOut?`<br />
`:`<br>
`:`
`};_e.text=function(e,t){return Ie(e[t].content)};_e.html_block=function(e,t){return e[t].content};_e.html_inline=function(e,t){return e[t].content};function ft(){this.rules=_u({},_e)}ft.prototype.renderAttrs=function(t){let u,r,i;if(!t.attrs)return"";for(i="",u=0,r=t.attrs.length;u<r;u++)i+=" "+Ie(t.attrs[u][0])+'="'+Ie(t.attrs[u][1])+'"';return i};ft.prototype.renderToken=function(t,u,r){const i=t[u];let s="";if(i.hidden)return"";i.block&&i.nesting!==-1&&u&&t[u-1].hidden&&(s+=`
`),s+=(i.nesting===-1?"</":"<")+i.tag,s+=this.renderAttrs(i),i.nesting===0&&r.xhtmlOut&&(s+=" /");let n=!1;if(i.block&&(n=!0,i.nesting===1&&u+1<t.length)){const a=t[u+1];(a.type==="inline"||a.hidden||a.nesting===-1&&a.tag===i.tag)&&(n=!1)}return s+=n?`>
`:">",s};ft.prototype.renderInline=function(e,t,u){let r="";const i=this.rules;for(let s=0,n=e.length;s<n;s++){const a=e[s].type;typeof i[a]<"u"?r+=i[a](e,s,t,u,this):r+=this.renderToken(e,s,t)}return r};ft.prototype.renderInlineAsText=function(e,t,u){let r="";for(let i=0,s=e.length;i<s;i++)switch(e[i].type){case"text":r+=e[i].content;break;case"image":r+=this.renderInlineAsText(e[i].children,t,u);break;case"html_inline":case"html_block":r+=e[i].content;break;case"softbreak":case"hardbreak":r+=`
`;break}return r};ft.prototype.render=function(e,t,u){let r="";const i=this.rules;for(let s=0,n=e.length;s<n;s++){const a=e[s].type;a==="inline"?r+=this.renderInline(e[s].children,t,u):typeof i[a]<"u"?r+=i[a](e,s,t,u,this):r+=this.renderToken(e,s,t,u)}return r};function re(){this.__rules__=[],this.__cache__=null}re.prototype.__find__=function(e){for(let t=0;t<this.__rules__.length;t++)if(this.__rules__[t].name===e)return t;return-1};re.prototype.__compile__=function(){const e=this,t=[""];e.__rules__.forEach(function(u){u.enabled&&u.alt.forEach(function(r){t.indexOf(r)<0&&t.push(r)})}),e.__cache__={},t.forEach(function(u){e.__cache__[u]=[],e.__rules__.forEach(function(r){r.enabled&&(u&&r.alt.indexOf(u)<0||e.__cache__[u].push(r.fn))})})};re.prototype.at=function(e,t,u){const r=this.__find__(e),i=u||{};if(r===-1)throw new Error("Parser rule not found: "+e);this.__rules__[r].fn=t,this.__rules__[r].alt=i.alt||[],this.__cache__=null};re.prototype.before=function(e,t,u,r){const i=this.__find__(e),s=r||{};if(i===-1)throw new Error("Parser rule not found: "+e);this.__rules__.splice(i,0,{name:t,enabled:!0,fn:u,alt:s.alt||[]}),this.__cache__=null};re.prototype.after=function(e,t,u,r){const i=this.__find__(e),s=r||{};if(i===-1)throw new Error("Parser rule not found: "+e);this.__rules__.splice(i+1,0,{name:t,enabled:!0,fn:u,alt:s.alt||[]}),this.__cache__=null};re.prototype.push=function(e,t,u){const r=u||{};this.__rules__.push({name:e,enabled:!0,fn:t,alt:r.alt||[]}),this.__cache__=null};re.prototype.enable=function(e,t){Array.isArray(e)||(e=[e]);const u=[];return e.forEach(function(r){const i=this.__find__(r);if(i<0){if(t)return;throw new Error("Rules manager: invalid rule name "+r)}this.__rules__[i].enabled=!0,u.push(r)},this),this.__cache__=null,u};re.prototype.enableOnly=function(e,t){Array.isArray(e)||(e=[e]),this.__rules__.forEach(function(u){u.enabled=!1}),this.enable(e,t)};re.prototype.disable=function(e,t){Array.isArray(e)||(e=[e]);const u=[];return e.forEach(function(r){const i=this.__find__(r);if(i<0){if(t)return;throw new Error("Rules manager: invalid rule name "+r)}this.__rules__[i].enabled=!1,u.push(r)},this),this.__cache__=null,u};re.prototype.getRules=function(e){return this.__cache__===null&&this.__compile__(),this.__cache__[e]||[]};function fe(e,t,u){this.type=e,this.tag=t,this.attrs=null,this.map=null,this.nesting=u,this.level=0,this.children=null,this.content="",this.markup="",this.info="",this.meta=null,this.block=!1,this.hidden=!1}fe.prototype.attrIndex=function(t){if(!this.attrs)return-1;const u=this.attrs;for(let r=0,i=u.length;r<i;r++)if(u[r][0]===t)return r;return-1};fe.prototype.attrPush=function(t){this.attrs?this.attrs.push(t):this.attrs=[t]};fe.prototype.attrSet=function(t,u){const r=this.attrIndex(t),i=[t,u];r<0?this.attrPush(i):this.attrs[r]=i};fe.prototype.attrGet=function(t){const u=this.attrIndex(t);let r=null;return u>=0&&(r=this.attrs[u][1]),r};fe.prototype.attrJoin=function(t,u){const r=this.attrIndex(t);r<0?this.attrPush([t,u]):this.attrs[r][1]=this.attrs[r][1]+" "+u};function Hs(e,t,u){this.src=e,this.env=u,this.tokens=[],this.inlineMode=!1,this.md=t}Hs.prototype.Token=fe;const hc=/\r\n?|\n/g,pc=/\0/g;function bc(e){let t;t=e.src.replace(hc,`
`),t=t.replace(pc,"�"),e.src=t}function mc(e){let t;e.inlineMode?(t=new e.Token("inline","",0),t.content=e.src,t.map=[0,1],t.children=[],e.tokens.push(t)):e.md.block.parse(e.src,e.md,e.env,e.tokens)}function gc(e){const t=e.tokens;for(let u=0,r=t.length;u<r;u++){const i=t[u];i.type==="inline"&&e.md.inline.parse(i.content,e.md,e.env,i.children)}}function _c(e){return/^<a[>\s]/i.test(e)}function yc(e){return/^<\/a\s*>/i.test(e)}function xc(e){const t=e.tokens;if(e.md.options.linkify)for(let u=0,r=t.length;u<r;u++){if(t[u].type!=="inline"||!e.md.linkify.pretest(t[u].content))continue;let i=t[u].children,s=0;for(let n=i.length-1;n>=0;n--){const a=i[n];if(a.type==="link_close"){for(n--;i[n].level!==a.level&&i[n].type!=="link_open";)n--;continue}if(a.type==="html_inline"&&(_c(a.content)&&s>0&&s--,yc(a.content)&&s++),!(s>0)&&a.type==="text"&&e.md.linkify.test(a.content)){const c=a.content;let l=e.md.linkify.match(c);const d=[];let o=a.level,h=0;l.length>0&&l[0].index===0&&n>0&&i[n-1].type==="text_special"&&(l=l.slice(1));for(let p=0;p<l.length;p++){const f=l[p].url,b=e.md.normalizeLink(f);if(!e.md.validateLink(b))continue;let m=l[p].text;l[p].schema?l[p].schema==="mailto:"&&!/^mailto:/i.test(m)?m=e.md.normalizeLinkText("mailto:"+m).replace(/^mailto:/,""):m=e.md.normalizeLinkText(m):m=e.md.normalizeLinkText("http://"+m).replace(/^http:\/\//,"");const g=l[p].index;if(g>h){const x=new e.Token("text","",0);x.content=c.slice(h,g),x.level=o,d.push(x)}const v=new e.Token("link_open","a",1);v.attrs=[["href",b]],v.level=o++,v.markup="linkify",v.info="auto",d.push(v);const w=new e.Token("text","",0);w.content=m,w.level=o,d.push(w);const y=new e.Token("link_close","a",-1);y.level=--o,y.markup="linkify",y.info="auto",d.push(y),h=l[p].lastIndex}if(h<c.length){const p=new e.Token("text","",0);p.content=c.slice(h),p.level=o,d.push(p)}t[u].children=i=Bs(i,n,d)}}}}const Vs=/\+-|\.\.|\?\?\?\?|!!!!|,,|--/,vc=/\((c|tm|r)\)/i,wc=/\((c|tm|r)\)/ig,kc={c:"©",r:"®",tm:"™"};function Cc(e,t){return kc[t.toLowerCase()]}function $c(e){let t=0;for(let u=e.length-1;u>=0;u--){const r=e[u];r.type==="text"&&!t&&(r.content=r.content.replace(wc,Cc)),r.type==="link_open"&&r.info==="auto"&&t--,r.type==="link_close"&&r.info==="auto"&&t++}}function Ec(e){let t=0;for(let u=e.length-1;u>=0;u--){const r=e[u];r.type==="text"&&!t&&Vs.test(r.content)&&(r.content=r.content.replace(/\+-/g,"±").replace(/\.{2,}/g,"…").replace(/([?!])…/g,"$1..").replace(/([?!]){4,}/g,"$1$1$1").replace(/,{2,}/g,",").replace(/(^|[^-])---(?=[^-]|$)/mg,"$1—").replace(/(^|\s)--(?=\s|$)/mg,"$1–").replace(/(^|[^-\s])--(?=[^-\s]|$)/mg,"$1–")),r.type==="link_open"&&r.info==="auto"&&t--,r.type==="link_close"&&r.info==="auto"&&t++}}function Ac(e){let t;if(e.md.options.typographer)for(t=e.tokens.length-1;t>=0;t--)e.tokens[t].type==="inline"&&(vc.test(e.tokens[t].content)&&$c(e.tokens[t].children),Vs.test(e.tokens[t].content)&&Ec(e.tokens[t].children))}const Dc=/['"]/,Ii=/['"]/g,Oi="’";function Zt(e,t,u){return e.slice(0,t)+u+e.slice(t+1)}function Sc(e,t){let u;const r=[];for(let i=0;i<e.length;i++){const s=e[i],n=e[i].level;for(u=r.length-1;u>=0&&!(r[u].level<=n);u--);if(r.length=u+1,s.type!=="text")continue;let a=s.content,c=0,l=a.length;e:for(;c<l;){Ii.lastIndex=c;const d=Ii.exec(a);if(!d)break;let o=!0,h=!0;c=d.index+1;const p=d[0]==="'";let f=32;if(d.index-1>=0)f=a.charCodeAt(d.index-1);else for(u=i-1;u>=0&&!(e[u].type==="softbreak"||e[u].type==="hardbreak");u--)if(e[u].content){f=e[u].content.charCodeAt(e[u].content.length-1);break}let b=32;if(c<l)b=a.charCodeAt(c);else for(u=i+1;u<e.length&&!(e[u].type==="softbreak"||e[u].type==="hardbreak");u++)if(e[u].content){b=e[u].content.charCodeAt(0);break}const m=zt(f)||Pt(String.fromCharCode(f)),g=zt(b)||Pt(String.fromCharCode(b)),v=Ot(f),w=Ot(b);if(w?o=!1:g&&(v||m||(o=!1)),v?h=!1:m&&(w||g||(h=!1)),b===34&&d[0]==='"'&&f>=48&&f<=57&&(h=o=!1),o&&h&&(o=m,h=g),!o&&!h){p&&(s.content=Zt(s.content,d.index,Oi));continue}if(h)for(u=r.length-1;u>=0;u--){let y=r[u];if(r[u].level<n)break;if(y.single===p&&r[u].level===n){y=r[u];let x,E;p?(x=t.md.options.quotes[2],E=t.md.options.quotes[3]):(x=t.md.options.quotes[0],E=t.md.options.quotes[1]),s.content=Zt(s.content,d.index,E),e[y.token].content=Zt(e[y.token].content,y.pos,x),c+=E.length-1,y.token===i&&(c+=x.length-1),a=s.content,l=a.length,r.length=u;continue e}}o?r.push({token:i,pos:d.index,single:p,level:n}):h&&p&&(s.content=Zt(s.content,d.index,Oi))}}}function Fc(e){if(e.md.options.typographer)for(let t=e.tokens.length-1;t>=0;t--)e.tokens[t].type!=="inline"||!Dc.test(e.tokens[t].content)||Sc(e.tokens[t].children,e)}function Tc(e){let t,u;const r=e.tokens,i=r.length;for(let s=0;s<i;s++){if(r[s].type!=="inline")continue;const n=r[s].children,a=n.length;for(t=0;t<a;t++)n[t].type==="text_special"&&(n[t].type="text");for(t=u=0;t<a;t++)n[t].type==="text"&&t+1<a&&n[t+1].type==="text"?n[t+1].content=n[t].content+n[t+1].content:(t!==u&&(n[u]=n[t]),u++);t!==u&&(n.length=u)}}const qu=[["normalize",bc],["block",mc],["inline",gc],["linkify",xc],["replacements",Ac],["smartquotes",Fc],["text_join",Tc]];function zr(){this.ruler=new re;for(let e=0;e<qu.length;e++)this.ruler.push(qu[e][0],qu[e][1])}zr.prototype.process=function(e){const t=this.ruler.getRules("");for(let u=0,r=t.length;u<r;u++)t[u](e)};zr.prototype.State=Hs;function ye(e,t,u,r){this.src=e,this.md=t,this.env=u,this.tokens=r,this.bMarks=[],this.eMarks=[],this.tShift=[],this.sCount=[],this.bsCount=[],this.blkIndent=0,this.line=0,this.lineMax=0,this.tight=!1,this.ddIndent=-1,this.listIndent=-1,this.parentType="root",this.level=0;const i=this.src;for(let s=0,n=0,a=0,c=0,l=i.length,d=!1;n<l;n++){const o=i.charCodeAt(n);if(!d)if(P(o)){a++,o===9?c+=4-c%4:c++;continue}else d=!0;(o===10||n===l-1)&&(o!==10&&n++,this.bMarks.push(s),this.eMarks.push(n),this.tShift.push(a),this.sCount.push(c),this.bsCount.push(0),d=!1,a=0,c=0,s=n+1)}this.bMarks.push(i.length),this.eMarks.push(i.length),this.tShift.push(0),this.sCount.push(0),this.bsCount.push(0),this.lineMax=this.bMarks.length-1}ye.prototype.push=function(e,t,u){const r=new fe(e,t,u);return r.block=!0,u<0&&this.level--,r.level=this.level,u>0&&this.level++,this.tokens.push(r),r};ye.prototype.isEmpty=function(t){return this.bMarks[t]+this.tShift[t]>=this.eMarks[t]};ye.prototype.skipEmptyLines=function(t){for(let u=this.lineMax;t<u&&!(this.bMarks[t]+this.tShift[t]<this.eMarks[t]);t++);return t};ye.prototype.skipSpaces=function(t){for(let u=this.src.length;t<u;t++){const r=this.src.charCodeAt(t);if(!P(r))break}return t};ye.prototype.skipSpacesBack=function(t,u){if(t<=u)return t;for(;t>u;)if(!P(this.src.charCodeAt(--t)))return t+1;return t};ye.prototype.skipChars=function(t,u){for(let r=this.src.length;t<r&&this.src.charCodeAt(t)===u;t++);return t};ye.prototype.skipCharsBack=function(t,u,r){if(t<=r)return t;for(;t>r;)if(u!==this.src.charCodeAt(--t))return t+1;return t};ye.prototype.getLines=function(t,u,r,i){if(t>=u)return"";const s=new Array(u-t);for(let n=0,a=t;a<u;a++,n++){let c=0;const l=this.bMarks[a];let d=l,o;for(a+1<u||i?o=this.eMarks[a]+1:o=this.eMarks[a];d<o&&c<r;){const h=this.src.charCodeAt(d);if(P(h))h===9?c+=4-(c+this.bsCount[a])%4:c++;else if(d-l<this.tShift[a])c++;else break;d++}c>r?s[n]=new Array(c-r+1).join(" ")+this.src.slice(d,o):s[n]=this.src.slice(d,o)}return s.join("")};ye.prototype.Token=fe;const Ic=65536;function Hu(e,t){const u=e.bMarks[t]+e.tShift[t],r=e.eMarks[t];return e.src.slice(u,r)}function Pi(e){const t=[],u=e.length;let r=0,i=e.charCodeAt(r),s=!1,n=0,a="";for(;r<u;)i===124&&(s?(a+=e.substring(n,r-1),n=r):(t.push(a+e.substring(n,r)),a="",n=r+1)),s=i===92,r++,i=e.charCodeAt(r);return t.push(a+e.substring(n)),t}function Oc(e,t,u,r){if(t+2>u)return!1;let i=t+1;if(e.sCount[i]<e.blkIndent||e.sCount[i]-e.blkIndent>=4)return!1;let s=e.bMarks[i]+e.tShift[i];if(s>=e.eMarks[i])return!1;const n=e.src.charCodeAt(s++);if(n!==124&&n!==45&&n!==58||s>=e.eMarks[i])return!1;const a=e.src.charCodeAt(s++);if(a!==124&&a!==45&&a!==58&&!P(a)||n===45&&P(a))return!1;for(;s<e.eMarks[i];){const y=e.src.charCodeAt(s);if(y!==124&&y!==45&&y!==58&&!P(y))return!1;s++}let c=Hu(e,t+1),l=c.split("|");const d=[];for(let y=0;y<l.length;y++){const x=l[y].trim();if(!x){if(y===0||y===l.length-1)continue;return!1}if(!/^:?-+:?$/.test(x))return!1;x.charCodeAt(x.length-1)===58?d.push(x.charCodeAt(0)===58?"center":"right"):x.charCodeAt(0)===58?d.push("left"):d.push("")}if(c=Hu(e,t).trim(),c.indexOf("|")===-1||e.sCount[t]-e.blkIndent>=4)return!1;l=Pi(c),l.length&&l[0]===""&&l.shift(),l.length&&l[l.length-1]===""&&l.pop();const o=l.length;if(o===0||o!==d.length)return!1;if(r)return!0;const h=e.parentType;e.parentType="table";const p=e.md.block.ruler.getRules("blockquote"),f=e.push("table_open","table",1),b=[t,0];f.map=b;const m=e.push("thead_open","thead",1);m.map=[t,t+1];const g=e.push("tr_open","tr",1);g.map=[t,t+1];for(let y=0;y<l.length;y++){const x=e.push("th_open","th",1);d[y]&&(x.attrs=[["style","text-align:"+d[y]]]);const E=e.push("inline","",0);E.content=l[y].trim(),E.children=[],e.push("th_close","th",-1)}e.push("tr_close","tr",-1),e.push("thead_close","thead",-1);let v,w=0;for(i=t+2;i<u&&!(e.sCount[i]<e.blkIndent);i++){let y=!1;for(let E=0,O=p.length;E<O;E++)if(p[E](e,i,u,!0)){y=!0;break}if(y||(c=Hu(e,i).trim(),!c)||e.sCount[i]-e.blkIndent>=4||(l=Pi(c),l.length&&l[0]===""&&l.shift(),l.length&&l[l.length-1]===""&&l.pop(),w+=o-l.length,w>Ic))break;if(i===t+2){const E=e.push("tbody_open","tbody",1);E.map=v=[t+2,0]}const x=e.push("tr_open","tr",1);x.map=[i,i+1];for(let E=0;E<o;E++){const O=e.push("td_open","td",1);d[E]&&(O.attrs=[["style","text-align:"+d[E]]]);const H=e.push("inline","",0);H.content=l[E]?l[E].trim():"",H.children=[],e.push("td_close","td",-1)}e.push("tr_close","tr",-1)}return v&&(e.push("tbody_close","tbody",-1),v[1]=i),e.push("table_close","table",-1),b[1]=i,e.parentType=h,e.line=i,!0}function Pc(e,t,u){if(e.sCount[t]-e.blkIndent<4)return!1;let r=t+1,i=r;for(;r<u;){if(e.isEmpty(r)){r++;continue}if(e.sCount[r]-e.blkIndent>=4){r++,i=r;continue}break}e.line=i;const s=e.push("code_block","code",0);return s.content=e.getLines(t,i,4+e.blkIndent,!1)+`
`,s.map=[t,e.line],!0}function zc(e,t,u,r){let i=e.bMarks[t]+e.tShift[t],s=e.eMarks[t];if(e.sCount[t]-e.blkIndent>=4||i+3>s)return!1;const n=e.src.charCodeAt(i);if(n!==126&&n!==96)return!1;let a=i;i=e.skipChars(i,n);let c=i-a;if(c<3)return!1;const l=e.src.slice(a,i),d=e.src.slice(i,s);if(n===96&&d.indexOf(String.fromCharCode(n))>=0)return!1;if(r)return!0;let o=t,h=!1;for(;o++,!(o>=u||(i=a=e.bMarks[o]+e.tShift[o],s=e.eMarks[o],i<s&&e.sCount[o]<e.blkIndent));)if(e.src.charCodeAt(i)===n&&!(e.sCount[o]-e.blkIndent>=4)&&(i=e.skipChars(i,n),!(i-a<c)&&(i=e.skipSpaces(i),!(i<s)))){h=!0;break}c=e.sCount[t],e.line=o+(h?1:0);const p=e.push("fence","code",0);return p.info=d,p.content=e.getLines(t+1,o,c,!0),p.markup=l,p.map=[t,e.line],!0}function Rc(e,t,u,r){let i=e.bMarks[t]+e.tShift[t],s=e.eMarks[t];const n=e.lineMax;if(e.sCount[t]-e.blkIndent>=4||e.src.charCodeAt(i)!==62)return!1;if(r)return!0;const a=[],c=[],l=[],d=[],o=e.md.block.ruler.getRules("blockquote"),h=e.parentType;e.parentType="blockquote";let p=!1,f;for(f=t;f<u;f++){const w=e.sCount[f]<e.blkIndent;if(i=e.bMarks[f]+e.tShift[f],s=e.eMarks[f],i>=s)break;if(e.src.charCodeAt(i++)===62&&!w){let x=e.sCount[f]+1,E,O;e.src.charCodeAt(i)===32?(i++,x++,O=!1,E=!0):e.src.charCodeAt(i)===9?(E=!0,(e.bsCount[f]+x)%4===3?(i++,x++,O=!1):O=!0):E=!1;let H=x;for(a.push(e.bMarks[f]),e.bMarks[f]=i;i<s;){const ee=e.src.charCodeAt(i);if(P(ee))ee===9?H+=4-(H+e.bsCount[f]+(O?1:0))%4:H++;else break;i++}p=i>=s,c.push(e.bsCount[f]),e.bsCount[f]=e.sCount[f]+1+(E?1:0),l.push(e.sCount[f]),e.sCount[f]=H-x,d.push(e.tShift[f]),e.tShift[f]=i-e.bMarks[f];continue}if(p)break;let y=!1;for(let x=0,E=o.length;x<E;x++)if(o[x](e,f,u,!0)){y=!0;break}if(y){e.lineMax=f,e.blkIndent!==0&&(a.push(e.bMarks[f]),c.push(e.bsCount[f]),d.push(e.tShift[f]),l.push(e.sCount[f]),e.sCount[f]-=e.blkIndent);break}a.push(e.bMarks[f]),c.push(e.bsCount[f]),d.push(e.tShift[f]),l.push(e.sCount[f]),e.sCount[f]=-1}const b=e.blkIndent;e.blkIndent=0;const m=e.push("blockquote_open","blockquote",1);m.markup=">";const g=[t,0];m.map=g,e.md.block.tokenize(e,t,f);const v=e.push("blockquote_close","blockquote",-1);v.markup=">",e.lineMax=n,e.parentType=h,g[1]=e.line;for(let w=0;w<d.length;w++)e.bMarks[w+t]=a[w],e.tShift[w+t]=d[w],e.sCount[w+t]=l[w],e.bsCount[w+t]=c[w];return e.blkIndent=b,!0}function Nc(e,t,u,r){const i=e.eMarks[t];if(e.sCount[t]-e.blkIndent>=4)return!1;let s=e.bMarks[t]+e.tShift[t];const n=e.src.charCodeAt(s++);if(n!==42&&n!==45&&n!==95)return!1;let a=1;for(;s<i;){const l=e.src.charCodeAt(s++);if(l!==n&&!P(l))return!1;l===n&&a++}if(a<3)return!1;if(r)return!0;e.line=t+1;const c=e.push("hr","hr",0);return c.map=[t,e.line],c.markup=Array(a+1).join(String.fromCharCode(n)),!0}function zi(e,t){const u=e.eMarks[t];let r=e.bMarks[t]+e.tShift[t];const i=e.src.charCodeAt(r++);if(i!==42&&i!==45&&i!==43)return-1;if(r<u){const s=e.src.charCodeAt(r);if(!P(s))return-1}return r}function Ri(e,t){const u=e.bMarks[t]+e.tShift[t],r=e.eMarks[t];let i=u;if(i+1>=r)return-1;let s=e.src.charCodeAt(i++);if(s<48||s>57)return-1;for(;;){if(i>=r)return-1;if(s=e.src.charCodeAt(i++),s>=48&&s<=57){if(i-u>=10)return-1;continue}if(s===41||s===46)break;return-1}return i<r&&(s=e.src.charCodeAt(i),!P(s))?-1:i}function Mc(e,t){const u=e.level+2;for(let r=t+2,i=e.tokens.length-2;r<i;r++)e.tokens[r].level===u&&e.tokens[r].type==="paragraph_open"&&(e.tokens[r+2].hidden=!0,e.tokens[r].hidden=!0,r+=2)}function jc(e,t,u,r){let i,s,n,a,c=t,l=!0;if(e.sCount[c]-e.blkIndent>=4||e.listIndent>=0&&e.sCount[c]-e.listIndent>=4&&e.sCount[c]<e.blkIndent)return!1;let d=!1;r&&e.parentType==="paragraph"&&e.sCount[c]>=e.blkIndent&&(d=!0);let o,h,p;if((p=Ri(e,c))>=0){if(o=!0,n=e.bMarks[c]+e.tShift[c],h=Number(e.src.slice(n,p-1)),d&&h!==1)return!1}else if((p=zi(e,c))>=0)o=!1;else return!1;if(d&&e.skipSpaces(p)>=e.eMarks[c])return!1;if(r)return!0;const f=e.src.charCodeAt(p-1),b=e.tokens.length;o?(a=e.push("ordered_list_open","ol",1),h!==1&&(a.attrs=[["start",h]])):a=e.push("bullet_list_open","ul",1);const m=[c,0];a.map=m,a.markup=String.fromCharCode(f);let g=!1;const v=e.md.block.ruler.getRules("list"),w=e.parentType;for(e.parentType="list";c<u;){s=p,i=e.eMarks[c];const y=e.sCount[c]+p-(e.bMarks[c]+e.tShift[c]);let x=y;for(;s<i;){const R=e.src.charCodeAt(s);if(R===9)x+=4-(x+e.bsCount[c])%4;else if(R===32)x++;else break;s++}const E=s;let O;E>=i?O=1:O=x-y,O>4&&(O=1);const H=y+O;a=e.push("list_item_open","li",1),a.markup=String.fromCharCode(f);const ee=[c,0];a.map=ee,o&&(a.info=e.src.slice(n,p-1));const Ee=e.tight,Je=e.tShift[c],D=e.sCount[c],C=e.listIndent;if(e.listIndent=e.blkIndent,e.blkIndent=H,e.tight=!0,e.tShift[c]=E-e.bMarks[c],e.sCount[c]=x,E>=i&&e.isEmpty(c+1)?e.line=Math.min(e.line+2,u):e.md.block.tokenize(e,c,u,!0),(!e.tight||g)&&(l=!1),g=e.line-c>1&&e.isEmpty(e.line-1),e.blkIndent=e.listIndent,e.listIndent=C,e.tShift[c]=Je,e.sCount[c]=D,e.tight=Ee,a=e.push("list_item_close","li",-1),a.markup=String.fromCharCode(f),c=e.line,ee[1]=c,c>=u||e.sCount[c]<e.blkIndent||e.sCount[c]-e.blkIndent>=4)break;let _=!1;for(let R=0,L=v.length;R<L;R++)if(v[R](e,c,u,!0)){_=!0;break}if(_)break;if(o){if(p=Ri(e,c),p<0)break;n=e.bMarks[c]+e.tShift[c]}else if(p=zi(e,c),p<0)break;if(f!==e.src.charCodeAt(p-1))break}return o?a=e.push("ordered_list_close","ol",-1):a=e.push("bullet_list_close","ul",-1),a.markup=String.fromCharCode(f),m[1]=c,e.line=c,e.parentType=w,l&&Mc(e,b),!0}function Lc(e,t,u,r){let i=e.bMarks[t]+e.tShift[t],s=e.eMarks[t],n=t+1;if(e.sCount[t]-e.blkIndent>=4||e.src.charCodeAt(i)!==91)return!1;function a(v){const w=e.lineMax;if(v>=w||e.isEmpty(v))return null;let y=!1;if(e.sCount[v]-e.blkIndent>3&&(y=!0),e.sCount[v]<0&&(y=!0),!y){const O=e.md.block.ruler.getRules("reference"),H=e.parentType;e.parentType="reference";let ee=!1;for(let Ee=0,Je=O.length;Ee<Je;Ee++)if(O[Ee](e,v,w,!0)){ee=!0;break}if(e.parentType=H,ee)return null}const x=e.bMarks[v]+e.tShift[v],E=e.eMarks[v];return e.src.slice(x,E+1)}let c=e.src.slice(i,s+1);s=c.length;let l=-1;for(i=1;i<s;i++){const v=c.charCodeAt(i);if(v===91)return!1;if(v===93){l=i;break}else if(v===10){const w=a(n);w!==null&&(c+=w,s=c.length,n++)}else if(v===92&&(i++,i<s&&c.charCodeAt(i)===10)){const w=a(n);w!==null&&(c+=w,s=c.length,n++)}}if(l<0||c.charCodeAt(l+1)!==58)return!1;for(i=l+2;i<s;i++){const v=c.charCodeAt(i);if(v===10){const w=a(n);w!==null&&(c+=w,s=c.length,n++)}else if(!P(v))break}const d=e.md.helpers.parseLinkDestination(c,i,s);if(!d.ok)return!1;const o=e.md.normalizeLink(d.str);if(!e.md.validateLink(o))return!1;i=d.pos;const h=i,p=n,f=i;for(;i<s;i++){const v=c.charCodeAt(i);if(v===10){const w=a(n);w!==null&&(c+=w,s=c.length,n++)}else if(!P(v))break}let b=e.md.helpers.parseLinkTitle(c,i,s);for(;b.can_continue;){const v=a(n);if(v===null)break;c+=v,i=s,s=c.length,n++,b=e.md.helpers.parseLinkTitle(c,i,s,b)}let m;for(i<s&&f!==i&&b.ok?(m=b.str,i=b.pos):(m="",i=h,n=p);i<s;){const v=c.charCodeAt(i);if(!P(v))break;i++}if(i<s&&c.charCodeAt(i)!==10&&m)for(m="",i=h,n=p;i<s;){const v=c.charCodeAt(i);if(!P(v))break;i++}if(i<s&&c.charCodeAt(i)!==10)return!1;const g=yu(c.slice(1,l));return g?(r||(typeof e.env.references>"u"&&(e.env.references={}),typeof e.env.references[g]>"u"&&(e.env.references[g]={title:m,href:o}),e.line=n),!0):!1}const Uc=["address","article","aside","base","basefont","blockquote","body","caption","center","col","colgroup","dd","details","dialog","dir","div","dl","dt","fieldset","figcaption","figure","footer","form","frame","frameset","h1","h2","h3","h4","h5","h6","head","header","hr","html","iframe","legend","li","link","main","menu","menuitem","nav","noframes","ol","optgroup","option","p","param","search","section","summary","table","tbody","td","tfoot","th","thead","title","tr","track","ul"],Bc="[a-zA-Z_:][a-zA-Z0-9:._-]*",qc="[^\"'=<>`\\x00-\\x20]+",Hc="'[^']*'",Vc='"[^"]*"',Wc="(?:"+qc+"|"+Hc+"|"+Vc+")",Jc="(?:\\s+"+Bc+"(?:\\s*=\\s*"+Wc+")?)",Ws="<[A-Za-z][A-Za-z0-9\\-]*"+Jc+"*\\s*\\/?>",Js="<\\/[A-Za-z][A-Za-z0-9\\-]*\\s*>",Zc="<!---?>|<!--(?:[^-]|-[^-]|--[^>])*-->",Gc="<[?][\\s\\S]*?[?]>",Kc="<![A-Za-z][^>]*>",Qc="<!\\[CDATA\\[[\\s\\S]*?\\]\\]>",Yc=new RegExp("^(?:"+Ws+"|"+Js+"|"+Zc+"|"+Gc+"|"+Kc+"|"+Qc+")"),Xc=new RegExp("^(?:"+Ws+"|"+Js+")"),Qe=[[/^<(script|pre|style|textarea)(?=(\s|>|$))/i,/<\/(script|pre|style|textarea)>/i,!0],[/^<!--/,/-->/,!0],[/^<\?/,/\?>/,!0],[/^<![A-Z]/,/>/,!0],[/^<!\[CDATA\[/,/\]\]>/,!0],[new RegExp("^</?("+Uc.join("|")+")(?=(\\s|/?>|$))","i"),/^$/,!0],[new RegExp(Xc.source+"\\s*$"),/^$/,!1]];function el(e,t,u,r){let i=e.bMarks[t]+e.tShift[t],s=e.eMarks[t];if(e.sCount[t]-e.blkIndent>=4||!e.md.options.html||e.src.charCodeAt(i)!==60)return!1;let n=e.src.slice(i,s),a=0;for(;a<Qe.length&&!Qe[a][0].test(n);a++);if(a===Qe.length)return!1;if(r)return Qe[a][2];let c=t+1;if(!Qe[a][1].test(n)){for(;c<u&&!(e.sCount[c]<e.blkIndent);c++)if(i=e.bMarks[c]+e.tShift[c],s=e.eMarks[c],n=e.src.slice(i,s),Qe[a][1].test(n)){n.length!==0&&c++;break}}e.line=c;const l=e.push("html_block","",0);return l.map=[t,c],l.content=e.getLines(t,c,e.blkIndent,!0),!0}function tl(e,t,u,r){let i=e.bMarks[t]+e.tShift[t],s=e.eMarks[t];if(e.sCount[t]-e.blkIndent>=4)return!1;let n=e.src.charCodeAt(i);if(n!==35||i>=s)return!1;let a=1;for(n=e.src.charCodeAt(++i);n===35&&i<s&&a<=6;)a++,n=e.src.charCodeAt(++i);if(a>6||i<s&&!P(n))return!1;if(r)return!0;s=e.skipSpacesBack(s,i);const c=e.skipCharsBack(s,35,i);c>i&&P(e.src.charCodeAt(c-1))&&(s=c),e.line=t+1;const l=e.push("heading_open","h"+String(a),1);l.markup="########".slice(0,a),l.map=[t,e.line];const d=e.push("inline","",0);d.content=e.src.slice(i,s).trim(),d.map=[t,e.line],d.children=[];const o=e.push("heading_close","h"+String(a),-1);return o.markup="########".slice(0,a),!0}function ul(e,t,u){const r=e.md.block.ruler.getRules("paragraph");if(e.sCount[t]-e.blkIndent>=4)return!1;const i=e.parentType;e.parentType="paragraph";let s=0,n,a=t+1;for(;a<u&&!e.isEmpty(a);a++){if(e.sCount[a]-e.blkIndent>3)continue;if(e.sCount[a]>=e.blkIndent){let p=e.bMarks[a]+e.tShift[a];const f=e.eMarks[a];if(p<f&&(n=e.src.charCodeAt(p),(n===45||n===61)&&(p=e.skipChars(p,n),p=e.skipSpaces(p),p>=f))){s=n===61?1:2;break}}if(e.sCount[a]<0)continue;let h=!1;for(let p=0,f=r.length;p<f;p++)if(r[p](e,a,u,!0)){h=!0;break}if(h)break}if(!s)return!1;const c=e.getLines(t,a,e.blkIndent,!1).trim();e.line=a+1;const l=e.push("heading_open","h"+String(s),1);l.markup=String.fromCharCode(n),l.map=[t,e.line];const d=e.push("inline","",0);d.content=c,d.map=[t,e.line-1],d.children=[];const o=e.push("heading_close","h"+String(s),-1);return o.markup=String.fromCharCode(n),e.parentType=i,!0}function rl(e,t,u){const r=e.md.block.ruler.getRules("paragraph"),i=e.parentType;let s=t+1;for(e.parentType="paragraph";s<u&&!e.isEmpty(s);s++){if(e.sCount[s]-e.blkIndent>3||e.sCount[s]<0)continue;let l=!1;for(let d=0,o=r.length;d<o;d++)if(r[d](e,s,u,!0)){l=!0;break}if(l)break}const n=e.getLines(t,s,e.blkIndent,!1).trim();e.line=s;const a=e.push("paragraph_open","p",1);a.map=[t,e.line];const c=e.push("inline","",0);return c.content=n,c.map=[t,e.line],c.children=[],e.push("paragraph_close","p",-1),e.parentType=i,!0}const Gt=[["table",Oc,["paragraph","reference"]],["code",Pc],["fence",zc,["paragraph","reference","blockquote","list"]],["blockquote",Rc,["paragraph","reference","blockquote","list"]],["hr",Nc,["paragraph","reference","blockquote","list"]],["list",jc,["paragraph","reference","blockquote"]],["reference",Lc],["html_block",el,["paragraph","reference","blockquote"]],["heading",tl,["paragraph","reference","blockquote"]],["lheading",ul],["paragraph",rl]];function xu(){this.ruler=new re;for(let e=0;e<Gt.length;e++)this.ruler.push(Gt[e][0],Gt[e][1],{alt:(Gt[e][2]||[]).slice()})}xu.prototype.tokenize=function(e,t,u){const r=this.ruler.getRules(""),i=r.length,s=e.md.options.maxNesting;let n=t,a=!1;for(;n<u&&(e.line=n=e.skipEmptyLines(n),!(n>=u||e.sCount[n]<e.blkIndent));){if(e.level>=s){e.line=u;break}const c=e.line;let l=!1;for(let d=0;d<i;d++)if(l=r[d](e,n,u,!1),l){if(c>=e.line)throw new Error("block rule didn't increment state.line");break}if(!l)throw new Error("none of the block rules matched");e.tight=!a,e.isEmpty(e.line-1)&&(a=!0),n=e.line,n<u&&e.isEmpty(n)&&(a=!0,n++,e.line=n)}};xu.prototype.parse=function(e,t,u,r){if(!e)return;const i=new this.State(e,t,u,r);this.tokenize(i,i.line,i.lineMax)};xu.prototype.State=ye;function Lt(e,t,u,r){this.src=e,this.env=u,this.md=t,this.tokens=r,this.tokens_meta=Array(r.length),this.pos=0,this.posMax=this.src.length,this.level=0,this.pending="",this.pendingLevel=0,this.cache={},this.delimiters=[],this._prev_delimiters=[],this.backticks={},this.backticksScanned=!1,this.linkLevel=0}Lt.prototype.pushPending=function(){const e=new fe("text","",0);return e.content=this.pending,e.level=this.pendingLevel,this.tokens.push(e),this.pending="",e};Lt.prototype.push=function(e,t,u){this.pending&&this.pushPending();const r=new fe(e,t,u);let i=null;return u<0&&(this.level--,this.delimiters=this._prev_delimiters.pop()),r.level=this.level,u>0&&(this.level++,this._prev_delimiters.push(this.delimiters),this.delimiters=[],i={delimiters:this.delimiters}),this.pendingLevel=this.level,this.tokens.push(r),this.tokens_meta.push(i),r};Lt.prototype.scanDelims=function(e,t){const u=this.posMax,r=this.src.charCodeAt(e),i=e>0?this.src.charCodeAt(e-1):32;let s=e;for(;s<u&&this.src.charCodeAt(s)===r;)s++;const n=s-e,a=s<u?this.src.charCodeAt(s):32,c=zt(i)||Pt(String.fromCharCode(i)),l=zt(a)||Pt(String.fromCharCode(a)),d=Ot(i),o=Ot(a),h=!o&&(!l||d||c),p=!d&&(!c||o||l);return{can_open:h&&(t||!p||c),can_close:p&&(t||!h||l),length:n}};Lt.prototype.Token=fe;function il(e){switch(e){case 10:case 33:case 35:case 36:case 37:case 38:case 42:case 43:case 45:case 58:case 60:case 61:case 62:case 64:case 91:case 92:case 93:case 94:case 95:case 96:case 123:case 125:case 126:return!0;default:return!1}}function sl(e,t){let u=e.pos;for(;u<e.posMax&&!il(e.src.charCodeAt(u));)u++;return u===e.pos?!1:(t||(e.pending+=e.src.slice(e.pos,u)),e.pos=u,!0)}const nl=/(?:^|[^a-z0-9.+-])([a-z][a-z0-9.+-]*)$/i;function al(e,t){if(!e.md.options.linkify||e.linkLevel>0)return!1;const u=e.pos,r=e.posMax;if(u+3>r||e.src.charCodeAt(u)!==58||e.src.charCodeAt(u+1)!==47||e.src.charCodeAt(u+2)!==47)return!1;const i=e.pending.match(nl);if(!i)return!1;const s=i[1],n=e.md.linkify.matchAtStart(e.src.slice(u-s.length));if(!n)return!1;let a=n.url;if(a.length<=s.length)return!1;let c=a.length;for(;c>0&&a.charCodeAt(c-1)===42;)c--;c!==a.length&&(a=a.slice(0,c));const l=e.md.normalizeLink(a);if(!e.md.validateLink(l))return!1;if(!t){e.pending=e.pending.slice(0,-s.length);const d=e.push("link_open","a",1);d.attrs=[["href",l]],d.markup="linkify",d.info="auto";const o=e.push("text","",0);o.content=e.md.normalizeLinkText(a);const h=e.push("link_close","a",-1);h.markup="linkify",h.info="auto"}return e.pos+=a.length-s.length,!0}function ol(e,t){let u=e.pos;if(e.src.charCodeAt(u)!==10)return!1;const r=e.pending.length-1,i=e.posMax;if(!t)if(r>=0&&e.pending.charCodeAt(r)===32)if(r>=1&&e.pending.charCodeAt(r-1)===32){let s=r-1;for(;s>=1&&e.pending.charCodeAt(s-1)===32;)s--;e.pending=e.pending.slice(0,s),e.push("hardbreak","br",0)}else e.pending=e.pending.slice(0,-1),e.push("softbreak","br",0);else e.push("softbreak","br",0);for(u++;u<i&&P(e.src.charCodeAt(u));)u++;return e.pos=u,!0}const Rr=[];for(let e=0;e<256;e++)Rr.push(0);"\\!\"#$%&'()*+,./:;<=>?@[]^_`{|}~-".split("").forEach(function(e){Rr[e.charCodeAt(0)]=1});function cl(e,t){let u=e.pos;const r=e.posMax;if(e.src.charCodeAt(u)!==92||(u++,u>=r))return!1;let i=e.src.charCodeAt(u);if(i===10){for(t||e.push("hardbreak","br",0),u++;u<r&&(i=e.src.charCodeAt(u),!!P(i));)u++;return e.pos=u,!0}let s=e.src[u];if(i>=55296&&i<=56319&&u+1<r){const a=e.src.charCodeAt(u+1);a>=56320&&a<=57343&&(s+=e.src[u+1],u++)}const n="\\"+s;if(!t){const a=e.push("text_special","",0);i<256&&Rr[i]!==0?a.content=s:a.content=n,a.markup=n,a.info="escape"}return e.pos=u+1,!0}function ll(e,t){let u=e.pos;if(e.src.charCodeAt(u)!==96)return!1;const i=u;u++;const s=e.posMax;for(;u<s&&e.src.charCodeAt(u)===96;)u++;const n=e.src.slice(i,u),a=n.length;if(e.backticksScanned&&(e.backticks[a]||0)<=i)return t||(e.pending+=n),e.pos+=a,!0;let c=u,l;for(;(l=e.src.indexOf("`",c))!==-1;){for(c=l+1;c<s&&e.src.charCodeAt(c)===96;)c++;const d=c-l;if(d===a){if(!t){const o=e.push("code_inline","code",0);o.markup=n,o.content=e.src.slice(u,l).replace(/\n/g," ").replace(/^ (.+) $/,"$1")}return e.pos=c,!0}e.backticks[d]=l}return e.backticksScanned=!0,t||(e.pending+=n),e.pos+=a,!0}function dl(e,t){const u=e.pos,r=e.src.charCodeAt(u);if(t||r!==126)return!1;const i=e.scanDelims(e.pos,!0);let s=i.length;const n=String.fromCharCode(r);if(s<2)return!1;let a;s%2&&(a=e.push("text","",0),a.content=n,s--);for(let c=0;c<s;c+=2)a=e.push("text","",0),a.content=n+n,e.delimiters.push({marker:r,length:0,token:e.tokens.length-1,end:-1,open:i.can_open,close:i.can_close});return e.pos+=i.length,!0}function Ni(e,t){let u;const r=[],i=t.length;for(let s=0;s<i;s++){const n=t[s];if(n.marker!==126||n.end===-1)continue;const a=t[n.end];u=e.tokens[n.token],u.type="s_open",u.tag="s",u.nesting=1,u.markup="~~",u.content="",u=e.tokens[a.token],u.type="s_close",u.tag="s",u.nesting=-1,u.markup="~~",u.content="",e.tokens[a.token-1].type==="text"&&e.tokens[a.token-1].content==="~"&&r.push(a.token-1)}for(;r.length;){const s=r.pop();let n=s+1;for(;n<e.tokens.length&&e.tokens[n].type==="s_close";)n++;n--,s!==n&&(u=e.tokens[n],e.tokens[n]=e.tokens[s],e.tokens[s]=u)}}function fl(e){const t=e.tokens_meta,u=e.tokens_meta.length;Ni(e,e.delimiters);for(let r=0;r<u;r++)t[r]&&t[r].delimiters&&Ni(e,t[r].delimiters)}const Zs={tokenize:dl,postProcess:fl};function hl(e,t){const u=e.pos,r=e.src.charCodeAt(u);if(t||r!==95&&r!==42)return!1;const i=e.scanDelims(e.pos,r===42);for(let s=0;s<i.length;s++){const n=e.push("text","",0);n.content=String.fromCharCode(r),e.delimiters.push({marker:r,length:i.length,token:e.tokens.length-1,end:-1,open:i.can_open,close:i.can_close})}return e.pos+=i.length,!0}function Mi(e,t){const u=t.length;for(let r=u-1;r>=0;r--){const i=t[r];if(i.marker!==95&&i.marker!==42||i.end===-1)continue;const s=t[i.end],n=r>0&&t[r-1].end===i.end+1&&t[r-1].marker===i.marker&&t[r-1].token===i.token-1&&t[i.end+1].token===s.token+1,a=String.fromCharCode(i.marker),c=e.tokens[i.token];c.type=n?"strong_open":"em_open",c.tag=n?"strong":"em",c.nesting=1,c.markup=n?a+a:a,c.content="";const l=e.tokens[s.token];l.type=n?"strong_close":"em_close",l.tag=n?"strong":"em",l.nesting=-1,l.markup=n?a+a:a,l.content="",n&&(e.tokens[t[r-1].token].content="",e.tokens[t[i.end+1].token].content="",r--)}}function pl(e){const t=e.tokens_meta,u=e.tokens_meta.length;Mi(e,e.delimiters);for(let r=0;r<u;r++)t[r]&&t[r].delimiters&&Mi(e,t[r].delimiters)}const Gs={tokenize:hl,postProcess:pl};function bl(e,t){let u,r,i,s,n="",a="",c=e.pos,l=!0;if(e.src.charCodeAt(e.pos)!==91)return!1;const d=e.pos,o=e.posMax,h=e.pos+1,p=e.md.helpers.parseLinkLabel(e,e.pos,!0);if(p<0)return!1;let f=p+1;if(f<o&&e.src.charCodeAt(f)===40){for(l=!1,f++;f<o&&(u=e.src.charCodeAt(f),!(!P(u)&&u!==10));f++);if(f>=o)return!1;if(c=f,i=e.md.helpers.parseLinkDestination(e.src,f,e.posMax),i.ok){for(n=e.md.normalizeLink(i.str),e.md.validateLink(n)?f=i.pos:n="",c=f;f<o&&(u=e.src.charCodeAt(f),!(!P(u)&&u!==10));f++);if(i=e.md.helpers.parseLinkTitle(e.src,f,e.posMax),f<o&&c!==f&&i.ok)for(a=i.str,f=i.pos;f<o&&(u=e.src.charCodeAt(f),!(!P(u)&&u!==10));f++);}(f>=o||e.src.charCodeAt(f)!==41)&&(l=!0),f++}if(l){if(typeof e.env.references>"u")return!1;if(f<o&&e.src.charCodeAt(f)===91?(c=f+1,f=e.md.helpers.parseLinkLabel(e,f),f>=0?r=e.src.slice(c,f++):f=p+1):f=p+1,r||(r=e.src.slice(h,p)),s=e.env.references[yu(r)],!s)return e.pos=d,!1;n=s.href,a=s.title}if(!t){e.pos=h,e.posMax=p;const b=e.push("link_open","a",1),m=[["href",n]];b.attrs=m,a&&m.push(["title",a]),e.linkLevel++,e.md.inline.tokenize(e),e.linkLevel--,e.push("link_close","a",-1)}return e.pos=f,e.posMax=o,!0}function ml(e,t){let u,r,i,s,n,a,c,l,d="";const o=e.pos,h=e.posMax;if(e.src.charCodeAt(e.pos)!==33||e.src.charCodeAt(e.pos+1)!==91)return!1;const p=e.pos+2,f=e.md.helpers.parseLinkLabel(e,e.pos+1,!1);if(f<0)return!1;if(s=f+1,s<h&&e.src.charCodeAt(s)===40){for(s++;s<h&&(u=e.src.charCodeAt(s),!(!P(u)&&u!==10));s++);if(s>=h)return!1;for(l=s,a=e.md.helpers.parseLinkDestination(e.src,s,e.posMax),a.ok&&(d=e.md.normalizeLink(a.str),e.md.validateLink(d)?s=a.pos:d=""),l=s;s<h&&(u=e.src.charCodeAt(s),!(!P(u)&&u!==10));s++);if(a=e.md.helpers.parseLinkTitle(e.src,s,e.posMax),s<h&&l!==s&&a.ok)for(c=a.str,s=a.pos;s<h&&(u=e.src.charCodeAt(s),!(!P(u)&&u!==10));s++);else c="";if(s>=h||e.src.charCodeAt(s)!==41)return e.pos=o,!1;s++}else{if(typeof e.env.references>"u")return!1;if(s<h&&e.src.charCodeAt(s)===91?(l=s+1,s=e.md.helpers.parseLinkLabel(e,s),s>=0?i=e.src.slice(l,s++):s=f+1):s=f+1,i||(i=e.src.slice(p,f)),n=e.env.references[yu(i)],!n)return e.pos=o,!1;d=n.href,c=n.title}if(!t){r=e.src.slice(p,f);const b=[];e.md.inline.parse(r,e.md,e.env,b);const m=e.push("image","img",0),g=[["src",d],["alt",""]];m.attrs=g,m.children=b,m.content=r,c&&g.push(["title",c])}return e.pos=s,e.posMax=h,!0}const gl=/^([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)$/,_l=/^([a-zA-Z][a-zA-Z0-9+.-]{1,31}):([^<>\x00-\x20]*)$/;function yl(e,t){let u=e.pos;if(e.src.charCodeAt(u)!==60)return!1;const r=e.pos,i=e.posMax;for(;;){if(++u>=i)return!1;const n=e.src.charCodeAt(u);if(n===60)return!1;if(n===62)break}const s=e.src.slice(r+1,u);if(_l.test(s)){const n=e.md.normalizeLink(s);if(!e.md.validateLink(n))return!1;if(!t){const a=e.push("link_open","a",1);a.attrs=[["href",n]],a.markup="autolink",a.info="auto";const c=e.push("text","",0);c.content=e.md.normalizeLinkText(s);const l=e.push("link_close","a",-1);l.markup="autolink",l.info="auto"}return e.pos+=s.length+2,!0}if(gl.test(s)){const n=e.md.normalizeLink("mailto:"+s);if(!e.md.validateLink(n))return!1;if(!t){const a=e.push("link_open","a",1);a.attrs=[["href",n]],a.markup="autolink",a.info="auto";const c=e.push("text","",0);c.content=e.md.normalizeLinkText(s);const l=e.push("link_close","a",-1);l.markup="autolink",l.info="auto"}return e.pos+=s.length+2,!0}return!1}function xl(e){return/^<a[>\s]/i.test(e)}function vl(e){return/^<\/a\s*>/i.test(e)}function wl(e){const t=e|32;return t>=97&&t<=122}function kl(e,t){if(!e.md.options.html)return!1;const u=e.posMax,r=e.pos;if(e.src.charCodeAt(r)!==60||r+2>=u)return!1;const i=e.src.charCodeAt(r+1);if(i!==33&&i!==63&&i!==47&&!wl(i))return!1;const s=e.src.slice(r).match(Yc);if(!s)return!1;if(!t){const n=e.push("html_inline","",0);n.content=s[0],xl(n.content)&&e.linkLevel++,vl(n.content)&&e.linkLevel--}return e.pos+=s[0].length,!0}const Cl=/^&#((?:x[a-f0-9]{1,6}|[0-9]{1,7}));/i,$l=/^&([a-z][a-z0-9]{1,31});/i;function El(e,t){const u=e.pos,r=e.posMax;if(e.src.charCodeAt(u)!==38||u+1>=r)return!1;if(e.src.charCodeAt(u+1)===35){const s=e.src.slice(u).match(Cl);if(s){if(!t){const n=s[1][0].toLowerCase()==="x"?parseInt(s[1].slice(1),16):parseInt(s[1],10),a=e.push("text_special","",0);a.content=Pr(n)?cu(n):cu(65533),a.markup=s[0],a.info="entity"}return e.pos+=s[0].length,!0}}else{const s=e.src.slice(u).match($l);if(s){const n=Us(s[0]);if(n!==s[0]){if(!t){const a=e.push("text_special","",0);a.content=n,a.markup=s[0],a.info="entity"}return e.pos+=s[0].length,!0}}}return!1}function ji(e){const t={},u=e.length;if(!u)return;let r=0,i=-2;const s=[];for(let n=0;n<u;n++){const a=e[n];if(s.push(0),(e[r].marker!==a.marker||i!==a.token-1)&&(r=n),i=a.token,a.length=a.length||0,!a.close)continue;t.hasOwnProperty(a.marker)||(t[a.marker]=[-1,-1,-1,-1,-1,-1]);const c=t[a.marker][(a.open?3:0)+a.length%3];let l=r-s[r]-1,d=l;for(;l>c;l-=s[l]+1){const o=e[l];if(o.marker===a.marker&&o.open&&o.end<0){let h=!1;if((o.close||a.open)&&(o.length+a.length)%3===0&&(o.length%3!==0||a.length%3!==0)&&(h=!0),!h){const p=l>0&&!e[l-1].open?s[l-1]+1:0;s[n]=n-l+p,s[l]=p,a.open=!1,o.end=n,o.close=!1,d=-1,i=-2;break}}}d!==-1&&(t[a.marker][(a.open?3:0)+(a.length||0)%3]=d)}}function Al(e){const t=e.tokens_meta,u=e.tokens_meta.length;ji(e.delimiters);for(let r=0;r<u;r++)t[r]&&t[r].delimiters&&ji(t[r].delimiters)}function Dl(e){let t,u,r=0;const i=e.tokens,s=e.tokens.length;for(t=u=0;t<s;t++)i[t].nesting<0&&r--,i[t].level=r,i[t].nesting>0&&r++,i[t].type==="text"&&t+1<s&&i[t+1].type==="text"?i[t+1].content=i[t].content+i[t+1].content:(t!==u&&(i[u]=i[t]),u++);t!==u&&(i.length=u)}const Vu=[["text",sl],["linkify",al],["newline",ol],["escape",cl],["backticks",ll],["strikethrough",Zs.tokenize],["emphasis",Gs.tokenize],["link",bl],["image",ml],["autolink",yl],["html_inline",kl],["entity",El]],Wu=[["balance_pairs",Al],["strikethrough",Zs.postProcess],["emphasis",Gs.postProcess],["fragments_join",Dl]];function Ut(){this.ruler=new re;for(let e=0;e<Vu.length;e++)this.ruler.push(Vu[e][0],Vu[e][1]);this.ruler2=new re;for(let e=0;e<Wu.length;e++)this.ruler2.push(Wu[e][0],Wu[e][1])}Ut.prototype.skipToken=function(e){const t=e.pos,u=this.ruler.getRules(""),r=u.length,i=e.md.options.maxNesting,s=e.cache;if(typeof s[t]<"u"){e.pos=s[t];return}let n=!1;if(e.level<i){for(let a=0;a<r;a++)if(e.level++,n=u[a](e,!0),e.level--,n){if(t>=e.pos)throw new Error("inline rule didn't increment state.pos");break}}else e.pos=e.posMax;n||e.pos++,s[t]=e.pos};Ut.prototype.tokenize=function(e){const t=this.ruler.getRules(""),u=t.length,r=e.posMax,i=e.md.options.maxNesting;for(;e.pos<r;){const s=e.pos;let n=!1;if(e.level<i){for(let a=0;a<u;a++)if(n=t[a](e,!1),n){if(s>=e.pos)throw new Error("inline rule didn't increment state.pos");break}}if(n){if(e.pos>=r)break;continue}e.pending+=e.src[e.pos++]}e.pending&&e.pushPending()};Ut.prototype.parse=function(e,t,u,r){const i=new this.State(e,t,u,r);this.tokenize(i);const s=this.ruler2.getRules(""),n=s.length;for(let a=0;a<n;a++)s[a](i)};Ut.prototype.State=Lt;function Sl(e){const t={};e=e||{},t.src_Any=Rs.source,t.src_Cc=Ns.source,t.src_Z=js.source,t.src_P=Ir.source,t.src_ZPCc=[t.src_Z,t.src_P,t.src_Cc].join("|"),t.src_ZCc=[t.src_Z,t.src_Cc].join("|");const u="[><｜]";return t.src_pseudo_letter="(?:(?!"+u+"|"+t.src_ZPCc+")"+t.src_Any+")",t.src_ip4="(?:(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",t.src_auth="(?:(?:(?!"+t.src_ZCc+"|[@/\\[\\]()]).)+@)?",t.src_port="(?::(?:6(?:[0-4]\\d{3}|5(?:[0-4]\\d{2}|5(?:[0-2]\\d|3[0-5])))|[1-5]?\\d{1,4}))?",t.src_host_terminator="(?=$|"+u+"|"+t.src_ZPCc+")(?!"+(e["---"]?"-(?!--)|":"-|")+"_|:\\d|\\.-|\\.(?!$|"+t.src_ZPCc+"))",t.src_path="(?:[/?#](?:(?!"+t.src_ZCc+"|"+u+`|[()[\\]{}.,"'?!\\-;]).|\\[(?:(?!`+t.src_ZCc+"|\\]).)*\\]|\\((?:(?!"+t.src_ZCc+"|[)]).)*\\)|\\{(?:(?!"+t.src_ZCc+'|[}]).)*\\}|\\"(?:(?!'+t.src_ZCc+`|["]).)+\\"|\\'(?:(?!`+t.src_ZCc+"|[']).)+\\'|\\'(?="+t.src_pseudo_letter+"|[-])|\\.{2,}[a-zA-Z0-9%/&]|\\.(?!"+t.src_ZCc+"|[.]|$)|"+(e["---"]?"\\-(?!--(?:[^-]|$))(?:-*)|":"\\-+|")+",(?!"+t.src_ZCc+"|$)|;(?!"+t.src_ZCc+"|$)|\\!+(?!"+t.src_ZCc+"|[!]|$)|\\?(?!"+t.src_ZCc+"|[?]|$))+|\\/)?",t.src_email_name='[\\-;:&=\\+\\$,\\.a-zA-Z0-9_][\\-;:&=\\+\\$,\\"\\.a-zA-Z0-9_]*',t.src_xn="xn--[a-z0-9\\-]{1,59}",t.src_domain_root="(?:"+t.src_xn+"|"+t.src_pseudo_letter+"{1,63})",t.src_domain="(?:"+t.src_xn+"|(?:"+t.src_pseudo_letter+")|(?:"+t.src_pseudo_letter+"(?:-|"+t.src_pseudo_letter+"){0,61}"+t.src_pseudo_letter+"))",t.src_host="(?:(?:(?:(?:"+t.src_domain+")\\.)*"+t.src_domain+"))",t.tpl_host_fuzzy="(?:"+t.src_ip4+"|(?:(?:(?:"+t.src_domain+")\\.)+(?:%TLDS%)))",t.tpl_host_no_ip_fuzzy="(?:(?:(?:"+t.src_domain+")\\.)+(?:%TLDS%))",t.src_host_strict=t.src_host+t.src_host_terminator,t.tpl_host_fuzzy_strict=t.tpl_host_fuzzy+t.src_host_terminator,t.src_host_port_strict=t.src_host+t.src_port+t.src_host_terminator,t.tpl_host_port_fuzzy_strict=t.tpl_host_fuzzy+t.src_port+t.src_host_terminator,t.tpl_host_port_no_ip_fuzzy_strict=t.tpl_host_no_ip_fuzzy+t.src_port+t.src_host_terminator,t.tpl_host_fuzzy_test="localhost|www\\.|\\.\\d{1,3}\\.|(?:\\.(?:%TLDS%)(?:"+t.src_ZPCc+"|>|$))",t.tpl_email_fuzzy="(^|"+u+'|"|\\(|'+t.src_ZCc+")("+t.src_email_name+"@"+t.tpl_host_fuzzy_strict+")",t.tpl_link_fuzzy="(^|(?![.:/\\-_@])(?:[$+<=>^`|｜]|"+t.src_ZPCc+"))((?![$+<=>^`|｜])"+t.tpl_host_port_fuzzy_strict+t.src_path+")",t.tpl_link_no_ip_fuzzy="(^|(?![.:/\\-_@])(?:[$+<=>^`|｜]|"+t.src_ZPCc+"))((?![$+<=>^`|｜])"+t.tpl_host_port_no_ip_fuzzy_strict+t.src_path+")",t}function cr(e){return Array.prototype.slice.call(arguments,1).forEach(function(u){u&&Object.keys(u).forEach(function(r){e[r]=u[r]})}),e}function vu(e){return Object.prototype.toString.call(e)}function Fl(e){return vu(e)==="[object String]"}function Tl(e){return vu(e)==="[object Object]"}function Il(e){return vu(e)==="[object RegExp]"}function Li(e){return vu(e)==="[object Function]"}function Ol(e){return e.replace(/[.?*+^$[\]\\(){}|-]/g,"\\$&")}const Ks={fuzzyLink:!0,fuzzyEmail:!0,fuzzyIP:!1};function Pl(e){return Object.keys(e||{}).reduce(function(t,u){return t||Ks.hasOwnProperty(u)},!1)}const zl={"http:":{validate:function(e,t,u){const r=e.slice(t);return u.re.http||(u.re.http=new RegExp("^\\/\\/"+u.re.src_auth+u.re.src_host_port_strict+u.re.src_path,"i")),u.re.http.test(r)?r.match(u.re.http)[0].length:0}},"https:":"http:","ftp:":"http:","//":{validate:function(e,t,u){const r=e.slice(t);return u.re.no_http||(u.re.no_http=new RegExp("^"+u.re.src_auth+"(?:localhost|(?:(?:"+u.re.src_domain+")\\.)+"+u.re.src_domain_root+")"+u.re.src_port+u.re.src_host_terminator+u.re.src_path,"i")),u.re.no_http.test(r)?t>=3&&e[t-3]===":"||t>=3&&e[t-3]==="/"?0:r.match(u.re.no_http)[0].length:0}},"mailto:":{validate:function(e,t,u){const r=e.slice(t);return u.re.mailto||(u.re.mailto=new RegExp("^"+u.re.src_email_name+"@"+u.re.src_host_strict,"i")),u.re.mailto.test(r)?r.match(u.re.mailto)[0].length:0}}},Rl="a[cdefgilmnoqrstuwxz]|b[abdefghijmnorstvwyz]|c[acdfghiklmnoruvwxyz]|d[ejkmoz]|e[cegrstu]|f[ijkmor]|g[abdefghilmnpqrstuwy]|h[kmnrtu]|i[delmnoqrst]|j[emop]|k[eghimnprwyz]|l[abcikrstuvy]|m[acdeghklmnopqrstuvwxyz]|n[acefgilopruz]|om|p[aefghklmnrstwy]|qa|r[eosuw]|s[abcdeghijklmnortuvxyz]|t[cdfghjklmnortvwz]|u[agksyz]|v[aceginu]|w[fs]|y[et]|z[amw]",Nl="biz|com|edu|gov|net|org|pro|web|xxx|aero|asia|coop|info|museum|name|shop|рф".split("|");function Ml(e){e.__index__=-1,e.__text_cache__=""}function jl(e){return function(t,u){const r=t.slice(u);return e.test(r)?r.match(e)[0].length:0}}function Ui(){return function(e,t){t.normalize(e)}}function lu(e){const t=e.re=Sl(e.__opts__),u=e.__tlds__.slice();e.onCompile(),e.__tlds_replaced__||u.push(Rl),u.push(t.src_xn),t.src_tlds=u.join("|");function r(a){return a.replace("%TLDS%",t.src_tlds)}t.email_fuzzy=RegExp(r(t.tpl_email_fuzzy),"i"),t.link_fuzzy=RegExp(r(t.tpl_link_fuzzy),"i"),t.link_no_ip_fuzzy=RegExp(r(t.tpl_link_no_ip_fuzzy),"i"),t.host_fuzzy_test=RegExp(r(t.tpl_host_fuzzy_test),"i");const i=[];e.__compiled__={};function s(a,c){throw new Error('(LinkifyIt) Invalid schema "'+a+'": '+c)}Object.keys(e.__schemas__).forEach(function(a){const c=e.__schemas__[a];if(c===null)return;const l={validate:null,link:null};if(e.__compiled__[a]=l,Tl(c)){Il(c.validate)?l.validate=jl(c.validate):Li(c.validate)?l.validate=c.validate:s(a,c),Li(c.normalize)?l.normalize=c.normalize:c.normalize?s(a,c):l.normalize=Ui();return}if(Fl(c)){i.push(a);return}s(a,c)}),i.forEach(function(a){e.__compiled__[e.__schemas__[a]]&&(e.__compiled__[a].validate=e.__compiled__[e.__schemas__[a]].validate,e.__compiled__[a].normalize=e.__compiled__[e.__schemas__[a]].normalize)}),e.__compiled__[""]={validate:null,normalize:Ui()};const n=Object.keys(e.__compiled__).filter(function(a){return a.length>0&&e.__compiled__[a]}).map(Ol).join("|");e.re.schema_test=RegExp("(^|(?!_)(?:[><｜]|"+t.src_ZPCc+"))("+n+")","i"),e.re.schema_search=RegExp("(^|(?!_)(?:[><｜]|"+t.src_ZPCc+"))("+n+")","ig"),e.re.schema_at_start=RegExp("^"+e.re.schema_search.source,"i"),e.re.pretest=RegExp("("+e.re.schema_test.source+")|("+e.re.host_fuzzy_test.source+")|@","i"),Ml(e)}function Ll(e,t){const u=e.__index__,r=e.__last_index__,i=e.__text_cache__.slice(u,r);this.schema=e.__schema__.toLowerCase(),this.index=u+t,this.lastIndex=r+t,this.raw=i,this.text=i,this.url=i}function lr(e,t){const u=new Ll(e,t);return e.__compiled__[u.schema].normalize(u,e),u}function se(e,t){if(!(this instanceof se))return new se(e,t);t||Pl(e)&&(t=e,e={}),this.__opts__=cr({},Ks,t),this.__index__=-1,this.__last_index__=-1,this.__schema__="",this.__text_cache__="",this.__schemas__=cr({},zl,e),this.__compiled__={},this.__tlds__=Nl,this.__tlds_replaced__=!1,this.re={},lu(this)}se.prototype.add=function(t,u){return this.__schemas__[t]=u,lu(this),this};se.prototype.set=function(t){return this.__opts__=cr(this.__opts__,t),this};se.prototype.test=function(t){if(this.__text_cache__=t,this.__index__=-1,!t.length)return!1;let u,r,i,s,n,a,c,l,d;if(this.re.schema_test.test(t)){for(c=this.re.schema_search,c.lastIndex=0;(u=c.exec(t))!==null;)if(s=this.testSchemaAt(t,u[2],c.lastIndex),s){this.__schema__=u[2],this.__index__=u.index+u[1].length,this.__last_index__=u.index+u[0].length+s;break}}return this.__opts__.fuzzyLink&&this.__compiled__["http:"]&&(l=t.search(this.re.host_fuzzy_test),l>=0&&(this.__index__<0||l<this.__index__)&&(r=t.match(this.__opts__.fuzzyIP?this.re.link_fuzzy:this.re.link_no_ip_fuzzy))!==null&&(n=r.index+r[1].length,(this.__index__<0||n<this.__index__)&&(this.__schema__="",this.__index__=n,this.__last_index__=r.index+r[0].length))),this.__opts__.fuzzyEmail&&this.__compiled__["mailto:"]&&(d=t.indexOf("@"),d>=0&&(i=t.match(this.re.email_fuzzy))!==null&&(n=i.index+i[1].length,a=i.index+i[0].length,(this.__index__<0||n<this.__index__||n===this.__index__&&a>this.__last_index__)&&(this.__schema__="mailto:",this.__index__=n,this.__last_index__=a))),this.__index__>=0};se.prototype.pretest=function(t){return this.re.pretest.test(t)};se.prototype.testSchemaAt=function(t,u,r){return this.__compiled__[u.toLowerCase()]?this.__compiled__[u.toLowerCase()].validate(t,r,this):0};se.prototype.match=function(t){const u=[];let r=0;this.__index__>=0&&this.__text_cache__===t&&(u.push(lr(this,r)),r=this.__last_index__);let i=r?t.slice(r):t;for(;this.test(i);)u.push(lr(this,r)),i=i.slice(this.__last_index__),r+=this.__last_index__;return u.length?u:null};se.prototype.matchAtStart=function(t){if(this.__text_cache__=t,this.__index__=-1,!t.length)return null;const u=this.re.schema_at_start.exec(t);if(!u)return null;const r=this.testSchemaAt(t,u[2],u[0].length);return r?(this.__schema__=u[2],this.__index__=u.index+u[1].length,this.__last_index__=u.index+u[0].length+r,lr(this,0)):null};se.prototype.tlds=function(t,u){return t=Array.isArray(t)?t:[t],u?(this.__tlds__=this.__tlds__.concat(t).sort().filter(function(r,i,s){return r!==s[i-1]}).reverse(),lu(this),this):(this.__tlds__=t.slice(),this.__tlds_replaced__=!0,lu(this),this)};se.prototype.normalize=function(t){t.schema||(t.url="http://"+t.url),t.schema==="mailto:"&&!/^mailto:/i.test(t.url)&&(t.url="mailto:"+t.url)};se.prototype.onCompile=function(){};const tt=2147483647,be=36,Nr=1,Rt=26,Ul=38,Bl=700,Qs=72,Ys=128,Xs="-",ql=/^xn--/,Hl=/[^\0-\x7F]/,Vl=/[\x2E\u3002\uFF0E\uFF61]/g,Wl={overflow:"Overflow: input needs wider integers to process","not-basic":"Illegal input >= 0x80 (not a basic code point)","invalid-input":"Invalid input"},Ju=be-Nr,me=Math.floor,Zu=String.fromCharCode;function Ae(e){throw new RangeError(Wl[e])}function Jl(e,t){const u=[];let r=e.length;for(;r--;)u[r]=t(e[r]);return u}function en(e,t){const u=e.split("@");let r="";u.length>1&&(r=u[0]+"@",e=u[1]),e=e.replace(Vl,".");const i=e.split("."),s=Jl(i,t).join(".");return r+s}function tn(e){const t=[];let u=0;const r=e.length;for(;u<r;){const i=e.charCodeAt(u++);if(i>=55296&&i<=56319&&u<r){const s=e.charCodeAt(u++);(s&64512)==56320?t.push(((i&1023)<<10)+(s&1023)+65536):(t.push(i),u--)}else t.push(i)}return t}const Zl=e=>String.fromCodePoint(...e),Gl=function(e){return e>=48&&e<58?26+(e-48):e>=65&&e<91?e-65:e>=97&&e<123?e-97:be},Bi=function(e,t){return e+22+75*(e<26)-((t!=0)<<5)},un=function(e,t,u){let r=0;for(e=u?me(e/Bl):e>>1,e+=me(e/t);e>Ju*Rt>>1;r+=be)e=me(e/Ju);return me(r+(Ju+1)*e/(e+Ul))},rn=function(e){const t=[],u=e.length;let r=0,i=Ys,s=Qs,n=e.lastIndexOf(Xs);n<0&&(n=0);for(let a=0;a<n;++a)e.charCodeAt(a)>=128&&Ae("not-basic"),t.push(e.charCodeAt(a));for(let a=n>0?n+1:0;a<u;){const c=r;for(let d=1,o=be;;o+=be){a>=u&&Ae("invalid-input");const h=Gl(e.charCodeAt(a++));h>=be&&Ae("invalid-input"),h>me((tt-r)/d)&&Ae("overflow"),r+=h*d;const p=o<=s?Nr:o>=s+Rt?Rt:o-s;if(h<p)break;const f=be-p;d>me(tt/f)&&Ae("overflow"),d*=f}const l=t.length+1;s=un(r-c,l,c==0),me(r/l)>tt-i&&Ae("overflow"),i+=me(r/l),r%=l,t.splice(r++,0,i)}return String.fromCodePoint(...t)},sn=function(e){const t=[];e=tn(e);const u=e.length;let r=Ys,i=0,s=Qs;for(const c of e)c<128&&t.push(Zu(c));const n=t.length;let a=n;for(n&&t.push(Xs);a<u;){let c=tt;for(const d of e)d>=r&&d<c&&(c=d);const l=a+1;c-r>me((tt-i)/l)&&Ae("overflow"),i+=(c-r)*l,r=c;for(const d of e)if(d<r&&++i>tt&&Ae("overflow"),d===r){let o=i;for(let h=be;;h+=be){const p=h<=s?Nr:h>=s+Rt?Rt:h-s;if(o<p)break;const f=o-p,b=be-p;t.push(Zu(Bi(p+f%b,0))),o=me(f/b)}t.push(Zu(Bi(o,0))),s=un(i,l,a===n),i=0,++a}++i,++r}return t.join("")},Kl=function(e){return en(e,function(t){return ql.test(t)?rn(t.slice(4).toLowerCase()):t})},Ql=function(e){return en(e,function(t){return Hl.test(t)?"xn--"+sn(t):t})},nn={version:"2.3.1",ucs2:{decode:tn,encode:Zl},decode:rn,encode:sn,toASCII:Ql,toUnicode:Kl},Yl={options:{html:!1,xhtmlOut:!1,breaks:!1,langPrefix:"language-",linkify:!1,typographer:!1,quotes:"“”‘’",highlight:null,maxNesting:100},components:{core:{},block:{},inline:{}}},Xl={options:{html:!1,xhtmlOut:!1,breaks:!1,langPrefix:"language-",linkify:!1,typographer:!1,quotes:"“”‘’",highlight:null,maxNesting:20},components:{core:{rules:["normalize","block","inline","text_join"]},block:{rules:["paragraph"]},inline:{rules:["text"],rules2:["balance_pairs","fragments_join"]}}},e0={options:{html:!0,xhtmlOut:!0,breaks:!1,langPrefix:"language-",linkify:!1,typographer:!1,quotes:"“”‘’",highlight:null,maxNesting:20},components:{core:{rules:["normalize","block","inline","text_join"]},block:{rules:["blockquote","code","fence","heading","hr","html_block","lheading","list","reference","paragraph"]},inline:{rules:["autolink","backticks","emphasis","entity","escape","html_inline","image","link","newline","text"],rules2:["balance_pairs","emphasis","fragments_join"]}}},t0={default:Yl,zero:Xl,commonmark:e0},u0=/^(vbscript|javascript|file|data):/,r0=/^data:image\/(gif|png|jpeg|webp);/;function i0(e){const t=e.trim().toLowerCase();return u0.test(t)?r0.test(t):!0}const an=["http:","https:","mailto:"];function s0(e){const t=Tr(e,!0);if(t.hostname&&(!t.protocol||an.indexOf(t.protocol)>=0))try{t.hostname=nn.toASCII(t.hostname)}catch{}return jt(Fr(t))}function n0(e){const t=Tr(e,!0);if(t.hostname&&(!t.protocol||an.indexOf(t.protocol)>=0))try{t.hostname=nn.toUnicode(t.hostname)}catch{}return nt(Fr(t),nt.defaultChars+"%")}function ne(e,t){if(!(this instanceof ne))return new ne(e,t);t||Or(e)||(t=e||{},e="default"),this.inline=new Ut,this.block=new xu,this.core=new zr,this.renderer=new ft,this.linkify=new se,this.validateLink=i0,this.normalizeLink=s0,this.normalizeLinkText=n0,this.utils=oc,this.helpers=_u({},fc),this.options={},this.configure(e),t&&this.set(t)}ne.prototype.set=function(e){return _u(this.options,e),this};ne.prototype.configure=function(e){const t=this;if(Or(e)){const u=e;if(e=t0[u],!e)throw new Error('Wrong `markdown-it` preset "'+u+'", check name')}if(!e)throw new Error("Wrong `markdown-it` preset, can't be empty");return e.options&&t.set(e.options),e.components&&Object.keys(e.components).forEach(function(u){e.components[u].rules&&t[u].ruler.enableOnly(e.components[u].rules),e.components[u].rules2&&t[u].ruler2.enableOnly(e.components[u].rules2)}),this};ne.prototype.enable=function(e,t){let u=[];Array.isArray(e)||(e=[e]),["core","block","inline"].forEach(function(i){u=u.concat(this[i].ruler.enable(e,!0))},this),u=u.concat(this.inline.ruler2.enable(e,!0));const r=e.filter(function(i){return u.indexOf(i)<0});if(r.length&&!t)throw new Error("MarkdownIt. Failed to enable unknown rule(s): "+r);return this};ne.prototype.disable=function(e,t){let u=[];Array.isArray(e)||(e=[e]),["core","block","inline"].forEach(function(i){u=u.concat(this[i].ruler.disable(e,!0))},this),u=u.concat(this.inline.ruler2.disable(e,!0));const r=e.filter(function(i){return u.indexOf(i)<0});if(r.length&&!t)throw new Error("MarkdownIt. Failed to disable unknown rule(s): "+r);return this};ne.prototype.use=function(e){const t=[this].concat(Array.prototype.slice.call(arguments,1));return e.apply(e,t),this};ne.prototype.parse=function(e,t){if(typeof e!="string")throw new Error("Input data should be a String");const u=new this.core.State(e,this,t);return this.core.process(u),u.tokens};ne.prototype.render=function(e,t){return t=t||{},this.renderer.render(this.parse(e,t),this.options,t)};ne.prototype.parseInline=function(e,t){const u=new this.core.State(e,this,t);return u.inlineMode=!0,this.core.process(u),u.tokens};ne.prototype.renderInline=function(e,t){return t=t||{},this.renderer.render(this.parseInline(e,t),this.options,t)};function a0(e){const t=document.createElement("div");return kr(k`${e}`,t),t.innerHTML.replaceAll(/<!--([^-]*)-->/gim,"")}class o0 extends lt{#e=ne({highlight:(t,u)=>{if(u==="html"){const r=document.createElement("iframe");return r.classList.add("html-view"),r.srcdoc=t,r.sandbox="",r.innerHTML}else return a0(t)}});#u=null;#r=null;update(t,[u,r]){return this.#u===u&&JSON.stringify(r)===this.#r?de:(this.#u=u,this.#r=JSON.stringify(r),this.render(u,r))}#t=new Map;#i(t){Object.entries(t).forEach(([u])=>{let r;switch(u){case"p":r="paragraph";break;case"h1":case"h2":case"h3":case"h4":case"h5":case"h6":r="heading";break;case"ul":r="bullet_list";break;case"ol":r="ordered_list";break;case"li":r="list_item";break;case"a":r="link";break;case"strong":r="strong";break;case"em":r="em";break}if(!r)return;const i=`${r}_open`;this.#e.renderer.rules[i]=(s,n,a,c,l)=>{const d=s[n],o=t[d.tag]??[];for(const h of o)d.attrJoin("class",h);return l.renderToken(s,n,a)}})}#a(){for(const[t]of this.#t)delete this.#e.renderer.rules[t];this.#t.clear()}render(t,u){u&&this.#i(u);const r=this.#e.render(t);return this.#a(),vo(r)}}const c0=ct(o0);ne();var Gu=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},kt=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-text")],t,u=[],r,i=Z,s,n=[],a=[],c,l=[],d=[];return class extends i{static{r=this}static{const o=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],c=[A({reflect:!0,attribute:"usage-hint"})],Gu(this,null,s,{kind:"accessor",name:"text",static:!1,private:!1,access:{has:h=>"text"in h,get:h=>h.text,set:(h,p)=>{h.text=p}},metadata:o},n,a),Gu(this,null,c,{kind:"accessor",name:"usageHint",static:!1,private:!1,access:{has:h=>"usageHint"in h,get:h=>h.usageHint,set:(h,p)=>{h.usageHint=p}},metadata:o},l,d),Gu(null,t={value:r},e,{kind:"class",name:r.name,metadata:o},null,u),r=t.value,o&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:o})}#e=kt(this,n,null);get text(){return this.#e}set text(o){this.#e=o}#u=(kt(this,a),kt(this,l,null));get usageHint(){return this.#u}set usageHint(o){this.#u=o}static{this.styles=[J,M`
      :host {
        display: block;
        flex: var(--weight);
      }

      h1,
      h2,
      h3,
      h4,
      h5 {
        line-height: inherit;
        font: inherit;
      }
    `]}#r(){let o=null;if(this.text&&typeof this.text=="object"){if("literalString"in this.text&&this.text.literalString)o=this.text.literalString;else if("literal"in this.text&&this.text.literal!==void 0)o=this.text.literal;else if(this.text&&"path"in this.text&&this.text.path){if(!this.processor||!this.component)return k`(no model)`;const p=this.processor.getData(this.component,this.text.path,this.surfaceId??N.DEFAULT_SURFACE_ID);p!=null&&(o=p.toString())}}if(o==null)return k`(empty)`;let h=o;switch(this.usageHint){case"h1":h=`# ${h}`;break;case"h2":h=`## ${h}`;break;case"h3":h=`### ${h}`;break;case"h4":h=`#### ${h}`;break;case"h5":h=`##### ${h}`;break;case"caption":h=`*${h}*`;break}return k`${c0(h,Ga(this.theme.markdown,["ol","ul","li"],{}))}`}#t(o){return typeof o!="object"||Array.isArray(o)||!o?!1:["h1","h2","h3","h4","h5","h6","caption","body"].every(p=>p in o)}#i(){let o={};const h=this.theme.additionalStyles?.Text;if(!h)return o;if(this.#t(h)){const p=this.usageHint??"body";o=h[p]}else o=h;return o}render(){const o=ae(this.theme.components.Text.all,this.usageHint?this.theme.components.Text[this.usageHint]:{});return k`<section
      class=${T(o)}
      style=${this.theme.additionalStyles?.Text?q(this.#i()):$}
    >
      ${this.#r()}
    </section>`}constructor(){super(...arguments),kt(this,d)}static{kt(r,u)}},r})();var qi=function(e,t,u,r,i,s){function n(g){if(g!==void 0&&typeof g!="function")throw new TypeError("Function expected");return g}for(var a=r.kind,c=a==="getter"?"get":a==="setter"?"set":"value",l=!t&&e?r.static?e:e.prototype:null,d=t||(l?Object.getOwnPropertyDescriptor(l,r.name):{}),o,h=!1,p=u.length-1;p>=0;p--){var f={};for(var b in r)f[b]=b==="access"?{}:r[b];for(var b in r.access)f.access[b]=r.access[b];f.addInitializer=function(g){if(h)throw new TypeError("Cannot add initializers after decoration has completed");s.push(n(g||null))};var m=(0,u[p])(a==="accessor"?{get:d.get,set:d.set}:d[c],f);if(a==="accessor"){if(m===void 0)continue;if(m===null||typeof m!="object")throw new TypeError("Object expected");(o=n(m.get))&&(d.get=o),(o=n(m.set))&&(d.set=o),(o=n(m.init))&&i.unshift(o)}else(o=n(m))&&(a==="field"?i.unshift(o):d[c]=o)}l&&Object.defineProperty(l,r.name,d),h=!0},Ku=function(e,t,u){for(var r=arguments.length>2,i=0;i<t.length;i++)u=r?t[i].call(e,u):t[i].call(e);return r?u:void 0};(()=>{let e=[j("a2ui-video")],t,u=[],r,i=Z,s,n=[],a=[];return class extends i{static{r=this}static{const c=typeof Symbol=="function"&&Symbol.metadata?Object.create(i[Symbol.metadata]??null):void 0;s=[A()],qi(this,null,s,{kind:"accessor",name:"url",static:!1,private:!1,access:{has:l=>"url"in l,get:l=>l.url,set:(l,d)=>{l.url=d}},metadata:c},n,a),qi(null,t={value:r},e,{kind:"class",name:r.name,metadata:c},null,u),r=t.value,c&&Object.defineProperty(r,Symbol.metadata,{enumerable:!0,configurable:!0,writable:!0,value:c})}#e=Ku(this,n,null);get url(){return this.#e}set url(c){this.#e=c}static{this.styles=[J,M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: auto;
      }

      video {
        display: block;
        width: 100%;
      }
    `]}#u(){if(!this.url)return $;if(this.url&&typeof this.url=="object"){if("literalString"in this.url)return k`<video controls src=${this.url.literalString} />`;if("literal"in this.url)return k`<video controls src=${this.url.literal} />`;if(this.url&&"path"in this.url&&this.url.path){if(!this.processor||!this.component)return k`(no processor)`;const c=this.processor.getData(this.component,this.url.path,this.surfaceId??N.DEFAULT_SURFACE_ID);return c?typeof c!="string"?k`Invalid video URL`:k`<video controls src=${c} />`:k`Invalid video URL`}}return k`(empty)`}render(){return k`<section
      class=${T(this.theme.components.Video)}
      style=${this.theme.additionalStyles?.Video?q(this.theme.additionalStyles?.Video):$}
    >
      ${this.#u()}
    </section>`}constructor(){super(...arguments),Ku(this,a)}static{Ku(r,u)}},r})();const l0={"typography-f-sf":!0,"typography-fs-n":!0,"typography-w-500":!0,"layout-as-n":!0,"layout-dis-iflx":!0,"layout-al-c":!0,"typography-td-none":!0,"color-c-p40":!0},d0={"layout-w-100":!0},f0={"typography-f-s":!0,"typography-fs-n":!0,"typography-w-400":!0,"layout-mt-0":!0,"layout-mb-2":!0,"typography-sz-bm":!0,"color-c-n10":!0},h0={"typography-f-sf":!0,"typography-fs-n":!0,"typography-w-500":!0,"layout-pt-3":!0,"layout-pb-3":!0,"layout-pl-5":!0,"layout-pr-5":!0,"layout-mb-1":!0,"border-br-16":!0,"border-bw-0":!0,"border-c-n70":!0,"border-bs-s":!0,"color-bgc-s30":!0,"behavior-ho-80":!0},pe={"typography-f-sf":!0,"typography-fs-n":!0,"typography-w-500":!0,"layout-mt-0":!0,"layout-mb-2":!0},p0={"behavior-sw-n":!0},on={"typography-f-sf":!0,"typography-fs-n":!0,"typography-w-400":!0,"layout-pl-4":!0,"layout-pr-4":!0,"layout-pt-2":!0,"layout-pb-2":!0,"border-br-6":!0,"border-bw-1":!0,"color-bc-s70":!0,"border-bs-s":!0,"layout-as-n":!0,"color-c-n10":!0},b0={"typography-f-s":!0,"typography-fs-n":!0,"typography-w-400":!0,"layout-m-0":!0,"typography-sz-bm":!0,"layout-as-n":!0,"color-c-n10":!0},m0={"typography-f-s":!0,"typography-fs-n":!0,"typography-w-400":!0,"layout-m-0":!0,"typography-sz-bm":!0,"layout-as-n":!0,"color-c-n10":!0},g0={"typography-f-s":!0,"typography-fs-n":!0,"typography-w-400":!0,"layout-m-0":!0,"typography-sz-bm":!0,"layout-as-n":!0,"color-c-n10":!0},_0={"typography-f-s":!0,"typography-fs-n":!0,"typography-w-400":!0,"layout-m-0":!0,"typography-sz-bm":!0,"layout-as-n":!0,"color-c-n10":!0},y0={"typography-f-c":!0,"typography-fs-n":!0,"typography-w-400":!0,"typography-sz-bm":!0,"typography-ws-p":!0,"layout-as-n":!0},x0={...on,"layout-r-none":!0,"layout-fs-c":!0},v0={"layout-el-cv":!0},Hi=ae(l0,{}),w0=ae(on,{}),k0=ae(x0,{}),C0=ae(h0,{}),$0=ae(f0,{}),Vi=ae(b0,{}),E0=ae(y0,{}),A0=ae(m0,{}),D0=ae(g0,{}),S0=ae(_0,{}),Mr={additionalStyles:{Button:{"--n-35":"var(--n-100)","--n-10":"var(--n-0)",background:"linear-gradient(135deg, light-dark(#818cf8, #06b6d4) 0%, light-dark(#a78bfa, #3b82f6) 100%)",boxShadow:"0 4px 15px rgba(102, 126, 234, 0.4)",padding:"12px 28px",textTransform:"uppercase"},Text:{h1:{color:"transparent",background:"linear-gradient(135deg, light-dark(#818cf8, #06b6d4) 0%, light-dark(#a78bfa, #3b82f6) 100%)","-webkit-background-clip":"text","background-clip":"text","-webkit-text-fill-color":"transparent"},h2:{color:"transparent",background:"linear-gradient(135deg, light-dark(#818cf8, #06b6d4) 0%, light-dark(#a78bfa, #3b82f6) 100%)","-webkit-background-clip":"text","background-clip":"text","-webkit-text-fill-color":"transparent"},h3:{color:"transparent",background:"linear-gradient(135deg, light-dark(#818cf8, #06b6d4) 0%, light-dark(#a78bfa, #3b82f6) 100%)","-webkit-background-clip":"text","background-clip":"text","-webkit-text-fill-color":"transparent"},h4:{},h5:{},body:{},caption:{}},Card:{background:"radial-gradient(circle at top left, light-dark(transparent, rgba(6, 182, 212, 0.15)), transparent 40%), radial-gradient(circle at bottom right, light-dark(transparent, rgba(139, 92, 246, 0.15)), transparent 40%), linear-gradient(135deg, light-dark(rgba(255, 255, 255, 0.7), rgba(30, 41, 59, 0.7)), light-dark(rgba(255, 255, 255, 0.7), rgba(15, 23, 42, 0.8)))"},TextField:{"--p-0":"light-dark(var(--n-0), #1e293b)","--color-error":"#B3261E"}},components:{AudioPlayer:{},Button:{"layout-pt-2":!0,"layout-pb-2":!0,"layout-pl-3":!0,"layout-pr-3":!0,"border-br-12":!0,"border-bw-0":!0,"border-bs-s":!0,"color-bgc-p30":!0,"behavior-ho-70":!0,"typography-w-400":!0},Card:{"border-br-9":!0,"layout-p-4":!0,"color-bgc-n100":!0},CheckBox:{element:{"layout-m-0":!0,"layout-mr-2":!0,"layout-p-2":!0,"border-br-12":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bgc-p100":!0,"color-bc-p60":!0,"color-c-n30":!0,"color-c-p30":!0},label:{"color-c-p30":!0,"typography-f-sf":!0,"typography-v-r":!0,"typography-w-400":!0,"layout-flx-1":!0,"typography-sz-ll":!0},container:{"layout-dsp-iflex":!0,"layout-al-c":!0}},Column:{"layout-g-2":!0},DateTimeInput:{container:{"typography-sz-bm":!0,"layout-w-100":!0,"layout-g-2":!0,"layout-dsp-flexhor":!0,"layout-al-c":!0,"typography-ws-nw":!0},label:{"color-c-p30":!0,"typography-sz-bm":!0},element:{"layout-pt-2":!0,"layout-pb-2":!0,"layout-pl-3":!0,"layout-pr-3":!0,"border-br-2":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bgc-p100":!0,"color-bc-p60":!0,"color-c-n30":!0,"color-c-p30":!0}},Divider:{},Image:{all:{"border-br-5":!0,"layout-el-cv":!0,"layout-w-100":!0,"layout-h-100":!0},avatar:{"is-avatar":!0},header:{},icon:{},largeFeature:{},mediumFeature:{},smallFeature:{}},Icon:{},List:{"layout-g-4":!0,"layout-p-2":!0},Modal:{backdrop:{"color-bbgc-p60_20":!0},element:{"border-br-2":!0,"color-bgc-p100":!0,"layout-p-4":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bc-p80":!0}},MultipleChoice:{container:{},label:{},element:{}},Row:{"layout-g-4":!0},Slider:{container:{},label:{},element:{}},Tabs:{container:{},controls:{all:{},selected:{}},element:{}},Text:{all:{"layout-w-100":!0,"layout-g-2":!0},h1:{"typography-f-sf":!0,"typography-v-r":!0,"typography-w-400":!0,"layout-m-0":!0,"layout-p-0":!0,"typography-sz-hs":!0},h2:{"typography-f-sf":!0,"typography-v-r":!0,"typography-w-400":!0,"layout-m-0":!0,"layout-p-0":!0,"typography-sz-tl":!0},h3:{"typography-f-sf":!0,"typography-v-r":!0,"typography-w-400":!0,"layout-m-0":!0,"layout-p-0":!0,"typography-sz-tl":!0},h4:{"typography-f-sf":!0,"typography-v-r":!0,"typography-w-400":!0,"layout-m-0":!0,"layout-p-0":!0,"typography-sz-bl":!0},h5:{"typography-f-sf":!0,"typography-v-r":!0,"typography-w-400":!0,"layout-m-0":!0,"layout-p-0":!0,"typography-sz-bm":!0},body:{},caption:{}},TextField:{container:{"typography-sz-bm":!0,"layout-w-100":!0,"layout-g-2":!0,"layout-dsp-flexhor":!0,"layout-al-c":!0,"typography-ws-nw":!0},label:{"layout-flx-0":!0,"color-c-p30":!0},element:{"typography-sz-bm":!0,"layout-pt-2":!0,"layout-pb-2":!0,"layout-pl-3":!0,"layout-pr-3":!0,"border-br-2":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bgc-p100":!0,"color-bc-p60":!0,"color-c-n30":!0,"color-c-p30":!0}},Video:{"border-br-5":!0,"layout-el-cv":!0}},elements:{a:Hi,audio:d0,body:$0,button:C0,h1:pe,h2:pe,h3:pe,h4:pe,h5:pe,iframe:p0,input:w0,p:Vi,pre:E0,textarea:k0,video:v0},markdown:{p:[...Object.keys(Vi)],h1:[...Object.keys(pe)],h2:[...Object.keys(pe)],h3:[...Object.keys(pe)],h4:[...Object.keys(pe)],h5:[...Object.keys(pe)],ul:[...Object.keys(D0)],ol:[...Object.keys(A0)],li:[...Object.keys(S0)],a:[...Object.keys(Hi)],strong:[],em:[]}};async function*F0(e){if(!e.body)throw new Error("SSE response body is undefined. Cannot read stream.");let t="",u="message",r="";const i=e.body.pipeThrough(new TextDecoderStream);for await(const s of T0(i)){t+=s;let n;for(;(n=t.indexOf(`
`))>=0;){const a=t.substring(0,n).trim();t=t.substring(n+1),a===""?r&&(yield{type:u,data:r},r="",u="message"):a.startsWith("event:")?u=a.substring(6).trim():a.startsWith("data:")&&(r=a.substring(5).trim())}}r&&(yield{type:u,data:r})}async function*T0(e){const t=e.getReader();try{for(;;){const{done:u,value:r}=await t.read();if(u)break;yield r}}finally{t.releaseLock()}}var I0=".well-known/agent-card.json",O0=class extends Error{constructor(e){super(e??"Task not found"),this.name="TaskNotFoundError"}},P0=class extends Error{constructor(e){super(e??"Task cannot be canceled"),this.name="TaskNotCancelableError"}},z0=class extends Error{constructor(e){super(e??"Push Notification is not supported"),this.name="PushNotificationNotSupportedError"}},R0=class extends Error{constructor(e){super(e??"This operation is not supported"),this.name="UnsupportedOperationError"}},N0=class extends Error{constructor(e){super(e??"Incompatible content types"),this.name="ContentTypeNotSupportedError"}},M0=class extends Error{constructor(e){super(e??"Invalid agent response type"),this.name="InvalidAgentResponseError"}},j0=class extends Error{constructor(e){super(e??"Authenticated Extended Card not configured"),this.name="AuthenticatedExtendedCardNotConfiguredError"}},L0=class Xt{customFetchImpl;endpoint;requestIdCounter=1;constructor(t){this.endpoint=t.endpoint,this.customFetchImpl=t.fetchImpl}async getExtendedAgentCard(t,u){return(await this._sendRpcRequest("agent/getAuthenticatedExtendedCard",void 0,u,t)).result}async sendMessage(t,u,r){return(await this._sendRpcRequest("message/send",t,r,u)).result}async*sendMessageStream(t,u){yield*this._sendStreamingRequest("message/stream",t,u)}async setTaskPushNotificationConfig(t,u,r){return(await this._sendRpcRequest("tasks/pushNotificationConfig/set",t,r,u)).result}async getTaskPushNotificationConfig(t,u,r){return(await this._sendRpcRequest("tasks/pushNotificationConfig/get",t,r,u)).result}async listTaskPushNotificationConfig(t,u,r){return(await this._sendRpcRequest("tasks/pushNotificationConfig/list",t,r,u)).result}async deleteTaskPushNotificationConfig(t,u,r){await this._sendRpcRequest("tasks/pushNotificationConfig/delete",t,r,u)}async getTask(t,u,r){return(await this._sendRpcRequest("tasks/get",t,r,u)).result}async cancelTask(t,u,r){return(await this._sendRpcRequest("tasks/cancel",t,r,u)).result}async*resubscribeTask(t,u){yield*this._sendStreamingRequest("tasks/resubscribe",t,u)}async callExtensionMethod(t,u,r,i){return await this._sendRpcRequest(t,u,r,i)}_fetch(...t){if(this.customFetchImpl)return this.customFetchImpl(...t);if(typeof fetch=="function")return fetch(...t);throw new Error("A `fetch` implementation was not provided and is not available in the global scope. Please provide a `fetchImpl` in the A2ATransportOptions. ")}async _sendRpcRequest(t,u,r,i){const s=r??this.requestIdCounter++,n={jsonrpc:"2.0",method:t,params:u,id:s},a=await this._fetchRpc(n,"application/json",i);if(!a.ok){let l="(empty or non-JSON response)",d;try{l=await a.text(),d=JSON.parse(l)}catch(o){throw new Error(`HTTP error for ${t}! Status: ${a.status} ${a.statusText}. Response: ${l}`,{cause:o})}throw d.jsonrpc&&d.error?Xt.mapToError(d):new Error(`HTTP error for ${t}! Status: ${a.status} ${a.statusText}. Response: ${l}`)}const c=await a.json();if(c.id!==s&&console.error(`CRITICAL: RPC response ID mismatch for method ${t}. Expected ${s}, got ${c.id}.`),"error"in c)throw Xt.mapToError(c);return c}async _fetchRpc(t,u="application/json",r){const i={method:"POST",headers:{...r?.serviceParameters,"Content-Type":"application/json",Accept:u},body:JSON.stringify(t),signal:r?.signal};return this._fetch(this.endpoint,i)}async*_sendStreamingRequest(t,u,r){const i=this.requestIdCounter++,s={jsonrpc:"2.0",method:t,params:u,id:i},n=await this._fetchRpc(s,"text/event-stream",r);if(!n.ok){let a="",c;try{a=await n.text(),c=JSON.parse(a)}catch(l){throw new Error(`HTTP error establishing stream for ${t}: ${n.status} ${n.statusText}. Response: ${a||"(empty)"}`,{cause:l})}throw c.error?new Error(`HTTP error establishing stream for ${t}: ${n.status} ${n.statusText}. RPC Error: ${c.error.message} (Code: ${c.error.code})`):new Error(`HTTP error establishing stream for ${t}: ${n.status} ${n.statusText}`)}if(!n.headers.get("Content-Type")?.startsWith("text/event-stream"))throw new Error(`Invalid response Content-Type for SSE stream for ${t}. Expected 'text/event-stream'.`);for await(const a of F0(n))yield this._processSseEventData(a.data,i)}_processSseEventData(t,u){if(!t.trim())throw new Error("Attempted to process empty SSE event data.");try{const i=JSON.parse(t);if(i.id!==u&&console.warn(`SSE Event's JSON-RPC response ID mismatch. Client request ID: ${u}, event response ID: ${i.id}.`),"error"in i){const s=i.error;throw new Error(`SSE event contained an error: ${s.message} (Code: ${s.code}) Data: ${JSON.stringify(s.data||{})}`,{cause:Xt.mapToError(i)})}if(!("result"in i)||typeof i.result>"u")throw new Error(`SSE event JSON-RPC response is missing 'result' field. Data: ${t}`);return i.result}catch(r){throw r instanceof Error&&(r.message.startsWith("SSE event contained an error")||r.message.startsWith("SSE event JSON-RPC response is missing 'result' field"))?r:(console.error("Failed to parse SSE event data string or unexpected JSON-RPC structure:",t,r),new Error(`Failed to parse SSE event data: "${t.substring(0,100)}...". Original error: ${r instanceof Error&&r.message||"Unknown error"}`))}}static mapToError(t){switch(t.error.code){case-32001:return new B0(t);case-32002:return new q0(t);case-32003:return new H0(t);case-32004:return new V0(t);case-32005:return new W0(t);case-32006:return new J0(t);case-32007:return new Z0(t);default:return new U0(t)}}},U0=class extends Error{constructor(e){super(`JSON-RPC error: ${e.error.message} (Code: ${e.error.code}) Data: ${JSON.stringify(e.error.data||{})}`),this.errorResponse=e}},B0=class extends O0{constructor(e){super(),this.errorResponse=e}},q0=class extends P0{constructor(e){super(),this.errorResponse=e}},H0=class extends z0{constructor(e){super(),this.errorResponse=e}},V0=class extends R0{constructor(e){super(),this.errorResponse=e}},W0=class extends N0{constructor(e){super(),this.errorResponse=e}},J0=class extends M0{constructor(e){super(),this.errorResponse=e}},Z0=class extends j0{constructor(e){super(),this.errorResponse=e}},G0=class we{static emptyOptions=void 0;agentCardPromise;customFetchImpl;serviceEndpointUrl;transport;requestIdCounter=1;constructor(t,u){if(this.customFetchImpl=u?.fetchImpl,typeof t=="string")console.warn("Warning: Constructing A2AClient with a URL is deprecated. Please use A2AClient.fromCardUrl() instead."),this.agentCardPromise=this._fetchAndCacheAgentCard(t,u?.agentCardPath);else{if(!t.url)throw new Error("Provided Agent Card does not contain a valid 'url' for the service endpoint.");this.serviceEndpointUrl=t.url,this.agentCardPromise=Promise.resolve(t)}}_fetch(...t){if(this.customFetchImpl)return this.customFetchImpl(...t);if(typeof fetch=="function")return fetch(...t);throw new Error("A `fetch` implementation was not provided and is not available in the global scope. Please provide a `fetchImpl` in the A2AClientOptions. For earlier Node.js versions (pre-v18), you can use a library like `node-fetch`.")}static async fromCardUrl(t,u){const r=u?.fetchImpl,i={headers:{Accept:"application/json"}};let s;if(r)s=await r(t,i);else if(typeof fetch=="function")s=await fetch(t,i);else throw new Error("A `fetch` implementation was not provided and is not available in the global scope. Please provide a `fetchImpl` in the A2AClientOptions. For earlier Node.js versions (pre-v18), you can use a library like `node-fetch`.");if(!s.ok)throw new Error(`Failed to fetch Agent Card from ${t}: ${s.status} ${s.statusText}`);let n;try{n=await s.json()}catch(a){throw console.error("Failed to parse Agent Card JSON:",a),new Error(`Failed to parse Agent Card JSON from ${t}. Original error: ${a.message}`)}return new we(n,u)}async sendMessage(t){return await this.invokeJsonRpc((u,r,i)=>u.sendMessage(r,we.emptyOptions,i),t)}async*sendMessageStream(t){if(!(await this.agentCardPromise).capabilities?.streaming)throw new Error("Agent does not support streaming (AgentCard.capabilities.streaming is not true).");yield*(await this._getOrCreateTransport()).sendMessageStream(t)}async setTaskPushNotificationConfig(t){if(!(await this.agentCardPromise).capabilities?.pushNotifications)throw new Error("Agent does not support push notifications (AgentCard.capabilities.pushNotifications is not true).");return await this.invokeJsonRpc((r,i,s)=>r.setTaskPushNotificationConfig(i,we.emptyOptions,s),t)}async getTaskPushNotificationConfig(t){return await this.invokeJsonRpc((u,r,i)=>u.getTaskPushNotificationConfig(r,we.emptyOptions,i),t)}async listTaskPushNotificationConfig(t){return await this.invokeJsonRpc((u,r,i)=>u.listTaskPushNotificationConfig(r,we.emptyOptions,i),t)}async deleteTaskPushNotificationConfig(t){return await this.invokeJsonRpc((u,r,i)=>u.deleteTaskPushNotificationConfig(r,we.emptyOptions,i),t)}async getTask(t){return await this.invokeJsonRpc((u,r,i)=>u.getTask(r,we.emptyOptions,i),t)}async cancelTask(t){return await this.invokeJsonRpc((u,r,i)=>u.cancelTask(r,we.emptyOptions,i),t)}async callExtensionMethod(t,u){const r=await this._getOrCreateTransport();try{return await r.callExtensionMethod(t,u,this.requestIdCounter++)}catch(i){const s=Wi(i);if(s)return s;throw i}}async*resubscribeTask(t){if(!(await this.agentCardPromise).capabilities?.streaming)throw new Error("Agent does not support streaming (required for tasks/resubscribe).");yield*(await this._getOrCreateTransport()).resubscribeTask(t)}async _getOrCreateTransport(){if(this.transport)return this.transport;const t=await this._getServiceEndpoint();return this.transport=new L0({fetchImpl:this.customFetchImpl,endpoint:t}),this.transport}async _fetchAndCacheAgentCard(t,u){try{const r=this.resolveAgentCardUrl(t,u),i=await this._fetch(r,{headers:{Accept:"application/json"}});if(!i.ok)throw new Error(`Failed to fetch Agent Card from ${r}: ${i.status} ${i.statusText}`);const s=await i.json();if(!s.url)throw new Error("Fetched Agent Card does not contain a valid 'url' for the service endpoint.");return this.serviceEndpointUrl=s.url,s}catch(r){throw console.error("Error fetching or parsing Agent Card:",r),r}}async getAgentCard(t,u){if(t){const r=this.resolveAgentCardUrl(t,u),i=await this._fetch(r,{headers:{Accept:"application/json"}});if(!i.ok)throw new Error(`Failed to fetch Agent Card from ${r}: ${i.status} ${i.statusText}`);return await i.json()}return this.agentCardPromise}resolveAgentCardUrl(t,u=I0){return`${t.replace(/\/$/,"")}/${u.replace(/^\//,"")}`}async _getServiceEndpoint(){if(this.serviceEndpointUrl)return this.serviceEndpointUrl;if(await this.agentCardPromise,!this.serviceEndpointUrl)throw new Error("Agent Card URL for RPC endpoint is not available. Fetching might have failed.");return this.serviceEndpointUrl}async invokeJsonRpc(t,u){const r=await this._getOrCreateTransport(),i=this.requestIdCounter++;try{const s=await t(r,u,i);return{id:i,jsonrpc:"2.0",result:s??null}}catch(s){const n=Wi(s);if(n)return n;throw s}}};function Wi(e){if(e instanceof Object&&"errorResponse"in e&&e.errorResponse instanceof Object&&"jsonrpc"in e.errorResponse&&e.errorResponse.jsonrpc==="2.0"&&"error"in e.errorResponse&&e.errorResponse.error!==null)return e.errorResponse}const Ji="application/json+a2ui";class Zi{#e;#u=null;constructor(t=""){this.#e=t}#r=Promise.resolve();get ready(){return this.#r}async#t(){if(!this.#u){const t=this.#e||window.location.origin;console.log("[A2UI] Initializing A2AClient with baseUrl:",t),this.#u=await G0.fromCardUrl(`${t}/.well-known/agent-card.json?t=${Date.now()}`,{fetchImpl:async(u,r)=>{console.log(`[A2UI] Fetching: ${u}`,r);const i=new Headers(r?.headers);i.set("X-A2A-Extensions","https://a2ui.org/a2a-extension/a2ui/v0.8");try{const s=await fetch(u,{...r,headers:i});return console.log(`[A2UI] Fetch success: ${u} -> ${s.status}`),s}catch(s){throw console.error(`[A2UI] Fetch failed: ${u}`,s),s}}})}return this.#u}async send(t){const u=await this.#t();console.log("[A2UI] Preparing to send message content:",t);let r=[];if(typeof t=="string")try{const n=JSON.parse(t);typeof n=="object"&&n!==null?r=[{kind:"data",data:n,mimeType:Ji}]:r=[{kind:"text",text:t}]}catch{const n="---a2ui_JSON---";if(t.includes(n)){const[a,c]=t.split(n);if(a.trim()&&r.push({kind:"text",text:a.trim()}),c.trim())try{const l=JSON.parse(c.trim());r.push({kind:"data",data:l})}catch(l){console.error("[A2UI] Failed to parse A2UI JSON part:",l),r.push({kind:"text",text:`[A2UI Parse Error] ${c.trim()}`})}}else r=[{kind:"text",text:t}]}else r=[{kind:"data",data:t,mimeType:Ji}];const i=await u.sendMessage({message:{messageId:crypto.randomUUID(),role:"user",parts:r,kind:"message"}});if("error"in i)throw console.error("[A2UI] Response error:",i.error),new Error(i.error.message);console.log("[A2UI] Start processing result:",i);const s=i.result;if(s.kind==="task"&&s.status.message?.parts){const n=[];for(const a of s.status.message.parts)if(a.kind==="data")n.push(a.data);else if(a.kind==="text"){const c="---a2ui_JSON---";if(a.text.includes(c)){const[l,d]=a.text.split(c);if(l.trim()){const o=`text-${crypto.randomUUID()}`,h=`surface-${crypto.randomUUID()}`;n.push({beginRendering:{surfaceId:h,root:o}}),n.push({surfaceUpdate:{surfaceId:h,components:[{id:o,component:{Text:{text:{literalString:l.trim()}}}}]}})}if(d.trim())try{const o=JSON.parse(d.trim());Array.isArray(o)?n.push(...o):(console.warn("[A2UI] Parsed JSON is not an array, treating as single message:",o),n.push(o))}catch(o){console.error("[A2UI] Failed to parse A2UI JSON from agent response:",o)}}else{const l=`text-${crypto.randomUUID()}`,d=`surface-${crypto.randomUUID()}`;n.push({beginRendering:{surfaceId:d,root:l}}),n.push({surfaceUpdate:{surfaceId:d,components:[{id:l,component:{Text:{text:{literalString:a.text}}}}]}})}}return n}return[]}}var Ft=(e=>(e.NONE="none",e.INFORMATION="information",e.WARNING="warning",e.ERROR="error",e.PENDING="pending",e))(Ft||{});const K0={bubbles:!0,cancelable:!0,composed:!0};class du extends Event{constructor(t,u,r){super(du.eventName,{...K0}),this.action=t,this.value=u,this.callback=r}static{this.eventName="snackbaraction"}}var Q0=Object.create,jr=Object.defineProperty,Y0=Object.getOwnPropertyDescriptor,cn=(e,t)=>(t=Symbol[e])?t:Symbol.for("Symbol."+e),ht=e=>{throw TypeError(e)},X0=(e,t,u)=>t in e?jr(e,t,{enumerable:!0,configurable:!0,writable:!0,value:u}):e[t]=u,Gi=(e,t)=>jr(e,"name",{value:t,configurable:!0}),ed=e=>[,,,Q0(e?.[cn("metadata")]??null)],ln=["class","method","getter","setter","accessor","field","value","get","set"],$t=e=>e!==void 0&&typeof e!="function"?ht("Function expected"):e,td=(e,t,u,r,i)=>({kind:ln[e],name:t,metadata:r,addInitializer:s=>u._?ht("Already initialized"):i.push($t(s||null))}),ud=(e,t)=>X0(t,cn("metadata"),e[3]),Ue=(e,t,u,r)=>{for(var i=0,s=e[t>>1],n=s&&s.length;i<n;i++)t&1?s[i].call(u):r=s[i].call(u,r);return r},wu=(e,t,u,r,i,s)=>{var n,a,c,l,d,o=t&7,h=!!(t&8),p=!!(t&16),f=o>3?e.length+1:o?h?1:2:0,b=ln[o+5],m=o>3&&(e[f-1]=[]),g=e[f]||(e[f]=[]),v=o&&(!p&&!h&&(i=i.prototype),o<5&&(o>3||!p)&&Y0(o<4?i:{get[u](){return U(this,s)},set[u](y){return dr(this,s,y)}},u));o?p&&o<4&&Gi(s,(o>2?"set ":o>1?"get ":"")+u):Gi(i,u);for(var w=r.length-1;w>=0;w--)l=td(o,u,c={},e[3],g),o&&(l.static=h,l.private=p,d=l.access={has:p?y=>rd(i,y):y=>u in y},o^3&&(d.get=p?y=>(o^1?U:id)(y,i,o^4?s:v.get):y=>y[u]),o>2&&(d.set=p?(y,x)=>dr(y,i,x,o^4?s:v.set):(y,x)=>y[u]=x)),a=(0,r[w])(o?o<4?p?s:v[b]:o>4?void 0:{get:v.get,set:v.set}:i,l),c._=1,o^4||a===void 0?$t(a)&&(o>4?m.unshift(a):o?p?s=a:v[b]=a:i=a):typeof a!="object"||a===null?ht("Object expected"):($t(n=a.get)&&(v.get=n),$t(n=a.set)&&(v.set=n),$t(n=a.init)&&m.unshift(n));return o||ud(e,i),v&&jr(i,u,v),p?o^4?s:v:i},Lr=(e,t,u)=>t.has(e)||ht("Cannot "+u),rd=(e,t)=>Object(t)!==t?ht('Cannot use the "in" operator on this value'):e.has(t),U=(e,t,u)=>(Lr(e,t,"read from private field"),u?u.call(e):t.get(e)),Ct=(e,t,u)=>t.has(e)?ht("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,u),dr=(e,t,u,r)=>(Lr(e,t,"write to private field"),r?r.call(e,u):t.set(e,u),u),id=(e,t,u)=>(Lr(e,t,"access private method"),u),dn,fn,hn,fr,pn,oe,Ur,Br,qr,W,eu;const sd=8e3;pn=[j("ui-snackbar")];class We extends(fr=He,hn=[A({reflect:!0,type:Boolean})],fn=[A({reflect:!0,type:Boolean})],dn=[A()],fr){constructor(){super(...arguments),Ct(this,Ur,Ue(oe,8,this,!1)),Ue(oe,11,this),Ct(this,Br,Ue(oe,12,this,!1)),Ue(oe,15,this),Ct(this,qr,Ue(oe,16,this,sd)),Ue(oe,19,this),Ct(this,W,[]),Ct(this,eu,0)}show(t,u=!1){const r=U(this,W).findIndex(i=>i.id===t.id);return r===-1?(u&&(U(this,W).length=0),U(this,W).push(t)):U(this,W)[r]=t,window.clearTimeout(U(this,eu)),U(this,W).every(i=>i.persistent)||dr(this,eu,window.setTimeout(()=>{this.hide()},this.timeout)),this.error=U(this,W).some(i=>i.type===Ft.ERROR),this.active=!0,this.requestUpdate(),t.id}hide(t){if(t){const u=U(this,W).findIndex(r=>r.id===t);u!==-1&&U(this,W).splice(u,1)}else U(this,W).length=0;this.active=U(this,W).length!==0,this.updateComplete.then(u=>{u&&this.requestUpdate()})}render(){let t=!1,u="";for(let r=U(this,W).length-1;r>=0;r--)if(!(!U(this,W)[r].type||U(this,W)[r].type===Ft.NONE)){u=U(this,W)[r].type,U(this,W)[r].type===Ft.PENDING&&(u="progress_activity",t=!0);break}return k` ${u?k`<span
            class=${T({"g-icon":!0,round:!0,filled:!0,rotate:t})}
            >${u}</span
          >`:$}
      <div id="messages">
        ${Yt(U(this,W),r=>r.id,r=>k`<div>${r.message}</div>`)}
      </div>
      <div id="actions">
        ${Yt(U(this,W),r=>r.id,r=>r.actions?k`${Yt(r.actions,i=>i.value,i=>k`<button
                  @click=${()=>{this.hide(),this.dispatchEvent(new du(i.action,i.value,i.callback))}}
                >
                  ${i.title}
                </button>`)}`:$)}
      </div>
      <button
        id="close"
        @click=${()=>{this.hide(),this.dispatchEvent(new du("dismiss"))}}
      >
        <span class="g-icon">close</span>
      </button>`}}oe=ed(fr);Ur=new WeakMap;Br=new WeakMap;qr=new WeakMap;W=new WeakMap;eu=new WeakMap;wu(oe,4,"active",hn,We,Ur);wu(oe,4,"error",fn,We,Br);wu(oe,4,"timeout",dn,We,qr);We=wu(oe,0,"Snackbar",pn,We);We.styles=[mu(Dr),M`
      :host {
        --text-color: var(--n-0);
        --bb-body-medium: 16px;
        --bb-body-line-height-medium: 24px;

        display: flex;
        align-items: center;
        position: fixed;
        bottom: var(--bb-grid-size-7);
        left: 50%;
        translate: -50% 0;
        opacity: 0;
        pointer-events: none;
        border-radius: var(--bb-grid-size-2);
        background: var(--n-90);
        padding: var(--bb-grid-size-3) var(--bb-grid-size-6);
        width: 60svw;
        max-width: 720px;
        z-index: 1800;
        scrollbar-width: none;
        overflow-x: scroll;
        font: 400 var(--bb-body-medium) / var(--bb-body-line-height-medium)
          var(--bb-font-family);
      }

      :host([active]) {
        transition: opacity 0.3s cubic-bezier(0, 0, 0.3, 1) 0.2s;
        opacity: 1;
        pointer-events: auto;
      }

      :host([error]) {
        background: var(--e-90);
        --text-color: var(--e-40);
      }

      .g-icon {
        flex: 0 0 auto;
        color: var(--text-color);
        margin-right: var(--bb-grid-size-4);

        &.rotate {
          animation: 1s linear 0s infinite normal forwards running rotate;
        }
      }

      #messages {
        color: var(--text-color);
        flex: 1 1 auto;
        margin-right: var(--bb-grid-size-11);

        a,
        a:visited {
          color: var(--bb-ui-600);
          text-decoration: none;

          &:hover {
            color: var(--bb-ui-500);
            text-decoration: underline;
          }
        }
      }

      #actions {
        flex: 0 1 auto;
        width: fit-content;
        margin-right: var(--bb-grid-size-3);

        & button {
          font: 500 var(--bb-body-medium) / var(--bb-body-line-height-medium)
            var(--bb-font-family);
          padding: 0;
          background: transparent;
          border: none;
          margin: 0 var(--bb-grid-size-4);
          color: var(--text-color);
          opacity: 0.7;
          transition: opacity 0.2s cubic-bezier(0, 0, 0.3, 1);

          &:not([disabled]) {
            cursor: pointer;

            &:hover,
            &:focus {
              opacity: 1;
            }
          }
        }
      }

      #close {
        display: flex;
        align-items: center;
        padding: 0;
        color: var(--text-color);
        background: transparent;
        border: none;
        margin: 0 0 0 var(--bb-grid-size-2);
        opacity: 0.7;
        transition: opacity 0.2s cubic-bezier(0, 0, 0.3, 1);

        .g-icon {
          margin-right: 0;
        }

        &:not([disabled]) {
          cursor: pointer;

          &:hover,
          &:focus {
            opacity: 1;
          }
        }
      }

      @keyframes rotate {
        from {
          rotate: 0deg;
        }

        to {
          rotate: 360deg;
        }
      }
    `];Ue(oe,1,We);const nd={key:"restaurant",title:"Restaurant Finder",heroImage:"/hero.png",heroImageDark:"/hero-dark.png",background:`radial-gradient(
    at 0% 0%,
    light-dark(rgba(161, 196, 253, 0.3), rgba(6, 182, 212, 0.15)) 0px,
    transparent 50%
  ),
  radial-gradient(
    at 100% 0%,
    light-dark(rgba(255, 226, 226, 0.3), rgba(59, 130, 246, 0.15)) 0px,
    transparent 50%
  ),
  radial-gradient(
    at 100% 100%,
    light-dark(rgba(162, 210, 255, 0.3), rgba(20, 184, 166, 0.15)) 0px,
    transparent 50%
  ),
  radial-gradient(
    at 0% 100%,
    light-dark(rgba(255, 200, 221, 0.3), rgba(99, 102, 241, 0.15)) 0px,
    transparent 50%
  ),
  linear-gradient(
    120deg,
    light-dark(#f0f4f8, #0f172a) 0%,
    light-dark(#e2e8f0, #1e293b) 100%
  )`,placeholder:"Top 5 Chinese restaurants in New York.",loadingText:["Finding the best spots for you...","Checking reviews...","Looking for open tables...","Almost there..."],serverUrl:"http://localhost:10002"};function ad(){return structuredClone(Mr)}const od={...ad(),additionalStyles:{Card:{"min-width":"320px","max-width":"400px",margin:"0 auto",background:"linear-gradient(135deg, light-dark(#ffffff99, #ffffff44) 0%, light-dark(#ffffff, #ffffff04) 100%)",border:"1px solid light-dark(transparent, #ffffff35)",boxShadow:"inset 0 20px 48px light-dark(rgba(0, 0, 0, 0.02), rgba(255, 255, 255, 0.08))"},Button:{"--p-70":"light-dark(var(--p-60), var(--n-10))","--n-60":"light-dark(var(--n-100), var(--n-0))"},Image:{"max-width":"120px","max-height":"120px",marginLeft:"auto",marginRight:"auto"},Text:{"--n-40":"light-dark(var(--p-60), var(--n-90))"}},components:{AudioPlayer:{},Button:{"layout-pt-2":!0,"layout-pb-2":!0,"layout-pl-5":!0,"layout-pr-5":!0,"border-br-2":!0,"border-bw-0":!0,"border-bs-s":!0,"color-bgc-p30":!0,"color-c-n100":!0,"behavior-ho-70":!0},Card:{"border-br-4":!0,"color-bgc-p100":!0,"layout-pt-10":!0,"layout-pb-10":!0,"layout-pl-4":!0,"layout-pr-4":!0},CheckBox:{element:{"layout-m-0":!0,"layout-mr-2":!0,"layout-p-2":!0,"border-br-12":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bgc-p100":!0,"color-bc-p60":!0,"color-c-n30":!0,"color-c-p30":!0},label:{"color-c-p30":!0,"typography-f-sf":!0,"typography-v-r":!0,"typography-w-400":!0,"layout-flx-1":!0,"typography-sz-ll":!0},container:{"layout-dsp-iflex":!0,"layout-al-c":!0}},Column:{},DateTimeInput:{container:{},label:{},element:{"layout-pt-2":!0,"layout-pb-2":!0,"layout-pl-3":!0,"layout-pr-3":!0,"border-br-12":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bgc-p100":!0,"color-bc-p60":!0,"color-c-n30":!0}},Divider:{"color-bgc-n90":!0,"layout-mt-6":!0,"layout-mb-6":!0},Image:{all:{"border-br-50pc":!0,"layout-el-cv":!0,"layout-w-100":!0,"layout-h-100":!0,"layout-dsp-flexhor":!0,"layout-al-c":!0,"layout-sp-c":!0,"layout-mb-3":!0},avatar:{},header:{},icon:{},largeFeature:{},mediumFeature:{},smallFeature:{}},Icon:{"border-br-1":!0,"layout-p-2":!0,"color-bgc-n98":!0,"layout-dsp-flexhor":!0,"layout-al-c":!0,"layout-sp-c":!0},List:{"layout-g-4":!0,"layout-p-2":!0},Modal:{backdrop:{"color-bbgc-p60_20":!0},element:{"border-br-2":!0,"color-bgc-p100":!0,"layout-p-4":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bc-p80":!0}},MultipleChoice:{container:{},label:{},element:{}},Row:{"layout-g-4":!0,"layout-mb-3":!0},Slider:{container:{},label:{},element:{}},Tabs:{container:{},controls:{all:{},selected:{}},element:{}},Text:{all:{"layout-w-100":!0,"layout-g-2":!0,"color-c-p30":!0},h1:{"typography-f-sf":!0,"typography-ta-c":!0,"typography-v-r":!0,"typography-w-500":!0,"layout-mt-0":!0,"layout-mr-0":!0,"layout-ml-0":!0,"layout-mb-2":!0,"layout-p-0":!0,"typography-sz-tl":!0},h2:{"typography-f-sf":!0,"typography-ta-c":!0,"typography-v-r":!0,"typography-w-500":!0,"layout-mt-0":!0,"layout-mr-0":!0,"layout-ml-0":!0,"layout-mb-2":!0,"layout-p-0":!0,"typography-sz-tl":!0},h3:{"typography-f-sf":!0,"typography-ta-c":!0,"typography-v-r":!0,"typography-w-500":!0,"layout-mt-0":!0,"layout-mr-0":!0,"layout-ml-0":!0,"layout-mb-0":!0,"layout-p-0":!0,"typography-sz-ts":!0},h4:{"typography-f-sf":!0,"typography-ta-c":!0,"typography-v-r":!0,"typography-w-500":!0,"layout-mt-0":!0,"layout-mr-0":!0,"layout-ml-0":!0,"layout-mb-0":!0,"layout-p-0":!0,"typography-sz-bl":!0},h5:{"typography-f-sf":!0,"typography-ta-c":!0,"typography-v-r":!0,"typography-w-500":!0,"layout-mt-0":!0,"layout-mr-0":!0,"layout-ml-0":!0,"layout-mb-0":!0,"layout-p-0":!0,"color-c-n30":!0,"typography-sz-bm":!0,"layout-mb-1":!0},body:{},caption:{}},TextField:{container:{"typography-sz-bm":!0,"layout-w-100":!0,"layout-g-2":!0,"layout-dsp-flexhor":!0,"layout-al-c":!0},label:{"layout-flx-0":!0},element:{"typography-sz-bm":!0,"layout-pt-2":!0,"layout-pb-2":!0,"layout-pl-3":!0,"layout-pr-3":!0,"border-br-12":!0,"border-bw-1":!0,"border-bs-s":!0,"color-bgc-p100":!0,"color-bc-p60":!0,"color-c-n30":!0,"color-c-p30":!0}},Video:{"border-br-5":!0,"layout-el-cv":!0}}},cd={key:"contacts",title:"Contact Manager",background:`radial-gradient(at 0% 0%, light-dark(rgba(45, 212, 191, 0.4), rgba(20, 184, 166, 0.2)) 0px, transparent 50%),
     radial-gradient(at 100% 0%, light-dark(rgba(56, 189, 248, 0.4), rgba(14, 165, 233, 0.2)) 0px, transparent 50%),
     radial-gradient(at 100% 100%, light-dark(rgba(163, 230, 53, 0.4), rgba(132, 204, 22, 0.2)) 0px, transparent 50%),
     radial-gradient(at 0% 100%, light-dark(rgba(52, 211, 153, 0.4), rgba(16, 185, 129, 0.2)) 0px, transparent 50%),
     linear-gradient(120deg, light-dark(#f0fdf4, #022c22) 0%, light-dark(#dcfce7, #064e3b) 100%)`,placeholder:"Alex Jordan",loadingText:["Searching contacts...","Looking up details...","Verifying information...","Just a moment..."],serverUrl:"http://localhost:10003",theme:od},ld={key:"phoneplan",title:"Corporate Phone Plan Shopper",placeholder:"e.g. I need a plan with international calling and a Pixel 9",theme:Mr,loadingText:["Checking plan eligibility...","Searching for devices...","Reviewing pricing..."]};var dd=Object.create,Hr=Object.defineProperty,fd=Object.getOwnPropertyDescriptor,bn=(e,t)=>(t=Symbol[e])?t:Symbol.for("Symbol."+e),pt=e=>{throw TypeError(e)},hd=(e,t,u)=>t in e?Hr(e,t,{enumerable:!0,configurable:!0,writable:!0,value:u}):e[t]=u,Ki=(e,t)=>Hr(e,"name",{value:t,configurable:!0}),pd=e=>[,,,dd(e?.[bn("metadata")]??null)],mn=["class","method","getter","setter","accessor","field","value","get","set"],Et=e=>e!==void 0&&typeof e!="function"?pt("Function expected"):e,bd=(e,t,u,r,i)=>({kind:mn[e],name:t,metadata:r,addInitializer:s=>u._?pt("Already initialized"):i.push(Et(s||null))}),md=(e,t)=>hd(t,bn("metadata"),e[3]),X=(e,t,u,r)=>{for(var i=0,s=e[t>>1],n=s&&s.length;i<n;i++)t&1?s[i].call(u):r=s[i].call(u,r);return r},Oe=(e,t,u,r,i,s)=>{var n,a,c,l,d,o=t&7,h=!!(t&8),p=!!(t&16),f=o>3?e.length+1:o?h?1:2:0,b=mn[o+5],m=o>3&&(e[f-1]=[]),g=e[f]||(e[f]=[]),v=o&&(!p&&!h&&(i=i.prototype),o<5&&(o>3||!p)&&fd(o<4?i:{get[u](){return I(this,s)},set[u](y){return ce(this,s,y)}},u));o?p&&o<4&&Ki(s,(o>2?"set ":o>1?"get ":"")+u):Ki(i,u);for(var w=r.length-1;w>=0;w--)l=bd(o,u,c={},e[3],g),o&&(l.static=h,l.private=p,d=l.access={has:p?y=>gd(i,y):y=>u in y},o^3&&(d.get=p?y=>(o^1?I:ue)(y,i,o^4?s:v.get):y=>y[u]),o>2&&(d.set=p?(y,x)=>ce(y,i,x,o^4?s:v.set):(y,x)=>y[u]=x)),a=(0,r[w])(o?o<4?p?s:v[b]:o>4?void 0:{get:v.get,set:v.set}:i,l),c._=1,o^4||a===void 0?Et(a)&&(o>4?m.unshift(a):o?p?s=a:v[b]=a:i=a):typeof a!="object"||a===null?pt("Object expected"):(Et(n=a.get)&&(v.get=n),Et(n=a.set)&&(v.set=n),Et(n=a.init)&&m.unshift(n));return o||md(e,i),v&&Hr(i,u,v),p?o^4?s:v:i},Vr=(e,t,u)=>t.has(e)||pt("Cannot "+u),gd=(e,t)=>Object(t)!==t?pt('Cannot use the "in" operator on this value'):e.has(t),I=(e,t,u)=>(Vr(e,t,"read from private field"),u?u.call(e):t.get(e)),ie=(e,t,u)=>t.has(e)?pt("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,u),ce=(e,t,u,r)=>(Vr(e,t,"write to private field"),r?r.call(e,u):t.set(e,u),u),ue=(e,t,u)=>(Vr(e,t,"access private method"),u),gn,_n,yn,xn,vn,wn,kn,hr,Cn,z,Wr,Jr,Qu,ut,tu,S,Zr,Yu,pr,Gr,Xu,$n,Kr,Qr,er,Yr,br,rt,ke,fu,Xe,mr,En,An,Dn,Sn,gr,Fn,Xr,tr,Nt,_r,Tn,In,On,Pn,ei;const ur={restaurant:nd,contacts:cd,phoneplan:ld};Cn=[j("a2ui-shell")];class ot extends(hr=us(He),kn=[Aa({context:ds})],wn=[Le()],vn=[Le()],xn=[Le()],yn=[Le()],_n=[Le()],gn=[Le()],hr){constructor(){super(...arguments),ie(this,S),ie(this,Wr,X(z,8,this,Mr)),X(z,11,this),ie(this,Jr,X(z,12,this,!1)),X(z,15,this),ie(this,Zr,X(z,16,this,null)),X(z,19,this),ie(this,Gr,X(z,20,this,[])),X(z,23,this),ie(this,Kr,X(z,24,this,ur.restaurant)),X(z,27,this),ie(this,Qr,X(z,28,this,0)),X(z,31,this),ie(this,rt),ie(this,ke,_o.createSignalA2uiMessageProcessor()),ie(this,fu,new Zi),ie(this,Xe),ie(this,mr,[]),ie(this,Xr,X(z,32,this,[])),X(z,35,this)}connectedCallback(){super.connectedCallback();const u=new URLSearchParams(window.location.search).get("app")||"phoneplan";this.config=ur[u]||ur.phoneplan,this.config.theme&&(this.theme=this.config.theme),window.document.title=this.config.title,window.document.documentElement.style.setProperty("--background",this.config.background),ce(this,fu,new Zi(this.config.serverUrl))}render(){return[ue(this,S,An).call(this),ue(this,S,Dn).call(this),ue(this,S,Tn).call(this),ue(this,S,En).call(this)]}snackbar(t,u,r=[],i=!1,s=globalThis.crypto.randomUUID(),n=!1){if(!I(this,Xe)){I(this,mr).push({message:{id:s,message:t,type:u,persistent:i,actions:r},replaceAll:n});return}return I(this,Xe).show({id:s,message:t,type:u,persistent:i,actions:r},n)}unsnackbar(t){I(this,Xe)&&I(this,Xe).hide(t)}}z=pd(hr);Wr=new WeakMap;Jr=new WeakMap;S=new WeakSet;Zr=new WeakMap;Gr=new WeakMap;Kr=new WeakMap;Qr=new WeakMap;rt=new WeakMap;ke=new WeakMap;fu=new WeakMap;Xe=new WeakMap;mr=new WeakMap;En=function(){return I(this,S,pr)?k`<div class="error">${I(this,S,pr)}</div>`:$};An=function(){return k` <div>
      <button
        @click=${e=>{if(!(e.target instanceof HTMLButtonElement))return;const{colorScheme:t}=window.getComputedStyle(e.target);t==="dark"?(document.body.classList.add("light"),document.body.classList.remove("dark")):(document.body.classList.add("dark"),document.body.classList.remove("light"))}}
        class="theme-toggle"
      >
        <span class="g-icon filled-heavy"></span>
      </button>
    </div>`};Dn=function(){return I(this,S,ut)||I(this,S,$n).length>0?$:k` <form
      @submit=${async e=>{if(e.preventDefault(),!(e.target instanceof HTMLFormElement))return;const u=new FormData(e.target).get("body")??null;if(!u)return;const r=u;console.log("[A2UI] Sending message:",r);try{await ue(this,S,ei).call(this,r)}catch(i){console.error("[A2UI] Send failed:",i)}}}
    >
      ${this.config.heroImage?k`<div
            style=${q({"--background-image-light":`url(${this.config.heroImage})`,"--background-image-dark":`url(${this.config.heroImageDark??this.config.heroImage})`})}
            id="hero-img"
          ></div>`:$}
      <h1 class="app-title">${this.config.title}</h1>
      <div>
        <input
          required
          placeholder="${this.config.placeholder}"
          autocomplete="off"
          id="body"
          name="body"
          type="text"
          ?disabled=${I(this,S,ut)}
        />
        <button type="submit" ?disabled=${I(this,S,ut)}>
          <span class="g-icon filled-heavy">send</span>
        </button>
      </div>
    </form>`};Sn=function(){Array.isArray(this.config.loadingText)&&this.config.loadingText.length>1&&(ce(this,S,0,br),ce(this,rt,window.setInterval(()=>{ce(this,S,(I(this,S,Yr)+1)%this.config.loadingText.length,br)},2e3)))};gr=function(){I(this,rt)&&(clearInterval(I(this,rt)),ce(this,rt,void 0))};Fn=async function(e){try{ce(this,S,!0,tu),ue(this,S,Sn).call(this);const t=I(this,fu).send(e);return await t,ce(this,S,!1,tu),ue(this,S,gr).call(this),t}catch(t){this.snackbar(t,Ft.ERROR)}finally{ce(this,S,!1,tu),ue(this,S,gr).call(this)}return[]};Xr=new WeakMap;Tn=function(){return I(this,S,Nt).length===0&&!I(this,S,ut)?$:k`<section id="chat-history" style="display: flex; flex-direction: column; gap: 16px; padding-bottom: 80px;">
      ${I(this,S,Nt).map(e=>ue(this,S,In).call(this,e))}
      ${I(this,S,ut)?ue(this,S,On).call(this):$}
    </section>`};In=function(e){const t=e.role==="user",u=t?"align-self: flex-end; background: var(--p-90); color: var(--on-p-90);":"align-self: flex-start; background: transparent;",r=t?"16px 16px 0 16px":"16px 16px 16px 0";return k`
      <div class="turn ${e.role}" style="
        max-width: 80%;
        padding: 12px 16px;
        border-radius: ${r};
        ${u}
        animation: fadeIn 0.3s ease-out;
      ">
        ${e.text?k`<div class="text-content" style="white-space: pre-wrap;">${e.text}</div>`:$}
        ${e.surfaces?k`<div class="surfaces-content" style="margin-top: 8px;">
          ${e.surfaces.map(i=>{const s=I(this,ke).getSurfaces().get(i);return s?k`<a2ui-surface
              .surfaceId=${i}
              .surface=${s}
              .processor=${I(this,ke)}
              @a2uiaction=${ue(this,S,Pn)}
            ></a2ui-surface>`:$})}
        </div>`:$}
      </div>
    `};On=function(){let e="Thinking...";return this.config.loadingText&&(e=Array.isArray(this.config.loadingText)?this.config.loadingText[I(this,S,Yr)]:this.config.loadingText),k`
      <div class="turn model requesting" style="align-self: flex-start; opacity: 0.7; padding: 12px;">
        <div class="spinner" style="width: 24px; height: 24px; border-width: 2px;"></div>
        <span style="margin-left: 8px;">${e}</span>
      </div>
    `};Pn=async function(e){const[t]=e.composedPath();if(!(t instanceof HTMLElement))return;const u={};if(e.detail.action.context){for(const s of e.detail.action.context)if(s.value.literalBoolean!==void 0)u[s.key]=s.value.literalBoolean;else if(s.value.literalNumber!==void 0)u[s.key]=s.value.literalNumber;else if(s.value.literalString!==void 0)u[s.key]=s.value.literalString;else if(s.value.path){const n=I(this,ke).resolvePath(s.value.path,e.detail.dataContextPath),a=I(this,ke).getData(e.detail.sourceComponent,n,e.detail.surfaceId);u[s.key]=a}}const r={userAction:{name:e.detail.action.name,surfaceId:e.detail.surfaceId,sourceComponentId:t.id,timestamp:new Date().toISOString(),context:u}};let i=`Action: ${e.detail.action.name}`;u.selection?i=String(u.selection):u.displayText?i=String(u.displayText):u.value&&(i=String(u.value)),await ue(this,S,ei).call(this,r,i)};ei=async function(e,t){t||e.userAction&&`${e.userAction.sourceComponentId}`;let u=t;!u&&typeof e=="object"&&e!==null&&"message"in e&&e.message,typeof e=="string"&&(u=u||e,ce(this,S,[...I(this,S,Nt),{id:crypto.randomUUID(),role:"user",text:e,timestamp:Date.now()}],_r));const r=await ue(this,S,Fn).call(this,e);console.log("Processed messages:",r.length);const i=new Set(I(this,ke).getSurfaces().keys());I(this,ke).processMessages(r),Array.from(I(this,ke).getSurfaces().keys()).filter(a=>!i.has(a)||!0);const n=new Set;for(const a of r)"surfaceUpdate"in a&&n.add(a.surfaceUpdate.surfaceId),"beginRendering"in a&&n.add(a.beginRendering.surfaceId);n.size>0&&ce(this,S,[...I(this,S,Nt),{id:crypto.randomUUID(),role:"model",surfaces:Array.from(n),timestamp:Date.now()}],_r),this.requestUpdate(),setTimeout(()=>{const a=this.shadowRoot?.getElementById("chat-history");a&&a.lastElementChild?.scrollIntoView({behavior:"smooth"})},100)};Oe(z,4,"theme",kn,ot,Wr);Qu=Oe(z,20,"#requesting",wn,S,Jr),ut=Qu.get,tu=Qu.set;Yu=Oe(z,20,"#error",vn,S,Zr),pr=Yu.get,Yu.set;Xu=Oe(z,20,"#lastMessages",xn,S,Gr),$n=Xu.get,Xu.set;Oe(z,4,"config",yn,ot,Kr);er=Oe(z,20,"#loadingTextIndex",_n,S,Qr),Yr=er.get,br=er.set;tr=Oe(z,20,"#turns",gn,S,Xr),Nt=tr.get,_r=tr.set;ot=Oe(z,0,"A2UILayoutEditor",Cn,ot);ot.styles=[mu(Dr),M`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        max-width: 640px;
        margin: 0 auto;
        min-height: 100%;
        color: light-dark(var(--n-10), var(--n-90));
        font-family: var(--font-family);
      }

      #hero-img {
        width: 100%;
        max-width: 400px;
        aspect-ratio: 1280/720;
        height: auto;
        margin-bottom: var(--bb-grid-size-6);
        display: block;
        margin: 0 auto;
        background: var(--background-image-light) center center / contain
          no-repeat;
      }

      #surfaces {
        width: 100%;
        max-width: 100svw;
        padding: var(--bb-grid-size-3);
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
      }

      form {
        display: flex;
        flex-direction: column;
        flex: 1;
        gap: 16px;
        align-items: center;
        padding: 16px 0;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 1s backwards;

        & h1 {
          color: light-dark(var(--p-40), var(--n-90));
        }

        & > div {
          display: flex;
          flex: 1;
          gap: 16px;
          align-items: center;
          width: 100%;

          & > input {
            display: block;
            flex: 1;
            border-radius: 32px;
            padding: 16px 24px;
            border: 1px solid var(--p-60);
            background: light-dark(var(--n-100), var(--n-10));
            font-size: 16px;
          }

          & > button {
            display: flex;
            align-items: center;
            background: var(--p-40);
            color: var(--n-100);
            border: none;
            padding: 8px 16px;
            border-radius: 32px;
            opacity: 0.5;

            &:not([disabled]) {
              cursor: pointer;
              opacity: 1;
            }
          }
        }
      }

      .rotate {
        animation: rotate 1s linear infinite;
      }

      .pending {
        width: 100%;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
        gap: 16px;
      }

      .spinner {
        width: 48px;
        height: 48px;
        border: 4px solid rgba(255, 255, 255, 0.1);
        border-left-color: var(--p-60);
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      .theme-toggle {
        padding: 0;
        margin: 0;
        border: none;
        display: flex;
        align-items: center;
        justify-content: center;
        position: fixed;
        top: var(--bb-grid-size-3);
        right: var(--bb-grid-size-4);
        background: light-dark(var(--n-100), var(--n-0));
        border-radius: 50%;
        color: var(--p-30);
        cursor: pointer;
        width: 48px;
        height: 48px;
        font-size: 32px;

        & .g-icon {
          pointer-events: none;

          &::before {
            content: "dark_mode";
          }
        }
      }

      @container style(--color-scheme: dark) {
        .theme-toggle .g-icon::before {
          content: "light_mode";
          color: var(--n-90);
        }

        #hero-img {
          background-image: var(--background-image-dark);
        }
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      @keyframes pulse {
        0% {
          opacity: 0.6;
        }
        50% {
          opacity: 1;
        }
        100% {
          opacity: 0.6;
        }
      }

      .error {
        color: var(--e-40);
        background-color: var(--e-95);
        border: 1px solid var(--e-80);
        padding: 16px;
        border-radius: 8px;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }

        to {
          opacity: 1;
        }
      }

      @keyframes rotate {
        from {
          rotate: 0deg;
        }

        to {
          rotate: 360deg;
        }
      }
    `];X(z,1,ot);
