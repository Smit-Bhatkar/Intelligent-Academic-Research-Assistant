/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#1F3864",
        accent: "#2E5597",
      },
    },
  },
  plugins: [],
};
