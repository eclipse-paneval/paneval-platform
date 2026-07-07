<script setup lang="ts">
import { ElCol, ElOption, ElRow, ElSelect, ElTabPane, ElTabs } from 'element-plus'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import EvaluationLogContent from './EvaluationLogContent.vue'

const props = defineProps<{
  evaluationId: string | number
  batchId?: string | number
  trySequence?: number | string
  online?: boolean
  domain?: string
}>()

const kind = ref('app.log.out')
const currentTrySequence = ref<number | string | undefined>(0)
const { t } = useI18n()

watch(
  () => props.trySequence,
  (value) => {
    currentTrySequence.value = value ?? 0
  },
  { immediate: true }
)
</script>

<template>
  <ElRow justify="center" class="mx-auto w-full">
    <ElCol :span="24" class="relative">
      <div class="absolute left-[580px] top-[8px] z-10">
        <ElSelect
          v-model="currentTrySequence"
          :empty-values="[null, undefined]"
          :placeholder="t('evaluationBatch.trySequence')"
          style="width: 140px"
          size="small"
        >
          <ElOption
            v-for="item in trySequence ? Number(trySequence) + 1 : 1"
            :key="item"
            :label="t('evaluationBatch.attempt', { index: item - 1 })"
            :value="item - 1"
          />
        </ElSelect>
      </div>
      <ElTabs v-model="kind">
        <ElTabPane :label="t('evaluationBatch.output')" name="app.log.out">
          <EvaluationLogContent
            :evaluation-id="evaluationId"
            :batch-id="batchId"
            kind="app.log.out"
            :try-sequence="currentTrySequence"
          />
        </ElTabPane>
        <ElTabPane v-if="!online" :label="t('evaluationBatch.modelLog')" name="app" lazy>
          <EvaluationLogContent
            :evaluation-id="evaluationId"
            :batch-id="batchId"
            kind="app"
            :try-sequence="currentTrySequence"
          />
        </ElTabPane>
        <ElTabPane
          v-if="domain !== 'S'"
          :label="t('evaluationBatch.evaluationLog')"
          name="eval"
          lazy
        >
          <EvaluationLogContent
            :evaluation-id="evaluationId"
            :batch-id="batchId"
            kind="eval"
            :try-sequence="currentTrySequence"
          />
        </ElTabPane>
        <ElTabPane
          v-if="domain !== 'S'"
          :label="t('evaluationBatch.rawResults')"
          name="results.json"
          lazy
        >
          <EvaluationLogContent
            :evaluation-id="evaluationId"
            :batch-id="batchId"
            kind="results.json"
            :try-sequence="currentTrySequence"
          />
        </ElTabPane>
      </ElTabs>
    </ElCol>
  </ElRow>
</template>
