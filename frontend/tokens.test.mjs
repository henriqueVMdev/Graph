// Guarda contra o bug que motivou este arquivo: accent.green-light e
// accent.yellow apontavam para o mesmo #f5c518, entao escalas de tres
// niveis (bom / aceitavel / ruim) saiam com dois niveis identicos na tela.
// Rodar: node tokens.test.mjs
import assert from 'node:assert/strict'
import cfg from './tailwind.config.js'

const accent = cfg.theme.extend.colors.accent

// Nenhum hex pode ter dois nomes: e assim que uma escala colapsa sem aviso.
const porHex = {}
for (const [nome, hex] of Object.entries(accent)) {
  const k = hex.toLowerCase()
  assert.equal(porHex[k], undefined,
    `accent.${nome} e accent.${porHex[k]} sao ambos ${hex} - a escala colapsa na tela`)
  porHex[k] = nome
}

// Os tres niveis usados pelos metric cards precisam ser visualmente distintos.
const escala = ['yellow', 'brass', 'red-light']
for (const nome of escala) {
  assert.ok(accent[nome], `accent.${nome} sumiu - a escala de avaliacao depende dele`)
}

// Contraste minimo AA (4.5:1) de cada nivel sobre surface-700, o fundo dos cards.
const lin = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }
const lum = (hex) => {
  const n = parseInt(hex.slice(1), 16)
  return 0.2126 * lin(n >> 16 & 255) + 0.7152 * lin(n >> 8 & 255) + 0.0722 * lin(n & 255)
}
const contraste = (a, b) => {
  const [x, y] = [lum(a), lum(b)]
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)
}

const fundo = cfg.theme.extend.colors.surface[700]
for (const nome of escala) {
  const r = contraste(accent[nome], fundo)
  assert.ok(r >= 4.5, `accent.${nome} tem ${r.toFixed(2)}:1 sobre surface-700 - abaixo de AA`)
}

// Niveis vizinhos precisam ser separaveis por algum canal: luminancia OU
// matiz. yellow e brass sao o mesmo ouro, entao so a luminancia os separa;
// brass e red-light tem luminancia quase igual e se separam pela matiz.
// Exigir os dois reprovaria um par que o olho distingue sem esforco.
const matiz = (hex) => {
  const n = parseInt(hex.slice(1), 16)
  const [r, g, b] = [n >> 16 & 255, n >> 8 & 255, n & 255].map((v) => v / 255)
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min
  if (d === 0) return 0
  const h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4
  return (h * 60 + 360) % 360
}
const distMatiz = (a, b) => {
  const d = Math.abs(matiz(a) - matiz(b)) % 360
  return d > 180 ? 360 - d : d
}

for (let i = 0; i < escala.length - 1; i++) {
  const [a, b] = [accent[escala[i]], accent[escala[i + 1]]]
  const lumR = contraste(a, b)
  const hueD = distMatiz(a, b)
  assert.ok(lumR >= 1.25 || hueD >= 30,
    `accent.${escala[i]} e accent.${escala[i + 1]}: ${lumR.toFixed(2)}:1 de luminancia e `
    + `${hueD.toFixed(0)} graus de matiz - indistinguiveis lado a lado`)
}

// Rampa de cinza de texto: todo nivel usado como texto precisa passar AA
// sobre surface-600, que e a superficie mais clara em que ele aparece.
const cinza = { 400: '#9ca3af', 500: cfg.theme.extend.colors.gray[500] }
const fundoClaro = cfg.theme.extend.colors.surface[600]
for (const [nivel, hex] of Object.entries(cinza)) {
  const r = contraste(hex, fundoClaro)
  assert.ok(r >= 4.5, `gray-${nivel} tem ${r.toFixed(2)}:1 sobre surface-600 - abaixo de AA`)
}
// E precisam ser degraus distintos, senao a hierarquia some.
const degrau = contraste(cinza[400], cinza[500])
assert.ok(degrau >= 1.25, `gray-400 e gray-500 a ${degrau.toFixed(2)}:1 - degrau fraco demais`)

console.log('tokens ok:', Object.entries(accent).map(([k, v]) => `${k}=${v}`).join(' '))
console.log('cinzas ok:', Object.entries(cinza).map(([k, v]) => `gray-${k}=${v}`).join(' '))
