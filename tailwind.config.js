/** =======================================================
 * 🎓 PSU Branded Tailwind Configuration
 * Matches PSU Connect web platform (Pitt State University)
 * ======================================================= */

module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/js/**/*.js"
  ],

  darkMode: "class", // Controlled by psu-theme.js toggle

  theme: {
    extend: {
      colors: {
        "psu-crimson": "#B5121B",
        "psu-gold": "#FFC72C",
        "psu-gray": "#F3F4F6",
        "psu-dark": "#1F2937",
        "psu-white": "#FFFFFF",
        "psu-silver": "#E5E7EB"
      },

      fontFamily: {
        sans: ["Inter", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"],
        heading: ["Poppins", "Inter", "sans-serif"],
      },

      boxShadow: {
        "psu-soft": "0 4px 10px rgba(0, 0, 0, 0.08)",
        "psu-strong": "0 6px 20px rgba(0, 0, 0, 0.12)",
      },

      borderRadius: {
        "2xl": "1rem",
      },

      transitionProperty: {
        "colors-transform": "color, background-color, transform",
      },

      keyframes: {
        fadeUp: {
          "0%": { opacity: 0, transform: "translateY(1.5rem)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: 0 },
          "100%": { opacity: 1 },
        },
      },

      animation: {
        fadeUp: "fadeUp 0.8s ease-out forwards",
        fadeIn: "fadeIn 0.6s ease-in forwards",
      },
    },
  },

  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
  ],
};
