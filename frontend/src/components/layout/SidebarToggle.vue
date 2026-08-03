<template>
  <button
    type="button"
    :aria-expanded="open"
    :aria-controls="controls"
    :aria-label="open ? 'Recolher painel lateral' : 'Expandir painel lateral'"
    class="toggle absolute top-1/2 -translate-y-1/2 z-40 w-4 h-10 flex items-center
           justify-center rounded-r-md bg-surface-700/60 hover:bg-surface-600/80
           border-y border-r border-surface-500/50 text-gray-500 hover:text-gray-300
           transition-all duration-300"
    :style="open ? `left: calc(${width} - 1px)` : 'left: 0'"
    @click="$emit('update:open', !open)"
  >
    <svg class="w-2.5 h-2.5 transition-transform duration-300"
         :class="open ? '' : 'rotate-180'"
         fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
    </svg>
  </button>
</template>

<script setup>
defineProps({
  open: { type: Boolean, required: true },
  width: { type: String, default: '18rem' },
  controls: { type: String, default: 'workspace-sidebar' },
})
defineEmits(['update:open'])
</script>

<style scoped>
/* A barra visual continua com 16px de largura, que e o que o layout pede.
   O alvo de toque cresce por fora com um pseudo-elemento, chegando a
   32x56px sem mudar um pixel do desenho. WCAG 2.5.8 pede 24x24 no minimo. */
.toggle::before {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: inherit;
}
</style>
