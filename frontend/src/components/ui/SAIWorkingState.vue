<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string;
    message?: string;
    detail?: string;
  }>(),
  {
    title: "AI is working",
    message: "Building the response now.",
    detail: "This can take a little time while the model reads the context and returns a structured answer.",
  },
);
</script>

<template>
  <div class="rounded-lg border border-primary-600/20 bg-primary-50/70 p-4" role="status" aria-live="polite">
    <div class="flex items-start gap-3">
      <span class="mt-1 inline-flex size-5 shrink-0 animate-spin rounded-full border-2 border-primary-600/25 border-t-primary-600" aria-hidden="true" />
      <div>
        <p class="text-sm font-semibold text-ink-900">{{ title }}</p>
        <p class="mt-1 text-sm leading-6 text-ink-700">{{ message }}</p>
        <p class="mt-1 text-xs leading-5 text-ink-500">{{ detail }}</p>
      </div>
    </div>
  </div>
</template>
