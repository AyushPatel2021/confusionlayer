<script setup lang="ts">
import SBadge from "./SBadge.vue";

type Column = { key: string; label: string; tone?: "neutral" | "info" | "success" | "primary" | "danger" | "warning" };
type Item = { id: number | string; status: string; title: string; subtitle?: string; meta?: string };

const props = defineProps<{ columns: Column[]; items: Item[] }>();
const emit = defineEmits<{ select: [item: Item] }>();

function byStatus(status: string) {
  return props.items.filter((item) => item.status === status);
}
</script>

<template>
  <div class="grid gap-4 lg:grid-cols-5">
    <section v-for="col in columns" :key="col.key" class="rounded-lg border border-hairline bg-surface/60 p-3">
      <div class="mb-3 flex items-center justify-between px-1">
        <span class="text-sm font-semibold text-ink-900">{{ col.label }}</span>
        <SBadge :tone="col.tone || 'neutral'">{{ byStatus(col.key).length }}</SBadge>
      </div>
      <div class="space-y-3">
        <button
          v-for="item in byStatus(col.key)"
          :key="item.id"
          type="button"
          class="card-lift s-focus w-full rounded-md border border-hairline bg-surface p-3 text-left"
          @click="emit('select', item)"
        >
          <span class="block text-sm font-semibold text-ink-900">{{ item.title }}</span>
          <span v-if="item.subtitle" class="block text-xs text-ink-500">{{ item.subtitle }}</span>
          <span v-if="item.meta" class="block truncate text-xs text-ink-500">{{ item.meta }}</span>
        </button>
        <p v-if="!byStatus(col.key).length" class="px-1 py-4 text-center text-xs text-ink-500">Empty</p>
      </div>
    </section>
  </div>
</template>
