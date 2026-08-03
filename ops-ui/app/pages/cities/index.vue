<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Cities</h1>
        <p>Location master data (OPS-LOC-01–03).</p>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="card stack" style="margin-bottom: 1.25rem" @submit.prevent="createCity">
      <h2 class="card-title">Add city</h2>
      <div class="grid-2">
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" required />
        </div>
        <div class="field">
          <label for="state">State</label>
          <input id="state" v-model="form.state" required />
        </div>
        <div class="field">
          <label for="order">Display order</label>
          <input id="order" v-model.number="form.display_order" type="number" />
        </div>
        <div class="field">
          <label class="checkbox-row" style="margin-top: 1.5rem">
            <input v-model="form.is_active" type="checkbox" />
            Active
          </label>
        </div>
      </div>
      <button class="btn" type="submit" :disabled="saving">{{ saving ? '…' : 'Create city' }}</button>
    </form>

    <div class="scroll-x card" style="padding: 0">
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>State</th>
            <th>Active</th>
            <th>Order</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in cities" :key="c.id">
            <td>{{ c.name }}</td>
            <td>{{ c.state }}</td>
            <td>
              <span :class="c.is_active ? 'badge badge-ok' : 'badge badge-off'">
                {{ c.is_active ? 'yes' : 'no' }}
              </span>
            </td>
            <td>{{ c.display_order }}</td>
            <td class="actions">
              <NuxtLink class="btn btn-secondary btn-sm" :to="`/cities/${c.id}`">Societies</NuxtLink>
              <button class="btn btn-secondary btn-sm" type="button" @click="toggleActive(c)">
                {{ c.is_active ? 'Deactivate' : 'Activate' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { City, Paginated } from '~/types/ops'

const { opsFetch } = useOpsApi()
const cities = ref<City[]>([])
const error = ref('')
const saving = ref(false)
const form = reactive({ name: '', state: '', is_active: true, display_order: 0 })

async function load() {
  error.value = ''
  try {
    const data = await opsFetch<Paginated<City>>('/cities', {
      query: { include_inactive: true, page_size: 100 },
    })
    cities.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load cities'
  }
}

async function createCity() {
  saving.value = true
  error.value = ''
  try {
    await opsFetch<City>('/cities', { method: 'POST', body: { ...form } })
    form.name = ''
    form.state = ''
    form.display_order = 0
    form.is_active = true
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create failed'
  } finally {
    saving.value = false
  }
}

async function toggleActive(c: City) {
  try {
    await opsFetch<City>(`/cities/${c.id}`, {
      method: 'PATCH',
      body: { is_active: !c.is_active },
    })
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  }
}

onMounted(load)
</script>
