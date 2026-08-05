<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Vehicle makes</a-typography-title>
    <a-typography-paragraph type="secondary">
      Catalog brands (OPS-VEH-01–03). Size tier lives on models.
    </a-typography-paragraph>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <a-card title="Add make" style="margin-bottom: 1rem">
      <a-form layout="vertical" @finish="createMake">
        <a-row :gutter="16">
          <a-col :xs="24" :md="12">
            <a-form-item label="Name" :rules="[{ required: true }]">
              <a-input v-model:value="form.name" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="6">
            <a-form-item label="Display order">
              <a-input-number v-model:value="form.display_order" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="6">
            <a-form-item label="Active">
              <a-switch v-model:checked="form.is_active" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-button type="primary" html-type="submit" :loading="saving">Create make</a-button>
      </a-form>
    </a-card>

    <div class="ops-table-scroll">
      <a-table
        :columns="columns"
        :data-source="makes"
        row-key="id"
        :pagination="false"
        :scroll="{ x: 560 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'active'">
            <a-tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? 'yes' : 'no' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space wrap>
              <a-button type="link" size="small" @click="navigateTo(`/vehicles/${record.id}`)">
                Models
              </a-button>
              <a-button size="small" @click="toggle(record)">
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
import type { Paginated, VehicleMake } from '~/types/ops'

const { opsFetch } = useOpsApi()
const makes = ref<VehicleMake[]>([])
const error = ref('')
const saving = ref(false)
const form = reactive({ name: '', is_active: true, display_order: 0 })

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Active', key: 'active', width: 100 },
  { title: 'Order', dataIndex: 'display_order', key: 'order', width: 90 },
  { title: '', key: 'actions' },
]

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
