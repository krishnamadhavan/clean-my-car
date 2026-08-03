<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ city?.name || 'City' }}</h1>
        <p>Societies (OPS-LOC-04–07). Service weekdays: pick exactly 3.</p>
      </div>
      <NuxtLink class="btn btn-secondary" to="/cities">All cities</NuxtLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="card stack" style="margin-bottom: 1.25rem" @submit.prevent="createSociety">
      <h2 class="card-title">Add society</h2>
      <div class="grid-2">
        <div class="field">
          <label for="sname">Name</label>
          <input id="sname" v-model="form.name" required />
        </div>
        <div class="field">
          <label for="addr">Address</label>
          <input id="addr" v-model="form.address_line" />
        </div>
      </div>
      <div class="field">
        <label>Service weekdays (exactly 3)</label>
        <div class="checkbox-row">
          <label v-for="(label, idx) in WEEKDAY_LABELS" :key="idx">
            <input v-model="form.service_weekdays" type="checkbox" :value="idx" />
            {{ label }}
          </label>
        </div>
      </div>
      <label class="checkbox-row">
        <input v-model="form.is_serviceable" type="checkbox" />
        Serviceable (live)
      </label>
      <button class="btn" type="submit" :disabled="saving">Create society</button>
    </form>

    <div class="scroll-x card" style="padding: 0">
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Weekdays</th>
            <th>Live</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in societies" :key="s.id">
            <td>
              <strong>{{ s.name }}</strong>
              <div v-if="s.address_line" class="muted" style="font-size: 0.85rem">{{ s.address_line }}</div>
            </td>
            <td>{{ formatWeekdays(s.service_weekdays) }}</td>
            <td>
              <span :class="s.is_serviceable ? 'badge badge-ok' : 'badge badge-off'">
                {{ s.is_serviceable ? 'yes' : 'no' }}
              </span>
            </td>
            <td class="actions">
              <button class="btn btn-secondary btn-sm" type="button" @click="toggleLive(s)">
                {{ s.is_serviceable ? 'Take offline' : 'Go live' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { City, Paginated, Society } from '~/types/ops'
import { formatWeekdays, WEEKDAY_LABELS } from '~/utils/format'

const route = useRoute()
const cityId = computed(() => String(route.params.id))
const { opsFetch } = useOpsApi()

const city = ref<City | null>(null)
const societies = ref<Society[]>([])
const error = ref('')
const saving = ref(false)
const form = reactive({
  name: '',
  address_line: '',
  service_weekdays: [0, 2, 4] as number[],
  is_serviceable: false,
})

async function load() {
  error.value = ''
  try {
    const cities = await opsFetch<Paginated<City>>('/cities', {
      query: { include_inactive: true, page_size: 100 },
    })
    city.value = cities.items.find((c) => c.id === cityId.value) || null
    const data = await opsFetch<Paginated<Society>>(`/cities/${cityId.value}/societies`, {
      query: { include_non_serviceable: true, page_size: 100 },
    })
    societies.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load'
  }
}

async function createSociety() {
  if (form.service_weekdays.length !== 3) {
    error.value = 'Select exactly 3 service weekdays'
    return
  }
  saving.value = true
  error.value = ''
  try {
    await opsFetch(`/cities/${cityId.value}/societies`, {
      method: 'POST',
      body: {
        name: form.name,
        address_line: form.address_line || null,
        service_weekdays: form.service_weekdays.slice().sort((a, b) => a - b),
        is_serviceable: form.is_serviceable,
      },
    })
    form.name = ''
    form.address_line = ''
    form.is_serviceable = false
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create failed'
  } finally {
    saving.value = false
  }
}

async function toggleLive(s: Society) {
  try {
    await opsFetch(`/societies/${s.id}`, {
      method: 'PATCH',
      body: { is_serviceable: !s.is_serviceable },
    })
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  }
}

onMounted(load)
</script>
