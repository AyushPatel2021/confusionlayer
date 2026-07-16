<script setup lang="ts">
defineProps<{ eyebrow?: string; title: string; subtitle?: string }>();
</script>

<template>
  <div class="flex flex-wrap items-start justify-between gap-4">
    <div>
      <p v-if="eyebrow" class="s-eyebrow">{{ eyebrow }}</p>
      <h1 class="mt-1 text-2xl font-semibold text-ink-900 md:text-3xl">{{ title }}</h1>
      <p v-if="subtitle" class="mt-2 max-w-reading text-sm leading-6 text-ink-500">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
