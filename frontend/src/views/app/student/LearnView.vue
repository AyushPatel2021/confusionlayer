<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SErrorState from "../../../components/ui/SErrorState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const syllabus = computed(() => session.syllabus);

onMounted(() => {
  if (!session.syllabus) void session.loadSyllabus();
});
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Your syllabus" title="Learn" :subtitle="syllabus?.classroom.name" />

    <SLoadingState v-if="session.loading === 'syllabus' && !syllabus" :rows="3" />
    <SErrorState v-else-if="session.error && !syllabus" :message="session.error" @retry="session.loadSyllabus()" />
    <SEmptyState
      v-else-if="syllabus && syllabus.chapters.length === 0"
      title="No chapters yet"
      message="Your teacher hasn't set up any chapters. Check back once your classroom is ready."
    />

    <div v-else-if="syllabus" class="space-y-5">
      <section
        v-for="chapter in syllabus.chapters"
        :key="chapter.id"
        class="rounded-lg border border-hairline bg-surface p-6"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-medium text-ink-500">Chapter {{ chapter.order }}</p>
            <h2 class="font-display text-xl font-semibold text-ink-900">{{ chapter.title }}</h2>
          </div>
          <SBadge :tone="chapter.locked ? 'neutral' : 'success'">{{ chapter.locked ? "Locked" : "Unlocked" }}</SBadge>
        </div>

        <p v-if="chapter.locked" class="mt-4 text-sm text-ink-500">
          This chapter unlocks when your teacher covers it in class.
        </p>
        <div v-else class="mt-4 grid gap-2 sm:grid-cols-2">
          <RouterLink
            v-for="concept in chapter.concepts"
            :key="concept.id"
            :to="`/app/learn/${concept.id}`"
            class="card-lift group flex items-center justify-between rounded-md border border-hairline bg-paper px-4 py-3 text-sm font-medium text-ink-800"
          >
            <span>{{ concept.title }}</span>
            <span class="text-primary-600">Open</span>
          </RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>
