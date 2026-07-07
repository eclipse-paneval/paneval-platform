<script setup lang="ts">
import {
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElCol,
  ElDescriptions,
  ElDescriptionsItem,
  ElLink,
  ElRow,
  ElSkeleton,
  ElTag,
  ElText,
  ElTooltip
} from 'element-plus'
import { useQuery } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { getDatasets, getEvaluation, getMultimodalDatasets } from '@/api/evaluations'
import type { EvaluationDataset, EvaluationDetail } from '@/api/evaluations/types'
import interfaceIcon from '@/assets/svgs/interface.svg'
import EvaluationOnlineBatches from './components/EvaluationOnlineBatches.vue'
import { buildDatasetLabelMap, datasetLabels, domainLabel, sceneLabel } from './formatters'
import { evalText } from './evaluationFormLabels'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const batchComponent = ref<InstanceType<typeof EvaluationOnlineBatches>>()

const evaluationId = computed(() => route.params.id as string)

const {
  data: evaluation,
  isLoading,
  refetch
} = useQuery({
  queryKey: computed(() => ['evaluation-detail', evaluationId.value]),
  queryFn: () => getEvaluation(evaluationId.value)
})

const { data: datasets } = useQuery({
  queryKey: ['evaluation-detail-dataset-labels'],
  queryFn: getDatasets
})

const { data: multimodalDatasetGroups } = useQuery({
  queryKey: ['evaluation-detail-mm-dataset-labels'],
  queryFn: getMultimodalDatasets
})

const datasetMap = computed(() => buildDatasetLabelMap(datasets.value || []))

const datasetItems = computed(() => {
  const detail = evaluation.value
  if (!detail) {
    return []
  }

  return datasetLabels(detail.datasets, datasetMap.value, detail.datasetsConfig)
})

const selectedDatasets = computed(() => {
  const detail = visibleDetail.value
  const ids = new Set((detail?.datasets || []).map((item) => Number(item)))
  if (detail && ['MM', 'M', 'Multimodal'].includes(detail.domain)) {
    return (multimodalDatasetGroups.value || [])
      .filter((group) => ids.has(group.id))
      .map(
        (group): EvaluationDataset => ({
          id: group.id,
          key: String(group.id),
          scenario: group.name,
          domain: detail.domain,
          name: group.name
        })
      )
  }

  return (datasets.value || []).filter((dataset) => ids.has(dataset.id))
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

const visibleDetail = computed<EvaluationDetail | undefined>(() => {
  const detail = evaluation.value
  if (!detail) {
    return undefined
  }

  return {
    ...detail,
    sence: 'EA'
  }
})

const title = computed(() => visibleDetail.value?.name || t('evaluation.evaluationDetail'))
const description = computed(() => visibleDetail.value?.description || '')
const createdAt = computed(() => formatDate(visibleDetail.value?.createdAt))
const currentDomain = computed(() => domainLabel(visibleDetail.value?.domain || ''))

const runBatch = (dryRun: boolean) => {
  void batchComponent.value?.runBatch(dryRun)
}

const editEvaluation = () => {
  void router.push(`/console/evaluations/${evaluationId.value}/edit`)
}

const onBatchRefreshed = () => {
  void refetch()
}
</script>

<template>
  <section class="evaluation-detail">
    <div class="mx-auto mb-10 max-w-350">
      <ElBreadcrumb class="mb-7.5 mt-2.5">
        <ElBreadcrumbItem :to="{ path: '/console/evaluations' }">
          {{ t('navigation.modelEvaluation') }}
        </ElBreadcrumbItem>
        <ElBreadcrumbItem>{{ t('evaluation.evaluationDetail') }}</ElBreadcrumbItem>
      </ElBreadcrumb>

      <ElSkeleton v-if="isLoading && !visibleDetail" :rows="8" animated />

      <template v-else-if="visibleDetail">
        <ElRow class="w-full" align="middle">
          <ElCol :span="12" class="title">
            <img class="title-icon" :src="interfaceIcon" alt="" />
            <div>{{ title }}</div>
          </ElCol>
          <ElCol :span="12" class="text-right">
            <ElButton type="primary" @click="editEvaluation">{{ t('common.edit') }}</ElButton>
            <ElButton type="default" @click="runBatch(true)">
              {{ t('evaluation.checkInference') }}
            </ElButton>
            <ElButton type="default" @click="runBatch(false)">
              {{ t('evaluation.runInference') }}
            </ElButton>
          </ElCol>
        </ElRow>

        <ElRow class="my-5 w-full">
          <ElText line-clamp="3" type="info" class="detail-description">
            {{ description }}
          </ElText>
        </ElRow>

        <ElRow class="custom-row w-full">
          <ElDescriptions class="w-full" direction="horizontal" :column="3">
            <ElDescriptionsItem label="ID">{{ visibleDetail.id }}</ElDescriptionsItem>
            <ElDescriptionsItem :label="evalText.domain">
              {{ currentDomain }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="evalText.evalDatasets" class-name="dataset-desc-item">
              <ElTooltip placement="top-start" effect="light" :popper-class="['max-w-[600px]']">
                <template #content>
                  <ElTag
                    v-for="item in datasetItems"
                    class="mr-1 my-0.5"
                    :key="item"
                    type="primary"
                    size="small"
                  >
                    {{ item }}
                  </ElTag>
                </template>
                <el-text class="dataset-tags" truncated>
                  <ElTag
                    v-for="item in datasetItems"
                    class="mr-1"
                    :key="item"
                    type="primary"
                    size="small"
                  >
                    {{ item }}
                  </ElTag>
                </el-text>
              </ElTooltip>
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="t('common.createdAt')">{{ createdAt }}</ElDescriptionsItem>
            <ElDescriptionsItem :label="evalText.url">
              <span class="break-all">{{ visibleDetail.url || '-' }}</span>
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="evalText.onlineModel">
              {{ visibleDetail.onlineModelName || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="evalText.onlineKey">
              <ElText class="break-all align-top" size="small">
                {{ visibleDetail.onlineApiKey || '-' }}
              </ElText>
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="t('evaluation.paperAndModel')">
              <ElLink
                v-if="visibleDetail.paperUrl"
                :href="visibleDetail.paperUrl"
                type="primary"
                target="_blank"
                class="mr-2.5"
              >
                {{ t('common.paper') }}
              </ElLink>
              <ElLink
                v-if="visibleDetail.modelUrl"
                :href="visibleDetail.modelUrl"
                type="primary"
                target="_blank"
              >
                {{ t('common.model') }}
              </ElLink>
              <span v-if="!visibleDetail.paperUrl && !visibleDetail.modelUrl">-</span>
            </ElDescriptionsItem>
            <ElDescriptionsItem v-if="visibleDetail.modelType" :label="evalText.modelType">
              {{ visibleDetail.modelType }}
            </ElDescriptionsItem>
            <ElDescriptionsItem
              v-if="visibleDetail.modelGenKwargs"
              :label="evalText.modelGenKwargs"
            >
              <span class="break-all">{{ visibleDetail.modelGenKwargs }}</span>
            </ElDescriptionsItem>
          </ElDescriptions>
        </ElRow>
      </template>
    </div>

    <div class="detail-bottom w-full px-5 py-7.5">
      <ElRow v-if="!visibleDetail" class="mx-auto max-w-350">
        <ElSkeleton :rows="6" animated />
      </ElRow>
      <ElRow v-else justify="center" class="mx-auto max-w-350">
        <ElCol :span="24">
          <EvaluationOnlineBatches
            ref="batchComponent"
            :evaluation-id="evaluationId"
            :detail="visibleDetail"
            :datasets="selectedDatasets"
            @refreshed="onBatchRefreshed"
          />
        </ElCol>
      </ElRow>
    </div>
  </section>
</template>

<style scoped>
.evaluation-detail {
  padding: 0 40px;
}

.title {
  display: flex;
  align-items: center;
  color: #292962;
  font-size: 24px;
}

.title-icon {
  width: 36px;
  height: 36px;
  margin-right: 20px;
}

.detail-description {
  color: #7f8499;
  font-weight: 500;
}

.custom-row :deep(.el-descriptions) {
  border-radius: 8px;
  background-color: #fff;
  padding: 20px 32px;
}

.custom-row :deep(.el-descriptions__label:not(.is-bordered-label)) {
  color: #7f8499;
}

.custom-row :deep(.el-descriptions__content:not(.is-bordered-label)) {
  color: #303133;
  font-weight: 500;
}

.custom-row :deep(.el-descriptions__cell) {
  vertical-align: top;
}

.custom-row :deep(.el-descriptions__cell:has(.dataset-desc-item)) {
  display: flex;
  max-width: 500px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dataset-tags {
  max-width: 400px;
}

.detail-bottom {
  background-color: unset;
}

.evaluation-detail :deep(.el-button) {
  border-radius: 8px;
  padding: 12px 25px;
}
</style>
