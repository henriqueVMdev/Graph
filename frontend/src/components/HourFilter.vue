<template>
  <div class="sidebar-section">
    <label class="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        :checked="params.hour_filter"
        @change="params.hour_filter = $event.target.checked"
        class="w-3.5 h-3.5 accent-accent-yellow"
      />
      <span class="sidebar-section-title mb-0">Horário de Operação</span>
    </label>

    <template v-if="params.hour_filter">
      <p class="text-[10px] text-gray-500 mt-2 mb-2">
        Só abre posição nas horas marcadas (horário de Brasília). Vale para timeframes intradiários.
      </p>

      <div class="flex gap-2 mb-2">
        <button
          @click="setAll(true)"
          class="flex-1 py-1 text-[10px] rounded bg-surface-600 text-gray-400 border border-surface-500 hover:text-gray-200"
        >Todas</button>
        <button
          @click="setAll(false)"
          class="flex-1 py-1 text-[10px] rounded bg-surface-600 text-gray-400 border border-surface-500 hover:text-gray-200"
        >Nenhuma</button>
      </div>

      <div class="grid grid-cols-6 gap-1">
        <button
          v-for="h in hours"
          :key="h"
          @click="toggleHour(h)"
          class="py-1 text-[10px] rounded font-medium transition-colors"
          :class="isActive(h)
            ? 'bg-accent-yellow/25 text-accent-yellow border border-accent-yellow/50'
            : 'bg-surface-600 text-gray-500 border border-surface-500'"
        >{{ String(h).padStart(2, '0') }}</button>
      </div>

      <p class="text-[10px] text-gray-600 mt-2">
        {{ (params.allowed_hours || []).length }} de 24 horas liberadas
      </p>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  // Objeto reativo de params (ex.: store.params) com hour_filter / allowed_hours.
  params: { type: Object, required: true },
})

const hours = Array.from({ length: 24 }, (_, i) => i)

function isActive(h) {
  return (props.params.allowed_hours || []).includes(h)
}

function toggleHour(h) {
  if (!Array.isArray(props.params.allowed_hours)) props.params.allowed_hours = []
  const arr = props.params.allowed_hours
  const idx = arr.indexOf(h)
  if (idx === -1) arr.push(h)
  else arr.splice(idx, 1)
}

function setAll(on) {
  props.params.allowed_hours = on ? [...hours] : []
}
</script>
