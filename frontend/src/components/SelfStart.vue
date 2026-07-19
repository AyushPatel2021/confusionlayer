<script setup lang="ts">
import { ref } from "vue";

import SAIWorkingState from "./ui/SAIWorkingState.vue";
import SButton from "./ui/SButton.vue";
import STutorialVisual from "./ui/STutorialVisual.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const topic = ref("");

async function submit() {
  await session.generateSelfStart(topic.value);
}
</script>

<template>
  <div>
    <p class="s-eyebrow">Explore | outside the syllabus</p>
    <p class="mt-2 text-sm leading-6 text-ink-600">
      Curious about something not yet unlocked? Generate a tutorial for any topic, pitched to your level. This is
      exploration only; it doesn't affect your class progress.
    </p>

    <form class="mt-5 flex flex-col gap-3 md:flex-row" @submit.prevent="submit">
      <input v-model="topic" class="s-input" placeholder="e.g. How do black holes form?" :disabled="!!session.loading" />
      <SButton type="submit" variant="primary" :disabled="!!session.loading || !topic.trim()">
        {{ session.loading === "self-start" ? "Building tutorial..." : "Generate" }}
      </SButton>
    </form>

    <SAIWorkingState
      v-if="session.loading === 'self-start'"
      class="mt-5"
      title="Building an original tutorial"
      message="Codex is pitching the topic to your level and keeping it separate from class progress."
      detail="The tutorial will appear below with an explanation, analogy, worked example, and visual."
    />

    <div v-else-if="session.selfStartTutorial" class="mt-5 space-y-4">
      <div class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Explanation</p>
        <p class="mt-3 whitespace-pre-line text-base leading-8 text-ink-800">{{ session.selfStartTutorial.explanation }}</p>
      </div>
      <div v-if="session.selfStartTutorial.analogy" class="rounded-lg border border-accent-600/30 bg-accent-100/40 p-5">
        <p class="s-eyebrow">Think of it like...</p>
        <p class="mt-3 whitespace-pre-line text-base leading-7 text-ink-800">{{ session.selfStartTutorial.analogy }}</p>
      </div>
      <div class="grid gap-4 xl:grid-cols-2">
        <div class="rounded-lg border border-hairline bg-surface p-5">
          <p class="s-eyebrow">Worked example</p>
          <p class="mt-3 whitespace-pre-line text-base leading-8 text-ink-800">{{ session.selfStartTutorial.worked_example }}</p>
        </div>
        <STutorialVisual :visual="session.selfStartTutorial.visual" />
      </div>
    </div>

    <div v-else class="mt-5 rounded-md border border-dashed border-hairline bg-surface px-4 py-10 text-center text-sm text-ink-500">
      Enter any topic above to generate an original tutorial.
    </div>
  </div>
</template>
