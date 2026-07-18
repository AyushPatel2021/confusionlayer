<script setup lang="ts">
import { computed } from "vue";

import SBadge from "./ui/SBadge.vue";
import SButton from "./ui/SButton.vue";
import SEmptyState from "./ui/SEmptyState.vue";
import SLoadingState from "./ui/SLoadingState.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const brief = computed(() => session.confusionBrief);
const isLoading = computed(() => session.loading === "confusion-brief");

function sharePct(count: number, total: number) {
  return total === 0 ? 0 : Math.round((count / total) * 100);
}
</script>

<template>
  <div>
    <div>
      <p class="s-eyebrow">Reactive | aggregated</p>
      <p class="mt-1 text-sm text-ink-600">
        Misconceptions students have actually shown, grouped by concept. Only patterns shared by
        {{ brief?.privacy_threshold ?? 3 }}+ students appear, never individual names.
      </p>
    </div>

    <SLoadingState v-if="isLoading && !brief" class="mt-5" :rows="3" />
    <SEmptyState
      v-else-if="brief && brief.concepts.length === 0"
      class="mt-5"
      title="No shared misconceptions yet"
      :message="`Once at least ${brief.privacy_threshold} students make the same mistake on a concept, it appears here as an actionable pattern.`"
    />
    <div v-else-if="brief" class="mt-5 space-y-4">
      <p class="text-xs text-ink-500">{{ brief.total_students }} students | privacy threshold {{ brief.privacy_threshold }}+ per pattern</p>
      <article v-for="c in brief.concepts" :key="c.concept_id" class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="text-xs font-medium text-ink-500">{{ c.chapter_title }}</p>
            <h3 class="font-display text-lg font-semibold text-ink-900">{{ c.concept_title }}</h3>
          </div>
          <SBadge>{{ c.affected_student_count }} of {{ brief.total_students }} affected</SBadge>
        </div>
        <ul class="mt-3 space-y-3">
          <li v-for="item in c.misconceptions" :key="item.code" class="rounded-md border border-hairline bg-paper p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <p class="font-mono text-xs font-semibold text-primary-600">{{ item.code }}</p>
              <span class="text-xs text-ink-500">{{ item.student_count }} students | {{ sharePct(item.student_count, brief.total_students) }}%</span>
            </div>
            <p class="mt-1 text-sm leading-6 text-ink-700">{{ item.description }}</p>
          </li>
        </ul>
        <div class="mt-4">
          <SButton variant="primary" :disabled="!!session.loading" @click="session.generateConfusionNarrative(c.concept_id)">
            {{ session.loading === `confusion-narrative-${c.concept_id}` ? "Writing brief..." : "Generate teaching brief" }}
          </SButton>
          <div v-if="session.confusionNarratives[c.concept_id]" class="mt-3 rounded-md border border-hairline bg-paper p-4">
            <p class="text-sm leading-6 text-ink-800">{{ session.confusionNarratives[c.concept_id].summary }}</p>
            <p class="mt-2 text-sm font-semibold text-ink-900">{{ session.confusionNarratives[c.concept_id].suggested_activity }}</p>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
