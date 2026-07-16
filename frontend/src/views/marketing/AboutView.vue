<script setup lang="ts">
import MarketingCta from "../../components/marketing/MarketingCta.vue";

const principles = [
  { title: "Teachers lead", body: "The AI never runs ahead of the lesson. Teachers decide what's unlocked, and the tutor only helps with that." },
  { title: "Numbers are earned, not guessed", body: "Mastery and forecasts are deterministic formulas in code. The AI names a misconception; it never grades itself." },
  { title: "Privacy by threshold", body: "No misconception is surfaced to a teacher unless at least three students share it — and never with a name attached." },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="mx-auto max-w-content px-6 pb-12 pt-16 lg:pt-24">
      <p v-reveal class="s-eyebrow">Why we built this</p>
      <h1 v-reveal class="mt-4 max-w-4xl font-display text-4xl font-semibold leading-tight text-ink-900 md:text-6xl">
        Confusion compounds. We wanted to catch it earlier.
      </h1>
      <div v-reveal class="mt-8 max-w-reading space-y-5 text-lg leading-8 text-ink-700">
        <p>
          Every teacher knows the pattern: a class stumbles on today's lesson because a prerequisite from three weeks
          ago quietly faded. By the time a quiz reveals it, the lesson is already lost.
        </p>
        <p>
          Slate started as a single question — <em class="text-primary-600 not-italic">what if you could see that coming?</em>
          The Confusion Forecast Engine reads decayed prerequisite mastery and predicts tomorrow's struggle, so a
          teacher can spend five minutes recapping instead of an hour re-teaching.
        </p>
        <p>
          Around that engine we built the boring-but-essential parts of running a school — admissions, fees, staff —
          so the office and the classroom finally share one source of truth.
        </p>
      </div>
    </section>

    <section class="border-y border-hairline bg-surface/50">
      <div class="mx-auto max-w-content px-6 py-16">
        <h2 v-reveal class="font-display text-3xl font-semibold text-ink-900">What we hold to</h2>
        <div class="mt-8 grid gap-8 md:grid-cols-3">
          <div v-for="(p, i) in principles" :key="p.title" v-reveal :style="{ transitionDelay: `${i * 80}ms` }">
            <span class="font-mono text-sm text-primary-600">{{ String(i + 1).padStart(2, "0") }}</span>
            <h3 class="mt-2 font-display text-xl font-semibold text-ink-900">{{ p.title }}</h3>
            <p class="mt-2 text-sm leading-6 text-ink-700">{{ p.body }}</p>
          </div>
        </div>
      </div>
    </section>

    <MarketingCta heading="Teach the lesson. We'll watch for the confusion." />
  </div>
</template>
