<script setup lang="ts">
import { ElMenu, ElMenuItem, ElSubMenu } from 'element-plus'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

withDefaults(
  defineProps<{
    active?: string
  }>(),
  {
    active: '/console/evaluations'
  }
)

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const activeMenu = computed(() => {
  if (route.path.startsWith('/console/images')) {
    return '/console/images'
  }

  return '/console/evaluations'
})

const selectMenu = (index: string) => {
  void router.push(index)
}
</script>

<template>
  <aside class="console-menu">
    <ElMenu
      :key="activeMenu"
      class="console-menu__nav"
      :default-active="activeMenu"
      :default-openeds="['/console/evaluations']"
      @select="selectMenu"
    >
      <ElSubMenu index="/console/evaluations">
        <template #title>
          <span>{{ t('navigation.console') }}</span>
        </template>
        <ElMenuItem index="/console/evaluations">{{ t('navigation.modelEvaluation') }}</ElMenuItem>
      </ElSubMenu>
    </ElMenu>
  </aside>
</template>

<style scoped>
.console-menu {
  min-height: calc(100vh - 6rem);
  margin: -24px 0 -24px -40px;
  background: #f5f6f8;
  padding: 36px 8px 24px;
}

.console-menu__nav {
  --el-menu-bg-color: #f5f6f8;
  --el-menu-item-height: 46px;

  position: sticky;
  top: 88px;
  border: 0;
  background: transparent;
}

.console-menu__nav :deep(.el-sub-menu__title),
.console-menu__nav :deep(.el-menu-item) {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border-radius: 4px;
  margin-bottom: 8px;
  background: transparent !important;
  transition:
    color 0.22s ease,
    font-weight 0.22s ease,
    transform 0.22s ease;
}

.console-menu__nav :deep(.el-sub-menu__title)::before,
.console-menu__nav :deep(.el-menu-item)::before {
  position: absolute;
  z-index: -1;
  border-radius: inherit;
  background: linear-gradient(90deg, rgb(23 98 238 / 30%) 0%, rgb(23 98 238 / 0%) 100%);
  content: '';
  inset: 0;
  opacity: 0;
  transform: translateX(-8px);
  transition:
    opacity 0.24s ease,
    transform 0.24s ease,
    background 0.24s ease;
}

.console-menu__nav :deep(.el-sub-menu__title:hover),
.console-menu__nav :deep(.el-menu-item:hover) {
  color: var(--el-color-primary);
  transform: translate3d(2px, 0, 0);
}

.console-menu__nav :deep(.el-sub-menu__title:hover)::before,
.console-menu__nav :deep(.el-menu-item:hover)::before {
  background: #ebecf4;
  opacity: 1;
  transform: translateX(0);
}

.console-menu__nav :deep(.el-sub-menu .el-menu) {
  padding-top: 8px;
  background: transparent;
}

.console-menu__nav :deep(.el-sub-menu.is-active > .el-sub-menu__title),
.console-menu__nav :deep(.el-menu-item.is-active) {
  border-radius: 4px;
  background: transparent !important;
  color: var(--el-color-primary) !important;
  font-weight: 500;
}

.console-menu__nav :deep(.el-sub-menu.is-active > .el-sub-menu__title)::before,
.console-menu__nav :deep(.el-menu-item.is-active)::before {
  opacity: 1;
  transform: translateX(0);
}

.console-menu__nav :deep(.el-sub-menu.is-active > .el-sub-menu__title)::after,
.console-menu__nav :deep(.el-menu-item.is-active)::after {
  position: absolute;
  top: 7px;
  right: 0;
  width: 4px;
  height: calc(100% - 14px);
  border-radius: 4px 0 0 4px;
  background: var(--color-primary);
  content: '';
}

.console-menu__nav :deep(.el-sub-menu.is-active > .el-sub-menu__title:hover)::before,
.console-menu__nav :deep(.el-menu-item.is-active:hover)::before {
  background: linear-gradient(90deg, rgb(23 98 238 / 30%) 0%, rgb(23 98 238 / 0%) 100%);
}

@media (prefers-reduced-motion: reduce) {
  .console-menu__nav :deep(.el-sub-menu__title),
  .console-menu__nav :deep(.el-menu-item),
  .console-menu__nav :deep(.el-sub-menu__title)::before,
  .console-menu__nav :deep(.el-menu-item)::before {
    transition: none;
  }

  .console-menu__nav :deep(.el-sub-menu__title:hover),
  .console-menu__nav :deep(.el-menu-item:hover) {
    transform: none;
  }
}

@media (max-width: 1023px) {
  .console-menu {
    min-height: auto;
    margin: 0;
    padding: 12px;
  }

  .console-menu__nav {
    position: static;
  }
}
</style>
