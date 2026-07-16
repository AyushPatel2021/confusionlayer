<script setup lang="ts">
import { RouterLink } from "vue-router";

import Marquee from "../../components/marketing/Marquee.vue";
import MarketingCta from "../../components/marketing/MarketingCta.vue";
import Squiggle from "../../components/marketing/Squiggle.vue";
import SButton from "../../components/ui/SButton.vue";

const flow = [
  { n: "1", title: "Create your institute", body: "Add a subject, invite teachers and batches. Minutes, not an IT project." },
  { n: "2", title: "Teach, gated", body: "Unlock chapters as you cover them. Students can't run ahead of class." },
  { n: "3", title: "See confusion early", body: "When a pattern clusters, you get an aggregated brief — with a suggested fix." },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="mx-auto grid max-w-content items-center gap-10 px-6 pb-14 pt-16 lg:grid-cols-[1fr_0.85fr] lg:pt-24">
      <div>
        <p v-reveal class="s-eyebrow pulse-dot ml-4">For tuition institutes</p>
        <h1 v-reveal class="mt-5 font-display text-4xl font-semibold leading-[1.05] text-ink-900 md:text-6xl">
          Just teaching.<br />Just <Squiggle color="#0F6E6E">learning.</Squiggle>
        </h1>
        <p v-reveal class="mt-6 max-w-reading text-lg leading-8 text-ink-700">
          The coaching-center essentials without the school-ERP weight: teachers, batches, and the AI learning engine
          — plus optional fee tracking when you need it.
        </p>
        <div v-reveal class="mt-8">
          <RouterLink to="/signup?segment=institute" class="nudge-host">
            <SButton variant="primary">Start your institute — free <span class="nudge">→</span></SButton>
          </RouterLink>
        </div>
      </div>

      <!-- Animated confusion brief -->
      <div v-reveal class="float rounded-lg border border-hairline bg-surface p-6 shadow-raised lg:justify-self-end">
        <p class="s-eyebrow">Confusion brief · live</p>
        <p class="mt-3 font-display text-lg font-semibold text-ink-900">
          <span v-countup="5" class="text-accent-600">5</span> of 14 confuse reactivity with electronegativity
        </p>
        <div class="mt-4 h-2 w-full overflow-hidden rounded-sm bg-surface-sunken">
          <div class="motif-bar h-full rounded-sm bg-accent-600" style="width: 36%; transform-origin: left" />
        </div>
        <p class="mt-4 text-sm leading-6 text-ink-700">
          Suggested activity: compare electron-loss ease across Na, Mg, Al (~7 min).
        </p>
        <p class="mt-4 border-t border-hairline pt-3 text-xs text-ink-500">Names never shown. Threshold: 3+ students.</p>
      </div>
    </section>

    <Marquee :items="['Physics', 'Chemistry', 'Mathematics', 'Biology', 'Class 9', 'Class 10', 'Foundation batches']" />

    <!-- Step flow with connector -->
    <section class="mx-auto max-w-content px-6 py-16">
      <div class="relative grid gap-8 md:grid-cols-3">
        <div class="absolute left-0 right-0 top-6 hidden h-px bg-hairline md:block" aria-hidden="true" />
        <div v-for="(s, i) in flow" :key="s.n" v-reveal class="relative" :style="{ transitionDelay: `${i * 110}ms` }">
          <div class="relative flex h-12 w-12 items-center justify-center rounded-full border border-primary-600 bg-paper font-display text-lg font-semibold text-primary-600">
            {{ s.n }}
          </div>
          <h3 class="mt-5 font-display text-xl font-semibold text-ink-900">{{ s.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ s.body }}</p>
        </div>
      </div>
    </section>

    <MarketingCta heading="Run your batches on a system that teaches with you." segment="institute" />
  </div>
</template>
