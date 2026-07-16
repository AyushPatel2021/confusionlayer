<script setup lang="ts">
defineProps<{ message: string }>();
defineEmits<{ (e: "retry"): void }>();
</script>

<template>
  <div class="rounded-md border border-danger/30 bg-danger-bg px-4 py-3 text-sm text-danger">
    <div class="flex items-start justify-between gap-3">
      <p class="leading-6">{{ message }}</p>
      <button
        v-if="$attrs.onRetry"
        class="s-focus shrink-0 rounded-sm border border-danger/40 px-2 py-1 text-xs font-semibold"
        @click="$emit('retry')"
      >
        Retry
      </button>
    </div>
  </div>
</template>
