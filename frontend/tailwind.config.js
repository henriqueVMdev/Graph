/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          900: '#000000',
          800: '#080808',
          700: '#0f0f0f',
          600: '#161616',
          500: '#1e1e1e',
          400: '#2a2a2a',
        },
        accent: {
          green: '#c9a227',
          'green-light': '#f5c518',
          red: '#dc2626',
          'red-light': '#f87171',
          blue: '#f5c518',
          yellow: '#f5c518',
          'yellow-dim': '#c9a227',
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'yellow-glow': '0 0 20px rgba(245, 197, 24, 0.15)',
        'yellow-glow-sm': '0 0 8px rgba(245, 197, 24, 0.2)',
      },
    },
  },
  plugins: [],
}
