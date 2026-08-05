<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Ops dashboard</a-typography-title>
    <a-typography-paragraph type="secondary">
      Master data and support tools for Modules 1–6.
    </a-typography-paragraph>

    <a-row :gutter="[16, 16]" style="margin-bottom: 1.25rem">
      <a-col :xs="24" :sm="8">
        <a-card size="small" :bordered="true">
          <a-statistic title="Waitlist" :value="waitlistTotal ?? undefined" :loading="statsLoading">
            <template v-if="waitlistTotal === null && !statsLoading" #formatter> — </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="8">
        <a-card size="small" :bordered="true">
          <a-statistic title="Pricing gaps" :value="missingPricing ?? undefined" :loading="statsLoading">
            <template v-if="missingPricing === null && !statsLoading" #formatter> — </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="8">
        <a-card size="small" :bordered="true">
          <div style="color: rgba(0,0,0,0.45); font-size: 14px; margin-bottom: 4px">Signed in</div>
          <div style="font-size: 16px; font-weight: 600; word-break: break-word; color: #4b49ac">
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
import type { MissingPricing, WaitlistSummary } from '~/types/ops'

const auth = useAuth()
const { opsFetch } = useOpsApi()

const waitlistTotal = ref<number | null>(null)
const missingPricing = ref<number | null>(null)
const loadError = ref('')
const statsLoading = ref(true)

const modules = [
  { to: '/users', title: 'Users', blurb: 'Search consumer accounts, deactivate / reactivate.', badge: 'Module 2' },
  { to: '/cities', title: 'Cities & societies', blurb: 'Location catalog and service weekdays.', badge: 'Module 3' },
  { to: '/waitlist', title: 'Waitlist', blurb: 'Triage demand and update status.', badge: 'Module 4' },
  { to: '/vehicles', title: 'Vehicle catalog', blurb: 'Makes, models, and size tiers.', badge: 'Module 5' },
  { to: '/pricing', title: 'Pricing', blurb: 'City tariffs, matrix, and quote preview.', badge: 'Module 6' },
  { to: '/pricing/quote', title: 'Quote preview', blurb: 'Run the same quote engine as consumer.', badge: 'Module 6' },
]

onMounted(async () => {
  statsLoading.value = true
  try {
    const [summary, missing] = await Promise.all([
      opsFetch<WaitlistSummary>('/waitlist/summary'),
      opsFetch<MissingPricing>('/pricing/missing'),
    ])
    waitlistTotal.value = summary.total
    missingPricing.value = missing.total
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : 'Failed to load dashboard stats'
  } finally {
    statsLoading.value = false
  }
})
</script>
