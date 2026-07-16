<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{ tone?: "neutral" | "primary" | "success" | "warning" | "danger" | "info" }>(),
  { tone: "neutral" },
);

const toneClass = computed(
  () =>
    ({
      neutral: "border-hairline bg-surface-sunken text-ink-700",
      primary: "border-primary-100 bg-primary-50 text-primary-600",
      success: "border-success/30 bg-success-bg text-success",
      warning: "border-warning/30 bg-warning-bg text-warning",
      danger: "border-danger/30 bg-danger-bg text-danger",
      info: "border-info/30 bg-info-bg text-info",
    })[props.tone],
);
</script>

<template>
  <span
    class="inline-flex h-6 shrink-0 items-center rounded-sm border px-2 text-xs font-semibold"
    :class="toneClass"
  >
    <slot />
  </span>
</template>
