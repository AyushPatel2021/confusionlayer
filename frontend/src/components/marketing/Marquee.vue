<script setup lang="ts">
defineProps<{ items: string[] }>();
</script>

<template>
  <div class="marquee border-y border-hairline bg-surface/60 py-3">
    <div class="marquee-track">
      <template v-for="pass in 2" :key="pass">
        <span v-for="(item, i) in items" :key="`${pass}-${i}`" class="flex items-center">
          <span class="px-6 font-display text-lg text-ink-700">{{ item }}</span>
          <span class="text-accent-600" aria-hidden="true">|</span>
        </span>
      </template>
    </div>
  </div>
</template>
