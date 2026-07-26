/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#fffdf8",
        panel: "#f6f0e8",
        border: "#e5d9cb",
        ink: "#352a22",
        muted: "#958476",
        accent: "#d98c72",
        hover: "#f3e8de",
      },
    },
  },
  plugins: [],
};
