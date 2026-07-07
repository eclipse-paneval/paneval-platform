<script setup lang="ts">
import { ElText, ElTree } from 'element-plus'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  treeData: unknown
  disabledKeys?: string[]
}>()

type TreeNode = {
  label: string
  parent: string
  children: TreeNode[] | null
  metric?: string
}

const expanded = ref(false)
const treeRef = ref<InstanceType<typeof ElTree>>()
const { t } = useI18n()

const defaultProps = {
  children: 'children',
  label: 'label'
}

const format = (data: unknown, parent = ''): TreeNode[] | null => {
  if (!data || typeof data !== 'object') {
    return null
  }

  return Object.entries(data as Record<string, unknown>)
    .filter(([key]) => !props.disabledKeys?.includes(key))
    .map(([key, value]) => ({
      label: key,
      parent,
      children: format(value, key),
      metric: typeof value === 'number' ? value.toFixed(4) : undefined
    }))
}

const treeData = computed(() => format(props.treeData) || [])
const canToggle = computed(() => treeData.value.some((item) => item.children?.length))

const handleExpand = () => {
  Object.values(treeRef.value?.store?.nodesMap || {}).forEach((node) => {
    if (expanded.value) {
      node.collapse()
    } else {
      node.expand()
    }
  })
  expanded.value = !expanded.value
}
</script>

<template>
  <div class="mm-tree">
    <div class="relative">
      <ElText
        v-if="canToggle"
        type="primary"
        size="small"
        class="absolute right-0 top-0 z-10 cursor-pointer"
        @click="handleExpand"
      >
        {{ expanded ? t('common.collapseAll') : t('common.expandAll') }}
      </ElText>
    </div>
    <ElTree
      ref="treeRef"
      :data="treeData"
      :props="defaultProps"
      empty-text=""
      :default-expand-all="false"
      class="w-full"
    >
      <template #default="{ node, data }">
        <div class="custom-tree-node">
          <div class="flex-1">
            <ElText size="small">{{ node.label }}</ElText>
          </div>
          <div class="metric">
            <ElText size="small" type="info">{{ data?.metric }}</ElText>
          </div>
        </div>
      </template>
    </ElTree>
  </div>
</template>

<style scoped>
.mm-tree {
  width: 100%;
}

.custom-tree-node {
  display: flex;
  flex: 1;
  align-items: center;
  font-size: 14px;
  line-height: 24px;
}

.metric {
  display: flex;
  flex-shrink: 0;
  width: 100px;
}

.mm-tree :deep(.el-tree) {
  background-color: unset;
}
</style>
