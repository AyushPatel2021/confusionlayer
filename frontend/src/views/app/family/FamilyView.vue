<script setup lang="ts">
import { computed, onMounted } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
onMounted(() => session.loadChildren());

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN")}`;
const totalOutstanding = computed(() => session.children.reduce((total, child) => total + child.outstanding_cents, 0));
const averageMastery = computed(() => {
  const values = session.children.map((child) => child.average_mastery).filter((value): value is number => value !== null);
  return values.length ? Math.round((values.reduce((total, value) => total + value, 0) / values.length) * 100) : null;
});
const attendanceTotal = (child: { attendance: Record<string, number> }) => Object.values(child.attendance || {}).reduce((total, value) => total + value, 0);
const attendanceRate = (child: { attendance: Record<string, number> }) => {
  const total = attendanceTotal(child);
  return total ? Math.round(((child.attendance.present || 0) / total) * 100) : null;
};
const quizRate = (child: { quiz_attempts: number; quiz_correct: number }) => child.quiz_attempts ? Math.round((child.quiz_correct / child.quiz_attempts) * 100) : null;
const masteryLabel = (value: number) => `${Math.round(value * 100)}%`;
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Family" title="My children" subtitle="A read-only view of your children's progress, attendance, practice, fees, and admission status." />

    <SLoadingState v-if="session.loading === 'children' && !session.children.length" :rows="2" />
    <SEmptyState
      v-else-if="!session.children.length"
      title="No children linked yet"
      message="Once your school links your account to a student, they'll appear here."
    />
    <template v-else>
      <div class="grid gap-4 sm:grid-cols-3">
        <article class="rounded-lg border border-hairline bg-surface p-4">
          <p class="text-xs font-medium text-ink-500">Children linked</p>
          <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ session.children.length }}</p>
        </article>
        <article class="rounded-lg border border-hairline bg-surface p-4">
          <p class="text-xs font-medium text-ink-500">Average mastery</p>
          <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ averageMastery !== null ? `${averageMastery}%` : "N/A" }}</p>
        </article>
        <article class="rounded-lg border border-hairline bg-surface p-4">
          <p class="text-xs font-medium text-ink-500">Fees outstanding</p>
          <p class="mt-1 font-display text-2xl font-semibold" :class="totalOutstanding ? 'text-accent-600' : 'text-success'">{{ money(totalOutstanding) }}</p>
        </article>
      </div>

      <div class="grid gap-5 xl:grid-cols-2">
        <article v-for="child in session.children" :key="child.student_id" class="rounded-lg border border-hairline bg-surface p-6">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 class="font-display text-xl font-semibold text-ink-900">{{ child.name }}</h2>
              <p v-if="child.latest_activity_at" class="mt-1 text-xs text-ink-500">Latest activity {{ new Date(child.latest_activity_at).toLocaleDateString() }}</p>
            </div>
            <SBadge v-if="child.admission_status" :tone="child.admission_status === 'enrolled' ? 'success' : 'neutral'">{{ child.admission_status }}</SBadge>
          </div>

          <dl class="mt-5 grid gap-3 sm:grid-cols-4">
            <div class="rounded-md bg-surface-sunken p-3">
              <dt class="text-xs text-ink-500">Mastery</dt>
              <dd class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ child.average_mastery !== null ? masteryLabel(child.average_mastery) : "N/A" }}</dd>
            </div>
            <div class="rounded-md bg-surface-sunken p-3">
              <dt class="text-xs text-ink-500">Attendance</dt>
              <dd class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ attendanceRate(child) !== null ? `${attendanceRate(child)}%` : "N/A" }}</dd>
            </div>
            <div class="rounded-md bg-surface-sunken p-3">
              <dt class="text-xs text-ink-500">Quiz score</dt>
              <dd class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ quizRate(child) !== null ? `${quizRate(child)}%` : "N/A" }}</dd>
            </div>
            <div class="rounded-md bg-surface-sunken p-3">
              <dt class="text-xs text-ink-500">Fees due</dt>
              <dd class="mt-1 font-display text-2xl font-semibold" :class="child.outstanding_cents > 0 ? 'text-accent-600' : 'text-success'">{{ money(child.outstanding_cents) }}</dd>
            </div>
          </dl>

          <div class="mt-5 grid gap-5 lg:grid-cols-2">
            <section>
              <p class="s-eyebrow">Strengths</p>
              <div v-if="child.strongest_topics.length" class="mt-3 space-y-2">
                <div v-for="topic in child.strongest_topics" :key="topic.concept_id" class="rounded-md border border-hairline p-3">
                  <div class="flex items-center justify-between gap-3">
                    <p class="text-sm font-semibold text-ink-900">{{ topic.title }}</p>
                    <SBadge tone="success">{{ masteryLabel(topic.effective_mastery) }}</SBadge>
                  </div>
                  <p class="mt-1 text-xs text-ink-500">{{ topic.chapter_title }}</p>
                </div>
              </div>
              <p v-else class="mt-3 rounded-md border border-dashed border-hairline p-4 text-sm text-ink-500">No strength data yet.</p>
            </section>

            <section>
              <p class="s-eyebrow">Needs support</p>
              <div v-if="child.weakest_topics.length" class="mt-3 space-y-2">
                <div v-for="topic in child.weakest_topics" :key="topic.concept_id" class="rounded-md border border-hairline p-3">
                  <div class="flex items-center justify-between gap-3">
                    <p class="text-sm font-semibold text-ink-900">{{ topic.title }}</p>
                    <SBadge tone="warning">{{ masteryLabel(topic.effective_mastery) }}</SBadge>
                  </div>
                  <p class="mt-1 text-xs text-ink-500">{{ topic.chapter_title }}</p>
                </div>
              </div>
              <p v-else class="mt-3 rounded-md border border-dashed border-hairline p-4 text-sm text-ink-500">No support gaps recorded yet.</p>
            </section>
          </div>

          <div class="mt-5 flex flex-wrap gap-2">
            <SBadge tone="neutral">{{ attendanceTotal(child) }} attendance records</SBadge>
            <SBadge tone="neutral">{{ child.quiz_attempts }} quizzes</SBadge>
            <SBadge tone="neutral">{{ child.teach_back_attempts }} teach-backs</SBadge>
          </div>
        </article>
      </div>
    </template>
  </div>
</template>
