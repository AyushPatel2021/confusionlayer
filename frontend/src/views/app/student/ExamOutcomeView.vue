<script setup lang="ts">
import { onMounted } from "vue";
import { RouterLink } from "vue-router";
import SBadge from "../../../components/ui/SBadge.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";
const session = useSessionStore(); onMounted(() => void session.loadExamOutcome());
</script>
<template><div class="space-y-8"><SPageHeader eyebrow="ConfusionLayer" title="Exam outlook" :subtitle="`${session.examOutcome?.days_to_exam ?? '...'} days until the next March board exam`"/><SLoadingState v-if="session.loading === 'exam-outcome'" :rows="3"/><div v-else class="space-y-3"><article v-for="(item, index) in session.examOutcome?.outcomes || []" :key="item.concept_id" class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-hairline bg-surface p-5"><div><p class="text-xs text-ink-500">{{ index + 1 }} | {{ item.chapter_title }}</p><h2 class="mt-1 font-display text-lg font-semibold">{{ item.title }}</h2><p class="mt-1 text-sm text-ink-600">{{ Math.round(item.risk * 100) }}% forecast risk | {{ Math.round(item.effective_mastery * 100) }}% current mastery</p></div><div class="flex gap-2"><RouterLink :to="`/app/learn/${item.concept_id}`" class="text-sm font-semibold text-primary-700 hover:underline">Start drill</RouterLink><RouterLink :to="{ path: `/app/learn/${item.concept_id}`, query: { tool: 'teach_back' } }" class="text-sm font-semibold text-primary-700 hover:underline">Teach back</RouterLink></div></article><p v-if="!session.examOutcome?.outcomes.length" class="text-sm text-ink-500">No forecast risks yet. Continue learning to build your outlook.</p></div></div></template>
