/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'maldives-blue': '#00AEEF',
        'maldives-sand': '#F5F5DC',
      }
    },
  },
  plugins: [],
}
