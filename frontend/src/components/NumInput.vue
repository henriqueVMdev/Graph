<template>
  <div
    class="flex rounded-lg border overflow-hidden transition-colors duration-150"
    :class="focused
      ? 'border-accent-yellow/60 ring-1 ring-accent-yellow bg-surface-600'
      : 'border-surface-400 bg-surface-600 hover:border-surface-300'"
  >
    <button
      type="button"
      @click="decrement"
      class="px-2.5 text-gray-500 hover:text-accent-yellow hover:bg-surface-500 transition-colors select-none border-r border-surface-400 text-base leading-none"
      tabindex="-1"
    >−</button>

    <input
      type="number"
      :value="modelValue"
      :min="min"
      :max="max"
      :step="step"
      @focus="focused = true"
      @blur="onBlur"
      @change="onChange"
      class="flex-1 bg-transparent text-center text-gray-100 text-xs focus:outline-none min-w-0 py-1.5 px-1"
    />

    <button
      type="button"
      @click="increment"
      class="px-2.5 text-gray-500 hover:text-accent-yellow hover:bg-surface-500 transition-colors select-none border-l border-surface-400 text-base leading-none"
      tabindex="-1"
    >+</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 0 },
  min: { type: Number, default: -Infinity },
  max: { type: Number, default: Infinity },
  step: { type: Number, default: 1 },
})

const emit = defineEmits(['update:modelValue', 'change'])
const focused = ref(false)

function decimals() {
  const s = String(props.step ?? 1)
  const dot = s.indexOf('.')
  return dot >= 0 ? s.length - dot - 1 : 0
}

function round(val) {
  const d = decimals()
  return Math.round(val * 10 ** d) / 10 ** d
}

function clamp(val) {
  const mn = props.min ?? -Infinity
  const mx = props.max ?? Infinity
  return Math.min(Math.max(val, mn), mx)
}

function emit_val(val) {
  const v = clamp(round(val))
  emit('update:modelValue', v)
  emit('change', v)
}

function increment() {
  emit_val((props.modelValue ?? 0) + (props.step ?? 1))
}

function decrement() {
  emit_val((props.modelValue ?? 0) - (props.step ?? 1))
}

function onChange(e) {
  const val = parseFloat(e.target.value)
  if (!isNaN(val)) emit_val(val)
}

function onBlur() {
  focused.value = false
}
</script>
