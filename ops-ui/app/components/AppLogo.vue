<template>
  <img
    :src="src"
    alt="Clean My Car"
    class="app-logo"
    :class="{
      'app-logo--sm': size === 'sm',
      'app-logo--md': size === 'md',
      'app-logo--lg': size === 'lg',
    }"
    width="40"
    height="40"
    decoding="async"
  />
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    /** mark = compact tile; full = primary app icon */
    variant?: 'mark' | 'full'
    size?: 'sm' | 'md' | 'lg'
  }>(),
  { variant: 'mark', size: 'md' },
)

// Prefer crisp SVG for UI; PNG assets also in public/
const src = computed(() => (props.variant === 'full' ? '/logo.svg' : '/logo-mark.svg'))
</script>

<style scoped>
.app-logo {
  display: block;
  flex-shrink: 0;
  object-fit: contain;
  border-radius: 0.45rem;
}

.app-logo--sm {
  width: 1.5rem;
  height: 1.5rem;
}

.app-logo--md {
  width: 2rem;
  height: 2rem;
}

.app-logo--lg {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.65rem;
}
</style>
