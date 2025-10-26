/* static/js/faculty_analytics.js */
(function () {
  // Helper: format date labels as M/D
  function shortDate(iso) {
    try {
      const d = new Date(iso);
      return `${d.getMonth() + 1}/${d.getDate()}`;
    } catch {
      return iso;
    }
  }

  // PSU palette
  const CRIMSON = "#990000";
  const GOLD = "#FFC82E";
  const GRAY = "#6B7280";

  // Discover slug from data attribute or URL
  function getSlug() {
    const el = document.getElementById("fa-views-chart");
    if (el && el.dataset.slug) return el.dataset.slug;
    // fallback: /faculty/<slug>
    const m = location.pathname.match(/\/faculty\/([^\/?#]+)/i);
    return m ? decodeURIComponent(m[1]) : null;
  }

  async function fetchJSON(url) {
    const res = await fetch(url, { credentials: "same-origin" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function init() {
    const slug = getSlug();
    if (!slug) return;

    // Canvas elements
    const viewsCanvas = document.getElementById("fa-views-chart");
    const engagementCanvas = document.getElementById("fa-engagement-chart");
    if (!viewsCanvas || !engagementCanvas) return;

    // API endpoints
    const base = `/faculty`;
    const summaryURL = `${base}/api/${encodeURIComponent(slug)}/analytics`;
    const seriesURL = `${base}/api/${encodeURIComponent(slug)}/timeseries?days=30`;

    try {
      // Fetch both datasets concurrently
      const [summaryResp, seriesResp] = await Promise.all([
        fetchJSON(summaryURL),
        fetchJSON(seriesURL),
      ]);

      if (summaryResp.status !== "success" || seriesResp.status !== "success") {
        throw new Error("Bad API response");
      }

      const summary = summaryResp.data || {};
      const series = (seriesResp.data || []).slice(0, 30);

      // Update KPI texts
      const viewsEl = document.getElementById("fa-views");
      const avgEl = document.getElementById("fa-avg-time");
      const updEl = document.getElementById("fa-updated-at");

      if (viewsEl) viewsEl.textContent = summary.views ?? "0";
      if (avgEl) avgEl.textContent = summary.avg_time_sec ?? "—";
      if (updEl) updEl.textContent = summary.updated_at ?? "—";

      // Prepare timeseries data
      const labels = series.map((d) => shortDate(d.date));
      const counts = series.map((d) => d.views ?? 0);

      // Render line chart (views)
      const lineCtx = viewsCanvas.getContext("2d");
      new Chart(lineCtx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Views",
              data: counts,
              borderColor: CRIMSON,
              backgroundColor: "rgba(153,0,0,0.15)",
              borderWidth: 2,
              pointRadius: 2,
              tension: 0.25,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { mode: "index", intersect: false },
          },
          scales: {
            x: { ticks: { color: GRAY } },
            y: { ticks: { color: GRAY }, beginAtZero: true, grace: "5%" },
          },
        },
      });
      // Ensure the container has some height
      viewsCanvas.parentElement.style.minHeight = "260px";

      // Render doughnut chart (engagement split)
      const doughnutCtx = engagementCanvas.getContext("2d");
      const engaged = Math.max(0, Math.round((summary.views || 0) * 0.65));
      const skim = Math.max(0, (summary.views || 0) - engaged);

      new Chart(doughnutCtx, {
        type: "doughnut",
        data: {
          labels: ["Engaged", "Skim"],
          datasets: [
            {
              data: [engaged, skim],
              backgroundColor: [GOLD, "#E5E7EB"],
              borderColor: ["#FFFFFF", "#FFFFFF"],
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom", labels: { color: GRAY } },
            tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed}` } },
          },
        },
      });
      engagementCanvas.parentElement.style.minHeight = "220px";
    } catch (err) {
      console.error("[Faculty Analytics] Failed to load charts:", err);
      const note = document.getElementById("fa-views-note");
      if (note) {
        note.textContent = "Analytics data is currently unavailable. Please try again later.";
        note.classList.add("text-red-600");
      }
    }
  }

  // Kick off when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
