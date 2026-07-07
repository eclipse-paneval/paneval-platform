<script setup lang="ts">
import { computed, onMounted } from 'vue'
import {
  ElAvatar,
  ElDescriptions,
  ElDescriptionsItem,
  ElLink,
  ElSkeleton,
  ElTag,
  ElText
} from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { refreshCurrentUser } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useLoginDialogStore } from '@/stores/loginDialog'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const loginDialogStore = useLoginDialogStore()

const user = computed(() => authStore.user)
const displayName = computed(
  () => user.value?.username || user.value?.name || user.value?.email || '-'
)
const avatarInitial = computed(() => displayName.value.slice(0, 1).toUpperCase())
const contactLine = computed(() => user.value?.email || user.value?.phone || 'PanEval account')
const emptyText = computed(() => t('mine.notProvided'))

const valueOrDash = (value?: string | number | boolean) => {
  if (value === undefined || value === null || value === '') {
    return emptyText.value
  }

  return String(value)
}

const taskLabels = computed(() => {
  const labels: Record<string, string> = {
    EA: t('mine.onlineEvaluation'),
    EM: t('mine.offlineEvaluation')
  }

  return (user.value?.tasks || []).map((item) => labels[item] || item)
})

const statusLabel = computed(() => {
  const status = user.value?.status
  if (!status) {
    return '-'
  }

  return t(`mine.status.${status}`, status)
})

const statusType = computed(() => {
  const status = user.value?.status
  if (status === 'A') return 'success'
  if (status === 'D') return 'danger'
  if (status === 'P') return 'warning'
  return 'info'
})

onMounted(() => {
  void refreshCurrentUser().catch(() => {
    loginDialogStore.open({
      redirectTo: '/mine'
    })
    void router.push({
      name: 'home'
    })
  })
})
</script>

<template>
  <section class="mine-page">
    <div class="mine-page__shell">
      <div class="mine-page__header">
        <div>
          <h1 class="mine-page__title">{{ t('mine.title') }}</h1>
          <p class="mine-page__subtitle">PanEval account profile</p>
        </div>
        <ElTag v-if="user" class="mine-status" :type="statusType" effect="light" round>
          {{ statusLabel }}
        </ElTag>
      </div>

      <ElSkeleton v-if="!user" :rows="9" animated />

      <template v-else>
        <section class="mine-summary" aria-label="Account summary">
          <div class="mine-summary__identity">
            <ElAvatar :size="68" :src="user.avatar || undefined" class="mine-summary__avatar">
              {{ avatarInitial }}
            </ElAvatar>
            <div class="mine-summary__copy">
              <h2>{{ displayName }}</h2>
              <p>{{ contactLine }}</p>
            </div>
          </div>
          <div class="mine-summary__meta">
            <div>
              <span>ID</span>
              <strong>{{ valueOrDash(user.id) }}</strong>
            </div>
            <div>
              <span>{{ t('mine.tasks') }}</span>
              <strong>{{
                taskLabels.length ? t('mine.enabledCount', { count: taskLabels.length }) : emptyText
              }}</strong>
            </div>
          </div>
        </section>

        <ElDescriptions class="mine-descriptions" size="large" border :column="1">
          <ElDescriptionsItem :label="t('mine.username')">
            <ElText :type="user.username ? undefined : 'info'">{{
              valueOrDash(user.username)
            }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="ID">
            <ElText :type="user.id ? undefined : 'info'">{{ valueOrDash(user.id) }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('mine.email')">
            <ElText :type="user.email ? undefined : 'info'">{{ valueOrDash(user.email) }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('common.name')">
            <ElText :type="user.name ? undefined : 'info'">{{ valueOrDash(user.name) }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('mine.organization')">
            <div class="mine-stack">
              <ElText :type="user.organization ? undefined : 'info'">
                {{ valueOrDash(user.organization) }}
              </ElText>
              <ElText v-if="user.organizationEn" type="info">{{ user.organizationEn }}</ElText>
            </div>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('mine.phone')">
            <ElText :type="user.phone ? undefined : 'info'">{{ valueOrDash(user.phone) }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('mine.researcher')">
            <ElText>{{ user.isResearcher ? t('mine.yes') : t('mine.no') }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('mine.selfResearchModel')">
            <ElText>{{ user.isPrivateModel ? t('mine.yes') : t('mine.no') }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('mine.tasks')">
            <div v-if="taskLabels.length" class="mine-tags">
              <ElTag v-for="item in taskLabels" :key="item" type="primary">{{ item }}</ElTag>
            </div>
            <ElText v-else type="info">{{ emptyText }}</ElText>
          </ElDescriptionsItem>
          <ElDescriptionsItem v-if="user.huggingface" :label="t('mine.huggingFace')">
            <ElLink :href="user.huggingface" type="primary" target="_blank">
              {{ user.huggingface }}
            </ElLink>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="t('mine.reviewStatus')">
            <ElTag :type="statusType" effect="light" round>{{ statusLabel }}</ElTag>
          </ElDescriptionsItem>
        </ElDescriptions>
      </template>
    </div>
  </section>
</template>

<style scoped>
.mine-page {
  min-height: 100vh;
  padding: 104px 24px 56px;
  background:
    radial-gradient(circle at 18% 8%, rgb(23 98 238 / 10%), transparent 28%),
    radial-gradient(circle at 82% 4%, rgb(21 184 166 / 8%), transparent 24%),
    linear-gradient(180deg, rgb(23 98 238 / 5%), transparent 260px), var(--color-page);
}

.mine-page__shell {
  max-width: 1120px;
  margin: 0 auto;
  border-radius: 8px;
  background: #fff;
  padding: 30px 34px 38px;
  box-shadow:
    0 18px 42px rgb(0 6 98 / 8%),
    0 1px 0 rgb(255 255 255 / 90%) inset;
}

.mine-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.mine-page__title {
  margin: 0;
  color: var(--color-text-strong);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0;
}

.mine-page__subtitle {
  margin: 6px 0 0;
  color: var(--color-text-muted);
  font-size: 14px;
}

.mine-status {
  min-width: 96px;
  justify-content: center;
  font-weight: 600;
}

.mine-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 28px;
  margin-bottom: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgb(23 98 238 / 10%), rgb(21 184 166 / 8%)), #f7faff;
  padding: 24px;
}

.mine-summary__identity {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 18px;
}

.mine-summary__avatar {
  flex: 0 0 auto;
  background: var(--gradient-primary);
  color: #fff;
  font-size: 24px;
  font-weight: 700;
}

.mine-summary__copy {
  min-width: 0;
}

.mine-summary__copy h2 {
  margin: 0;
  overflow: hidden;
  color: var(--color-text-strong);
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mine-summary__copy p {
  margin: 7px 0 0;
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mine-summary__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(88px, 1fr));
  gap: 10px;
}

.mine-summary__meta div {
  min-width: 0;
  border-radius: 8px;
  background: rgb(255 255 255 / 76%);
  padding: 12px 14px;
}

.mine-summary__meta span {
  display: block;
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.2;
}

.mine-summary__meta strong {
  display: block;
  margin-top: 8px;
  overflow: hidden;
  color: var(--color-text-strong);
  font-size: 16px;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mine-descriptions {
  max-width: 820px;
}

.mine-descriptions :deep(.el-descriptions__body) {
  overflow: hidden;
}

.mine-descriptions :deep(.el-descriptions__label) {
  width: 210px;
  background: #f6f8fc;
  color: var(--color-text-muted);
  font-weight: 650;
}

.mine-descriptions :deep(.el-descriptions__content) {
  color: var(--color-text-strong);
  font-weight: 500;
}

.mine-descriptions :deep(.el-link) {
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.mine-stack {
  display: grid;
  gap: 8px;
}

.mine-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 767px) {
  .mine-page {
    padding: 88px 16px 32px;
  }

  .mine-page__shell {
    padding: 22px 16px 28px;
  }

  .mine-page__header,
  .mine-summary,
  .mine-summary__identity {
    align-items: flex-start;
  }

  .mine-page__header,
  .mine-summary {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .mine-summary__meta {
    width: 100%;
    grid-template-columns: 1fr;
  }

  .mine-descriptions {
    max-width: 100%;
  }

  .mine-descriptions :deep(.el-descriptions__label) {
    width: 132px;
  }
}
</style>
