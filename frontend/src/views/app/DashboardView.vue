<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";

import SChart from "../../components/ui/SChart.vue";
import SEmptyState from "../../components/ui/SEmptyState.vue";
import SErrorState from "../../components/ui/SErrorState.vue";
import SLoadingState from "../../components/ui/SLoadingState.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
import SStatCard from "../../components/ui/SStatCard.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
});
const name = computed(() => session.user?.name || (session.user?.role === "student" ? "Learner" : "there"));
const nextAction = computed(() => {
  if (session.isStudent) return { to: "/app/learn", label: "Continue learning", text: "Start with an unlocked topic and build on your current mastery." };
  if (session.user?.role === "teacher") return { to: "/app/teacher/forecast", label: "Review forecast brief", text: "Check the concepts likely to need extra attention before your next class." };
  if (session.isParent) return { to: "/app/family", label: "View family summary", text: "Review your child’s learning progress and current school updates." };
  if (session.isOrgAdmin) return { to: "/app/classrooms", label: "Review classrooms", text: "Make sure every active class has a teacher, subject, and enrolled students." };
  return { to: "/app/dashboard", label: "Review workspace", text: "Check the current work that needs attention today." };
});

onMounted(async () => {
  await session.loadDashboard();
  if (session.isStudent) await session.loadExamOutcome();
});
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Today" :title="`${greeting}, ${name}`" :subtitle="session.dashboard?.title || 'Your workspace overview'" />
    <SLoadingState v-if="session.loading === 'dashboard' && !session.dashboard" :rows="3" />
    <SErrorState v-else-if="session.error && !session.dashboard" :message="session.error" @retry="session.loadDashboard" />
    <template v-else-if="session.dashboard">
      <dl class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SStatCard v-for="metric in session.dashboard.metrics" :key="metric.label" :label="metric.label" :value="metric.value" />
      </dl>
      <section class="flex flex-wrap items-center justify-between gap-5 rounded-lg border border-primary-200 bg-primary-50 p-5">
        <div>
          <p class="s-eyebrow">Your next step</p>
          <p class="mt-1 text-sm text-ink-700">{{ nextAction.text }}</p>
        </div>
        <RouterLink :to="nextAction.to" class="rounded-md bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-500">{{ nextAction.label }}</RouterLink>
      </section>
      <section v-if="session.isStudent && session.examOutcome?.outcomes.length" class="rounded-lg border border-hairline bg-surface p-5"><div class="flex items-center justify-between gap-3"><div><p class="s-eyebrow">Five-minute decay drills</p><p class="mt-1 text-sm text-ink-600">Review the concepts most likely to fade before your exam.</p></div><RouterLink to="/app/exam-outcome" class="text-sm font-semibold text-primary-700 hover:underline">See exam outlook</RouterLink></div><div class="mt-4 grid gap-3 md:grid-cols-3"><RouterLink v-for="item in session.examOutcome.outcomes.slice(0, 3)" :key="item.concept_id" :to="`/app/learn/${item.concept_id}`" class="rounded-md border border-hairline bg-paper p-4 hover:border-primary-500"><p class="font-semibold text-ink-900">{{ item.title }}</p><p class="mt-1 text-xs text-ink-500">{{ Math.round(item.risk * 100) }}% forecast risk</p><p class="mt-3 text-sm font-semibold text-primary-700">Start drill</p></RouterLink></div></section>
      <SChart :label="session.dashboard.chart.label" :labels="session.dashboard.chart.labels" :values="session.dashboard.chart.values" />
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
