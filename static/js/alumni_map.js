// static/js/alumni_map.js
// PSU-branded Leaflet world map with city-level clusters

(function () {
  function makeMap() {
    const map = L.map("alumniMap", { scrollWheelZoom: true });
    // World view
    map.setView([20, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
    }).addTo(map);

    return map;
  }

  function badge(text) {
    const span = document.createElement("span");
    span.className = "badge rounded-pill";
    span.style.background = "#BA0C2F";
    span.textContent = text;
    return span.outerHTML;
  }

  window.PSU_ALUMNI_MAP_BOOT = async function ({ dataUrl, colors }) {
    const map = makeMap();
    try {
      const res = await fetch(dataUrl, { cache: "no-store" });
      const data = await res.json();

      data.clusters.forEach((c) => {
        const { lat, lon, city, state, country, count, sample } = c;
        if (typeof lat !== "number" || typeof lon !== "number") return;

        const m = L.circleMarker([lat, lon], {
          radius: Math.min(20, 6 + Math.sqrt(count)),
          color: colors.red,
          fillColor: colors.red,
          fillOpacity: 0.75,
          weight: 1
        }).addTo(map);

        const lines = [];
        lines.push(`<div class="fw-bold" style="color:#BA0C2F;">${city}${state ? ", " + state : ""}${country ? ", " + country : ""}</div>`);
        lines.push(`<div class="text-muted small">Alumni: <strong>${count.toLocaleString()}</strong></div>`);
        if (sample && sample.length) {
          lines.push(`<hr class="my-1" />`);
          sample.forEach(s => {
            const gy = s.graduation_year ? ` (’${String(s.graduation_year).slice(-2)})` : "";
            lines.push(`<div class="small">${badge(s.department || "Alumni")} ${s.name}${gy}<br/><span class="text-muted">${s.headline || ""}</span></div>`);
          });
        }

        m.bindPopup(lines.join(""), { className: "shadow-sm" });
      });
    } catch (e) {
      console.error("Failed to load alumni map:", e);
    }
  };
})();
