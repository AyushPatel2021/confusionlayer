<script setup lang="ts">
import { computed, onMounted } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const org = computed(() => session.org);
const currentPlan = computed(() => org.value?.subscription?.plan?.code);

onMounted(() => {
  session.loadOrg();
  session.loadPlans();
});

function limitLabel(key: string, value: number) {
  const labels: Record<string, string> = { max_students: "students", max_classrooms: "classrooms", ai_calls_per_day: "AI calls/day" };
  return `${value} ${labels[key] || key}`;
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Settings" title="Plan & billing" subtitle="Every plan is free right now — switching won't charge you." />

    <SLoadingState v-if="session.loading === 'org' && !org" :rows="2" />

    <div v-else-if="org" class="space-y-8">
      <!-- Current org + usage -->
      <div class="grid gap-4 sm:grid-cols-4">
        <div class="rounded-md border border-hairline bg-surface p-4">
          <p class="text-xs text-ink-500">Organization</p>
          <p class="mt-1 font-semibold text-ink-900">{{ org.name }}</p>
          <p class="text-xs capitalize text-ink-500">{{ org.segment }}</p>
        </div>
        <div class="rounded-md border border-hairline bg-surface p-4">
          <p class="text-xs text-ink-500">Members</p>
          <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ org.usage.members }}</p>
        </div>
        <div class="rounded-md border border-hairline bg-surface p-4">
          <p class="text-xs text-ink-500">Students</p>
          <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ org.usage.students }}</p>
        </div>
        <div class="rounded-md border border-hairline bg-surface p-4">
          <p class="text-xs text-ink-500">Classrooms</p>
          <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ org.usage.classrooms }}</p>
        </div>
      </div>

      <!-- Plans -->
      <div>
        <p class="s-eyebrow">Plans for {{ org.segment }}</p>
        <div class="mt-4 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="plan in session.plans"
            :key="plan.code"
            class="flex flex-col rounded-lg border bg-surface p-6"
            :class="currentPlan === plan.code ? 'border-primary-600 shadow-raised' : 'border-hairline'"
          >
            <div class="flex items-center justify-between">
              <h3 class="font-display text-xl font-semibold text-ink-900">{{ plan.name }}</h3>
              <SBadge v-if="currentPlan === plan.code" tone="primary">current</SBadge>
            </div>
            <p class="mt-3 font-display text-3xl font-semibold text-ink-900">$0<span class="text-sm font-normal text-ink-500">/mo</span></p>
            <ul class="mt-4 flex-1 space-y-1.5 text-sm text-ink-700">
              <li v-for="(value, key) in plan.limits" :key="key" class="flex items-start gap-2">
                <span class="mt-0.5 text-primary-600" aria-hidden="true">✓</span>{{ limitLabel(key, value) }}
              </li>
            </ul>
            <SButton
              v-if="session.isOwner"
              class="mt-6"
              :variant="currentPlan === plan.code ? 'secondary' : 'primary'"
              block
              :disabled="currentPlan === plan.code || session.loading === `plan-${plan.code}`"
              @click="session.changePlan(plan.code)"
            >
              {{ currentPlan === plan.code ? "Current plan" : session.loading === `plan-${plan.code}` ? "Switching…" : "Switch to this plan" }}
            </SButton>
          </div>
        </div>
      </div>
      <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>
    </div>
  </div>
</template>
