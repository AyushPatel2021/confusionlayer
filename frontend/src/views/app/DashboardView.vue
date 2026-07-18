<script setup lang="ts">
import Chart from "chart.js/auto";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import SEmptyState from "../../components/ui/SEmptyState.vue";
import SErrorState from "../../components/ui/SErrorState.vue";
import SLoadingState from "../../components/ui/SLoadingState.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
const canvas = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

onMounted(async () => {
  await session.loadDashboard();
  renderChart();
});
onBeforeUnmount(() => chart?.destroy());
watch(() => session.dashboard, () => renderChart());

function renderChart() {
  if (!canvas.value || !session.dashboard) return;
  chart?.destroy();
  chart = new Chart(canvas.value, {
    type: "bar",
    data: { labels: session.dashboard.chart.labels, datasets: [{ data: session.dashboard.chart.values, backgroundColor: "#0F6E6E", borderRadius: 4 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Workspace" :title="session.dashboard?.title || 'Overview'" subtitle="The current state of your school and learning work." />
    <SLoadingState v-if="session.loading === 'dashboard' && !session.dashboard" :rows="3" />
    <SErrorState v-else-if="session.error && !session.dashboard" :message="session.error" @retry="session.loadDashboard" />
    <template v-else-if="session.dashboard">
      <dl class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div v-for="metric in session.dashboard.metrics" :key="metric.label" class="rounded-md border border-hairline bg-surface p-5">
          <dt class="text-sm text-ink-500">{{ metric.label }}</dt>
          <dd class="mt-2 font-display text-3xl font-semibold text-ink-900">{{ metric.value }}</dd>
        </div>
      </dl>
      <section class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">{{ session.dashboard.chart.label }}</p>
        <div class="mt-4 h-64"><canvas ref="canvas" /></div>
      </section>
      <section v-if="session.dashboard.classrooms.length" class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex items-center justify-between gap-4">
          <p class="s-eyebrow">Classrooms</p>
          <RouterLink v-if="session.isOrgAdmin" to="/app/classrooms" class="text-sm font-semibold text-primary-700 hover:text-primary-600">Manage classrooms</RouterLink>
        </div>
        <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <div v-for="classroom in session.dashboard.classrooms" :key="classroom.id" class="rounded-md border border-hairline bg-paper p-4">
            <p class="font-semibold text-ink-900">{{ classroom.name }}</p>
            <p class="mt-1 text-sm text-ink-500">{{ classroom.subject.name }} | {{ classroom.teacher.name }}</p>
            <p class="mt-3 text-sm text-ink-700">{{ classroom.students.length }} students</p>
          </div>
        </div>
      </section>
      <SEmptyState v-else-if="session.isOrgAdmin" title="Create your first classroom" message="Add a subject and teacher first, then enrol students into a classroom.">
        <template #action><RouterLink to="/app/classrooms" class="text-sm font-semibold text-primary-700">Manage classrooms</RouterLink></template>
      </SEmptyState>
    </template>
  </div>
</template>
