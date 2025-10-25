// static/js/theme-auto.js
// PSU Smart Auto Theme Controller
(() => {
  const STORAGE_KEY = "psu-theme";
  const root = document.documentElement;

  // Detect system preference
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");
  const applyTheme = (mode) => root.setAttribute("data-theme", mode);

  // Load saved or system theme
  const saved = localStorage.getItem(STORAGE_KEY);
  const initial = saved || (prefersDark.matches ? "dark" : "light");
  applyTheme(initial);

  // Sync when OS preference changes
  prefersDark.addEventListener("change", (e) => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      applyTheme(e.matches ? "dark" : "light");
    }
  });

  // Manual toggle (attached globally)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-toggle-theme]");
    if (!btn) return;
    const current = root.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
    localStorage.setItem(STORAGE_KEY, next);
  });

  // Smooth transition for better UX
  root.style.transition = "background-color 0.3s, color 0.3s";
})();
