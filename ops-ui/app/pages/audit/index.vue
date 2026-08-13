<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Audit log</a-typography-title>
    <a-typography-paragraph type="secondary">
      Recent ops actions (OPS-PLAT-02).
    </a-typography-paragraph>

    <a-form layout="inline" class="ops-filter-form" style="margin-bottom: 1rem" @finish="load(1)">
      <a-form-item label="Action">
        <a-input v-model:value="filters.action" allow-clear placeholder="faq.replace" />
      </a-form-item>
      <a-form-item label="Resource">
        <a-input v-model:value="filters.resource_type" allow-clear placeholder="faq" />
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
        :scroll="{ x: 800 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'when'">
            {{ formatDateTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'summary'">
            {{ record.summary || record.action }}
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AuditEvent, Paginated } from '~/types/ops'
import { formatDateTime } from '~/utils/format'

const { opsFetch } = useOpsApi()
const items = ref<AuditEvent[]>([])
const loading = ref(false)
const error = ref('')
const filters = reactive({ action: '', resource_type: '' })

const columns = [
  { title: 'When', key: 'when', width: 180 },
  { title: 'Action', dataIndex: 'action', key: 'action', width: 160 },
  { title: 'Resource', dataIndex: 'resource_type', key: 'resource', width: 120 },
  { title: 'Summary', key: 'summary' },
]

async function load(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const list = await opsFetch<Paginated<AuditEvent>>('/audit', {
      query: {
        page,
        page_size: 50,
        action: filters.action || undefined,
        resource_type: filters.resource_type || undefined,
      },
    })
    items.value = list.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load audit'
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))
</script>
