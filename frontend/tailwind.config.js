/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
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
        // Quatro valores, quatro nomes. Antes eram sete chaves para quatro
        // cores: green-light, blue e yellow apontavam todas para #f5c518, o
        // que fazia escalas de tres niveis (bom / aceitavel / ruim) sairem
        // com dois niveis identicos na tela.
        //
        // Escala de avaliacao, do melhor para o pior:
        //   yellow    #f5c518  11.8:1  nivel forte, acao, destaque
        //   brass     #c9a227   7.9:1  nivel intermediario
        //   red-light #f87171   6.9:1  nivel fraco, valor negativo
        //   gray-400  #9ca3af   7.6:1  sem dado / sem julgamento
        // Ratios medidos sobre surface-700 (#0f0f0f).
        accent: {
          yellow: '#f5c518',
          brass: '#c9a227',
          red: '#dc2626',
          'red-light': '#f87171',
        },
        // O #6b7280 padrao do Tailwind da 3.96:1 sobre surface-700 e reprova
        // AA. Era a cor de texto mais usada do app. gray-600 (2.54:1) e
        // gray-700 (1.86:1) eram ilegiveis e foram absorvidos aqui: dois
        // niveis que se le em vez de quatro que nao se le.
        //   gray-400 #9ca3af  7.6:1  secundario
        //   gray-500 #858b99  5.6:1  terciario, hint, placeholder
        gray: {
          500: '#858b99',
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
