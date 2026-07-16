<script setup lang="ts">
withDefaults(defineProps<{ padded?: boolean; raised?: boolean }>(), { padded: true, raised: false });
</script>

<template>
  <div
    class="rounded-lg border border-hairline bg-surface"
    :class="[padded && 'p-6', raised && 'shadow-raised']"
  >
    <slot />
  </div>
</template>
