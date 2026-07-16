<script setup lang="ts">
import { RouterLink } from "vue-router";

import MarketingCta from "../../components/marketing/MarketingCta.vue";
import SButton from "../../components/ui/SButton.vue";

const modules = [
  { name: "Admissions", body: "Applicant intake → review → accept → enrolled, without the spreadsheet." },
  { name: "Fees & accounting", body: "Fee structures, invoices, receipts, and dues — per student, per term." },
  { name: "Staff & payroll", body: "Employee records, designations, salary structures, and payroll runs." },
  { name: "Learning", body: "The ConfusionLayer engine: tutoring, diagnosis, and pre-lesson forecasts." },
];

const hierarchy = [
  { role: "Owner", note: "runs the org & subscription" },
  { role: "School Admin", note: "members, classes, settings" },
  { role: "Accountant · HR · Teachers", note: "their own modules" },
  { role: "Students · Parents", note: "learning & visibility" },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="mx-auto max-w-content px-6 pb-16 pt-16 lg:pt-24">
      <p v-reveal class="s-eyebrow">For schools</p>
      <h1 v-reveal class="mt-4 max-w-4xl font-display text-4xl font-semibold leading-tight text-ink-900 md:text-6xl">
        The whole school, in one hierarchy.
      </h1>
      <p v-reveal class="mt-6 max-w-reading text-lg leading-8 text-ink-700">
        Admissions, fees, staff, and the learning platform under a single roof and a single set of roles — so the
        front office and the classroom finally run on the same system.
      </p>
      <div v-reveal class="mt-8">
        <RouterLink to="/signup?segment=school" class="nudge-host">
          <SButton variant="primary">Start your school — free <span class="nudge">→</span></SButton>
        </RouterLink>
      </div>
    </section>

    <!-- Modules -->
    <section class="mx-auto max-w-content px-6 py-14">
      <div class="grid gap-5 md:grid-cols-2">
        <div
          v-for="(m, i) in modules"
          :key="m.name"
          v-reveal
          class="card-lift rounded-lg border border-hairline bg-surface p-6"
          :style="{ transitionDelay: `${i * 70}ms` }"
        >
          <h3 class="font-display text-xl font-semibold text-ink-900">{{ m.name }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-700">{{ m.body }}</p>
        </div>
      </div>
    </section>

    <!-- Hierarchy -->
    <section class="border-y border-hairline bg-surface/50">
      <div class="mx-auto max-w-content px-6 py-16">
        <h2 v-reveal class="font-display text-3xl font-semibold text-ink-900">A role for everyone, access for no one extra</h2>
        <div class="mt-8 space-y-2">
          <div
            v-for="(level, i) in hierarchy"
            :key="level.role"
            v-reveal
            class="flex flex-wrap items-center justify-between gap-2 rounded-md border border-hairline bg-surface px-5 py-4 transition-colors hover:border-primary-500"
            :style="{ marginLeft: `${i * 1.5}rem`, transitionDelay: `${i * 60}ms` }"
          >
            <span class="font-semibold text-ink-900">{{ level.role }}</span>
            <span class="text-sm text-ink-500">{{ level.note }}</span>
          </div>
        </div>
        <p v-reveal class="mt-6 max-w-reading text-sm leading-6 text-ink-500">
          Every screen is gated by role and scoped to your organization. A user can never see another school's data.
        </p>
      </div>
    </section>

    <MarketingCta heading="Bring your whole school onto one system." segment="school" />
  </div>
</template>
