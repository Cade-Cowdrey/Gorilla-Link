// static/js/campus_charts.js
// PSU-branded charts and counters for the public microsite

(function () {
  const easeCount = (el, target, dur = 900) => {
    let start = 0;
    if (!el) return;
    const step = Math.max(1, Math.ceil(target / (dur / 20)));
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        start = target;
        clearInterval(timer);
      }
      el.textContent = Number(start).toLocaleString();
    }, 20);
  };

  const renderPartners = (listEl, partners) => {
    if (!listEl) return;
    listEl.innerHTML = "";
    if (!partners || !partners.length) {
      const li = document.createElement("li");
      li.className = "list-group-item text-muted";
      li.textContent = "Partner updates coming soon.";
      listEl.appendChild(li);
      return;
    }
    partners.forEach((p) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between";
      li.innerHTML = `<span>${p.company}</span><span class="badge" style="background:#BA0C2F;">${p.count}</span>`;
      listEl.appendChild(li);
    });
  };

  const renderTrend = (canvasId, labels, values, colors) => {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "New Gorillas",
          data: values,
          borderColor: colors.red,
          backgroundColor: "rgba(186, 12, 47, 0.12)",
          borderWidth: 2,
          tension: 0.25,
          fill: true,
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } },
          x: {}
        }
      }
    });
  };

  window.PSU_CAMPUS_MICROSITE_BOOT = async function ({ dataUrl, colors }) {
    try {
      const res = await fetch(dataUrl, { cache: "no-store" });
      const data = await res.json();

      // Counters
      easeCount(document.getElementById("countCommunity"), data.topline.community);
      easeCount(document.getElementById("countMentors"), data.topline.mentors);
      easeCount(document.getElementById("countDepartments"), data.topline.departments);
      easeCount(document.getElementById("countOpportunities"), data.topline.opportunities_active);

      const engagementEl = document.getElementById("countEngagement");
      if (engagementEl) engagementEl.textContent = Number(data.topline.engagement_30d).toLocaleString();

      // Partners
      renderPartners(document.getElementById("partnersList"), data.partners);

      // Trend chart
      renderTrend("psuTrendChart", data.trend.labels, data.trend.values, colors);
    } catch (e) {
      console.error("Failed to load campus data:", e);
    }
  };
})();
