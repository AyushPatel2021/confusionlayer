<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SErrorState from "../../../components/ui/SErrorState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const route = useRoute();
const doubtText = ref("");
const quizAnswer = ref("");
const teachBackText = ref("");

const tools = [
  { key: "tutorial", label: "Tutorial" },
  { key: "doubt", label: "Doubt chat" },
  { key: "quiz", label: "Quiz" },
  { key: "teach_back", label: "Teach-back" },
] as const;

const concept = computed(() => session.selectedConcept);

function load() {
  const id = Number(route.params.conceptId);
  if (id) void session.loadConceptById(id);
}
onMounted(load);
watch(() => route.params.conceptId, load);

const quizQuestion = computed(() => `Explain one key idea from ${concept.value?.title || "this concept"} in your own words.`);
const quizRubric = computed(
  () => `A correct answer should accurately describe ${concept.value?.title || "the concept"}, use relevant terms, and avoid the listed misconception patterns.`,
);
const teachBackSummary = computed(() => {
  const title = concept.value?.title || "the concept";
  const taxonomy = concept.value?.taxonomy.map((t) => `${t.code}: ${t.description}`).join("; ") || "the fixed misconception patterns";
  return `A strong explanation of ${title} should define the idea, connect it to the chapter, and avoid: ${taxonomy}`;
});
const turn = computed(() => session.chatMessages.filter((m) => m.role === "student").length + 1);

async function sendDoubt() {
  const message = doubtText.value;
  doubtText.value = "";
  await session.sendDoubt(message);
}
async function submitQuiz() {
  await session.submitQuiz(quizQuestion.value, quizAnswer.value, quizRubric.value);
}
async function submitTeachBack() {
  await session.submitTeachBack(teachBackText.value, teachBackSummary.value);
}
</script>

<template>
  <div class="space-y-6">
    <RouterLink to="/app/learn" class="text-sm font-medium text-primary-600 hover:text-primary-500">← Syllabus</RouterLink>

    <SLoadingState v-if="session.loading === `concept-${route.params.conceptId}` && !concept" :rows="2" />
    <SErrorState v-else-if="!concept && session.error" :message="session.error" @retry="load" />

    <template v-else-if="concept">
      <div class="border-b border-hairline pb-5">
        <p class="s-eyebrow">{{ concept.chapter_title }}</p>
        <h1 class="mt-2 font-display text-3xl font-semibold text-ink-900">{{ concept.title }}</h1>
        <p class="mt-2 text-sm text-ink-500">
          {{ concept.subject.board }} Class {{ concept.subject.class_level }} · {{ concept.subject.name }}
        </p>
      </div>

      <!-- Taxonomy -->
      <section v-if="concept.taxonomy.length">
        <p class="s-eyebrow">Fixed misconception taxonomy</p>
        <div class="mt-3 grid gap-3 md:grid-cols-2">
          <div v-for="item in concept.taxonomy" :key="item.code" class="rounded-md border border-hairline bg-surface p-4">
            <p class="font-mono text-xs font-semibold text-primary-600">{{ item.code }}</p>
            <p class="mt-1 text-sm leading-6 text-ink-700">{{ item.description }}</p>
          </div>
        </div>
      </section>

      <!-- Tool tabs -->
      <nav class="flex flex-wrap gap-2 border-b border-hairline pb-3">
        <button
          v-for="tool in tools"
          :key="tool.key"
          class="s-focus rounded-full px-4 py-1.5 text-sm font-semibold transition"
          :class="session.activeTool === tool.key ? 'bg-primary-600 text-white' : 'border border-hairline bg-surface text-ink-700 hover:border-primary-500'"
          @click="session.activeTool = tool.key"
        >
          {{ tool.label }}
        </button>
      </nav>

      <SErrorState v-if="session.error" :message="session.error" />

      <!-- Tutorial -->
      <section v-if="session.activeTool === 'tutorial'" class="space-y-4">
        <div class="flex items-center justify-between gap-3">
          <p class="s-eyebrow">Tutorial generator</p>
          <SButton variant="primary" :disabled="!!session.loading" @click="session.generateTutorial()">
            {{ session.loading === "tutorial" ? "Generating…" : "Generate tutorial" }}
          </SButton>
        </div>
        <div v-if="session.tutorial" class="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.8fr)]">
          <div class="rounded-lg border border-hairline bg-surface p-5">
            <p class="s-eyebrow">Explanation</p>
            <p class="mt-3 whitespace-pre-line text-base leading-8 text-ink-800">{{ session.tutorial.explanation }}</p>
          </div>
          <div class="rounded-lg border border-hairline bg-surface p-5">
            <p class="s-eyebrow">Worked example</p>
            <p class="mt-3 whitespace-pre-line text-base leading-8 text-ink-800">{{ session.tutorial.worked_example }}</p>
          </div>
        </div>
        <div v-else class="rounded-md border border-dashed border-hairline bg-surface px-4 py-10 text-center text-sm text-ink-500">
          No tutorial generated yet.
        </div>
      </section>

      <!-- Doubt chat -->
      <section v-else-if="session.activeTool === 'doubt'" class="space-y-4">
        <div class="flex items-center justify-between gap-3">
          <p class="s-eyebrow">Progressive scaffolding</p>
          <SBadge>Turn {{ turn }}</SBadge>
        </div>
        <div class="flex min-h-64 flex-col gap-3 rounded-lg border border-hairline bg-surface p-4">
          <p v-if="session.chatMessages.length === 0" class="m-auto text-sm text-ink-500">Ask a question to get a guiding nudge.</p>
          <div
            v-for="(m, i) in session.chatMessages"
            :key="i"
            class="max-w-[88%] rounded-lg px-4 py-3 text-sm leading-6"
            :class="m.role === 'student' ? 'ml-auto bg-primary-600 text-white' : 'mr-auto border border-hairline bg-paper text-ink-800'"
          >
            <p class="text-[11px] font-semibold uppercase tracking-wide" :class="m.role === 'student' ? 'text-white/70' : 'text-accent-600'">
              {{ m.role }}<span v-if="m.response_type"> · {{ m.response_type }}</span>
            </p>
            <p class="mt-1 whitespace-pre-line">{{ m.content }}</p>
          </div>
        </div>
        <form v-if="session.isStudent" class="flex flex-col gap-3 md:flex-row" @submit.prevent="sendDoubt">
          <input v-model="doubtText" class="s-input" placeholder="Ask a doubt about this concept" :disabled="!!session.loading" />
          <SButton type="submit" variant="primary" :disabled="!!session.loading || !doubtText.trim()">
            {{ session.loading === "doubt" ? "Sending…" : "Send" }}
          </SButton>
        </form>
        <p v-else class="text-sm text-ink-500">Sign in as a student to use doubt chat.</p>
      </section>

      <!-- Quiz -->
      <section v-else-if="session.activeTool === 'quiz'" class="space-y-4">
        <div class="grid gap-3 md:grid-cols-2">
          <div class="rounded-md border border-hairline bg-surface p-4">
            <p class="text-xs font-semibold text-ink-500">Question</p>
            <p class="mt-1 text-sm leading-6 text-ink-800">{{ quizQuestion }}</p>
          </div>
          <div class="rounded-md border border-hairline bg-surface p-4">
            <p class="text-xs font-semibold text-ink-500">Rubric</p>
            <p class="mt-1 text-sm leading-6 text-ink-800">{{ quizRubric }}</p>
          </div>
        </div>
        <form class="space-y-3" @submit.prevent="submitQuiz">
          <textarea v-model="quizAnswer" class="s-input min-h-32 py-2" placeholder="Write your answer" :disabled="!!session.loading || !session.isStudent" />
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm text-ink-500">{{ session.isStudent ? "Answer as yourself" : "Students only" }}</p>
            <SButton type="submit" variant="primary" :disabled="!!session.loading || !quizAnswer.trim() || !session.isStudent">
              {{ session.loading === "quiz" ? "Grading…" : "Grade answer" }}
            </SButton>
          </div>
        </form>
        <div v-if="session.quizGrade" class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex flex-wrap items-center gap-2">
            <SBadge :tone="session.quizGrade.is_correct ? 'success' : 'warning'">
              {{ session.quizGrade.is_correct ? "Correct" : "Needs review" }}
            </SBadge>
            <SBadge>Confidence {{ Math.round(session.quizGrade.confidence * 100) }}%</SBadge>
            <SBadge v-if="session.quizGrade.misconception_code" tone="danger">{{ session.quizGrade.misconception_code }}</SBadge>
          </div>
          <p class="mt-3 text-sm leading-6 text-ink-800">{{ session.quizGrade.misconception_summary }}</p>
          <p class="mt-3 text-sm font-semibold text-ink-900">{{ session.quizGrade.follow_up_question }}</p>
        </div>
      </section>

      <!-- Teach-back -->
      <section v-else class="space-y-4">
        <div class="rounded-md border border-hairline bg-surface p-4">
          <p class="s-eyebrow">Teach it back</p>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ teachBackSummary }}</p>
        </div>
        <form class="space-y-3" @submit.prevent="submitTeachBack">
          <textarea v-model="teachBackText" class="s-input min-h-32 py-2" placeholder="Explain this concept in your own words" :disabled="!!session.loading || !session.isStudent" />
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm text-ink-500">{{ session.isStudent ? "Explain as yourself" : "Students only" }}</p>
            <SButton type="submit" variant="primary" :disabled="!!session.loading || !teachBackText.trim() || !session.isStudent">
              {{ session.loading === "teach-back" ? "Grading…" : "Grade teach-back" }}
            </SButton>
          </div>
        </form>
        <div v-if="session.teachBackGrade" class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex flex-wrap items-center gap-2">
            <SBadge>Clarity {{ Math.round(session.teachBackGrade.clarity_score * 100) }}%</SBadge>
            <SBadge>Accuracy {{ Math.round(session.teachBackGrade.accuracy_score * 100) }}%</SBadge>
          </div>
          <p class="mt-3 text-sm leading-6 text-ink-800">{{ session.teachBackGrade.gap_identified }}</p>
          <p class="mt-3 text-sm font-semibold text-ink-900">{{ session.teachBackGrade.encouragement }}</p>
        </div>
      </section>
    </template>
  </div>
</template>
