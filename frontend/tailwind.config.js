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
        // Neutral light-gray section background (was "arena", a warm sand tone).
        gris: "#E5E5E2",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Public Sans", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
