<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Waitlist</h1>
        <p>Triage demand (OPS-WAIT-01–04).</p>
      </div>
    </div>

    <div v-if="summary" class="stat-grid" style="margin-bottom: 1rem">
      <div class="stat">
        <div class="label">Total</div>
        <div class="value">{{ summary.total }}</div>
      </div>
      <div v-for="row in summary.by_status" :key="row.status" class="stat">
        <div class="label">{{ row.status }}</div>
        <div class="value">{{ row.count }}</div>
      </div>
    </div>

    <form class="toolbar" @submit.prevent="load(1)">
      <div class="field">
        <label for="status">Status</label>
        <select id="status" v-model="filters.status">
          <option value="">All</option>
          <option value="pending">pending</option>
          <option value="contacted">contacted</option>
          <option value="converted">converted</option>
          <option value="closed">closed</option>
        </select>
      </div>
      <div class="field">
        <label for="phone">Phone</label>
        <input id="phone" v-model="filters.phone" type="search" />
      </div>
      <div class="field">
        <label for="society">Society name</label>
        <input id="society" v-model="filters.society_name" type="search" />
      </div>
      <button class="btn" type="submit" :disabled="loading">Filter</button>
    </form>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div class="scroll-x card" style="padding: 0">
      <table class="table">
        <thead>
          <tr>
            <th>Society</th>
            <th>City</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Created</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in items" :key="e.id">
            <td>{{ e.society_name }}</td>
            <td>{{ e.city?.name || shortId(e.city_id) }}</td>
            <td class="mono">{{ e.phone }}</td>
            <td><span class="badge">{{ e.status }}</span></td>
            <td>{{ formatDateTime(e.created_at) }}</td>
            <td class="actions">
              <NuxtLink class="btn btn-secondary btn-sm" :to="`/waitlist/${e.id}`">Open</NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
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
const filters = reactive({ status: '', phone: '', society_name: '' })

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
