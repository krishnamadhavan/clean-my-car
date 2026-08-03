<template>
  <div>
    <div class="page-header">
      <div>
        <h1>User vehicle</h1>
        <p>Inspect / correct registration (OPS-VEH-07/08).</p>
      </div>
      <NuxtLink class="btn btn-secondary" :to="`/users/${userId}`">Back to user</NuxtLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-else-if="loading" class="muted">Loading…</div>
    <div v-else-if="vehicle" class="stack">
      <div class="card">
        <dl class="dl">
          <dt>Make</dt>
          <dd>{{ vehicle.make?.name || '—' }}</dd>
          <dt>Model</dt>
          <dd>{{ vehicle.model?.name || '—' }}</dd>
          <dt>Size tier</dt>
          <dd><span class="badge">{{ vehicle.size_tier }}</span></dd>
          <dt>Plate</dt>
          <dd class="mono">{{ vehicle.plate_number || '—' }}</dd>
          <dt>Nickname</dt>
          <dd>{{ vehicle.nickname || '—' }}</dd>
          <dt>Colour</dt>
          <dd>{{ vehicle.colour || '—' }}</dd>
          <dt>Parking</dt>
          <dd>{{ [vehicle.parking_tower, vehicle.parking_slot].filter(Boolean).join(' · ') || '—' }}</dd>
        </dl>
      </div>

      <form class="card stack" @submit.prevent="save">
        <h2 class="card-title">Correct vehicle</h2>
        <div class="grid-2">
          <div class="field">
            <label for="model">Model ID</label>
            <input id="model" v-model="form.model_id" class="mono" placeholder="UUID of catalog model" />
            <span class="field-hint">Leave blank to keep current model. Size re-derives on change.</span>
          </div>
          <div class="field">
            <label for="plate">Plate</label>
            <input id="plate" v-model="form.plate_number" placeholder="KA01AB1234 or 26BH1234AB" />
          </div>
          <div class="field">
            <label for="nick">Nickname</label>
            <input id="nick" v-model="form.nickname" />
          </div>
          <div class="field">
            <label for="colour">Colour</label>
            <input id="colour" v-model="form.colour" />
          </div>
          <div class="field">
            <label for="tower">Parking tower</label>
            <input id="tower" v-model="form.parking_tower" />
          </div>
          <div class="field">
            <label for="slot">Parking slot</label>
            <input id="slot" v-model="form.parking_slot" />
          </div>
        </div>
        <div v-if="saveMsg" class="alert alert-success">{{ saveMsg }}</div>
        <button class="btn" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save corrections' }}</button>
      </form>
    </div>
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
