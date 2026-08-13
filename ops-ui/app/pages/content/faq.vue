<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">FAQ</a-typography-title>
        <a-typography-paragraph type="secondary" style="margin-bottom: 0">
          Publish FAQ for the consumer app (OPS-SUP-01).
        </a-typography-paragraph>
      </div>
      <a-button type="primary" @click="addRow">Add entry</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
    <a-alert v-if="message" type="success" show-icon :message="message" style="margin-bottom: 1rem" />

    <a-card v-for="(row, idx) in rows" :key="idx" size="small" style="margin-bottom: 0.75rem">
      <a-form layout="vertical">
        <a-row :gutter="12">
          <a-col :xs="24" :md="16">
            <a-form-item label="Question">
              <a-input v-model:value="row.question" />
            </a-form-item>
          </a-col>
          <a-col :xs="12" :md="4">
            <a-form-item label="Category">
              <a-input v-model:value="row.category" />
            </a-form-item>
          </a-col>
          <a-col :xs="12" :md="4">
            <a-form-item label="Order">
              <a-input-number v-model:value="row.display_order" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="Answer">
          <a-textarea v-model:value="row.answer" :rows="3" />
        </a-form-item>
        <a-button danger type="link" @click="rows.splice(idx, 1)">Remove</a-button>
      </a-form>
    </a-card>

    <a-button type="primary" :loading="saving" @click="save">Publish FAQ</a-button>
  </div>
</template>

<script setup lang="ts">
import type { FaqEntry } from '~/types/ops'

const { opsFetch } = useOpsApi()
const rows = ref<
  { question: string; answer: string; category: string; display_order: number; is_active: boolean }[]
>([])
const saving = ref(false)
const error = ref('')
const message = ref('')

function addRow() {
  rows.value.push({
    question: '',
    answer: '',
    category: 'general',
    display_order: rows.value.length,
    is_active: true,
  })
}

async function load() {
  error.value = ''
  try {
    const config = useRuntimeConfig()
    const root = String(config.public.apiBase).replace(/\/$/, '')
    const data = await $fetch<{ items: FaqEntry[] }>(`${root}/api/v1/content/faq`)
    if (data.items?.length) {
      rows.value = data.items.map((i) => ({
        question: i.question,
        answer: i.answer,
        category: i.category,
        display_order: i.display_order,
        is_active: true,
      }))
    } else if (!rows.value.length) {
      addRow()
    }
  } catch {
    if (!rows.value.length) addRow()
  }
}

async function save() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    const payload = {
      items: rows.value
        .filter((r) => r.question.trim() && r.answer.trim())
        .map((r, i) => ({
          question: r.question.trim(),
          answer: r.answer.trim(),
          category: r.category || 'general',
          display_order: r.display_order ?? i,
          is_active: true,
        })),
    }
    const res = await opsFetch<{ items: FaqEntry[] }>('/content/faq', {
      method: 'PUT',
      body: payload,
    })
    rows.value = res.items.map((i) => ({
      question: i.question,
      answer: i.answer,
      category: i.category,
      display_order: i.display_order,
      is_active: true,
    }))
    message.value = `Published ${res.items.length} FAQ entr${res.items.length === 1 ? 'y' : 'ies'}`
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Publish failed'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
