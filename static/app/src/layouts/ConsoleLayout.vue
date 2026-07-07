<script setup lang="ts">
import AppTopNav from '@/components/AppTopNav.vue'
</script>

<template>
  <div class="min-h-screen bg-(--color-page) pt-16 text-(--color-text)">
    <AppTopNav />

    <main class="min-w-0 px-6 py-6 lg:px-10">
      <RouterView v-slot="{ Component, route }">
        <KeepAlive>
          <component :is="Component" v-if="route.meta.keepAlive" />
        </KeepAlive>
        <component :is="Component" v-if="!route.meta.keepAlive" />
      </RouterView>
    </main>
  </div>
</template>
