<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElAvatar, ElDropdown, ElDropdownItem, ElDropdownMenu, ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { logoutApi, refreshCurrentUser } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useLoginDialogStore } from '@/stores/loginDialog'

type NavItem = {
  labelKey: string
  to: string
  target?: '_blank'
}

const navItems: NavItem[] = [
  { labelKey: 'navigation.home', to: '/' },
  { labelKey: 'navigation.guide', to: '/documents/', target: '_blank' }
]

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const loginDialogStore = useLoginDialogStore()
const isRefreshing = ref(false)
const isSessionPending = ref(!authStore.isAuthenticated)
const isMobileMenuOpen = ref(false)
const isElevated = ref(false)

const displayName = computed(() => authStore.displayName || t('navigation.account'))
const avatarInitial = computed(() => displayName.value.slice(0, 1).toUpperCase())

const refreshSession = async () => {
  if (authStore.isAuthenticated) {
    isSessionPending.value = false
    return
  }

  if (isRefreshing.value) return

  isRefreshing.value = true
  try {
    await refreshCurrentUser()
  } catch {
    // Public pages should stay readable when there is no active session.
  } finally {
    isRefreshing.value = false
    isSessionPending.value = false
  }
}

const handleLogout = async () => {
  try {
    await logoutApi()
    authStore.clearUser()
    isMobileMenuOpen.value = false
    await router.push('/')
  } catch {
    ElMessage.error(t('navigation.failedToSignOut'))
  }
}

const goToProfile = async () => {
  isMobileMenuOpen.value = false
  await router.push('/mine')
}

const openLogin = () => {
  isMobileMenuOpen.value = false
  loginDialogStore.open({
    redirectTo: route.fullPath === '/' ? '' : route.fullPath
  })
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const syncNavigationSurface = () => {
  isElevated.value = window.scrollY > 28
}

onMounted(() => {
  void refreshSession()
  syncNavigationSurface()
  window.addEventListener('scroll', syncNavigationSurface, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', syncNavigationSurface)
})

watch(
  () => route.fullPath,
  () => {
    closeMobileMenu()
  }
)
</script>

<template>
  <header class="app-top-nav fixed inset-x-0 top-0 z-50" :class="{ 'is-elevated': isElevated }">
    <div class="nav-shell flex items-center justify-between px-5 md:px-6 lg:px-10">
      <RouterLink to="/" class="brand-link flex h-full items-center gap-3 no-underline">
        <span class="brand-mark-shell flex items-center justify-center" aria-hidden="true">
          <span
            class="brand-mark flex items-center justify-center rounded-md text-sm font-bold text-[#fff]"
            style="color: #fff; background: var(--gradient-primary)"
          >
            PE
          </span>
        </span>
        <span class="text-base font-semibold tracking-[0] text-(--color-text-strong)">PanEval</span>
      </RouterLink>

      <nav class="hidden h-full flex-1 items-center pl-12 md:flex" aria-label="Primary">
        <template v-for="item in navItems" :key="item.to">
          <a
            v-if="item.target"
            :href="item.to"
            :target="item.target"
            rel="noopener noreferrer"
            class="nav-link flex h-full items-center px-5 text-sm font-medium no-underline transition"
          >
            {{ t(item.labelKey) }}
          </a>
          <RouterLink
            v-else
            :to="item.to"
            class="nav-link flex h-full items-center px-5 text-sm font-medium no-underline transition"
            exact-active-class="is-active"
          >
            {{ t(item.labelKey) }}
          </RouterLink>
        </template>
      </nav>

      <div class="hidden h-full items-center gap-3 md:flex">
        <RouterLink
          to="/console"
          class="nav-ghost-action px-3 py-2 text-sm font-medium no-underline transition"
        >
          {{ t('navigation.console').toUpperCase() }}
        </RouterLink>

        <span v-if="isSessionPending" class="auth-placeholder" aria-hidden="true" />

        <button
          v-else-if="!authStore.isAuthenticated"
          type="button"
          class="pan-primary-button nav-login-button text-[#fff] no-underline transition"
          style="color: #fff"
          @click="openLogin"
        >
          {{ t('navigation.signIn') }}
        </button>

        <ElDropdown v-else trigger="click">
          <button
            type="button"
            class="nav-account-button flex items-center justify-center"
            :class="{ 'is-compact': isElevated }"
            :aria-label="displayName"
          >
            <ElAvatar
              :size="34"
              :src="authStore.user?.avatar || undefined"
              class="nav-account-avatar text-[#fff]"
              style="color: #fff; background: var(--gradient-primary)"
            >
              {{ avatarInitial }}
            </ElAvatar>
          </button>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem @click="goToProfile">{{ displayName }}</ElDropdownItem>
              <ElDropdownItem divided @click="handleLogout">
                {{ t('navigation.signOut') }}
              </ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>

      <button
        type="button"
        class="mobile-menu-button flex shrink-0 items-center justify-center text-(--color-text) transition md:hidden"
        :aria-expanded="isMobileMenuOpen"
        :aria-label="t('navigation.toggleNavigationMenu')"
        @click="toggleMobileMenu"
      >
        <span class="relative h-6 w-7" aria-hidden="true">
          <span
            class="absolute left-0 top-1 block h-0.5 w-7 rounded-full bg-(--color-text) transition"
            :class="isMobileMenuOpen ? 'translate-y-2 rotate-45' : ''"
          />
          <span
            class="absolute left-0 top-3 block h-0.5 w-7 rounded-full bg-(--color-text) transition"
            :class="isMobileMenuOpen ? 'opacity-0' : ''"
          />
          <span
            class="absolute left-0 top-5 block h-0.5 w-7 rounded-full bg-(--color-text) transition"
            :class="isMobileMenuOpen ? '-translate-y-2 -rotate-45' : ''"
          />
        </span>
      </button>
    </div>

    <div
      v-show="isMobileMenuOpen"
      class="mobile-menu border-t border-white/50 bg-white/90 shadow-(--shadow-soft) backdrop-blur-xl md:hidden"
    >
      <nav class="grid px-4 py-3">
        <template v-for="item in navItems" :key="item.to">
          <a
            v-if="item.target"
            :href="item.to"
            :target="item.target"
            rel="noopener noreferrer"
            class="rounded-md px-3 py-3 text-sm font-semibold text-(--color-text-muted) no-underline transition hover:bg-(--color-surface-soft) hover:text-(--color-primary)"
            @click="closeMobileMenu"
          >
            {{ t(item.labelKey) }}
          </a>
          <RouterLink
            v-else
            :to="item.to"
            class="rounded-md px-3 py-3 text-sm font-semibold text-(--color-text-muted) no-underline transition hover:bg-(--color-surface-soft) hover:text-(--color-primary)"
            active-class="bg-(--color-surface-muted) text-(--color-text)"
          >
            {{ t(item.labelKey) }}
          </RouterLink>
        </template>
      </nav>

      <div class="grid gap-3 border-t border-(--color-border) px-4 py-4">
        <RouterLink
          to="/console"
          class="rounded-md border border-(--color-border) px-4 py-3 text-center text-sm font-semibold text-(--color-text) no-underline transition hover:bg-(--color-surface-muted)"
        >
          {{ t('navigation.console') }}
        </RouterLink>

        <span v-if="isSessionPending" class="h-11" aria-hidden="true" />

        <button
          v-else-if="!authStore.isAuthenticated"
          type="button"
          class="pan-primary-button rounded-md px-4 py-3 text-center text-sm font-semibold text-[#fff] no-underline transition"
          style="color: #fff"
          @click="openLogin"
        >
          {{ t('navigation.signIn') }}
        </button>

        <div v-else class="grid gap-2">
          <button
            type="button"
            class="flex items-center justify-between rounded-md border border-(--color-border) px-4 py-3 text-sm font-semibold text-(--color-text) transition hover:bg-(--color-surface-muted)"
            @click="goToProfile"
          >
            <span class="truncate">{{ displayName }}</span>
            <span class="text-(--color-text-muted)">{{ t('navigation.profile') }}</span>
          </button>
          <button
            type="button"
            class="rounded-md border border-(--color-border) px-4 py-3 text-sm font-semibold text-(--color-text) transition hover:bg-(--color-surface-muted)"
            @click="handleLogout"
          >
            {{ t('navigation.signOut') }}
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-top-nav {
  --nav-motion: 220ms cubic-bezier(0.2, 0, 0.2, 1);

  color: var(--color-text-strong);
  background:
    linear-gradient(180deg, rgb(255 255 255 / 38%), rgb(255 255 255 / 0%)),
    linear-gradient(90deg, rgb(255 255 255 / 12%), rgb(255 255 255 / 4%));
  transition:
    background 220ms ease,
    box-shadow 220ms ease,
    color 220ms ease;
}

.app-top-nav::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: '';
  opacity: 0;
  background:
    linear-gradient(90deg, rgb(255 255 255 / 72%), rgb(255 255 255 / 46%)),
    radial-gradient(circle at 18% 0%, rgb(23 98 238 / 13%), transparent 34%);
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
  transition: opacity 220ms ease;
}

.app-top-nav.is-elevated {
  box-shadow:
    0 18px 45px rgb(20 32 92 / 10%),
    inset 0 -1px 0 rgb(255 255 255 / 42%);
}

.app-top-nav.is-elevated::after {
  opacity: 1;
}

.nav-shell,
.mobile-menu {
  position: relative;
  z-index: 1;
}

.nav-shell {
  height: 60px;
  transition: height 220ms ease;
}

.is-elevated .nav-shell {
  height: 46px;
}

.brand-link {
  min-width: 0;
}

.brand-mark-shell {
  width: 32px;
  height: 32px;
  transition:
    width var(--nav-motion),
    height var(--nav-motion);
}

.is-elevated .brand-mark-shell {
  width: 26px;
  height: 26px;
}

.brand-mark {
  width: 100%;
  height: 100%;
  box-shadow: 0 12px 26px rgb(23 98 238 / 20%);
  transition:
    border-radius var(--nav-motion),
    box-shadow 180ms ease,
    font-size var(--nav-motion);
}

.is-elevated .brand-mark {
  border-radius: 6px;
  font-size: 0.72rem;
}

.brand-link:hover .brand-mark {
  box-shadow: 0 14px 28px rgb(23 98 238 / 24%);
}

.nav-link {
  position: relative;
  color: rgb(41 41 98 / 74%);
}

.nav-link::after {
  position: absolute;
  right: 20px;
  bottom: 12px;
  left: 20px;
  height: 2px;
  content: '';
  background: linear-gradient(90deg, #1762ee, #15b8a6);
  border-radius: 999px;
  opacity: 0;
  transform: scaleX(0.35);
  transition:
    opacity 180ms ease,
    transform 180ms ease,
    bottom 220ms ease;
}

.is-elevated .nav-link::after {
  bottom: 8px;
}

.nav-link:hover,
.nav-link.is-active {
  color: var(--color-text-strong);
}

.nav-link.is-active::after {
  opacity: 1;
  transform: scaleX(1);
}

.nav-ghost-action {
  color: rgb(41 41 98 / 78%);
}

.nav-ghost-action:hover {
  color: var(--color-primary);
}

.pan-primary-button {
  border: 0;
  cursor: pointer;
  font-family: inherit;
}

.nav-login-button {
  height: 38px;
  padding: 0 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  transition:
    height var(--nav-motion),
    padding var(--nav-motion),
    font-size var(--nav-motion),
    filter 180ms ease,
    transform 180ms ease;
}

.nav-login-button:hover {
  transform: translateY(-1px);
}

.is-elevated .nav-login-button {
  height: 32px;
  padding: 0 14px;
  font-size: 12px;
}

.nav-account-button {
  width: 46px;
  height: 46px;
  border: 0;
  border-radius: 8px;
  color: var(--color-text-strong);
  background: transparent;
  cursor: pointer;
  transition:
    background 180ms ease,
    width var(--nav-motion),
    height var(--nav-motion),
    transform var(--nav-motion);
}

.nav-account-button:hover {
  background: rgb(255 255 255 / 34%);
}

.nav-account-button.is-compact {
  width: 34px;
  height: 34px;
}

.nav-account-avatar {
  transform-origin: center;
  transition:
    transform var(--nav-motion),
    box-shadow 220ms ease;
}

.nav-account-button:hover .nav-account-avatar {
  box-shadow: 0 10px 22px rgb(23 98 238 / 18%);
  transform: scale(1.04);
}

.nav-account-button.is-compact .nav-account-avatar {
  transform: scale(0.765);
}

.nav-account-button.is-compact:hover .nav-account-avatar {
  transform: scale(0.82);
}

.auth-placeholder {
  width: 76px;
  height: 36px;
}

.mobile-menu-button {
  width: 42px;
  height: 42px;
  border: 1px solid rgb(23 98 238 / 10%);
  border-radius: 8px;
  background: rgb(255 255 255 / 48%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.is-elevated .mobile-menu-button {
  width: 36px;
  height: 36px;
  background: rgb(255 255 255 / 74%);
}

@media (max-width: 767px) {
  .nav-shell {
    height: 56px;
  }

  .is-elevated .nav-shell {
    height: 44px;
  }
}
</style>
