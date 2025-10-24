/* PSU AI Client — Expanded */

;(() => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const safeJSON = async (res) => { try { return await res.json(); } catch { return { ok:false, error:{message:"Bad JSON"} }; } };

  class LocalCache {
    constructor(prefix='psu-ai'){ this.prefix=prefix; }
    k(k){ return `${this.prefix}:${k}`; }
    set(k,v,ttl=600){ try{ localStorage.setItem(this.k(k), JSON.stringify({v,exp:Date.now()+ttl*1000})) }catch{} }
    get(k){ try{ const raw=localStorage.getItem(this.k(k)); if(!raw) return null; const p=JSON.parse(raw); if(Date.now()>p.exp){ localStorage.removeItem(this.k(k)); return null } return p.v }catch{ return null } }
  }

  async function fetchJSON(url, opts={}, {timeout=15000, retries=1, retryDelay=600}={}){
    const ctrl=new AbortController(); const t=setTimeout(()=>ctrl.abort(), timeout);
    try{
      const res=await fetch(url, {...opts, signal:ctrl.signal, headers:{"Content-Type":"application/json", ...(opts.headers||{})}});
      if(!res.ok && (res.status>=500 || res.status===429) && retries>0){ await sleep(retryDelay); return fetchJSON(url, opts, {timeout, retries:retries-1, retryDelay:retryDelay*2});}
      return res;
    } finally{ clearTimeout(t); }
  }

  const toastCSS = `
    .psu-toast-wrap{position:fixed;right:1rem;bottom:1rem;z-index:9999;display:flex;flex-direction:column;gap:.5rem}
    .psu-toast{background:#1a1a1a;color:#fff;border-radius:.75rem;padding:.75rem 1rem;box-shadow:0 8px 24px rgba(0,0,0,.2);display:flex;gap:.75rem;align-items:flex-start;max-width:420px;opacity:0;transform:translateY(8px);transition:opacity .2s ease,transform .2s ease}
    .psu-toast.show{opacity:1;transform:translateY(0)}
    .psu-toast .psu-dot{width:.65rem;height:.65rem;border-radius:50%;}
    .psu-toast.success .psu-dot{background:#22c55e}
    .psu-toast.info .psu-dot{background:#ffb81c}
    .psu-toast.error .psu-dot{background:#ef4444}
    .psu-toast .psu-msg{flex:1;font-size:.925rem;line-height:1.35}
    .psu-toast .psu-x{cursor:pointer;opacity:.8}
    .psu-btn-busy{position:relative;pointer-events:none;opacity:.8}
    .psu-btn-busy::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 50% 50%, rgba(255,255,255,.25), transparent 40%);animation:psu-pulse 1s infinite ease-in-out;border-radius:inherit;}
    @keyframes psu-pulse{0%,100%{opacity:.25}50%{opacity:.6}}
  `;
  const ensureToast = (()=>{ let done=false; return ()=>{ if(done) return; const s=document.createElement('style'); s.textContent=toastCSS; document.head.appendChild(s); const w=document.createElement('div'); w.className='psu-toast-wrap'; document.body.appendChild(w); done=true; };})();
  const toast=(msg,type='info',timeout=3500)=>{ ensureToast(); const w=document.querySelector('.psu-toast-wrap'); const el=document.createElement('div'); el.className=`psu-toast ${type}`; el.innerHTML=`<div class="psu-dot"></div><div class="psu-msg">${msg}</div><div class="psu-x">✖</div>`; w.appendChild(el); requestAnimationFrame(()=>el.classList.add('show')); const rm=()=>{el.classList.remove('show'); setTimeout(()=>el.remove(),200)}; el.querySelector('.psu-x').addEventListener('click',rm); if(timeout) setTimeout(rm,timeout); return rm; };

  function hashCode(str){ let h=0; for(let i=0;i<str.length;i++){ h=(h<<5)-h+str.charCodeAt(i); h|=0;} return (h>>>0).toString(16); }
  function escapeHtml(s){ return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;"); }

  class PSUAIClient {
    constructor(cfg={}) {
      this.base = cfg.base || "/api/ai";
      this.cache = new LocalCache(cfg.cachePrefix || "psu-ai");
      this.ttl = { summary:600, topics:900, match:1800, rewrite:900, insight:600, learn:1800, thread:600, resume:1200, essay:1200, donor:3600 };
      this.rateInfo={ last429At:0 };
      this._autoBind();
    }
    _busy(btn, b){ if(!btn) return; btn.disabled=!!b; btn.classList.toggle("psu-btn-busy", !!b); }
    async _call(path, {method="GET", body=null, cacheKey=null, ttl=0}={}){
      if(cacheKey && ttl>0){ const hit=this.cache.get(cacheKey); if(hit) return {ok:true, data:hit, meta:{cached:true}}; }
      let res; try{
        res=await fetchJSON(`${this.base}${path}`, body?{method, body:JSON.stringify(body)}:{method}, {timeout:15000, retries:1});
      }catch{ toast("Network error contacting AI.","error"); return {ok:false, error:{message:"network"}}; }
      const json=await safeJSON(res);
      if(!res.ok || json.ok===false){ if(res.status===429){ this.rateInfo.last429At=Date.now(); toast("Slow down a bit — rate limit.","error",4200);} else { toast(`AI: ${(json.error?.message)||"Error"}`,"error",4200); } return json; }
      if(cacheKey && ttl>0 && json.data) this.cache.set(cacheKey, json.data, ttl);
      return json;
    }

    // Endpoints
    health(){ return this._call("/health",{method:"GET", cacheKey:"health", ttl:60}); }
    summary({text}){ const k=`summary:${hashCode(text||"")}`; return this._call("/summary",{method:"POST", body:{text}, cacheKey:k, ttl:this.ttl.summary}); }
    topics({seed}){ const k=`topics:${hashCode(seed||"")}`; return this._call(`/topics?seed=${encodeURIComponent(seed||"")}`,{method:"GET", cacheKey:k, ttl:this.ttl.topics}); }
    match({interests, goals=[], persona=[]}){ const key=[...(interests||[]),...(goals||[]),...(persona||[])].join(","); const k=`match:${hashCode(key)}`; return this._call("/match",{method:"POST", body:{interests,goals,persona}, cacheKey:k, ttl:this.ttl.match}); }
    rewrite({text, tone}){ const k=`rewrite:${hashCode(text||"")}:${tone}`; return this._call("/rewrite",{method:"POST", body:{text,tone}, cacheKey:k, ttl:this.ttl.rewrite}); }
    insight(payload){ const k=`insight:${hashCode(JSON.stringify(payload||{}))}`; return this._call("/insight",{method:"POST", body:payload, cacheKey:k, ttl:this.ttl.insight}); }
    learningPath({goal}){ const k=`learn:${hashCode(goal||"")}`; return this._call("/learning-path",{method:"POST", body:{goal}, cacheKey:k, ttl:this.ttl.learn}); }
    threadSummary({text}){ const k=`thread:${hashCode(text||"")}`; return this._call("/thread/summary",{method:"POST", body:{text}, cacheKey:k, ttl:this.ttl.thread}); }
    resumeOptimize({resume, job_description}){ const k=`resume:${hashCode((resume||"")+":")}:${hashCode(job_description||"")}`; return this._call("/resume/optimize",{method:"POST", body:{resume, job_description}, cacheKey:k, ttl:this.ttl.resume}); }
    essayAnalyze({essay, criteria}){ const k=`essay:${hashCode((essay||"")+criteria||"")}`; return this._call("/essay/analyze",{method:"POST", body:{essay, criteria}, cacheKey:k, ttl:this.ttl.essay}); }
    donorStory(stats){ const k=`donor:${hashCode(JSON.stringify(stats||{}))}`; return this._call("/donor/story",{method:"POST", body:{stats}, cacheKey:k, ttl:this.ttl.donor}); }
    moderate({text, threshold=0.8}){ return this._call("/moderate",{method:"POST", body:{text, threshold}}); }

    // Auto-binding: existing IDs + new helper hooks
    _autoBind(){
      // Existing bindings (summary, match, topics) — unchanged
      const sumBtn=document.getElementById("aiSummaryBtn"); const sumOut=document.getElementById("aiSummaryText");
      if(sumBtn&&sumOut){ sumBtn.addEventListener("click", async()=>{ this._busy(sumBtn,true); const text=collectFeedText()||"Summarize campus sentiment."; const res=await this.summary({text}); this._busy(sumBtn,false); if(res.ok){ renderSummaryTo(sumOut, res.data.summary); sumOut.classList.remove("hidden"); colorizeSentiment(document, res.data.summary?.sentiment); toast("AI summary updated.","success",2200);} }); }
      const mBtn=document.getElementById("aiMatchBtn"); const mOut=document.getElementById("aiMatchResult");
      if(mBtn&&mOut){ mBtn.addEventListener("click", async()=>{ this._busy(mBtn,true); const interests=inferUserInterests(); const res=await this.match({interests}); this._busy(mBtn,false); if(res.ok){ const m=res.data.matches?.[0]; const expl=res.data.explanation||""; mOut.textContent= m? `${m.name} (${m.field}) — ${expl}` : "No mentor match available."; mOut.classList.remove("hidden"); toast("Mentor suggestions ready.","success",2200);} }); }
      const tBtn=document.getElementById("aiTopicBtn"); const tList=document.getElementById("aiTopics");
      if(tBtn&&tList){ tBtn.addEventListener("click", async()=>{ this._busy(tBtn,true); const res=await this.topics({seed:"internships, scholarships, campus life"}); this._busy(tBtn,false); if(res.ok){ tList.innerHTML=(res.data.topics||[]).map(t=>`<li>${escapeHtml(t)}</li>`).join(""); tList.classList.remove("hidden"); toast("AI suggestions added.","success",2200);} }); }
    }
  }

  // Helpers
  function collectFeedText(){ const cards=Array.from(document.querySelectorAll(".card")); const out=[]; for(const c of cards){ const p=c.querySelector("p"); if(p&&p.textContent) out.push(p.textContent.trim()); if(out.length>=10) break; } return out.join(" · ").slice(0,4000); }
  function inferUserInterests(){ const tags=Array.from(document.querySelectorAll("[data-interest]")).map(x=>x.getAttribute("data-interest")); return tags.length? tags.slice(0,6) : ["python","internships","data","resume","tableau"]; }

  // Render summary (bullets + takeaway)
  function renderSummaryTo(el, summary){
    if(!summary){ el.textContent="No summary."; return; }
    const bullets = summary.bullets || [];
    const takeaway = summary.takeaway || "";
    el.innerHTML = `
      <ul class="list-disc text-left pl-6 mb-2">${bullets.map(b=>`<li>${escapeHtml(b)}</li>`).join("")}</ul>
      <div class="text-sm"><em>${escapeHtml(takeaway)}</em></div>
    `;
  }

  // Sentiment colorization
  function colorizeSentiment(root, sentiment){
    root.querySelectorAll(".sentiment-tag").forEach(e=>e.remove());
    const badge=document.createElement("span");
    badge.className=`sentiment-tag inline-block px-2 py-0.5 rounded text-xs ml-2 ${sentimentClass(sentiment)}`;
    badge.textContent = `${sentiment||"neutral"}`;
    const h1=root.querySelector("h1, h2");
    if(h1) h1.appendChild(badge);

    // tint cards softly
    const tint = sentimentTint(sentiment);
    root.querySelectorAll(".card").forEach(c=>{ c.style.boxShadow="0 4px 12px rgba(0,0,0,0.05)"; c.style.backgroundColor=tint; });
  }
  function sentimentClass(s){
    if(s==="positive") return "bg-green-100 text-green-800";
    if(s==="negative") return "bg-red-100 text-red-800";
    return "bg-yellow-100 text-yellow-900";
  }
  function sentimentTint(s){
    if(s==="positive") return "rgba(16,185,129,0.06)"; // green-500 @ 6%
    if(s==="negative") return "rgba(220,38,38,0.06)";  // red-600
    return "rgba(234,179,8,0.06)";                     // amber-500
  }

  window.PSUAIClient = PSUAIClient;
  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",()=>{ window.psuAI=new PSUAIClient(); });
  } else { window.psuAI=new PSUAIClient(); }
})();
