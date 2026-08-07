<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">City pricing</a-typography-title>
        <a-typography-text type="secondary" code>{{ cityId }}</a-typography-text>
      </div>
      <a-button @click="navigateTo('/pricing')">All cities</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-alert v-if="msg" type="success" show-icon :message="msg" style="margin-bottom: 1rem" />
    <a-alert
      v-if="!loading && !pricing && !error"
      type="info"
      show-icon
      message="No pricing configured for this city yet"
      description="Defaults below are placeholders. Click Save config to create the city pricing row, then set size and interior prices."
      style="margin-bottom: 1rem"
    />
    <a-spin :spinning="loading">
      <a-card title="Config (OPS-PRICE-02)" style="margin-bottom: 1rem">
        <a-form layout="vertical" :model="config" @finish="saveConfig">
          <a-row :gutter="16">
            <a-col :xs="24" :md="8">
              <a-form-item label="Currency" name="currency">
                <a-input v-model:value="config.currency" :maxlength="3" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="GST rate (bps, 1800 = 18%)" name="gst_rate_bps">
                <a-input-number
                  v-model:value="config.gst_rate_bps"
                  :min="0"
                  :max="10000"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="Flags">
                <a-space direction="vertical">
                  <a-checkbox v-model:checked="config.amounts_include_gst">
                    Amounts include GST
                  </a-checkbox>
                  <a-checkbox v-model:checked="config.is_active">Active</a-checkbox>
                </a-space>
              </a-form-item>
            </a-col>
          </a-row>
          <a-button type="primary" html-type="submit" :loading="saving">Save config</a-button>
        </a-form>
      </a-card>

      <a-card title="Size prices — ₹ / month (OPS-PRICE-03)" style="margin-bottom: 1rem">
        <a-form layout="vertical" :model="sizeRupees" @finish="saveSizes">
          <a-row :gutter="16">
            <a-col v-for="tier in tiers" :key="tier" :xs="24" :sm="8">
              <a-form-item :label="tier" :name="tier">
                <a-input-number
                  v-model:value="sizeRupees[tier]"
                  :min="0"
                  :step="0.01"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-button type="primary" html-type="submit" :loading="saving">
            Replace size prices
          </a-button>
        </a-form>
      </a-card>

      <a-card title="Interior add-ons — ₹ / month (OPS-PRICE-04)" style="margin-bottom: 1rem">
        <a-form layout="vertical" :model="interiorRupees" @finish="saveInteriors">
          <a-row :gutter="16">
            <a-col v-for="freq in freqs" :key="freq" :xs="12" :sm="6">
              <a-form-item :label="`${freq}× / month`" :name="String(freq)">
                <a-input-number
                  v-model:value="interiorRupees[freq]"
                  :min="0"
                  :step="0.01"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-button type="primary" html-type="submit" :loading="saving">
            Replace interior prices
          </a-button>
        </a-form>
      </a-card>

      <a-card v-if="pricing?.matrix?.length" title="Matrix">
        <div class="ops-table-scroll">
          <a-table
            :columns="matrixColumns"
            :data-source="pricing.matrix"
            :pagination="false"
            size="small"
            :scroll="{ x: 560 }"
            :row-key="(r) => `${r.size_tier}-${r.interior_frequency}`"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'base'">
                {{ formatPaise(record.base_amount_paise) }}
              </template>
              <template v-else-if="column.key === 'interior'">
                {{ formatPaise(record.interior_amount_paise) }}
              </template>
              <template v-else-if="column.key === 'total'">
                <strong>{{ formatPaise(record.monthly_total_paise) }}</strong>
              </template>
              <template v-else-if="column.key === 'freq'">{{ record.interior_frequency }}×</template>
            </template>
          </a-table>
        </div>
      </a-card>
    </a-spin>
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
const loading = ref(true)

const config = reactive({
  currency: 'INR',
  amounts_include_gst: true,
  gst_rate_bps: 1800,
  is_active: true,
})

const sizeRupees = reactive<Record<VehicleSizeTier, number>>({
  small: 999,
  medium: 1299,
  large: 1599,
})

const interiorRupees = reactive<Record<number, number>>({
  0: 0,
  1: 199,
  2: 349,
  4: 599,
})

const matrixColumns = [
  { title: 'Size', dataIndex: 'size_tier', key: 'size' },
  { title: 'Interior', key: 'freq' },
  { title: 'Base', key: 'base' },
  { title: 'Interior ₹', key: 'interior' },
  { title: 'Total', key: 'total' },
]

function applyPricing(p: CityPricing) {
  pricing.value = p
  config.currency = p.currency
  config.amounts_include_gst = p.amounts_include_gst
  config.gst_rate_bps = p.gst_rate_bps
  config.is_active = p.is_active
  for (const tier of tiers) {
    const row = p.size_prices.find((s) => s.size_tier === tier)
    if (row) sizeRupees[tier] = Number(rupeesFromPaise(row.monthly_amount_paise))
  }
  for (const freq of freqs) {
    const row = p.interior_prices.find((i) => i.interior_frequency === freq)
    if (row) interiorRupees[freq] = Number(rupeesFromPaise(row.monthly_amount_paise))
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const p = await opsFetch<CityPricing>(`/cities/${cityId.value}/pricing`)
    applyPricing(p)
  } catch (e: unknown) {
    const code = (e as { code?: string }).code
    if (code === 'pricing_not_found') {
      pricing.value = null
      return
    }
    error.value = e instanceof Error ? e.message : 'Failed to load pricing'
  } finally {
    loading.value = false
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
watch(cityId, load)
</script>
