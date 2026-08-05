<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">User detail</a-typography-title>
        <a-typography-text type="secondary" code>{{ id }}</a-typography-text>
      </div>
      <a-button @click="navigateTo('/users')">Back</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-spin v-else-if="loading || !user" />
    <template v-else>
      <a-card style="margin-bottom: 1rem">
        <a-descriptions :column="{ xs: 1, sm: 2 }" bordered size="small">
          <a-descriptions-item label="Phone">
            <code>{{ user.phone }}</code>
          </a-descriptions-item>
          <a-descriptions-item label="Name">{{ user.name || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Email">{{ user.email || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Status">
            <a-tag :color="user.is_active ? 'success' : 'default'">
              {{ user.is_active ? 'active' : 'inactive' }}
            </a-tag>
            <a-tag v-if="user.deleted_at" color="error">deleted</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="City">{{ user.city?.name || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Society">{{ user.society?.name || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Vehicle">{{ user.has_vehicle ? 'Yes' : 'No' }}</a-descriptions-item>
          <a-descriptions-item label="Created">{{ formatDateTime(user.created_at) }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-space wrap>
        <a-popconfirm
          v-if="user.is_active"
          title="Deactivate this consumer account?"
          ok-text="Deactivate"
          ok-type="danger"
          @confirm="deactivate"
        >
          <a-button danger :loading="acting">Deactivate</a-button>
        </a-popconfirm>
        <a-button v-else type="primary" :loading="acting" @click="reactivate">Reactivate</a-button>
        <a-button v-if="user.has_vehicle" @click="navigateTo(`/users/${id}/vehicle`)">
          View vehicle
        </a-button>
      </a-space>
      <a-alert v-if="actionMsg" type="success" show-icon :message="actionMsg" style="margin-top: 1rem" />
    </template>
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
