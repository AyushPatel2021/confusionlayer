<script setup lang="ts">
defineProps<{ title: string; message?: string }>();
</script>

<template>
  <div class="rounded-lg border border-dashed border-hairline bg-surface px-6 py-12 text-center">
    <h3 class="text-lg font-semibold text-ink-900">{{ title }}</h3>
    <p v-if="message" class="mx-auto mt-2 max-w-reading text-sm leading-6 text-ink-500">{{ message }}</p>
    <div class="mt-4 flex justify-center"><slot name="action" /></div>
  </div>
</template>
