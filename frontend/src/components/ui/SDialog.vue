<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    description?: string;
    size?: "sm" | "md" | "lg" | "xl";
  }>(),
  { description: "", size: "md" },
);

const emit = defineEmits<{ close: [] }>();
const panel = ref<HTMLElement | null>(null);

const sizeClass = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    await nextTick();
    panel.value?.focus();
  },
);
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-[60] flex items-center justify-center bg-ink-900/45 p-4"
    role="dialog"
    aria-modal="true"
    :aria-label="title"
    @keydown.esc="$emit('close')"
  >
    <section
      ref="panel"
      tabindex="-1"
      class="s-focus w-full rounded-lg border border-hairline bg-surface p-6 shadow-raised"
      :class="sizeClass[size]"
    >
      <header class="flex items-start justify-between gap-4">
        <div>
          <h2 class="font-display text-xl font-semibold text-ink-900">{{ title }}</h2>
          <p v-if="description" class="mt-1 text-sm leading-6 text-ink-600">{{ description }}</p>
        </div>
        <button type="button" class="s-focus rounded-md px-2 py-1 text-sm font-semibold text-ink-600 hover:bg-primary-50" @click="$emit('close')">
          Close
        </button>
      </header>
      <div class="mt-5">
        <slot />
      </div>
      <footer v-if="$slots.footer" class="mt-6 flex justify-end gap-2">
        <slot name="footer" />
      </footer>
    </section>
  </div>
</template>
