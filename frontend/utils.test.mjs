// Guarda de maxOf/minOf. Rodar: node utils.test.mjs
// O ponto do exercicio e o array grande: e exatamente onde Math.max(...arr)
// falha, e onde nenhum teste curto teria pego.
import assert from 'node:assert/strict'
import { maxOf, minOf } from './src/utils.js'

// mesma semantica de Math.max/min para entradas pequenas
for (const caso of [[3, 1, 2], [-5, -1, -9], [0], [1.5, 1.4999]]) {
  assert.equal(maxOf(caso), Math.max(...caso), `maxOf ${caso}`)
  assert.equal(minOf(caso), Math.min(...caso), `minOf ${caso}`)
}

// semente participa da comparacao, como o argumento extra participava
assert.equal(minOf([3, 4], 0), Math.min(...[3, 4], 0))
assert.equal(maxOf([0.2, 0.3], 1), Math.max(...[0.2, 0.3], 1))
assert.equal(minOf([-1, 5], 0), -1)

// array vazio devolve a semente, igual a Math.max() sem argumentos
assert.equal(maxOf([]), -Infinity)
assert.equal(minOf([]), Infinity)
assert.equal(maxOf([], 7), 7)

// o caso que motivou o arquivo: 300k elementos derrubam o spread
const grande = new Float64Array(300_000)
for (let i = 0; i < grande.length; i++) grande[i] = i % 1000
assert.throws(() => Math.max(...grande), RangeError,
  'se o spread parou de estourar, este helper virou opcional')
assert.equal(maxOf(grande), 999)
assert.equal(minOf(grande), 0)

console.log('utils ok: 300k elementos sem estourar a pilha')
