/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './layouts/**/*.html',
    './content/**/*.md',
  ],

  darkMode: 'class',

  theme: {
    container: {
      center: true,
      padding: '1rem',
    },

    extend: {
      borderRadius: {
        'sm': '0.125rem',
        'DEFAULT': '0.25rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
        'full': '9999px',
      },
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
      },
      typography: {
        DEFAULT: {
          css: {
            blockquote: {
              color: 'var(--tw-prose-body)',
              fontWeight: 'normal',
              fontStyle: 'normal',
            },
            p: {
              wordBreak: 'break-word',
            },
            pre: null,
            'pre code': null,
            'pre code::before': null,
            'pre code::after': null,
            code: null,
            'code::before': null,
            'code::after': null,
          },
        },
        quoteless: {
          css: {
            'blockquote p:first-of-type::before': { content: 'none' },
            'blockquote p:first-of-type::after': { content: 'none' },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}