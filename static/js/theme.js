// static/js/theme.js
(function() {
  const key = "psu-theme";
  const setTheme = (t) => document.documentElement.setAttribute("data-theme", t);
  const saved = localStorage.getItem(key) || "light";
  setTheme(saved);
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-toggle-theme]");
    if (!btn) return;
    const next = (document.documentElement.getAttribute("data-theme") === "dark") ? "light" : "dark";
    localStorage.setItem(key, next);
    setTheme(next);
  });
})();
