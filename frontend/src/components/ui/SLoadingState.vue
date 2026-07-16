<script setup lang="ts">
withDefaults(defineProps<{ rows?: number; label?: string }>(), { rows: 3 });
</script>

<template>
  <div class="space-y-3" role="status" :aria-label="label || 'Loading'">
    <div
      v-for="n in rows"
      :key="n"
      class="h-20 w-full animate-pulse rounded-md border border-hairline bg-surface-sunken"
    />
  </div>
</template>
