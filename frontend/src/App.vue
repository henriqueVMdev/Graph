<template>
  <div class="min-h-screen bg-transparent text-gray-100 flex flex-col">
    <AppNav />
    <main class="flex-1 overflow-hidden">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import AppNav from '@/components/layout/AppNav.vue'
</script>
