<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">{{ city?.name || 'City' }}</a-typography-title>
        <a-typography-paragraph type="secondary" style="margin-bottom: 0">
          Societies (OPS-LOC-04–07). Service weekdays: pick exactly 3.
        </a-typography-paragraph>
      </div>
      <a-button @click="navigateTo('/cities')">All cities</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <a-card title="Add society" style="margin-bottom: 1rem">
      <a-form layout="vertical" :model="form" @finish="createSociety">
        <a-row :gutter="16">
          <a-col :xs="24" :md="12">
            <a-form-item
              label="Name"
              name="name"
              :rules="[{ required: true, message: 'Society name is required' }]"
            >
              <a-input v-model:value="form.name" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-form-item label="Address" name="address_line">
              <a-input v-model:value="form.address_line" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="Service weekdays (exactly 3)" name="service_weekdays">
          <a-checkbox-group v-model:value="form.service_weekdays" :options="weekdayOptions" />
        </a-form-item>
        <a-form-item label="Serviceable (live)" name="is_serviceable">
          <a-switch v-model:checked="form.is_serviceable" />
        </a-form-item>
        <a-button type="primary" html-type="submit" :loading="saving">Create society</a-button>
      </a-form>
    </a-card>

    <div class="ops-table-scroll">
      <a-table
        :columns="columns"
        :data-source="societies"
        row-key="id"
        :pagination="false"
        :scroll="{ x: 640 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <strong>{{ record.name }}</strong>
            <div v-if="record.address_line" style="color: rgba(0,0,0,0.45); font-size: 0.85rem">
              {{ record.address_line }}
            </div>
          </template>
          <template v-else-if="column.key === 'weekdays'">
            {{ formatWeekdays(record.service_weekdays) }}
          </template>
          <template v-else-if="column.key === 'live'">
            <a-tag :color="record.is_serviceable ? 'success' : 'default'">
              {{ record.is_serviceable ? 'yes' : 'no' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button size="small" @click="toggleLive(record)">
              {{ record.is_serviceable ? 'Take offline' : 'Go live' }}
            </a-button>
          </template>
        </template>
      </a-table>
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

const weekdayOptions = WEEKDAY_LABELS.map((label, value) => ({ label, value }))

const columns = [
  { title: 'Name', key: 'name' },
  { title: 'Weekdays', key: 'weekdays' },
  { title: 'Live', key: 'live', width: 90 },
  { title: '', key: 'actions', width: 130 },
]

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
