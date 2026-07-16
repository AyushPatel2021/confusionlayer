<script setup lang="ts">
import { RouterLink } from "vue-router";

import Marquee from "../../components/marketing/Marquee.vue";
import Squiggle from "../../components/marketing/Squiggle.vue";
import SButton from "../../components/ui/SButton.vue";

const steps = [
  { n: "01", title: "Teachers unlock, chapter by chapter", body: "AI only tutors what's actually been taught. Nothing runs ahead of the lesson." },
  { n: "02", title: "Students learn with guardrails", body: "Tutorials, Socratic doubt-chat, and quizzes — scaffolded, never spoon-fed." },
  { n: "03", title: "Every mistake gets a name", body: "Answers are diagnosed against a fixed misconception taxonomy, not a vague 'incorrect'." },
  { n: "04", title: "The class is forecast — before the lesson", body: "Decayed prerequisite mastery predicts tomorrow's struggle, and briefs the teacher first." },
];

const segments = [
  { to: "/schools", name: "For schools", body: "Admissions, fees, staff, and teaching in one hierarchy — with the learning engine built in." },
  { to: "/institutes", name: "For tuition institutes", body: "The teaching and learning core, lightweight, for teachers and their students." },
  { to: "/students", name: "For individual learners", body: "Learn any topic at your level, with an AI that clears confusion instead of hiding it." },
];

const forecast = [
  { concept: "Ionic Bonding", pct: 78 },
  { concept: "Reactivity Series", pct: 54 },
  { concept: "Neutralisation", pct: 31 },
];

const headline = ["Clear", "the", "confusion"];
</script>

<template>
  <div class="overflow-hidden">
    <!-- Hero -->
    <section class="relative">
      <div class="dot-grid pointer-events-none absolute inset-0 opacity-60" aria-hidden="true" />
      <div class="relative mx-auto grid max-w-content items-center gap-12 px-6 pb-16 pt-16 lg:grid-cols-[1.05fr_0.95fr] lg:pt-24">
        <div>
          <p class="s-eyebrow pulse-dot ml-4">Teacher-gated · predictive</p>
          <h1 class="mt-5 font-display text-[2.7rem] font-semibold leading-[1.04] text-ink-900 md:text-6xl">
            <span
              v-for="(w, i) in headline"
              :key="w"
              class="word mr-[0.25em]"
              :style="{ animationDelay: `${i * 0.09}s` }"
              >{{ w }}</span
            ><br />
            <Squiggle>before</Squiggle>
            <span class="word mr-[0.25em]" :style="{ animationDelay: '0.4s' }">&nbsp;it</span>
            <span class="word" :style="{ animationDelay: '0.48s' }">starts.</span>
          </h1>
          <p class="mt-6 max-w-reading text-lg leading-8 text-ink-700">
            Most tools react after a student fails a quiz. Slate forecasts which upcoming concepts a class will
            struggle with — from decayed mastery of the prerequisites — and hands the teacher a briefing the night
            before the lesson.
          </p>
          <div class="mt-8 flex flex-wrap items-center gap-3">
            <RouterLink to="/signup" class="nudge-host">
              <SButton variant="primary">Get started — it's free <span class="nudge">→</span></SButton>
            </RouterLink>
            <RouterLink to="/login"><SButton variant="ghost">Explore the sample school</SButton></RouterLink>
          </div>
        </div>

        <!-- Forecast motif -->
        <div v-reveal class="lg:justify-self-end">
          <div class="float card-lift w-full max-w-sm rounded-lg border border-hairline bg-surface p-6 shadow-raised">
            <div class="flex items-center justify-between">
              <p class="s-eyebrow">Forecast brief · Ch. 5</p>
              <span class="rounded-sm bg-accent-100 px-2 py-0.5 text-xs font-semibold text-accent-600">tomorrow</span>
            </div>
            <p class="mt-3 font-display text-lg font-semibold text-ink-900">
              <span v-countup="7" class="text-accent-600">7</span> of 12 likely to struggle
            </p>
            <div class="mt-5 space-y-4">
              <div v-for="(row, i) in forecast" :key="row.concept">
                <div class="flex items-baseline justify-between text-sm">
                  <span class="text-ink-700">{{ row.concept }}</span>
                  <span class="font-mono text-xs text-ink-500">{{ row.pct }}%</span>
                </div>
                <div class="mt-1 h-2 w-full overflow-hidden rounded-sm bg-surface-sunken">
                  <div
                    class="motif-bar h-full rounded-sm"
                    :class="row.pct > 65 ? 'bg-accent-600' : row.pct > 45 ? 'bg-warning' : 'bg-primary-500'"
                    :style="{ width: `${row.pct}%`, transitionDelay: `${i * 120}ms`, transformOrigin: 'left' }"
                  />
                </div>
              </div>
            </div>
            <p class="mt-5 border-t border-hairline pt-4 text-sm leading-6 text-ink-500">
              Suggested: a 5-minute recap of <span class="text-ink-700">Atomic Structure</span> before you start.
            </p>
          </div>
        </div>
      </div>
    </section>

    <Marquee :items="['Admissions', 'Fees & accounting', 'Confusion forecasts', 'Teach-back grading', 'Doubt-chat', 'Mastery over time', 'Staff & payroll']" />

    <!-- Insight statement -->
    <section class="bg-surface/50">
      <div v-reveal class="mx-auto max-w-content px-6 py-16">
        <p class="max-w-3xl font-display text-2xl leading-relaxed text-ink-900 md:text-3xl">
          A report card tells you what already went wrong. Slate tells you
          <span class="mark">what's about to</span> — while there's still time to teach differently.
        </p>
      </div>
    </section>

    <!-- How it works -->
    <section class="mx-auto max-w-content px-6 py-20">
      <div v-reveal class="flex items-end justify-between gap-6">
        <h2 class="font-display text-3xl font-semibold text-ink-900">How it works</h2>
        <span class="hidden text-sm text-ink-500 sm:block">Four moving parts, one loop.</span>
      </div>
      <div class="mt-10 grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline md:grid-cols-2">
        <div
          v-for="(step, i) in steps"
          :key="step.n"
          v-reveal
          class="group relative bg-surface p-8 transition-colors hover:bg-primary-50"
          :style="{ transitionDelay: `${i * 70}ms` }"
        >
          <span class="font-mono text-sm text-primary-600">{{ step.n }}</span>
          <h3 class="mt-3 font-display text-xl font-semibold text-ink-900">{{ step.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ step.body }}</p>
          <span class="absolute right-8 top-8 text-ink-300 transition-all group-hover:right-6 group-hover:text-primary-600" aria-hidden="true">→</span>
        </div>
      </div>
    </section>

    <!-- Differentiator (dark band) -->
    <section class="border-t border-hairline bg-ink-900 text-paper">
      <div class="mx-auto grid max-w-content items-center gap-10 px-6 py-20 lg:grid-cols-2">
        <div v-reveal>
          <p class="text-xs font-semibold uppercase tracking-wide text-accent-600">The engine</p>
          <h2 class="mt-3 font-display text-3xl font-semibold md:text-4xl">Deterministic, not a guess.</h2>
          <p class="mt-5 max-w-reading leading-8 text-paper/80">
            The forecast isn't the AI's opinion. It's graph math over the prerequisite map: each concept's predicted
            difficulty comes from how much its prerequisites have decayed. The AI names the misconception — the
            system computes the number.
          </p>
        </div>
        <div v-reveal class="grid grid-cols-3 gap-4">
          <div class="rounded-lg border border-paper/15 p-4 text-center">
            <p class="font-display text-4xl font-semibold text-paper"><span v-countup="7">7</span></p>
            <p class="mt-1 text-xs text-paper/70">of 12 flagged before the lesson</p>
          </div>
          <div class="rounded-lg border border-paper/15 p-4 text-center">
            <p class="font-display text-4xl font-semibold text-paper"><span v-countup="3" data-suffix="+">3+</span></p>
            <p class="mt-1 text-xs text-paper/70">privacy threshold, always</p>
          </div>
          <div class="rounded-lg border border-paper/15 p-4 text-center">
            <p class="font-display text-4xl font-semibold text-paper"><span v-countup="4">4</span></p>
            <p class="mt-1 text-xs text-paper/70">structured AI roles</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Segments -->
    <section class="mx-auto max-w-content px-6 py-20">
      <h2 v-reveal class="font-display text-3xl font-semibold text-ink-900">One platform, three ways in</h2>
      <div class="mt-10 grid gap-5 md:grid-cols-3">
        <RouterLink
          v-for="(segment, i) in segments"
          :key="segment.to"
          :to="segment.to"
          v-reveal
          class="card-lift group flex flex-col rounded-lg border border-hairline bg-surface p-6"
          :style="{ transitionDelay: `${i * 80}ms` }"
        >
          <h3 class="font-display text-xl font-semibold text-ink-900">{{ segment.name }}</h3>
          <p class="mt-3 flex-1 text-sm leading-6 text-ink-700">{{ segment.body }}</p>
          <span class="mt-5 text-sm font-semibold text-primary-600">Learn more <span class="nudge">→</span></span>
        </RouterLink>
      </div>
    </section>

    <!-- Closing -->
    <section class="border-t border-hairline">
      <div v-reveal class="mx-auto max-w-content px-6 py-20 text-center">
        <h2 class="mx-auto max-w-2xl font-display text-3xl font-semibold text-ink-900 md:text-4xl">
          Built for the teacher who'd rather <Squiggle color="#0F6E6E">prevent</Squiggle> the confusion than grade it.
        </h2>
        <div class="mt-8 flex justify-center">
          <RouterLink to="/signup" class="nudge-host">
            <SButton variant="primary">Create your free workspace <span class="nudge">→</span></SButton>
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>
