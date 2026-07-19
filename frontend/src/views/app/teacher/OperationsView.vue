<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const timetable = ref({ classroom_id: null as number | null, weekday: 0, starts_at: "09:00", ends_at: "10:00", room: "" });
const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const classroomOptions = computed(() => session.classrooms.map((room) => ({ label: room.name, value: room.id, hint: room.subject.name })));
const dayOptions = computed(() => days.map((day, index) => ({ label: day, value: index })));
const timetableByDay = computed(() => days.map((day, index) => ({
  day,
  entries: session.timetable.filter((entry) => entry.weekday === index).sort((a, b) => `${a.starts_at}${a.ends_at}`.localeCompare(`${b.starts_at}${b.ends_at}`)),
})));
const totalLessons = computed(() => session.timetable.length);
const activeDays = computed(() => timetableByDay.value.filter((day) => day.entries.length).length);
const busiestDay = computed(() => {
  const sorted = [...timetableByDay.value].sort((a, b) => b.entries.length - a.entries.length);
  return sorted[0]?.entries.length ? sorted[0].day : "None";
});

onMounted(async () => {
  await session.loadClassrooms();
  timetable.value.classroom_id = session.classrooms[0]?.id || null;
  await session.loadOperations();
});

async function addTimetable() {
  if (!timetable.value.classroom_id) return;
  await session.createTimetable({ ...timetable.value, classroom_id: timetable.value.classroom_id, room: timetable.value.room.trim() || undefined });
  timetable.value = { ...timetable.value, starts_at: "09:00", ends_at: "10:00", room: "" };
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="School office" title="Timetable" subtitle="Plan the teaching week by day, time, classroom, and room." />

    <div class="grid gap-4 sm:grid-cols-3">
      <article class="rounded-lg border border-hairline bg-surface p-4">
        <p class="text-xs font-medium text-ink-500">Lessons</p>
        <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ totalLessons }}</p>
      </article>
      <article class="rounded-lg border border-hairline bg-surface p-4">
        <p class="text-xs font-medium text-ink-500">Active days</p>
        <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ activeDays }}</p>
      </article>
      <article class="rounded-lg border border-hairline bg-surface p-4">
        <p class="text-xs font-medium text-ink-500">Busiest day</p>
        <p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ busiestDay }}</p>
      </article>
    </div>

    <form class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 lg:grid-cols-[minmax(0,1.5fr)_140px_120px_120px_minmax(0,1fr)_auto]" @submit.prevent="addTimetable">
      <SCombobox v-model="timetable.classroom_id" label="Classroom" placeholder="Choose classroom" :options="classroomOptions" />
      <SCombobox v-model="timetable.weekday" label="Day" placeholder="Day" :options="dayOptions" />
      <label class="text-sm">Starts<input v-model="timetable.starts_at" class="s-input mt-1" type="time" required /></label>
      <label class="text-sm">Ends<input v-model="timetable.ends_at" class="s-input mt-1" type="time" required /></label>
      <label class="text-sm">Room<input v-model="timetable.room" class="s-input mt-1" placeholder="Lab 2" /></label>
      <SButton class="self-end" type="submit" variant="primary" :disabled="!timetable.classroom_id || session.loading === 'operations'">Add lesson</SButton>
    </form>

    <SLoadingState v-if="session.loading === 'operations' && !session.timetable.length" :rows="3" />
    <section v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-7">
      <div v-for="day in timetableByDay" :key="day.day" class="min-h-48 rounded-lg border border-hairline bg-surface">
        <div class="flex items-center justify-between border-b border-hairline px-4 py-3">
          <h2 class="font-semibold text-ink-900">{{ day.day }}</h2>
          <SBadge tone="neutral">{{ day.entries.length }}</SBadge>
        </div>
        <div class="space-y-3 p-3">
          <article v-for="entry in day.entries" :key="entry.id" class="rounded-md border border-hairline bg-surface-sunken p-3">
            <p class="text-xs font-semibold text-primary-700">{{ entry.starts_at }} - {{ entry.ends_at }}</p>
            <h3 class="mt-1 text-sm font-semibold text-ink-900">{{ entry.classroom }}</h3>
            <p class="mt-1 text-xs text-ink-500">{{ entry.room || "Room not set" }}</p>
            <div class="mt-3 flex justify-end">
              <SButton variant="ghost" :disabled="session.loading === 'operations'" @click="session.deleteTimetable(entry.id)">Remove</SButton>
            </div>
          </article>
          <p v-if="!day.entries.length" class="rounded-md border border-dashed border-hairline px-3 py-6 text-center text-sm text-ink-500">No lessons</p>
        </div>
      </div>
    </section>

    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>
  </div>
</template>
