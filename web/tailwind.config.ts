import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Ultrahuman glass UI - black and white
        uh: {
          black: '#000000',
          bg: '#0A0A0A',
          'bg-secondary': '#111111',
          glass: 'rgba(255, 255, 255, 0.05)',
          'glass-hover': 'rgba(255, 255, 255, 0.08)',
          'glass-border': 'rgba(255, 255, 255, 0.1)',
          'glass-strong': 'rgba(255, 255, 255, 0.12)',
          white: '#FFFFFF',
          'white-90': 'rgba(255, 255, 255, 0.9)',
          'white-70': 'rgba(255, 255, 255, 0.7)',
          'white-50': 'rgba(255, 255, 255, 0.5)',
          'white-30': 'rgba(255, 255, 255, 0.3)',
          'white-20': 'rgba(255, 255, 255, 0.2)',
          'white-10': 'rgba(255, 255, 255, 0.1)',
          success: '#4ADE80',
          warning: '#FBBF24',
          error: '#F87171',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
      },
    },
  },
  darkMode: 'class'
};

export default config;
