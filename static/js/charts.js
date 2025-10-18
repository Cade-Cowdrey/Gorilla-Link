document.addEventListener("DOMContentLoaded", ()=>{
  const el = document.getElementById("visitsChart"); if(!el) return;
  const ctx = el.getContext("2d");
  new Chart(ctx, { type: "line",
    data: { labels: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
      datasets: [{ label:"Visits", data:[5,9,7,12,8,10,6]}] },
    options: { responsive:true, maintainAspectRatio:false, scales:{ y:{ beginAtZero:true } } }
  });
});
