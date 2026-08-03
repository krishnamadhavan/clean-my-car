<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Pricing</h1>
        <p>City tariffs (OPS-PRICE-01–04, 06). Amounts stored in paise.</p>
      </div>
      <NuxtLink class="btn btn-secondary" to="/pricing/quote">Quote preview</NuxtLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <section v-if="missing.length" class="card" style="margin-bottom: 1.25rem">
      <h2 class="card-title">Missing active pricing ({{ missing.length }})</h2>
      <ul class="muted" style="margin: 0; padding-left: 1.2rem">
        <li v-for="row in missing" :key="row.city.id" style="margin-bottom: 0.35rem">
          <NuxtLink :to="`/pricing/${row.city.id}`">{{ row.city.name }}</NuxtLink>
          <span v-if="row.has_inactive_pricing"> · inactive config exists</span>
        </li>
      </ul>
    </section>

    <div class="scroll-x card" style="padding: 0">
      <table class="table">
        <thead>
          <tr>
            <th>City</th>
            <th>State</th>
            <th>Active city</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in cities" :key="c.id">
            <td>{{ c.name }}</td>
            <td>{{ c.state }}</td>
            <td>
              <span :class="c.is_active ? 'badge badge-ok' : 'badge badge-off'">
                {{ c.is_active ? 'yes' : 'no' }}
              </span>
            </td>
            <td class="actions">
              <NuxtLink class="btn btn-secondary btn-sm" :to="`/pricing/${c.id}`">Edit pricing</NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { City, MissingPricing, Paginated } from '~/types/ops'

const { opsFetch } = useOpsApi()
const cities = ref<City[]>([])
const missing = ref<MissingPricing['items']>([])
const error = ref('')

onMounted(async () => {
  try {
    const [cityData, miss] = await Promise.all([
      opsFetch<Paginated<City>>('/cities', { query: { include_inactive: true, page_size: 100 } }),
      opsFetch<MissingPricing>('/pricing/missing'),
    ])
    cities.value = cityData.items
    missing.value = miss.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load pricing index'
  }
})
</script>
