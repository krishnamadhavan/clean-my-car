<template>
  <a-layout class="ops-layout" has-sider>
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      :trigger="null"
      :width="220"
      :collapsed-width="isMobile ? 0 : 64"
      theme="light"
      class="ops-sider"
      :class="{ 'ops-sider-mobile': isMobile }"
      breakpoint="lg"
      :style="isMobile ? { position: 'fixed', height: '100vh', left: 0, top: 0, bottom: 0 } : undefined"
      @breakpoint="onBreakpoint"
    >
      <div class="ops-sider-logo">
        <AppLogo :size="collapsed && !isMobile ? 'sm' : 'md'" />
        <template v-if="!collapsed">
          <span class="ops-sider-title">Clean My Car</span>
          <span class="ops">Ops</span>
        </template>
      </div>
      <a-menu
        v-model:selected-keys="selectedKeys"
        mode="inline"
        :items="menuItems"
        @click="onMenuClick"
      />
    </a-layout-sider>

    <!-- Mobile mask when drawer-style sider is open -->
    <div
      v-if="isMobile && !collapsed"
      class="ops-sider-mask"
      aria-hidden="true"
      @click="collapsed = true"
    />

    <a-layout class="ops-main-layout">
      <a-layout-header class="ops-header">
        <div class="ops-header-left">
          <a-button type="text" class="ops-trigger" aria-label="Toggle menu" @click="toggleCollapsed">
            <template #icon>
              <MenuUnfoldOutlined v-if="collapsed" />
              <MenuFoldOutlined v-else />
            </template>
          </a-button>
          <span class="ops-header-title">{{ pageTitle }}</span>
        </div>
        <div class="ops-header-right">
          <span v-if="auth.operator.value" class="ops-user">
            {{ auth.operator.value.name || auth.operator.value.email }}
          </span>
          <a-button ghost size="small" :loading="loggingOut" @click="onLogout">Log out</a-button>
        </div>
      </a-layout-header>

      <a-layout-content class="ops-content">
        <div class="ops-page">
          <slot />
        </div>
      </a-layout-content>

      <a-layout-footer class="ops-footer">
        <span>Internal tools only · not the consumer app</span>
        <span class="ops-footer-api">{{ apiBase }}{{ opsApiPrefix }}</span>
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import {
  CalendarOutlined,
  CarOutlined,
  CreditCardOutlined,
  CustomerServiceOutlined,
  DashboardOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  EnvironmentOutlined,
  FileTextOutlined,
  HistoryOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  TeamOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons-vue'
import type { ItemType } from 'ant-design-vue'

const config = useRuntimeConfig()
const auth = useAuth()
const { logout } = useOpsApi()
const route = useRoute()
const router = useRouter()

const apiBase = config.public.apiBase
const opsApiPrefix = config.public.opsApiPrefix

const collapsed = ref(false)
const isMobile = ref(false)
const loggingOut = ref(false)

const menuItems = computed<ItemType[]>(() => [
  { key: '/', icon: () => h(DashboardOutlined), label: 'Dashboard' },
  { key: '/users', icon: () => h(TeamOutlined), label: 'Users' },
  { key: '/cities', icon: () => h(EnvironmentOutlined), label: 'Cities' },
  { key: '/waitlist', icon: () => h(UnorderedListOutlined), label: 'Waitlist' },
  { key: '/vehicles', icon: () => h(CarOutlined), label: 'Vehicles' },
  { key: '/pricing', icon: () => h(DollarOutlined), label: 'Pricing' },
  { key: '/subscriptions', icon: () => h(CalendarOutlined), label: 'Subscriptions' },
  { key: '/payments', icon: () => h(CreditCardOutlined), label: 'Payments' },
  { key: '/washes', icon: () => h(CheckCircleOutlined), label: 'Washes' },
  { key: '/support', icon: () => h(CustomerServiceOutlined), label: 'Support' },
  { key: '/content/faq', icon: () => h(FileTextOutlined), label: 'FAQ' },
  { key: '/content/legal', icon: () => h(FileTextOutlined), label: 'Legal' },
  { key: '/app-config', icon: () => h(SettingOutlined), label: 'App config' },
  { key: '/audit', icon: () => h(HistoryOutlined), label: 'Audit' },
])

const selectedKeys = computed({
  get: () => {
    const path = route.path
    if (path.startsWith('/users')) return ['/users']
    if (path.startsWith('/cities')) return ['/cities']
    if (path.startsWith('/waitlist')) return ['/waitlist']
    if (path.startsWith('/vehicles')) return ['/vehicles']
    if (path.startsWith('/pricing')) return ['/pricing']
    if (path.startsWith('/subscriptions')) return ['/subscriptions']
    if (path.startsWith('/payments')) return ['/payments']
    if (path.startsWith('/washes')) return ['/washes']
    if (path.startsWith('/support')) return ['/support']
    if (path.startsWith('/content/faq')) return ['/content/faq']
    if (path.startsWith('/content/legal')) return ['/content/legal']
    if (path.startsWith('/app-config')) return ['/app-config']
    if (path.startsWith('/audit')) return ['/audit']
    return ['/']
  },
  set: () => {},
})

const pageTitle = computed(() => {
  const path = route.path
  if (path.startsWith('/users')) return 'Users'
  if (path.startsWith('/cities')) return 'Cities & societies'
  if (path.startsWith('/waitlist')) return 'Waitlist'
  if (path.startsWith('/vehicles')) return 'Vehicle catalog'
  if (path.startsWith('/pricing')) return 'Pricing'
  if (path.startsWith('/subscriptions')) return 'Subscriptions'
  if (path.startsWith('/payments')) return 'Payments'
  if (path.startsWith('/washes')) return 'Washes'
  if (path.startsWith('/support')) return 'Support'
  if (path.startsWith('/content/faq')) return 'FAQ'
  if (path.startsWith('/content/legal')) return 'Legal'
  if (path.startsWith('/app-config')) return 'App config'
  if (path.startsWith('/audit')) return 'Audit'
  return 'Dashboard'
})

function onBreakpoint(broken: boolean) {
  isMobile.value = broken
  collapsed.value = broken
}

function toggleCollapsed() {
  collapsed.value = !collapsed.value
}

function onMenuClick(info: { key: string | number }) {
  router.push(String(info.key))
  if (isMobile.value) collapsed.value = true
}

async function onLogout() {
  loggingOut.value = true
  try {
    await logout()
    await navigateTo('/login')
  } finally {
    loggingOut.value = false
  }
}

onMounted(() => {
  // Align mobile state if first paint is already narrow
  if (typeof window !== 'undefined' && window.innerWidth < 992) {
    isMobile.value = true
    collapsed.value = true
  }
})
</script>

<style scoped>
.ops-layout {
  min-height: 100vh;
  min-height: 100dvh;
}

.ops-sider {
  z-index: 100;
  border-right: 1px solid #f0f0f0;
  overflow: auto;
}

.ops-sider :deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
}

.ops-sider-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 56px;
  padding: 0 1rem;
  font-weight: 700;
  color: #4b49ac;
  border-bottom: 1px solid #f0f0f0;
  white-space: nowrap;
  overflow: hidden;
}

.ops-sider-title {
  overflow: hidden;
  text-overflow: ellipsis;
}

.ops-sider-logo .ops {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #4b49ac;
  background: #eef0ff;
  padding: 0.1rem 0.4rem;
  border-radius: 999px;
}

.ops-sider-mask {
  position: fixed;
  inset: 0;
  z-index: 99;
  background: rgba(0, 0, 0, 0.35);
}

.ops-main-layout {
  min-width: 0;
  flex: 1;
}

.ops-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0 12px 0 0;
  background: #4b49ac !important;
  height: 56px;
  line-height: 56px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.ops-header-left,
.ops-header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.ops-header-right {
  padding-right: 12px;
  flex-shrink: 0;
}

.ops-trigger {
  color: #fff !important;
  font-size: 16px;
  width: 48px;
  height: 56px;
}

.ops-header-title {
  color: #fff;
  font-weight: 600;
  font-size: clamp(0.95rem, 2.5vw, 1.05rem);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ops-user {
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.85rem;
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 576px) {
  .ops-user {
    display: none;
  }
}

.ops-content {
  padding: clamp(12px, 3vw, 24px);
  background: #f5f7fb;
  min-height: calc(100vh - 56px - 64px);
}

.ops-page {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.ops-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem 1rem;
  padding: 12px clamp(12px, 3vw, 24px);
  background: #f5f7fb;
  color: rgba(0, 0, 0, 0.45);
  font-size: 0.8rem;
}

.ops-footer-api {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  word-break: break-all;
}
</style>
