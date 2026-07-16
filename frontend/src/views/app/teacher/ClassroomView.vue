<script setup lang="ts">
import { computed, onMounted } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SErrorState from "../../../components/ui/SErrorState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const syllabus = computed(() => session.syllabus);
const unlockedCount = computed(() => syllabus.value?.chapters.filter((c) => !c.locked).length || 0);

onMounted(() => {
  if (!session.syllabus) void session.loadSyllabus();
});
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Classroom" title="Chapter unlocks" :subtitle="syllabus?.classroom.name">
      <template #actions>
        <SButton variant="secondary" :disabled="!!session.loading" @click="session.loadSyllabus()">Refresh</SButton>
      </template>
    </SPageHeader>

    <SLoadingState v-if="session.loading === 'syllabus' && !syllabus" :rows="3" />
    <SEmptyState
      v-else-if="!syllabus && session.error"
      title="No classroom yet"
      :message="'This workspace has no classroom set up yet. The sample school (from the demo login) shows the full flow.'"
    />
    <div v-else-if="syllabus" class="space-y-5">
      <p class="text-sm text-ink-500">{{ unlockedCount }} of {{ syllabus.chapters.length }} chapters unlocked.</p>
      <section
        v-for="chapter in syllabus.chapters"
        :key="chapter.id"
        class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-hairline bg-surface p-5"
      >
        <div>
          <p class="text-xs font-medium text-ink-500">Chapter {{ chapter.order }} · {{ chapter.concepts.length }} concepts</p>
          <h2 class="font-display text-lg font-semibold text-ink-900">{{ chapter.title }}</h2>
        </div>
        <div class="flex items-center gap-3">
          <SBadge :tone="chapter.locked ? 'neutral' : 'success'">{{ chapter.locked ? "Locked" : "Unlocked" }}</SBadge>
          <SButton
            v-if="chapter.locked"
            variant="primary"
            :disabled="session.loading === `unlock-${chapter.id}`"
            @click="session.unlockChapter(chapter.id)"
          >
            {{ session.loading === `unlock-${chapter.id}` ? "Unlocking…" : "Unlock" }}
          </SButton>
        </div>
      </section>
      <SErrorState v-if="session.error" :message="session.error" />
    </div>
  </div>
</template>
