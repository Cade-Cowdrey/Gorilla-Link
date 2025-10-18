/* =======================================================
   🎓 PSU Branded Theme Script — psu-theme.js
   Handles: Theme Toggle | Scroll Progress | Navbar | Animations
   ======================================================= */

// --- 🌗 Theme Toggle (Light / Dark Mode) ---
const themeToggle = document.getElementById("theme-toggle");
const html = document.documentElement;

// Load saved theme preference
if (localStorage.getItem("theme") === "dark") {
  html.classList.add("dark");
} else {
  html.classList.remove("dark");
}

// Toggle handler
if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    html.classList.toggle("dark");
    const darkMode = html.classList.contains("dark");
    localStorage.setItem("theme", darkMode ? "dark" : "light");

    // Icon swap (sun ↔ moon)
    const sunIcon = themeToggle.querySelector(".sun-icon");
    const moonIcon = themeToggle.querySelector(".moon-icon");
    if (sunIcon && moonIcon) {
      sunIcon.classList.toggle("hidden", darkMode);
      moonIcon.classList.toggle("hidden", !darkMode);
    }
  });
}

// --- 📊 Scroll Progress Bar ---
window.addEventListener("scroll", () => {
  const progressBar = document.getElementById("scroll-progress");
  if (!progressBar) return;

  const scrollTop = document.documentElement.scrollTop;
  const scrollHeight =
    document.documentElement.scrollHeight -
    document.documentElement.clientHeight;
  const progress = (scrollTop / scrollHeight) * 100;

  progressBar.style.width = progress + "%";
});

// --- ⬆️ Back-to-Top Button ---
const backToTop = document.getElementById("back-to-top");
window.addEventListener("scroll", () => {
  if (!backToTop) return;

  if (window.scrollY > 400) {
    backToTop.classList.remove("opacity-0", "pointer-events-none");
    backToTop.classList.add("opacity-100");
  } else {
    backToTop.classList.add("opacity-0", "pointer-events-none");
    backToTop.classList.remove("opacity-100");
  }
});

if (backToTop) {
  backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// --- 🍔 Mobile Navbar Toggle ---
const mobileMenuButton = document.getElementById("mobile-menu-button");
const mobileMenu = document.getElementById("mobile-menu");

if (mobileMenuButton && mobileMenu) {
  mobileMenuButton.addEventListener("click", () => {
    mobileMenu.classList.toggle("hidden");

    const expanded =
      mobileMenuButton.getAttribute("aria-expanded") === "true"
        ? "false"
        : "true";
    mobileMenuButton.setAttribute("aria-expanded", expanded);
  });
}

// --- ✨ Fade-In Animation on Scroll ---
const revealElements = document.querySelectorAll(".reveal-on-scroll");
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add(
          "opacity-100",
          "translate-y-0",
          "transition-all",
          "duration-700"
        );
      }
    });
  },
  { threshold: 0.15 }
);

revealElements.forEach((el) => {
  el.classList.add("opacity-0", "translate-y-6");
  observer.observe(el);
});

// --- 💨 Smooth Scroll for Internal Links ---
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth" });
    }
  });
});

// --- 🏫 PSU Signature UI Enhancements ---
document.addEventListener("DOMContentLoaded", () => {
  console.log("🎓 PSU Theme Active — Gorillas Up!");
  const footerYear = document.getElementById("footer-year");
  if (footerYear) footerYear.textContent = new Date().getFullYear();
});
