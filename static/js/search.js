let overlay,input,results;
function showSearch(){overlay=document.getElementById("globalSearchOverlay");input=document.getElementById("globalSearchInput");results=document.getElementById("globalSearchResults");overlay.classList.remove("d-none"); setTimeout(()=>input&&input.focus(),50);}
function hideSearch(){overlay.classList.add("d-none");}
document.addEventListener("keydown",(e)=>{if(e.key==="/"&&!e.target.matches("input, textarea")){e.preventDefault();showSearch();}else if(e.key==="Escape"&&overlay&&!overlay.classList.contains("d-none")){hideSearch();}});
async function doSearch(q){if(!q||q.length<2){results.innerHTML="";return;} const r=await fetch(`/api/search?q=${encodeURIComponent(q)}`); const data=await r.json(); results.innerHTML = `
<div class="row">
  <div class="col-md-4"><h5>Departments</h5>
  <ul class="list-group">${data.departments.map(d=>`<li class="list-group-item d-flex justify-content-between"><span>${d.name}</span><a class="btn btn-sm btn-danger" href="/departments/${(d.college||'college').toLowerCase().replaceAll(' ','-')}/${d.slug}">Open</a></li>`).join("")}</ul></div>
  <div class="col-md-4"><h5>Alumni</h5><ul class="list-group">${data.alumni.map(a=>`<li class="list-group-item">${a.name} — ${a.major||""} ${a.year?`(${a.year})`:""}</li>`).join("")}</ul></div>
  <div class="col-md-4"><h5>Opportunities</h5><ul class="list-group">${data.opportunities.map(o=>`<li class="list-group-item">${o.title} — ${o.org||""}</li>`).join("")}</ul></div>
</div>`;}
document.addEventListener("input",(e)=>{if(e.target.id==="globalSearchInput") doSearch(e.target.value.trim());});
