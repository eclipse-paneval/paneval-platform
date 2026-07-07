<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { ElPagination, ElRadio, ElTable, ElTableColumn } from 'element-plus'
import { reactive, ref, unref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationQueueResources } from '@/api/evaluations'
import type { EvaluationResource } from '@/api/evaluations/types'

const modelValue = defineModel<string>({ default: '' })

const props = defineProps<{
  id?: string | number
}>()

const currentRow = ref(modelValue.value)
const { t } = useI18n()
const paging = reactive({
  page: 1,
  pageSize: 100
})

const { data, isLoading, refetch } = useQuery({
  queryKey: ['evaluation-queue-resources', () => props.id, () => paging.page],
  enabled: () => Boolean(props.id),
  queryFn: () =>
    getEvaluationQueueResources({
      page: paging.page,
      pageSize: paging.pageSize,
      id: props.id || ''
    })
})

const handleCurrentChange = (value?: EvaluationResource) => {
  currentRow.value = value ? JSON.stringify(value) : ''
}

watch(
  () => currentRow.value,
  (value) => {
    modelValue.value = value
  }
)

watch(
  () => modelValue.value,
  (value) => {
    if (value === unref(currentRow)) return
    currentRow.value = value
  }
)

watch(
  () => props.id,
  () => {
    paging.page = 1
    currentRow.value = ''
    void refetch()
  }
)
</script>

<template>
  <div class="resource-table">
    <ElTable
      v-loading="isLoading"
      :data="data?.items || []"
      highlight-current-row
      style="width: 100%"
      size="small"
      stripe
      border
      flexible
      @current-change="handleCurrentChange"
    >
      <ElTableColumn label="" width="60" align="left">
        <template #default="{ row }">
          <ElRadio v-model="currentRow" :label="JSON.stringify(row)">
            {{ '' }}
          </ElRadio>
        </template>
      </ElTableColumn>
      <ElTableColumn property="acceleratorModel" label="GPU" />
      <ElTableColumn property="acceleratorCount" width="80" label="#GPUs" />
      <ElTableColumn property="cpuCores" width="100" label=" #CPU Cores" />
      <ElTableColumn property="memGib" width="100" :label="t('evaluationBatch.memoryG')" />
    </ElTable>
    <ElPagination
      v-model:current-page="paging.page"
      :page-size="paging.pageSize"
      size="small"
      background
      layout="prev, pager, next"
      :total="data?.paging.total || 0"
      class="mt-4"
      hide-on-single-page
      @current-change="() => refetch()"
    />
  </div>
</template>

<style scoped>
.resource-table {
  width: 100%;
}
</style>
