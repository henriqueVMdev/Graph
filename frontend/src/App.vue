<template>
  <div class="min-h-screen bg-transparent text-gray-100 flex flex-col">
    <!-- Sem isso o teclado atravessa os seis grupos da nav a cada troca de
         rota. href real pela semantica, mas o salto e feito no script: deixar
         o browser navegar poluiria o historico com #conteudo. -->
    <a
      href="#conteudo"
      class="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50
             focus:rounded-lg focus:bg-accent-yellow focus:px-4 focus:py-2
             focus:text-sm focus:font-semibold focus:text-black"
      @click.prevent="pularParaConteudo"
    >Pular para o conteúdo</a>

    <AppNav @open-cmd="cmdLine?.show()" />
    <main id="conteudo" ref="conteudo" tabindex="-1" class="flex-1 overflow-hidden outline-none">
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
const conteudo = ref(null)

function pularParaConteudo() {
  conteudo.value?.focus()
}
</script>
