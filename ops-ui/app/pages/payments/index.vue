<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Payments</a-typography-title>
    <a-typography-paragraph type="secondary">
      Search intents / captures and reconcile exceptions (OPS-PAY-01–03).
    </a-typography-paragraph>

    <a-form layout="inline" class="ops-filter-form" style="margin-bottom: 1rem" @finish="load(1)">
      <a-form-item label="Status">
        <a-select v-model:value="filters.status" style="min-width: 9rem" allow-clear placeholder="All">
          <a-select-option value="pending">pending</a-select-option>
          <a-select-option value="succeeded">succeeded</a-select-option>
          <a-select-option value="failed">failed</a-select-option>
          <a-select-option value="cancelled">cancelled</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="Search">
        <a-input v-model:value="filters.q" allow-clear placeholder="Phone, provider ref, id" style="min-width: 14rem" />
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
        :scroll="{ x: 900 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'user'">
            <code>{{ record.user?.phone || shortId(record.user_id) }}</code>
          </template>
          <template v-else-if="column.key === 'amount'">
            {{ formatPaise(record.amount_paise) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'kind'">
            {{ record.kind }}
          </template>
          <template v-else-if="column.key === 'provider'">
            {{ record.provider }}
            <div v-if="record.provider_ref" style="font-size: 12px; color: rgba(0,0,0,0.45)">
              {{ record.provider_ref }}
            </div>
          </template>
          <template v-else-if="column.key === 'created'">
            {{ formatDateTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="navigateTo(`/payments/${record.id}`)">
              Open
            </a-button>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { OpsPayment, Paginated, PaymentStatus } from '~/types/ops'
import { formatDateTime, formatPaise, shortId } from '~/utils/format'

const { opsFetch } = useOpsApi()
const items = ref<OpsPayment[]>([])
const loading = ref(false)
const error = ref('')
const filters = reactive({
  status: undefined as PaymentStatus | undefined,
  q: '',
})

const columns = [
  { title: 'User', key: 'user' },
  { title: 'Amount', key: 'amount' },
  { title: 'Status', key: 'status' },
  { title: 'Kind', key: 'kind' },
  { title: 'Provider', key: 'provider' },
  { title: 'Created', key: 'created' },
  { title: '', key: 'actions', width: 90 },
]

function statusColor(status: PaymentStatus) {
  switch (status) {
    case 'succeeded':
      return 'success'
    case 'pending':
      return 'warning'
    case 'failed':
      return 'error'
    case 'cancelled':
      return 'default'
    default:
      return 'default'
  }
}

async function load(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const list = await opsFetch<Paginated<OpsPayment>>('/payments', {
      query: {
        page,
        page_size: 50,
        status: filters.status || undefined,
        q: filters.q || undefined,
      },
    })
    items.value = list.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load payments'
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))
</script>
