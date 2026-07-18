

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      colors: {
        primary: '#0D1117',
        secondary: '#161B22',
        accent: '#58A6FF',    // buttons and highlights
        success: '#2EA043',   // positive actions
        warning: '#D29922',   // warnings
        error: '#FF3860',     // errors
        neutral: '#C9D1D9',   // readable text
      },
    },
  },
  plugins: [],
}
export default config

