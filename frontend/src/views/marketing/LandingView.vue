<script setup lang="ts">
import { RouterLink } from "vue-router";

import SBadge from "../../components/ui/SBadge.vue";
import SButton from "../../components/ui/SButton.vue";
import SCard from "../../components/ui/SCard.vue";

const segments = [
  {
    id: "schools",
    name: "Schools",
    blurb:
      "The full stack — admissions, fees & accounting, staff & payroll, teaching, and the learning platform, under one org hierarchy.",
  },
  {
    id: "institutes",
    name: "Tuition institutes",
    blurb: "The teaching and learning core for teachers and students, with optional fee tracking.",
  },
  {
    id: "students",
    name: "Individual learners",
    blurb: "Self-serve access to the ConfusionLayer learning experience — tutorials, doubt chat, and progress.",
  },
];

const features = [
  {
    title: "Forecast confusion before the lesson",
    body: "Deterministic prerequisite-mastery propagation predicts which upcoming concepts a class will struggle with — and briefs the teacher first.",
  },
  {
    title: "Teacher-gated AI",
    body: "Tutorials, Socratic doubt chat, quizzes with misconception diagnosis, and teach-back grading — only for what's been taught.",
  },
  {
    title: "Run the whole school",
    body: "Admissions, fees, and staff alongside learning — one system, one hierarchy, clean role-based access.",
  },
];
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="mx-auto max-w-content px-6 pb-16 pt-20 text-center">
      <div class="mx-auto max-w-reading">
        <SBadge tone="primary">Powered by the ConfusionLayer AI engine</SBadge>
        <h1 class="mt-5 font-display text-4xl font-semibold leading-tight text-ink-900 md:text-5xl">
          Run your school. Clear the confusion.
        </h1>
        <p class="mt-5 text-lg leading-8 text-ink-700">
          Slate unifies everyday school operations with an AI learning engine that predicts and clears student
          confusion before it derails a lesson.
        </p>
        <div class="mt-8 flex items-center justify-center gap-3">
          <RouterLink to="/signup"><SButton variant="primary">Get started — free</SButton></RouterLink>
          <RouterLink to="/login"><SButton variant="secondary">Sign in</SButton></RouterLink>
        </div>
        <p class="mt-3 text-xs text-ink-500">All plans are currently free.</p>
      </div>
    </section>

    <!-- Segments -->
    <section class="border-t border-hairline bg-surface/60">
      <div class="mx-auto max-w-content px-6 py-16">
        <h2 class="text-center font-display text-2xl font-semibold text-ink-900">One platform, three ways in</h2>
        <div class="mt-10 grid gap-5 md:grid-cols-3">
          <SCard v-for="segment in segments" :id="segment.id" :key="segment.id">
            <h3 class="font-display text-xl font-semibold text-ink-900">{{ segment.name }}</h3>
            <p class="mt-3 text-sm leading-6 text-ink-700">{{ segment.blurb }}</p>
            <RouterLink :to="`/signup?segment=${segment.id === 'schools' ? 'school' : segment.id === 'institutes' ? 'institute' : 'individual'}`" class="mt-4 inline-block text-sm font-semibold text-primary-600 hover:text-primary-500">
              Get started →
            </RouterLink>
          </SCard>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="mx-auto max-w-content px-6 py-16">
      <div class="grid gap-5 md:grid-cols-3">
        <div v-for="feature in features" :key="feature.title">
          <p class="s-eyebrow">ConfusionLayer</p>
          <h3 class="mt-2 font-display text-lg font-semibold text-ink-900">{{ feature.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ feature.body }}</p>
        </div>
      </div>
    </section>
  </div>
</template>
