// Handles light/dark mode toggle persistence
const themeToggle = document.getElementById("theme-toggle");

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    document.documentElement.classList.toggle("dark");
    localStorage.setItem(
      "theme",
      document.documentElement.classList.contains("dark") ? "dark" : "light"
    );
  });
}

// Auto-load saved preference
if (localStorage.getItem("theme") === "dark") {
  document.documentElement.classList.add("dark");
}
