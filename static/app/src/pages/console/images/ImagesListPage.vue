<script setup lang="ts">
import {
  ElButton,
  ElDrawer,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElPagination,
  ElPopconfirm,
  ElPopover,
  ElRow,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTooltip
} from 'element-plus'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { auditImage, deleteImage, getImages } from '@/api/images'
import type { ImageData } from '@/api/images/types'
import ConsoleSideMenu from '@/pages/console/components/ConsoleSideMenu.vue'
import PresetImage from './components/PresetImage.vue'
import { imageLabels, imageStatus, imageStatusStage, importMethods } from './imageLabels'

const FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
})

const router = useRouter()
const { t } = useI18n()
const activeTab = ref('presetImages')
const status = ref<string | undefined>()
const orderBy = ref<string | undefined>()
const isLoading = ref(false)
const tableData = ref<ImageData[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const showDockerfileModal = ref(false)
const dockerfileCommand = ref('')

const statusFilters = computed(() =>
  Object.entries(imageStatus).map(([value, text]) => ({
    text,
    value
  }))
)

const formatTime = (value?: string) => {
  if (!value) {
    return '-'
  }

  return FORMATTER.format(new Date(value)).replace(/\//g, '-')
}

const sourceLabel = (source?: string) => (source ? importMethods[source] || source : '-')
const statusLabel = (value?: string) => (value ? imageStatus[value] || value : '-')
const stageLabel = (value?: string) => (value ? imageStatusStage[value] || value : '-')

const creatorLabel = (user?: ImageData['user']) => {
  if (!user) {
    return '-'
  }

  if (typeof user === 'string') {
    return user
  }

  return user.username || user.name || user.email || String(user.id || '-')
}

const loadImages = async () => {
  isLoading.value = true
  try {
    const response = await getImages({
      pageIndex: page.value,
      pageSize: pageSize.value,
      status: status.value,
      orderBy: orderBy.value
    })
    tableData.value = response.list
    total.value = response.total
  } finally {
    isLoading.value = false
  }
}

const handleFilterChange = async (filters: Record<string, string[]>) => {
  const values = Object.values(filters)[0]
  status.value = values && values.length > 0 ? values[0] : undefined
  page.value = 1
  await nextTick()
  void loadImages()
}

const handleSortChange = async ({ prop, order }: { prop?: string; order?: string | null }) => {
  if (prop === 'createdAt' && order === 'ascending') {
    orderBy.value = 'id'
  } else if (prop === 'createdAt' && order === 'descending') {
    orderBy.value = '-id'
  } else {
    orderBy.value = undefined
  }

  page.value = 1
  await nextTick()
  void loadImages()
}

const handlePageChange = async (nextPage: number) => {
  page.value = nextPage
  await nextTick()
  void loadImages()
}

const handlePageSizeChange = async (nextPageSize: number) => {
  pageSize.value = nextPageSize
  page.value = 1
  await nextTick()
  void loadImages()
}

const routeToCreateImage = () => {
  void router.push('/console/images/create')
}

const handleShowDockerfile = (file?: string) => {
  dockerfileCommand.value = file ? `\`\`\`\n${file}\n\`\`\`` : ''
  showDockerfileModal.value = true
}

const actionDelete = async (image: ImageData) => {
  await deleteImage(image.id)
  ElMessage.success(t('images.deleteSuccess'))
  void loadImages()
}

const actionApprove = async (image: ImageData) => {
  await auditImage(image.id, { stage1Status: 'R' })
  ElMessage.success(t('images.submitSuccess'))
  void loadImages()
}

const actionDeny = async (image: ImageData) => {
  const { value } = await ElMessageBox.prompt('', imageLabels.denyTitle, {
    confirmButtonText: t('common.ok'),
    cancelButtonText: t('common.cancel')
  })

  await auditImage(image.id, { stage1Status: 'D', reason: value })
  ElMessage.success(t('images.submitSuccess'))
  void loadImages()
}

onMounted(() => {
  void loadImages()
})
</script>

<template>
  <section class="images-page">
    <ConsoleSideMenu active="/console/images" />

    <div class="images-content">
      <ElTabs v-model="activeTab" class="images-tabs">
        <ElTabPane :label="imageLabels.presetImages" name="presetImages">
          <div class="content-wrap">
            <ElRow class="w-full">
              <PresetImage class="w-full" />
            </ElRow>
          </div>
        </ElTabPane>

        <ElTabPane :label="imageLabels.customImagesLabel" name="customImages">
          <div>
            <div class="content-wrap mb-5">
              <ElRow class="w-full">
                <div class="flex w-full">
                  <ElButton size="large" class="mr-6" @click="routeToCreateImage">
                    + {{ imageLabels.importImages }}
                  </ElButton>
                  <ElAlert type="warning" :closable="false">
                    <template #title>
                      <ElText type="info">
                        {{ imageLabels.importTip }}
                      </ElText>
                    </template>
                  </ElAlert>
                </div>
                <div v-if="false" class="w-1/3">
                  <ElInput :placeholder="imageLabels.keywordsPlaceholder" clearable size="large" />
                </div>
              </ElRow>
            </div>

            <div class="content-wrap">
              <ElRow class="w-full">
                <ElTable
                  v-loading="isLoading"
                  :data="tableData"
                  row-key="id"
                  style="width: 100%"
                  border
                  stripe
                  show-overflow-tooltip
                  @filter-change="handleFilterChange"
                  @sort-change="handleSortChange"
                >
                  <ElTableColumn prop="id" :label="imageLabels.id" width="80" />
                  <ElTableColumn
                    :label="`${imageLabels.name} : ${imageLabels.tag}`"
                    min-width="120"
                  >
                    <template #default="{ row }">
                      <ElTooltip
                        :content="row.tag ? `${row.name}:${row.tag}` : row.name"
                        placement="top"
                      >
                        <span class="ellipsis">{{
                          row.tag ? `${row.name}:${row.tag}` : row.name
                        }}</span>
                      </ElTooltip>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn :label="imageLabels.source" min-width="110">
                    <template #default="{ row }">{{ sourceLabel(row.source) }}</template>
                  </ElTableColumn>
                  <ElTableColumn
                    prop="url"
                    :label="imageLabels.registryUrl"
                    min-width="200"
                    show-overflow-tooltip
                  />
                  <ElTableColumn :label="imageLabels.dockerfile" min-width="110">
                    <template #default="{ row }">
                      <ElLink type="primary" @click="handleShowDockerfile(row.dockerfile)">
                        {{ imageLabels.check }}
                      </ElLink>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn
                    column-key="status"
                    prop="status"
                    :label="imageLabels.status"
                    :filters="statusFilters"
                    :filter-multiple="false"
                    min-width="120"
                  >
                    <template #default="{ row }">
                      <span>{{ statusLabel(row.status) }}</span>
                      <ElPopover
                        v-if="row.status === 'D'"
                        placement="top"
                        :title="t('images.reason')"
                        :width="200"
                        trigger="click"
                        :content="row.reason"
                      >
                        <template #reference>
                          <span class="question ml-1">?</span>
                        </template>
                      </ElPopover>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn :label="imageLabels.first" min-width="110">
                    <template #default="{ row }">{{ stageLabel(row.stage1Status) }}</template>
                  </ElTableColumn>
                  <ElTableColumn :label="imageLabels.second" min-width="110">
                    <template #default="{ row }">{{ stageLabel(row.stage2Status) }}</template>
                  </ElTableColumn>
                  <ElTableColumn
                    prop="createdAt"
                    :label="imageLabels.createdTime"
                    sortable="custom"
                    min-width="165"
                  >
                    <template #default="{ row }">{{
                      formatTime(row.createdAt || row.created_at)
                    }}</template>
                  </ElTableColumn>
                  <ElTableColumn :label="imageLabels.creator" min-width="110" show-overflow-tooltip>
                    <template #default="{ row }">{{ creatorLabel(row.user) }}</template>
                  </ElTableColumn>
                  <ElTableColumn :label="imageLabels.action" width="200" fixed="right">
                    <template #default="{ row }">
                      <ElPopconfirm
                        :title="imageLabels.actionDeleteMessage"
                        confirm-button-type="danger"
                        width="240"
                        hide-icon
                        @confirm="actionDelete(row)"
                      >
                        <template #reference>
                          <ElButton link type="primary">{{ t('common.delete') }}</ElButton>
                        </template>
                      </ElPopconfirm>
                      <ElPopconfirm
                        :title="imageLabels.approveMessage"
                        confirm-button-type="danger"
                        width="200"
                        hide-icon
                        @confirm="actionApprove(row)"
                      >
                        <template #reference>
                          <ElButton link type="primary" :disabled="row.stage1Status !== 'P'">
                            {{ t('images.approve') }}
                          </ElButton>
                        </template>
                      </ElPopconfirm>
                      <ElButton
                        link
                        type="primary"
                        :disabled="row.stage1Status !== 'P'"
                        @click="actionDeny(row)"
                      >
                        {{ t('images.deny') }}
                      </ElButton>
                    </template>
                  </ElTableColumn>
                </ElTable>
              </ElRow>

              <div class="mt-4 flex justify-end">
                <ElPagination
                  v-model:current-page="page"
                  v-model:page-size="pageSize"
                  layout="total, sizes, prev, pager, next"
                  :total="total"
                  :page-sizes="[10]"
                  @current-change="handlePageChange"
                  @size-change="handlePageSizeChange"
                />
              </div>
            </div>
          </div>
        </ElTabPane>
      </ElTabs>
    </div>

    <ElDrawer
      v-model="showDockerfileModal"
      :title="imageLabels.dockerFileTitle"
      direction="rtl"
      size="40%"
    >
      <pre class="dockerfile-drawer">{{ dockerfileCommand || '-' }}</pre>
    </ElDrawer>
  </section>
</template>

<style scoped>
.images-page {
  display: grid;
  grid-template-columns: 216px minmax(0, 1fr);
  gap: 24px;
  width: 100%;
}

.images-content {
  min-width: 0;
}

.images-tabs {
  width: 100%;
  margin: 0 24px;
}

.images-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 0;
}

.images-tabs :deep(.el-tabs__content) {
  border-radius: 8px;
  background-color: #fff;
  padding: 16px;
}

.images-tabs :deep(.el-tabs__nav) {
  padding: 4px 0;
}

.images-tabs :deep(.el-tabs__item) {
  background-color: unset;
  color: #979cba;
  font-size: 20px;
  font-weight: 700;
}

.images-tabs :deep(.el-tabs__item.is-active),
.images-tabs :deep(.el-tabs__item:hover) {
  color: #292962;
}

.images-tabs :deep(.el-tabs__active-bar) {
  height: 5px;
  border-radius: 4px;
  background-color: unset;
}

.images-tabs :deep(.el-tabs__active-bar)::after {
  display: block;
  width: 48px;
  height: 5px;
  margin: 0 auto;
  border-radius: 8px;
  background: linear-gradient(90deg, #1762ee 0%, rgb(23 98 238 / 1%) 100%);
  content: '';
}

.images-tabs :deep(.el-table__column-filter-trigger > .el-icon > svg) {
  display: none;
}

.images-tabs :deep(.el-table__column-filter-trigger > .el-icon) {
  margin-left: 2px;
}

.content-wrap {
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: #fff;
  padding: 16px;
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
}

.ellipsis {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border: 1px solid currentcolor;
  border-radius: 50%;
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 11px;
  line-height: 1;
  vertical-align: text-top;
}

.dockerfile-drawer {
  min-height: 320px;
  overflow: auto;
  margin: 0;
  border-radius: 6px;
  background: #f6f8fa;
  padding: 16px;
  white-space: pre-wrap;
}

@media (max-width: 1023px) {
  .images-page {
    grid-template-columns: 1fr;
  }
}
</style>
