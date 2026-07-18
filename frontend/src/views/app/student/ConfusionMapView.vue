<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const router = useRouter();
const selectedId = ref<number | null>(null);
onMounted(async () => { await session.loadConfusionMap(); selectedId.value = session.confusionMap?.nodes[0]?.concept_id ?? null; });
const positioned = computed(() => (session.confusionMap?.nodes || []).map((node, index) => ({ ...node, x: 150 + (index % 3) * 310, y: 110 + Math.floor(index / 3) * 170 })));
const mapHeight = computed(() => Math.max(310, Math.ceil(positioned.value.length / 3) * 170 + 80));
const byId = computed(() => new Map(positioned.value.map((node) => [node.concept_id, node])));
const selected = computed(() => positioned.value.find((node) => node.concept_id === selectedId.value) || null);
const tone = (mastery: number): "success" | "warning" | "danger" => mastery >= .8 ? "success" : mastery >= .6 ? "warning" : "danger";
const label = (mastery: number) => mastery >= .8 ? "Mastered" : mastery >= .6 ? "Fading" : "At risk";
</script>

<template>
  <div class="space-y-8"><SPageHeader eyebrow="ConfusionLayer" title="Your confusion map" subtitle="Trace prerequisite links to see which foundations are driving tomorrow's gaps." />
    <SLoadingState v-if="session.loading === 'confusion-map'" :rows="4" />
    <template v-else-if="session.confusionMap"><section class="overflow-auto rounded-lg border border-hairline bg-surface p-4"><svg :viewBox="`0 0 960 ${mapHeight}`" class="min-w-[760px]" role="img" aria-label="Prerequisite concept graph"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#9ca3af" /></marker></defs><line v-for="edge in session.confusionMap.edges" :key="`${edge.prerequisite_concept_id}-${edge.concept_id}`" :x1="byId.get(edge.prerequisite_concept_id)?.x" :y1="byId.get(edge.prerequisite_concept_id)?.y" :x2="byId.get(edge.concept_id)?.x" :y2="byId.get(edge.concept_id)?.y" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)" /><g v-for="node in positioned" :key="node.concept_id" class="cursor-pointer" tabindex="0" role="button" @click="selectedId = node.concept_id" @keydown.enter="selectedId = node.concept_id"><rect :x="node.x - 115" :y="node.y - 46" width="230" height="92" rx="6" :fill="selectedId === node.concept_id ? '#e6f3f2' : '#ffffff'" :stroke="tone(node.effective_mastery) === 'success' ? '#2f7d69' : tone(node.effective_mastery) === 'warning' ? '#b98222' : '#c65b38'" stroke-width="2" /><text :x="node.x" :y="node.y - 10" text-anchor="middle" class="fill-ink-900 text-sm font-semibold">{{ node.title }}</text><text :x="node.x" :y="node.y + 14" text-anchor="middle" class="fill-ink-500 text-xs">{{ Math.round(node.effective_mastery * 100) }}% mastery</text></g></svg></section>
      <section v-if="selected" class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-hairline bg-surface p-5"><div><p class="text-xs text-ink-500">{{ selected.chapter_title }}</p><h2 class="mt-1 font-display text-xl font-semibold text-ink-900">{{ selected.title }}</h2><div class="mt-2 flex gap-2"><SBadge :tone="tone(selected.effective_mastery)">{{ label(selected.effective_mastery) }}</SBadge><SBadge v-if="selected.forecast_risk !== null" tone="neutral">{{ Math.round(selected.forecast_risk * 100) }}% forecast risk</SBadge></div></div><button class="s-focus rounded-md border border-primary-600 bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-500" @click="router.push(`/app/learn/${selected.concept_id}`)">Review concept</button></section>
      <p v-if="!positioned.length" class="text-sm text-ink-500">Complete learning activities to build your first concept map.</p></template>
  </div>
</template>
