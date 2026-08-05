<template>
  <a-config-provider :theme="opsTheme" :wave="{ disabled: false }">
    <a-app class="ops-app-root">
      <NuxtLayout>
        <NuxtPage />
      </NuxtLayout>
    </a-app>
  </a-config-provider>
</template>

<script setup lang="ts">
import { opsTheme } from '~/utils/theme'
</script>
