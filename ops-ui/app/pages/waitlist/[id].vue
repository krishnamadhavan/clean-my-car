<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Waitlist entry</h1>
        <p>Update status and notes (OPS-WAIT-02/03).</p>
      </div>
      <NuxtLink class="btn btn-secondary" to="/waitlist">Back</NuxtLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-else-if="loading || !entry" class="muted">Loading…</div>
    <div v-else class="stack">
      <div class="card">
        <dl class="dl">
          <dt>Society</dt>
          <dd>{{ entry.society_name }}</dd>
          <dt>City</dt>
          <dd>{{ entry.city?.name || entry.city_id }}</dd>
          <dt>Phone</dt>
          <dd class="mono">{{ entry.phone }}</dd>
          <dt>Status</dt>
          <dd><span class="badge">{{ entry.status }}</span></dd>
          <dt>Created</dt>
          <dd>{{ formatDateTime(entry.created_at) }}</dd>
        </dl>
      </div>

      <form class="card stack" @submit.prevent="save">
        <h2 class="card-title">Triage</h2>
        <div class="grid-2">
          <div class="field">
            <label for="status">Status</label>
            <select id="status" v-model="form.status">
              <option value="pending">pending</option>
              <option value="contacted">contacted</option>
              <option value="converted">converted</option>
              <option value="closed">closed</option>
            </select>
          </div>
          <div class="field">
            <label for="society">Society name</label>
            <input id="society" v-model="form.society_name" />
          </div>
        </div>
        <div class="field">
          <label for="notes">Notes</label>
          <textarea id="notes" v-model="form.notes" rows="4" />
        </div>
        <div v-if="msg" class="alert alert-success">{{ msg }}</div>
        <button class="btn" type="submit" :disabled="saving">{{ saving ? '…' : 'Save' }}</button>
      </form>
    </div>
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
