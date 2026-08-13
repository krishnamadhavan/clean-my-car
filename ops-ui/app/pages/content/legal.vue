<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Legal documents</a-typography-title>
    <a-typography-paragraph type="secondary">
      Publish terms / privacy / cancellation (OPS-SUP-02).
    </a-typography-paragraph>

    <a-form layout="vertical" style="max-width: 720px" @finish="save">
      <a-form-item label="Document type" required>
        <a-select v-model:value="form.doc_type">
          <a-select-option value="terms">terms</a-select-option>
          <a-select-option value="privacy">privacy</a-select-option>
          <a-select-option value="cancellation">cancellation</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="Version">
        <a-input v-model:value="form.version" />
      </a-form-item>
      <a-form-item label="Title" required>
        <a-input v-model:value="form.title" />
      </a-form-item>
      <a-form-item label="Body">
        <a-textarea v-model:value="form.body" :rows="10" />
      </a-form-item>
      <a-form-item label="External URL (optional)">
        <a-input v-model:value="form.url" placeholder="https://…" />
      </a-form-item>
      <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
      <a-alert v-if="message" type="success" show-icon :message="message" style="margin-bottom: 1rem" />
      <a-button type="primary" html-type="submit" :loading="saving">Publish</a-button>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import type { LegalDocType, LegalDocument } from '~/types/ops'

const { opsFetch } = useOpsApi()
const saving = ref(false)
const error = ref('')
const message = ref('')
const form = reactive({
  doc_type: 'terms' as LegalDocType,
  version: '1.0',
  title: 'Terms of Service',
  body: '',
  url: '',
})

watch(
  () => form.doc_type,
  (t) => {
    if (t === 'privacy') form.title = 'Privacy Policy'
    else if (t === 'cancellation') form.title = 'Cancellation Policy'
    else form.title = 'Terms of Service'
  },
)

async function save() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    const res = await opsFetch<LegalDocument>(`/content/legal/${form.doc_type}`, {
      method: 'PUT',
      body: {
        version: form.version,
        title: form.title,
        body: form.body || null,
        url: form.url || null,
        is_active: true,
      },
    })
    message.value = `Published ${res.doc_type} v${res.version}`
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Publish failed'
  } finally {
    saving.value = false
  }
}
</script>
