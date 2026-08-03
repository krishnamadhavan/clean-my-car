<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Ops dashboard</h1>
        <p>Master data and support tools for Modules 1–6.</p>
      </div>
    </div>

    <div class="stat-grid" style="margin-bottom: 1.25rem">
      <div class="stat">
        <div class="label">Waitlist</div>
        <div class="value">{{ waitlistTotal ?? '—' }}</div>
      </div>
      <div class="stat">
        <div class="label">Pricing gaps</div>
        <div class="value">{{ missingPricing ?? '—' }}</div>
      </div>
      <div class="stat">
        <div class="label">Signed in</div>
        <div class="value" style="font-size: 1rem; word-break: break-word">
          {{ auth.operator.value?.email || '—' }}
        </div>
      </div>
    </div>

    <div v-if="loadError" class="alert alert-error" style="margin-bottom: 1rem">{{ loadError }}</div>

    <section class="cards" aria-label="Modules">
      <NuxtLink v-for="item in modules" :key="item.to" :to="item.to" class="card card-link">
        <h2>{{ item.title }}</h2>
        <p>{{ item.blurb }}</p>
        <span class="badge badge-ok">{{ item.badge }}</span>
      </NuxtLink>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { MissingPricing, WaitlistSummary } from '~/types/ops'

const auth = useAuth()
const { opsFetch } = useOpsApi()

const waitlistTotal = ref<number | null>(null)
const missingPricing = ref<number | null>(null)
const loadError = ref('')

const modules = [
  { to: '/users', title: 'Users', blurb: 'Search consumer accounts, deactivate / reactivate.', badge: 'Module 2' },
  { to: '/cities', title: 'Cities & societies', blurb: 'Location catalog and service weekdays.', badge: 'Module 3' },
  { to: '/waitlist', title: 'Waitlist', blurb: 'Triage demand and update status.', badge: 'Module 4' },
  { to: '/vehicles', title: 'Vehicle catalog', blurb: 'Makes, models, and size tiers.', badge: 'Module 5' },
  { to: '/pricing', title: 'Pricing', blurb: 'City tariffs, matrix, and quote preview.', badge: 'Module 6' },
  { to: '/pricing/quote', title: 'Quote preview', blurb: 'Run the same quote engine as consumer.', badge: 'Module 6' },
]

onMounted(async () => {
  try {
    const [summary, missing] = await Promise.all([
      opsFetch<WaitlistSummary>('/waitlist/summary'),
      opsFetch<MissingPricing>('/pricing/missing'),
    ])
    waitlistTotal.value = summary.total
    missingPricing.value = missing.total
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : 'Failed to load dashboard stats'
  }
})
</script>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr));
  gap: 0.85rem;
}

.card-link {
  color: inherit;
  text-decoration: none;
  transition: border-color 0.15s ease, transform 0.15s ease;
}

.card-link:hover {
  border-color: var(--accent);
  text-decoration: none;
  transform: translateY(-1px);
}

.card-link h2 {
  margin: 0 0 0.35rem;
  font-size: 1rem;
}

.card-link p {
  margin: 0 0 0.75rem;
  color: var(--muted);
  font-size: 0.9rem;
}
</style>
