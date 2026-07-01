<template>
  <div class="w-full h-full">
    <TvChart v-if="store.renderer === 'tv'" class="w-full h-full" />
    <PlotlyChart v-else class="w-full h-full" />
  </div>
</template>

<script setup>
import { useChartStore } from '@/stores/chart.js'
import TvChart from './TvChart.vue'
import PlotlyChart from './PlotlyChart.vue'

const store = useChartStore()
</script>
