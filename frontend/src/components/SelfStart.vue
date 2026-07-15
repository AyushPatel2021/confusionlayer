<script setup lang="ts">
import { ref } from "vue";

import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const topic = ref("");

async function submit() {
  await session.generateSelfStart(topic.value);
}
</script>

<template>
  <div class="panel">
    <div>
      <p class="eyebrow">Explore · outside the syllabus</p>
      <h2 class="panel-title">Self-Start a Topic</h2>
      <p class="mt-1 text-sm text-slate-600">
        Curious about something not yet unlocked in your class? Generate a tutorial for any topic — pitched to your
        level. This is exploration only; it doesn't affect your class progress.
      </p>
    </div>

    <form class="mt-5 flex flex-col gap-3 md:flex-row" @submit.prevent="submit">
      <input
        v-model="topic"
        class="text-input"
        placeholder="e.g. How do black holes form?"
        :disabled="!!session.loading"
      />
      <button class="btn-primary" :disabled="!!session.loading || !topic.trim()">
        {{ session.loading === "self-start" ? "Generating" : "Generate Tutorial" }}
      </button>
    </form>

    <!-- Loading -->
    <div v-if="session.loading === 'self-start'" class="mt-5 space-y-3">
      <div class="skeleton-card" />
      <div class="skeleton-card" />
    </div>

    <!-- Data -->
    <div v-else-if="session.selfStartTutorial" class="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.8fr)]">
      <div class="tutorial-band">
        <p class="eyebrow">Tutorial</p>
        <p class="mt-3 whitespace-pre-line text-base leading-8 text-slate-800">
          {{ session.selfStartTutorial.explanation }}
        </p>
      </div>
      <div class="tutorial-band">
        <p class="eyebrow">Worked example</p>
        <p class="mt-3 whitespace-pre-line text-base leading-8 text-slate-800">
          {{ session.selfStartTutorial.worked_example }}
        </p>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="mt-5 empty-tool">Enter any topic above to generate an original tutorial.</div>
  </div>
</template>
