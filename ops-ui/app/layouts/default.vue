<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <NuxtLink to="/" class="brand-link">
          <span class="mark" aria-hidden="true" />
          <div>
            <strong>Clean My Car</strong>
            <span class="badge">Ops</span>
          </div>
        </NuxtLink>
      </div>

      <button
        type="button"
        class="btn btn-secondary btn-sm nav-toggle"
        aria-label="Toggle navigation"
        :aria-expanded="navOpen"
        @click="navOpen = !navOpen"
      >
        Menu
      </button>

      <nav class="nav" :class="{ open: navOpen }" aria-label="Primary">
        <NuxtLink to="/" @click="navOpen = false">Dashboard</NuxtLink>
        <NuxtLink to="/users" @click="navOpen = false">Users</NuxtLink>
        <NuxtLink to="/cities" @click="navOpen = false">Cities</NuxtLink>
        <NuxtLink to="/waitlist" @click="navOpen = false">Waitlist</NuxtLink>
        <NuxtLink to="/vehicles" @click="navOpen = false">Vehicles</NuxtLink>
        <NuxtLink to="/pricing" @click="navOpen = false">Pricing</NuxtLink>
      </nav>

      <div class="session">
        <span v-if="auth.operator.value" class="who muted" :title="auth.operator.value.email">
          {{ auth.operator.value.name || auth.operator.value.email }}
        </span>
        <button type="button" class="btn btn-secondary btn-sm" :disabled="loggingOut" @click="onLogout">
          {{ loggingOut ? '…' : 'Log out' }}
        </button>
      </div>
    </header>
    <main class="main">
      <slot />
    </main>
    <footer class="footer">
      <span>Internal tools only · not the consumer app</span>
      <span class="api mono">{{ apiBase }}{{ opsApiPrefix }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const auth = useAuth()
const { logout } = useOpsApi()
const apiBase = config.public.apiBase
const opsApiPrefix = config.public.opsApiPrefix
const navOpen = ref(false)
const loggingOut = ref(false)

async function onLogout() {
  loggingOut.value = true
  try {
    await logout()
    await navigateTo('/login')
  } finally {
    loggingOut.value = false
  }
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem 1rem;
  padding: 0.75rem var(--space-page-x);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: inherit;
  text-decoration: none;
  min-width: 0;
}

.brand-link:hover {
  text-decoration: none;
}

.mark {
  flex-shrink: 0;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.45rem;
  background: linear-gradient(135deg, var(--accent), #22d3ee);
}

.badge {
  margin-left: 0.4rem;
}

.nav-toggle {
  margin-left: auto;
}

.nav {
  display: none;
  flex-basis: 100%;
  flex-direction: column;
  gap: 0.15rem;
  font-size: 0.92rem;
}

.nav.open {
  display: flex;
}

.nav a {
  color: var(--muted);
  padding: 0.45rem 0.35rem;
  border-radius: var(--radius-sm);
}

.nav a:hover {
  color: var(--text);
  background: var(--accent-soft);
  text-decoration: none;
}

.nav a.router-link-active {
  color: var(--text);
  font-weight: 600;
  background: var(--accent-soft);
}

.session {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  justify-content: space-between;
}

.who {
  font-size: 0.85rem;
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-page-y) var(--space-page-x) calc(var(--space-page-y) * 1.5);
}

.footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem 1rem;
  padding: 0.75rem var(--space-page-x);
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.8rem;
}

.api {
  word-break: break-all;
}

@media (min-width: 900px) {
  .nav-toggle {
    display: none;
  }

  .nav {
    display: flex;
    flex-basis: auto;
    flex-direction: row;
    flex: 1;
    align-items: center;
    gap: 0.15rem 0.35rem;
    flex-wrap: wrap;
  }

  .nav a {
    padding: 0.35rem 0.55rem;
  }

  .session {
    width: auto;
    margin-left: auto;
  }
}
</style>
