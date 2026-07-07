<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Hide, Lock, User, View } from '@element-plus/icons-vue'
import {
  ElAlert,
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage
} from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { loginApi, refreshCurrentUser } from '@/api/auth'
import { useLoginDialogStore } from '@/stores/loginDialog'

type LoginForm = {
  username: string
  password: string
}

const { t } = useI18n()
const router = useRouter()
const loginDialogStore = useLoginDialogStore()
const { visible, redirectTo } = storeToRefs(loginDialogStore)
const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')
const isPasswordVisible = ref(false)
const activeField = ref<keyof LoginForm | null>(null)
const visualRef = ref<HTMLElement>()

const form = reactive<LoginForm>({
  username: '',
  password: ''
})

const rules = computed<FormRules<LoginForm>>(() => ({
  username: [{ required: true, message: t('auth.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('auth.passwordRequired'), trigger: 'blur' }]
}))

const resetForm = () => {
  form.username = ''
  form.password = ''
  errorMessage.value = ''
  isPasswordVisible.value = false
  activeField.value = null
  formRef.value?.clearValidate()
}

const closeDialog = () => {
  loginDialogStore.close()
}

const updateVisualPointer = (event: PointerEvent) => {
  const visualEl = visualRef.value
  if (!visualEl) return

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = (event.clientX - rect.left) / rect.width - 0.5
  const y = (event.clientY - rect.top) / rect.height - 0.5
  const visualRect = visualEl.getBoundingClientRect()

  visualEl.style.setProperty('--pointer-x', x.toFixed(3))
  visualEl.style.setProperty('--pointer-y', y.toFixed(3))
  visualEl.style.setProperty('--glow-x', `${event.clientX - visualRect.left}px`)
  visualEl.style.setProperty('--glow-y', `${event.clientY - visualRect.top}px`)
}

const resetVisualPointer = () => {
  const visualEl = visualRef.value
  if (!visualEl) return

  visualEl.style.setProperty('--pointer-x', '0')
  visualEl.style.setProperty('--pointer-y', '0')
  visualEl.style.setProperty('--glow-x', '50%')
  visualEl.style.setProperty('--glow-y', '50%')
}

const submitLogin = async () => {
  const formEl = formRef.value
  if (!formEl || loading.value) return

  const valid = await formEl.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  errorMessage.value = ''

  try {
    await loginApi({
      username: form.username.trim(),
      password: form.password
    })
    await refreshCurrentUser()

    const target = redirectTo.value
    loginDialogStore.close()
    loginDialogStore.resetRedirect()
    ElMessage.success(t('auth.loginSuccess'))

    if (target) {
      await router.push(target)
    }
  } catch {
    errorMessage.value = t('auth.loginFailed')
  } finally {
    loading.value = false
  }
}

watch(visible, (isVisible) => {
  if (isVisible) {
    errorMessage.value = ''
    return
  }

  resetForm()
})
</script>

<template>
  <ElDialog
    v-model="visible"
    class="global-login-dialog"
    width="820px"
    :show-close="!loading"
    :close-on-click-modal="!loading"
    :close-on-press-escape="!loading"
    align-center
    append-to-body
    @close="closeDialog"
  >
    <div class="login-panel" @pointermove="updateVisualPointer" @pointerleave="resetVisualPointer">
      <button
        type="button"
        class="login-panel__close"
        :aria-label="t('common.cancel')"
        :disabled="loading"
        @click="closeDialog"
      >
        <span aria-hidden="true" />
      </button>

      <aside ref="visualRef" class="login-panel__visual" aria-hidden="true">
        <div class="login-panel__visual-grid" />
        <div class="login-panel__orbit">
          <span class="login-panel__orbit-ring login-panel__orbit-ring--outer" />
          <span class="login-panel__orbit-ring login-panel__orbit-ring--inner" />
          <span class="login-panel__orbit-node login-panel__orbit-node--one" />
          <span class="login-panel__orbit-node login-panel__orbit-node--two" />
          <div class="login-panel__score">
            <span>PE</span>
            <strong>Eval Core</strong>
          </div>
        </div>
      </aside>

      <section class="login-panel__content">
        <div class="login-panel__header">
          <div class="login-panel__mark" aria-hidden="true">PE</div>
          <div>
            <p class="login-panel__eyebrow">{{ t('auth.secureAccess') }}</p>
            <h2>{{ t('auth.title') }}</h2>
          </div>
        </div>

        <p class="login-panel__copy">{{ t('auth.description') }}</p>

        <ElAlert
          v-if="errorMessage"
          class="login-panel__alert"
          :title="errorMessage"
          type="error"
          :closable="false"
          show-icon
        />

        <ElForm
          ref="formRef"
          class="login-panel__form"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="submitLogin"
        >
          <ElFormItem
            :class="[
              'login-panel__field',
              {
                'is-active': activeField === 'username',
                'has-value': form.username.length > 0
              }
            ]"
            :label="t('auth.username')"
            prop="username"
          >
            <ElInput
              v-model.trim="form.username"
              class="login-panel__input"
              :placeholder="t('auth.usernamePlaceholder')"
              autocomplete="username"
              :disabled="loading"
              size="large"
              @focus="activeField = 'username'"
              @blur="activeField = null"
            >
              <template #prefix>
                <ElIcon class="login-panel__input-icon"><User /></ElIcon>
              </template>
            </ElInput>
          </ElFormItem>

          <ElFormItem
            :class="[
              'login-panel__field',
              {
                'is-active': activeField === 'password',
                'has-value': form.password.length > 0
              }
            ]"
            :label="t('auth.password')"
            prop="password"
          >
            <ElInput
              v-model="form.password"
              class="login-panel__input"
              :type="isPasswordVisible ? 'text' : 'password'"
              :placeholder="t('auth.passwordPlaceholder')"
              autocomplete="current-password"
              :disabled="loading"
              size="large"
              @focus="activeField = 'password'"
              @blur="activeField = null"
              @keyup.enter="submitLogin"
            >
              <template #prefix>
                <ElIcon class="login-panel__input-icon"><Lock /></ElIcon>
              </template>
              <template #suffix>
                <button
                  type="button"
                  class="login-panel__password-toggle"
                  :aria-label="isPasswordVisible ? t('auth.hidePassword') : t('auth.showPassword')"
                  :disabled="loading"
                  @click="isPasswordVisible = !isPasswordVisible"
                >
                  <ElIcon>
                    <View v-if="!isPasswordVisible" />
                    <Hide v-else />
                  </ElIcon>
                </button>
              </template>
            </ElInput>
          </ElFormItem>

          <ElButton
            class="login-panel__submit"
            type="primary"
            :loading="loading"
            @click="submitLogin"
          >
            {{ t('auth.submit') }}
          </ElButton>
        </ElForm>
      </section>
    </div>
  </ElDialog>
</template>

<style scoped>
:global(.global-login-dialog) {
  border-radius: 8px;
  overflow: hidden;
}

:global(.global-login-dialog .el-dialog__header) {
  display: none;
}

:global(.global-login-dialog .el-dialog__body) {
  padding: 0;
}

.login-panel {
  position: relative;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  min-height: 470px;
  padding: 28px;
  background: #fff;
}

.login-panel__close {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 2;
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 8px;
  color: rgb(41 41 98 / 52%);
  background: rgb(255 255 255 / 52%);
  cursor: pointer;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition:
    color 160ms ease,
    transform 160ms ease,
    background 160ms ease,
    border-color 160ms ease;
}

.login-panel__close span,
.login-panel__close span::after {
  display: block;
  width: 13px;
  height: 1.5px;
  content: '';
  background: currentcolor;
  border-radius: 999px;
}

.login-panel__close span {
  transform: rotate(45deg);
}

.login-panel__close span::after {
  transform: rotate(90deg);
}

.login-panel__close:hover:not(:disabled) {
  border-color: rgb(23 98 238 / 12%);
  color: var(--color-primary);
  background: #fff;
  transform: translateY(-1px);
}

.login-panel__close:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.login-panel__visual {
  --glow-x: 50%;
  --glow-y: 50%;
  --pointer-x: 0;
  --pointer-y: 0;

  position: relative;
  display: grid;
  min-height: 414px;
  place-items: center;
  overflow: hidden;
  padding: 28px;
  border-radius: 8px;
  color: #fff;
  background:
    radial-gradient(circle at var(--glow-x) var(--glow-y), rgb(255 255 255 / 22%), transparent 28%),
    radial-gradient(circle at 28% 22%, rgb(118 183 255 / 48%), transparent 27%),
    radial-gradient(circle at 72% 70%, rgb(21 184 166 / 30%), transparent 31%),
    linear-gradient(145deg, #1762ee 0%, #0a3cae 54%, #11174a 100%);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 22%);
  transition: background-position 220ms ease;
}

.login-panel__visual::before,
.login-panel__visual::after {
  position: absolute;
  content: '';
  pointer-events: none;
}

.login-panel__visual::before {
  inset: -54px auto auto -42px;
  width: 172px;
  height: 172px;
  border: 1px solid rgb(255 255 255 / 22%);
  border-radius: 999px;
}

.login-panel__visual::after {
  right: -44px;
  bottom: -58px;
  width: 190px;
  height: 190px;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 999px;
  background: radial-gradient(circle, rgb(255 255 255 / 9%), transparent 58%);
}

.login-panel__visual-grid {
  position: absolute;
  inset: 0;
  opacity: 0.2;
  background-image:
    linear-gradient(rgb(255 255 255 / 16%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(255 255 255 / 16%) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(180deg, #000, transparent 86%);
}

.login-panel__orbit {
  position: relative;
  width: 206px;
  height: 206px;
  margin: 0;
  transform: translate(calc(var(--pointer-x) * 18px), calc(var(--pointer-y) * 18px));
  transition: transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__orbit-ring {
  position: absolute;
  border: 1px solid rgb(255 255 255 / 24%);
  border-radius: 999px;
  transition:
    border-color 220ms ease,
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__orbit-ring--outer {
  inset: 0;
  box-shadow: 0 0 48px rgb(93 177 255 / 22%);
  transform: translate(calc(var(--pointer-x) * -8px), calc(var(--pointer-y) * -8px));
}

.login-panel__orbit-ring--inner {
  inset: 32px;
  border-color: rgb(255 255 255 / 36%);
  transform: translate(calc(var(--pointer-x) * 7px), calc(var(--pointer-y) * 7px));
}

.login-panel__orbit-node {
  position: absolute;
  width: 10px;
  height: 10px;
  border: 2px solid rgb(255 255 255 / 78%);
  border-radius: 999px;
  background: #7ee7ff;
  box-shadow: 0 0 18px rgb(126 231 255 / 82%);
  transition:
    box-shadow 220ms ease,
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__orbit-node--one {
  top: 24px;
  right: 42px;
  transform: translate(calc(var(--pointer-x) * 16px), calc(var(--pointer-y) * 16px));
}

.login-panel__orbit-node--two {
  bottom: 40px;
  left: 22px;
  background: #8bf5c8;
  box-shadow: 0 0 18px rgb(139 245 200 / 72%);
  transform: translate(calc(var(--pointer-x) * -14px), calc(var(--pointer-y) * -14px));
}

.login-panel__score {
  position: absolute;
  inset: 48px;
  display: grid;
  place-content: center;
  border: 1px solid rgb(255 255 255 / 22%);
  border-radius: 999px;
  background: rgb(255 255 255 / 11%);
  text-align: center;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transform: translate(calc(var(--pointer-x) * 10px), calc(var(--pointer-y) * 10px));
  transition:
    background 220ms ease,
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__score span {
  color: #fff;
  font-size: 24px;
  font-weight: 850;
  letter-spacing: 0;
}

.login-panel__score strong {
  color: rgb(255 255 255 / 72%);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.login-panel__content {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  padding: 18px 26px 18px 46px;
}

.login-panel__header {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-panel__mark {
  display: flex;
  width: 46px;
  height: 46px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: var(--gradient-primary);
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0;
}

.login-panel__eyebrow {
  margin: 0 0 4px;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.login-panel h2 {
  margin: 0;
  color: var(--color-text-strong);
  font-size: 22px;
  font-weight: 750;
  letter-spacing: 0;
}

.login-panel__copy {
  margin: 16px 0 22px;
  color: var(--color-text-muted);
  font-size: 14px;
  line-height: 1.7;
}

.login-panel__alert {
  margin-bottom: 18px;
}

.login-panel__form {
  display: grid;
  gap: 4px;
}

.login-panel__field {
  position: relative;
}

.login-panel__field :deep(.el-form-item__error) {
  position: relative;
  top: auto;
  left: auto;
  padding-top: 6px;
  font-size: 12px;
  line-height: 1.25;
}

.login-panel__form :deep(.el-form-item__label) {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin-bottom: 8px;
  color: var(--color-text-strong);
  font-size: 14px;
  font-weight: 750;
  letter-spacing: 0;
  transform-origin: left center;
  transition:
    color 220ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1),
    text-shadow 220ms ease;
}

.login-panel__form :deep(.el-form-item__label::after) {
  position: absolute;
  right: 0;
  bottom: -2px;
  left: 16px;
  height: 2px;
  content: '';
  background: linear-gradient(90deg, var(--color-primary), rgb(63 186 255 / 74%));
  border-radius: 999px;
  box-shadow: 0 6px 14px rgb(23 98 238 / 22%);
  opacity: 0;
  transform: scaleX(0);
  transform-origin: left center;
  transition:
    opacity 220ms ease,
    transform 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__field.is-active :deep(.el-form-item__label) {
  color: var(--color-primary);
  text-shadow: 0 8px 22px rgb(23 98 238 / 18%);
  transform: translateY(-2px) scale(0.96);
}

.login-panel__field.is-active :deep(.el-form-item__label::after) {
  opacity: 1;
  transform: scaleX(1);
}

.login-panel__field.has-value:not(.is-active) :deep(.el-form-item__label) {
  color: rgb(41 41 98 / 86%);
}

.login-panel__form
  :deep(.el-form-item.is-required:not(.is-no-asterisk) .el-form-item__label::before) {
  color: var(--color-danger);
  transition: color 220ms ease;
}

.login-panel__field.is-active
  :deep(.el-form-item.is-required:not(.is-no-asterisk) .el-form-item__label::before) {
  color: var(--color-primary);
}

.login-panel__input {
  width: 100%;
}

.login-panel__input :deep(.el-input__wrapper) {
  min-height: 46px;
  padding: 0 14px;
  border-radius: 8px;
  background: #f3f5fa;
  box-shadow: none;
  transition:
    background 160ms ease,
    box-shadow 220ms ease,
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__input :deep(.el-input__wrapper:hover) {
  background: #eef2f8;
  box-shadow: none;
}

.login-panel__input :deep(.el-input__wrapper.is-focus) {
  background: #fff;
  box-shadow:
    0 0 0 2px rgb(23 98 238 / 16%),
    0 12px 26px rgb(23 98 238 / 10%);
  transform: translateY(-1px);
}

.login-panel__input :deep(.el-input__inner) {
  color: var(--color-text-strong);
  font-size: 14px;
  font-weight: 650;
}

.login-panel__input :deep(.el-input__inner::placeholder) {
  color: rgb(41 41 98 / 40%);
  font-weight: 500;
}

.login-panel__input-icon {
  margin-right: 7px;
  color: rgb(41 41 98 / 48%);
  font-size: 18px;
  transition:
    color 220ms ease,
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__field.is-active .login-panel__input-icon {
  color: var(--color-primary);
  transform: scale(1.08);
}

.login-panel__password-toggle {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 8px;
  color: rgb(41 41 98 / 38%);
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  transition:
    color 160ms ease,
    background 160ms ease;
}

.login-panel__password-toggle:hover:not(:disabled) {
  color: var(--color-primary);
  background: rgb(23 98 238 / 7%);
}

.login-panel__password-toggle:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.login-panel__submit {
  position: relative;
  width: 100%;
  height: 44px;
  margin-top: 14px;
  border: 0;
  border-radius: 8px;
  overflow: hidden;
  background:
    linear-gradient(
      120deg,
      rgb(57 122 255 / 0%) 0%,
      rgb(57 122 255 / 0%) 36%,
      #2b74ff 58%,
      #0f46c9 100%
    ),
    var(--gradient-primary);
  background-position:
    100% 0,
    0 0;
  background-size:
    240% 100%,
    100% 100%;
  font-weight: 700;
  transition:
    background-position 420ms cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 220ms ease,
    transform 220ms ease,
    filter 220ms ease;
}

.login-panel__submit :deep(span) {
  position: relative;
  z-index: 1;
}

.login-panel__submit::before {
  position: absolute;
  inset: 0;
  content: '';
  background: linear-gradient(90deg, transparent, rgb(255 255 255 / 22%), transparent);
  opacity: 0;
  transform: translateX(-70%);
  transition:
    opacity 220ms ease,
    transform 520ms cubic-bezier(0.22, 1, 0.36, 1);
}

.login-panel__submit:hover:not(.is-disabled) {
  background-position:
    0 0,
    0 0;
  box-shadow: 0 12px 26px rgb(23 98 238 / 24%);
  filter: brightness(1.03);
  transform: translateY(-1px);
}

.login-panel__submit:hover:not(.is-disabled)::before {
  opacity: 1;
  transform: translateX(70%);
}

@media (max-width: 760px) {
  :global(.global-login-dialog) {
    width: calc(100vw - 32px) !important;
  }

  .login-panel {
    display: block;
    padding: 24px;
  }

  .login-panel__visual {
    display: none;
  }

  .login-panel__content {
    padding: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-panel__form :deep(.el-form-item__label),
  .login-panel__form :deep(.el-form-item__label::after),
  .login-panel__input :deep(.el-input__wrapper),
  .login-panel__input-icon,
  .login-panel__orbit,
  .login-panel__orbit-ring,
  .login-panel__orbit-node,
  .login-panel__score,
  .login-panel__submit,
  .login-panel__submit::before {
    transition: none;
  }

  .login-panel__orbit,
  .login-panel__orbit-ring,
  .login-panel__orbit-node,
  .login-panel__score {
    transform: none;
  }
}
</style>
