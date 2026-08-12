<template>
  <div>
    <a-page-header
      style="padding: 0 0 1rem"
      title="Payment"
      :sub-title="shortId(id)"
      @back="navigateTo('/payments')"
    />

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-spin :spinning="loading">
      <template v-if="payment">
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :md="14">
            <a-card title="Payment" size="small">
              <a-descriptions :column="1" size="small" bordered>
                <a-descriptions-item label="Status">
                  <a-tag>{{ payment.status }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="Amount">
                  {{ formatPaise(payment.amount_paise) }} {{ payment.currency }}
                </a-descriptions-item>
                <a-descriptions-item label="Kind">{{ payment.kind }}</a-descriptions-item>
                <a-descriptions-item label="Provider">{{ payment.provider }}</a-descriptions-item>
                <a-descriptions-item label="Provider ref">
                  {{ payment.provider_ref || '—' }}
                </a-descriptions-item>
                <a-descriptions-item label="Period">
                  <template v-if="payment.period_start">
                    {{ payment.period_start }} → {{ payment.period_end }}
                  </template>
                  <template v-else>—</template>
                </a-descriptions-item>
                <a-descriptions-item label="Captured">
                  {{ payment.captured_at ? formatDateTime(payment.captured_at) : '—' }}
                </a-descriptions-item>
                <a-descriptions-item label="Reconciled">
                  {{ payment.reconciled_at ? formatDateTime(payment.reconciled_at) : '—' }}
                </a-descriptions-item>
                <a-descriptions-item v-if="payment.failure_reason" label="Failure">
                  {{ payment.failure_reason }}
                </a-descriptions-item>
                <a-descriptions-item v-if="payment.notes" label="Notes">
                  <pre style="margin: 0; white-space: pre-wrap; font-family: inherit">{{ payment.notes }}</pre>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="10">
            <a-card title="User" size="small" style="margin-bottom: 1rem">
              <p v-if="payment.user">
                <code>{{ payment.user.phone }}</code>
              </p>
              <a-button type="link" style="padding-left: 0" @click="navigateTo(`/users/${payment.user_id}`)">
                Open user
              </a-button>
              <a-button
                v-if="payment.subscription_id"
                type="link"
                @click="navigateTo(`/subscriptions/${payment.subscription_id}`)"
              >
                Open subscription
              </a-button>
            </a-card>

            <a-card title="Reconcile" size="small">
              <a-typography-paragraph type="secondary" style="margin-bottom: 0.75rem">
                Mark as captured for bank / gateway exceptions (OPS-PAY-03).
              </a-typography-paragraph>
              <a-form layout="vertical">
                <a-form-item label="Provider ref">
                  <a-input v-model:value="providerRef" :disabled="!canReconcile" placeholder="UTR / order id" />
                </a-form-item>
                <a-form-item label="Notes">
                  <a-textarea v-model:value="notes" :rows="3" :disabled="!canReconcile" />
                </a-form-item>
                <a-button
                  type="primary"
                  :loading="reconciling"
                  :disabled="!canReconcile"
                  @click="onReconcile"
                >
                  Mark captured
                </a-button>
              </a-form>
              <a-alert
                v-if="payment.status === 'succeeded'"
                type="success"
                show-icon
                style="margin-top: 0.75rem"
                message="Already succeeded"
              />
            </a-card>
          </a-col>
        </a-row>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import type { OpsPayment } from '~/types/ops'
import { formatDateTime, formatPaise, shortId } from '~/utils/format'

const route = useRoute()
const { opsFetch } = useOpsApi()
const id = computed(() => String(route.params.id))

const payment = ref<OpsPayment | null>(null)
const loading = ref(true)
const error = ref('')
const providerRef = ref('')
const notes = ref('')
const reconciling = ref(false)

const canReconcile = computed(() => {
  const s = payment.value?.status
  return s === 'pending' || s === 'failed'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    payment.value = await opsFetch<OpsPayment>(`/payments/${id.value}`)
    providerRef.value = payment.value.provider_ref || ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load payment'
  } finally {
    loading.value = false
  }
}

async function onReconcile() {
  reconciling.value = true
  error.value = ''
  try {
    payment.value = await opsFetch<OpsPayment>(`/payments/${id.value}/reconcile`, {
      method: 'POST',
      body: {
        notes: notes.value || null,
        provider_ref: providerRef.value || null,
      },
    })
    notes.value = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Reconcile failed'
  } finally {
    reconciling.value = false
  }
}

onMounted(load)
watch(id, load)
</script>
