// Minimo e maximo sem espalhar o array nos argumentos.
//
// Math.max(...serie) passa cada elemento como um argumento; acima de mais ou
// menos 124 mil argumentos o V8 estoura com RangeError. Series de candles
// intradiarias de varios anos passam disso com folga, e o erro so aparece no
// backtest longo do usuario, nunca no teste curto.
//
// O segundo parametro e uma semente opcional, para o caso
// Math.min(...vals, 0) onde o zero participa da comparacao.

export function maxOf(arr, semente = -Infinity) {
  let m = semente
  for (const v of arr) if (v > m) m = v
  return m
}

export function minOf(arr, semente = Infinity) {
  let m = semente
  for (const v of arr) if (v < m) m = v
  return m
}
