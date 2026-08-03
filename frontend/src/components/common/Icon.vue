<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
    class="shrink-0 inline-block"
    v-html="TRACOS[name] || ''"
  />
</template>

<script setup>
// Mesmo traco dos icones que ja viviam no AppNav: viewBox 24, contorno de
// 2px, cantos e pontas redondos. Isso existe porque a UI usava emoji no
// lugar de icone — e emoji vem colorido, muda de desenho a cada sistema
// operacional, e nao herda currentColor.
defineProps({ name: { type: String, required: true } })

const TRACOS = {
  fechar: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  aviso: '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  ok: '<polyline points="20 6 9 17 4 12"/>',
  seta: '<polyline points="6 9 12 15 18 9"/>',
  executar: '<polygon points="6 3 20 12 6 21 6 3"/>',
  raio: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
  olho: '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/>',
  ficha: '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
    + '<rect x="8" y="2" width="8" height="4" rx="1"/>',
  livro: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
  relogio: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  alta: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
  onda: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
  coracao: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21.2l7.8-7.8 1-1.1a5.5 5.5 0 0 0 0-7.7z"/>',
  externo: '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/>',
  bloqueado: '<circle cx="12" cy="12" r="10"/><line x1="4.9" y1="4.9" x2="19.1" y2="19.1"/>',
  engrenagem: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2v2.6M12 19.4V22M4.2 4.2l1.9 1.9M17.9 17.9l1.9 1.9'
    + 'M2 12h2.6M19.4 12H22M4.2 19.8l1.9-1.9M17.9 6.1l1.9-1.9"/>',
  recarregar: '<polyline points="23 4 23 10 17 10"/><path d="M20.5 15a9 9 0 1 1-2.1-9.4L23 10"/>',
  grade: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>'
    + '<rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
  ideia: '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"/>',
  chama: '<path d="M12 2c1.2 3.8-1.8 5-1.8 8a3.8 3.8 0 0 0 7.6 0c0-1-.4-2-1-2.9 2 1.6 3.2 3.9 3.2 6.4a8 8 0 0 1-16 0C4 9 7.2 5.6 12 2z"/>',
  brilho: '<path d="M11 3l1.7 4.3L17 9l-4.3 1.7L11 15l-1.7-4.3L5 9l4.3-1.7z"/>'
    + '<path d="M18.5 14l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>',
  instituicao: '<path d="M3 21h18"/><path d="M4 10h16"/><path d="M6 10v11M10 10v11M14 10v11M18 10v11"/><path d="M12 3l9 5H3z"/>',
}
</script>
