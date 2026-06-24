/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#1a1a2e", light: "#16213e", accent: "#0f3460", highlight: "#e94560" },
      },
    },
  },
  plugins: [],
};
