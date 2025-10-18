let deferredPrompt=null; const btn = document.getElementById("installBtn");
window.addEventListener("beforeinstallprompt",(e)=>{e.preventDefault(); deferredPrompt=e; if(btn) btn.classList.remove("d-none"); });
if(btn){ btn.addEventListener("click", async ()=>{ if(!deferredPrompt) return; deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt=null; btn.classList.add("d-none"); }); }
if("serviceWorker" in navigator){ window.addEventListener("load", ()=>{ navigator.serviceWorker.register("/static/sw.js").catch(console.error); }); }
