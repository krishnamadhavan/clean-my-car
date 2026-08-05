<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Waitlist</a-typography-title>
    <a-typography-paragraph type="secondary">
      Triage demand (OPS-WAIT-01–04).
    </a-typography-paragraph>

    <a-row v-if="summary" :gutter="[12, 12]" style="margin-bottom: 1rem">
      <a-col :xs="12" :sm="8" :md="4">
        <a-card size="small"><a-statistic title="Total" :value="summary.total" /></a-card>
      </a-col>
      <a-col v-for="row in summary.by_status" :key="row.status" :xs="12" :sm="8" :md="5">
        <a-card size="small">
          <a-statistic :title="row.status" :value="row.count" />
        </a-card>
      </a-col>
    </a-row>

    <a-form layout="inline" class="ops-filter-form" style="margin-bottom: 1rem" @finish="load(1)">
      <a-form-item label="Status">
        <a-select v-model:value="filters.status" style="min-width: 8rem" allow-clear placeholder="All">
          <a-select-option value="pending">pending</a-select-option>
          <a-select-option value="contacted">contacted</a-select-option>
          <a-select-option value="converted">converted</a-select-option>
          <a-select-option value="closed">closed</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="Phone">
        <a-input v-model:value="filters.phone" allow-clear />
      </a-form-item>
      <a-form-item label="Society">
        <a-input v-model:value="filters.society_name" allow-clear />
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
        :scroll="{ x: 720 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'city'">
            {{ record.city?.name || shortId(record.city_id) }}
          </template>
          <template v-else-if="column.key === 'phone'">
            <code>{{ record.phone }}</code>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag color="processing">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'created'">
            {{ formatDateTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="navigateTo(`/waitlist/${record.id}`)">
              Open
            </a-button>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Paginated, WaitlistEntry, WaitlistSummary } from '~/types/ops'
import { formatDateTime, shortId } from '~/utils/format'

const { opsFetch } = useOpsApi()
const items = ref<WaitlistEntry[]>([])
const summary = ref<WaitlistSummary | null>(null)
const loading = ref(false)
const error = ref('')
const filters = reactive({ status: undefined as string | undefined, phone: '', society_name: '' })

const columns = [
  { title: 'Society', dataIndex: 'society_name', key: 'society' },
  { title: 'City', key: 'city' },
  { title: 'Phone', key: 'phone' },
  { title: 'Status', key: 'status' },
  { title: 'Created', key: 'created' },
  { title: '', key: 'actions', width: 90 },
]

async function load(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const [list, sum] = await Promise.all([
      opsFetch<Paginated<WaitlistEntry>>('/waitlist', {
        query: {
          page,
          page_size: 50,
          status: filters.status || undefined,
          phone: filters.phone || undefined,
          society_name: filters.society_name || undefined,
        },
      }),
      opsFetch<WaitlistSummary>('/waitlist/summary'),
    ])
    items.value = list.items
    summary.value = sum
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load waitlist'
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))
</script>

<style scoped>
.ops-filter-form :deep(.ant-form-item) {
  margin-bottom: 0.5rem;
}
</style>
