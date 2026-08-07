<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">Quote preview</a-typography-title>
        <a-typography-paragraph type="secondary" style="margin-bottom: 0">
          Same engine as consumer (OPS-PRICE-05).
        </a-typography-paragraph>
      </div>
      <a-button @click="navigateTo('/pricing')">Pricing</a-button>
    </a-space>

    <a-card style="margin-bottom: 1rem">
      <a-form layout="vertical" :model="form" @finish="runQuote">
        <a-row :gutter="16">
          <a-col :xs="24" :md="12">
            <a-form-item
              label="City ID"
              name="city_id"
              :rules="[{ required: true, message: 'City ID is required' }]"
            >
              <a-input v-model:value="form.city_id" placeholder="UUID" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="6">
            <a-form-item label="Size tier" name="size_tier">
              <a-select v-model:value="form.size_tier">
                <a-select-option value="small">small</a-select-option>
                <a-select-option value="medium">medium</a-select-option>
                <a-select-option value="large">large</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="6">
            <a-form-item label="Interior frequency" name="interior_frequency">
              <a-select v-model:value="form.interior_frequency">
                <a-select-option :value="0">0</a-select-option>
                <a-select-option :value="1">1</a-select-option>
                <a-select-option :value="2">2</a-select-option>
                <a-select-option :value="4">4</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-form-item label="Start date">
              <a-date-picker v-model:value="startDate" style="width: 100%" value-format="YYYY-MM-DD" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-button type="primary" html-type="submit" :loading="loading">Compute quote</a-button>
      </a-form>
    </a-card>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <a-card v-if="quote" :title="`Result — ${quote.city.name}`">
      <a-descriptions :column="{ xs: 1, sm: 2 }" bordered size="small">
        <a-descriptions-item label="Full monthly">
          <strong>{{ formatPaise(quote.full_monthly_total_paise) }}</strong>
        </a-descriptions-item>
        <a-descriptions-item label="Due now">
          {{ formatPaise(quote.amount_due_now_paise) }}
        </a-descriptions-item>
        <a-descriptions-item label="Prorated">{{ quote.is_prorated ? 'yes' : 'no' }}</a-descriptions-item>
        <a-descriptions-item label="Billing month">
          {{ quote.billing_month }} → next {{ quote.next_billing_month }}
        </a-descriptions-item>
        <a-descriptions-item label="Period">
          {{ quote.remaining_days }} / {{ quote.days_in_month }} days from {{ quote.start_date }}
        </a-descriptions-item>
        <a-descriptions-item label="Plan">
          {{ quote.size_tier }} · interior {{ quote.interior_frequency }}×
        </a-descriptions-item>
      </a-descriptions>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import type { QuoteOut, VehicleSizeTier } from '~/types/ops'
import { formatPaise } from '~/utils/format'

const { opsFetch } = useOpsApi()
const loading = ref(false)
const error = ref('')
const quote = ref<QuoteOut | null>(null)
const startDate = ref<Dayjs | string>(dayjs())

const form = reactive({
  city_id: '',
  size_tier: 'medium' as VehicleSizeTier,
  interior_frequency: 2,
})

async function runQuote() {
  loading.value = true
  error.value = ''
  quote.value = null
  const start =
    typeof startDate.value === 'string'
      ? startDate.value
      : startDate.value
        ? dayjs(startDate.value).format('YYYY-MM-DD')
        : null
  try {
    quote.value = await opsFetch<QuoteOut>('/pricing/quote', {
      method: 'POST',
      body: {
        city_id: form.city_id.trim(),
        size_tier: form.size_tier,
        interior_frequency: form.interior_frequency,
        start_date: start,
      },
    })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Quote failed'
  } finally {
    loading.value = false
  }
}
</script>
