<script setup lang="ts">
import {
  ElAlert,
  ElButton,
  ElCol,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElLink,
  ElMessage,
  ElMessageBox,
  ElNotification,
  ElPagination,
  ElPopconfirm,
  ElRadio,
  ElRow,
  ElScrollbar,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElText
} from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  continueEvaluationBatch,
  getEvaluationBatchDags,
  getEvaluationBatchResults,
  getEvaluationBatches,
  runEvaluationBatch,
  startManualEvaluating,
  stopEvaluationBatch
} from '@/api/evaluations'
import type {
  EvaluationBatch,
  EvaluationDag,
  EvaluationDataset,
  EvaluationDetail
} from '@/api/evaluations/types'
import {
  batchStatusTitle,
  batchStatusType,
  CAN_CONTINUE_STATUS,
  CAN_EDIT_STATUS,
  CAN_STOP_STATUS,
  RUNNING_STATUS
} from './batchConstants'
import EvaluationDevsetTable from './EvaluationDevsetTable.vue'
import EvaluationLog from './EvaluationLog.vue'
import EvaluationResultNlp from './EvaluationResultNlp.vue'
import EvaluationStatusDescription from './EvaluationStatusDescription.vue'
import EvaluationVersionEdit from './EvaluationVersionEdit.vue'
import MultimodalCheckTable from './MultimodalCheckTable.vue'
import MultimodalTable from './MultimodalTable.vue'

const props = defineProps<{
  evaluationId: string | number
  detail?: EvaluationDetail
  datasets: EvaluationDataset[]
}>()

const emit = defineEmits<{
  refreshed: []
}>()

const { t } = useI18n()
const batches = ref<EvaluationBatch[]>([])
const dags = ref<EvaluationDag[]>([])
const loading = ref(false)
const dagsLoading = ref(false)
const submitting = ref(false)
const continueButtonLoading = ref(false)
const startGqButtonLoading = ref(false)
const activeTab = ref('checkInference')
const currentBatchId = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const editVisible = ref(false)
const editingRow = ref<EvaluationBatch>()
const singleTableRef = ref<InstanceType<typeof ElTable>>()
let timer: number | undefined

const currentBatch = computed(
  () => batches.value.find((batch) => String(batch.id) === currentBatchId.value) || null
)

const currentDryRun = computed(() =>
  currentBatch.value ? Boolean(currentBatch.value.dryRun) : undefined
)
const batchId = computed(() => currentBatch.value?.id)
const currentCreated = computed(() => formatDate(currentBatch.value?.createdAt))
const currentTrySequence = computed(() => currentBatch.value?.trySequence ?? 0)
const latestModelRevision = computed(() => props.detail?.modelRevision)
const currentStatusType = computed(() => batchStatusType(currentBatch.value?.status))
const currentRowSubmitted = computed(() => Boolean(currentBatch.value?.submitted))
const currentJobId = computed(() => currentBatch.value?.jointJobId)
const currentOnlineModelName = computed(() => currentBatch.value?.onlineModelName)

const resourceSettings = computed(() => {
  const data = currentBatch.value?.resource
  if (!data || Object.keys(data).length === 0) {
    return ''
  }

  return `${data.acceleratorModel}/${data.acceleratorCount} cards/${data.cpuCores} cores/${data.memGib} G`
})

const gqDags = computed(() =>
  dags.value.filter((dag) => {
    const dataset = props.datasets.find((item) => item.id === dag.datasetId)
    return dataset?.language === 'zh' && dataset?.scenario === 'GQ'
  })
)

const includesGq = computed(() =>
  props.datasets.some((dataset) => dataset.language === 'zh' && dataset.scenario === 'GQ')
)

const isMultimodal = computed(() => {
  const domain = props.detail?.domain
  return domain === 'MM' || domain === 'M' || domain === 'Multimodal'
})

const formatDate = (value?: string) => {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
    .format(new Date(value))
    .replace(/\//g, '-')
}

const loadDags = async () => {
  if (!currentBatch.value) {
    dags.value = []
    return
  }

  dagsLoading.value = true
  try {
    dags.value = await getEvaluationBatchDags({
      evaluationId: props.evaluationId,
      batchId: currentBatch.value.id
    })

    if (!currentDryRun.value) {
      await getEvaluationBatchResults({
        evaluationId: props.evaluationId,
        batchId: currentBatch.value.id
      })
    }
  } finally {
    dagsLoading.value = false
  }
}

const setCurrent = async (row?: EvaluationBatch) => {
  await nextTick()
  currentBatchId.value = row ? String(row.id) : ''
  if (row) {
    activeTab.value = row.dryRun ? 'checkInference' : 'inference'
  }
  if (row) {
    singleTableRef.value?.setCurrentRow(row)
  }
}

const refreshBatches = async (keepCurrent = true) => {
  loading.value = true
  try {
    const previousId = currentBatchId.value
    const response = await getEvaluationBatches({
      evaluationId: props.evaluationId,
      page: page.value
    })
    batches.value = response.results
    total.value = response.count

    const nextRow =
      (keepCurrent && batches.value.find((batch) => String(batch.id) === previousId)) ||
      batches.value[0]
    await setCurrent(nextRow)
    await loadDags()
  } finally {
    loading.value = false
  }
}

const scheduleRefresh = () => {
  if (timer) {
    clearTimeout(timer)
  }

  if (!currentBatch.value?.status || !RUNNING_STATUS.includes(currentBatch.value.status)) {
    return
  }

  timer = window.setTimeout(async () => {
    await refreshBatches(true)
    if (dags.value.some((dag) => dag.status && RUNNING_STATUS.includes(dag.status))) {
      scheduleRefresh()
    }
  }, 5000)
}

const handleCurrentChange = async (row: EvaluationBatch | null) => {
  if (dagsLoading.value) {
    return
  }

  currentBatchId.value = row ? String(row.id) : ''
  await loadDags()
  scheduleRefresh()
}

const changePage = async (value: number) => {
  page.value = value
  await refreshBatches(false)
}

const runBatch = async (dryRun?: boolean) => {
  submitting.value = true
  try {
    const resource =
      typeof props.detail?.jointResource === 'string'
        ? JSON.parse(props.detail.jointResource)
        : props.detail?.jointResource

    await runEvaluationBatch({
      evaluationId: props.evaluationId,
      resource,
      dryRun,
      priority: props.detail?.jointPriority
    })
    activeTab.value = dryRun ? 'checkInference' : 'inference'
    await refreshBatches(false)
    emit('refreshed')
    ElMessage.success(t('evaluationBatch.submittedSuccessfully'))
    scheduleRefresh()
  } finally {
    submitting.value = false
  }
}

const stopPropagation = () => {}

const onConfirmDelete = async (row: EvaluationBatch) => {
  await stopEvaluationBatch({ evaluationId: props.evaluationId, batchId: row.id })
  ElNotification({ title: t('evaluationBatch.stoppedSuccessfully'), message: '', type: 'success' })
  await refreshBatches(true)
}

const continueEvalMethod = async (row: EvaluationBatch) => {
  continueButtonLoading.value = true
  try {
    await continueEvaluationBatch({ evaluationId: props.evaluationId, batchId: row.id })
    ElNotification({
      title: t('evaluationBatch.submittedSuccessfully'),
      message: '',
      type: 'success'
    })
    await refreshBatches(true)
    scheduleRefresh()
  } finally {
    continueButtonLoading.value = false
  }
}

const editEvalMethod = (row: EvaluationBatch) => {
  editingRow.value = row
  editVisible.value = true
}

const onDatasetsEdited = async () => {
  emit('refreshed')
  await refreshBatches(true)
}

const handleStartGq = () => {
  activeTab.value = 'inference'
  if (!gqDags.value.length) {
    return
  }

  void ElMessageBox.confirm(
    t('evaluationBatch.startHumanEvaluationConfirm', { count: gqDags.value.length }),
    '',
    {
      type: 'warning'
    }
  ).then(async () => {
    startGqButtonLoading.value = true
    try {
      for (const dag of gqDags.value) {
        await startManualEvaluating(dag.id)
      }
      ElMessage.success(t('evaluationBatch.startedSuccessfully'))
      await refreshBatches(true)
    } finally {
      startGqButtonLoading.value = false
    }
  })
}

watch(
  () => currentDryRun.value,
  (isDryRun) => {
    if (isDryRun === undefined) {
      return
    }

    activeTab.value = isDryRun ? 'checkInference' : 'inference'
  }
)

watch(
  () => currentBatch.value?.status,
  () => scheduleRefresh()
)

onMounted(() => {
  void refreshBatches(false)
})

onBeforeUnmount(() => {
  if (timer) {
    clearTimeout(timer)
  }
})

defineExpose({
  runBatch
})
</script>

<template>
  <div class="online-batches">
    <ElRow justify="space-between" :gutter="24">
      <ElCol :span="8">
        <div class="batch-title pb-2">{{ t('evaluationBatch.versions') }}</div>
        <div class="table-container">
          <ElTable
            ref="singleTableRef"
            v-loading="loading"
            :data="batches"
            row-key="id"
            highlight-current-row
            class="w-full"
            size="small"
            flexible
            @current-change="handleCurrentChange"
          >
            <ElTableColumn width="55" align="center">
              <template #default="{ row }">
                <ElRadio v-model="currentBatchId" :label="String(row.id)" :disabled="dagsLoading">
                  {{ '' }}
                </ElRadio>
              </template>
            </ElTableColumn>
            <ElTableColumn property="sequence" :label="t('evaluationBatch.version')" width="70" />
            <ElTableColumn property="dryRun" :label="t('evaluationBatch.type')">
              <template #default="{ row }">
                {{ row.dryRun ? t('common.check') : t('evaluationBatch.evaluation') }}
              </template>
            </ElTableColumn>
            <ElTableColumn property="status" :label="t('common.status')">
              <template #default="{ row }">
                <ElText size="small" :type="batchStatusType(row.status)">
                  {{ batchStatusTitle(row.status) }}
                </ElText>
              </template>
            </ElTableColumn>
            <ElTableColumn :label="t('evaluationBatch.submitter')">
              <template #default="{ row }">{{ row.owner }}</template>
            </ElTableColumn>
            <ElTableColumn :label="t('common.action')" width="90">
              <template #default="{ row }">
                <ElPopconfirm
                  v-if="row.status && CAN_STOP_STATUS.includes(row.status)"
                  trigger="click"
                  :title="t('evaluationBatch.stopConfirm')"
                  @confirm="onConfirmDelete(row)"
                >
                  <template #reference>
                    <ElLink
                      type="primary"
                      size="small"
                      class="z-10 mr-1"
                      style="color: #333"
                      :title="t('evaluationBatch.stop')"
                      @click.stop="stopPropagation"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                      >
                        <rect width="4" height="14" x="6" y="5" fill="currentColor" rx="1" />
                        <rect width="4" height="14" x="14" y="5" fill="currentColor" rx="1" />
                      </svg>
                    </ElLink>
                  </template>
                </ElPopconfirm>
                <ElLink
                  v-if="
                    row.status &&
                    ((CAN_CONTINUE_STATUS.includes(row.status) &&
                      row.modelRevision === latestModelRevision) ||
                      row.status === 'M')
                  "
                  type="primary"
                  size="small"
                  class="z-10 mr-1"
                  style="color: #333"
                  :title="t('evaluationBatch.continue')"
                  :disabled="continueButtonLoading"
                  @click.stop="continueEvalMethod(row)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                  >
                    <path
                      fill="currentColor"
                      stroke="currentColor"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="1.5"
                      d="M6.906 4.537A.6.6 0 0 0 6 5.053v13.894a.6.6 0 0 0 .906.516l11.723-6.947a.6.6 0 0 0 0-1.032z"
                    />
                  </svg>
                </ElLink>
                <ElLink
                  v-if="row.status && CAN_EDIT_STATUS.includes(row.status) && false"
                  type="primary"
                  size="small"
                  class="z-10"
                  style="color: #333"
                  :title="t('common.edit')"
                  :disabled="continueButtonLoading"
                  @click.stop="editEvalMethod(row)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                  >
                    <path
                      fill="currentColor"
                      d="m22.038 7.573l-5.61-5.61l-4.197 4.196l5.61 5.61zm-5.611 5.611l-5.61-5.61L2 16.39V22h5.61zM12.682 22h9.542v-2h-9.542z"
                    />
                  </svg>
                </ElLink>
              </template>
            </ElTableColumn>
          </ElTable>
        </div>
        <ElPagination
          v-model:current-page="page"
          :page-size="pageSize"
          size="small"
          layout="prev, pager, next"
          :total="total"
          class="mt-4"
          hide-on-single-page
          @current-change="changePage"
        />
      </ElCol>

      <ElCol :span="16">
        <ElRow justify="center" class="mx-auto w-full">
          <ElCol :span="24" class="relative">
            <ElButton
              v-if="
                detail?.modelType === 'SFT' &&
                includesGq &&
                !currentDryRun &&
                ['inference', 'result'].includes(activeTab)
              "
              class="absolute right-0 z-10"
              type="primary"
              :disabled="gqDags.every((item) => item.status !== 'DI')"
              :loading="startGqButtonLoading"
              @click="handleStartGq"
            >
              {{ t('evaluationBatch.startHumanEvaluation') }}
            </ElButton>

            <ElTabs v-model="activeTab" class="eval-tabs">
              <ElTabPane :label="t('evaluationBatch.checkInference')" name="checkInference">
                <ElRow>
                  <ElCol :span="24" class="mb-[12px]">
                    <ElAlert
                      :title="t('evaluationBatch.inferenceTips')"
                      type="warning"
                      :closable="false"
                    >
                      <template #default>
                        <span class="description">
                          {{ t('evaluationBatch.checkInferenceTipText') }}
                        </span>
                      </template>
                    </ElAlert>
                  </ElCol>
                </ElRow>
                <ElRow
                  v-if="!currentBatchId || currentDryRun"
                  class="w-full"
                  justify="space-between"
                >
                  <ElForm inline class="w-full" label-width="auto">
                    <ElFormItem v-if="batchId" :label="t('evaluationBatch.batchId')">
                      <ElText type="info">{{ batchId }}</ElText>
                    </ElFormItem>
                    <ElFormItem v-if="currentJobId" :label="t('evaluationBatch.jobId')">
                      <ElText type="info">{{ currentJobId }}</ElText>
                    </ElFormItem>
                    <ElFormItem v-if="batches.length > 0" :label="t('evaluationBatch.submitTime')">
                      <ElText type="info">{{ currentCreated }}</ElText>
                    </ElFormItem>
                    <ElFormItem
                      v-if="resourceSettings"
                      class="w-full"
                      :label="t('evaluationBatch.resourceSettings')"
                    >
                      <ElText type="info">{{ resourceSettings }}</ElText>
                    </ElFormItem>
                  </ElForm>
                </ElRow>
                <ElScrollbar max-height="550" always>
                  <ElEmpty v-if="!batchId" :description="t('common.empty')" />
                  <ElRow v-else-if="currentDryRun" class="w-full" justify="space-between">
                    <ElCol v-if="!isMultimodal" v-loading="dagsLoading" :span="24">
                      <EvaluationStatusDescription :dags="dags" :datasets="datasets" check />
                    </ElCol>
                  </ElRow>
                  <ElRow v-if="batchId && isMultimodal && currentDryRun">
                    <ElCol :span="24" class="pan-section-title my-[20px]">
                      {{ t('evaluationBatch.progressTable') }}
                    </ElCol>
                    <ElCol :span="24">
                      <MultimodalTable
                        v-if="batchId"
                        :evaluation-id="evaluationId"
                        :batch-id="batchId"
                        :active="activeTab"
                        :submitted="currentRowSubmitted"
                      />
                    </ElCol>
                  </ElRow>
                  <ElRow v-if="batchId && currentDryRun">
                    <ElCol :span="24" class="pan-section-title my-[20px]">
                      {{
                        isMultimodal
                          ? t('evaluationBatch.result')
                          : t('evaluationBatch.checkResult')
                      }}
                    </ElCol>
                    <ElCol :span="24">
                      <MultimodalCheckTable
                        v-if="isMultimodal && batchId"
                        :evaluation-id="evaluationId"
                        :batch-id="batchId"
                      />
                      <EvaluationDevsetTable
                        v-else-if="batchId"
                        :evaluation-id="evaluationId"
                        :batch-id="batchId"
                        :active="activeTab"
                      />
                    </ElCol>
                  </ElRow>
                </ElScrollbar>
              </ElTabPane>

              <ElTabPane :label="t('evaluationBatch.inference')" name="inference">
                <ElRow>
                  <ElCol :span="24" class="mb-[12px]">
                    <ElAlert
                      :title="t('evaluationBatch.inferenceTips')"
                      type="warning"
                      :closable="false"
                    >
                      <template #default>
                        <span class="description">
                          {{ t('evaluationBatch.inferenceTipText') }}
                        </span>
                      </template>
                    </ElAlert>
                    <br />
                  </ElCol>
                </ElRow>
                <ElEmpty v-if="!batchId || currentDryRun" :description="t('common.empty')" />
                <ElRow v-else class="w-full" justify="space-between">
                  <ElForm inline class="w-full" label-width="auto">
                    <ElFormItem v-if="batchId" :label="t('evaluationBatch.batchId')">
                      <ElText type="info">{{ batchId }}</ElText>
                    </ElFormItem>
                    <ElFormItem v-if="currentJobId" :label="t('evaluationBatch.jobId')">
                      <ElText type="info">{{ currentJobId }}</ElText>
                    </ElFormItem>
                    <ElFormItem v-if="batches.length > 0" :label="t('evaluationBatch.submitTime')">
                      <ElText type="info">{{ currentCreated }}</ElText>
                    </ElFormItem>
                    <ElFormItem
                      v-if="resourceSettings"
                      :label="t('evaluationBatch.resourceSettings')"
                    >
                      <ElText type="info">{{ resourceSettings }}</ElText>
                    </ElFormItem>
                    <ElFormItem
                      v-if="currentOnlineModelName"
                      :label="t('evaluationBatch.onlineModel')"
                    >
                      <ElText type="info">{{ currentOnlineModelName }}</ElText>
                    </ElFormItem>
                  </ElForm>
                  <ElCol v-if="isMultimodal" v-loading="dagsLoading" :span="24">
                    <MultimodalTable
                      v-if="batchId"
                      :evaluation-id="evaluationId"
                      :batch-id="batchId"
                      :active="activeTab"
                      :submitted="currentRowSubmitted"
                    />
                  </ElCol>
                  <ElCol v-else v-loading="dagsLoading" :span="24">
                    <EvaluationStatusDescription :dags="dags" :datasets="datasets" />
                  </ElCol>
                </ElRow>
              </ElTabPane>

              <ElTabPane
                v-if="!isMultimodal"
                :label="t('evaluationBatch.result')"
                name="result"
                lazy
              >
                <EvaluationResultNlp
                  v-if="batchId && !currentDryRun"
                  :key="activeTab"
                  :evaluation-id="evaluationId"
                  :batch-id="batchId"
                  :datasets="datasets"
                  :type="currentStatusType"
                  :submitted="currentRowSubmitted"
                />
                <ElEmpty v-else :description="t('common.empty')" />
              </ElTabPane>

              <ElTabPane :label="t('evaluationBatch.log')" name="log" lazy>
                <EvaluationLog
                  :evaluation-id="evaluationId"
                  :batch-id="batchId"
                  :online="true"
                  :domain="detail?.domain"
                  :try-sequence="currentTrySequence"
                />
              </ElTabPane>
            </ElTabs>
          </ElCol>
        </ElRow>
      </ElCol>
    </ElRow>

    <EvaluationVersionEdit
      v-model:visible="editVisible"
      :detail="detail"
      :row="editingRow"
      :datasets="datasets"
      @edited="onDatasetsEdited"
    />
  </div>
</template>

<style scoped>
.online-batches {
  width: 100%;
}

.online-batches :deep(.el-tabs__nav-wrap::after) {
  height: 0;
}

.online-batches :deep(.el-tabs__content) {
  border-radius: 8px;
  background-color: #fff;
  padding: 16px;
}

.online-batches :deep(.el-tabs__nav) {
  padding: 4px 0;
}

.online-batches :deep(.el-tabs__item) {
  background-color: unset;
  color: #979cba;
  font-size: 20px;
  font-weight: 700;
}

.online-batches :deep(.el-tabs__item.is-active),
.online-batches :deep(.el-tabs__item:hover) {
  color: #292962;
}

.online-batches :deep(.el-tabs__active-bar) {
  height: 5px;
  border-radius: 4px;
  background-color: unset;
}

.online-batches :deep(.el-tabs__active-bar)::after {
  display: block;
  width: 48px;
  height: 5px;
  margin: 0 auto;
  border-radius: 8px;
  background: linear-gradient(90deg, #1762ee 0%, rgb(23 98 238 / 1%) 100%);
  content: '';
}

.online-batches :deep(.el-table) {
  --el-table-current-row-bg-color: rgb(23 98 238 / 10%);
}

.online-batches :deep(.el-table tr) {
  background-color: #fff;
}

.online-batches :deep(.el-table th.el-table__cell) {
  background-color: #f3f4f7;
  color: var(--Pan-Info-color, #7f8499);
}

.online-batches :deep(.el-table .el-table__cell) {
  color: var(--Pan-Text-Default, #303133);
}

.online-batches :deep(.el-alert--warning.is-light) {
  background-color: rgb(255 185 72 / 10%);
}

.online-batches :deep(.el-form-item__label) {
  color: var(--Pan-Info-color, #7f8499);
}

.online-batches :deep(.el-text.el-text--info) {
  color: var(--Pan-Text-Default, #303133);
}

.online-batches :deep(.el-link) {
  color: #333;
}

.online-batches :deep(.el-link .el-link__inner) {
  align-items: center;
  display: inline-flex;
}

.table-container {
  margin-top: 24px;
  background-color: #fff;
}

.batch-title {
  color: var(--Pan-Title-color2, #292962);
  font-size: 20px;
  font-weight: 700;
}

.description {
  color: var(--Pan-Info-color, #7f8499);
  font-size: 14px;
}

.pan-section-title {
  display: flex;
  align-items: center;
  color: #292962;
  font-size: 20px;
  font-weight: 700;
}

.pan-section-title::before {
  display: inline-block;
  width: 4px;
  height: 18px;
  margin-right: 10px;
  border-radius: 4px;
  background: linear-gradient(180deg, #1762ee 0%, rgb(23 98 238 / 10%) 100%);
  content: '';
}
</style>
