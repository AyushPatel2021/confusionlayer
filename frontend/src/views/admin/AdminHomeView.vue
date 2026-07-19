<script setup lang="ts">
import { computed, onMounted } from "vue";

import SBadge from "../../components/ui/SBadge.vue";
import SErrorState from "../../components/ui/SErrorState.vue";
import SLoadingState from "../../components/ui/SLoadingState.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
import SStatCard from "../../components/ui/SStatCard.vue";
import { roleLabels, useSessionStore, type Role } from "../../stores/session";

const session = useSessionStore();
const roleLabel = (role: string) => roleLabels[role as Role] || role.replace("_", " ");
const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const activationRate = computed(() => {
  const total = session.adminUsage?.users || 0;
  return total ? `${Math.round(((session.adminUsage?.active_users || 0) / total) * 100)}%` : "0%";
});
const segmentStats = computed(() => [
  { label: "ERP workspaces", value: session.adminUsage?.school_orgs || 0, description: "Operations-enabled accounts" },
  { label: "Teaching workspaces", value: session.adminUsage?.institute_orgs || 0, description: "Learning-only teams" },
  { label: "Self-learning", value: session.adminUsage?.individual_orgs || 0, description: "Individual accounts" },
]);
const platformSignals = computed(() => [
  { label: "Activation", value: activationRate.value, note: `${session.adminUsage?.active_users || 0} active of ${session.adminUsage?.users || 0} users` },
  { label: "Revenue collected", value: money(session.adminUsage?.collected_cents || 0), note: `${session.adminUsage?.invoices || 0} invoices issued` },
  { label: "Open receivables", value: money(session.adminUsage?.outstanding_cents || 0), note: "Across all billing records" },
  { label: "Admissions demand", value: session.adminUsage?.applications || 0, note: "Applications in the platform" },
]);
const activeUsers = computed(() => session.adminUsers.filter((user) => user.active).length);

onMounted(async () => {
  await session.loadAdmin();
});
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Platform admin" title="Slate platform overview" subtitle="App-owner visibility across adoption, revenue, content, users, and audit activity." />

    <SLoadingState v-if="session.loading === 'admin' && !session.adminOrgs.length" :rows="3" />
    <SErrorState v-else-if="session.error && !session.adminOrgs.length" :message="session.error" @retry="session.loadAdmin()" />

    <template v-else>
      <div v-if="session.adminUsage" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SStatCard label="Workspaces" :value="session.adminUsage.orgs" />
        <SStatCard label="Active users" :value="session.adminUsage.active_users" />
        <SStatCard label="Learners" :value="session.adminUsage.students" />
        <SStatCard label="Educators" :value="session.adminUsage.teachers" />
        <SStatCard label="Collected" :value="money(session.adminUsage.collected_cents)" tone="success" />
        <SStatCard label="Outstanding" :value="money(session.adminUsage.outstanding_cents)" tone="warning" />
        <SStatCard label="Staff records" :value="session.adminUsage.employees" />
        <SStatCard label="Applications" :value="session.adminUsage.applications" />
      </div>

      <section v-if="session.adminUsage" class="grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="s-eyebrow">Workspace mix</p>
              <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Product adoption</h2>
            </div>
            <SBadge tone="primary">{{ session.adminUsage.users }} total users</SBadge>
          </div>
          <div class="mt-5 grid gap-3">
            <article v-for="item in segmentStats" :key="item.label" class="rounded-md border border-hairline bg-paper p-4">
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-semibold text-ink-900">{{ item.label }}</p>
                <p class="font-display text-2xl font-semibold text-primary-700">{{ item.value }}</p>
              </div>
              <p class="mt-1 text-xs text-ink-500">{{ item.description }}</p>
            </article>
          </div>
        </div>
        <div class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Operating signals</p>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <article v-for="item in platformSignals" :key="item.label" class="rounded-md bg-surface-sunken p-4">
              <p class="text-xs font-medium text-ink-500">{{ item.label }}</p>
              <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ item.value }}</p>
              <p class="mt-1 text-xs text-ink-500">{{ item.note }}</p>
            </article>
          </div>
        </div>
      </section>

      <section v-if="session.adminContent" class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="s-eyebrow">Content library</p>
            <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Curriculum graph health</h2>
          </div>
          <SBadge tone="neutral">{{ session.adminContent.concepts }} concepts</SBadge>
        </div>
        <div class="mt-5 grid gap-3 sm:grid-cols-4">
          <article v-for="(value, label) in session.adminContent" :key="label" class="rounded-md bg-surface-sunken p-3">
            <p class="text-xs capitalize text-ink-500">{{ label.replace("_", " ") }}</p>
            <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ value }}</p>
          </article>
        </div>
      </section>

      <section class="overflow-hidden rounded-lg border border-hairline bg-surface">
        <div class="flex items-center justify-between border-b border-hairline p-5">
          <p class="s-eyebrow">Recent users</p>
          <SBadge tone="neutral">{{ activeUsers }} active in latest list</SBadge>
        </div>
        <div class="divide-y divide-hairline">
          <div v-for="user in session.adminUsers.slice(0, 10)" :key="user.id" class="flex items-center justify-between gap-3 p-4 text-sm">
            <div class="min-w-0">
              <p class="truncate font-medium text-ink-900">{{ user.name || user.email }}</p>
              <p class="text-xs text-ink-500">{{ roleLabel(user.role) }}</p>
            </div>
            <SBadge :tone="user.active ? 'success' : 'neutral'">{{ user.active ? "Active" : "Inactive" }}</SBadge>
          </div>
        </div>
      </section>

      <section class="overflow-hidden rounded-lg border border-hairline bg-surface">
        <div class="border-b border-hairline p-5"><p class="s-eyebrow">Audit trail</p></div>
        <div v-if="session.adminAuditLogs.length" class="divide-y divide-hairline">
          <div v-for="entry in session.adminAuditLogs" :key="entry.id" class="grid gap-1 p-4 text-sm sm:grid-cols-[1fr_1fr_1fr_auto]">
            <span class="font-medium text-ink-900">{{ entry.action.replace(/\./g, " ") }}</span>
            <span class="text-ink-700">{{ entry.target || "System" }}</span>
            <span class="text-ink-500">{{ entry.actor || "System" }}</span>
            <time class="text-xs text-ink-500">{{ new Date(entry.created_at).toLocaleString() }}</time>
          </div>
        </div>
        <p v-else class="p-5 text-sm text-ink-500">No recorded activity yet.</p>
      </section>
    </template>
  </div>
</template>
