// Envolve o callback de um setInterval para ele nao rodar com a aba escondida.
//
// Uso: setInterval(quandoVisivel(fetchWatch), 5000)
//
// De proposito nao registra listener de visibilitychange. Um listener global
// precisaria ser removido junto com o clearInterval, e os pontos que fazem
// polling dentro de componente limpam o timer no unmount sem saber do
// listener — o que faria a busca disparar depois do componente morrer. O
// preco de nao ter listener e que o dado volta defasado em no maximo um
// intervalo, o que para polls de 3 a 60 segundos e irrelevante.
//
// Nao use em poll que decide fim de tarefa (progresso de otimizacao, estado
// de job): la o tick precisa acontecer mesmo sem ninguem olhando.

export function quandoVisivel(fn) {
  return (...args) => {
    if (document.hidden) return
    return fn(...args)
  }
}
