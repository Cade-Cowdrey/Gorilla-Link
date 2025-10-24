// static/js/analytics-dashboard.js
// ===============================================================
//  Live PSU Dashboard Power-ups
// ===============================================================
const apiSummary = "/api/analytics/summary";
const apiInsight = "/api/ai/insight";
const chartCtx = document.getElementById("trendChart");

let chart;

// --------------------------
//  Fetch Metrics
// --------------------------
async function loadMetrics() {
  try {
    const res = await fetch(apiSummary);
    const data = await res.json();
    if (!data.success) throw new Error(data.error);
    const m = data.data;
    document.getElementById("users-total").textContent = m.users_total;
    document.getElementById("active-sessions").textContent = m.active_sessions;
    document.getElementById("open-scholarships").textContent = m.open_scholarships;
    document.getElementById("events-upcoming").textContent = m.events_upcoming;
    document.getElementById("jobs-posted").textContent = m.jobs_posted;
    document.getElementById("avg-match-score").textContent = `${m.avg_match_score}%`;
    updateChart(m);
  } catch (err) {
    console.error("Metrics load error:", err);
  }
}

// --------------------------
//  Fetch AI Insight
// --------------------------
async function loadInsight() {
  try {
    const res = await fetch(apiInsight, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ context: "Summarize weekly engagement and key growth metrics." }),
    });
    const data = await res.json();
    const insight = data?.data?.answer || "No insight available.";
    document.getElementById("insight-content").innerHTML = insight.replace(/\n/g, "<br>");
  } catch (err) {
    document.getElementById("insight-content").textContent = "Failed to load insights.";
  }
}

// --------------------------
//  Chart.js Trend Graph
// --------------------------
async function updateChart(m) {
  const ctx = chartCtx.getContext("2d");
  const values = [
    m.users_total,
    m.alumni,
    m.active_sessions,
    m.jobs_posted,
    m.events_upcoming,
    m.open_scholarships,
  ];
  const labels = [
    "Users",
    "Alumni",
    "Sessions",
    "Jobs",
    "Events",
    "Scholarships",
  ];
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Engagement Metrics",
          data: values,
          backgroundColor: "#a6192eaa",
          borderRadius: 8,
        },
      ],
    },
    options: {
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

// --------------------------
//  Export CSV
// --------------------------
document.getElementById("export-btn").addEventListener("click", async () => {
  const res = await fetch(apiSummary);
  const data = await res.json();
  const rows = Object.entries(data.data);
  const csv = ["Metric,Value", ...rows.map(([k, v]) => `${k},${v}`)].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `pittstate-analytics-${Date.now()}.csv`;
  link.click();
});

// --------------------------
//  Theme Toggle (Persistent)
// --------------------------
const themeBtn = document.getElementById("theme-toggle");
themeBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
});
window.addEventListener("load", () => {
  if (localStorage.getItem("theme") === "dark") document.body.classList.add("dark");
});

// --------------------------
//  Auto-Refresh & Init
// --------------------------
loadMetrics();
loadInsight();
setInterval(() => {
  loadMetrics();
  loadInsight();
}, 5 * 60 * 1000);
