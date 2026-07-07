<script setup lang="ts">
import { keepPreviousData, useQuery } from '@tanstack/vue-query'
import {
  ElButton,
  ElInput,
  ElOption,
  ElPagination,
  ElPopconfirm,
  ElSelect,
  ElSegmented,
  ElTable,
  ElTableColumn,
  ElTag,
  ElMessage
} from 'element-plus'
import { computed, nextTick, onActivated, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { getDatasets, getEvaluations, removeEvaluation } from '@/api/evaluations'
import type { EvaluationListItem } from '@/api/evaluations/types'
import ConsoleSideMenu from '@/pages/console/components/ConsoleSideMenu.vue'
import { evaluationCapabilities } from './capabilities'
import { buildDatasetLabelMap, datasetLabels, domainLabel, sceneLabel } from './formatters'

const router = useRouter()
const { t } = useI18n()

const filters = reactive({
  keyword: '',
  searchBy: 'modelName',
  submittedKeyword: '',
  submittedSearchBy: 'modelName',
  me: '1',
  domain: ''
})

const page = ref(1)
const pageSize = ref(10)
const tableAnimationKey = ref(0)
const hasActivatedOnce = ref(false)

const isMineScope = computed(() => filters.me === '1')

const evaluationQueryKey = computed(() => [
  'evaluations',
  page.value,
  pageSize.value,
  filters.me,
  filters.submittedSearchBy,
  filters.submittedKeyword,
  filters.domain
])

const { data, isLoading, isFetching, refetch } = useQuery({
  queryKey: evaluationQueryKey,
  queryFn: () =>
    getEvaluations({
      pageIndex: page.value,
      pageSize: pageSize.value,
      me: filters.me,
      modelName: filters.submittedSearchBy === 'modelName' ? filters.submittedKeyword : undefined,
      createUser: filters.submittedSearchBy === 'createUser' ? filters.submittedKeyword : undefined,
      domain: filters.domain
    }),
  placeholderData: keepPreviousData
})

const isRefreshingList = computed(() => isFetching.value && !isLoading.value)

onActivated(() => {
  if (!hasActivatedOnce.value) {
    hasActivatedOnce.value = true
    return
  }

  void refetch()
})

watch(
  () => data.value?.list,
  async () => {
    await nextTick()
    tableAnimationKey.value += 1
  },
  { flush: 'post' }
)

const { data: datasets } = useQuery({
  queryKey: ['evaluation-dataset-labels'],
  queryFn: getDatasets
})

const datasetMap = computed(() => buildDatasetLabelMap(datasets.value || []))

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

const submitSearch = () => {
  if (isMineScope.value && filters.searchBy === 'createUser') {
    filters.searchBy = 'modelName'
  }

  filters.submittedKeyword = filters.keyword.trim()
  filters.submittedSearchBy = filters.searchBy
  page.value = 1
}

const switchScope = () => {
  if (isMineScope.value && filters.searchBy === 'createUser') {
    filters.searchBy = 'modelName'
  }

  filters.keyword = ''
  filters.submittedKeyword = ''
  filters.submittedSearchBy = filters.searchBy
  page.value = 1
}

const handleSearchByChange = () => {
  if (isMineScope.value && filters.searchBy === 'createUser') {
    filters.searchBy = 'modelName'
  }
}

const handlePageChange = (nextPage: number) => {
  page.value = nextPage
}

const handlePageSizeChange = (nextPageSize: number) => {
  pageSize.value = nextPageSize
  page.value = 1
}

const canOpenEvaluation = (evaluation: EvaluationListItem) => {
  return ['N', 'NLP', 'M', 'MM', 'Multimodal'].includes(evaluation.domain)
}

const openDetail = (evaluation: EvaluationListItem) => {
  if (!canOpenEvaluation(evaluation)) {
    return
  }

  void router.push(`/console/evaluations/${evaluation.id}`)
}

const editEvaluation = (evaluation: EvaluationListItem) => {
  if (!canOpenEvaluation(evaluation)) {
    return
  }

  void router.push(`/console/evaluations/${evaluation.id}/edit`)
}

const deleteEvaluation = async (evaluation: EvaluationListItem) => {
  await removeEvaluation(evaluation.id)
  ElMessage.success(t('evaluation.evaluationDeleted'))
  void refetch()
}

const getRowClassName = () => 'evaluation-row-enter'

const getRowStyle = ({ rowIndex }: { rowIndex: number }) => {
  return {
    animationDelay: `${Math.min(rowIndex, 10) * 32}ms`
  }
}
</script>

<template>
  <section class="evaluation-page">
    <ConsoleSideMenu active="/console/evaluations" />

    <div class="evaluation-content">
      <div class="eval-card mb-5">
        <div class="flex w-full flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex-1">
            <ElButton
              class="eval-radius-button"
              @click="router.push('/console/evaluations/create')"
            >
              {{ t('evaluation.createEvaluation') }}
            </ElButton>
          </div>
          <div v-if="evaluationCapabilities.canViewAllEvaluations" class="w-[200px]">
            <ElSegmented
              v-model="filters.me"
              :options="[
                { label: t('common.mine'), value: '1' },
                { label: t('common.all'), value: '0' }
              ]"
              class="eval-segmented"
              @change="switchScope"
            />
          </div>
          <div class="w-full lg:w-125">
            <ElInput
              v-model="filters.keyword"
              :placeholder="t('common.input')"
              class="input-with-select"
              style="--el-input-border-radius: 8px"
              clearable
              @keyup.enter="submitSearch"
              @clear="submitSearch"
            >
              <template #prepend>
                <ElSelect
                  v-model="filters.searchBy"
                  :placeholder="t('common.select')"
                  style="width: 115px"
                  @change="handleSearchByChange"
                >
                  <ElOption :label="t('common.model')" value="modelName" />
                  <ElOption :label="t('common.owner')" value="createUser" :disabled="isMineScope" />
                </ElSelect>
              </template>
              <template #append>
                <ElButton
                  class="eval-search-button"
                  :aria-label="t('common.search')"
                  :title="t('common.search')"
                  @click="submitSearch"
                />
              </template>
            </ElInput>
          </div>
        </div>
      </div>

      <div class="eval-card eval-list-card" :class="{ 'is-refreshing': isRefreshingList }">
        <span v-if="isRefreshingList" class="eval-list-refresh-bar" aria-hidden="true" />
        <div class="mb-4 text-base font-semibold">{{ t('evaluation.evaluationList') }}</div>
        <ElTable
          :key="tableAnimationKey"
          v-loading="isLoading"
          class="eval-list-table"
          :data="data?.list || []"
          row-key="id"
          style="width: 100%"
          :row-class-name="getRowClassName"
          :row-style="getRowStyle"
        >
          <ElTableColumn :label="t('common.name')" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <button
                v-if="canOpenEvaluation(row)"
                class="eval-anchor"
                type="button"
                @click="openDetail(row)"
              >
                {{ row.name }}
              </button>
              <span v-else class="eval-disabled-text">{{ row.name }}</span>
            </template>
          </ElTableColumn>
          <ElTableColumn
            prop="description"
            :label="t('common.description')"
            min-width="220"
            show-overflow-tooltip
          />
          <ElTableColumn :label="t('evaluation.deploymentMethod')" width="200">
            <template #default="{ row }">
              {{ sceneLabel(row.sence) }}
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('evaluation.domain')" width="130">
            <template #default="{ row }">
              <ElTag type="info">{{ domainLabel(row.domain) }}</ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('evaluation.datasets')" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <ElTag
                v-for="dataset in datasetLabels(row.datasets, datasetMap, row.datasetsConfig)"
                :key="dataset"
                class="dataset-summary__tag mr-1"
                type="primary"
                size="small"
              >
                {{ dataset }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn :label="t('common.createdAt')" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatDate(row.createdAt) }}
            </template>
          </ElTableColumn>
          <ElTableColumn
            prop="owner"
            :label="t('common.owner')"
            width="150"
            show-overflow-tooltip
          />
          <ElTableColumn :label="t('common.action')" width="180" fixed="right">
            <template #default="{ row }">
              <ElButton
                v-if="canOpenEvaluation(row)"
                link
                type="primary"
                @click="editEvaluation(row)"
              >
                {{ t('common.edit') }}
              </ElButton>
              <ElButton v-else link type="primary" disabled>{{ t('common.edit') }}</ElButton>
              <ElPopconfirm :title="t('evaluation.deleteConfirm')" @confirm="deleteEvaluation(row)">
                <template #reference>
                  <ElButton link type="primary">{{ t('common.delete') }}</ElButton>
                </template>
              </ElPopconfirm>
            </template>
          </ElTableColumn>
        </ElTable>

        <div class="mt-4 flex justify-end">
          <ElPagination
            v-model:current-page="page"
            v-model:page-size="pageSize"
            layout="total, sizes, prev, pager, next"
            :total="data?.total || 0"
            :page-sizes="[10, 20, 50]"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.evaluation-page {
  display: grid;
  grid-template-columns: 216px minmax(0, 1fr);
  gap: 24px;
  width: 100%;
}

.evaluation-content {
  min-width: 0;
}

.eval-card {
  border-radius: 8px;
  background: #fff;
  padding: 20px;
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
}

.eval-list-card {
  position: relative;
  overflow: hidden;
}

.eval-list-refresh-bar {
  position: absolute;
  top: 0;
  left: 20px;
  right: 20px;
  height: 2px;
  overflow: hidden;
  border-radius: 999px;
  background: rgb(23 98 238 / 10%);
}

.eval-list-refresh-bar::after {
  position: absolute;
  inset: 0;
  width: 36%;
  border-radius: inherit;
  background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
  content: '';
  animation: eval-list-refresh 900ms ease-in-out infinite;
}

.eval-list-card.is-refreshing .eval-list-table {
  opacity: 0.68;
  transition: opacity 160ms ease;
}

.eval-radius-button {
  --el-border-radius-base: 8px;
}

.eval-segmented {
  --el-border-radius-base: 8px;
}

.eval-search-button {
  width: 100%;
}

.eval-search-button::before {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentcolor;
  border-radius: 50%;
  content: '';
}

.eval-search-button::after {
  display: inline-block;
  width: 6px;
  height: 2px;
  margin-left: -2px;
  background: currentcolor;
  content: '';
  transform: rotate(45deg) translate(1px, 2px);
}

.eval-anchor {
  border: 0;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  padding: 0;
  text-align: left;
}

.eval-anchor:hover {
  text-decoration: underline;
}

.eval-disabled-text {
  color: var(--el-text-color-disabled);
  cursor: not-allowed;
}

.dataset-summary {
  display: flex;
  max-width: 100%;
  gap: 4px;
  overflow: hidden;
  white-space: nowrap;
}

.dataset-summary__tag {
  flex: 0 0 auto;
  max-width: 144px;
}

.dataset-summary__tag :deep(.el-tag__content) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.evaluation-row-enter) {
  animation: evaluation-row-enter 260ms cubic-bezier(0.2, 0, 0.2, 1) both;
  will-change: opacity, transform;
}

@keyframes evaluation-row-enter {
  from {
    opacity: 0;
    transform: translateY(3px);
  }

  70% {
    opacity: 1;
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes eval-list-refresh {
  from {
    transform: translateX(-110%);
  }

  to {
    transform: translateX(280%);
  }
}

:deep(.el-select__wrapper) {
  --el-border-radius-base: 8px;
}

@media (prefers-reduced-motion: reduce) {
  :deep(.evaluation-row-enter) {
    animation: none;
  }

  .eval-list-refresh-bar::after {
    animation: none;
  }
}

@media (max-width: 1023px) {
  .evaluation-page {
    grid-template-columns: 1fr;
  }
}
</style>
