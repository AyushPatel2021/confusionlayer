<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";
const session = useSessionStore(); const classroomId = ref<number | null>(null); const today = ref(new Date().toISOString().slice(0, 10));
const classrooms = computed(() => session.dashboard?.classrooms || []);
onMounted(async () => { await session.loadDashboard(); classroomId.value = classrooms.value[0]?.id || null; if (classroomId.value) await session.loadAttendance(classroomId.value, today.value); });
watch([classroomId, today], ([id, value]) => { if (id) void session.loadAttendance(id, value); });
async function save() { if (classroomId.value) await session.saveAttendance(classroomId.value, today.value, session.attendance.map((student) => ({ student_id: student.id, status: student.status || 'present', note: student.note }))); }
</script>
<template><div class="space-y-8"><SPageHeader eyebrow="Teaching" title="Attendance" subtitle="Record attendance for a classroom and keep learner records current." /><div class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-2"><label class="text-sm">Classroom<select v-model="classroomId" class="s-input mt-1"><option v-for="room in classrooms" :key="room.id" :value="room.id">{{ room.name }}</option></select></label><label class="text-sm">Date<input v-model="today" type="date" class="s-input mt-1" /></label></div><SLoadingState v-if="session.loading === 'attendance'" :rows="3"/><section v-else class="overflow-hidden rounded-lg border border-hairline bg-surface"><div class="divide-y divide-hairline"><div v-for="student in session.attendance" :key="student.id" class="flex flex-wrap items-center justify-between gap-3 p-4"><b class="text-sm text-ink-900">{{ student.name }}</b><select v-model="student.status" class="s-input w-32"><option value="present">Present</option><option value="absent">Absent</option><option value="late">Late</option><option value="excused">Excused</option></select></div></div><div class="border-t border-hairline p-4"><SButton variant="primary" @click="save">Save attendance</SButton></div></section></div></template>
