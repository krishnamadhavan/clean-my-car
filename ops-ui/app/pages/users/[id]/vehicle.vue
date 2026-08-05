<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">User vehicle</a-typography-title>
        <a-typography-paragraph type="secondary" style="margin-bottom: 0">
          Inspect / correct registration (OPS-VEH-07/08).
        </a-typography-paragraph>
      </div>
      <a-button @click="navigateTo(`/users/${userId}`)">Back to user</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-spin v-else-if="loading" />
    <template v-else-if="vehicle">
      <a-card style="margin-bottom: 1rem" title="Current vehicle">
        <a-descriptions :column="{ xs: 1, sm: 2 }" bordered size="small">
          <a-descriptions-item label="Make">{{ vehicle.make?.name || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Model">{{ vehicle.model?.name || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Size tier">
            <a-tag color="purple">{{ vehicle.size_tier }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="Plate">
            <code>{{ vehicle.plate_number || '—' }}</code>
          </a-descriptions-item>
          <a-descriptions-item label="Nickname">{{ vehicle.nickname || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Colour">{{ vehicle.colour || '—' }}</a-descriptions-item>
          <a-descriptions-item label="Parking">
            {{ [vehicle.parking_tower, vehicle.parking_slot].filter(Boolean).join(' · ') || '—' }}
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-card title="Correct vehicle">
        <a-form layout="vertical" @finish="save">
          <a-row :gutter="16">
            <a-col :xs="24" :md="12">
              <a-form-item label="Model ID" extra="Leave blank to keep current. Size re-derives on change.">
                <a-input v-model:value="form.model_id" placeholder="UUID of catalog model" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="Plate">
                <a-input v-model:value="form.plate_number" placeholder="KA01AB1234 or 26BH1234AB" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="Nickname">
                <a-input v-model:value="form.nickname" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="Colour">
                <a-input v-model:value="form.colour" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="Parking tower">
                <a-input v-model:value="form.parking_tower" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="Parking slot">
                <a-input v-model:value="form.parking_slot" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-alert v-if="saveMsg" type="success" show-icon :message="saveMsg" style="margin-bottom: 1rem" />
          <a-button type="primary" html-type="submit" :loading="saving">Save corrections</a-button>
        </a-form>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { UserVehicle } from '~/types/ops'

const route = useRoute()
const userId = computed(() => String(route.params.id))
const { opsFetch } = useOpsApi()

const vehicle = ref<UserVehicle | null>(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const saveMsg = ref('')

const form = reactive({
  model_id: '',
  plate_number: '',
  nickname: '',
  colour: '',
  parking_slot: '',
  parking_tower: '',
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    vehicle.value = await opsFetch<UserVehicle>(`/users/${userId.value}/vehicle`)
    form.plate_number = vehicle.value.plate_number || ''
    form.nickname = vehicle.value.nickname || ''
    form.colour = vehicle.value.colour || ''
    form.parking_slot = vehicle.value.parking_slot || ''
    form.parking_tower = vehicle.value.parking_tower || ''
    form.model_id = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load vehicle'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  saveMsg.value = ''
  error.value = ''
  const body: Record<string, string> = {}
  if (form.model_id.trim()) body.model_id = form.model_id.trim()
  body.plate_number = form.plate_number
  body.nickname = form.nickname
  body.colour = form.colour
  body.parking_slot = form.parking_slot
  body.parking_tower = form.parking_tower
  try {
    vehicle.value = await opsFetch<UserVehicle>(`/users/${userId.value}/vehicle`, {
      method: 'PATCH',
      body,
    })
    saveMsg.value = 'Vehicle updated.'
    form.model_id = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
