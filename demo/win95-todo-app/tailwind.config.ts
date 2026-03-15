import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        buttonBg: '#FFFFFF',
        buttonText: '#000000',
      },
      fontFamily: {
        sans: ['Tahoma', 'Verdana', 'ui-sans-serif', 'system-ui'],
      },
    },
  },
  plugins: [],
};

export default config;