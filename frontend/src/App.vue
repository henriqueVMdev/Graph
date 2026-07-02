<template>
  <div class="min-h-screen bg-transparent text-gray-100 flex flex-col">
    <AppNav @open-cmd="cmdLine?.show()" />
    <main class="flex-1 overflow-hidden">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <CommandLine ref="cmdLine" />
    <ToastStack />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppNav from '@/components/layout/AppNav.vue'
import CommandLine from '@/components/terminal/CommandLine.vue'
import ToastStack from '@/components/terminal/ToastStack.vue'

const cmdLine = ref(null)
</script>
