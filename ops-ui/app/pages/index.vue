<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Ops dashboard</a-typography-title>
    <a-typography-paragraph type="secondary">
      Overview across catalog, subscriptions, and field operations.
    </a-typography-paragraph>

    <a-row :gutter="[16, 16]" style="margin-bottom: 1.25rem">
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <a-statistic title="Active cities" :value="overview?.cities_active ?? undefined" :loading="statsLoading" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <a-statistic title="Live societies" :value="overview?.societies_live ?? undefined" :loading="statsLoading" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <a-statistic title="Open waitlist" :value="overview?.waitlist_open ?? undefined" :loading="statsLoading" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <a-statistic
            title="Active subs"
            :value="overview?.subscriptions_active ?? undefined"
            :loading="statsLoading"
          />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <a-statistic
            title="Washes today"
            :value="overview?.washes_scheduled_today ?? undefined"
            :loading="statsLoading"
          />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <a-statistic
            title="Completed today"
            :value="overview?.washes_completed_today ?? undefined"
            :loading="statsLoading"
          />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <a-statistic title="Pricing gaps" :value="missingPricing ?? undefined" :loading="statsLoading" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6">
        <a-card size="small">
          <div style="color: rgba(0,0,0,0.45); font-size: 14px; margin-bottom: 4px">Signed in</div>
          <div style="font-size: 14px; font-weight: 600; word-break: break-word; color: #4b49ac">
            {{ auth.operator.value?.email || '—' }}
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-alert v-if="loadError" type="error" show-icon :message="loadError" style="margin-bottom: 1rem" />

    <a-row :gutter="[16, 16]">
      <a-col v-for="item in modules" :key="item.to" :xs="24" :sm="12" :lg="8">
        <a-card
          hoverable
          :bordered="true"
          style="height: 100%; cursor: pointer"
          @click="navigateTo(item.to)"
        >
          <template #title>
            <span style="color: #4b49ac">{{ item.title }}</span>
          </template>
          <template #extra>
            <a-tag color="purple">{{ item.badge }}</a-tag>
          </template>
          <a-typography-paragraph type="secondary" style="margin-bottom: 0">
            {{ item.blurb }}
          </a-typography-paragraph>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import type { MissingPricing, OpsOverview } from '~/types/ops'

const auth = useAuth()
const { opsFetch } = useOpsApi()

const overview = ref<OpsOverview | null>(null)
const missingPricing = ref<number | null>(null)
const loadError = ref('')
const statsLoading = ref(true)

const modules = [
  { to: '/users', title: 'Users', blurb: 'Search consumer accounts, deactivate / reactivate.', badge: 'Module 2' },
  { to: '/cities', title: 'Cities & societies', blurb: 'Location catalog and service weekdays.', badge: 'Module 3' },
  { to: '/waitlist', title: 'Waitlist', blurb: 'Triage demand and update status.', badge: 'Module 4' },
  { to: '/vehicles', title: 'Vehicle catalog', blurb: 'Makes, models, and size tiers.', badge: 'Module 5' },
  { to: '/pricing', title: 'Pricing', blurb: 'City tariffs, matrix, and quote preview.', badge: 'Module 6' },
  { to: '/subscriptions', title: 'Subscriptions', blurb: 'Search plans and schedule admin cancel.', badge: 'Module 7' },
  { to: '/payments', title: 'Payments', blurb: 'Search intents and reconcile captures.', badge: 'Module 8' },
  { to: '/washes', title: 'Washes', blurb: 'Complete / miss field visits and generate schedule rows.', badge: 'Module 10' },
  { to: '/support', title: 'Support', blurb: 'Ticket queue and ops replies.', badge: 'Module 12' },
  { to: '/content/faq', title: 'FAQ', blurb: 'Publish FAQ for the consumer app.', badge: 'Module 12' },
  { to: '/content/legal', title: 'Legal', blurb: 'Publish terms, privacy, cancellation.', badge: 'Module 12' },
  { to: '/app-config', title: 'App config', blurb: 'Min iOS version, force update, support contacts.', badge: 'Module 13' },
  { to: '/audit', title: 'Audit', blurb: 'Recent ops actions log.', badge: 'Module 15' },
]

onMounted(async () => {
  statsLoading.value = true
  try {
    const [ov, missing] = await Promise.all([
      opsFetch<OpsOverview>('/overview'),
      opsFetch<MissingPricing>('/pricing/missing'),
    ])
    overview.value = ov
    missingPricing.value = missing.total
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : 'Failed to load dashboard stats'
  } finally {
    statsLoading.value = false
  }
})
</script>
