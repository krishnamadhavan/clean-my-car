<template>
  <div>
    <a-page-header
      style="padding: 0 0 1rem"
      title="Subscription"
      :sub-title="shortId(id)"
      @back="navigateTo('/subscriptions')"
    />

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-spin :spinning="loading">
      <template v-if="sub">
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :md="14">
            <a-card title="Plan" size="small">
              <a-descriptions :column="1" size="small" bordered>
                <a-descriptions-item label="Status">
                  <a-tag>{{ sub.status }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="Size tier">{{ sub.size_tier }}</a-descriptions-item>
                <a-descriptions-item label="Interior">{{ sub.interior_frequency }}× / month</a-descriptions-item>
                <a-descriptions-item label="Monthly">
                  {{ formatPaise(sub.monthly_amount_paise) }} {{ sub.currency }}
                </a-descriptions-item>
                <a-descriptions-item label="Period">
                  {{ sub.period_start }} → {{ sub.period_end }}
                </a-descriptions-item>
                <a-descriptions-item v-if="sub.cancel_at" label="Cancel at">
                  {{ sub.cancel_at }}
                </a-descriptions-item>
                <a-descriptions-item label="Society">
                  {{ sub.society?.name || shortId(sub.society_id) }}
                </a-descriptions-item>
                <a-descriptions-item label="City">
                  {{ sub.city ? `${sub.city.name}, ${sub.city.state}` : shortId(sub.city_id) }}
                </a-descriptions-item>
                <a-descriptions-item v-if="sub.notes" label="Notes">
                  <pre style="margin: 0; white-space: pre-wrap; font-family: inherit">{{ sub.notes }}</pre>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="10">
            <a-card title="User" size="small" style="margin-bottom: 1rem">
              <p v-if="sub.user">
                <code>{{ sub.user.phone }}</code><br />
                {{ sub.user.name || '—' }}
              </p>
              <a-button type="link" style="padding-left: 0" @click="navigateTo(`/users/${sub.user_id}`)">
                Open user
              </a-button>
            </a-card>

            <a-card title="Admin cancel" size="small">
              <a-typography-paragraph type="secondary" style="margin-bottom: 0.75rem">
                Schedules cancel at period end (service continues until {{ sub.period_end }}). No refund.
              </a-typography-paragraph>
              <a-textarea
                v-model:value="cancelNotes"
                :rows="3"
                placeholder="Optional ops note"
                :disabled="!canCancel"
              />
              <a-button
                type="primary"
                danger
                style="margin-top: 0.75rem"
                :loading="cancelling"
                :disabled="!canCancel"
                @click="onCancel"
              >
                Schedule cancel
              </a-button>
              <a-alert
                v-if="sub.status === 'cancel_scheduled'"
                type="info"
                show-icon
                style="margin-top: 0.75rem"
                message="Cancel already scheduled"
              />
            </a-card>
          </a-col>
        </a-row>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import type { OpsSubscription } from '~/types/ops'
import { formatPaise, shortId } from '~/utils/format'

const route = useRoute()
const { opsFetch } = useOpsApi()
const id = computed(() => String(route.params.id))

const sub = ref<OpsSubscription | null>(null)
const loading = ref(true)
const error = ref('')
const cancelNotes = ref('')
const cancelling = ref(false)

const canCancel = computed(() => {
  const s = sub.value?.status
  return s === 'active' || s === 'pending_payment' || s === 'paused'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    sub.value = await opsFetch<OpsSubscription>(`/subscriptions/${id.value}`)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load subscription'
  } finally {
    loading.value = false
  }
}

async function onCancel() {
  cancelling.value = true
  error.value = ''
  try {
    sub.value = await opsFetch<OpsSubscription>(`/subscriptions/${id.value}/cancel`, {
      method: 'POST',
      body: { notes: cancelNotes.value || null },
    })
    cancelNotes.value = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Cancel failed'
  } finally {
    cancelling.value = false
  }
}

onMounted(load)
watch(id, load)
</script>
