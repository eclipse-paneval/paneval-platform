<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import {
  ElDescriptions,
  ElDescriptionsItem,
  ElPagination,
  ElRadio,
  ElRow,
  ElTable,
  ElTableColumn
} from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationImages } from '@/api/evaluations'
import type { EvaluationImage } from '@/api/evaluations/types'

const emit = defineEmits<{
  select: [value: string]
}>()

const currentRow = ref('')
const { t } = useI18n()
const paging = reactive({
  page: 1,
  pageSize: 10
})

const { data, refetch } = useQuery({
  queryKey: ['evaluation-images', () => paging.page],
  queryFn: () => getEvaluationImages(paging.page, paging.pageSize)
})

const selectedImage = computed<EvaluationImage | null>(() => {
  if (!currentRow.value) return null
  return JSON.parse(currentRow.value) as EvaluationImage
})

const handleCurrentChange = (value?: EvaluationImage) => {
  currentRow.value = value ? JSON.stringify(value) : ''
  emit('select', currentRow.value)
}

const formatDate = (value?: string | number) => {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
    .format(new Date(Number(value)))
    .replace(/\//g, '-')
}
</script>

<template>
  <div class="image-select">
    <ElTable
      class="mt-20px"
      :data="data?.items || []"
      highlight-current-row
      style="width: 100%"
      @current-change="handleCurrentChange"
    >
      <ElTableColumn width="55" align="center">
        <template #default="{ row }">
          <ElRadio v-model="currentRow" :label="JSON.stringify(row)">
            {{ '' }}
          </ElRadio>
        </template>
      </ElTableColumn>
      <ElTableColumn property="name" :label="t('evaluation.imageName')">
        <template #default="{ row }"> {{ `${row.name}:${row.tag}` }} </template>
      </ElTableColumn>
    </ElTable>
    <ElPagination
      v-model:current-page="paging.page"
      :page-size="paging.pageSize"
      size="small"
      layout="prev, pager, next"
      :total="data?.paging.total || 0"
      class="mt-4"
      hide-on-single-page
      @current-change="() => refetch()"
    />
    <ElRow v-if="selectedImage" class="mt-20px">
      <ElDescriptions
        class="w-full"
        :title="`${selectedImage.name}:${selectedImage.tag}`"
        :column="1"
        border
      >
        <ElDescriptionsItem :label="t('common.size')">{{
          selectedImage.imageSize
        }}</ElDescriptionsItem>
        <ElDescriptionsItem :label="t('common.createdAt')">
          {{ formatDate(selectedImage.createdTime) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="t('evaluation.imageIntro')">
          {{ selectedImage.desc }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="t('evaluation.adaptFrame')">
          {{ selectedImage.frameLabel }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="t('evaluation.imageTag')">
          {{ selectedImage.label }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="t('evaluation.applicableModel')">
          {{ selectedImage.processorLabel }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="t('evaluation.dockerfile')">
          {{ selectedImage.packageInfo }}
        </ElDescriptionsItem>
      </ElDescriptions>
    </ElRow>
  </div>
</template>
