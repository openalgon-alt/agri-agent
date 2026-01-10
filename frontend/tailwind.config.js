/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mw-beige': '#FDFBF7', // The background color from the image
        'mw-card': '#EEEBE5',  // The logic/reasoning box color
        'mw-primary': '#FF6B4A', // The orange accent (Emily icon)
        'mw-text': '#1A1A1A',
        'mw-gray': '#666666'
      },
      fontFamily: {
        serif: ['Merriweather', 'serif'], // Matching the serif headers
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
