/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#fafaf7",
        panel: "#f5f3ef",
        border: "#e0dbd4",
        ink: "#2c2416",
        muted: "#8c8273",
        accent: "#e8a838",
        hover: "#f0ede6",
      },
    },
  },
  plugins: [],
};
