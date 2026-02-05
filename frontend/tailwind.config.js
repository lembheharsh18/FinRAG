/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0066FF',
          50: '#E6F0FF',
          100: '#CCE0FF',
          200: '#99C2FF',
          300: '#66A3FF',
          400: '#3385FF',
          500: '#0066FF',
          600: '#0052CC',
          700: '#003D99',
          800: '#002966',
          900: '#001433',
        },
        secondary: {
          DEFAULT: '#00D9FF',
          50: '#E6FCFF',
          100: '#CCF9FF',
          200: '#99F3FF',
          300: '#66ECFF',
          400: '#33E6FF',
          500: '#00D9FF',
          600: '#00AECC',
          700: '#008299',
          800: '#005766',
          900: '#002B33',
        },
        dark: {
          DEFAULT: '#0A0E27',
          50: '#1A1F3A',
          100: '#151931',
          200: '#0F1229',
          300: '#0A0E27',
          400: '#080B1F',
          500: '#050817',
        },
      },
      backgroundImage: {
        'gradient-dark': 'linear-gradient(135deg, #0A0E27 0%, #1A1F3A 100%)',
        'gradient-primary': 'linear-gradient(135deg, #0066FF 0%, #00D9FF 100%)',
        'gradient-glow': 'radial-gradient(circle at center, rgba(0, 102, 255, 0.15) 0%, transparent 70%)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(0, 102, 255, 0.3)' },
          '100%': { boxShadow: '0 0 40px rgba(0, 102, 255, 0.6)' },
        },
      },
    },
  },
  plugins: [],
}
