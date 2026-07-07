<script setup lang="ts">
import { ElPopover } from 'element-plus'
import { evalText } from '../evaluationFormLabels'
</script>

<template>
  <ElPopover placement="top-start" :width="200" trigger="hover">
    <p>{{ evalText.modelTypeTip1 }}</p>
    <p>{{ evalText.modelTypeTip2 }}</p>
    <template #reference>
      <span class="model-type-tip">
        <span class="model-type-tip__icon">?</span>
        <span class="model-type-tip__title">{{ evalText.modelType }}</span>
      </span>
    </template>
  </ElPopover>
</template>

<style scoped>
.model-type-tip {
  position: absolute;
  right: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.model-type-tip__icon {
  display: inline-flex;
  width: 16px;
  height: 16px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #e0e0e0;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.model-type-tip__title {
  color: var(--el-color-primary);
}
</style>
