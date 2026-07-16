<script setup lang="ts">
import { onMounted } from "vue";

import SBadge from "../../components/ui/SBadge.vue";
import SErrorState from "../../components/ui/SErrorState.vue";
import SLoadingState from "../../components/ui/SLoadingState.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
onMounted(() => session.loadAdmin());
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

      <div class="overflow-hidden rounded-lg border border-hairline bg-surface">
        <table class="w-full text-sm">
          <thead class="bg-surface-sunken text-left text-xs uppercase tracking-wide text-ink-500">
            <tr><th class="px-4 py-3">Organization</th><th class="px-4 py-3">Segment</th><th class="px-4 py-3">Plan</th><th class="px-4 py-3">Members</th></tr>
          </thead>
          <tbody class="divide-y divide-hairline">
            <tr v-for="org in session.adminOrgs" :key="org.id">
              <td class="px-4 py-3 font-medium text-ink-900">{{ org.name }}</td>
              <td class="px-4 py-3"><SBadge tone="primary">{{ org.segment }}</SBadge></td>
              <td class="px-4 py-3 text-ink-700">{{ org.plan_code || "—" }}</td>
              <td class="px-4 py-3 text-ink-700">{{ org.member_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
