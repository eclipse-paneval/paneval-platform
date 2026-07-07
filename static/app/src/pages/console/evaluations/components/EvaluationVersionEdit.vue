<script setup lang="ts">
import {
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElDialog,
  ElForm,
  ElFormItem,
  ElNotification,
  type FormInstance,
  type FormRules
} from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationBatchResults, updateEvaluationBatchDatasets } from '@/api/evaluations'
import type { EvaluationBatch, EvaluationDataset, EvaluationDetail } from '@/api/evaluations/types'
import MultimodalDatasetCheckbox from './MultimodalDatasetCheckbox.vue'
import { MULTIMODAL_TASK_IDS } from './multimodalLabels'

const visible = defineModel<boolean>('visible', { default: false })

const props = defineProps<{
  detail?: EvaluationDetail
  row?: EvaluationBatch
  datasets: EvaluationDataset[]
}>()

const emit = defineEmits<{
  edited: [row: EvaluationBatch]
}>()

const { t } = useI18n()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const datasetStatus = ref<Record<string, string | number | undefined>>({})
const form = reactive({
  datasets: [] as number[],
  datasetsConfig: [] as string[],
  dimensions: ['accuracy'] as string[]
})

const rules: FormRules<typeof form> = {
  datasets: [{ required: true, message: t('evaluation.selectTasks'), trigger: 'change' }],
  datasetsConfig: [
    {
      required: true,
      message: t('evaluation.selectTasks'),
      trigger: ['blur', 'change']
    },
    {
      validator: (_rule, _value, callback) => {
        if (form.datasets.length > 0) {
          callback()
          return
        }
        callback(new Error(t('evaluation.selectTasks')))
      },
      trigger: ['blur', 'change']
    }
  ],
  dimensions: [{ required: true, message: t('evaluation.selectDimensions'), trigger: 'change' }]
}

const title = computed(() => {
  const row = props.row
  if (!row) {
    return t('evaluation.editCurrentVersion')
  }

  return t('evaluation.editCurrentVersionWithSequence', {
    type: row.dryRun ? t('common.check') : t('evaluationBatch.evaluation'),
    sequence: row.sequence || ''
  })
})

const options = computed(() =>
  props.datasets.map((item) => ({
    id: item.id,
    label: item.name || item.label || item.key || String(item.id)
  }))
)

const isMultimodal = computed(() => {
  const domain = props.detail?.domain
  return domain === 'MM' || domain === 'M' || domain === 'Multimodal'
})

type MultimodalDatasetGroupLike = NonNullable<EvaluationDetail['datasetsConfig']>

const getAllMultimodalDatasets = async (
  groups: Array<{ id: number; data: MultimodalDatasetGroupLike }>
) => {
  if (!props.detail || !props.row) {
    return
  }

  const response = await getEvaluationBatchResults({
    evaluationId: props.detail.id,
    batchId: props.row.id
  })
  const taskIds = new Set<number>()
  const statusMap: Record<string, string | number | undefined> = {}

  const datasetsConfig = (response.results || [])
    .filter((item) => item.lbx !== 1)
    .flatMap((item) => {
      const taskId =
        MULTIMODAL_TASK_IDS[String(item.name || '')] ||
        groups.find((group) => group.data.some((dataset) => dataset.datasetShow === item.dataset))
          ?.id

      if (!taskId) {
        return []
      }

      taskIds.add(Number(taskId))
      const group = groups.find((candidate) => Number(candidate.id) === Number(taskId))
      const target = group?.data.find((dataset) => item.dataset === dataset.datasetShow)
      if (!target) {
        return []
      }

      const value = JSON.stringify(target)
      statusMap[value] = item.status
      return [value]
    })

  form.datasets = [...taskIds]
  form.datasetsConfig = datasetsConfig
  datasetStatus.value = statusMap
}

watch(
  () => visible.value,
  (value) => {
    if (!value) {
      return
    }

    form.datasets = [...(props.detail?.datasets || [])]
    form.datasetsConfig = (props.detail?.datasetsConfig || []).map((item) => JSON.stringify(item))
    form.dimensions = props.row?.includeRobustness ? ['accuracy', 'robustness'] : ['accuracy']
    datasetStatus.value = {}
  }
)

const cancel = () => {
  visible.value = false
}

const submit = async () => {
  if (!props.detail || !props.row) {
    return
  }

  await formRef.value?.validate(async (valid) => {
    if (!valid || !props.detail || !props.row) {
      return
    }

    submitting.value = true
    try {
      const datasetsConfig = isMultimodal.value
        ? form.datasetsConfig.map((item) => JSON.parse(item))
        : props.detail.datasetsConfig
      const selectedDatasetsConfig = datasetsConfig || []
      const datasets = isMultimodal.value ? form.datasets : form.datasets

      await updateEvaluationBatchDatasets({
        evaluationId: props.detail.id,
        batchId: props.row.id,
        datasets,
        datasetsConfig: selectedDatasetsConfig,
        includeRobustness: form.dimensions.includes('robustness')
      })
      emit('edited', props.row)
      visible.value = false
      ElNotification({ title: t('common.success'), message: '', type: 'success' })
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <ElDialog v-model="visible" :title="title" width="600">
    <ElForm ref="formRef" :model="form" :rules="rules" label-position="top">
      <ElFormItem v-if="!isMultimodal" prop="datasets" :label="t('evaluation.taskDatasets')">
        <ElCheckboxGroup v-model="form.datasets" class="dataset-options">
          <ElCheckbox v-for="item in options" :key="item.id" :value="item.id">
            {{ item.label }}
          </ElCheckbox>
        </ElCheckboxGroup>
      </ElFormItem>
      <ElFormItem v-else prop="datasetsConfig" :label="t('evaluation.taskDatasets')">
        <MultimodalDatasetCheckbox
          :key="row?.id"
          v-model:datasets="form.datasetsConfig"
          v-model:ids="form.datasets"
          :status="datasetStatus"
          :staff="true"
          @all="getAllMultimodalDatasets"
        />
      </ElFormItem>
      <ElFormItem prop="dimensions" :label="t('evaluation.dimensions')">
        <ElCheckboxGroup v-model="form.dimensions">
          <ElCheckbox disabled value="accuracy">
            {{ t('evaluationBatch.accuracyEvaluation') }}
          </ElCheckbox>
          <ElCheckbox value="robustness">
            {{ t('evaluationBatch.robustnessEvaluation') }}
          </ElCheckbox>
        </ElCheckboxGroup>
      </ElFormItem>
    </ElForm>
    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="cancel">{{ t('common.cancel') }}</ElButton>
        <ElButton type="primary" :loading="submitting" @click="submit">
          {{ t('common.confirm') }}
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<style scoped>
.dataset-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  width: 100%;
}

.dataset-options :deep(.el-checkbox) {
  margin-right: 0;
}
</style>
