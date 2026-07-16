<script setup lang="ts">
import { ref } from "vue";

import SButton from "./ui/SButton.vue";
import SLoadingState from "./ui/SLoadingState.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const topic = ref("");

async function submit() {
  await session.generateSelfStart(topic.value);
}
</script>

<template>
  <div>
    <p class="s-eyebrow">Explore · outside the syllabus</p>
    <p class="mt-2 text-sm leading-6 text-ink-600">
      Curious about something not yet unlocked? Generate a tutorial for any topic — pitched to your level. This is
      exploration only; it doesn't affect your class progress.
    </p>

    <form class="mt-5 flex flex-col gap-3 md:flex-row" @submit.prevent="submit">
      <input v-model="topic" class="s-input" placeholder="e.g. How do black holes form?" :disabled="!!session.loading" />
      <SButton type="submit" variant="primary" :disabled="!!session.loading || !topic.trim()">
        {{ session.loading === "self-start" ? "Generating…" : "Generate" }}
      </SButton>
    </form>

    <SLoadingState v-if="session.loading === 'self-start'" class="mt-5" :rows="2" />

    <div v-else-if="session.selfStartTutorial" class="mt-5 space-y-4">
      <div class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Explanation</p>
        <p class="mt-3 whitespace-pre-line text-base leading-8 text-ink-800">{{ session.selfStartTutorial.explanation }}</p>
      </div>
      <div v-if="session.selfStartTutorial.analogy" class="rounded-lg border border-accent-600/30 bg-accent-100/40 p-5">
        <p class="s-eyebrow">Think of it like…</p>
        <p class="mt-3 whitespace-pre-line text-base leading-7 text-ink-800">{{ session.selfStartTutorial.analogy }}</p>
      </div>
      <div class="grid gap-4 xl:grid-cols-2">
        <div class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Worked example</p>
          <p class="mt-3 whitespace-pre-line text-base leading-8 text-ink-800">{{ session.selfStartTutorial.worked_example }}</p>
        </div>
        <div v-if="session.selfStartTutorial.visual" class="rounded-lg border border-hairline bg-ink-900 p-5">
          <p class="text-xs font-semibold uppercase tracking-wide text-paper/70">Visual</p>
          <pre class="mt-3 overflow-x-auto whitespace-pre font-mono text-xs leading-5 text-paper">{{ session.selfStartTutorial.visual }}</pre>
        </div>
      </div>
    </div>

    <div v-else class="mt-5 rounded-md border border-dashed border-hairline bg-surface px-4 py-10 text-center text-sm text-ink-500">
      Enter any topic above to generate an original tutorial.
    </div>
  </div>
</template>
