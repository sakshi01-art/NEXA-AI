/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        nexa: {
          bg: '#0A0E1A',
          card: '#111827',
          accent: '#6366F1',
          secondary: '#8B5CF6',
        }
      }
    },
  },
  plugins: [],
}
