/* static/js/faculty_admin_analytics.js */
(function () {
  const CRIMSON = "#990000";
  const GOLD = "#FFC82E";
  const GRAY = "#6B7280";
  let lineChart, barChart;

  function shortDate(iso) {
    try { const d = new Date(iso); return `${d.getMonth()+1}/${d.getDate()}`; }
    catch { return iso; }
  }

  async function getJSON(url) {
    const res = await fetch(url, { credentials: "same-origin" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function qs(id) { return document.getElementById(id); }

  function renderLine(labels, values) {
    const el = qs("fa-overview-chart").getContext("2d");
    if (lineChart) lineChart.destroy();
    lineChart = new Chart(el, {
      type: "line",
      data: { labels, datasets: [{ data: values, label: "Views", borderColor: CRIMSON, backgroundColor: "rgba(153,0,0,0.15)", borderWidth: 2, pointRadius: 2, tension: 0.25 }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { mode: "index", intersect: false }},
        scales: { x: { ticks: { color: GRAY } }, y: { beginAtZero: true, grace: "5%", ticks: { color: GRAY } } }
      }
    });
  }

  function renderBar(labels, values) {
    const el = qs("fa-dept-chart").getContext("2d");
    if (barChart) barChart.destroy();
    barChart = new Chart(el, {
      type: "bar",
      data: { labels, datasets: [{ data: values, label: "Views", backgroundColor: GOLD, borderColor: "#FFFFFF", borderWidth: 1 }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }},
        scales: { x: { ticks: { color: GRAY } }, y: { beginAtZero: true, grace: "5%", ticks: { color: GRAY } } }
      }
    });
  }

  function fillTopTable(rows) {
    const tb = qs("fa-top-table");
    tb.innerHTML = "";
    if (!rows || rows.length === 0) {
      tb.innerHTML = `<tr><td class="py-3 text-gray-500" colspan="5">No data for this range.</td></tr>`;
      return;
    }
    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.className = "border-b last:border-0";
      tr.innerHTML = `
        <td class="py-2 pr-4">${r.name}</td>
        <td class="py-2 pr-4 text-gray-600">${r.title || "—"}</td>
        <td class="py-2 pr-4 text-gray-600">${r.department || "—"}</td>
        <td class="py-2 pr-4 font-semibold text-crimson">${r.views}</td>
        <td class="py-2 pr-4">
          <a class="text-gold hover:text-crimson font-semibold" href="/faculty/${encodeURIComponent(r.slug)}">Open →</a>
        </td>`;
      tb.appendChild(tr);
    });
  }

  async function loadAll() {
    const days = qs("fa-days").value;
    const dept = qs("fa-dept").value;
    const limit = qs("fa-top-limit").value;

    const qOverview = `/faculty/api/analytics/overview?days=${days}&department=${encodeURIComponent(dept)}`;
    const qBreakdown = `/faculty/api/analytics/department-breakdown?days=${days}`;
    const qTop = `/faculty/api/analytics/top-faculty?days=${days}&limit=${limit}&department=${encodeURIComponent(dept)}`;

    try {
      const [ov, bd, top] = await Promise.all([getJSON(qOverview), getJSON(qBreakdown), getJSON(qTop)]);

      // KPIs
      if (ov.status === "success") {
        qs("kpi-views").textContent = ov.kpis.total_views ?? 0;
        qs("kpi-avg").firstChild.nodeValue = (ov.kpis.avg_time_sec ?? 0) + " ";
        qs("kpi-count").textContent = ov.kpis.faculty_count ?? 0;
        const labels = (ov.series || []).map(d => shortDate(d.date));
        const values = (ov.series || []).map(d => d.views ?? 0);
        renderLine(labels, values);
        qs("fa-overview-updated").textContent = `Last ${days} days`;
      }

      if (bd.status === "success") {
        renderBar(bd.labels || [], bd.counts || []);
      }

      if (top.status === "success") {
        fillTopTable(top.results || []);
      }
    } catch (e) {
      console.error("[Faculty Admin Analytics] load error", e);
      // Gentle UI fallback
      qs("kpi-views").textContent = "0";
      qs("kpi-avg").firstChild.nodeValue = "0 ";
      qs("kpi-count").textContent = "0";
      renderLine([], []);
      renderBar([], []);
      fillTopTable([]);
    }
  }

  function onReady() {
    // Default select init from server
    if (window.__FA_DEFAULT_DAYS__) {
      const sel = qs("fa-days");
      if (sel) sel.value = String(window.__FA_DEFAULT_DAYS__);
    }
    qs("fa-filters").addEventListener("submit", function (e) {
      e.preventDefault();
      loadAll();
    });
    qs("fa-top-limit").addEventListener("change", loadAll);
    loadAll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();
