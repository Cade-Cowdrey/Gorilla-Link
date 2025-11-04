/**
 * Theme Toggle for PittState Connect
 * Handles dark mode switching with localStorage persistence
 * and system preference detection
 */

(function() {
  'use strict';

  const THEME_KEY = 'pittstate-theme';
  const THEMES = {
    LIGHT: 'light',
    DARK: 'dark'
  };

  class ThemeManager {
    constructor() {
      this.currentTheme = this.getInitialTheme();
      this.init();
    }

    /**
     * Get initial theme from localStorage or system preference
     */
    getInitialTheme() {
      // Check localStorage first
      const savedTheme = localStorage.getItem(THEME_KEY);
      if (savedTheme) {
        return savedTheme;
      }

      // Check system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return THEMES.DARK;
      }

      return THEMES.LIGHT;
    }

    /**
     * Initialize theme manager
     */
    init() {
      // Prevent flash of unstyled content
      document.body.classList.add('no-transition');
      
      // Apply initial theme
      this.applyTheme(this.currentTheme, false);
      
      // Re-enable transitions after a brief delay
      setTimeout(() => {
        document.body.classList.remove('no-transition');
      }, 100);

      // Listen for system theme changes
      if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
          // Only auto-switch if user hasn't set a preference
          if (!localStorage.getItem(THEME_KEY)) {
            const newTheme = e.matches ? THEMES.DARK : THEMES.LIGHT;
            this.setTheme(newTheme);
          }
        });
      }

      // Set up toggle button
      this.setupToggleButton();

      // Dispatch initial theme event
      this.dispatchThemeEvent();
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme, animate = true) {
      if (!animate) {
        document.body.classList.add('no-transition');
      }

      document.documentElement.setAttribute('data-theme', theme);
      this.currentTheme = theme;

      // Update meta theme-color for mobile browsers
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', theme === THEMES.DARK ? '#1a1a1a' : '#8B1538');
      }

      // Update toggle button if it exists
      this.updateToggleButton();

      if (!animate) {
        setTimeout(() => {
          document.body.classList.remove('no-transition');
        }, 100);
      }
    }

    /**
     * Set theme and save to localStorage
     */
    setTheme(theme) {
      this.applyTheme(theme, true);
      localStorage.setItem(THEME_KEY, theme);
      this.dispatchThemeEvent();
      
      // Send analytics event if gtag is available
      if (typeof gtag !== 'undefined') {
        gtag('event', 'theme_change', {
          theme: theme
        });
      }
    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
      const newTheme = this.currentTheme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT;
      this.setTheme(newTheme);
    }

    /**
     * Dispatch custom theme change event
     */
    dispatchThemeEvent() {
      const event = new CustomEvent('themechange', {
        detail: { theme: this.currentTheme }
      });
      document.dispatchEvent(event);
    }

    /**
     * Set up toggle button click handler
     */
    setupToggleButton() {
      const toggleBtn = document.getElementById('theme-toggle');
      if (toggleBtn) {
        toggleBtn.addEventListener('click', () => this.toggleTheme());
      }
    }

    /**
     * Update toggle button appearance
     */
    updateToggleButton() {
      const toggleBtn = document.getElementById('theme-toggle');
      if (!toggleBtn) return;

      const icon = toggleBtn.querySelector('.theme-toggle-icon');
      if (icon) {
        if (this.currentTheme === THEMES.DARK) {
          icon.innerHTML = '🌙';
          toggleBtn.setAttribute('aria-label', 'Switch to light mode');
        } else {
          icon.innerHTML = '☀️';
          toggleBtn.setAttribute('aria-label', 'Switch to dark mode');
        }
      }
    }

    /**
     * Get current theme
     */
    getTheme() {
      return this.currentTheme;
    }
  }

  // Initialize theme manager
  const themeManager = new ThemeManager();

  // Expose to global scope for external access
  window.ThemeManager = themeManager;

  // Add keyboard shortcut (Ctrl/Cmd + Shift + D)
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
      e.preventDefault();
      themeManager.toggleTheme();
    }
  });

  // Listen for theme change events from other tabs
  window.addEventListener('storage', (e) => {
    if (e.key === THEME_KEY && e.newValue) {
      themeManager.applyTheme(e.newValue, false);
    }
  });

  console.log('🌓 Theme Manager initialized. Current theme:', themeManager.getTheme());
  console.log('💡 Keyboard shortcut: Ctrl/Cmd + Shift + D to toggle theme');

})();

/**
 * Chart.js theme integration (if Chart.js is present)
 */
document.addEventListener('themechange', (e) => {
  if (typeof Chart !== 'undefined') {
    const theme = e.detail.theme;
    const isDark = theme === 'dark';

    // Update Chart.js defaults
    Chart.defaults.color = isDark ? '#f8f9fa' : '#212529';
    Chart.defaults.borderColor = isDark ? '#495057' : '#dee2e6';
    
    if (Chart.defaults.plugins && Chart.defaults.plugins.legend) {
      Chart.defaults.plugins.legend.labels.color = isDark ? '#f8f9fa' : '#212529';
    }

    // Re-render all charts
    Object.values(Chart.instances).forEach(chart => {
      if (chart && chart.update) {
        chart.update();
      }
    });
  }
});

/**
 * DataTables theme integration (if DataTables is present)
 */
document.addEventListener('themechange', (e) => {
  if (typeof $.fn.dataTable !== 'undefined') {
    const theme = e.detail.theme;
    const isDark = theme === 'dark';

    // Update DataTables styling
    $('table.dataTable').each(function() {
      const table = $(this).DataTable();
      if (table) {
        table.draw(false);
      }
    });
  }
});

/**
 * Code highlighting theme integration (if Prism or highlight.js is present)
 */
document.addEventListener('themechange', (e) => {
  const theme = e.detail.theme;
  const isDark = theme === 'dark';

  // Prism.js
  if (typeof Prism !== 'undefined') {
    document.querySelectorAll('pre code').forEach(block => {
      Prism.highlightElement(block);
    });
  }

  // highlight.js
  if (typeof hljs !== 'undefined') {
    document.querySelectorAll('pre code').forEach(block => {
      hljs.highlightElement(block);
    });
  }
});
