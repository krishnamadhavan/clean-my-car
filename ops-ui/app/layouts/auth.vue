<template>
  <div class="auth-shell">
    <div class="panel">
      <div class="brand">
        <span class="mark" aria-hidden="true" />
        <div>
          <strong>Clean My Car</strong>
          <span class="badge">Ops</span>
        </div>
      </div>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.auth-shell {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-page-y) var(--space-page-x);
  background:
    radial-gradient(ellipse at top, rgba(59, 130, 246, 0.12), transparent 55%),
    var(--bg);
}

.panel {
  width: 100%;
  max-width: 24rem;
  padding: clamp(1.25rem, 4vw, 1.75rem);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 1.25rem;
}

.mark {
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
}
</style>
