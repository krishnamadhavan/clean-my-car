<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Vehicle makes</h1>
        <p>Catalog brands (OPS-VEH-01–03). Size tier lives on models.</p>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="card stack" style="margin-bottom: 1.25rem" @submit.prevent="createMake">
      <h2 class="card-title">Add make</h2>
      <div class="grid-2">
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" required />
        </div>
        <div class="field">
          <label for="order">Display order</label>
          <input id="order" v-model.number="form.display_order" type="number" />
        </div>
      </div>
      <label class="checkbox-row">
        <input v-model="form.is_active" type="checkbox" />
        Active
      </label>
      <button class="btn" type="submit" :disabled="saving">Create make</button>
    </form>

    <div class="scroll-x card" style="padding: 0">
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Active</th>
            <th>Order</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in makes" :key="m.id">
            <td>{{ m.name }}</td>
            <td>
              <span :class="m.is_active ? 'badge badge-ok' : 'badge badge-off'">
                {{ m.is_active ? 'yes' : 'no' }}
              </span>
            </td>
            <td>{{ m.display_order }}</td>
            <td class="actions">
              <NuxtLink class="btn btn-secondary btn-sm" :to="`/vehicles/${m.id}`">Models</NuxtLink>
              <button class="btn btn-secondary btn-sm" type="button" @click="toggle(m)">
                {{ m.is_active ? 'Deactivate' : 'Activate' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Paginated, VehicleMake } from '~/types/ops'

const { opsFetch } = useOpsApi()
const makes = ref<VehicleMake[]>([])
const error = ref('')
const saving = ref(false)
const form = reactive({ name: '', is_active: true, display_order: 0 })

async function load() {
  error.value = ''
  try {
    const data = await opsFetch<Paginated<VehicleMake>>('/vehicle-makes', {
      query: { include_inactive: true, page_size: 100 },
    })
    makes.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load makes'
  }
}

async function createMake() {
  saving.value = true
  error.value = ''
  try {
    await opsFetch('/vehicle-makes', { method: 'POST', body: { ...form } })
    form.name = ''
    form.display_order = 0
    form.is_active = true
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create failed'
  } finally {
    saving.value = false
  }
}

async function toggle(m: VehicleMake) {
  try {
    await opsFetch(`/vehicle-makes/${m.id}`, {
      method: 'PATCH',
      body: { is_active: !m.is_active },
    })
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  }
}

onMounted(load)
</script>
