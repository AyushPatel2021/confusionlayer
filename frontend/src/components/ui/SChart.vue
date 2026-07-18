<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ label: string; labels: string[]; values: number[]; max?: number; suffix?: string }>();
const maxValue = computed(() => props.max || Math.max(1, ...props.values));
</script>

<template>
  <section class="rounded-lg border border-hairline bg-surface p-5">
    <p class="s-eyebrow">{{ label }}</p>
    <div class="mt-4 space-y-3">
      <div v-for="(item, index) in labels" :key="`${item}-${index}`" class="grid gap-2 sm:grid-cols-[220px_minmax(0,1fr)_56px] sm:items-center">
        <p class="truncate text-sm text-ink-700">{{ item }}</p>
        <div class="h-2 rounded-full bg-surface-sunken">
          <div class="h-full rounded-full bg-primary-600" :style="{ width: `${Math.max(3, Math.min(100, (values[index] / maxValue) * 100))}%` }" />
        </div>
        <p class="text-right text-xs font-medium text-ink-500">{{ values[index] }}{{ suffix || "" }}</p>
      </div>
    </div>
  </section>
</template>
