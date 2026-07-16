<script setup lang="ts">
import { RouterLink } from "vue-router";

import MarketingCta from "../../components/marketing/MarketingCta.vue";
import SButton from "../../components/ui/SButton.vue";

const points = [
  { title: "Set up in minutes", body: "Create your institute, add a subject, invite your teachers and batches. No IT project." },
  { title: "Teaching you gate", body: "Unlock chapters as you cover them. Students can't run ahead of your class." },
  { title: "See confusion cluster", body: "When three students trip on the same idea, you get an aggregated brief — with a fix." },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="mx-auto grid max-w-content items-center gap-10 px-6 pb-16 pt-16 lg:grid-cols-[1fr_0.8fr] lg:pt-24">
      <div>
        <p v-reveal class="s-eyebrow">For tuition institutes</p>
        <h1 v-reveal class="mt-4 font-display text-4xl font-semibold leading-tight text-ink-900 md:text-6xl">
          Just teaching. Just learning.
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
      <div v-reveal class="rounded-lg border border-hairline bg-surface p-6 shadow-raised lg:justify-self-end">
        <p class="s-eyebrow">Confusion brief</p>
        <p class="mt-3 font-display text-lg font-semibold text-ink-900">5 of 14 confuse reactivity with electronegativity</p>
        <p class="mt-3 text-sm leading-6 text-ink-700">
          Suggested activity: compare electron-loss ease across Na, Mg, Al (~7 min).
        </p>
        <p class="mt-4 border-t border-hairline pt-3 text-xs text-ink-500">Names are never shown. Threshold: 3+ students.</p>
      </div>
    </section>

    <section class="mx-auto max-w-content px-6 py-14">
      <div class="grid gap-8 md:grid-cols-3">
        <div v-for="(p, i) in points" :key="p.title" v-reveal :style="{ transitionDelay: `${i * 80}ms` }">
          <div class="h-px w-10 bg-accent-600" />
          <h3 class="mt-4 font-display text-xl font-semibold text-ink-900">{{ p.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ p.body }}</p>
        </div>
      </div>
    </section>

    <MarketingCta heading="Run your batches on a system that teaches with you." segment="institute" />
  </div>
</template>
