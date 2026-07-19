<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SDatePicker from "../../../components/ui/SDatePicker.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore, type AttendanceStudent } from "../../../stores/session";

const session = useSessionStore();
const classroomId = ref<number | null>(null);
const today = ref(new Date().toISOString().slice(0, 10));
const currentIndex = ref(0);
const saved = ref(false);
const statusOptions: Array<{ key: NonNullable<AttendanceStudent["status"]>; label: string; tone: "success" | "warning" | "danger" | "info" }> = [
  { key: "present", label: "Present", tone: "success" },
  { key: "late", label: "Late", tone: "warning" },
  { key: "absent", label: "Absent", tone: "danger" },
  { key: "excused", label: "Excused", tone: "info" },
];

const classrooms = computed(() => session.dashboard?.classrooms || []);
const classroomOptions = computed(() => classrooms.value.map((room) => ({ label: room.name, value: room.id, hint: room.subject.name })));
const students = computed(() => session.attendance);
const currentStudent = computed(() => students.value[currentIndex.value] || null);
const markedCount = computed(() => students.value.filter((student) => student.status).length);
const counts = computed(() => Object.fromEntries(statusOptions.map((option) => [option.key, students.value.filter((student) => student.status === option.key).length])) as Record<NonNullable<AttendanceStudent["status"]>, number>);
const progress = computed(() => students.value.length ? `${Math.round((markedCount.value / students.value.length) * 100)}%` : "0%");

onMounted(async () => {
  await session.loadDashboard();
  classroomId.value = classrooms.value[0]?.id || null;
  if (classroomId.value) await load();
});

watch([classroomId, today], () => {
  currentIndex.value = 0;
  saved.value = false;
  if (classroomId.value) void load();
});

async function load() {
  if (!classroomId.value) return;
  await session.loadAttendance(classroomId.value, today.value);
  currentIndex.value = Math.min(currentIndex.value, Math.max(0, students.value.length - 1));
}

function setStatus(status: NonNullable<AttendanceStudent["status"]>) {
  if (!currentStudent.value) return;
  currentStudent.value.status = status;
  saved.value = false;
  const next = students.value.findIndex((student, index) => index > currentIndex.value && !student.status);
  if (next >= 0) currentIndex.value = next;
}

function markAll(status: NonNullable<AttendanceStudent["status"]>) {
  students.value.forEach((student) => {
    if (!student.status) student.status = status;
  });
  saved.value = false;
}

async function save() {
  if (!classroomId.value) return;
  await session.saveAttendance(classroomId.value, today.value, students.value.map((student) => ({
    student_id: student.id,
    status: student.status || "present",
    note: student.note,
  })));
  saved.value = !session.error;
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Teaching" title="Attendance" subtitle="Take roll-call quickly, in student roll-number order." />

    <div class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 md:grid-cols-[minmax(0,1fr)_240px_auto]">
      <SCombobox v-model="classroomId" label="Classroom" placeholder="Choose classroom" :options="classroomOptions" />
      <SDatePicker v-model="today" label="Date" />
      <SButton class="self-end" variant="secondary" :disabled="!students.length" @click="markAll('present')">Mark remaining present</SButton>
    </div>

    <SLoadingState v-if="session.loading === 'attendance'" :rows="4" />
    <SEmptyState v-else-if="!students.length" title="No students enrolled" message="Enroll students into this classroom before taking attendance." />
    <template v-else>
      <section class="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="s-eyebrow">Roll call</p>
              <h2 class="mt-1 font-display text-3xl font-semibold text-ink-900">{{ currentStudent?.name }}</h2>
              <p class="mt-1 text-sm text-ink-500">
                Roll {{ currentStudent?.roll_number || "not set" }}<template v-if="currentStudent?.section"> · Section {{ currentStudent.section }}</template>
              </p>
            </div>
            <SBadge :tone="currentStudent?.status ? statusOptions.find((option) => option.key === currentStudent?.status)?.tone || 'neutral' : 'neutral'">
              {{ currentStudent?.status || "unmarked" }}
            </SBadge>
          </div>

          <div class="mt-6 grid grid-cols-2 gap-3">
            <button
              v-for="option in statusOptions"
              :key="option.key"
              type="button"
              class="s-focus rounded-md border px-4 py-5 text-left transition hover:border-primary-500 hover:bg-primary-50"
              :class="currentStudent?.status === option.key ? 'border-primary-600 bg-primary-50' : 'border-hairline bg-paper'"
              @click="setStatus(option.key)"
            >
              <span class="block text-lg font-semibold text-ink-900">{{ option.label }}</span>
              <span class="mt-1 block text-xs uppercase tracking-wide text-ink-500">{{ counts[option.key] }} marked</span>
            </button>
          </div>

          <div class="mt-5 flex items-center justify-between gap-3">
            <SButton variant="ghost" :disabled="currentIndex <= 0" @click="currentIndex -= 1">Previous</SButton>
            <span class="text-sm text-ink-500">{{ currentIndex + 1 }} of {{ students.length }}</span>
            <SButton variant="ghost" :disabled="currentIndex >= students.length - 1" @click="currentIndex += 1">Next</SButton>
          </div>
        </div>

        <div class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="s-eyebrow">Class summary</p>
              <p class="mt-1 text-sm text-ink-500">{{ markedCount }} of {{ students.length }} students marked.</p>
            </div>
            <SBadge v-if="saved" tone="success">saved</SBadge>
          </div>
          <div class="mt-4 h-2 rounded-full bg-hairline">
            <div class="h-2 rounded-full bg-primary-600" :style="{ width: progress }" />
          </div>
          <div class="mt-5 grid grid-cols-2 gap-3">
            <div v-for="option in statusOptions" :key="option.key" class="rounded-md border border-hairline bg-paper p-4">
              <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">{{ option.label }}</p>
              <p class="mt-2 font-display text-2xl font-semibold text-ink-900">{{ counts[option.key] }}</p>
            </div>
          </div>
          <div class="mt-5 max-h-72 overflow-auto rounded-md border border-hairline">
            <button
              v-for="(student, index) in students"
              :key="student.id"
              type="button"
              class="flex w-full items-center justify-between gap-3 border-b border-hairline px-4 py-3 text-left text-sm last:border-b-0 hover:bg-primary-50"
              :class="index === currentIndex ? 'bg-primary-50' : 'bg-surface'"
              @click="currentIndex = index"
            >
              <span>
                <span class="font-semibold text-ink-900">{{ student.roll_number || "-" }} · {{ student.name }}</span>
                <span v-if="student.section" class="block text-xs text-ink-500">Section {{ student.section }}</span>
              </span>
              <span class="text-xs font-semibold uppercase tracking-wide text-ink-500">{{ student.status || "unmarked" }}</span>
            </button>
          </div>
          <div class="mt-5 flex justify-end">
            <SButton variant="primary" :disabled="session.loading === 'attendance'" @click="save">Save attendance</SButton>
          </div>
        </div>
      </section>
    </template>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>
  </div>
</template>
