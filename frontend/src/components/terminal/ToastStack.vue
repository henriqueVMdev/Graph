<template>
  <Teleport to="body">
    <!-- Alerta disparado precisa chegar em quem usa leitor de tela tambem.
         polite para nao cortar o que estiver sendo lido no momento. -->
    <div
      class="fixed bottom-4 right-4 z-[110] space-y-2 w-80 max-w-[calc(100vw-2rem)]"
      role="status"
      aria-live="polite"
      aria-relevant="additions"
      @mouseenter="pausado = true"
      @mouseleave="pausado = false"
      @focusin="pausado = true"
      @focusout="pausado = false"
    >
      <TransitionGroup name="toast">
        <div
          v-for="t in terminal.toasts"
          :key="t.id"
          class="relative rounded-xl border border-accent-yellow/50 bg-black/95
                 shadow-yellow-glow flex items-start"
        >
          <button
            type="button"
            class="flex-1 text-left px-4 py-3 rounded-xl"
            @click="abrirAlertas"
          >
            <span class="block text-sm font-semibold text-accent-yellow">{{ t.title }}</span>
            <span class="block text-xs text-gray-300 mt-0.5">{{ t.body }}</span>
          </button>
          <button
            type="button"
            class="fechar shrink-0 m-2 w-6 h-6 flex items-center justify-center rounded-md
                   text-gray-400 hover:text-gray-100 hover:bg-surface-600 transition-colors"
            :aria-label="`Dispensar alerta: ${t.title}`"
            @click="terminal.dismissToast(t.id)"
          >
            <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useTerminalStore } from '@/stores/terminal.js'

const terminal = useTerminalStore()
const router = useRouter()

const DURACAO = 8000
const pausado = ref(false)
const restante = new Map()   // id -> ms que faltam
let tick = null

// Um unico tick para toda a pilha em vez de um timer por toast: enquanto o
// ponteiro ou o foco estiver sobre a pilha, o relogio simplesmente nao anda.
function iniciarTick() {
  if (tick) return
  const PASSO = 250
  tick = setInterval(() => {
    if (pausado.value) return
    for (const t of terminal.toasts) {
      const ms = (restante.get(t.id) ?? DURACAO) - PASSO
      if (ms <= 0) { restante.delete(t.id); terminal.dismissToast(t.id) }
      else restante.set(t.id, ms)
    }
    if (!terminal.toasts.length) { clearInterval(tick); tick = null }
  }, PASSO)
}

watch(() => terminal.toasts.length, (n) => { if (n) iniciarTick() })
onBeforeUnmount(() => clearInterval(tick))

function abrirAlertas() {
  router.push('/alerts')
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(30px); }
.toast-leave-to { opacity: 0; transform: translateY(8px); }

@media (prefers-reduced-motion: reduce) {
  .toast-enter-active, .toast-leave-active { transition: opacity 0.25s ease; }
  .toast-enter-from, .toast-leave-to { transform: none; }
}

/* O X so aparece no hover/foco da pilha, mas nunca some para o teclado. */
.fechar:focus-visible { opacity: 1; }
</style>
