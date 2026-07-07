<script setup lang="ts">
import { ElEmpty, ElImage, ElSkeleton, ElTable, ElTableColumn, ElText } from 'element-plus'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationBatchResults } from '@/api/evaluations'
import { multimodalTaskName } from './multimodalLabels'

const props = defineProps<{
  evaluationId: string | number
  batchId?: string | number
}>()

const results = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const { t } = useI18n()

const imageUrl = (md5?: string) => `/api/evaluations/img?md5=${md5}`

const loadResults = async () => {
  if (!props.batchId) {
    results.value = []
    return
  }

  loading.value = true
  try {
    const response = await getEvaluationBatchResults({
      evaluationId: props.evaluationId,
      batchId: props.batchId
    })
    const rows: Record<string, unknown>[] = []
    ;(response.results || []).forEach((item) => {
      const data = item.data as { data?: Record<string, unknown>[] } | undefined
      data?.data?.forEach((row) => rows.push({ ...row, parent: item }))
    })
    results.value = rows
  } finally {
    loading.value = false
  }
}

watch(() => props.batchId, loadResults, { immediate: true })
</script>

<template>
  <div class="multi-table">
    <div class="description mb-[12px]">{{ t('evaluationBatch.checkSampleDescription') }}</div>
    <ElSkeleton :rows="6" animated :throttle="0" :loading="loading">
      <template #default>
        <ElTable v-if="results.length" stripe :data="results" size="small" border>
          <ElTableColumn :label="t('evaluationBatch.task')">
            <template #default="{ row }">
              <ElText size="small" type="info">{{ multimodalTaskName(row.parent?.name) }}</ElText>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('evaluationBatch.dataset')">
            <template #default="{ row }">
              <ElText size="small" type="info">{{ row.parent?.dataset }}</ElText>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('evaluationBatch.input')">
            <template #default="{ row }">
              <ElText v-if="row.parent?.name === '文本生成图像'" size="small" type="info">
                {{ row.prompt }}
              </ElText>
              <template v-else-if="row.parent?.name === '图问答'">
                <div>
                  <ElText size="small">{{ t('evaluationBatch.question') }}</ElText>
                </div>
                <ElText size="small" type="info">{{ row.question }}</ElText>
                <div>
                  <ElText size="small">{{ t('evaluationBatch.image') }}</ElText>
                </div>
                <ElImage v-if="row.md5" class="el-img" :src="imageUrl(row.md5)" fit="cover" />
              </template>
              <ElImage
                v-else-if="row.parent?.name === '图像-文本匹配' && row.md5"
                class="el-img"
                :src="imageUrl(row.md5)"
                fit="cover"
              />
              <ElText v-else size="small" type="info">{{ row.prompt || '-' }}</ElText>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('evaluationBatch.label')">
            <template #default="{ row }">
              <ElText size="small">{{ row.label || '-' }}</ElText>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('evaluationBatch.predict')">
            <template #default="{ row }">
              <ElImage
                v-if="row.parent?.name === '文本生成图像' && row.md5"
                class="el-img"
                :src="imageUrl(row.md5)"
                fit="cover"
              />
              <ElText v-else size="small" type="info">
                {{ row.answer || row.txt || row.output || '-' }}
              </ElText>
            </template>
          </ElTableColumn>
        </ElTable>
        <ElEmpty v-else :description="t('common.empty')" />
      </template>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.multi-table {
  width: 100%;
}

.description {
  color: var(--Pan-Info-color, #7f8499);
  font-size: 14px;
}

.el-img {
  width: 120px;
  height: 120px;
}

.multi-table :deep(.el-table .el-table__cell) {
  vertical-align: top;
}
</style>
