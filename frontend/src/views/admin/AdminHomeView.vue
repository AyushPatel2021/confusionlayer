<script setup lang="ts">
import Chart from "chart.js/auto";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import SBadge from "../../components/ui/SBadge.vue";
import SErrorState from "../../components/ui/SErrorState.vue";
import SLoadingState from "../../components/ui/SLoadingState.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
const canvas = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

onMounted(async () => {
  await session.loadAdmin();
  await nextTick();
  renderChart();
});
onBeforeUnmount(() => chart?.destroy());
watch(() => session.adminUsage, async () => {
  await nextTick();
  renderChart();
});

function renderChart() {
  if (!canvas.value || !session.adminUsage) return;
  chart?.destroy();
  const entries = Object.entries(session.adminUsage);
  chart = new Chart(canvas.value, { type: "bar", data: { labels: entries.map(([label]) => label), datasets: [{ data: entries.map(([, value]) => value), backgroundColor: "#0F6E6E", borderRadius: 4 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } } });
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Platform admin" title="Overview" subtitle="Every organization on Slate, at a glance." />

    <SLoadingState v-if="session.loading === 'admin' && !session.adminOrgs.length" :rows="3" />
    <SErrorState v-else-if="session.error && !session.adminOrgs.length" :message="session.error" @retry="session.loadAdmin()" />

    <template v-else>
      <div v-if="session.adminUsage" class="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <div v-for="(value, key) in session.adminUsage" :key="key" class="rounded-md border border-hairline bg-surface p-4">
          <p class="text-xs capitalize text-ink-500">{{ key }}</p>
          <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ value }}</p>
        </div>
      </div>

      <section v-if="session.adminUsage" class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Platform footprint</p>
        <div class="mt-4 h-64"><canvas ref="canvas" /></div>
      </section>

      <div class="overflow-hidden rounded-lg border border-hairline bg-surface">
        <table class="w-full text-sm">
          <thead class="bg-surface-sunken text-left text-xs uppercase tracking-wide text-ink-500">
            <tr><th class="px-4 py-3">Organization</th><th class="px-4 py-3">Segment</th><th class="px-4 py-3">Plan</th><th class="px-4 py-3">Members</th></tr>
          </thead>
          <tbody class="divide-y divide-hairline">
            <tr v-for="org in session.adminOrgs" :key="org.id">
              <td class="px-4 py-3 font-medium text-ink-900">{{ org.name }}</td>
              <td class="px-4 py-3"><SBadge tone="primary">{{ org.segment }}</SBadge></td>
              <td class="px-4 py-3 text-ink-700">{{ org.plan_code || "," }}</td>
              <td class="px-4 py-3 text-ink-700">{{ org.member_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="grid gap-5 lg:grid-cols-2"><section class="overflow-hidden rounded-lg border border-hairline bg-surface"><div class="border-b border-hairline p-5"><p class="s-eyebrow">Recent users</p></div><div class="divide-y divide-hairline"><div v-for="user in session.adminUsers.slice(0, 8)" :key="user.id" class="flex items-center justify-between gap-3 p-4 text-sm"><div><p class="font-medium text-ink-900">{{ user.name || user.email }}</p><p class="text-xs text-ink-500">{{ user.organization || 'Platform' }} · {{ user.role.replace('_', ' ') }}</p></div><SBadge :tone="user.active ? 'success' : 'neutral'">{{ user.active ? 'Active' : 'Inactive' }}</SBadge></div></div></section><section v-if="session.adminContent" class="rounded-lg border border-hairline bg-surface p-5"><p class="s-eyebrow">Content library</p><div class="mt-4 grid grid-cols-2 gap-3"><div v-for="(value, label) in session.adminContent" :key="label" class="rounded-md bg-surface-sunken p-3"><p class="text-xs capitalize text-ink-500">{{ label.replace('_', ' ') }}</p><p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ value }}</p></div></div></section></div>
      <section class="overflow-hidden rounded-lg border border-hairline bg-surface"><div class="border-b border-hairline p-5"><p class="s-eyebrow">Audit trail</p></div><div v-if="session.adminAuditLogs.length" class="divide-y divide-hairline"><div v-for="entry in session.adminAuditLogs" :key="entry.id" class="grid gap-1 p-4 text-sm sm:grid-cols-[1fr_1fr_1fr_auto]"><span class="font-medium text-ink-900">{{ entry.action.replace(/\./g, ' ') }}</span><span class="text-ink-700">{{ entry.target || 'System' }}</span><span class="text-ink-500">{{ entry.organization || 'Platform' }} · {{ entry.actor || 'System' }}</span><time class="text-xs text-ink-500">{{ new Date(entry.created_at).toLocaleString() }}</time></div></div><p v-else class="p-5 text-sm text-ink-500">No recorded activity yet.</p></section>
    </template>
  </div>
</template>
