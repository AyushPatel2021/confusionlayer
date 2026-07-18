<script setup lang="ts">
import { onMounted } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
onMounted(() => session.loadChildren());

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN")}`;
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Family" title="My children" subtitle="A read-only view of your children's progress, fees, and admission status." />

    <SLoadingState v-if="session.loading === 'children' && !session.children.length" :rows="2" />
    <SEmptyState
      v-else-if="!session.children.length"
      title="No children linked yet"
      message="Once your school links your account to a student, they'll appear here."
    />
    <div v-else class="grid gap-5 md:grid-cols-2">
      <div v-for="child in session.children" :key="child.student_id" class="rounded-lg border border-hairline bg-surface p-6">
        <div class="flex items-center justify-between">
          <h2 class="font-display text-xl font-semibold text-ink-900">{{ child.name }}</h2>
          <SBadge v-if="child.admission_status" :tone="child.admission_status === 'enrolled' ? 'success' : 'neutral'">{{ child.admission_status }}</SBadge>
        </div>
        <dl class="mt-5 grid grid-cols-2 gap-4">
          <div>
            <dt class="text-xs text-ink-500">Average mastery</dt>
            <dd class="mt-1 font-display text-2xl font-semibold text-ink-900">
              {{ child.average_mastery !== null ? Math.round(child.average_mastery * 100) + "%" : "N/A" }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-ink-500">Fees outstanding</dt>
            <dd class="mt-1 font-display text-2xl font-semibold" :class="child.outstanding_cents > 0 ? 'text-accent-600' : 'text-success'">
              {{ money(child.outstanding_cents) }}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>
