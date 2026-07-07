<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import {
  ElButton,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElPagination,
  ElRadio,
  ElTable,
  ElTableColumn,
  ElText
} from 'element-plus'
import { computed, ref } from 'vue'
import { getCustomImages } from '@/api/evaluations'
import type { EvaluationImage } from '@/api/evaluations/types'
import { evalText } from '../evaluationFormLabels'

const emit = defineEmits<{
  select: [value: string]
}>()

const currentRow = ref('')
const page = ref(1)
const pageSize = ref(10)

const { data, isLoading } = useQuery({
  queryKey: computed(() => ['custom-images', page.value, pageSize.value]),
  queryFn: () => getCustomImages({ page: page.value, pageSize: pageSize.value })
})

const tableData = computed(() => data.value?.results || [])
const total = computed(() => data.value?.count || 0)

const curImage = computed<EvaluationImage | null>(() => {
  if (!currentRow.value) {
    return null
  }

  return JSON.parse(currentRow.value) as EvaluationImage
})

const dockerfileText = computed(() => curImage.value?.dockerfile || '')

const imageRegistryUrl = (image: EvaluationImage) =>
  image.registryUrl || image.jointRaw?.registryUrl || image.baseUrl || image.jointRaw?.baseUrl || ''

const formatDate = (value?: string | number) => {
  if (!value) {
    return ''
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  const pad = (item: number) => String(item).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const handleCurrentChange = (row?: EvaluationImage) => {
  if (!row) {
    return
  }

  const rawRow = row.jointRaw ? { ...row.jointRaw, ...row } : row
  currentRow.value = JSON.stringify(row)
  emit('select', JSON.stringify(rawRow))
}
</script>

<template>
  <div class="custom-image-select">
    <div v-if="tableData.length > 0" class="image-container">
      <ElTable
        v-loading="isLoading"
        :data="tableData"
        class="mt-20px"
        highlight-current-row
        style="width: 100%"
        @current-change="handleCurrentChange"
      >
        <ElTableColumn width="55" align="center">
          <template #default="{ row }">
            <ElRadio v-model="currentRow" :label="JSON.stringify(row)">{{ '' }}</ElRadio>
          </template>
        </ElTableColumn>
        <ElTableColumn property="name" :label="evalText.mirrorName">
          <template #default="{ row }"> {{ `${row.name}:${row.tag}` }} </template>
        </ElTableColumn>
      </ElTable>
      <ElPagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        size="small"
        hide-on-single-page
        layout="prev, pager, next"
        class="mt-4"
      />
      <div v-if="curImage" class="mt-20px">
        <ElDescriptions
          class="w-full"
          :title="`${curImage.name}:${curImage.tag}`"
          :column="1"
          border
        >
          <ElDescriptionsItem :label="evalText.size">
            {{ curImage.jointRaw?.imageSize || curImage.imageSize }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="evalText.created">
            {{ formatDate(curImage.createdAt || curImage.createdTime) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="evalText.mirrorIntro">
            {{ curImage.comment || curImage.desc }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="evalText.adaptFrame">
            {{ curImage.jointRaw?.frameLabel || curImage.frameLabel }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="evalText.mirrorTags">
            {{ curImage.jointRaw?.label || curImage.label }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="evalText.applicable">
            {{ curImage.jointRaw?.processorLabel || curImage.processorLabel }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="evalText.dockerfile">
            <pre class="dockerfile-preview">{{ dockerfileText }}</pre>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="evalText.registryUrl">
            {{ imageRegistryUrl(curImage) }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </div>
    </div>
    <ElEmpty v-else>
      <template #description>
        <div>
          <ElText size="large">{{ evalText.customEmptyDescription }}</ElText>
          <br />
          <ElText type="info">{{ evalText.customEmptyInformation }}</ElText>
        </div>
      </template>
      <ElButton type="primary" disabled>{{ evalText.customEmptyAction }}</ElButton>
    </ElEmpty>
  </div>
</template>

<style scoped>
.custom-image-select,
.image-container {
  width: 100%;
}

.dockerfile-preview {
  max-height: 260px;
  overflow: auto;
  margin: 0;
  border-radius: 4px;
  background: #f7f8fa;
  padding: 12px;
  color: #303133;
  font-size: 12px;
  line-height: 18px;
  white-space: pre-wrap;
}
</style>
