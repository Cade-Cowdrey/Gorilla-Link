/* PSU Campus Copilot — Floating Panel */
;(() => {
  const panelCSS = `
    .psu-ai-panel{position:fixed;right:1rem;bottom:5rem;width:340px;max-width:90vw;background:#fff;border-radius:1rem;box-shadow:0 12px 40px rgba(0,0,0,.18);z-index:9998;overflow:hidden;border:1px solid rgba(0,0,0,.06)}
    .psu-ai-head{display:flex;align-items:center;gap:.5rem;padding:.6rem .8rem;background:linear-gradient(135deg,#a6192e,#ffb81c);color:#fff;cursor:move}
    .psu-ai-head .psu-title{font-weight:700;letter-spacing:.2px}
    .psu-ai-body{padding:.8rem}
    .psu-ai-row{display:flex;gap:.5rem;margin:.5rem 0}
    .psu-ai-row button{flex:1;border:none;padding:.5rem .6rem;border-radius:.6rem;background:#f3f4f6;cursor:pointer}
    .psu-ai-row button:hover{background:#e5e7eb}
    .psu-ai-ta{width:100%;min-height:80px;border:1px solid #e5e7eb;border-radius:.6rem;padding:.6rem}
    .psu-ai-actions{display:flex;justify-content:flex-end;gap:.5rem;margin-top:.5rem}
    .psu-ai-min{position:fixed;right:1rem;bottom:1rem;width:52px;height:52px;border-radius:50%;background:#a6192e;color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px rgba(0,0,0,.25);cursor:pointer;z-index:9999;font-size:22px}
    .psu-ai-chip{display:inline-block;padding:.15rem .5rem;border-radius:999px;background:#fff1; color:#fff; border:1px solid rgba(255,255,255,.5); font-size:.75rem}
  `;
  const style=document.createElement('style'); style.textContent=panelCSS; document.head.appendChild(style);

  const btn=document.createElement('div'); btn.className='psu-ai-min'; btn.title="Campus Copilot"; btn.innerHTML="🤖"; document.body.appendChild(btn);

  const panel=document.createElement('div');
  panel.className='psu-ai-panel'; panel.style.display='none';
  panel.innerHTML=`
    <div class="psu-ai-head">
      <div class="psu-title">Campus Copilot</div>
      <div style="margin-left:auto;display:flex;gap:.5rem"><span class="psu-ai-chip">AI</span><span class="psu-ai-chip">PSU</span></div>
    </div>
    <div class="psu-ai-body">
      <div class="psu-ai-row">
        <button data-act="rewrite">✍️ Improve My Post</button>
        <button data-act="topics">💡 Topic Ideas</button>
      </div>
      <div class="psu-ai-row">
        <button data-act="mentor">👥 Mentor Matches</button>
        <button data-act="resume">💼 Optimize Resume</button>
      </div>
      <div class="psu-ai-row">
        <button data-act="summary">🧾 Summarize</button>
        <button data-act="learn">🧭 Learning Path</button>
      </div>
      <textarea class="psu-ai-ta" placeholder="Ask anything… or paste text here."></textarea>
      <div class="psu-ai-actions">
        <button class="psu-ai-run">Run</button>
        <button class="psu-ai-close">Close</button>
      </div>
      <div class="psu-ai-out" style="margin-top:.6rem; font-size:.9rem; color:#374151;"></div>
    </div>
  `;
  document.body.appendChild(panel);

  // Drag
  (function drag() {
    const head=panel.querySelector('.psu-ai-head'); let ox=0, oy=0, dx=0, dy=0, dragging=false;
    head.addEventListener('mousedown', e=>{ dragging=true; ox=e.clientX; oy=e.clientY; const r=panel.getBoundingClientRect(); dx=ox-r.left; dy=oy-r.top; document.body.style.userSelect='none'; });
    window.addEventListener('mousemove', e=>{ if(!dragging) return; panel.style.left=(e.clientX-dx)+'px'; panel.style.top=(e.clientY-dy)+'px'; panel.style.right='auto'; panel.style.bottom='auto'; panel.style.position='fixed'; });
    window.addEventListener('mouseup', ()=>{ dragging=false; document.body.style.userSelect=''; });
  })();

  // Toggle
  btn.addEventListener('click', ()=>{ panel.style.display = panel.style.display==='none'? 'block':'none'; });

  const ta = panel.querySelector('.psu-ai-ta');
  const out = panel.querySelector('.psu-ai-out');
  let action = "rewrite";
  panel.querySelectorAll('[data-act]').forEach(b=>b.addEventListener('click', ()=>{ action=b.getAttribute('data-act'); out.textContent=`Selected: ${action}`; }));

  panel.querySelector('.psu-ai-close').addEventListener('click', ()=>{ panel.style.display='none'; });
  panel.querySelector('.psu-ai-run').addEventListener('click', async ()=>{
    const client = window.psuAI || new window.PSUAIClient();
    const text = ta.value.trim();
    out.textContent="Working…";
    try {
      if(action==="rewrite"){
        const r = await client.rewrite({text, tone:"warm and confident"});
        out.innerHTML = r.ok ? `<strong>Rewritten:</strong><br>${escapeHtml(r.data.rewritten||'')}` : `Error: ${r.error?.message}`;
      } else if(action==="topics"){
        const r = await client.topics({seed:text||"internships, scholarships, campus life"});
        out.innerHTML = r.ok ? `<ul>${(r.data.topics||[]).map(t=>`<li>${escapeHtml(t)}</li>`).join("")}</ul>` : `Error: ${r.error?.message}`;
      } else if(action==="mentor"){
        const r = await client.match({interests:(text||"python, data").split(",").map(s=>s.trim())});
        const m = r.data?.matches?.[0]; out.innerHTML = r.ok && m ? `${m.name} (${m.field})<br>Compat: ${m.compatibility||75}%<br>${escapeHtml(r.data.explanation||'')}` : `No match`;
      } else if(action==="resume"){
        const r = await client.resumeOptimize({resume:text||"student resume", job_description:"data analyst internship"});
        out.innerHTML = r.ok ? `
          <div><strong>Score:</strong> ${r.data.score||0}</div>
          <div><strong>Missing Keywords:</strong> ${(r.data.missingKeywords||[]).join(", ")}</div>
          <div><strong>Improved Summary:</strong> ${escapeHtml(r.data.improvedSummary||'')}</div>
        ` : `Error: ${r.error?.message}`;
      } else if(action==="summary"){
        const r = await client.summary({text: text || collectFeedText()});
        out.innerHTML = r.ok ? `<pre style="white-space:pre-wrap">${escapeHtml(JSON.stringify(r.data.summary,null,2))}</pre>` : `Error: ${r.error?.message}`;
      } else if(action==="learn"){
        const r = await client.learningPath({goal: text || "software engineer"});
        out.innerHTML = r.ok ? `<pre style="white-space:pre-wrap">${escapeHtml(JSON.stringify(r.data,null,2))}</pre>` : `Error: ${r.error?.message}`;
      }
    } catch(e){ out.textContent="Something went wrong."; }
  });

  function escapeHtml(s){ return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;"); }
})();
