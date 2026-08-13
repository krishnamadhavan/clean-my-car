<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Washes</a-typography-title>
    <a-typography-paragraph type="secondary">
      Field visits — complete / miss / list (OPS-WASH-01–04).
    </a-typography-paragraph>

    <a-form layout="inline" class="ops-filter-form" style="margin-bottom: 1rem" @finish="load(1)">
      <a-form-item label="Status">
        <a-select v-model:value="filters.status" style="min-width: 10rem" allow-clear placeholder="All">
          <a-select-option value="scheduled">scheduled</a-select-option>
          <a-select-option value="retry_scheduled">retry_scheduled</a-select-option>
          <a-select-option value="completed">completed</a-select-option>
          <a-select-option value="missed">missed</a-select-option>
          <a-select-option value="skipped">skipped</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="Service date">
        <a-date-picker v-model:value="serviceDate" value-format="YYYY-MM-DD" style="width: 100%" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit" :loading="loading">Filter</a-button>
      </a-form-item>
      <a-form-item>
        <a-button :loading="generating" @click="generate">Generate rows</a-button>
      </a-form-item>
    </a-form>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-alert v-if="message" type="success" show-icon :message="message" style="margin-bottom: 1rem" />

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
            <div>{{ record.user_name || '—' }}</div>
            <code>{{ record.user_phone || shortId(record.user_id) }}</code>
          </template>
          <template v-else-if="column.key === 'society'">
            {{ record.society_name || shortId(record.society_id) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                type="link"
                size="small"
                :disabled="record.status === 'completed'"
                :loading="actingId === record.id"
                @click="complete(record)"
              >
                Complete
              </a-button>
              <a-button
                type="link"
                size="small"
                danger
                :disabled="record.status === 'completed' || record.status === 'missed'"
                :loading="actingId === record.id"
                @click="miss(record)"
              >
                Miss
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Dayjs } from 'dayjs'
import type { OpsWash, Paginated, WashStatus } from '~/types/ops'
import { shortId } from '~/utils/format'

const { opsFetch } = useOpsApi()
const items = ref<OpsWash[]>([])
const loading = ref(false)
const generating = ref(false)
const actingId = ref<string | null>(null)
const error = ref('')
const message = ref('')
const serviceDate = ref<string | Dayjs | null>(null)
const filters = reactive({ status: undefined as WashStatus | undefined })

const columns = [
  { title: 'Date', dataIndex: 'service_date', key: 'date', width: 120 },
  { title: 'User', key: 'user' },
  { title: 'Society', key: 'society' },
  { title: 'Status', key: 'status', width: 140 },
  { title: 'Actions', key: 'actions', width: 180 },
]

function statusColor(status: WashStatus) {
  if (status === 'completed') return 'success'
  if (status === 'missed') return 'error'
  if (status === 'retry_scheduled') return 'warning'
  return 'processing'
}

async function load(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const day =
      typeof serviceDate.value === 'string'
        ? serviceDate.value
        : serviceDate.value
          ? String(serviceDate.value)
          : undefined
    const list = await opsFetch<Paginated<OpsWash>>('/washes', {
      query: {
        page,
        page_size: 50,
        status: filters.status || undefined,
        service_date: day || undefined,
      },
    })
    items.value = list.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load washes'
  } finally {
    loading.value = false
  }
}

async function complete(record: OpsWash) {
  actingId.value = record.id
  error.value = ''
  message.value = ''
  try {
    await opsFetch(`/washes/${record.id}/complete`, {
      method: 'POST',
      body: { includes_interior: false },
    })
    message.value = 'Marked complete'
    await load(1)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Complete failed'
  } finally {
    actingId.value = null
  }
}

async function miss(record: OpsWash) {
  actingId.value = record.id
  error.value = ''
  message.value = ''
  try {
    await opsFetch(`/washes/${record.id}/miss`, {
      method: 'POST',
      body: { schedule_retry: true, reason: 'Missed by field ops' },
    })
    message.value = 'Marked missed (retry scheduled if available)'
    await load(1)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Miss failed'
  } finally {
    actingId.value = null
  }
}

async function generate() {
  generating.value = true
  error.value = ''
  message.value = ''
  try {
    const res = await opsFetch<{ created: number; message: string }>('/washes/generate', {
      method: 'POST',
      body: {},
    })
    message.value = res.message || `Created ${res.created} rows`
    await load(1)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Generate failed'
  } finally {
    generating.value = false
  }
}

onMounted(() => load(1))
</script>
