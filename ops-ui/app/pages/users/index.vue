<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Users</a-typography-title>
    <a-typography-paragraph type="secondary">
      Search consumer accounts (OPS-PROF-01).
    </a-typography-paragraph>

    <a-space wrap style="margin-bottom: 1rem; width: 100%">
      <a-input-search
        v-model:value="q"
        placeholder="Phone, UUID, name, email"
        enter-button="Search"
        style="min-width: min(100%, 20rem)"
        :loading="loading"
        @search="load(1)"
      />
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <div class="ops-table-scroll">
      <a-table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        row-key="id"
        :pagination="pagination"
        :scroll="{ x: 640 }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'phone'">
            <code>{{ record.phone }}</code>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? 'active' : 'inactive' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created'">
            {{ formatDateTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="navigateTo(`/users/${record.id}`)">
              Open
            </a-button>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TablePaginationConfig } from 'ant-design-vue'
import type { OpsUserSummary, Paginated } from '~/types/ops'
import { formatDateTime } from '~/utils/format'

const { opsFetch } = useOpsApi()
const q = ref('')
const items = ref<OpsUserSummary[]>([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const columns = [
  { title: 'Phone', key: 'phone', dataIndex: 'phone' },
  { title: 'Name', dataIndex: 'name', key: 'name', customRender: ({ text }: { text: string | null }) => text || '—' },
  { title: 'Status', key: 'status' },
  { title: 'Created', key: 'created' },
  { title: '', key: 'actions', width: 90 },
]

const pagination = computed(() => ({
  current: page.value,
  pageSize,
  total: total.value,
  showSizeChanger: false,
  responsive: true,
}))

async function load(p = 1) {
  loading.value = true
  error.value = ''
  try {
    const data = await opsFetch<Paginated<OpsUserSummary>>('/users', {
      query: { q: q.value || undefined, page: p, page_size: pageSize },
    })
    items.value = data.items
    total.value = data.total
    page.value = data.page
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load users'
  } finally {
    loading.value = false
  }
}

function onTableChange(pag: TablePaginationConfig) {
  load(pag.current || 1)
}

onMounted(() => load(1))
</script>
