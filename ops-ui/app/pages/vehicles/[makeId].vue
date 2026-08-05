<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">Models</a-typography-title>
        <a-typography-paragraph type="secondary" style="margin-bottom: 0">
          Models for make <code>{{ makeId }}</code> (OPS-VEH-04–06).
        </a-typography-paragraph>
      </div>
      <a-button @click="navigateTo('/vehicles')">All makes</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <a-card title="Add model" style="margin-bottom: 1rem">
      <a-form layout="vertical" @finish="createModel">
        <a-row :gutter="16">
          <a-col :xs="24" :md="10">
            <a-form-item label="Name" :rules="[{ required: true }]">
              <a-input v-model:value="form.name" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-form-item label="Size tier">
              <a-select v-model:value="form.size_tier">
                <a-select-option value="small">small</a-select-option>
                <a-select-option value="medium">medium</a-select-option>
                <a-select-option value="large">large</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="6">
            <a-form-item label="Active">
              <a-switch v-model:checked="form.is_active" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-button type="primary" html-type="submit" :loading="saving">Create model</a-button>
      </a-form>
    </a-card>

    <div class="ops-table-scroll">
      <a-table
        :columns="columns"
        :data-source="models"
        row-key="id"
        :pagination="false"
        :scroll="{ x: 560 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'tier'">
            <a-tag color="purple">{{ record.size_tier }}</a-tag>
          </template>
          <template v-else-if="column.key === 'active'">
            <a-tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? 'yes' : 'no' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space wrap>
              <a-button size="small" @click="cycleTier(record)">Cycle size</a-button>
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

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Size', key: 'tier', width: 110 },
  { title: 'Active', key: 'active', width: 100 },
  { title: '', key: 'actions' },
]

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
