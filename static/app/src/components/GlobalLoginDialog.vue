<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ArrowRight, Hide, Lock, User, View } from '@element-plus/icons-vue'
import {
  ElAlert,
  ElButton,
  ElCheckbox,
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
import { getCachedOidcStatus, getOidcStatus, loginApi, oidcLoginUrl, refreshCurrentUser } from '@/api/auth'
import { useLoginDialogStore } from '@/stores/loginDialog'
import SsoFingerprintIcon from './SsoFingerprintIcon.vue'

type LoginForm = {
  username: string
  password: string
}

type LoginMode = 'checking' | 'password' | 'sso'

const { t } = useI18n()
const router = useRouter()
const loginDialogStore = useLoginDialogStore()
const { visible, redirectTo } = storeToRefs(loginDialogStore)
const formRef = ref<FormInstance>()
const loading = ref(false)
const loginMode = ref<LoginMode>('password')
const errorMessage = ref('')
const isPasswordVisible = ref(false)
const activeField = ref<keyof LoginForm | null>(null)
const visualRef = ref<HTMLElement>()
const ssoAgreement = ref(false)
const oidcStatusCheckId = ref(0)
const privacyUrl = 'https://www.eclipse.org/legal/privacy.php'
const termsUrl = 'https://www.eclipse.org/legal/termsofuse.php'

const form = reactive<LoginForm>({
  username: '',
  password: ''
})

const isPasswordMode = computed(() => loginMode.value === 'password')
const dialogWidth = computed(() => (isPasswordMode.value ? '820px' : '560px'))

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
  ssoAgreement.value = false
  formRef.value?.clearValidate()
}

const closeDialog = () => {
  loginDialogStore.close()
}

const handleDialogClosed = () => {
  loginMode.value = 'password'
  loading.value = false
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

const checkOidcAvailability = async () => {
  const checkId = oidcStatusCheckId.value + 1
  oidcStatusCheckId.value = checkId
  loading.value = false
  errorMessage.value = ''
  ssoAgreement.value = false

  const cachedStatus = getCachedOidcStatus()
  if (cachedStatus) {
    loginMode.value = cachedStatus.enabled ? 'sso' : 'password'
    return
  }

  loginMode.value = 'checking'

  try {
    const status = await getOidcStatus()
    if (oidcStatusCheckId.value !== checkId || !visible.value) return
    loginMode.value = status.enabled ? 'sso' : 'password'
  } catch {
    if (oidcStatusCheckId.value !== checkId || !visible.value) return
    loginMode.value = 'password'
  }
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

const submitSsoLogin = () => {
  if (!ssoAgreement.value || loading.value) return

  loading.value = true
  loginDialogStore.persistOidcRedirectTarget()
  window.location.assign(oidcLoginUrl)
}

watch(visible, (isVisible) => {
  if (isVisible) {
    void checkOidcAvailability()
    return
  }

  oidcStatusCheckId.value += 1
  resetForm()
})
</script>

<template>
  <ElDialog
    v-model="visible"
    :class="['global-login-dialog', { 'global-login-dialog--sso': !isPasswordMode }]"
    :width="dialogWidth"
    :show-close="!loading"
    :close-on-click-modal="!loading"
    :close-on-press-escape="!loading"
    align-center
    append-to-body
    @close="closeDialog"
    @closed="handleDialogClosed"
  >
    <div
      v-if="loginMode === 'password'"
      class="login-panel"
      @pointermove="updateVisualPointer"
      @pointerleave="resetVisualPointer"
    >
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

    <div v-else class="sso-panel" :class="{ 'sso-panel--checking': loginMode === 'checking' }">
      <button
        type="button"
        class="sso-panel__close"
        :aria-label="t('common.cancel')"
        :disabled="loading"
        @click="closeDialog"
      >
        <span aria-hidden="true" />
      </button>

      <div class="sso-panel__accent" aria-hidden="true" />

      <section class="sso-panel__content" aria-labelledby="sso-panel-title">
        <div
          class="sso-panel__identity-icon"
          :class="{ 'sso-panel__identity-icon--checking': loginMode === 'checking' }"
          aria-hidden="true"
        >
          <SsoFingerprintIcon />
        </div>

        <div class="sso-panel__header">
          <h2 id="sso-panel-title">
            {{ loginMode === 'sso' ? t('auth.sso.title') : t('auth.sso.checkingTitle') }}
          </h2>
          <p>
            {{
              loginMode === 'sso' ? t('auth.sso.subtitle') : t('auth.sso.checkingDescription')
            }}
          </p>
        </div>

        <div v-if="loginMode === 'sso'" class="sso-panel__security-note">
          <ElIcon class="sso-panel__security-icon"><Lock /></ElIcon>
          <i18n-t keypath="auth.sso.securityMessage" tag="p">
            <template #provider>
              <strong>{{ t('auth.sso.provider') }}</strong>
            </template>
          </i18n-t>
        </div>

        <ElCheckbox
          v-if="loginMode === 'sso'"
          v-model="ssoAgreement"
          class="sso-panel__agreement"
          :disabled="loading"
        >
          <i18n-t keypath="auth.sso.agreementMessage" tag="span">
            <template #terms>
              <a :href="termsUrl" target="_blank" rel="noopener noreferrer" @click.stop>
                {{ t('auth.sso.terms') }}
              </a>
            </template>
            <template #privacy>
              <a :href="privacyUrl" target="_blank" rel="noopener noreferrer" @click.stop>
                {{ t('auth.sso.privacy') }}
              </a>
            </template>
          </i18n-t>
        </ElCheckbox>

        <button
          v-if="loginMode === 'sso'"
          type="button"
          class="sso-panel__submit"
          :class="{ 'is-disabled': !ssoAgreement || loading, 'is-loading': loading }"
          :disabled="!ssoAgreement || loading"
          @click="submitSsoLogin"
        >
          <ElIcon v-if="!loading" class="sso-panel__submit-shield"><Lock /></ElIcon>
          <span>{{ loading ? t('auth.sso.redirecting') : t('auth.sso.submit') }}</span>
          <ElIcon v-if="!loading" class="sso-panel__submit-arrow"><ArrowRight /></ElIcon>
        </button>
      </section>
    </div>
  </ElDialog>
</template>

<style scoped>
:global(.global-login-dialog) {
  --el-dialog-padding-primary: 0;

  border-radius: 8px;
  overflow: hidden;
}

:global(.global-login-dialog .el-dialog__header) {
  display: none;
}

:global(.global-login-dialog .el-dialog__body) {
  padding: 0;
}

:global(.global-login-dialog--sso) {
  border-radius: 28px;
  background: transparent;
  box-shadow: none;
}

.sso-panel {
  position: relative;
  overflow: hidden;
  min-height: 676px;
  border-radius: 28px;
  background: #fff;
  box-shadow: 0 22px 54px rgb(31 48 89 / 16%);
}

.sso-panel__accent {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 10px;
  border-radius: 28px 28px 0 0;
  background: linear-gradient(90deg, #1762ee 0%, #3357f4 62%, #5638f4 100%);
}

.sso-panel__close {
  position: absolute;
  top: 18px;
  right: 20px;
  z-index: 2;
  display: inline-flex;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 10px;
  color: #91a0bd;
  background: transparent;
  cursor: pointer;
  transition:
    color 160ms ease,
    background 160ms ease,
    transform 160ms ease;
}

.sso-panel__close span,
.sso-panel__close span::after {
  display: block;
  width: 14px;
  height: 1.7px;
  content: '';
  background: currentcolor;
  border-radius: 999px;
}

.sso-panel__close span {
  transform: rotate(45deg);
}

.sso-panel__close span::after {
  transform: rotate(90deg);
}

.sso-panel__close:hover:not(:disabled) {
  color: #1762ee;
  background: #f3f6fc;
  transform: translateY(-1px);
}

.sso-panel__close:disabled {
  cursor: not-allowed;
  opacity: 0.48;
}

.sso-panel__content {
  display: flex;
  min-height: 676px;
  flex-direction: column;
  align-items: center;
  padding: 62px 36px 50px;
}

.sso-panel__identity-icon {
  display: inline-flex;
  width: 80px;
  height: 80px;
  align-items: center;
  justify-content: center;
  margin-top: 10px;
  border: 1px solid rgb(23 98 238 / 8%);
  border-radius: 20px;
  background:
    radial-gradient(circle at 50% 22%, rgb(255 255 255 / 92%), transparent 42%),
    linear-gradient(145deg, #edf5ff 0%, #dbe9ff 100%);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 70%),
    0 14px 26px rgb(23 98 238 / 13%);
  color: #1762ee;
  font-size: 38px;
}

.sso-panel__identity-icon svg {
  width: 46px;
  height: 46px;
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3.2;
}

.sso-panel__identity-icon--checking {
  animation: sso-breathe 1.2s ease-in-out infinite;
}

.sso-panel__header {
  margin-top: 40px;
  text-align: center;
}

.sso-panel__header h2 {
  margin: 0;
  color: #1e2a3e;
  font-size: 31px;
  font-weight: 820;
  letter-spacing: 0;
  line-height: 1.12;
}

.sso-panel__header p {
  margin: 13px 0 0;
  color: #64748f;
  font-size: 18px;
  line-height: 1.35;
}

.sso-panel__security-note {
  display: grid;
  width: 100%;
  grid-template-columns: 24px minmax(0, 1fr);
  gap: 16px;
  margin-top: 52px;
  padding: 16px;
  border: 1px solid #edf1f7;
  border-radius: 18px;
  background: #fbfcff;
  color: #475671;
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 80%);
}

.sso-panel__security-icon {
  margin-top: 2px;
  color: #8da0bc;
  font-size: 22px;
}

.sso-panel__security-note p {
  margin: 0;
  font-size: 18px;
  line-height: 1.55;
  text-align: left;
}

.sso-panel__security-note strong {
  color: #2c3c55;
  font-weight: 780;
}

.sso-panel__agreement {
  display: inline-flex;
  width: auto;
  max-width: 100%;
  align-self: flex-start;
  align-items: center;
  margin-top: 30px;
  color: #475671;
}

.sso-panel__agreement :deep(.el-checkbox__input) {
  align-self: center;
  margin-top: 0;
}

.sso-panel__agreement :deep(.el-checkbox__label) {
  color: #475671;
  font-size: 16px;
  line-height: 1.45;
  padding-left: 8px;
  white-space: normal;
}

.sso-panel__agreement a {
  color: #075ef4;
  text-decoration: none;
}

.sso-panel__agreement a:hover {
  text-decoration: underline;
}

.sso-panel__submit {
  display: inline-flex;
  width: 100%;
  height: 70px;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 22px;
  border: 0;
  border-radius: 18px;
  font: inherit;
  color: #fff;
  font-size: 20px;
  font-weight: 780;
  text-decoration: none;
  transition:
    background 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.sso-panel__submit:not(.is-disabled) {
  background: linear-gradient(100deg, #1762ee 0%, #1458ee 58%, #5142ec 100%);
  box-shadow: 0 14px 28px rgb(23 98 238 / 24%);
  cursor: pointer;
}

.sso-panel__submit:not(.is-disabled):hover {
  box-shadow: 0 18px 34px rgb(23 98 238 / 30%);
  transform: translateY(-1px);
}

.sso-panel__submit.is-disabled,
.sso-panel__submit.is-disabled:hover,
.sso-panel__submit.is-loading,
.sso-panel__submit.is-loading:hover {
  background: #cbd5e1;
  color: #fff;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.sso-panel__submit-shield,
.sso-panel__submit-arrow {
  color: currentcolor;
  font-size: 22px;
  opacity: 0.62;
}

.sso-panel--checking .sso-panel__content {
  justify-content: center;
}

.sso-panel--checking .sso-panel__header {
  margin-top: 28px;
}

@keyframes sso-breathe {
  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.04);
  }
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

  .sso-panel {
    min-height: auto;
    border-radius: 22px;
  }

  .sso-panel__content {
    min-height: auto;
    padding: 48px 26px 34px;
  }

  .sso-panel__identity-icon {
    width: 68px;
    height: 68px;
    border-radius: 18px;
    font-size: 32px;
  }

  .sso-panel__header {
    margin-top: 30px;
  }

  .sso-panel__header h2 {
    font-size: 26px;
  }

  .sso-panel__header p {
    font-size: 16px;
  }

  .sso-panel__security-note {
    grid-template-columns: 24px minmax(0, 1fr);
    gap: 12px;
    margin-top: 38px;
    padding: 22px 20px;
  }

  .sso-panel__security-note p,
  .sso-panel__agreement :deep(.el-checkbox__label) {
    font-size: 16px;
  }

  .sso-panel__submit {
    height: 60px;
    border-radius: 16px;
    font-size: 18px;
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

  .sso-panel__identity-icon--checking {
    animation: none;
  }
}
</style>
