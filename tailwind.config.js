/** @type {import('tailwindcss').Config} */
module.exports = {
  // 1. Укажите пути к вашим файлам
  content: [
    './layouts/**/*.html',
    './content/**/*.md',
    './themes/**/layouts/**/*.html',
    './themes/**/content/**/*.md',
  ],
  
  // 2. Настройки темы
  theme: {
    container: {
      center: true,
      padding: '1rem',
    },
    
    // 3. Расширение базовой темы
    extend: {
      // Border radius должен быть здесь!
      borderRadius: {
        'sm': '0.125rem',
        'DEFAULT': '0.25rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem', // ← Вот rounded-xl!
        '2xl': '1rem',
        '3xl': '1.5rem',
        'full': '9999px',
      },
      
      // Другие настройки...
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        // ... добавьте остальные цвета
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
  
  // 4. Плагины
  plugins: [
    require('@tailwindcss/typography'),
    // require('daisyui') // Если используете DaisyUI
  ],
}