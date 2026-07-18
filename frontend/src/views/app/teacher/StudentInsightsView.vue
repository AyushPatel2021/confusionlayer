<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const classroomId = ref<number | null>(null);
const studentId = ref<number | null>(null);
const classrooms = computed(() => session.dashboard?.classrooms || []);
const selectedClassroom = computed(() => classrooms.value.find((room) => room.id === classroomId.value));

onMounted(async () => {
  await session.loadDashboard();
  if (classrooms.value.length) classroomId.value = classrooms.value[0].id;
});

watch(classroomId, (id) => {
  studentId.value = selectedClassroom.value?.students[0]?.id ?? null;
  if (id && studentId.value) void session.loadStudentInsights(id, studentId.value);
});
watch(studentId, (id) => {
  if (classroomId.value && id) void session.loadStudentInsights(classroomId.value, id);
});

const mastery = (value: number) => `${Math.round(value * 100)}%`;
const tone = (value: number) => value >= 0.8 ? "success" : value >= 0.6 ? "warning" : "danger";
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Teaching" title="Student insights" subtitle="Review each learner's strongest concepts, gaps, and forecast risk before planning support." />

    <div class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 md:grid-cols-2">
      <label class="text-sm">Classroom
        <select v-model="classroomId" class="s-input mt-1">
          <option v-for="room in classrooms" :key="room.id" :value="room.id">{{ room.name }}</option>
        </select>
      </label>
      <label class="text-sm">Student
        <select v-model="studentId" class="s-input mt-1">
          <option v-for="student in selectedClassroom?.students || []" :key="student.id" :value="student.id">{{ student.name }}</option>
        </select>
      </label>
    </div>

    <SLoadingState v-if="session.loading === 'student-insights'" :rows="3" />
    <template v-else-if="session.studentInsights">
      <div class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex items-start justify-between gap-3"><div><p class="s-eyebrow">{{ session.studentInsights.student_name }}</p>
        <p class="mt-1 font-display text-3xl font-semibold text-ink-900">{{ mastery(session.studentInsights.average_effective_mastery) }} mastery</p>
        </div><RouterLink :to="`/app/students/${session.studentInsights.student_id}`" class="text-sm font-semibold text-primary-700 hover:underline">Open learner record</RouterLink></div>
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
      <section class="rounded-lg border border-hairline bg-surface p-5"><p class="s-eyebrow">Learner map</p><div class="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-3"><div v-for="item in session.studentInsights.concepts" :key="item.concept_id" class="rounded-md border border-hairline p-3"><p class="truncate text-sm font-semibold text-ink-900">{{ item.title }}</p><p class="mt-2 text-xs text-ink-500">{{ item.chapter_title }}</p><div class="mt-3 h-2 overflow-hidden rounded bg-surface-sunken"><div class="h-full bg-primary-600" :style="{ width: `${Math.round(item.effective_mastery * 100)}%` }" /></div><p class="mt-2 text-xs font-semibold text-ink-700">{{ mastery(item.effective_mastery) }} mastery</p></div></div></section>
    </template>
    <p v-else class="text-sm text-ink-500">Choose a classroom with enrolled students to review progress.</p>
  </div>
</template>
