<script setup lang="ts">
import Chart from "chart.js/auto";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import SEmptyState from "./ui/SEmptyState.vue";
import SLoadingState from "./ui/SLoadingState.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const canvas = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

const progress = computed(() => session.progress);

onMounted(() => {
  if (!session.progress) void session.loadProgress();
  renderChart();
});
onBeforeUnmount(() => chart?.destroy());
watch(progress, () => renderChart());

function averagedSeries(): { labels: string[]; values: number[] } {
  const p = session.progress;
  if (!p) return { labels: [], values: [] };
  const byDate = new Map<string, { sum: number; count: number }>();
  for (const concept of p.concepts) {
    for (const point of concept.history) {
      const bucket = byDate.get(point.recorded_at) ?? { sum: 0, count: 0 };
      bucket.sum += point.mastery;
      bucket.count += 1;
      byDate.set(point.recorded_at, bucket);
    }
  }
  const labels = [...byDate.keys()].sort();
  return { labels, values: labels.map((d) => Math.round((byDate.get(d)!.sum / byDate.get(d)!.count) * 100)) };
}

function renderChart() {
  if (!canvas.value) return;
  const { labels, values } = averagedSeries();
  chart?.destroy();
  if (labels.length === 0) return;
  chart = new Chart(canvas.value, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Average mastery (%)", data: values, borderColor: "#0F6E6E", backgroundColor: "rgba(15,110,110,0.12)", fill: true, tension: 0.3, pointRadius: 3 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { min: 0, max: 100, ticks: { callback: (v) => `${v}%` } } },
      plugins: { legend: { display: false } },
    },
  });
}

function pct(v: number) {
  return Math.round(v * 100);
}
</script>

<template>
  <div>
    <SLoadingState v-if="session.loading === 'progress' && !progress" :rows="2" />
    <SEmptyState
      v-else-if="progress && progress.concepts.length === 0"
      title="No mastery data yet"
      message="Once you've worked through some concepts, your mastery trend will show here."
    />
    <div v-else-if="progress" class="space-y-6">
      <dl class="grid grid-cols-3 gap-3">
        <div class="rounded-md border border-hairline bg-surface p-4">
          <dt class="text-xs font-medium text-ink-500">Concepts</dt>
          <dd class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ progress.summary.concept_count }}</dd>
        </div>
        <div class="rounded-md border border-hairline bg-surface p-4">
          <dt class="text-xs font-medium text-ink-500">Mastered (≥{{ pct(progress.mastered_threshold) }}%)</dt>
          <dd class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ progress.summary.mastered_count }}</dd>
        </div>
        <div class="rounded-md border border-hairline bg-surface p-4">
          <dt class="text-xs font-medium text-ink-500">Avg mastery now</dt>
          <dd class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ pct(progress.summary.average_effective_mastery) }}%</dd>
        </div>
      </dl>

      <div class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Average mastery over time</p>
        <div class="mt-3" style="position: relative; height: 16rem"><canvas ref="canvas" /></div>
      </div>

      <div>
        <p class="s-eyebrow">Current mastery by concept</p>
        <ul class="mt-3 space-y-2">
          <li v-for="c in progress.concepts" :key="c.concept_id" class="rounded-md border border-hairline bg-surface p-3">
            <div class="flex items-center justify-between gap-3">
              <span class="text-sm font-medium text-ink-800">{{ c.concept_title }}</span>
              <span class="text-xs text-ink-500">{{ pct(c.effective_mastery) }}% now | {{ pct(c.current_mastery) }}% peak</span>
            </div>
            <div class="mt-2 h-2 w-full overflow-hidden rounded-sm bg-surface-sunken">
              <div class="h-full rounded-sm bg-primary-600" :style="{ width: `${pct(c.effective_mastery)}%` }" />
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
