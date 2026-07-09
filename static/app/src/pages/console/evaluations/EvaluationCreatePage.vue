<script setup lang="ts">
import {
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElRadio,
  ElRadioGroup,
  ElSegmented,
  ElSelect,
  type FormInstance,
  type FormRules
} from 'element-plus'
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { createEvaluation, getEvaluation, updateEvaluation } from '@/api/evaluations'
import { refreshCurrentUser } from '@/api/auth'
import backIcon from '@/assets/svgs/icon-back-rounded.svg'
import type { EvaluationDetail, EvaluationPayload } from '@/api/evaluations/types'
import EvalTitle from './components/EvalTitle.vue'
import ModelTypeTooltip from './components/ModelTypeTooltip.vue'
import MultimodalDatasetSelector from './components/MultimodalDatasetSelector.vue'
import NlpDatasetSelector from './components/NlpDatasetSelector.vue'
import UploadTokenizer from './components/UploadTokenizer.vue'
import { TOKENIZERS, evalText } from './evaluationFormLabels'

type EvaluationForm = EvaluationPayload & {
  domain: 'NLP' | 'Multimodal'
  pkgs: string[]
  datasetsConfig: NonNullable<EvaluationPayload['datasetsConfig']>
  onlineModelName: string
  onlineApiKey: string
  environVars: Record<string, unknown>
  paperUrl: string
  modelUrl: string
  tokenizerName: string
  pretrainedTokenizerId?: string
  maxSequenceLength: number | string
  endOfTextToken: string
  prefixToken: string
  dimensions: string[]
  robustEnv?: string
  modelGenKwargs: string
}

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const formRef = ref<FormInstance>()
const loading = ref(false)
const datasetCompletion = ref(false)

const evalId = computed(() => route.params.id as string | undefined)
const isEdit = computed(() => Boolean(evalId.value))

const ENV_OPTIONS = [
  'NVIDIA_A800-SXM4-80GB',
  'CAMBRICON_MLU370-S4',
  'Ascend 910B2 x Kunpeng 920',
  'MTT S4000'
]
const form = reactive<EvaluationForm>({
  sence: 'EA',
  name: '',
  description: '',
  domain: 'NLP',
  agreement: true,
  scenarios: [],
  datasets: [],
  pkgs: [],
  datasetsConfig: [],
  url: '',
  model: '',
  modelType: '',
  onlineModelName: '',
  onlineApiKey: '',
  environVars: {},
  paperUrl: '',
  modelUrl: '',
  tokenizerName: 'gpt2',
  pretrainedTokenizerId: undefined,
  maxSequenceLength: 2048,
  endOfTextToken: '</s>',
  prefixToken: '',
  dimensions: ['accuracy'],
  robustEnv: undefined,
  modelGenKwargs: ''
})

const isNlpOnline = computed(() => form.domain === 'NLP')

const modelTypeRules = computed(() => {
  if (isNlpOnline.value) {
    return []
  }
  return [{ required: true, message: evalText.select(evalText.modelType), trigger: 'change' }]
})

const tokenizerNameRules = computed(() => {
  if (isNlpOnline.value) {
    return []
  }
  return [{ required: true, message: evalText.select('tokenizer_name'), trigger: 'change' }]
})

const maxSequenceLengthRules = computed(() => {
  const positiveRule = {
    pattern: /^[1-9]\d*$/,
    message: 'Please enter positive integer'
  }
  if (isNlpOnline.value) {
    return [positiveRule]
  }
  return [
    { required: true, message: evalText.input('max_sequence_length'), trigger: 'change' },
    positiveRule
  ]
})

const endOfTextTokenRules = computed(() => {
  if (isNlpOnline.value) {
    return []
  }
  return [{ required: true, message: evalText.input('end_of_text_token'), trigger: 'change' }]
})

const rules = reactive<FormRules<EvaluationForm>>({
  name: [
    { required: true, message: evalText.input(evalText.name), trigger: 'blur' },
    {
      pattern: /^[a-zA-Z][-a-zA-Z0-9./_]{1,126}[a-zA-Z0-9]$/,
      message: evalText.modelNameCheck,
      trigger: 'blur'
    }
  ],
  sence: [{ required: true, message: evalText.select(evalText.scene), trigger: 'change' }],
  domain: [{ required: true, message: evalText.select(evalText.domain), trigger: 'change' }],
  datasets: [
    {
      required: true,
      message: evalText.select(evalText.evalDatasets),
      trigger: ['change', 'blur']
    },
    {
      validator: (_rule, _value, callback) => {
        if (form.domain === 'NLP' && form.pkgs.length > 1) {
          callback(new Error(evalText.nlpPackageTip))
          return
        }
        callback()
      },
      trigger: ['change', 'blur']
    }
  ],
  datasetsConfig: [
    { required: true, message: evalText.select(evalText.evalDatasets), trigger: ['change', 'blur'] }
  ],
  url: [{ required: true, message: evalText.input(evalText.url), trigger: 'blur' }],
  onlineModelName: [
    { required: true, message: evalText.input(evalText.onlineModel), trigger: 'blur' }
  ],
  onlineApiKey: [{ required: true, message: evalText.input(evalText.onlineKey), trigger: 'blur' }],
  robustEnv: [
    { required: true, message: evalText.select(evalText.environmentLabel), trigger: 'change' }
  ],
  agreement: [
    {
      type: 'enum',
      enum: [true],
      required: true,
      message: evalText.select(`“${evalText.agreement}”`)
    }
  ]
})

const domainOptions = ['NLP', 'Multimodal']
const deploymentMethodOptions = [{ label: 'Online Evaluation', value: 'EA' }]

const toDisplayDomain = (domain?: string): 'NLP' | 'Multimodal' => {
  if (domain === 'M' || domain === 'MM' || domain === 'Multimodal') {
    return 'Multimodal'
  }
  return 'NLP'
}

const toPayloadDomain = (domain: string) => (domain === 'Multimodal' ? 'M' : 'N')

const handleDomainSelectChange = () => {
  form.sence = 'EA'
  form.datasets = []
  form.datasetsConfig = []
  form.pkgs = []
  datasetCompletion.value = false
}

const handleModelTypeChange = (value: string | number | boolean | undefined) => {
  if (value === 'Base') {
    form.model = ''
  }
}

const datasetMounted = () => {
  if (isEdit.value) {
    datasetCompletion.value = true
  }
}

const populateForm = (evaluation: EvaluationDetail) => {
  form.sence = 'EA'
  form.name = evaluation.name || ''
  form.description = evaluation.description || ''
  form.domain = toDisplayDomain(evaluation.domain)
  form.agreement = evaluation.agreement ?? true
  form.datasets = evaluation.datasets || []
  form.datasetsConfig = evaluation.datasetsConfig || []
  form.pkgs = evaluation.pkgs || []
  form.url = evaluation.url || ''
  form.modelType = evaluation.modelType || (form.domain === 'Multimodal' ? 'direct-model' : '')
  form.onlineModelName = evaluation.onlineModelName || ''
  form.onlineApiKey = evaluation.onlineApiKey || ''
  form.environVars = evaluation.environVars || {}
  form.paperUrl = evaluation.paperUrl || ''
  form.modelUrl = evaluation.modelUrl || ''
  form.tokenizerName = evaluation.tokenizer?.tokenizerName || evaluation.tokenizerName || 'gpt2'
  form.pretrainedTokenizerId = evaluation.pretrainedTokenizerId || undefined
  if (form.pretrainedTokenizerId) {
    form.tokenizerName = 'pretrainedTokenizerId'
  }
  form.maxSequenceLength =
    evaluation.tokenizer?.maxSequenceLength || evaluation.maxSequenceLength || 2048
  form.endOfTextToken = evaluation.tokenizer?.endOfTextToken || evaluation.endOfTextToken || '</s>'
  form.prefixToken = evaluation.tokenizer?.prefixToken || evaluation.prefixToken || ''
  form.dimensions = evaluation.includeRobustness ? ['accuracy', 'robustness'] : ['accuracy']
  form.robustEnv = evaluation.robustEnv
  form.modelGenKwargs = evaluation.modelGenKwargs || ''
}

const buildPayload = () => {
  const payload: EvaluationPayload = {
    ...form,
    sence: 'EA',
    domain: toPayloadDomain(form.domain),
    datasets:
      form.domain === 'Multimodal'
        ? form.datasetsConfig.map((dataset) => Number(dataset.id)).filter(Boolean)
        : form.datasets,
    datasetsConfig: form.domain === 'Multimodal' ? form.datasetsConfig : undefined,
    tokenizer: {
      tokenizerName: form.tokenizerName,
      maxSequenceLength: form.maxSequenceLength,
      endOfTextToken: form.endOfTextToken,
      prefixToken: form.prefixToken
    },
    includeRobustness: form.dimensions.includes('robustness'),
    environVars: {
      ...form.environVars,
      ...(form.onlineApiKey ? { openaiApiKey: form.onlineApiKey } : {})
    }
  }

  if (form.tokenizerName === 'pretrainedTokenizerId') {
    payload.tokenizer = {
      ...payload.tokenizer,
      tokenizerName: undefined
    }
    payload.pretrainedTokenizerId = form.pretrainedTokenizerId
  }

  return payload
}

const submitForm = async (formEl?: FormInstance) => {
  if (!formEl) {
    return
  }

  await formEl.validate(async (valid) => {
    if (!valid) {
      return
    }

    if (form.tokenizerName === 'pretrainedTokenizerId' && !form.pretrainedTokenizerId) {
      ElMessage.warning(evalText.uploadTokenizerMessage)
      return
    }

    loading.value = true
    try {
      const payload = buildPayload()
      if (evalId.value) {
        await updateEvaluation(evalId.value, payload)
        await router.push(`/console/evaluations/${evalId.value}`)
        await refreshCurrentUser()
        ElMessage.success(t('evaluation.evaluationUpdated'))
      } else {
        const response = await createEvaluation(payload)
        await router.push(`/console/evaluations/${response.id}`)
        await refreshCurrentUser()
        ElMessage.success(t('evaluation.evaluationCreated'))
      }
    } finally {
      loading.value = false
    }
  })
}

const cancel = () => {
  void router.push('/console/evaluations')
}

const handleTokenizerChange = (value: string) => {
  if (value === 'pretrainedTokenizerId') {
    ElMessage.warning(evalText.uploadTokenizerMessage)
    return
  }
  form.pretrainedTokenizerId = undefined
}

const handleUploadSuccess = (value: string) => {
  form.pretrainedTokenizerId = value
}

watch(
  () => form.domain,
  (value) => {
    form.sence = 'EA'
    if (value === 'Multimodal') {
      form.modelType = 'direct-model'
    }
    if (value === 'NLP' && !['Base', 'SFT'].includes(form.modelType || '')) {
      form.modelType = ''
    }
  }
)

watch(
  () => form.dimensions,
  (value) => {
    if (!value.includes('robustness')) {
      form.robustEnv = undefined
    }
  }
)

onBeforeMount(async () => {
  if (!evalId.value) {
    return
  }

  const evaluation = await getEvaluation(evalId.value)
  populateForm(evaluation)
})
</script>

<template>
  <section class="evaluation-form-page">
    <div class="evaluation-page-head" @click="router.back()">
      <img class="evaluation-page-head__back" :src="backIcon" alt="" />
      <span class="evaluation-page-head__title">{{
        isEdit ? t('router.editEvaluation') : t('router.createEvaluation')
      }}</span>
    </div>
    <div class="evaluation-form-card">
      <ElForm
        ref="formRef"
        label-position="left"
        label-width="170px"
        :model="form"
        :rules="rules"
        status-icon
        require-asterisk-position="right"
      >
        <ElFormItem :label="evalText.domain" prop="domain">
          <ElSegmented
            v-model="form.domain"
            size="large"
            :disabled="isEdit"
            :options="domainOptions"
            @change="handleDomainSelectChange"
          />
        </ElFormItem>

        <EvalTitle>{{ evalText.basicData }}</EvalTitle>

        <ElFormItem
          :label="evalText.name"
          prop="name"
          style="margin-bottom: 28px"
          :class="{ complete: form.name }"
        >
          <ElInput
            v-model="form.name"
            size="large"
            maxlength="128"
            show-word-limit
            :placeholder="evalText.input(evalText.name)"
            :formatter="(value: string) => value.trim()"
            :disabled="isEdit"
          />
        </ElFormItem>

        <ElFormItem
          :label="evalText.description"
          prop="description"
          :class="{ complete: form.description }"
        >
          <ElInput
            v-model="form.description"
            size="large"
            maxlength="256"
            show-word-limit
            :placeholder="evalText.input(evalText.description)"
            type="textarea"
          />
        </ElFormItem>

        <ElFormItem v-if="form.domain === 'NLP'" :label="evalText.evalDatasets" prop="datasets">
          <NlpDatasetSelector
            v-model="form.datasets"
            v-model:packages="form.pkgs"
            :completion="datasetCompletion"
            @completed="datasetCompletion = $event"
            @mounted="datasetMounted"
          />
        </ElFormItem>

        <ElFormItem
          v-if="form.domain === 'Multimodal'"
          :label="evalText.tasks"
          prop="datasetsConfig"
        >
          <MultimodalDatasetSelector
            v-model="form.datasetsConfig"
            :completion="datasetCompletion"
            @completed="datasetCompletion = $event"
            @mounted="datasetMounted"
          />
        </ElFormItem>

        <ElFormItem :label="evalText.scene" prop="sence">
          <ElRadioGroup v-model="form.sence">
            <ElRadio v-for="item in deploymentMethodOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </ElRadio>
          </ElRadioGroup>
        </ElFormItem>

        <ElFormItem :label="evalText.dimensions" required>
          <ElCheckboxGroup v-model="form.dimensions">
            <ElCheckbox disabled value="accuracy">
              {{ t('evaluationBatch.accuracyEvaluation') }}
            </ElCheckbox>
            <ElCheckbox value="robustness">
              {{ t('evaluationBatch.robustnessEvaluation') }}
            </ElCheckbox>
          </ElCheckboxGroup>
        </ElFormItem>

        <ElFormItem
          v-if="form.dimensions.includes('robustness')"
          :label="evalText.environmentLabel"
          required
          prop="robustEnv"
        >
          <ElSelect
            v-model="form.robustEnv"
            :placeholder="evalText.select(evalText.environmentLabel)"
          >
            <ElOption v-for="item in ENV_OPTIONS" :key="item" :label="item" :value="item" />
          </ElSelect>
        </ElFormItem>

        <ElFormItem :label="evalText.url" prop="url">
          <ElInput
            v-model="form.url"
            size="large"
            :placeholder="evalText.input(evalText.url)"
            :formatter="(value: string) => value.trim()"
          />
          <div class="description">
            {{ evalText.interfaceTip }}
            <a
              href="https://github.com/eclipse-paneval/paneval-platform/blob/ccb94fbb3675613c850e216ba6271594923c0ebc/docs/paneval-api-interface-requirements.md"
              target="_blank"
              rel="noopener noreferrer"
              style="color: #1762ee"
            >
              {{ evalText.interfaceIntroduction }}
            </a>
          </div>
        </ElFormItem>

        <ElFormItem :label="evalText.onlineModel" prop="onlineModelName">
          <ElInput
            v-model="form.onlineModelName"
            size="large"
            :placeholder="evalText.input(evalText.onlineModel)"
            :formatter="(value: string) => value.trim()"
          />
        </ElFormItem>

        <ElFormItem :label="evalText.onlineKey" prop="onlineApiKey">
          <ElInput
            v-model="form.onlineApiKey"
            size="large"
            :placeholder="evalText.input(evalText.onlineKey)"
            :formatter="(value: string) => value.trim()"
          />
        </ElFormItem>

        <EvalTitle>{{ evalText.modelData }}</EvalTitle>

        <ElFormItem
          v-if="form.domain === 'NLP'"
          class="relative"
          :label="evalText.modelType"
          prop="modelType"
          :rules="modelTypeRules"
        >
          <ElRadioGroup v-model="form.modelType" @change="handleModelTypeChange">
            <ElRadio value="Base">Base</ElRadio>
            <ElRadio value="SFT">SFT</ElRadio>
          </ElRadioGroup>
          <ModelTypeTooltip />
        </ElFormItem>

        <ElFormItem
          v-if="form.domain === 'Multimodal'"
          class="relative"
          :label="evalText.modelType"
          prop="modelType"
          required
        >
          <ElRadioGroup v-model="form.modelType" @change="handleModelTypeChange">
            <ElRadio value="direct-model">{{ t('evaluation.directInferenceModel') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>

        <template v-if="form.domain === 'NLP'">
          <ElFormItem :label="evalText.modelGenKwargs" prop="modelGenKwargs">
            <ElInput
              v-model="form.modelGenKwargs"
              size="large"
              :placeholder="evalText.input(evalText.modelGenKwargs)"
            />
          </ElFormItem>
          <ElFormItem
            class="relative"
            label="tokenizer_name"
            prop="tokenizerName"
            :rules="tokenizerNameRules"
          >
            <ElSelect
              v-model="form.tokenizerName"
              :placeholder="evalText.select('tokenizer_name')"
              class="w-full"
              size="large"
              @change="handleTokenizerChange"
            >
              <ElOption :label="evalText.pretrainedTokenizerId" value="pretrainedTokenizerId" />
              <ElOption v-for="item in TOKENIZERS" :key="item" :label="item" :value="item" />
            </ElSelect>
            <div v-if="form.tokenizerName === 'pretrainedTokenizerId'" class="mt-6 w-full">
              <UploadTokenizer @get-id="handleUploadSuccess" />
            </div>
          </ElFormItem>
          <ElFormItem
            class="relative"
            label="max_sequence_length"
            prop="maxSequenceLength"
            :rules="maxSequenceLengthRules"
          >
            <ElInput
              v-model.number="form.maxSequenceLength"
              size="large"
              :placeholder="evalText.input('max_sequence_length')"
            />
          </ElFormItem>
          <ElFormItem
            class="relative"
            label="end_of_text_token"
            prop="endOfTextToken"
            :rules="endOfTextTokenRules"
          >
            <ElInput
              v-model="form.endOfTextToken"
              size="large"
              :placeholder="evalText.input('end_of_text_token')"
            />
          </ElFormItem>
          <ElFormItem class="relative" label="prefix_token" prop="prefixToken">
            <ElInput
              v-model="form.prefixToken"
              size="large"
              :placeholder="evalText.input('prefix_token')"
            />
          </ElFormItem>
        </template>

        <ElFormItem :label="evalText.paperUrl" prop="paperUrl">
          <ElInput
            v-model="form.paperUrl"
            size="large"
            :placeholder="evalText.input(evalText.paperUrl)"
            :formatter="(value: string) => value.trim()"
          />
        </ElFormItem>

        <ElFormItem :label="evalText.modelUrl" prop="modelUrl">
          <ElInput
            v-model="form.modelUrl"
            size="large"
            :placeholder="evalText.input(evalText.modelUrl)"
            :formatter="(value: string) => value.trim()"
          />
        </ElFormItem>

        <ElFormItem class="agreement-form-item" prop="agreement">
          <ElCheckbox v-model="form.agreement" class="agreement-checkbox">
            {{ evalText.agreement }}
          </ElCheckbox>
        </ElFormItem>

        <ElFormItem class="form-actions">
          <ElButton
            class="w-20"
            type="default"
            bg
            text
            style="--el-fill-color-light: #f2f2f2; --el-button-text-color: #b2b2b2"
            @click="cancel"
          >
            {{ evalText.cancel }}
          </ElButton>
          <ElButton class="w-20" :loading="loading" type="primary" @click="submitForm(formRef)">
            {{ evalText.submit }}
          </ElButton>
        </ElFormItem>
      </ElForm>
    </div>
  </section>
</template>

<style scoped>
.evaluation-form-page {
  width: 100%;
  padding: 24px 40px;
}

.evaluation-form-card {
  --regular-color: #292962;
  --el-border-radius-base: 8px;
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 8px;
  background: #fff;
  padding: 24px 15vw 32px 40px;
}

.evaluation-page-head {
  display: flex;
  max-width: 1400px;
  align-items: center;
  margin: 0 auto 24px;
  cursor: pointer;
}

.evaluation-page-head__back {
  width: 32px;
  height: 32px;
  margin-right: 12px;
}

.evaluation-page-head__title {
  color: #292962;
  font-size: 28px;
  font-weight: 700;
}

.description {
  width: 100%;
  margin-top: 6px;
  color: #999;
  font-size: 12px;
  line-height: 18px;
}

.warning-tip {
  margin-left: 5px;
  color: #999;
  cursor: pointer;
}

:deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--el-text-color-primary);
  font-weight: 700;
  line-height: 16px;
}

:deep(.el-textarea__inner),
:deep(.el-input__count-inner),
:deep(.el-textarea .el-input__count),
:deep(.el-input__wrapper) {
  --el-input-border-color: #e9e9e9;
  --el-input-hover-border: rgba(41, 41, 98, 0.5);
}

:deep(.el-input .el-input__count .el-input__count-inner),
:deep(.el-textarea .el-input__count) {
  background: unset;
  color: #acacac;
}

:deep(.el-input),
:deep(.el-select),
:deep(.el-textarea) {
  --el-input-text-color: var(--regular-color);
}

.complete :deep(.el-input__wrapper) {
  --el-input-border-color: #fff;
  background-color: rgba(23, 98, 238, 0.05);
}

.complete :deep(.el-textarea) {
  --el-input-bg-color: rgba(23, 98, 238, 0.05);
}

.complete :deep(.el-textarea__inner) {
  --el-input-border-color: #fff;
}

:deep(.el-segmented) {
  --el-border-radius-base: 8px;
}

:deep(.el-segmented--large .el-segmented__item) {
  padding: 0 20px;
}

.agreement-form-item {
  margin-bottom: 34px;
}

.agreement-form-item :deep(.el-form-item__content) {
  min-width: 0;
  align-items: flex-start;
  line-height: 1.45;
}

.agreement-form-item :deep(.el-form-item__error) {
  position: relative;
  top: auto;
  left: auto;
  width: 100%;
  padding-top: 8px;
  line-height: 1.45;
}

.agreement-checkbox {
  width: 100%;
  height: auto;
  align-items: flex-start;
  white-space: normal;
}

.agreement-checkbox :deep(.el-checkbox__input) {
  margin-top: 3px;
}

.agreement-checkbox :deep(.el-checkbox__label) {
  min-width: 0;
  font-weight: 600;
  line-height: 1.45;
  overflow-wrap: anywhere;
  white-space: normal;
}

.form-actions {
  margin-top: 8px;
  margin-bottom: 0;
}

.form-actions :deep(.el-form-item__content) {
  display: flex;
  gap: 16px;
}

.form-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}
</style>
