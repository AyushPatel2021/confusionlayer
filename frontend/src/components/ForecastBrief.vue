<script setup lang="ts">
import { computed } from "vue";

import SBadge from "./ui/SBadge.vue";
import SButton from "./ui/SButton.vue";
import SEmptyState from "./ui/SEmptyState.vue";
import SLoadingState from "./ui/SLoadingState.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const brief = computed(() => session.forecastBrief);
const isLoading = computed(() => session.loading === "forecast-brief" || session.loading === "recompute");

function riskTone(atRisk: number, total: number) {
  if (total === 0) return "neutral" as const;
  const ratio = atRisk / total;
  if (ratio >= 0.5) return "danger" as const;
  if (ratio > 0) return "warning" as const;
  return "success" as const;
}
function riskLabel(atRisk: number, total: number) {
  if (total === 0) return "No students";
  const ratio = atRisk / total;
  return ratio >= 0.5 ? "High risk" : ratio > 0 ? "Some risk" : "On track";
}
const p = (v: number) => Math.round(v * 100);
</script>

<template>
  <div>
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="s-eyebrow">Predictive · pre-lesson</p>
        <p class="mt-1 text-sm text-ink-600">Which upcoming concepts the class will struggle with — before you teach them.</p>
      </div>
      <SButton variant="secondary" :disabled="!!session.loading" @click="session.recomputeForecasts()">
        {{ session.loading === "recompute" ? "Recomputing…" : "Recompute" }}
      </SButton>
    </div>

    <SLoadingState v-if="isLoading && !brief" class="mt-5" :rows="3" />
    <SEmptyState
      v-else-if="brief && brief.concepts.length === 0"
      class="mt-5"
      title="No forecasts yet"
      message="Once mastery data exists for upcoming chapters, press Recompute to predict where the class will struggle."
    />
    <div v-else-if="brief" class="mt-5 space-y-4">
      <p class="text-xs text-ink-500">
        {{ brief.total_students }} students · threshold {{ p(brief.at_risk_threshold) }}%
        <span v-if="brief.computed_at"> · computed {{ new Date(brief.computed_at).toLocaleString() }}</span>
      </p>
      <article v-for="c in brief.concepts" :key="c.concept_id" class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="text-xs font-medium text-ink-500">{{ c.chapter_title }}</p>
            <h3 class="font-display text-lg font-semibold text-ink-900">{{ c.concept_title }}</h3>
          </div>
          <SBadge :tone="riskTone(c.at_risk_count, c.total_students)">{{ riskLabel(c.at_risk_count, c.total_students) }}</SBadge>
        </div>
        <p class="mt-3 text-sm text-ink-700">
          <span class="font-semibold text-ink-900">{{ c.at_risk_count }} of {{ c.total_students }}</span>
          predicted to struggle · avg difficulty {{ p(c.average_difficulty) }}%
        </p>
        <div class="mt-2 h-2 w-full overflow-hidden rounded-sm bg-surface-sunken">
          <div class="h-full rounded-sm bg-accent-600" :style="{ width: `${p(c.average_difficulty)}%` }" />
        </div>
        <div v-if="c.top_contributors.length" class="mt-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Weak prerequisites driving this</p>
          <ul class="mt-2 space-y-1">
            <li v-for="con in c.top_contributors" :key="con.concept_id" class="flex items-center justify-between gap-3 text-sm text-ink-700">
              <span>{{ con.title }}</span>
              <span class="text-xs text-ink-500">avg mastery {{ p(con.average_effective_mastery) }}% · {{ con.mention_count }} students</span>
            </li>
          </ul>
        </div>
        <div class="mt-4">
          <SButton variant="primary" :disabled="!!session.loading" @click="session.generateForecastNarrative(c.concept_id)">
            {{ session.loading === `forecast-narrative-${c.concept_id}` ? "Writing brief…" : "Generate teaching brief" }}
          </SButton>
          <div v-if="session.forecastNarratives[c.concept_id]" class="mt-3 rounded-md border border-hairline bg-paper p-4">
            <p class="text-sm leading-6 text-ink-800">{{ session.forecastNarratives[c.concept_id].summary }}</p>
            <p class="mt-2 text-sm font-semibold text-ink-900">{{ session.forecastNarratives[c.concept_id].suggested_activity }}</p>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
