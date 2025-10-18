const DARK_KEY="psc_dark"; function applyDarkMode(isDark){document.documentElement.setAttribute("data-theme", isDark ? "dark":"light"); try{localStorage.setItem(DARK_KEY, JSON.stringify(isDark));}catch{}}
(function(){let stored=null; try{stored=JSON.parse(localStorage.getItem(DARK_KEY));}catch{} const prefers=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches; applyDarkMode(stored===null?prefers:stored);})();
function toggleDarkMode(){const nowDark = document.documentElement.getAttribute("data-theme")!=="dark"; applyDarkMode(nowDark);}
