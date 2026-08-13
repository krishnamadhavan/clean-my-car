<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Subscriptions</a-typography-title>
    <a-typography-paragraph type="secondary">
      Support search and admin cancel (OPS-SUB-01–03). Consumer start/pay flows land with Module 7.
    </a-typography-paragraph>

    <a-form layout="inline" class="ops-filter-form" style="margin-bottom: 1rem" @finish="load(1)">
      <a-form-item label="Status">
        <a-select v-model:value="filters.status" style="min-width: 10rem" allow-clear placeholder="All">
          <a-select-option v-for="s in statuses" :key="s" :value="s">{{ s }}</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="Search">
        <a-input v-model:value="filters.q" allow-clear placeholder="Phone, name, id" style="min-width: 12rem" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit" :loading="loading">Filter</a-button>
      </a-form-item>
    </a-form>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <div class="ops-table-scroll">
      <a-table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        row-key="id"
        :pagination="false"
        :scroll="{ x: 960 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'user'">
            <div>
              <code>{{ record.user?.phone || shortId(record.user_id) }}</code>
              <div v-if="record.user?.name" style="color: rgba(0,0,0,0.45); font-size: 12px">
                {{ record.user.name }}
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'plan'">
            {{ record.size_tier }} · int {{ record.interior_frequency }}×
          </template>
          <template v-else-if="column.key === 'amount'">
            {{ formatPaise(record.monthly_amount_paise) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'period'">
            {{ record.period_start }} → {{ record.period_end }}
          </template>
          <template v-else-if="column.key === 'society'">
            {{ record.society?.name || shortId(record.society_id) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="navigateTo(`/subscriptions/${record.id}`)">
              Open
            </a-button>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { OpsSubscription, Paginated, SubscriptionStatus } from '~/types/ops'
import { formatPaise, shortId } from '~/utils/format'

const { opsFetch } = useOpsApi()
const items = ref<OpsSubscription[]>([])
const loading = ref(false)
const error = ref('')
const filters = reactive({
  status: undefined as SubscriptionStatus | undefined,
  q: '',
})

const statuses: SubscriptionStatus[] = [
  'pending_payment',
  'active',
  'cancel_scheduled',
  'paused',
  'expired',
  'inactive',
]

const columns = [
  { title: 'User', key: 'user' },
  { title: 'Plan', key: 'plan' },
  { title: 'Amount / mo', key: 'amount' },
  { title: 'Status', key: 'status' },
  { title: 'Period', key: 'period' },
  { title: 'Society', key: 'society' },
  { title: '', key: 'actions', width: 90 },
]

function statusColor(status: SubscriptionStatus) {
  switch (status) {
    case 'active':
      return 'success'
    case 'pending_payment':
      return 'warning'
    case 'cancel_scheduled':
      return 'orange'
    case 'paused':
      return 'processing'
    case 'expired':
    case 'inactive':
      return 'default'
    default:
      return 'default'
  }
}

async function load(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const list = await opsFetch<Paginated<OpsSubscription>>('/subscriptions', {
      query: {
        page,
        page_size: 50,
        status: filters.status || undefined,
        q: filters.q || undefined,
      },
    })
    items.value = list.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load subscriptions'
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))
</script>
