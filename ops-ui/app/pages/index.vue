<template>
  <div>
    <h1>Ops dashboard</h1>
    <p class="lede">
      Scaffold for the internal portal. Application screens (login, catalogs, waitlist, pricing)
      will land here against
      <code>/api/v1/ops/*</code>.
    </p>

    <section class="cards" aria-label="Planned modules">
      <article v-for="item in modules" :key="item.id" class="card">
        <h2>{{ item.title }}</h2>
        <p>{{ item.blurb }}</p>
        <span class="status">{{ item.status }}</span>
      </article>
    </section>

    <section class="note">
      <h2>Local development</h2>
      <ol>
        <li>Start the API stack from the monorepo root: <code>make up</code></li>
        <li>In this app: <code>npm install && npm run dev</code> (or <code>make ops-ui-dev</code>)</li>
        <li>Open <a href="http://localhost:3000">http://localhost:3000</a></li>
      </ol>
      <p>
        Swagger for ops APIs:
        <a :href="opsDocsUrl" target="_blank" rel="noopener">{{ opsDocsUrl }}</a>
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const opsDocsUrl = computed(() => `${config.public.apiBase}/ops/docs`)

const modules = [
  { id: 'auth', title: 'Auth', blurb: 'Operator email/password login (ops JWT).', status: 'API ready' },
  { id: 'location', title: 'Location', blurb: 'Cities and societies master data.', status: 'API ready' },
  { id: 'waitlist', title: 'Waitlist', blurb: 'Demand triage and status workflow.', status: 'API ready' },
  { id: 'vehicle', title: 'Vehicle catalog', blurb: 'Makes, models, size tiers.', status: 'API ready' },
  { id: 'pricing', title: 'Pricing', blurb: 'City tariffs and quote preview.', status: 'API ready' },
  { id: 'users', title: 'Users', blurb: 'Consumer account support tools.', status: 'API ready' },
]
</script>

<style scoped>
h1 {
  margin: 0 0 0.5rem;
  font-size: clamp(1.35rem, 4vw, 1.75rem);
  letter-spacing: -0.02em;
}

.lede {
  margin: 0 0 clamp(1.25rem, 4vw, 2rem);
  max-width: 40rem;
  color: var(--muted);
}

.lede code {
  color: var(--text);
  font-size: 0.9em;
  word-break: break-word;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr));
  gap: 0.85rem;
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.card {
  min-width: 0;
  padding: 1rem 1.1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
}

.card h2 {
  margin: 0 0 0.35rem;
  font-size: 1rem;
}

.card p {
  margin: 0 0 0.75rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.status {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #34d399;
}

.note {
  padding: clamp(1rem, 3vw, 1.25rem);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
}

.note h2 {
  margin: 0 0 0.75rem;
  font-size: 1rem;
}

.note ol {
  margin: 0 0 1rem;
  padding-left: 1.25rem;
  color: var(--muted);
}

.note li {
  margin-bottom: 0.35rem;
  overflow-wrap: anywhere;
}

.note code {
  color: var(--text);
  font-size: 0.88em;
  word-break: break-word;
}

.note p {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
  overflow-wrap: anywhere;
}
</style>
