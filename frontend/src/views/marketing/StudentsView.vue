<script setup lang="ts">
import { RouterLink } from "vue-router";

import MarketingCta from "../../components/marketing/MarketingCta.vue";
import SButton from "../../components/ui/SButton.vue";

const features = [
  { title: "Ask, and get a nudge — not the answer", body: "Doubt-chat scaffolds you turn by turn: a guiding question, then a hint, then a worked step. You still do the thinking." },
  { title: "Explain it back", body: "Teach-back grading catches the gap between 'I memorised it' and 'I understand it.'" },
  { title: "Watch your mastery move", body: "A real mastery-over-time chart — see what's sticking and what's decaying." },
  { title: "Start anything", body: "Curious about something off-syllabus? Self-start a tutorial for any topic, pitched to your level." },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="mx-auto max-w-content px-6 pb-16 pt-16 text-center lg:pt-24">
      <p v-reveal class="s-eyebrow justify-center">For individual learners</p>
      <h1 v-reveal class="mx-auto mt-4 max-w-3xl font-display text-4xl font-semibold leading-tight text-ink-900 md:text-6xl">
        An AI that wants you to understand — not just finish.
      </h1>
      <p v-reveal class="mx-auto mt-6 max-w-reading text-lg leading-8 text-ink-700">
        Learn at your level with a tutor that clears confusion instead of hiding it behind a right answer.
      </p>
      <div v-reveal class="mt-8 flex justify-center">
        <RouterLink to="/signup?segment=individual" class="nudge-host">
          <SButton variant="primary">Start learning — free <span class="nudge">→</span></SButton>
        </RouterLink>
      </div>
    </section>

    <section class="mx-auto max-w-content px-6 py-14">
      <div class="grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline sm:grid-cols-2">
        <div
          v-for="(f, i) in features"
          :key="f.title"
          v-reveal
          class="bg-surface p-8 transition-colors hover:bg-accent-100/40"
          :style="{ transitionDelay: `${i * 70}ms` }"
        >
          <h3 class="font-display text-xl font-semibold text-ink-900">{{ f.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ f.body }}</p>
        </div>
      </div>
    </section>

    <MarketingCta heading="Learn the thing, not the answer key." segment="individual" />
  </div>
</template>
