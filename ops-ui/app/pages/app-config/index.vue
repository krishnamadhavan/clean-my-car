<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">App config</a-typography-title>
    <a-typography-paragraph type="secondary">
      Remote config for the iOS client (OPS-APP-01/02).
    </a-typography-paragraph>

    <a-spin :spinning="loading">
      <a-form layout="vertical" style="max-width: 560px" @finish="save">
        <a-form-item label="Min iOS version">
          <a-input v-model:value="form.min_ios_version" />
        </a-form-item>
        <a-form-item label="Force update">
          <a-switch v-model:checked="form.force_update" />
        </a-form-item>
        <a-form-item label="Support WhatsApp">
          <a-input v-model:value="form.support_whatsapp" placeholder="+91…" />
        </a-form-item>
        <a-form-item label="WhatsApp URL">
          <a-input v-model:value="form.support_whatsapp_url" placeholder="https://wa.me/…" />
        </a-form-item>
        <a-form-item label="Support email">
          <a-input v-model:value="form.support_email" />
        </a-form-item>
        <a-form-item label="Support phone">
          <a-input v-model:value="form.support_phone" />
        </a-form-item>
        <a-form-item label="Feature flags (JSON)">
          <a-textarea v-model:value="flagsJson" :rows="4" />
        </a-form-item>
        <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />
        <a-alert v-if="message" type="success" show-icon :message="message" style="margin-bottom: 1rem" />
        <a-button type="primary" html-type="submit" :loading="saving">Save</a-button>
      </a-form>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import type { AppConfig } from '~/types/ops'

const { opsFetch } = useOpsApi()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')
const flagsJson = ref('{}')
const form = reactive({
  min_ios_version: '17.0',
  force_update: false,
  support_whatsapp: '',
  support_whatsapp_url: '',
  support_email: '',
  support_phone: '',
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const cfg = await opsFetch<AppConfig>('/app/config')
    form.min_ios_version = cfg.min_ios_version
    form.force_update = cfg.force_update
    form.support_whatsapp = cfg.support_whatsapp || ''
    form.support_whatsapp_url = cfg.support_whatsapp_url || ''
    form.support_email = cfg.support_email || ''
    form.support_phone = cfg.support_phone || ''
    flagsJson.value = JSON.stringify(cfg.feature_flags || {}, null, 2)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load config'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    let feature_flags: Record<string, unknown> = {}
    try {
      feature_flags = JSON.parse(flagsJson.value || '{}')
    } catch {
      error.value = 'Feature flags must be valid JSON'
      return
    }
    await opsFetch<AppConfig>('/app/config', {
      method: 'PUT',
      body: {
        min_ios_version: form.min_ios_version,
        force_update: form.force_update,
        feature_flags,
        support_whatsapp: form.support_whatsapp || null,
        support_whatsapp_url: form.support_whatsapp_url || null,
        support_email: form.support_email || null,
        support_phone: form.support_phone || null,
      },
    })
    message.value = 'Saved'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
