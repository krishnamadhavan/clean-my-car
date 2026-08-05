<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">Waitlist entry</a-typography-title>
        <a-typography-paragraph type="secondary" style="margin-bottom: 0">
          Update status and notes (OPS-WAIT-02/03).
        </a-typography-paragraph>
      </div>
      <a-button @click="navigateTo('/waitlist')">Back</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-spin v-else-if="loading || !entry" />
    <template v-else>
      <a-card style="margin-bottom: 1rem">
        <a-descriptions :column="{ xs: 1, sm: 2 }" bordered size="small">
          <a-descriptions-item label="Society">{{ entry.society_name }}</a-descriptions-item>
          <a-descriptions-item label="City">{{ entry.city?.name || entry.city_id }}</a-descriptions-item>
          <a-descriptions-item label="Phone"><code>{{ entry.phone }}</code></a-descriptions-item>
          <a-descriptions-item label="Status">
            <a-tag color="processing">{{ entry.status }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="Created">{{ formatDateTime(entry.created_at) }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-card title="Triage">
        <a-form layout="vertical" @finish="save">
          <a-row :gutter="16">
            <a-col :xs="24" :md="12">
              <a-form-item label="Status">
                <a-select v-model:value="form.status">
                  <a-select-option value="pending">pending</a-select-option>
                  <a-select-option value="contacted">contacted</a-select-option>
                  <a-select-option value="converted">converted</a-select-option>
                  <a-select-option value="closed">closed</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="Society name">
                <a-input v-model:value="form.society_name" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="Notes">
            <a-textarea v-model:value="form.notes" :rows="4" />
          </a-form-item>
          <a-alert v-if="msg" type="success" show-icon :message="msg" style="margin-bottom: 1rem" />
          <a-button type="primary" html-type="submit" :loading="saving">Save</a-button>
        </a-form>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { WaitlistEntry, WaitlistStatus } from '~/types/ops'
import { formatDateTime } from '~/utils/format'

const route = useRoute()
const id = computed(() => String(route.params.id))
const { opsFetch } = useOpsApi()

const entry = ref<WaitlistEntry | null>(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const msg = ref('')
const form = reactive({
  status: 'pending' as WaitlistStatus,
  notes: '',
  society_name: '',
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    entry.value = await opsFetch<WaitlistEntry>(`/waitlist/${id.value}`)
    form.status = entry.value.status
    form.notes = entry.value.notes || ''
    form.society_name = entry.value.society_name
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  msg.value = ''
  error.value = ''
  try {
    entry.value = await opsFetch<WaitlistEntry>(`/waitlist/${id.value}`, {
      method: 'PATCH',
      body: {
        status: form.status,
        notes: form.notes || null,
        society_name: form.society_name,
      },
    })
    msg.value = 'Updated.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
