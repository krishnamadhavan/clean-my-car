<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Users</h1>
        <p>Search consumer accounts (OPS-PROF-01).</p>
      </div>
    </div>

    <form class="toolbar" @submit.prevent="load(1)">
      <div class="field">
        <label for="q">Search</label>
        <input id="q" v-model="q" type="search" placeholder="Phone, UUID, name, email" />
      </div>
      <button class="btn" type="submit" :disabled="loading">{{ loading ? '…' : 'Search' }}</button>
    </form>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div v-else-if="!loading && items.length === 0" class="empty">No users found.</div>

    <div v-else class="scroll-x card" style="padding: 0">
      <table class="table">
        <thead>
          <tr>
            <th>Phone</th>
            <th>Name</th>
            <th>Status</th>
            <th>Created</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in items" :key="u.id">
            <td class="mono">{{ u.phone }}</td>
            <td>{{ u.name || '—' }}</td>
            <td>
              <span :class="u.is_active ? 'badge badge-ok' : 'badge badge-off'">
                {{ u.is_active ? 'active' : 'inactive' }}
              </span>
            </td>
            <td>{{ formatDateTime(u.created_at) }}</td>
            <td class="actions">
              <NuxtLink class="btn btn-secondary btn-sm" :to="`/users/${u.id}`">Open</NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="total > pageSize" class="row" style="margin-top: 1rem">
      <button class="btn btn-secondary btn-sm" :disabled="page <= 1 || loading" @click="load(page - 1)">
        Prev
      </button>
      <span class="muted">Page {{ page }} · {{ total }} total</span>
      <button
        class="btn btn-secondary btn-sm"
        :disabled="page * pageSize >= total || loading"
        @click="load(page + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { OpsUserSummary, Paginated } from '~/types/ops'
import { formatDateTime } from '~/utils/format'

const { opsFetch } = useOpsApi()
const q = ref('')
const items = ref<OpsUserSummary[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)
const error = ref('')

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

onMounted(() => load(1))
</script>
