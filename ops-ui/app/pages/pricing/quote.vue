<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Quote preview</h1>
        <p>Same engine as consumer (OPS-PRICE-05).</p>
      </div>
      <NuxtLink class="btn btn-secondary" to="/pricing">Pricing</NuxtLink>
    </div>

    <form class="card stack" @submit.prevent="runQuote">
      <div class="grid-2">
        <div class="field">
          <label for="city">City ID</label>
          <input id="city" v-model="form.city_id" class="mono" required placeholder="UUID" />
        </div>
        <div class="field">
          <label for="tier">Size tier</label>
          <select id="tier" v-model="form.size_tier">
            <option value="small">small</option>
            <option value="medium">medium</option>
            <option value="large">large</option>
          </select>
        </div>
        <div class="field">
          <label for="freq">Interior frequency</label>
          <select id="freq" v-model.number="form.interior_frequency">
            <option :value="0">0</option>
            <option :value="1">1</option>
            <option :value="2">2</option>
            <option :value="4">4</option>
          </select>
        </div>
        <div class="field">
          <label for="start">Start date</label>
          <input id="start" v-model="form.start_date" type="date" />
        </div>
      </div>
      <button class="btn" type="submit" :disabled="loading">{{ loading ? '…' : 'Compute quote' }}</button>
    </form>

    <div v-if="error" class="alert alert-error" style="margin-top: 1rem">{{ error }}</div>

    <div v-if="quote" class="card stack" style="margin-top: 1rem">
      <h2 class="card-title">Result — {{ quote.city.name }}</h2>
      <dl class="dl">
        <dt>Full monthly</dt>
        <dd><strong>{{ formatPaise(quote.full_monthly_total_paise) }}</strong></dd>
        <dt>Due now</dt>
        <dd>{{ formatPaise(quote.amount_due_now_paise) }}</dd>
        <dt>Prorated</dt>
        <dd>{{ quote.is_prorated ? 'yes' : 'no' }}</dd>
        <dt>Billing month</dt>
        <dd>{{ quote.billing_month }} → next {{ quote.next_billing_month }}</dd>
        <dt>Period</dt>
        <dd>{{ quote.remaining_days }} / {{ quote.days_in_month }} days from {{ quote.start_date }}</dd>
        <dt>Plan</dt>
        <dd>{{ quote.size_tier }} · interior {{ quote.interior_frequency }}×</dd>
      </dl>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { QuoteOut, VehicleSizeTier } from '~/types/ops'
import { formatPaise } from '~/utils/format'

const { opsFetch } = useOpsApi()
const loading = ref(false)
const error = ref('')
const quote = ref<QuoteOut | null>(null)

const form = reactive({
  city_id: '',
  size_tier: 'medium' as VehicleSizeTier,
  interior_frequency: 2,
  start_date: new Date().toISOString().slice(0, 10),
})

async function runQuote() {
  loading.value = true
  error.value = ''
  quote.value = null
  try {
    quote.value = await opsFetch<QuoteOut>('/pricing/quote', {
      method: 'POST',
      body: {
        city_id: form.city_id.trim(),
        size_tier: form.size_tier,
        interior_frequency: form.interior_frequency,
        start_date: form.start_date || null,
      },
    })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Quote failed'
  } finally {
    loading.value = false
  }
}
</script>
