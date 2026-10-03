/** @type {import('tailwindcss').Config} */
module.exports = {
  // "tw-" avoids collisions with Bootstrap's utility classes while both
  // coexist during the page-by-page migration (see README "Migración a Tailwind").
  prefix: "tw-",
  content: ["./src/**/*.{js,jsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        ink: "#16181D",
        "ink-soft": "#52544D",
        paper: "#F7F6F3",
        "paper-raised": "#FFFFFF",
        rule: "#DDD8CC",
        magenta: "#C4005F",
        azul: "#1C3F94",
        verde: "#1B6E51",
        danger: "#B3261E",
        // Neutral light-gray section background (was "arena", a warm sand tone).
        gris: "#E5E5E2",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Public Sans", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "Menlo", "monospace"],
      },
      keyframes: {
        deriva: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "50%": { transform: "translate(-28px, 20px) scale(1.04)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        deriva: "deriva 40s ease-in-out infinite",
        "fade-in-up": "fade-in-up 0.35s ease-out",
      },
    },
  },
  plugins: [],
};
