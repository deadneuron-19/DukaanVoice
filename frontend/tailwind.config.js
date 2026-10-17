/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: "#254D3A",
        sage: "#A9B9A0",
        cream: "#F7F3E9",
        ivory: "#FFFCF5",
        ink: "#252A25",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        display: ["Playfair Display", "serif"],
      },
    },
  },
  plugins: [],
};
