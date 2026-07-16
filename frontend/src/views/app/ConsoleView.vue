<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import ConfusionBrief from "../../components/ConfusionBrief.vue";
import ForecastBrief from "../../components/ForecastBrief.vue";
import Progress from "../../components/Progress.vue";
import SelfStart from "../../components/SelfStart.vue";
import type { ChapterSummary, ConceptSummary } from "../../stores/session";
import { useSessionStore } from "../../stores/session";

type MainView = "console" | "insights" | "selfstart" | "progress";

const session = useSessionStore();
const doubtText = ref("");
const quizAnswer = ref("");
const teachBackText = ref("");
const mainView = ref<MainView>("console");

onMounted(() => {
  void session.restore();
});

function setView(view: MainView) {
  mainView.value = view;
  if (view === "insights") {
    if (!session.forecastBrief) void session.loadForecastBrief();
    if (!session.confusionBrief) void session.loadConfusionBrief();
  }
  if (view === "progress" && !session.progress) void session.loadProgress();
}

// Reset to the console whenever the signed-in user changes (e.g. switching demo role).
watch(
  () => session.user?.id,
  () => {
    mainView.value = "console";
  },
);

const unlockedCount = computed(() => session.syllabus?.chapters.filter((chapter) => !chapter.locked).length || 0);
const totalConcepts = computed(
  () => session.syllabus?.chapters.reduce((total, chapter) => total + chapter.concepts.length, 0) || 0,
);

function chapterState(chapter: ChapterSummary) {
  return chapter.locked ? "Locked" : "Unlocked";
}

function canOpen(concept: ConceptSummary) {
  return !concept.locked && !session.loading;
}

const quizQuestion = computed(() => {
  const title = session.selectedConcept?.title || "this concept";
  return `Explain one key idea from ${title} in your own words.`;
});

const quizRubric = computed(() => {
  const title = session.selectedConcept?.title || "the concept";
  return `A correct answer should accurately describe ${title}, use relevant terms from the concept, and avoid the listed misconception patterns.`;
});

const teachBackSummary = computed(() => {
  const title = session.selectedConcept?.title || "the concept";
  const taxonomy = session.selectedConcept?.taxonomy.map((item) => `${item.code}: ${item.description}`).join("; ") || "No misconception taxonomy loaded.";
  return `A strong explanation of ${title} should define the idea, connect it to the chapter context, and avoid these misconception patterns: ${taxonomy}`;
});

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
  <div>
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-emerald-700">ConfusionLayer</p>
          <h1 class="mt-1 text-2xl font-semibold tracking-normal">Teacher-gated learning console</h1>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <div v-if="session.user" class="mr-1 flex flex-wrap gap-2">
            <button
              class="tool-tab"
              :class="{ 'tool-tab-active': mainView === 'console' }"
              @click="setView('console')"
            >
              Learning Console
            </button>
            <button
              v-if="session.isTeacher"
              class="tool-tab"
              :class="{ 'tool-tab-active': mainView === 'insights' }"
              @click="setView('insights')"
            >
              Teacher Insights
            </button>
            <button
              v-if="session.isStudent"
              class="tool-tab"
              :class="{ 'tool-tab-active': mainView === 'selfstart' }"
              @click="setView('selfstart')"
            >
              Self-Start
            </button>
            <button
              v-if="session.isStudent"
              class="tool-tab"
              :class="{ 'tool-tab-active': mainView === 'progress' }"
              @click="setView('progress')"
            >
              My Progress
            </button>
          </div>
          <button
            class="btn-primary"
            :disabled="!!session.loading"
            @click="session.demoLogin('teacher')"
          >
            Teacher Demo
          </button>
          <button
            class="btn-secondary"
            :disabled="!!session.loading"
            @click="session.demoLogin('student')"
          >
            Student Demo
          </button>
          <button v-if="session.user" class="btn-ghost" :disabled="!!session.loading" @click="session.logout()">
            Sign Out
          </button>
        </div>
      </div>
    </header>

    <section class="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[360px_minmax(0,1fr)]">
      <aside class="space-y-5">
        <div class="panel">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="eyebrow">Session</p>
              <h2 class="panel-title">{{ session.user?.name || "Choose a demo role" }}</h2>
            </div>
            <span v-if="session.user" class="badge">{{ session.user.role }}</span>
          </div>
          <dl v-if="session.syllabus" class="mt-5 grid grid-cols-2 gap-3">
            <div class="metric">
              <dt>Classroom</dt>
              <dd>{{ session.syllabus.classroom.name }}</dd>
            </div>
            <div class="metric">
              <dt>Chapters</dt>
              <dd>{{ unlockedCount }}/{{ session.syllabus.chapters.length }}</dd>
            </div>
            <div class="metric col-span-2">
              <dt>Subject</dt>
              <dd>{{ session.syllabus.classroom.subject.board }} {{ session.syllabus.classroom.subject.class_level }} · {{ session.syllabus.classroom.subject.name }}</dd>
            </div>
          </dl>
          <p v-else class="mt-4 text-sm leading-6 text-slate-600">No active session</p>
        </div>

        <div v-if="session.syllabus" class="panel">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="eyebrow">Syllabus</p>
              <h2 class="panel-title">{{ totalConcepts }} concepts</h2>
            </div>
            <button class="btn-ghost" :disabled="!!session.loading" @click="session.loadSyllabus()">Refresh</button>
          </div>

          <div class="mt-5 space-y-3">
            <section v-for="chapter in session.syllabus.chapters" :key="chapter.id" class="chapter-block">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs font-medium text-slate-500">Chapter {{ chapter.order }}</p>
                  <h3 class="text-sm font-semibold leading-5">{{ chapter.title }}</h3>
                </div>
                <span :class="chapter.locked ? 'badge-muted' : 'badge'">{{ chapterState(chapter) }}</span>
              </div>

              <button
                v-if="session.isTeacher && chapter.locked"
                class="mt-3 w-full btn-secondary"
                :disabled="session.loading === `unlock-${chapter.id}`"
                @click="session.unlockChapter(chapter.id)"
              >
                {{ session.loading === `unlock-${chapter.id}` ? "Unlocking" : "Unlock Chapter" }}
              </button>

              <div class="mt-3 space-y-2">
                <button
                  v-for="concept in chapter.concepts"
                  :key="concept.id"
                  class="concept-row"
                  :class="{ 'concept-row-active': session.selectedConcept?.id === concept.id }"
                  :disabled="!canOpen(concept)"
                  @click="session.openConcept(concept)"
                >
                  <span>{{ concept.title }}</span>
                  <span class="text-xs text-slate-500">{{ concept.locked ? "Locked" : "Open" }}</span>
                </button>
              </div>
            </section>
          </div>
        </div>
      </aside>

      <div v-if="session.isTeacher && mainView === 'insights'" class="space-y-5">
        <div v-if="session.error" class="border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {{ session.error }}
        </div>
        <ForecastBrief />
        <ConfusionBrief />
      </div>

      <div v-else-if="session.isStudent && mainView === 'selfstart'" class="space-y-5">
        <div v-if="session.error" class="border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {{ session.error }}
        </div>
        <SelfStart />
      </div>

      <div v-else-if="session.isStudent && mainView === 'progress'" class="space-y-5">
        <div v-if="session.error" class="border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {{ session.error }}
        </div>
        <Progress />
      </div>

      <section v-else class="panel min-h-[620px]">
        <div v-if="session.error" class="mb-4 border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {{ session.error }}
        </div>

        <div v-if="!session.user" class="flex min-h-[520px] items-center justify-center">
          <div class="max-w-xl text-center">
            <p class="eyebrow justify-center">Live demo</p>
            <h2 class="mt-2 text-3xl font-semibold">Start with teacher or student mode</h2>
            <p class="mt-4 text-base leading-7 text-slate-600">Seeded CBSE Class 10 Science classroom</p>
          </div>
        </div>

        <div v-else-if="!session.selectedConcept" class="flex min-h-[520px] items-center justify-center">
          <div class="max-w-xl text-center">
            <p class="eyebrow justify-center">Classroom loaded</p>
            <h2 class="mt-2 text-3xl font-semibold">Select an unlocked concept</h2>
            <p class="mt-4 text-base leading-7 text-slate-600">{{ session.syllabus?.classroom.name }}</p>
          </div>
        </div>

        <article v-else class="space-y-6">
          <div class="border-b border-slate-200 pb-5">
            <p class="eyebrow">{{ session.selectedConcept.chapter_title }}</p>
            <div class="mt-2 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 class="text-3xl font-semibold">{{ session.selectedConcept.title }}</h2>
                <p class="mt-2 text-sm text-slate-600">
                  {{ session.selectedConcept.subject.board }} Class {{ session.selectedConcept.subject.class_level }} · {{ session.selectedConcept.subject.name }}
                </p>
              </div>
            </div>
          </div>

          <nav class="flex flex-wrap gap-2 border-b border-slate-200 pb-4">
            <button
              class="tool-tab"
              :class="{ 'tool-tab-active': session.activeTool === 'tutorial' }"
              @click="session.activeTool = 'tutorial'"
            >
              Tutorial
            </button>
            <button
              class="tool-tab"
              :class="{ 'tool-tab-active': session.activeTool === 'doubt' }"
              @click="session.activeTool = 'doubt'"
            >
              Doubt Chat
            </button>
            <button
              class="tool-tab"
              :class="{ 'tool-tab-active': session.activeTool === 'quiz' }"
              @click="session.activeTool = 'quiz'"
            >
              Quiz
            </button>
            <button
              class="tool-tab"
              :class="{ 'tool-tab-active': session.activeTool === 'teach_back' }"
              @click="session.activeTool = 'teach_back'"
            >
              Teach-Back
            </button>
          </nav>

          <section>
            <p class="eyebrow">Fixed taxonomy</p>
            <div class="mt-3 grid gap-3 md:grid-cols-2">
              <div v-for="item in session.selectedConcept.taxonomy" :key="item.code" class="taxonomy-item">
                <p class="text-xs font-semibold text-emerald-800">{{ item.code }}</p>
                <p class="mt-1 text-sm leading-6 text-slate-700">{{ item.description }}</p>
              </div>
            </div>
          </section>

          <section v-if="session.activeTool === 'tutorial'" class="space-y-4">
            <div class="flex items-center justify-between gap-3">
              <p class="eyebrow">Tutorial generator</p>
              <button class="btn-primary" :disabled="!!session.loading" @click="session.generateTutorial()">
                {{ session.loading === "tutorial" ? "Generating" : "Generate Tutorial" }}
              </button>
            </div>
            <div v-if="session.tutorial" class="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.8fr)]">
              <div class="tutorial-band">
                <p class="eyebrow">Tutorial</p>
                <p class="mt-3 whitespace-pre-line text-base leading-8 text-slate-800">{{ session.tutorial.explanation }}</p>
              </div>
              <div class="tutorial-band">
                <p class="eyebrow">Worked example</p>
                <p class="mt-3 whitespace-pre-line text-base leading-8 text-slate-800">{{ session.tutorial.worked_example }}</p>
              </div>
            </div>
            <div v-else class="empty-tool">No generated tutorial yet</div>
          </section>

          <section v-if="session.activeTool === 'doubt'" class="space-y-4">
            <div class="flex items-center justify-between gap-3">
              <p class="eyebrow">Progressive scaffolding</p>
              <span class="badge-muted">{{ session.chatMessages.filter((item) => item.role === "student").length + 1 }} turn</span>
            </div>
            <div class="chat-box">
              <div v-if="session.chatMessages.length === 0" class="empty-tool">No messages yet</div>
              <div
                v-for="(message, index) in session.chatMessages"
                :key="`${message.role}-${index}`"
                class="chat-message"
                :class="message.role === 'student' ? 'chat-message-student' : 'chat-message-assistant'"
              >
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {{ message.role }} <span v-if="message.response_type">· {{ message.response_type }}</span>
                </p>
                <p class="mt-1 whitespace-pre-line text-sm leading-6">{{ message.content }}</p>
              </div>
            </div>
            <form class="flex flex-col gap-3 md:flex-row" @submit.prevent="sendDoubt">
              <input
                v-model="doubtText"
                class="text-input"
                placeholder="Ask a doubt about this concept"
                :disabled="!!session.loading"
              />
              <button class="btn-primary" :disabled="!!session.loading || !doubtText.trim()">
                {{ session.loading === "doubt" ? "Sending" : "Send" }}
              </button>
            </form>
          </section>

          <section v-if="session.activeTool === 'quiz'" class="space-y-4">
            <div>
              <p class="eyebrow">Quiz grader</p>
              <div class="mt-3 grid gap-3 md:grid-cols-2">
                <div class="taxonomy-item">
                  <p class="text-xs font-semibold text-slate-500">Question</p>
                  <p class="mt-1 text-sm leading-6 text-slate-800">{{ quizQuestion }}</p>
                </div>
                <div class="taxonomy-item">
                  <p class="text-xs font-semibold text-slate-500">Rubric</p>
                  <p class="mt-1 text-sm leading-6 text-slate-800">{{ quizRubric }}</p>
                </div>
              </div>
            </div>
            <form class="space-y-3" @submit.prevent="submitQuiz">
              <textarea
                v-model="quizAnswer"
                class="text-area"
                placeholder="Write your answer"
                :disabled="!!session.loading || !session.isStudent"
              />
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm text-slate-500">{{ session.isStudent ? "Answer as the student demo account" : "Switch to Student Demo to submit" }}</p>
                <button class="btn-primary" :disabled="!!session.loading || !quizAnswer.trim() || !session.isStudent">
                  {{ session.loading === "quiz" ? "Grading" : "Grade Answer" }}
                </button>
              </div>
            </form>
            <div v-if="session.quizGrade" class="tutorial-band">
              <div class="flex flex-wrap items-center gap-2">
                <span :class="session.quizGrade.is_correct ? 'badge' : 'badge-muted'">
                  {{ session.quizGrade.is_correct ? "Correct" : "Needs review" }}
                </span>
                <span class="badge-muted">Confidence {{ Math.round(session.quizGrade.confidence * 100) }}%</span>
                <span v-if="session.quizGrade.misconception_code" class="badge-muted">{{ session.quizGrade.misconception_code }}</span>
              </div>
              <p class="mt-3 text-sm leading-6 text-slate-800">{{ session.quizGrade.misconception_summary }}</p>
              <p class="mt-3 text-sm font-semibold text-slate-950">{{ session.quizGrade.follow_up_question }}</p>
            </div>
          </section>

          <section v-if="session.activeTool === 'teach_back'" class="space-y-4">
            <div>
              <p class="eyebrow">Teach-back grader</p>
              <div class="mt-3 tutorial-band">
                <p class="text-sm leading-6 text-slate-800">{{ teachBackSummary }}</p>
              </div>
            </div>
            <form class="space-y-3" @submit.prevent="submitTeachBack">
              <textarea
                v-model="teachBackText"
                class="text-area"
                placeholder="Explain this concept in your own words"
                :disabled="!!session.loading || !session.isStudent"
              />
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm text-slate-500">{{ session.isStudent ? "Teach back as the student demo account" : "Switch to Student Demo to submit" }}</p>
                <button class="btn-primary" :disabled="!!session.loading || !teachBackText.trim() || !session.isStudent">
                  {{ session.loading === "teach-back" ? "Grading" : "Grade Teach-Back" }}
                </button>
              </div>
            </form>
            <div v-if="session.teachBackGrade" class="tutorial-band">
              <div class="flex flex-wrap items-center gap-2">
                <span class="badge-muted">Clarity {{ Math.round(session.teachBackGrade.clarity_score * 100) }}%</span>
                <span class="badge-muted">Accuracy {{ Math.round(session.teachBackGrade.accuracy_score * 100) }}%</span>
              </div>
              <p class="mt-3 text-sm leading-6 text-slate-800">{{ session.teachBackGrade.gap_identified }}</p>
              <p class="mt-3 text-sm font-semibold text-slate-950">{{ session.teachBackGrade.encouragement }}</p>
            </div>
          </section>
        </article>
      </section>
    </section>
  </div>
</template>
