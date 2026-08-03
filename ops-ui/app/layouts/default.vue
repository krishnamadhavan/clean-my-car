<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <span class="mark" aria-hidden="true" />
        <div>
          <strong>Clean My Car</strong>
          <span class="badge">Ops</span>
        </div>
      </div>
      <nav class="nav" aria-label="Primary">
        <NuxtLink to="/">Dashboard</NuxtLink>
      </nav>
    </header>
    <main class="main">
      <slot />
    </main>
    <footer class="footer">
      <span>Internal tools only · not the consumer app</span>
      <span class="api">API: {{ apiBase }}{{ opsApiPrefix }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const opsApiPrefix = config.public.opsApiPrefix
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
  justify-content: space-between;
  gap: 0.75rem 1rem;
  padding: 0.75rem var(--space-page-x);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-width: 0;
}

.brand strong {
  font-size: clamp(0.95rem, 2.5vw, 1.05rem);
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
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--accent);
  background: var(--accent-soft);
  white-space: nowrap;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1rem;
  font-size: 0.95rem;
}

.nav a {
  color: var(--muted);
  padding: 0.25rem 0;
}

.nav a.router-link-active {
  color: var(--text);
  font-weight: 600;
  text-decoration: none;
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
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  word-break: break-all;
}
</style>
