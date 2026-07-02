<template>
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-[110] space-y-2 w-80">
      <TransitionGroup name="toast">
        <div
          v-for="t in terminal.toasts"
          :key="t.id"
          class="rounded-xl border border-accent-yellow/50 bg-black/95 shadow-yellow-glow
                 px-4 py-3 cursor-pointer"
          @click="goAlerts"
        >
          <div class="text-sm font-semibold text-accent-yellow">{{ t.title }}</div>
          <div class="text-xs text-gray-300 mt-0.5">{{ t.body }}</div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useTerminalStore } from '@/stores/terminal.js'

const terminal = useTerminalStore()
const router = useRouter()

function goAlerts() {
  router.push('/alerts')
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(30px); }
.toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
