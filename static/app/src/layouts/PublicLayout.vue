<script setup lang="ts">
import AppTopNav from '@/components/AppTopNav.vue'
</script>

<template>
  <div class="min-h-screen bg-(--color-page) text-(--color-text)">
    <AppTopNav />
    <main class="min-h-screen">
      <RouterView />
    </main>
  </div>
</template>
