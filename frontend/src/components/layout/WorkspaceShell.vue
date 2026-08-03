<template>
  <div class="flex h-[calc(100dvh-3.5rem)] overflow-hidden relative">

    <!-- Fundo escuro so no modo gaveta, para o toque fora fechar o painel -->
    <Transition name="scrim">
      <div
        v-if="open"
        class="fixed inset-x-0 bottom-0 top-14 z-30 bg-black/60 lg:hidden"
        @click="open = false"
      />
    </Transition>

    <!-- Abaixo de lg o painel e fixo e flutua sobre o conteudo; a partir de lg
         volta para o fluxo e empurra o conteudo, como era antes. A mesma
         animacao de largura serve aos dois casos. -->
    <div
      id="workspace-sidebar"
      class="shrink-0 overflow-hidden transition-[width] duration-300
             fixed bottom-0 left-0 top-14 z-30
             lg:static lg:top-auto lg:z-auto"
      :style="{ width: open ? width : '0' }"
    >
      <slot name="sidebar" />
    </div>

    <SidebarToggle v-model:open="open" :width="width" controls="workspace-sidebar" />

    <slot />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import SidebarToggle from './SidebarToggle.vue'

const props = defineProps({
  width: { type: String, default: '18rem' },
  // Em telas estreitas o painel comeca fechado: 288px sobre 390px de viewport
  // nao deixava conteudo utilizavel.
  startOpen: { type: Boolean, default: true },
})

const open = ref(props.startOpen && !window.matchMedia('(max-width: 1023px)').matches)

// Plotly e lightweight-charts so remedem no evento de resize; sem isso o
// grafico fica com a largura antiga ate a proxima interacao.
watch(open, () => {
  setTimeout(() => window.dispatchEvent(new Event('resize')), 310)
})

defineExpose({ open })
</script>

<style scoped>
.scrim-enter-active,
.scrim-leave-active { transition: opacity 0.2s ease; }
.scrim-enter-from,
.scrim-leave-to { opacity: 0; }
</style>
