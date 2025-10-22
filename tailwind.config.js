/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Enables dark mode toggle via .dark class
  content: [
    './templates/**/*.html',
    './blueprints/**/*.html',
    './static/js/**/*.js',
    './**/*.py'
  ],
  theme: {
    extend: {
      colors: {
        'psu-crimson': '#991B1E',
        'psu-gold': '#FFC82E',
        'psu-charcoal': '#2C2A29',
        'psu-gray': '#E5E5E5',
        'psu-light': '#F9F9F9'
      },
      fontFamily: {
        heading: ['Poppins', 'Segoe UI', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif']
      },
      boxShadow: {
        smooth: '0 4px 20px rgba(0,0,0,0.1)',
        gold: '0 0 12px rgba(255, 200, 46, 0.4)',
      },
      transitionProperty: {
        colors: 'background-color, border-color, color, fill, stroke',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 200, 46, 0.5)' },
          '50%': { boxShadow: '0 0 10px 6px rgba(255, 200, 46, 0.3)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.5s ease-in-out',
        pulseGold: 'pulseGold 2s infinite',
      },
      container: {
        center: true,
        padding: '1rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
