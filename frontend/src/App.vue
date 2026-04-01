<template>
  <div class="min-h-screen bg-surface-900 text-gray-100 flex flex-col">
    <AppNav />
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import AppNav from '@/components/layout/AppNav.vue'
</script>
