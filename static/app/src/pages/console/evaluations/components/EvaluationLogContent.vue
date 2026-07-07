<script setup lang="ts">
import { ElInput, ElPagination, ElRow } from 'element-plus'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationBatchLog } from '@/api/evaluations'

const props = defineProps<{
  evaluationId: string | number
  batchId?: string | number
  kind: string
  trySequence?: string | number
}>()

const content = ref('')
const page = ref(1)
const pageCount = ref(0)
const { t } = useI18n()

const loadContent = async () => {
  if (!props.evaluationId || !props.batchId || !props.kind) {
    content.value = t('common.empty')
    return
  }

  try {
    content.value = t('common.loading')
    const response = await getEvaluationBatchLog({
      evaluationId: props.evaluationId,
      batchId: props.batchId,
      kind: props.kind,
      trySequence: props.trySequence,
      page: page.value
    })
    content.value = response.results || t('common.empty')
    pageCount.value = response.page?.total || 0
  } catch {
    content.value = t('common.empty')
    pageCount.value = 0
  }
}

watch(
  () => [props.batchId, props.kind, props.trySequence],
  () => {
    page.value = 1
    void loadContent()
  },
  { immediate: true }
)
</script>

<template>
  <ElRow>
    <ElInput
      v-model="content"
      disabled
      :rows="30"
      type="textarea"
      :placeholder="t('common.empty')"
    />
    <ElPagination
      v-model:current-page="page"
      :page-count="pageCount"
      layout="prev, pager, next"
      @current-change="loadContent"
    />
  </ElRow>
</template>
