<template>
  <div>
    <div class="page-header">
      <div>
        <h1>User detail</h1>
        <p class="mono muted">{{ id }}</p>
      </div>
      <NuxtLink class="btn btn-secondary" to="/users">Back</NuxtLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-else-if="loading || !user" class="muted">Loading…</div>
    <div v-else class="stack">
      <div class="card">
        <dl class="dl">
          <dt>Phone</dt>
          <dd class="mono">{{ user.phone }}</dd>
          <dt>Name</dt>
          <dd>{{ user.name || '—' }}</dd>
          <dt>Email</dt>
          <dd>{{ user.email || '—' }}</dd>
          <dt>Status</dt>
          <dd>
            <span :class="user.is_active ? 'badge badge-ok' : 'badge badge-off'">
              {{ user.is_active ? 'active' : 'inactive' }}
            </span>
            <span v-if="user.deleted_at" class="badge badge-warn" style="margin-left: 0.35rem">
              deleted
            </span>
          </dd>
          <dt>City</dt>
          <dd>{{ user.city?.name || '—' }}</dd>
          <dt>Society</dt>
          <dd>{{ user.society?.name || '—' }}</dd>
          <dt>Vehicle</dt>
          <dd>{{ user.has_vehicle ? 'Yes' : 'No' }}</dd>
          <dt>Created</dt>
          <dd>{{ formatDateTime(user.created_at) }}</dd>
        </dl>
      </div>

      <div class="row">
        <button
          v-if="user.is_active"
          type="button"
          class="btn btn-danger"
          :disabled="acting"
          @click="deactivate"
        >
          Deactivate
        </button>
        <button v-else type="button" class="btn" :disabled="acting" @click="reactivate">
          Reactivate
        </button>
        <NuxtLink
          v-if="user.has_vehicle"
          class="btn btn-secondary"
          :to="`/users/${id}/vehicle`"
        >
          View vehicle
        </NuxtLink>
      </div>
      <div v-if="actionMsg" class="alert alert-success">{{ actionMsg }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { OpsUserDetail } from '~/types/ops'
import { formatDateTime } from '~/utils/format'

const route = useRoute()
const id = computed(() => String(route.params.id))
const { opsFetch } = useOpsApi()

const user = ref<OpsUserDetail | null>(null)
const loading = ref(true)
const error = ref('')
const acting = ref(false)
const actionMsg = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    user.value = await opsFetch<OpsUserDetail>(`/users/${id.value}`)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load user'
  } finally {
    loading.value = false
  }
}

async function deactivate() {
  if (!confirm('Deactivate this consumer account?')) return
  acting.value = true
  actionMsg.value = ''
  try {
    user.value = await opsFetch<OpsUserDetail>(`/users/${id.value}/deactivate`, { method: 'POST' })
    actionMsg.value = 'Account deactivated.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    acting.value = false
  }
}

async function reactivate() {
  acting.value = true
  actionMsg.value = ''
  try {
    user.value = await opsFetch<OpsUserDetail>(`/users/${id.value}/reactivate`, { method: 'POST' })
    actionMsg.value = 'Account reactivated.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    acting.value = false
  }
}

onMounted(load)
</script>
