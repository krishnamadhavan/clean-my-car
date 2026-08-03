<template>
  <div>
    <h1>Operator login</h1>
    <p class="muted">Sign in with your ops email and password (not consumer phone OTP).</p>

    <form class="stack" @submit.prevent="onSubmit">
      <div class="field">
        <label for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          autocomplete="username"
          required
          placeholder="admin@example.com"
        />
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          minlength="8"
        />
      </div>

      <div v-if="error" class="alert alert-error" role="alert">{{ error }}</div>

      <button class="btn" type="submit" :disabled="loading">
        {{ loading ? 'Signing in…' : 'Sign in' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const { login } = useOpsApi()
const route = useRoute()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  loading.value = true
  error.value = ''
  try {
    await login(email.value.trim(), password.value)
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    await navigateTo(next.startsWith('/') ? next : '/')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
