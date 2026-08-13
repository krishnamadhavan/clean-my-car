<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Support tickets</a-typography-title>
    <a-typography-paragraph type="secondary">
      Consumer support queue (OPS-SUP-03/04).
    </a-typography-paragraph>

    <a-form layout="inline" class="ops-filter-form" style="margin-bottom: 1rem" @finish="load(1)">
      <a-form-item label="Status">
        <a-select v-model:value="filters.status" style="min-width: 10rem" allow-clear placeholder="All">
          <a-select-option value="open">open</a-select-option>
          <a-select-option value="in_progress">in_progress</a-select-option>
          <a-select-option value="resolved">resolved</a-select-option>
          <a-select-option value="closed">closed</a-select-option>
        </a-select>
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
            <div>{{ record.user_name || '—' }}</div>
            <code>{{ record.user_phone || shortId(record.user_id) }}</code>
          </template>
          <template v-else-if="column.key === 'message'">
            <div style="max-width: 280px; white-space: normal">{{ record.message }}</div>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag>{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'created'">
            {{ formatDateTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="openEdit(record)">Update</a-button>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="editOpen"
      title="Update ticket"
      ok-text="Save"
      :confirm-loading="saving"
      @ok="saveEdit"
    >
      <a-form layout="vertical">
        <a-form-item label="Status">
          <a-select v-model:value="editForm.status">
            <a-select-option value="open">open</a-select-option>
            <a-select-option value="in_progress">in_progress</a-select-option>
            <a-select-option value="resolved">resolved</a-select-option>
            <a-select-option value="closed">closed</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Reply to user">
          <a-textarea v-model:value="editForm.ops_reply" :rows="3" />
        </a-form-item>
        <a-form-item label="Internal notes">
          <a-textarea v-model:value="editForm.ops_notes" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import type { OpsSupportTicket, Paginated, SupportTicketStatus } from '~/types/ops'
import { formatDateTime, shortId } from '~/utils/format'

const { opsFetch } = useOpsApi()
const items = ref<OpsSupportTicket[]>([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const filters = reactive({ status: undefined as SupportTicketStatus | undefined })
const editOpen = ref(false)
const editId = ref<string | null>(null)
const editForm = reactive({
  status: 'open' as SupportTicketStatus,
  ops_reply: '',
  ops_notes: '',
})

const columns = [
  { title: 'User', key: 'user', width: 160 },
  { title: 'Category', dataIndex: 'category', key: 'category', width: 100 },
  { title: 'Message', key: 'message' },
  { title: 'Status', key: 'status', width: 120 },
  { title: 'Created', key: 'created', width: 160 },
  { title: '', key: 'actions', width: 90 },
]

async function load(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const list = await opsFetch<Paginated<OpsSupportTicket>>('/support/tickets', {
      query: {
        page,
        page_size: 50,
        status: filters.status || undefined,
      },
    })
    items.value = list.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load tickets'
  } finally {
    loading.value = false
  }
}

function openEdit(record: OpsSupportTicket) {
  editId.value = record.id
  editForm.status = record.status
  editForm.ops_reply = record.ops_reply || ''
  editForm.ops_notes = record.ops_notes || ''
  editOpen.value = true
}

async function saveEdit() {
  if (!editId.value) return
  saving.value = true
  error.value = ''
  try {
    await opsFetch(`/support/tickets/${editId.value}`, {
      method: 'PATCH',
      body: {
        status: editForm.status,
        ops_reply: editForm.ops_reply || null,
        ops_notes: editForm.ops_notes || null,
      },
    })
    editOpen.value = false
    await load(1)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  } finally {
    saving.value = false
  }
}

onMounted(() => load(1))
</script>
