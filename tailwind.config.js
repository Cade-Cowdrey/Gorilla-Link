/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./blueprints/**/*.html",
    "./static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        psu: {
          crimson: "#991B1E",
          gold: "#FFC82E",
          charcoal: "#2C2A29",
          gray: "#E5E5E5",
          light: "#F9F9F9",
          accent: "#D97706" // amber tone for hover states
        }
      },
      fontFamily: {
        sans: ["Inter", "Helvetica", "Arial", "sans-serif"],
        heading: ["Poppins", "sans-serif"]
      },
      boxShadow: {
        smooth: "0 4px 20px rgba(0,0,0,0.1)",
        gold: "0 0 12px rgba(255,200,46,0.4)"
      },
      gradientColorStops: {
        psu: {
          warm: ["#991B1E", "#FFC82E"],
          cool: ["#991B1E", "#2C2A29"]
        }
      },
      backgroundImage: {
        "psu-gold-gradient": "linear-gradient(90deg, #991B1E 0%, #FFC82E 100%)",
        "psu-dark-gradient": "linear-gradient(90deg, #2C2A29 0%, #991B1E 100%)"
      }
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
    require("@tailwindcss/line-clamp")
  ],
};
