<template>
  <div ref="chartEl" class="w-full" style="min-height: 400px;"></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { initChart, updateChart, purgeChart, onPointClick } from '@/composables/useCharts.js'

const props = defineProps({
  chartJson: { type: Object, default: null },
})

const emit = defineEmits(['point-clicked'])
const chartEl = ref(null)
let initialized = false

async function render(json) {
  if (!json || !chartEl.value) return
  if (!initialized) {
    await initChart(chartEl.value, json, { height: 420 })
    onPointClick(chartEl.value, ({ rank }) => emit('point-clicked', rank))
    initialized = true
  } else {
    await updateChart(chartEl.value, json, { height: 420 })
  }
}

onMounted(() => {
  if (props.chartJson) render(props.chartJson)
})

watch(() => props.chartJson, (newJson) => {
  if (newJson) render(newJson)
})

async function resize() {
  if (!chartEl.value) return
  const Plotly = (await import('plotly.js-dist-min')).default
  Plotly.Plots.resize(chartEl.value)
}

defineExpose({ resize })

onBeforeUnmount(async () => {
  await purgeChart(chartEl.value)
  initialized = false
})
</script>
