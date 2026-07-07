<script setup lang="ts">
import {
  ElButton,
  ElCol,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElRadio,
  ElRadioGroup,
  ElRow
} from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { createImage } from '@/api/images'
import type { ImageFormData } from '@/api/images'
import { imageLabels, importMethods } from '../imageLabels'

const regImageName = /^[a-z][-a-z0-9.]{1,126}[a-z0-9]$/

const formRef = ref<FormInstance>()
const loading = ref(false)
const router = useRouter()
const { t } = useI18n()

const checkTag = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value?.toLowerCase().includes('latest')) {
    callback(new Error(imageLabels.notLatest))
  } else {
    callback()
  }
}

const form = reactive<ImageFormData>({
  name: '',
  tag: '',
  url: '',
  source: 'P',
  dockerfile: '',
  comment: ''
})

const rules = reactive<FormRules<ImageFormData>>({
  name: [
    {
      required: true,
      message: t('evaluation.input', { item: imageLabels.name }),
      trigger: 'blur'
    },
    {
      pattern: regImageName,
      message: imageLabels.nameTip,
      trigger: 'blur'
    }
  ],
  url: [
    {
      required: true,
      message: t('evaluation.input', { item: imageLabels.url }),
      trigger: 'blur'
    }
  ],
  source: [
    {
      required: true,
      message: t('evaluation.select', { item: imageLabels.source }),
      trigger: 'change'
    }
  ],
  dockerfile: [
    {
      required: true,
      message: imageLabels.dockerfilePlaceholder,
      trigger: 'blur'
    }
  ],
  tag: [
    {
      required: false,
      validator: checkTag,
      trigger: 'blur'
    }
  ]
})

const cancel = () => {
  router.back()
}

const submitForm = async () => {
  if (!formRef.value) {
    return
  }

  const valid = await formRef.value.validate()
  if (!valid) {
    return
  }

  loading.value = true
  try {
    await createImage(form)
    ElMessage.success(imageLabels.submitSuccessMessage)
    void router.push('/console/images')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="image-form">
    <ElRow class="w-full">
      <ElCol :span="24">
        <ElForm
          ref="formRef"
          label-position="left"
          label-width="145px"
          :model="form"
          :rules="rules"
          status-icon
          require-asterisk-position="right"
        >
          <ElFormItem :label="imageLabels.name" prop="name">
            <ElInput
              v-model="form.name"
              maxlength="128"
              show-word-limit
              :placeholder="t('evaluation.input', { item: imageLabels.name })"
            />
          </ElFormItem>

          <ElFormItem :label="imageLabels.tag" prop="tag">
            <ElInput
              v-model="form.tag"
              :placeholder="t('evaluation.input', { item: imageLabels.tag })"
            />
          </ElFormItem>

          <ElFormItem :label="imageLabels.source" prop="source">
            <ElRadioGroup v-model="form.source">
              <ElRadio label="P">{{ importMethods.P }}</ElRadio>
              <ElRadio label="F" disabled>{{ importMethods.F }}</ElRadio>
            </ElRadioGroup>
          </ElFormItem>

          <ElFormItem :label="imageLabels.url" prop="url">
            <ElInput v-model="form.url" :placeholder="`Please input ${imageLabels.url}`" />
            <ElRow class="description">{{ imageLabels.urlDescription }}</ElRow>
          </ElFormItem>

          <ElFormItem :label="imageLabels.dockerfile" prop="dockerfile">
            <ElInput
              v-model="form.dockerfile"
              type="textarea"
              :autosize="{ minRows: 16 }"
              :placeholder="imageLabels.dockerfilePlaceholder"
            />
            <ElRow class="description"> {{ imageLabels.dockerfileDescription }}&nbsp;&nbsp; </ElRow>
          </ElFormItem>

          <ElFormItem :label="imageLabels.imageDesc" prop="comment">
            <ElInput
              v-model="form.comment"
              type="textarea"
              maxlength="256"
              show-word-limit
              :autosize="{ minRows: 4 }"
              :placeholder="t('evaluation.input', { item: imageLabels.imageDesc })"
            />
          </ElFormItem>

          <ElFormItem class="mt-[30px]">
            <ElButton class="ml-[155px] w-[80px]" @click="cancel">
              {{ t('common.cancel') }}
            </ElButton>
            <ElButton class="w-[80px]" type="primary" :loading="loading" @click="submitForm">
              {{ t('common.submit') }}
            </ElButton>
          </ElFormItem>
        </ElForm>
      </ElCol>
    </ElRow>
  </div>
</template>

<style scoped>
.image-form {
  width: 100%;
}

.image-form :deep(.el-form-item) {
  margin-bottom: 28px;
}

.description {
  color: var(--el-text-color-secondary);
}

.image-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--el-text-color-primary);
  font-weight: 700;
  line-height: 16px;
}

.image-form :deep(.el-textarea__inner),
.image-form :deep(.el-input__count-inner),
.image-form :deep(.el-textarea .el-input__count),
.image-form :deep(.el-input__wrapper) {
  background-color: #eff4fa;
}

.image-form
  :deep(
    .el-form-item.is-required:not(.is-no-asterisk).asterisk-left > .el-form-item__label
  )::before {
  margin: 0;
  content: '';
}

.image-form
  :deep(
    .el-form-item.is-required:not(.is-no-asterisk).asterisk-left > .el-form-item__label
  )::after {
  margin-left: 4px;
  color: var(--el-color-danger);
  content: '*';
}
</style>
