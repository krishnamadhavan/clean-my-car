<template>
  <div>
    <div class="page-header">
      <div>
        <h1>City pricing</h1>
        <p class="mono muted">{{ cityId }}</p>
      </div>
      <NuxtLink class="btn btn-secondary" to="/pricing">All cities</NuxtLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="msg" class="alert alert-success">{{ msg }}</div>

    <form class="card stack" style="margin-bottom: 1rem" @submit.prevent="saveConfig">
      <h2 class="card-title">Config (OPS-PRICE-02)</h2>
      <div class="grid-2">
        <div class="field">
          <label for="currency">Currency</label>
          <input id="currency" v-model="config.currency" maxlength="3" />
        </div>
        <div class="field">
          <label for="gst">GST rate (bps, 1800 = 18%)</label>
          <input id="gst" v-model.number="config.gst_rate_bps" type="number" min="0" max="10000" />
        </div>
      </div>
      <div class="checkbox-row">
        <label><input v-model="config.amounts_include_gst" type="checkbox" /> Amounts include GST</label>
        <label><input v-model="config.is_active" type="checkbox" /> Active</label>
      </div>
      <button class="btn" type="submit" :disabled="saving">Save config</button>
    </form>

    <form class="card stack" style="margin-bottom: 1rem" @submit.prevent="saveSizes">
      <h2 class="card-title">Size prices — ₹ / month (OPS-PRICE-03)</h2>
      <div class="grid-2">
        <div v-for="tier in tiers" :key="tier" class="field">
          <label :for="`size-${tier}`">{{ tier }}</label>
          <input :id="`size-${tier}`" v-model="sizeRupees[tier]" type="number" min="0" step="0.01" />
        </div>
      </div>
      <button class="btn" type="submit" :disabled="saving">Replace size prices</button>
    </form>

    <form class="card stack" style="margin-bottom: 1rem" @submit.prevent="saveInteriors">
      <h2 class="card-title">Interior add-ons — ₹ / month (OPS-PRICE-04)</h2>
      <div class="grid-2">
        <div v-for="freq in freqs" :key="freq" class="field">
          <label :for="`int-${freq}`">{{ freq }}× / month</label>
          <input :id="`int-${freq}`" v-model="interiorRupees[freq]" type="number" min="0" step="0.01" />
        </div>
      </div>
      <button class="btn" type="submit" :disabled="saving">Replace interior prices</button>
    </form>

    <div v-if="pricing?.matrix?.length" class="card">
      <h2 class="card-title">Matrix</h2>
      <div class="scroll-x">
        <table class="table">
          <thead>
            <tr>
              <th>Size</th>
              <th>Interior</th>
              <th>Base</th>
              <th>Interior</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(cell, i) in pricing.matrix" :key="i">
              <td>{{ cell.size_tier }}</td>
              <td>{{ cell.interior_frequency }}×</td>
              <td>{{ formatPaise(cell.base_amount_paise) }}</td>
              <td>{{ formatPaise(cell.interior_amount_paise) }}</td>
              <td><strong>{{ formatPaise(cell.monthly_total_paise) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CityPricing, VehicleSizeTier } from '~/types/ops'
import { formatPaise, paiseFromRupeesInput, rupeesFromPaise } from '~/utils/format'

const route = useRoute()
const cityId = computed(() => String(route.params.cityId))
const { opsFetch } = useOpsApi()

const tiers: VehicleSizeTier[] = ['small', 'medium', 'large']
const freqs = [0, 1, 2, 4] as const

const pricing = ref<CityPricing | null>(null)
const error = ref('')
const msg = ref('')
const saving = ref(false)

const config = reactive({
  currency: 'INR',
  amounts_include_gst: true,
  gst_rate_bps: 1800,
  is_active: true,
})

const sizeRupees = reactive<Record<VehicleSizeTier, string>>({
  small: '999',
  medium: '1299',
  large: '1599',
})

const interiorRupees = reactive<Record<number, string>>({
  0: '0',
  1: '199',
  2: '349',
  4: '599',
})

function applyPricing(p: CityPricing) {
  pricing.value = p
  config.currency = p.currency
  config.amounts_include_gst = p.amounts_include_gst
  config.gst_rate_bps = p.gst_rate_bps
  config.is_active = p.is_active
  for (const tier of tiers) {
    const row = p.size_prices.find((s) => s.size_tier === tier)
    if (row) sizeRupees[tier] = rupeesFromPaise(row.monthly_amount_paise)
  }
  for (const freq of freqs) {
    const row = p.interior_prices.find((i) => i.interior_frequency === freq)
    if (row) interiorRupees[freq] = rupeesFromPaise(row.monthly_amount_paise)
  }
}

async function load() {
  error.value = ''
  try {
    const p = await opsFetch<CityPricing>(`/cities/${cityId.value}/pricing`)
    applyPricing(p)
  } catch (e: unknown) {
    // 404 = not configured yet — form still usable for create
    if (e instanceof Error && e.message.toLowerCase().includes('not')) {
      pricing.value = null
      return
    }
    // OpsApiError code
    const code = (e as { code?: string }).code
    if (code === 'pricing_not_found') {
      pricing.value = null
      return
    }
    error.value = e instanceof Error ? e.message : 'Failed to load pricing'
  }
}

async function putConfig(): Promise<CityPricing> {
  const p = await opsFetch<CityPricing>(`/cities/${cityId.value}/pricing`, {
    method: 'PUT',
    body: { ...config },
  })
  applyPricing(p)
  return p
}

async function saveConfig() {
  saving.value = true
  error.value = ''
  msg.value = ''
  try {
    await putConfig()
    msg.value = 'Config saved.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

async function saveSizes() {
  saving.value = true
  error.value = ''
  msg.value = ''
  try {
    if (!pricing.value) await putConfig()
    const p = await opsFetch<CityPricing>(`/cities/${cityId.value}/pricing/size-prices`, {
      method: 'PUT',
      body: {
        items: tiers.map((size_tier) => ({
          size_tier,
          monthly_amount_paise: paiseFromRupeesInput(sizeRupees[size_tier]),
        })),
      },
    })
    applyPricing(p)
    msg.value = 'Size prices replaced.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

async function saveInteriors() {
  saving.value = true
  error.value = ''
  msg.value = ''
  try {
    if (!pricing.value) await putConfig()
    const p = await opsFetch<CityPricing>(`/cities/${cityId.value}/pricing/interior-prices`, {
      method: 'PUT',
      body: {
        items: freqs.map((interior_frequency) => ({
          interior_frequency,
          monthly_amount_paise: paiseFromRupeesInput(interiorRupees[interior_frequency]),
        })),
      },
    })
    applyPricing(p)
    msg.value = 'Interior prices replaced.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
