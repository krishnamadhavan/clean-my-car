<template>
  <div class="auth-shell">
    <a-card class="auth-card" :bordered="true">
      <div class="auth-brand">
        <span class="ops-brand-mark" aria-hidden="true" />
        <div>
          <strong>Clean My Car</strong>
          <a-tag color="purple" style="margin-left: 0.5rem">Ops</a-tag>
        </div>
      </div>
      <slot />
    </a-card>
  </div>
</template>

<style scoped>
.auth-shell {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(1rem, 4vw, 2rem);
  background:
    radial-gradient(ellipse at top, rgba(152, 189, 255, 0.45), transparent 55%),
    linear-gradient(160deg, #eef0ff 0%, #f5f7fb 45%, #fff5f6 100%);
}

.auth-card {
  width: 100%;
  max-width: 24rem;
  box-shadow: 0 8px 28px rgba(75, 73, 172, 0.12);
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 1.25rem;
  color: #4b49ac;
}
</style>
