<script setup lang="ts">
defineProps<{ label: string; value: string | number; tone?: "default" | "success" | "warning" | "danger" }>();

const toneClass = {
  default: "text-ink-900",
  success: "text-success",
  warning: "text-accent-600",
  danger: "text-danger",
};
</script>

<template>
  <article class="rounded-md border border-hairline bg-surface p-4">
    <p class="text-xs font-medium text-ink-500">{{ label }}</p>
    <p class="mt-1 font-display text-2xl font-semibold" :class="toneClass[tone || 'default']">{{ value }}</p>
    <p v-if="$slots.default" class="mt-1 text-xs text-ink-500"><slot /></p>
  </article>
</template>
