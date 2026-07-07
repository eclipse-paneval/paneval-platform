<script setup lang="ts">
import { ElButton, ElLink, ElMessage, ElNotification, ElUpload } from 'element-plus'
import type { UploadProps, UploadUserFile } from 'element-plus'
import { computed, onBeforeMount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createTokenizerUpload } from '@/api/evaluations'
import { evalText } from '../evaluationFormLabels'

const emit = defineEmits<{
  getId: [value: string]
}>()

const fileList = ref<UploadUserFile[]>([])
const tokenizerId = ref('')
const { t } = useI18n()

const csrfToken = computed(() => {
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${encodeURIComponent('csrftoken')}=`))
  return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : undefined
})

const uploadAction = computed(() =>
  tokenizerId.value ? `/api/evaluations/tokenizers/${tokenizerId.value}` : ''
)

const getTokenizerId = async () => {
  const response = await createTokenizerUpload()
  tokenizerId.value = String(response.id)
}

const handleUploadSuccess = () => {
  ElMessage.success(t('evaluation.uploadSuccess'))
  emit('getId', tokenizerId.value)
}

const handleUploadError = (error: Error) => {
  let message = error.message
  try {
    message = JSON.parse(error.message).detail || message
  } catch {
    // Keep the raw upload error if it is not JSON.
  }
  ElNotification({
    title: t('common.error'),
    message,
    type: 'error'
  })
}

const beforeRemove: UploadProps['beforeRemove'] = () => {
  ElMessage.error(t('evaluation.cannotRemoveFile'))
  return false
}

onBeforeMount(() => {
  void getTokenizerId()
})
</script>

<template>
  <div class="upload-tokenizer">
    <ElUpload
      ref="uploadRef"
      v-model:file-list="fileList"
      :action="uploadAction"
      with-credentials
      multiple
      :headers="{ 'X-CSRFToken': csrfToken || '' }"
      :auto-upload="true"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      :before-remove="beforeRemove"
    >
      <template #trigger>
        <ElButton type="primary">{{ evalText.uploadTokenizer }}</ElButton>
      </template>
    </ElUpload>
    <div class="tip">
      <span>{{ evalText.uploadTokenizerComment }}</span>
      <ElLink
        type="primary"
        target="_blank"
        href="https://huggingface.co/docs/transformers/main_classes/tokenizer"
      >
        huggingface
      </ElLink>
    </div>
  </div>
</template>

<style scoped>
.upload-tokenizer {
  position: relative;
  width: 100%;
}

.tip {
  position: absolute;
  top: 0;
  left: 120px;
  width: 450px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 20px;
}
</style>
