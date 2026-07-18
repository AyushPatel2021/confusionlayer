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
  if (classroomId.value && id) { void session.loadStudentInsights(classroomId.value, id); void session.loadTeacherConfusionMap(classroomId.value, id); }
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
      <section class="overflow-auto rounded-lg border border-hairline bg-surface p-5"><p class="s-eyebrow">Learner prerequisite map</p><div class="relative mt-4 min-w-[680px]"><svg viewBox="0 0 900 320" class="w-full" aria-label="Learner prerequisite map"><line v-for="edge in session.teacherConfusionMap?.edges || []" :key="`${edge.prerequisite_concept_id}-${edge.concept_id}`" x1="180" y1="160" x2="720" y2="160" stroke="#9ca3af" stroke-width="2" /><g v-for="(item, index) in session.teacherConfusionMap?.nodes || []" :key="item.concept_id" :transform="`translate(${120 + (index % 4) * 220}, ${80 + Math.floor(index / 4) * 150})`"><rect width="180" height="84" rx="6" fill="#fff" :stroke="tone(item.effective_mastery) === 'success' ? '#2f7d69' : tone(item.effective_mastery) === 'warning' ? '#b98222' : '#c65b38'" stroke-width="2"/><text x="90" y="32" text-anchor="middle" class="fill-ink-900 text-sm font-semibold">{{ item.title }}</text><text x="90" y="58" text-anchor="middle" class="fill-ink-500 text-xs">{{ mastery(item.effective_mastery) }} mastery</text></g></svg></div></section>
    </template>
    <p v-else class="text-sm text-ink-500">Choose a classroom with enrolled students to review progress.</p>
  </div>
</template>
