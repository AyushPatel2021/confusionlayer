<script setup lang="ts">
import { computed } from "vue";

import { useSessionStore } from "../stores/session";

const session = useSessionStore();

const brief = computed(() => session.forecastBrief);
const isLoading = computed(() => session.loading === "forecast-brief" || session.loading === "recompute");

function riskLabel(atRisk: number, total: number) {
  if (total === 0) return "No students";
  const ratio = atRisk / total;
  if (ratio >= 0.5) return "High risk";
  if (ratio > 0) return "Some risk";
  return "On track";
}

function difficultyPct(value: number) {
  return Math.round(value * 100);
}

function masteryPct(value: number) {
  return Math.round(value * 100);
}
</script>

<template>
  <div class="panel">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="eyebrow">Predictive · pre-lesson</p>
        <h2 class="panel-title">Forecast Brief</h2>
        <p class="mt-1 text-sm text-slate-600">
          Deterministic prediction of which upcoming concepts the class will struggle with, before you teach them.
        </p>
      </div>
      <button class="btn-secondary" :disabled="!!session.loading" @click="session.recomputeForecasts()">
        {{ session.loading === "recompute" ? "Recomputing" : "Recompute" }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading && !brief" class="mt-5 space-y-3">
      <div v-for="n in 3" :key="n" class="skeleton-card" />
    </div>

    <!-- Empty -->
    <div v-else-if="brief && brief.concepts.length === 0" class="mt-5 empty-tool">
      No forecasts yet. Once mastery data exists for upcoming chapters, press “Recompute” to predict where the class will
      struggle before the next lesson.
    </div>

    <!-- Data -->
    <div v-else-if="brief" class="mt-5 space-y-4">
      <p class="text-xs text-slate-500">
        {{ brief.total_students }} students · predicted-difficulty threshold {{ difficultyPct(brief.at_risk_threshold) }}%
        <span v-if="brief.computed_at"> · computed {{ new Date(brief.computed_at).toLocaleString() }}</span>
      </p>

      <article v-for="concept in brief.concepts" :key="concept.concept_id" class="tutorial-band">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="text-xs font-medium text-slate-500">{{ concept.chapter_title }}</p>
            <h3 class="text-lg font-semibold text-slate-950">{{ concept.concept_title }}</h3>
          </div>
          <span :class="concept.at_risk_count / concept.total_students >= 0.5 ? 'badge-muted' : 'badge'">
            {{ riskLabel(concept.at_risk_count, concept.total_students) }}
          </span>
        </div>

        <p class="mt-3 text-sm text-slate-700">
          <span class="font-semibold text-slate-950">{{ concept.at_risk_count }} of {{ concept.total_students }}</span>
          students predicted to struggle · avg difficulty {{ difficultyPct(concept.average_difficulty) }}%
        </p>

        <div class="mt-2 forecast-bar">
          <div class="forecast-bar-fill" :style="{ width: `${difficultyPct(concept.average_difficulty)}%` }" />
        </div>

        <div v-if="concept.top_contributors.length" class="mt-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Weak prerequisites driving this</p>
          <ul class="mt-2 space-y-1">
            <li
              v-for="contributor in concept.top_contributors"
              :key="contributor.concept_id"
              class="flex items-center justify-between gap-3 text-sm text-slate-700"
            >
              <span>{{ contributor.title }}</span>
              <span class="text-xs text-slate-500">
                avg mastery {{ masteryPct(contributor.average_effective_mastery) }}% · {{ contributor.mention_count }} students
              </span>
            </li>
          </ul>
        </div>

        <div class="mt-4">
          <button
            class="btn-primary"
            :disabled="!!session.loading"
            @click="session.generateForecastNarrative(concept.concept_id)"
          >
            {{ session.loading === `forecast-narrative-${concept.concept_id}` ? "Writing brief" : "Generate teaching brief" }}
          </button>
          <div v-if="session.forecastNarratives[concept.concept_id]" class="mt-3 border border-slate-200 bg-white p-4">
            <p class="text-sm leading-6 text-slate-800">{{ session.forecastNarratives[concept.concept_id].summary }}</p>
            <p class="mt-2 text-sm font-semibold text-slate-950">
              {{ session.forecastNarratives[concept.concept_id].suggested_activity }}
            </p>
          </div>
        </div>
      </article>
    </div>

    <!-- Pre-load prompt -->
    <div v-else class="mt-5 empty-tool">Loading forecast brief…</div>
  </div>
</template>
