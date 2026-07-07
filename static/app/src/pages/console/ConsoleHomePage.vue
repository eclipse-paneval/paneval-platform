<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import { getEvaluations } from '@/api/evaluations'

const { data, isLoading } = useQuery({
  queryKey: ['evaluation-overview'],
  queryFn: () => getEvaluations({ pageIndex: 1, pageSize: 1 })
})

const overviewCards = computed(() => [
  ['Total', data.value?.total ?? 0],
  ['Loaded page', data.value?.list.length ?? 0],
  ['Staff actions', 'Enabled']
])
</script>

<template>
  <section class="mx-auto max-w-6xl">
    <div class="mb-6">
      <h2 class="text-2xl font-semibold tracking-[0]">Overview</h2>
      <p class="mt-2 text-sm text-(--color-text-muted)">
        Evaluation console backed by compatible APIs.
      </p>
    </div>
    <div class="grid gap-4 md:grid-cols-3">
      <div
        v-for="item in overviewCards"
        :key="item[0]"
        class="rounded-lg border border-(--color-border) bg-white p-5"
      >
        <p class="text-sm text-(--color-text-muted)">{{ item[0] }}</p>
        <p class="mt-3 text-3xl font-semibold">{{ isLoading ? '-' : item[1] }}</p>
      </div>
    </div>
  </section>
</template>
