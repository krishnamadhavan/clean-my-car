<template>
  <div>
    <a-space wrap style="margin-bottom: 1rem; width: 100%; justify-content: space-between">
      <div>
        <a-typography-title :level="3" style="margin: 0">Pricing</a-typography-title>
        <a-typography-paragraph type="secondary" style="margin-bottom: 0">
          City tariffs (OPS-PRICE-01–04, 06). Amounts stored in paise.
          Open a city to load/save pricing via the ops API.
        </a-typography-paragraph>
      </div>
      <a-button type="primary" ghost @click="navigateTo('/pricing/quote')">Quote preview</a-button>
    </a-space>

    <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 1rem" />

    <a-card v-if="missing.length" title="Missing active pricing" style="margin-bottom: 1rem">
      <a-list size="small" :data-source="missing">
        <template #renderItem="{ item }">
          <a-list-item>
            <a @click.prevent="navigateTo(`/pricing/${item.city.id}`)">{{ item.city.name }}</a>
            <a-tag v-if="item.has_inactive_pricing" color="warning">inactive config exists</a-tag>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <div class="ops-table-scroll">
      <a-table
        :columns="columns"
        :data-source="cities"
        row-key="id"
        :pagination="false"
        :scroll="{ x: 560 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'active'">
            <a-tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? 'yes' : 'no' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="navigateTo(`/pricing/${record.id}`)">
              Edit pricing
            </a-button>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { City, MissingPricing, Paginated } from '~/types/ops'

const { opsFetch } = useOpsApi()
const cities = ref<City[]>([])
const missing = ref<MissingPricing['items']>([])
const error = ref('')

const columns = [
  { title: 'City', dataIndex: 'name', key: 'name' },
  { title: 'State', dataIndex: 'state', key: 'state' },
  { title: 'Active city', key: 'active', width: 120 },
  { title: '', key: 'actions', width: 130 },
]

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
