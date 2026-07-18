<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import SBadge from "../../../components/ui/SBadge.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";
const session = useSessionStore();
onMounted(() => { if (!session.progress) void session.loadProgress(); });
const concepts = computed(() => [...(session.progress?.concepts || [])].sort((a, b) => a.effective_mastery - b.effective_mastery).slice(0, 5));
</script>
<template><div class="space-y-8"><SPageHeader eyebrow="Exam mode" title="Practice exam concepts" subtitle="Work through your highest-priority concepts under exam conditions. Attempts are recorded separately from normal practice."/><SLoadingState v-if="session.loading === 'progress'" :rows="3"/><div v-else class="grid gap-4 lg:grid-cols-2"><article v-for="(concept, index) in concepts" :key="concept.concept_id" class="rounded-lg border border-hairline bg-surface p-5"><div class="flex items-start justify-between gap-3"><div><p class="s-eyebrow">Question {{ index + 1 }}</p><h2 class="mt-2 font-display text-xl font-semibold text-ink-900">{{ concept.concept_title }}</h2><p class="mt-1 text-sm text-ink-500">{{ concept.chapter_title }}</p></div><SBadge :tone="concept.effective_mastery < .6 ? 'danger' : 'warning'">{{ Math.round(concept.effective_mastery * 100) }}% mastery</SBadge></div><RouterLink :to="`/app/learn/${concept.concept_id}?tool=quiz&mode=exam`" class="mt-5 inline-block text-sm font-semibold text-primary-700 hover:underline">Start question</RouterLink></article></div><p v-if="!concepts.length" class="text-sm text-ink-500">Complete learning activity first to generate your exam-practice queue.</p></div></template>
