<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Cities</a-typography-title>
    <a-typography-paragraph type="secondary">
      Location master data (OPS-LOC-01–03). State is chosen from the India states list.
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
              <a-input v-model:value="form.name" placeholder="e.g. Bengaluru" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-form-item
              label="State"
              name="state"
              :rules="[{ required: true, message: 'State is required' }]"
            >
              <a-select
                v-model:value="form.state"
                show-search
                :options="INDIA_STATE_OPTIONS"
                placeholder="Select state / UT"
                option-filter-prop="label"
                style="width: 100%"
              />
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
        :scroll="{ x: 720 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'active'">
            <a-tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? 'yes' : 'no' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space wrap>
              <a-button type="link" size="small" @click="openEdit(record)">Edit</a-button>
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

    <a-modal
      v-model:open="editOpen"
      title="Edit city"
      :confirm-loading="editSaving"
      ok-text="Save"
      destroy-on-close
      @ok="submitEdit"
    >
      <a-alert
        v-if="editError"
        type="error"
        show-icon
        :message="editError"
        style="margin-bottom: 1rem"
      />
      <a-form ref="editFormRef" layout="vertical" :model="editForm">
        <a-form-item
          label="Name"
          name="name"
          :rules="[{ required: true, message: 'City name is required' }]"
        >
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-form-item
          label="State"
          name="state"
          :rules="[{ required: true, message: 'State is required' }]"
        >
          <a-select
            v-model:value="editForm.state"
            show-search
            :options="stateOptionsForEdit"
            placeholder="Select state / UT"
            option-filter-prop="label"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="Display order" name="display_order">
          <a-input-number v-model:value="editForm.display_order" style="width: 100%" />
        </a-form-item>
        <a-form-item label="Active" name="is_active">
          <a-switch v-model:checked="editForm.is_active" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import type { City, Paginated } from '~/types/ops'
import { INDIA_STATE_OPTIONS, INDIA_STATES } from '~/utils/indiaStates'

const { opsFetch } = useOpsApi()
const cities = ref<City[]>([])
const error = ref('')
const saving = ref(false)
const loading = ref(false)
const form = reactive({ name: '', state: undefined as string | undefined, is_active: true, display_order: 0 })

const editOpen = ref(false)
const editSaving = ref(false)
const editError = ref('')
const editId = ref<string | null>(null)
const editFormRef = ref<{ validate: () => Promise<void> } | null>(null)
const editForm = reactive({
  name: '',
  state: undefined as string | undefined,
  is_active: true,
  display_order: 0,
})

/** Include legacy free-text state values so existing rows remain selectable. */
const stateOptionsForEdit = computed(() => {
  const options = [...INDIA_STATE_OPTIONS]
  const current = editForm.state?.trim()
  if (current && !INDIA_STATES.includes(current)) {
    options.unshift({ label: `${current} (current)`, value: current })
  }
  return options
})

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'State', dataIndex: 'state', key: 'state' },
  { title: 'Active', key: 'active' },
  { title: 'Order', dataIndex: 'display_order', key: 'order', width: 90 },
  { title: '', key: 'actions', width: 260 },
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
    await opsFetch<City>('/cities', {
      method: 'POST',
      body: {
        name: form.name,
        state: form.state,
        is_active: form.is_active,
        display_order: form.display_order,
      },
    })
    form.name = ''
    form.state = undefined
    form.display_order = 0
    form.is_active = true
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create failed'
  } finally {
    saving.value = false
  }
}

function openEdit(c: City) {
  editId.value = c.id
  editForm.name = c.name
  editForm.state = c.state
  editForm.is_active = c.is_active
  editForm.display_order = c.display_order
  editError.value = ''
  editOpen.value = true
}

async function submitEdit() {
  if (!editId.value) return Promise.reject(new Error('No city selected'))
  editError.value = ''
  try {
    await editFormRef.value?.validate()
  } catch {
    return Promise.reject(new Error('validation failed'))
  }
  editSaving.value = true
  try {
    await opsFetch<City>(`/cities/${editId.value}`, {
      method: 'PATCH',
      body: {
        name: editForm.name.trim(),
        state: String(editForm.state).trim(),
        is_active: editForm.is_active,
        display_order: editForm.display_order,
      },
    })
    editOpen.value = false
    await load()
  } catch (err: unknown) {
    editError.value = err instanceof Error ? err.message : 'Update failed'
    return Promise.reject(err)
  } finally {
    editSaving.value = false
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
