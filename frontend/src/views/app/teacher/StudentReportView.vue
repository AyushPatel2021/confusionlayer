<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";
const session = useSessionStore(); const route = useRoute();
const id = computed(() => Number(route.params.studentId));
function load() { if (id.value) void session.loadStudentReport(id.value); }
onMounted(load); watch(id, load);
const percent = (value: number) => `${Math.round(value * 100)}%`;
</script>
<template>
  <div class="space-y-8"><SPageHeader eyebrow="Learner record" :title="session.studentReport?.student_name || 'Student record'" subtitle="Learning progress, attendance, and fee position in one place." />
    <SLoadingState v-if="session.loading === 'student-report'" :rows="4" />
    <template v-else-if="session.studentReport">
      <div class="grid gap-4 sm:grid-cols-3"><section class="rounded-lg border border-hairline bg-surface p-5"><p class="s-eyebrow">Average mastery</p><p class="mt-2 font-display text-3xl text-ink-900">{{ percent(session.studentReport.learning.reduce((sum, row) => sum + row.mastery, 0) / Math.max(1, session.studentReport.learning.length)) }}</p></section><section class="rounded-lg border border-hairline bg-surface p-5"><p class="s-eyebrow">Outstanding fees</p><p class="mt-2 font-display text-3xl text-ink-900">₹{{ (session.studentReport.fees.outstanding_cents / 100).toLocaleString('en-IN') }}</p></section><section class="rounded-lg border border-hairline bg-surface p-5"><p class="s-eyebrow">Attendance records</p><p class="mt-2 font-display text-3xl text-ink-900">{{ Object.values(session.studentReport.attendance).reduce((sum, count) => sum + count, 0) }}</p></section></div>
      <section v-if="Object.values(session.studentReport.profile).some(Boolean)" class="rounded-lg border border-hairline bg-surface p-5"><p class="s-eyebrow">Student details</p><dl class="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4"><div v-if="session.studentReport.profile.roll_number"><dt class="text-ink-500">Roll number</dt><dd class="font-medium text-ink-900">{{ session.studentReport.profile.roll_number }}</dd></div><div v-if="session.studentReport.profile.section"><dt class="text-ink-500">Section</dt><dd class="font-medium text-ink-900">{{ session.studentReport.profile.section }}</dd></div><div v-if="session.studentReport.profile.guardian_name"><dt class="text-ink-500">Guardian</dt><dd class="font-medium text-ink-900">{{ session.studentReport.profile.guardian_name }}</dd></div><div v-if="session.studentReport.profile.guardian_phone"><dt class="text-ink-500">Guardian phone</dt><dd class="font-medium text-ink-900">{{ session.studentReport.profile.guardian_phone }}</dd></div></dl></section>
      <section class="overflow-hidden rounded-lg border border-hairline bg-surface"><div class="border-b border-hairline p-5"><p class="s-eyebrow">Learning record</p></div><div class="divide-y divide-hairline"><div v-for="row in session.studentReport.learning" :key="`${row.chapter}-${row.concept}`" class="flex items-center justify-between gap-4 p-4"><span><b class="block text-sm text-ink-900">{{ row.concept }}</b><span class="text-xs text-ink-500">{{ row.chapter }}</span></span><span class="text-sm font-semibold text-ink-900">{{ percent(row.mastery) }}</span></div></div></section>
    </template><p v-else class="text-sm text-ink-500">No learner record is available.</p></div>
</template>
