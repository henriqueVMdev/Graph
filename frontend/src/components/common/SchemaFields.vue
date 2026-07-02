<template>
  <div v-for="section in schema" :key="section.title" class="mb-4">
    <h4 class="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-2">
      {{ section.title }}
    </h4>
    <div class="space-y-2">
      <template v-for="field in section.fields" :key="field.key">
        <div
          v-show="(!field.show_if || params[field.show_if]) && !hidden.includes(field.key)"
          class="flex items-center justify-between gap-2"
        >
          <label class="text-xs text-gray-400 shrink-0">{{ field.label }}</label>

          <input
            v-if="field.type === 'checkbox'"
            type="checkbox"
            :checked="!!params[field.key]"
            @change="params[field.key] = $event.target.checked"
            class="accent-yellow-400 w-4 h-4"
          />

          <select
            v-else-if="field.type === 'select'"
            :value="params[field.key]"
            @change="params[field.key] = $event.target.value"
            class="bg-surface-600 border border-surface-400 rounded-lg text-xs text-gray-100 px-2 py-1.5 w-36"
          >
            <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>

          <div v-else class="w-36">
            <NumInput
              :model-value="Number(params[field.key] ?? field.default ?? 0)"
              :min="field.min"
              :max="field.max"
              :step="field.step || 1"
              @update:model-value="params[field.key] = $event"
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
// Renderização genérica do CONFIG_SCHEMA das estratégias (mesmo padrão
// inline de BacktestSidebar/PropChallengeSidebar, extraído para reuso).
// `params` é mutado diretamente (objeto reativo do chamador).
import NumInput from '@/components/NumInput.vue'

defineProps({
  schema: { type: Array, default: () => [] },
  params: { type: Object, required: true },
  hidden: { type: Array, default: () => [] },
})
</script>
