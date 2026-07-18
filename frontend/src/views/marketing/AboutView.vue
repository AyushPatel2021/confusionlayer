<script setup lang="ts">
import MarketingCta from "../../components/marketing/MarketingCta.vue";
import Squiggle from "../../components/marketing/Squiggle.vue";

const beats = [
  { title: "The pattern every teacher knows", body: "A class stumbles on today's lesson because a prerequisite from three weeks ago quietly faded." },
  { title: "The insight", body: "That fade is measurable. Decayed mastery of prerequisites predicts tomorrow's struggle, before a quiz reveals it." },
  { title: "The engine", body: "So we built the Confusion Forecast Engine: deterministic graph math that briefs the teacher the night before." },
  { title: "The rest of the school", body: "Then the boring-but-essential parts, admissions, fees, staff, so office and classroom share one source of truth." },
];

const principles = [
  { title: "Teachers lead", body: "The AI never runs ahead of the lesson. Teachers decide what's unlocked." },
  { title: "Numbers are earned, not guessed", body: "Mastery and forecasts are deterministic formulas. The AI never grades itself." },
  { title: "Privacy by threshold", body: "No misconception is surfaced unless 3+ students share it, never with a name." },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="relative">
      <div class="dot-grid pointer-events-none absolute inset-0 opacity-50" aria-hidden="true" />
      <div class="relative mx-auto max-w-content px-6 pb-10 pt-16 lg:pt-24">
        <p v-reveal class="s-eyebrow">Why we built this</p>
        <h1 v-reveal class="mt-5 max-w-4xl font-display text-4xl font-semibold leading-[1.05] text-ink-900 md:text-6xl">
          Confusion compounds. We wanted to catch it <Squiggle>earlier.</Squiggle>
        </h1>
      </div>
    </section>

    <section class="mx-auto max-w-content px-6 py-12">
      <ol class="max-w-3xl border-l border-hairline pl-8">
        <li v-for="(beat, i) in beats" :key="beat.title" v-reveal class="relative pb-10 last:pb-0" :style="{ transitionDelay: `${i * 60}ms` }">
          <span class="absolute -left-[37px] top-1 h-4 w-4 rounded-full border-2 border-primary-600 bg-paper" aria-hidden="true" />
          <h3 class="font-display text-xl font-semibold text-ink-900">{{ beat.title }}</h3>
          <p class="mt-2 max-w-reading text-base leading-8 text-ink-700">{{ beat.body }}</p>
        </li>
      </ol>
    </section>

    <!-- Pull quote -->
    <section class="border-y border-hairline bg-ink-900 text-paper">
      <div v-reveal class="mx-auto max-w-content px-6 py-20">
        <p class="max-w-3xl font-display text-3xl leading-snug md:text-4xl">
          “Spend five minutes recapping, instead of an hour re-teaching.”
        </p>
      </div>
    </section>

    <!-- Principles -->
    <section class="mx-auto max-w-content px-6 py-16">
      <h2 v-reveal class="font-display text-3xl font-semibold text-ink-900">What we hold to</h2>
      <div class="mt-8 grid gap-8 md:grid-cols-3">
        <div v-for="(p, i) in principles" :key="p.title" v-reveal :style="{ transitionDelay: `${i * 80}ms` }">
          <span class="font-mono text-sm text-primary-600">{{ String(i + 1).padStart(2, "0") }}</span>
          <h3 class="mt-2 font-display text-xl font-semibold text-ink-900">{{ p.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ p.body }}</p>
        </div>
      </div>
    </section>

    <MarketingCta heading="Teach the lesson. We'll watch for the confusion." />
  </div>
</template>
