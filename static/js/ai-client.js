// static/js/ai-client.js
// PSU AI Client — handles communication with your Flask AI API endpoints.
// Works with /api/ai/query, /api/ai/insight, /api/ai/moderate, etc.

class PSUAIClient {
  constructor(base = "/api/ai") {
    this.base = base;
  }

  async post(path, body = {}) {
    const response = await fetch(`${this.base}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  }

  async query(prompt) {
    return this.post("/query", { q: prompt });
  }

  async moderate(text) {
    return this.post("/moderate", { text });
  }

  async insight(data) {
    return this.post("/insight", data);
  }

  async essayReview(text) {
    return this.post("/tools/analyze_essay", { text });
  }

  async resumeOptimize(bullets) {
    return this.post("/tools/optimize_resume", { bullets });
  }
}

// Attach global instance for site-wide usage
window.psuAI = new PSUAIClient();

// Optional toast helper (for user feedback)
window.psuNotify = function (msg, type = "info") {
  const existing = document.querySelector(".psu-toast");
  if (existing) existing.remove();
  const el = document.createElement("div");
  el.className = `psu-toast psu-toast-${type}`;
  el.textContent = msg;
  Object.assign(el.style, {
    position: "fixed",
    bottom: "30px",
    right: "30px",
    background: type === "error" ? "#a6192e" : "#ffb81c",
    color: "#fff",
    padding: "12px 18px",
    borderRadius: "10px",
    fontWeight: "600",
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
    zIndex: "9999",
    transition: "opacity 0.3s ease",
  });
  document.body.appendChild(el);
  setTimeout(() => (el.style.opacity = "0"), 4000);
  setTimeout(() => el.remove(), 4500);
};
