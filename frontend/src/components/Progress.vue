<script setup lang="ts">
import Chart from "chart.js/auto";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

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

// Average mastery across all concepts at each recorded date -> a single trend line.
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
  return {
    labels,
    values: labels.map((date) => Math.round((byDate.get(date)!.sum / byDate.get(date)!.count) * 100)),
  };
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
        {
          label: "Average mastery (%)",
          data: values,
          borderColor: "#0f766e",
          backgroundColor: "rgba(15, 118, 110, 0.12)",
          fill: true,
          tension: 0.3,
          pointRadius: 3,
        },
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

function pct(value: number) {
  return Math.round(value * 100);
}
</script>

<template>
  <div class="panel">
    <div>
      <p class="eyebrow">Student · mastery over time</p>
      <h2 class="panel-title">My Progress</h2>
    </div>

    <!-- Loading -->
    <div v-if="session.loading === 'progress' && !progress" class="mt-5 space-y-3">
      <div class="skeleton-card" style="height: 16rem" />
    </div>

    <!-- Empty -->
    <div v-else-if="progress && progress.concepts.length === 0" class="mt-5 empty-tool">
      No mastery data yet. Once you've worked through some concepts, your mastery trend will show here.
    </div>

    <!-- Data -->
    <div v-else-if="progress" class="mt-5 space-y-5">
      <dl class="grid grid-cols-3 gap-3">
        <div class="metric">
          <dt>Concepts</dt>
          <dd>{{ progress.summary.concept_count }}</dd>
        </div>
        <div class="metric">
          <dt>Mastered (≥{{ pct(progress.mastered_threshold) }}%)</dt>
          <dd>{{ progress.summary.mastered_count }}</dd>
        </div>
        <div class="metric">
          <dt>Avg mastery now</dt>
          <dd>{{ pct(progress.summary.average_effective_mastery) }}%</dd>
        </div>
      </dl>

      <div class="tutorial-band">
        <p class="eyebrow">Average mastery over time</p>
        <div class="mt-3" style="position: relative; height: 16rem">
          <canvas ref="canvas" />
        </div>
      </div>

      <div>
        <p class="eyebrow">Current mastery by concept</p>
        <ul class="mt-3 space-y-2">
          <li v-for="concept in progress.concepts" :key="concept.concept_id" class="border border-slate-200 bg-white p-3">
            <div class="flex items-center justify-between gap-3">
              <span class="text-sm font-medium text-slate-800">{{ concept.concept_title }}</span>
              <span class="text-xs text-slate-500">
                {{ pct(concept.effective_mastery) }}% now · {{ pct(concept.current_mastery) }}% peak
              </span>
            </div>
            <div class="mt-2 forecast-bar">
              <div class="forecast-bar-fill" :style="{ width: `${pct(concept.effective_mastery)}%` }" />
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- Pre-load -->
    <div v-else class="mt-5 empty-tool">Loading progress…</div>
  </div>
</template>
