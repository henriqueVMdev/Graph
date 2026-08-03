<template>
  <span ref="raiz" class="relative inline-flex align-middle">
    <button
      type="button"
      class="gatilho"
      :aria-expanded="aberto"
      :aria-controls="idPainel"
      :aria-label="`Ajuda sobre ${rotulo}`"
      @click.stop="aberto = !aberto"
    >?</button>

    <!-- v-show, nao v-if: o aria-controls precisa resolver mesmo fechado -->
    <span
      v-show="aberto"
      :id="idPainel"
      ref="painel"
      role="note"
      class="painel"
      :class="ancora === 'direita' ? 'ancora-direita' : 'ancora-esquerda'"
    >
      <slot>{{ texto }}</slot>
    </span>
  </span>
</template>

<script setup>
import { ref, useId, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

const props = defineProps({
  // Aparece no nome acessivel do botao: "Ajuda sobre Sharpe".
  rotulo: { type: String, required: true },
  texto: { type: String, default: '' },
})

const idPainel = `ajuda-${useId()}`
const aberto = ref(false)
const raiz = ref(null)
const painel = ref(null)
const ancora = ref('esquerda')

// Perto da borda direita o painel sairia da tela; ancora pelo outro lado.
watch(aberto, async (v) => {
  if (!v) return
  await nextTick()
  const r = raiz.value?.getBoundingClientRect()
  if (r) ancora.value = r.left > window.innerWidth - 280 ? 'direita' : 'esquerda'
})

function foraDaqui(e) {
  if (aberto.value && raiz.value && !raiz.value.contains(e.target)) aberto.value = false
}
function aoTeclar(e) {
  if (e.key !== 'Escape' || !aberto.value) return
  aberto.value = false
  raiz.value?.querySelector('button')?.focus()
}

onMounted(() => {
  window.addEventListener('click', foraDaqui)
  window.addEventListener('keydown', aoTeclar)
})
onBeforeUnmount(() => {
  window.removeEventListener('click', foraDaqui)
  window.removeEventListener('keydown', aoTeclar)
})
</script>

<style scoped>
/* O circulo continua com 15px, que e o que a grade densa comporta. A area
   de toque cresce por fora com o pseudo-elemento, como no resto do app. */
.gatilho {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 15px;
  height: 15px;
  margin-left: 3px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  border-radius: 9999px;
  border: 1px solid rgba(156, 163, 175, 0.35);
  color: rgba(156, 163, 175, 0.75);
  transition: color 0.12s ease, border-color 0.12s ease;
}
.gatilho::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 24px;
  height: 24px;
  transform: translate(-50%, -50%);
}
.gatilho:hover,
.gatilho[aria-expanded='true'] {
  color: #f5c518;
  border-color: rgba(245, 197, 24, 0.55);
}

.painel {
  position: absolute;
  top: calc(100% + 6px);
  z-index: 60;
  width: 15rem;
  padding: 0.5rem 0.625rem;
  border-radius: 0.5rem;
  border: 1px solid #2a2a2a;
  background: #0f0f0f;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  font-size: 11px;
  font-weight: 400;
  line-height: 1.45;
  text-align: left;
  text-transform: none;
  letter-spacing: normal;
  color: #d1d5db;
  white-space: normal;
}
.ancora-esquerda { left: 0; }
.ancora-direita { right: 0; }
</style>
