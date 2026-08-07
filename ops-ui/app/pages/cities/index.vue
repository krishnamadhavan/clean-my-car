<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Cities</a-typography-title>
    <a-typography-paragraph type="secondary">
      Location master data (OPS-LOC-01–03).
    </a-typography-paragraph>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <a-card title="Add city" style="margin-bottom: 1rem">
      <a-form layout="vertical" :model="form" @finish="createCity">
        <a-row :gutter="16">
          <a-col :xs="24" :md="8">
            <a-form-item
              label="Name"
              name="name"
              :rules="[{ required: true, message: 'City name is required' }]"
            >
              <a-input v-model:value="form.name" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-form-item
              label="State"
              name="state"
              :rules="[{ required: true, message: 'State is required' }]"
            >
              <a-input v-model:value="form.state" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="4">
            <a-form-item label="Display order" name="display_order">
              <a-input-number v-model:value="form.display_order" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="4">
            <a-form-item label="Active" name="is_active">
              <a-switch v-model:checked="form.is_active" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-button type="primary" html-type="submit" :loading="saving">Create city</a-button>
      </a-form>
    </a-card>

    <div class="ops-table-scroll">
      <a-table
        :columns="columns"
        :data-source="cities"
        :loading="loading"
        row-key="id"
        :pagination="false"
        :scroll="{ x: 640 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'active'">
            <a-tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? 'yes' : 'no' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space wrap>
              <a-button type="link" size="small" @click="navigateTo(`/cities/${record.id}`)">
                Societies
              </a-button>
              <a-button size="small" @click="toggleActive(record)">
                {{ record.is_active ? 'Deactivate' : 'Activate' }}
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { City, Paginated } from '~/types/ops'

const { opsFetch } = useOpsApi()
const cities = ref<City[]>([])
const error = ref('')
const saving = ref(false)
const loading = ref(false)
const form = reactive({ name: '', state: '', is_active: true, display_order: 0 })

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'State', dataIndex: 'state', key: 'state' },
  { title: 'Active', key: 'active' },
  { title: 'Order', dataIndex: 'display_order', key: 'order', width: 90 },
  { title: '', key: 'actions' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await opsFetch<Paginated<City>>('/cities', {
      query: { include_inactive: true, page_size: 100 },
    })
    cities.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load cities'
  } finally {
    loading.value = false
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
