<script setup lang="ts">
import { computed } from "vue";

import { useSessionStore } from "../stores/session";

const session = useSessionStore();

const brief = computed(() => session.confusionBrief);
const isLoading = computed(() => session.loading === "confusion-brief");

function sharePct(count: number, total: number) {
  if (total === 0) return 0;
  return Math.round((count / total) * 100);
}
</script>

<template>
  <div class="panel">
    <div>
      <p class="eyebrow">Reactive · aggregated</p>
      <h2 class="panel-title">Confusion Brief</h2>
      <p class="mt-1 text-sm text-slate-600">
        Misconceptions students have actually shown, grouped by concept. Only patterns shared by
        {{ brief?.privacy_threshold ?? 3 }}+ students are shown — never individual names.
      </p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading && !brief" class="mt-5 space-y-3">
      <div v-for="n in 3" :key="n" class="skeleton-card" />
    </div>

    <!-- Empty -->
    <div v-else-if="brief && brief.concepts.length === 0" class="mt-5 empty-tool">
      No shared misconceptions yet. Once at least {{ brief.privacy_threshold }} students make the same mistake on a
      concept, it will appear here as an actionable pattern.
    </div>

    <!-- Data -->
    <div v-else-if="brief" class="mt-5 space-y-4">
      <p class="text-xs text-slate-500">
        {{ brief.total_students }} students · privacy threshold {{ brief.privacy_threshold }}+ students per pattern
      </p>

      <article v-for="concept in brief.concepts" :key="concept.concept_id" class="tutorial-band">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="text-xs font-medium text-slate-500">{{ concept.chapter_title }}</p>
            <h3 class="text-lg font-semibold text-slate-950">{{ concept.concept_title }}</h3>
          </div>
          <span class="badge-muted">{{ concept.affected_student_count }} of {{ brief.total_students }} affected</span>
        </div>

        <ul class="mt-3 space-y-3">
          <li v-for="item in concept.misconceptions" :key="item.code" class="border border-slate-200 bg-white p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <p class="text-xs font-semibold text-emerald-800">{{ item.code }}</p>
              <span class="text-xs text-slate-500">{{ item.student_count }} students · {{ sharePct(item.student_count, brief.total_students) }}%</span>
            </div>
            <p class="mt-1 text-sm leading-6 text-slate-700">{{ item.description }}</p>
          </li>
        </ul>

        <div class="mt-4">
          <button
            class="btn-primary"
            :disabled="!!session.loading"
            @click="session.generateConfusionNarrative(concept.concept_id)"
          >
            {{ session.loading === `confusion-narrative-${concept.concept_id}` ? "Writing brief" : "Generate teaching brief" }}
          </button>
          <div v-if="session.confusionNarratives[concept.concept_id]" class="mt-3 border border-slate-200 bg-white p-4">
            <p class="text-sm leading-6 text-slate-800">{{ session.confusionNarratives[concept.concept_id].summary }}</p>
            <p class="mt-2 text-sm font-semibold text-slate-950">
              {{ session.confusionNarratives[concept.concept_id].suggested_activity }}
            </p>
          </div>
        </div>
      </article>
    </div>

    <!-- Pre-load prompt -->
    <div v-else class="mt-5 empty-tool">Loading confusion brief…</div>
  </div>
</template>
