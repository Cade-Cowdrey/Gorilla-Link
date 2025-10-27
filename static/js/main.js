// ============================================================
// 🦍 PittState-Connect | PSU Frontend Interactivity Script
// ============================================================

// 🌙 Dark Mode Toggle
const html = document.documentElement;
const toggleBtn = document.getElementById("themeToggle");
const savedTheme = localStorage.getItem("theme");

if (savedTheme === "dark" || (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
  html.classList.add("dark");
  if (toggleBtn) toggleBtn.textContent = "☀️";
}

if (toggleBtn) {
  toggleBtn.addEventListener("click", () => {
    html.classList.toggle("dark");
    const isDark = html.classList.contains("dark");
    toggleBtn.textContent = isDark ? "☀️" : "🌙";
    localStorage.setItem("theme", isDark ? "dark" : "light");
  });
}

// 🧭 Navbar Scroll Shadow Effect
const navbar = document.getElementById("navbar");
if (navbar) {
  window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
      navbar.classList.add("shadow-2xl", "bg-opacity-95");
    } else {
      navbar.classList.remove("shadow-2xl", "bg-opacity-95");
    }
  });
}

// ✨ Flash Message Auto-Dismiss
setTimeout(() => {
  document.querySelectorAll(".flash-message").forEach(msg => {
    msg.classList.add("opacity-0", "transition-opacity", "duration-500");
    setTimeout(() => msg.remove(), 500);
  });
}, 5000);

// 📊 Optional Analytics Hook (extendable)
window.addEventListener("load", () => {
  try {
    fetch("/analytics/ping", { method: "POST" }).catch(() => {});
  } catch (e) {}
});

// 🧩 Smooth anchor scroll (for internal nav links)
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener("click", function (e) {
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth" });
    }
  });
});
