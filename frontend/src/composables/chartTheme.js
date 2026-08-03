// Tema unico dos graficos.
//
// Antes: 331 hex espalhados por 25 arquivos, com quatro valores diferentes
// para a mesma linha de zero ('#445', '#333', '#2a2a2a', '#222') e dois para
// o mesmo fundo ('#000000' e '#000'). Cada grafico redecidia o proprio
// cinza, entao nenhum ficava igual ao vizinho.
//
// Os valores espelham os tokens do tailwind.config.js. Plotly nao le CSS
// custom properties, entao a duplicacao e inevitavel; o que da para evitar e
// ela estar em 25 lugares em vez de um.

export const TEMA = {
  fundoPapel: '#000000',   // surface-900
  fundoPlot: '#080808',    // surface-800
  grade: '#1e1e1e',        // surface-500
  eixo: '#2a2a2a',         // surface-400
  linhaZero: '#2a2a2a',    // surface-400: um valor, nao quatro
  texto: '#d1d5db',        // gray-300
  textoFraco: '#9ca3af',   // gray-400, o mesmo piso de contraste do app
  destaque: '#f5c518',     // accent-yellow
  intermediario: '#c9a227',// accent-brass
  negativo: '#f87171',     // accent-red-light
}

// Serie categorica para graficos multi-linha. Ouro primeiro: a serie
// principal e sempre a que o produto quer que voce olhe.
export const SERIE = [
  TEMA.destaque, TEMA.intermediario, TEMA.negativo,
  '#8ab4f8', '#a78bfa', '#5eead4', '#fb923c',
]

// Direcao de preco. Era teal/vermelho do TradingView; agora acompanha a
// mesma decisao do resto do app, onde ganho e ouro.
//
// Consequencia: a media rapida era ouro e passaria a sumir dentro do candle
// de alta. Ela virou neutra clara, que e o que uma linha sobreposta deve
// ser — o candle e o dado, a media e leitura sobre ele.
export const DIRECAO = {
  alta: TEMA.destaque,
  baixa: TEMA.negativo,
  altaBorda: TEMA.intermediario,   // contorno do marcador de entrada long
  baixaBorda: '#dc2626',           // accent-red
  mediaRapida: TEMA.texto,
  mediaLenta: SERIE[3],
}

// Versoes translucidas, para preenchimento e barra de volume.
export const rgbaAlta = (a) => `rgba(245, 197, 24, ${a})`
export const rgbaBaixa = (a) => `rgba(248, 113, 113, ${a})`

// Paleta de estudos sobrepostos ao candle. So tons frios: o candle e quente
// (ouro e vermelho), entao a linha de estudo precisa recuar para o fundo em
// vez de disputar atencao com o preco. Verde e laranja saem por isso, nao
// por serem cores erradas.
export const ESTUDOS = [
  '#8ab4f8', '#5eead4', '#a78bfa', '#f472b6', '#93c5fd', '#67e8f9',
]

export const FONTE = { family: 'Inter, system-ui, sans-serif', size: 12, color: TEMA.texto }

// Layout base. Passe o que for especifico do grafico como override.
export function layoutBase(extra = {}) {
  return {
    paper_bgcolor: TEMA.fundoPapel,
    plot_bgcolor: TEMA.fundoPlot,
    font: { ...FONTE },
    margin: { t: 16, r: 24, b: 36, l: 48 },
    hoverlabel: {
      bgcolor: '#0f0f0f', bordercolor: TEMA.destaque, font: { color: TEMA.texto },
    },
    legend: {
      bgcolor: 'transparent', font: { size: 11, color: TEMA.textoFraco },
      orientation: 'h', x: 0, y: 1.06,
    },
    ...extra,
  }
}

// Eixo base, ja com a grade e a linha de zero unificadas.
export function eixoBase(extra = {}) {
  return {
    gridcolor: TEMA.grade,
    linecolor: TEMA.eixo,
    zerolinecolor: TEMA.linhaZero,
    tickfont: { color: TEMA.textoFraco, size: 11 },
    ...extra,
  }
}
