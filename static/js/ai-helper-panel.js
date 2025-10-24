// static/js/ai-helper-panel.js
// Floating PSU Campus Assistant Widget

(function () {
  if (document.getElementById("psu-ai-panel")) return;

  const panel = document.createElement("div");
  panel.id = "psu-ai-panel";
  panel.style.position = "fixed";
  panel.style.right = "20px";
  panel.style.bottom = "20px";
  panel.style.width = "320px";
  panel.style.maxWidth = "90vw";
  panel.style.zIndex = "2000";
  panel.innerHTML = `
    <div class="card shadow-lg border-0" style="border-radius:16px;overflow:hidden;">
      <div class="card-header text-white" style="background:linear-gradient(135deg,#a6192e,#ffb81c);display:flex;justify-content:space-between;align-items:center;">
        <strong>Campus Assistant</strong>
        <button id="psu-ai-toggle" class="btn btn-sm btn-outline-light" style="background:rgba(255,255,255,0.2);border:none;">_</button>
      </div>
      <div id="psu-ai-body" class="card-body" style="padding:10px;background:#fafafa;">
        <textarea id="psu-ai-input" class="form-control" rows="3" placeholder="Ask me anything about Pitt State..."></textarea>
        <div style="margin-top:8px;display:flex;gap:6px;">
          <button id="psu-ai-send" class="btn btn-crimson flex-fill">Ask</button>
          <button id="psu-ai-clear" class="btn btn-outline-secondary flex-fill">Clear</button>
        </div>
        <div id="psu-ai-output" class="mt-3" style="font-size:0.9rem;color:#333;"></div>
      </div>
    </div>
  `;

  document.body.appendChild(panel);

  const body = document.getElementById("psu-ai-body");
  const output = document.getElementById("psu-ai-output");
  const input = document.getElementById("psu-ai-input");

  // Toggle collapse
  document.getElementById("psu-ai-toggle").onclick = () => {
    body.style.display = body.style.display === "none" ? "block" : "none";
  };

  // Clear
  document.getElementById("psu-ai-clear").onclick = () => {
    input.value = "";
    output.innerHTML = "";
  };

  // Ask
  document.getElementById("psu-ai-send").onclick = async () => {
    const q = input.value.trim();
    if (!q) return window.psuNotify("Ask a question first!");
    output.innerHTML = "⏳ Thinking...";
    try {
      const res = await window.psuAI.query(q);
      output.innerHTML =
        res?.data?.answer ||
        "<em>No detailed response yet — try rephrasing your question.</em>";
    } catch (err) {
      output.innerHTML = "<span style='color:#a6192e'>⚠️ Error connecting to AI.</span>";
    }
  };
})();
