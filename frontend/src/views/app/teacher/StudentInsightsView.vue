<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const classroomId = ref<number | null>(null);
const studentId = ref<number | null>(null);
const classrooms = computed(() => session.dashboard?.classrooms || []);
const selectedClassroom = computed(() => classrooms.value.find((room) => room.id === classroomId.value));
const classroomOptions = computed(() => classrooms.value.map((room) => ({ label: room.name, value: room.id, hint: room.subject.name })));
const studentOptions = computed(() => (selectedClassroom.value?.students || []).map((student) => ({ label: student.name, value: student.id })));

onMounted(async () => {
  await session.loadDashboard();
  if (classrooms.value.length) classroomId.value = classrooms.value[0].id;
});

watch(classroomId, (id) => {
  studentId.value = selectedClassroom.value?.students[0]?.id ?? null;
  if (id && studentId.value) void session.loadStudentInsights(id, studentId.value);
});
watch(studentId, (id) => {
  if (classroomId.value && id) { void session.loadStudentInsights(classroomId.value, id); void session.loadTeacherConfusionMap(classroomId.value, id); }
});

const mastery = (value: number) => `${Math.round(value * 100)}%`;
const tone = (value: number) => value >= 0.8 ? "success" : value >= 0.6 ? "warning" : "danger";
const riskList = computed(() => [...(session.studentInsights?.concepts || [])].filter((item) => item.forecast_risk !== null).sort((a, b) => (b.forecast_risk || 0) - (a.forecast_risk || 0)).slice(0, 4));
const conceptById = computed(() => new Map((session.teacherConfusionMap?.nodes || []).map((node) => [node.concept_id, node])));
const dependencyRows = computed(() => (session.teacherConfusionMap?.edges || [])
  .map((edge) => ({
    prerequisite: conceptById.value.get(edge.prerequisite_concept_id),
    concept: conceptById.value.get(edge.concept_id),
  }))
  .filter((row) => row.prerequisite && row.concept)
  .sort((a, b) => (a.prerequisite?.effective_mastery || 0) - (b.prerequisite?.effective_mastery || 0)));
const readinessText = (value: number) => value >= 0.8 ? "Ready" : value >= 0.6 ? "Review soon" : "Needs support";
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Teaching" title="Student insights" subtitle="Review each learner's strongest concepts, gaps, and forecast risk before planning support." />

    <div class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 md:grid-cols-2">
      <SCombobox v-model="classroomId" label="Classroom" placeholder="Choose classroom" :options="classroomOptions" />
      <SCombobox v-model="studentId" label="Student" placeholder="Choose student" :options="studentOptions" />
    </div>

    <SLoadingState v-if="session.loading === 'student-insights'" :rows="3" />
    <template v-else-if="session.studentInsights">
      <div class="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <section class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="s-eyebrow">{{ selectedClassroom?.name || "Classroom" }}</p>
              <h2 class="mt-1 font-display text-3xl font-semibold text-ink-900">{{ session.studentInsights.student_name }}</h2>
              <p class="mt-2 text-sm text-ink-500">Current learning profile for topic support and lesson planning.</p>
            </div>
            <RouterLink :to="`/app/students/${session.studentInsights.student_id}`" class="text-sm font-semibold text-primary-700 hover:underline">Open learner record</RouterLink>
          </div>
          <div class="mt-5 grid gap-3 sm:grid-cols-3">
            <div class="rounded-md border border-hairline bg-paper p-4">
              <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Average mastery</p>
              <p class="mt-2 font-display text-3xl font-semibold text-ink-900">{{ mastery(session.studentInsights.average_effective_mastery) }}</p>
            </div>
            <div class="rounded-md border border-hairline bg-paper p-4">
              <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Strong topics</p>
              <p class="mt-2 font-display text-3xl font-semibold text-ink-900">{{ session.studentInsights.strengths.length }}</p>
            </div>
            <div class="rounded-md border border-hairline bg-paper p-4">
              <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Support topics</p>
              <p class="mt-2 font-display text-3xl font-semibold text-ink-900">{{ session.studentInsights.weaknesses.length }}</p>
            </div>
          </div>
        </section>
        <section class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Today focus</p>
          <div v-if="session.studentInsights.weaknesses.length" class="mt-4 space-y-3">
            <div v-for="item in session.studentInsights.weaknesses" :key="item.concept_id" class="rounded-md border border-hairline bg-paper p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-semibold text-ink-900">{{ item.title }}</p>
                  <p class="text-xs text-ink-500">{{ item.chapter_title }}</p>
                </div>
                <SBadge :tone="tone(item.effective_mastery)">{{ readinessText(item.effective_mastery) }}</SBadge>
              </div>
              <div class="mt-3 h-2 rounded-full bg-hairline">
                <div class="h-2 rounded-full bg-primary-700" :style="{ width: mastery(item.effective_mastery) }" />
              </div>
            </div>
          </div>
          <p v-else class="mt-4 text-sm text-ink-500">No weak topic is currently flagged for this learner.</p>
        </section>
      </div>
      <div class="grid gap-5 lg:grid-cols-2">
        <section class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Strengths</p>
          <ul class="mt-4 space-y-3"><li v-for="item in session.studentInsights.strengths" :key="item.concept_id" class="flex items-center justify-between gap-3"><span><b class="block text-sm text-ink-900">{{ item.title }}</b><span class="text-xs text-ink-500">{{ item.chapter_title }}</span></span><SBadge :tone="tone(item.effective_mastery)">{{ mastery(item.effective_mastery) }}</SBadge></li></ul>
        </section>
        <section class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Needs attention</p>
          <ul class="mt-4 space-y-3"><li v-for="item in session.studentInsights.weaknesses" :key="item.concept_id" class="flex items-center justify-between gap-3"><span><b class="block text-sm text-ink-900">{{ item.title }}</b><span class="text-xs text-ink-500">{{ item.chapter_title }}<template v-if="item.forecast_risk"> | forecast risk {{ mastery(item.forecast_risk) }}</template></span></span><SBadge :tone="tone(item.effective_mastery)">{{ mastery(item.effective_mastery) }}</SBadge></li></ul>
        </section>
      </div>
      <div class="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <section class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Prerequisite readiness</p>
          <p class="mt-1 text-sm text-ink-500">Foundations are listed beside the concepts they support, sorted by weakest prerequisite first.</p>
          <div v-if="dependencyRows.length" class="mt-4 divide-y divide-hairline">
            <div v-for="row in dependencyRows" :key="`${row.prerequisite?.concept_id}-${row.concept?.concept_id}`" class="grid gap-3 py-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Foundation</p>
                <div class="mt-2 flex items-center justify-between gap-3">
                  <div>
                    <p class="font-semibold text-ink-900">{{ row.prerequisite?.title }}</p>
                    <p class="text-xs text-ink-500">{{ row.prerequisite?.chapter_title }}</p>
                  </div>
                  <SBadge :tone="tone(row.prerequisite?.effective_mastery || 0)">{{ mastery(row.prerequisite?.effective_mastery || 0) }}</SBadge>
                </div>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Supports</p>
                <div class="mt-2 flex items-center justify-between gap-3">
                  <div>
                    <p class="font-semibold text-ink-900">{{ row.concept?.title }}</p>
                    <p class="text-xs text-ink-500">{{ row.concept?.chapter_title }}</p>
                  </div>
                  <SBadge :tone="tone(row.concept?.effective_mastery || 0)">{{ readinessText(row.concept?.effective_mastery || 0) }}</SBadge>
                </div>
              </div>
            </div>
          </div>
          <p v-else class="mt-4 text-sm text-ink-500">No prerequisite links are available for this learner yet.</p>
        </section>
        <section class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Forecast risk</p>
          <div v-if="riskList.length" class="mt-4 space-y-4">
            <div v-for="item in riskList" :key="item.concept_id">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-semibold text-ink-900">{{ item.title }}</p>
                  <p class="text-xs text-ink-500">{{ item.chapter_title }}</p>
                </div>
                <span class="text-sm font-semibold text-ink-700">{{ mastery(item.forecast_risk || 0) }}</span>
              </div>
              <div class="mt-2 h-2 rounded-full bg-hairline">
                <div class="h-2 rounded-full bg-accent-600" :style="{ width: mastery(item.forecast_risk || 0) }" />
              </div>
            </div>
          </div>
          <p v-else class="mt-4 text-sm text-ink-500">Forecast risk will appear after enough attempts are available.</p>
        </section>
      </div>
    </template>
    <p v-else class="text-sm text-ink-500">Choose a classroom with enrolled students to review progress.</p>
  </div>
</template>
