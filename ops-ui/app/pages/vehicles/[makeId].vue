<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Models</h1>
        <p>Models for make <span class="mono">{{ makeId }}</span> (OPS-VEH-04–06).</p>
      </div>
      <NuxtLink class="btn btn-secondary" to="/vehicles">All makes</NuxtLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="card stack" style="margin-bottom: 1.25rem" @submit.prevent="createModel">
      <h2 class="card-title">Add model</h2>
      <div class="grid-2">
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" required />
        </div>
        <div class="field">
          <label for="tier">Size tier</label>
          <select id="tier" v-model="form.size_tier" required>
            <option value="small">small</option>
            <option value="medium">medium</option>
            <option value="large">large</option>
          </select>
        </div>
      </div>
      <label class="checkbox-row">
        <input v-model="form.is_active" type="checkbox" />
        Active
      </label>
      <button class="btn" type="submit" :disabled="saving">Create model</button>
    </form>

    <div class="scroll-x card" style="padding: 0">
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Active</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in models" :key="m.id">
            <td>{{ m.name }}</td>
            <td><span class="badge">{{ m.size_tier }}</span></td>
            <td>
              <span :class="m.is_active ? 'badge badge-ok' : 'badge badge-off'">
                {{ m.is_active ? 'yes' : 'no' }}
              </span>
            </td>
            <td class="actions">
              <button class="btn btn-secondary btn-sm" type="button" @click="cycleTier(m)">
                Cycle size
              </button>
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
import type { Paginated, VehicleModel, VehicleSizeTier } from '~/types/ops'

const route = useRoute()
const makeId = computed(() => String(route.params.makeId))
const { opsFetch } = useOpsApi()

const models = ref<VehicleModel[]>([])
const error = ref('')
const saving = ref(false)
const form = reactive({
  name: '',
  size_tier: 'medium' as VehicleSizeTier,
  is_active: true,
  display_order: 0,
})

const tiers: VehicleSizeTier[] = ['small', 'medium', 'large']

async function load() {
  error.value = ''
  try {
    const data = await opsFetch<Paginated<VehicleModel>>(`/vehicle-makes/${makeId.value}/models`, {
      query: { include_inactive: true, page_size: 100 },
    })
    models.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load models'
  }
}

async function createModel() {
  saving.value = true
  error.value = ''
  try {
    await opsFetch(`/vehicle-makes/${makeId.value}/models`, {
      method: 'POST',
      body: { ...form },
    })
    form.name = ''
    form.size_tier = 'medium'
    form.is_active = true
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create failed'
  } finally {
    saving.value = false
  }
}

async function toggle(m: VehicleModel) {
  try {
    await opsFetch(`/vehicle-models/${m.id}`, {
      method: 'PATCH',
      body: { is_active: !m.is_active },
    })
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  }
}

async function cycleTier(m: VehicleModel) {
  const next = tiers[(tiers.indexOf(m.size_tier) + 1) % tiers.length]
  try {
    await opsFetch(`/vehicle-models/${m.id}`, {
      method: 'PATCH',
      body: { size_tier: next },
    })
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  }
}

onMounted(load)
</script>
