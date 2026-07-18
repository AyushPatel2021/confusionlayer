<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import SBadge from "../../../components/ui/SBadge.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";
const session = useSessionStore();
onMounted(() => { if (!session.progress) void session.loadProgress(); });
const concepts = computed(() => [...(session.progress?.concepts || [])].sort((a, b) => a.effective_mastery - b.effective_mastery));
const state = (value: number): [string, "success" | "warning" | "danger"] => value >= .8 ? ["Mastered", "success"] : value >= .6 ? ["Fading", "warning"] : ["At risk", "danger"];
</script>
<template><div class="space-y-8"><SPageHeader eyebrow="ConfusionLayer" title="Your confusion map" subtitle="Your persistent concept map, based on mastery and time since review." /><SLoadingState v-if="session.loading === 'progress'" :rows="4" /><div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><article v-for="concept in concepts" :key="concept.concept_id" class="rounded-lg border border-hairline bg-surface p-5"><div class="flex items-start justify-between gap-3"><div><p class="text-xs text-ink-500">{{ concept.chapter_title }}</p><h2 class="mt-1 font-display text-lg font-semibold text-ink-900">{{ concept.concept_title }}</h2></div><SBadge :tone="state(concept.effective_mastery)[1]">{{ state(concept.effective_mastery)[0] }}</SBadge></div><div class="mt-5 h-2 overflow-hidden rounded bg-surface-sunken"><div class="h-full bg-primary-600" :style="{ width: `${Math.round(concept.effective_mastery * 100)}%` }" /></div><div class="mt-3 flex items-center justify-between text-sm"><span class="font-semibold text-ink-900">{{ Math.round(concept.effective_mastery * 100) }}% mastery</span><RouterLink :to="`/app/learn/${concept.concept_id}`" class="font-semibold text-primary-700 hover:underline">Review</RouterLink></div></article></div></div></template>
