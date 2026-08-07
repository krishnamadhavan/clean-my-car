<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Vehicle makes</a-typography-title>
    <a-typography-paragraph type="secondary">
      Catalog brands (OPS-VEH-01–03). Size tier lives on models.
      Display order must be unique (leave blank on create to auto-assign the next free value).
    </a-typography-paragraph>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <a-card title="Add make" style="margin-bottom: 1rem">
      <a-form layout="vertical" :model="form" @finish="createMake">
        <a-row :gutter="16">
          <a-col :xs="24" :md="12">
            <a-form-item
              label="Name"
              name="name"
              :rules="[{ required: true, message: 'Make name is required' }]"
            >
              <a-input v-model:value="form.name" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="6">
            <a-form-item
              label="Display order"
              name="display_order"
              :rules="[{ validator: validateCreateDisplayOrder }]"
              extra="Unique sort key. Empty = next free."
            >
              <a-input-number
                v-model:value="form.display_order"
                :min="0"
                style="width: 100%"
                placeholder="auto"
              />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="6">
            <a-form-item label="Active" name="is_active">
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
              <a-button type="link" size="small" @click="openEdit(record)">Edit</a-button>
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

    <a-modal
      v-model:open="editOpen"
      title="Edit make"
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
          :rules="[{ required: true, message: 'Make name is required' }]"
        >
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-form-item
          label="Display order"
          name="display_order"
          :rules="[
            { required: true, message: 'Display order is required' },
            { validator: validateEditDisplayOrder },
          ]"
          extra="Must be unique across all makes."
        >
          <a-input-number v-model:value="editForm.display_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="Active" name="is_active">
          <a-switch v-model:checked="editForm.is_active" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import type { Paginated, VehicleMake } from '~/types/ops'

const { opsFetch } = useOpsApi()
const makes = ref<VehicleMake[]>([])
const error = ref('')
const saving = ref(false)
const form = reactive({
  name: '',
  is_active: true,
  display_order: null as number | null,
})

const editOpen = ref(false)
const editSaving = ref(false)
const editError = ref('')
const editId = ref<string | null>(null)
const editFormRef = ref<{ validate: () => Promise<void> } | null>(null)
const editForm = reactive({
  name: '',
  is_active: true,
  display_order: 0,
})

const usedDisplayOrders = computed(() => new Set(makes.value.map((m) => m.display_order)))

async function validateCreateDisplayOrder(_rule: unknown, value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value as number)) {
    return Promise.resolve()
  }
  if (usedDisplayOrders.value.has(value)) {
    return Promise.reject(new Error(`Display order ${value} is already used`))
  }
  return Promise.resolve()
}

async function validateEditDisplayOrder(_rule: unknown, value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value as number)) {
    return Promise.reject(new Error('Display order is required'))
  }
  const taken = makes.value.some((m) => m.display_order === value && m.id !== editId.value)
  if (taken) {
    return Promise.reject(new Error(`Display order ${value} is already used`))
  }
  return Promise.resolve()
}

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Active', key: 'active', width: 100 },
  { title: 'Order', dataIndex: 'display_order', key: 'order', width: 90 },
  { title: '', key: 'actions', width: 260 },
]

async function load() {
  error.value = ''
  try {
    const data = await opsFetch<Paginated<VehicleMake>>('/vehicle-makes', {
      query: { include_inactive: true, page_size: 100 },
    })
    makes.value = data.items
    form.display_order = null
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load makes'
  }
}

async function createMake() {
  saving.value = true
  error.value = ''
  try {
    const body: Record<string, unknown> = {
      name: form.name,
      is_active: form.is_active,
    }
    if (form.display_order !== null && form.display_order !== undefined) {
      body.display_order = form.display_order
    }
    await opsFetch('/vehicle-makes', { method: 'POST', body })
    form.name = ''
    form.display_order = null
    form.is_active = true
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create failed'
  } finally {
    saving.value = false
  }
}

function openEdit(m: VehicleMake) {
  editId.value = m.id
  editForm.name = m.name
  editForm.is_active = m.is_active
  editForm.display_order = m.display_order
  editError.value = ''
  editOpen.value = true
}

async function submitEdit() {
  if (!editId.value) return Promise.reject(new Error('No make selected'))
  editError.value = ''
  try {
    await editFormRef.value?.validate()
  } catch {
    return Promise.reject(new Error('validation failed'))
  }
  editSaving.value = true
  try {
    await opsFetch(`/vehicle-makes/${editId.value}`, {
      method: 'PATCH',
      body: {
        name: editForm.name.trim(),
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
