<script setup lang="ts">
import {
  ElDescriptions,
  ElDescriptionsItem,
  ElPagination,
  ElRow,
  ElTable,
  ElTableColumn
} from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationImages } from '@/api/evaluations'
import type { EvaluationImage } from '@/api/evaluations/types'

const FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
})

const tableData = ref<EvaluationImage[]>([])
const currentRow = ref<EvaluationImage | null>(null)
const isLoading = ref(false)
const { t } = useI18n()
const paging = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const currentTitle = computed(() => {
  return currentRow.value ? `${currentRow.value.name}:${currentRow.value.tag}` : ''
})

const formatTime = (value?: string | number) => {
  if (!value) {
    return '-'
  }

  const date =
    typeof value === 'number' || /^\d+$/.test(String(value))
      ? new Date(Number(value))
      : new Date(value)

  return FORMATTER.format(date).replace(/\//g, '-')
}

const loadImages = async () => {
  isLoading.value = true
  try {
    const response = await getEvaluationImages(paging.page, paging.pageSize)
    tableData.value = response.items
    paging.page = response.paging.page
    paging.pageSize = response.paging.pageSize
    paging.total = response.paging.total
  } finally {
    isLoading.value = false
  }
}

const handleCurrentChange = (row: EvaluationImage | null) => {
  currentRow.value = row
}

const handlePageChange = (page: number) => {
  paging.page = page
  void loadImages()
}

onMounted(() => {
  void loadImages()
})
</script>

<template>
  <div class="preset-image">
    <ElTable
      v-loading="isLoading"
      :data="tableData"
      highlight-current-row
      border
      stripe
      show-overflow-tooltip
      style="width: 100%"
      @current-change="handleCurrentChange"
    >
      <ElTableColumn :label="t('images.nameTag')" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ `${row.name}:${row.tag}` }}</template>
      </ElTableColumn>
      <ElTableColumn
        prop="desc"
        :label="t('common.description')"
        min-width="180"
        show-overflow-tooltip
      />
      <ElTableColumn
        prop="frameLabel"
        :label="t('images.framework')"
        width="130"
        show-overflow-tooltip
      />
      <ElTableColumn
        prop="processorLabel"
        :label="t('images.applicable')"
        min-width="150"
        show-overflow-tooltip
      />
      <ElTableColumn prop="label" :label="t('images.tags')" min-width="120" show-overflow-tooltip />
      <ElTableColumn prop="imageSize" :label="t('common.size')" width="120" show-overflow-tooltip />
      <ElTableColumn :label="t('common.created')" width="180">
        <template #default="{ row }">{{ formatTime(row.createdTime) }}</template>
      </ElTableColumn>
    </ElTable>

    <div class="mt-4 flex justify-end">
      <ElPagination
        v-model:current-page="paging.page"
        :page-size="paging.pageSize"
        small
        layout="prev, pager, next"
        :total="paging.total"
        @current-change="handlePageChange"
      />
    </div>

    <ElRow v-if="currentRow" class="mt-5">
      <ElDescriptions class="w-full" :title="currentTitle" :column="1" border>
        <ElDescriptionsItem :label="t('common.size')">{{
          currentRow.imageSize || '-'
        }}</ElDescriptionsItem>
        <ElDescriptionsItem :label="t('common.created')">{{
          formatTime(currentRow.createdTime)
        }}</ElDescriptionsItem>
        <ElDescriptionsItem :label="t('common.description')">{{
          currentRow.desc || '-'
        }}</ElDescriptionsItem>
        <ElDescriptionsItem :label="t('images.framework')">{{
          currentRow.frameLabel || '-'
        }}</ElDescriptionsItem>
        <ElDescriptionsItem :label="t('images.tags')">{{
          currentRow.label || '-'
        }}</ElDescriptionsItem>
        <ElDescriptionsItem :label="t('images.applicable')">{{
          currentRow.processorLabel || '-'
        }}</ElDescriptionsItem>
        <ElDescriptionsItem :label="t('images.dockerfile')">
          <pre class="dockerfile-preview">{{ currentRow.packageInfo || '-' }}</pre>
        </ElDescriptionsItem>
      </ElDescriptions>
    </ElRow>
  </div>
</template>

<style scoped>
.dockerfile-preview {
  max-height: 320px;
  overflow: auto;
  margin: 0;
  border-radius: 6px;
  background: #f6f8fa;
  padding: 12px;
  white-space: pre-wrap;
}
</style>
