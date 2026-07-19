<script setup lang="ts">
import { computed, onMounted } from "vue";
import { Activity, Building2, CircleDollarSign, Database, GraduationCap, ShieldCheck, UserRoundCheck, UsersRound } from "@lucide/vue";

import SBadge from "../../components/ui/SBadge.vue";
import SErrorState from "../../components/ui/SErrorState.vue";
import SLoadingState from "../../components/ui/SLoadingState.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
import SStatCard from "../../components/ui/SStatCard.vue";
import { roleLabels, useSessionStore, type Role } from "../../stores/session";

const session = useSessionStore();

const roleLabel = (role: string) => roleLabels[role as Role] || role.replace(/_/g, " ");
const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const percent = (value: number, total: number) => (total ? `${Math.round((value / total) * 100)}%` : "0%");
const segmentLabel = (segment: string) => {
  if (segment === "school") return "School";
  if (segment === "institute") return "Institute";
  if (segment === "individual") return "Individual";
  return segment;
};

const latestOrgs = computed(() => session.adminOrgs.slice(0, 8));
const activeUsers = computed(() => session.adminUsers.filter((user) => user.active));
const inactiveUsers = computed(() => session.adminUsers.filter((user) => !user.active));
const roleMix = computed(() => {
  const counts = new Map<string, number>();
  for (const user of session.adminUsers) counts.set(user.role, (counts.get(user.role) || 0) + 1);
  return [...counts.entries()]
    .map(([role, count]) => ({ role, count, label: roleLabel(role) }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);
});
const segmentStats = computed(() => [
  { key: "school", label: "Schools", value: session.adminUsage?.school_orgs || 0, note: "Full ERP workspaces", tone: "primary" as const },
  { key: "institute", label: "Institutes", value: session.adminUsage?.institute_orgs || 0, note: "Teaching teams", tone: "success" as const },
  { key: "individual", label: "Individuals", value: session.adminUsage?.individual_orgs || 0, note: "Self-study accounts", tone: "neutral" as const },
]);
const appSignals = computed(() => [
  { label: "Activation", value: percent(session.adminUsage?.active_users || 0, session.adminUsage?.users || 0), note: `${session.adminUsage?.active_users || 0} active of ${session.adminUsage?.users || 0} users`, icon: UserRoundCheck },
  { label: "Learning reach", value: session.adminUsage?.students || 0, note: `${session.adminUsage?.teachers || 0} educators`, icon: GraduationCap },
  { label: "Collected", value: money(session.adminUsage?.collected_cents || 0), note: `${session.adminUsage?.invoices || 0} invoices`, icon: CircleDollarSign },
  { label: "Open balance", value: money(session.adminUsage?.outstanding_cents || 0), note: "Across active invoices", icon: Activity },
]);
const contentItems = computed(() => {
  if (!session.adminContent) return [];
  return [
    { label: "Subjects", value: session.adminContent.subjects },
    { label: "Chapters", value: session.adminContent.chapters },
    { label: "Concepts", value: session.adminContent.concepts },
    { label: "Prerequisite edges", value: session.adminContent.concept_edges },
    { label: "Employees", value: session.adminContent.employees },
    { label: "Applications", value: session.adminContent.applications },
  ];
});

onMounted(async () => {
  await session.loadAdmin();
});
</script>

<template>
  <div class="space-y-8">
    <SPageHeader
      eyebrow="Platform admin"
      title="Slate command center"
      subtitle="App-owner view across workspace adoption, learning content, users, finance signals and audit activity."
    />

    <SLoadingState v-if="session.loading === 'admin' && !session.adminOrgs.length" :rows="3" />
    <SErrorState v-else-if="session.error && !session.adminOrgs.length" :message="session.error" @retry="session.loadAdmin()" />

    <template v-else>
      <section v-if="session.adminUsage" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SStatCard label="Workspaces" :value="session.adminUsage.orgs" />
        <SStatCard label="Active users" :value="session.adminUsage.active_users" tone="success" />
        <SStatCard label="Learners" :value="session.adminUsage.students" />
        <SStatCard label="Educators" :value="session.adminUsage.teachers" />
      </section>

      <section class="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(22rem,0.95fr)]">
        <div class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="s-eyebrow">Workspace portfolio</p>
              <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Product mix</h2>
              <p class="mt-1 text-sm text-ink-500">Track how each Slate package is represented in the live system.</p>
            </div>
            <SBadge tone="primary">{{ session.adminOrgs.length }} loaded</SBadge>
          </div>

          <div class="mt-5 grid gap-3 md:grid-cols-3">
            <article v-for="item in segmentStats" :key="item.key" class="rounded-md border border-hairline bg-paper p-4">
              <div class="flex items-center justify-between gap-3">
                <span class="grid h-9 w-9 place-items-center rounded-md bg-primary-50 text-primary-700">
                  <Building2 :size="18" aria-hidden="true" />
                </span>
                <SBadge :tone="item.tone">{{ item.value }}</SBadge>
              </div>
              <p class="mt-4 font-semibold text-ink-900">{{ item.label }}</p>
              <p class="mt-1 text-xs text-ink-500">{{ item.note }}</p>
            </article>
          </div>

          <div class="mt-5 overflow-hidden rounded-md border border-hairline">
            <div class="grid grid-cols-[1.3fr_0.8fr_0.8fr_auto] gap-3 border-b border-hairline bg-surface-sunken px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink-500">
              <span>Workspace</span>
              <span>Segment</span>
              <span>Plan</span>
              <span class="text-right">Members</span>
            </div>
            <div class="divide-y divide-hairline">
              <div v-for="org in latestOrgs" :key="org.id" class="grid grid-cols-[1.3fr_0.8fr_0.8fr_auto] items-center gap-3 px-4 py-3 text-sm">
                <span class="min-w-0">
                  <b class="block truncate text-ink-900">{{ org.name }}</b>
                  <span class="text-xs text-ink-500">{{ org.slug }}</span>
                </span>
                <SBadge tone="neutral">{{ segmentLabel(org.segment) }}</SBadge>
                <span class="truncate text-xs text-ink-500">{{ org.plan_code || "No plan" }}</span>
                <span class="text-right font-semibold text-ink-900">{{ org.member_count }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-5">
          <section class="rounded-lg border border-hairline bg-surface p-5">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="s-eyebrow">App health</p>
                <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Operating signals</h2>
              </div>
              <ShieldCheck :size="24" class="text-primary-700" aria-hidden="true" />
            </div>
            <div class="mt-5 grid gap-3 sm:grid-cols-2">
              <article v-for="item in appSignals" :key="item.label" class="rounded-md bg-surface-sunken p-4">
                <component :is="item.icon" :size="18" class="text-primary-700" aria-hidden="true" />
                <p class="mt-3 text-xs font-medium text-ink-500">{{ item.label }}</p>
                <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ item.value }}</p>
                <p class="mt-1 text-xs text-ink-500">{{ item.note }}</p>
              </article>
            </div>
          </section>

          <section class="rounded-lg border border-hairline bg-surface p-5">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="s-eyebrow">User operations</p>
                <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Role mix</h2>
              </div>
              <SBadge tone="neutral">{{ inactiveUsers.length }} inactive</SBadge>
            </div>
            <div class="mt-4 space-y-3">
              <div v-for="item in roleMix" :key="item.role" class="grid grid-cols-[8rem_minmax(0,1fr)_auto] items-center gap-3 text-sm">
                <span class="truncate font-medium text-ink-800">{{ item.label }}</span>
                <span class="h-2 overflow-hidden rounded-full bg-surface-sunken">
                  <span class="block h-full rounded-full bg-primary-700" :style="{ width: percent(item.count, session.adminUsers.length) }" />
                </span>
                <span class="font-semibold text-ink-900">{{ item.count }}</span>
              </div>
            </div>
          </section>
        </div>
      </section>

      <section class="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <section v-if="session.adminContent" class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="s-eyebrow">Content graph</p>
              <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Curriculum and operations depth</h2>
            </div>
            <Database :size="24" class="text-primary-700" aria-hidden="true" />
          </div>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <article v-for="item in contentItems" :key="item.label" class="rounded-md border border-hairline bg-paper p-4">
              <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">{{ item.label }}</p>
              <p class="mt-2 font-display text-2xl font-semibold text-ink-900">{{ item.value }}</p>
            </article>
          </div>
        </section>

        <section class="overflow-hidden rounded-lg border border-hairline bg-surface">
          <div class="flex items-center justify-between border-b border-hairline p-5">
            <div>
              <p class="s-eyebrow">Recent users</p>
              <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Account activity</h2>
            </div>
            <SBadge tone="success">{{ activeUsers.length }} active</SBadge>
          </div>
          <div class="divide-y divide-hairline">
            <div v-for="user in session.adminUsers.slice(0, 8)" :key="user.id" class="grid gap-3 p-4 text-sm sm:grid-cols-[minmax(0,1fr)_10rem_auto] sm:items-center">
              <div class="min-w-0">
                <p class="truncate font-semibold text-ink-900">{{ user.name || user.email }}</p>
                <p class="truncate text-xs text-ink-500">{{ user.email }}</p>
              </div>
              <span class="text-xs text-ink-500">{{ user.organization || "Platform" }}</span>
              <div class="flex items-center gap-2 sm:justify-end">
                <SBadge tone="neutral">{{ roleLabel(user.role) }}</SBadge>
                <SBadge :tone="user.active ? 'success' : 'neutral'">{{ user.active ? "Active" : "Inactive" }}</SBadge>
              </div>
            </div>
          </div>
        </section>
      </section>

      <section class="overflow-hidden rounded-lg border border-hairline bg-surface">
        <div class="flex items-center justify-between border-b border-hairline p-5">
          <div>
            <p class="s-eyebrow">Audit trail</p>
            <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">Sensitive activity</h2>
          </div>
          <UsersRound :size="22" class="text-primary-700" aria-hidden="true" />
        </div>
        <div v-if="session.adminAuditLogs.length" class="divide-y divide-hairline">
          <div v-for="entry in session.adminAuditLogs.slice(0, 12)" :key="entry.id" class="grid gap-2 p-4 text-sm lg:grid-cols-[1fr_1fr_1fr_auto] lg:items-center">
            <span class="font-medium capitalize text-ink-900">{{ entry.action.replace(/\./g, " ") }}</span>
            <span class="text-ink-700">{{ entry.target || "System" }}</span>
            <span class="text-ink-500">{{ entry.organization || entry.actor || "System" }}</span>
            <time class="text-xs text-ink-500">{{ new Date(entry.created_at).toLocaleString() }}</time>
          </div>
        </div>
        <p v-else class="p-5 text-sm text-ink-500">No recorded activity yet.</p>
      </section>
    </template>
  </div>
</template>
