<template>
  <div>
    <a-typography-title :level="3" style="margin-top: 0">Operator login</a-typography-title>
    <a-typography-paragraph type="secondary">
      Sign in with your ops email and password (not consumer phone OTP).
    </a-typography-paragraph>

    <a-form layout="vertical" :model="form" @finish="onSubmit">
      <a-form-item
        label="Email"
        name="email"
        :rules="[{ required: true, type: 'email', message: 'Enter a valid email' }]"
      >
        <a-input
          v-model:value="form.email"
          size="large"
          autocomplete="username"
          placeholder="admin@example.com"
        />
      </a-form-item>
      <a-form-item
        label="Password"
        name="password"
        :rules="[{ required: true, min: 8, message: 'Min 8 characters' }]"
      >
        <a-input-password
          v-model:value="form.password"
          size="large"
          autocomplete="current-password"
        />
      </a-form-item>

      <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

      <a-button type="primary" html-type="submit" size="large" block :loading="loading">
        Sign in
      </a-button>
    </a-form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const { login } = useOpsApi()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  loading.value = true
  error.value = ''
  try {
    await login(form.email.trim(), form.password)
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    await navigateTo(next.startsWith('/') ? next : '/')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
