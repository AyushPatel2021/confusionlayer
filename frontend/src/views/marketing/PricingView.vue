<script setup lang="ts">
import { RouterLink } from "vue-router";

import MarketingCta from "../../components/marketing/MarketingCta.vue";
import SButton from "../../components/ui/SButton.vue";

const plans = [
  {
    name: "Individual",
    segment: "individual",
    tagline: "For a single learner",
    features: ["Full learning engine", "Doubt-chat, quizzes, teach-back", "Self-start any topic", "Mastery-over-time"],
    featured: false,
  },
  {
    name: "Institute",
    segment: "institute",
    tagline: "For coaching centers",
    features: ["Everything in Individual", "Teachers & student batches", "Chapter unlocks", "Confusion + Forecast briefs", "Optional fee tracking"],
    featured: true,
  },
  {
    name: "School",
    segment: "school",
    tagline: "For the whole institution",
    features: ["Everything in Institute", "Full role hierarchy", "Admissions", "Fees & accounting", "Staff & payroll", "Parent portal"],
    featured: false,
  },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="mx-auto max-w-content px-6 pb-10 pt-16 text-center lg:pt-24">
      <p v-reveal class="s-eyebrow justify-center">Pricing</p>
      <h1 v-reveal class="mt-4 font-display text-4xl font-semibold text-ink-900 md:text-5xl">Everything is free right now.</h1>
      <p v-reveal class="mx-auto mt-5 max-w-reading text-lg leading-8 text-ink-700">
        We're building in the open. Pick the shape that matches you — every plan is $0, no card required. Paid tiers,
        if they ever arrive, won't touch what you've already got.
      </p>
    </section>

    <section class="mx-auto max-w-content px-6 py-12">
      <div class="grid items-start gap-6 lg:grid-cols-3">
        <div
          v-for="(plan, i) in plans"
          :key="plan.name"
          v-reveal
          class="card-lift flex flex-col rounded-lg border bg-surface p-7"
          :class="plan.featured ? 'border-primary-600 shadow-raised lg:-mt-3' : 'border-hairline'"
          :style="{ transitionDelay: `${i * 80}ms` }"
        >
          <div class="flex items-center justify-between">
            <h2 class="font-display text-2xl font-semibold text-ink-900">{{ plan.name }}</h2>
            <span v-if="plan.featured" class="rounded-sm bg-primary-50 px-2 py-0.5 text-xs font-semibold text-primary-600">popular</span>
          </div>
          <p class="mt-1 text-sm text-ink-500">{{ plan.tagline }}</p>
          <p class="mt-5 font-display text-4xl font-semibold text-ink-900">$0<span class="text-base font-normal text-ink-500">/mo</span></p>
          <ul class="mt-6 flex-1 space-y-2">
            <li v-for="feature in plan.features" :key="feature" class="flex items-start gap-2 text-sm text-ink-700">
              <span class="mt-0.5 text-primary-600" aria-hidden="true">✓</span>{{ feature }}
            </li>
          </ul>
          <RouterLink :to="`/signup?segment=${plan.segment}`" class="mt-7 nudge-host">
            <SButton :variant="plan.featured ? 'primary' : 'secondary'" block>Get started <span class="nudge">→</span></SButton>
          </RouterLink>
        </div>
      </div>
    </section>

    <MarketingCta heading="Free to start, yours to keep." />
  </div>
</template>
