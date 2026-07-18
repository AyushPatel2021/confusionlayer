<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ChevronDown, ChevronUp } from "@lucide/vue";

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
const expandedChapterIds = ref(new Set<number>());

onMounted(() => {
  if (!session.syllabus) void session.loadSyllabus();
});

function isExpanded(chapterId: number) {
  return expandedChapterIds.value.has(chapterId);
}

function toggleChapter(chapterId: number) {
  const next = new Set(expandedChapterIds.value);
  if (next.has(chapterId)) next.delete(chapterId);
  else next.add(chapterId);
  expandedChapterIds.value = next;
}
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
        class="rounded-lg border border-hairline bg-surface"
      >
        <div class="flex flex-wrap items-center justify-between gap-4 p-5">
          <button class="s-focus flex min-w-0 flex-1 items-center gap-3 text-left" :aria-expanded="isExpanded(chapter.id)" @click="toggleChapter(chapter.id)">
            <component :is="isExpanded(chapter.id) ? ChevronUp : ChevronDown" :size="19" class="shrink-0 text-ink-500" aria-hidden="true" />
            <span class="min-w-0">
              <span class="block text-xs font-medium text-ink-500">Chapter {{ chapter.order }} | {{ chapter.concepts.length }} topics</span>
              <span class="block truncate font-display text-lg font-semibold text-ink-900">{{ chapter.title }}</span>
            </span>
          </button>
          <div class="flex items-center gap-3">
            <SBadge :tone="chapter.locked ? 'neutral' : 'success'">{{ chapter.locked ? "Locked" : "Unlocked" }}</SBadge>
            <SButton
              v-if="chapter.locked"
              variant="primary"
              :disabled="session.loading === `unlock-${chapter.id}`"
              @click="session.unlockChapter(chapter.id)"
            >
              {{ session.loading === `unlock-${chapter.id}` ? "Unlocking..." : "Unlock chapter" }}
            </SButton>
          </div>
        </div>
        <div v-if="isExpanded(chapter.id)" class="border-t border-hairline bg-paper px-5 py-4">
          <p class="text-xs font-medium text-ink-500">Topics in this chapter</p>
          <ul class="mt-3 grid gap-2 sm:grid-cols-2">
            <li v-for="concept in chapter.concepts" :key="concept.id" class="flex items-center justify-between gap-3 rounded-md border border-hairline bg-surface px-3 py-2.5 text-sm">
              <span class="font-medium text-ink-800">{{ concept.order }}. {{ concept.title }}</span>
              <SBadge :tone="chapter.locked ? 'neutral' : 'success'">{{ chapter.locked ? "Locked" : "Ready" }}</SBadge>
            </li>
          </ul>
          <p v-if="chapter.locked" class="mt-3 text-sm text-ink-500">Unlocking this chapter makes every listed topic available to students.</p>
        </div>
      </section>
      <SErrorState v-if="session.error" :message="session.error" />
    </div>
  </div>
</template>
