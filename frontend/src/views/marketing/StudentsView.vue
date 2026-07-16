<script setup lang="ts">
import { RouterLink } from "vue-router";

import MarketingCta from "../../components/marketing/MarketingCta.vue";
import Squiggle from "../../components/marketing/Squiggle.vue";
import SButton from "../../components/ui/SButton.vue";

const chat = [
  { who: "you", text: "How do I balance H₂ + O₂ → H₂O?", type: "" },
  { who: "slate", text: "Good one. What has to stay equal on both sides of any equation?", type: "guiding question" },
  { who: "slate", text: "Count the oxygen atoms on each side first — what do you get?", type: "hint" },
  { who: "slate", text: "Right — 2 on the left, 1 on the right. So we place a 2 in front of H₂O…", type: "worked step" },
];

const features = [
  { title: "Ask, and get a nudge — not the answer", body: "Doubt-chat scaffolds you turn by turn. You still do the thinking." },
  { title: "Explain it back", body: "Teach-back grading catches the gap between 'I memorised it' and 'I understand it.'" },
  { title: "Watch your mastery move", body: "A real mastery-over-time chart — see what's sticking and what's decaying." },
  { title: "Start anything", body: "Curious about something off-syllabus? Self-start a tutorial for any topic." },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="mx-auto grid max-w-content items-center gap-12 px-6 pb-14 pt-16 lg:grid-cols-[1fr_1fr] lg:pt-24">
      <div>
        <p v-reveal class="s-eyebrow pulse-dot ml-4">For individual learners</p>
        <h1 v-reveal class="mt-5 font-display text-4xl font-semibold leading-[1.05] text-ink-900 md:text-6xl">
          Learn the thing,<br />not the <Squiggle>answer key.</Squiggle>
        </h1>
        <p v-reveal class="mt-6 max-w-reading text-lg leading-8 text-ink-700">
          An AI tutor that clears confusion instead of hiding it behind a right answer — pitched to your level, on any
          topic you're curious about.
        </p>
        <div v-reveal class="mt-8">
          <RouterLink to="/signup?segment=individual" class="nudge-host">
            <SButton variant="primary">Start learning — free <span class="nudge">→</span></SButton>
          </RouterLink>
        </div>
      </div>

      <!-- Animated doubt-chat -->
      <div v-reveal class="space-y-3 rounded-lg border border-hairline bg-surface p-5 shadow-raised">
        <div
          v-for="(m, i) in chat"
          :key="i"
          class="bubble max-w-[85%] rounded-lg px-4 py-3 text-sm leading-6"
          :class="m.who === 'you' ? 'ml-auto bg-primary-600 text-white' : 'mr-auto border border-hairline bg-paper text-ink-700'"
          :style="{ animationDelay: `${0.15 + i * 0.5}s` }"
        >
          <p v-if="m.type" class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-accent-600">{{ m.type }}</p>
          {{ m.text }}
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-content px-6 py-16">
      <div class="grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline sm:grid-cols-2">
        <div
          v-for="(f, i) in features"
          :key="f.title"
          v-reveal
          class="group bg-surface p-8 transition-colors hover:bg-accent-100/40"
          :style="{ transitionDelay: `${i * 70}ms` }"
        >
          <h3 class="font-display text-xl font-semibold text-ink-900">{{ f.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ f.body }}</p>
          <span class="mt-3 inline-block text-sm font-semibold text-primary-600 opacity-0 transition-opacity group-hover:opacity-100">
            In the app <span class="nudge">→</span>
          </span>
        </div>
      </div>
    </section>

    <MarketingCta heading="Understand it — don't just finish it." segment="individual" />
  </div>
</template>
