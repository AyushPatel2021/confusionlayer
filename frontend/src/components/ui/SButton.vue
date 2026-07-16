<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "ghost" | "danger";
    type?: "button" | "submit";
    disabled?: boolean;
    block?: boolean;
  }>(),
  { variant: "primary", type: "button", disabled: false, block: false },
);

const variantClass = computed(
  () =>
    ({
      primary: "border-primary-600 bg-primary-600 text-white hover:bg-primary-500",
      secondary: "border-hairline bg-surface text-ink-900 hover:border-ink-500",
      ghost: "border-transparent bg-transparent text-ink-700 hover:bg-primary-50",
      danger: "border-danger bg-danger text-white hover:opacity-90",
    })[props.variant],
);
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    class="s-focus inline-flex min-h-10 items-center justify-center gap-2 rounded-md border px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55"
    :class="[variantClass, block && 'w-full']"
  >
    <slot />
  </button>
</template>
