<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";

import MarketingCta from "../../components/marketing/MarketingCta.vue";
import Squiggle from "../../components/marketing/Squiggle.vue";
import SButton from "../../components/ui/SButton.vue";

const modules = [
  { key: "admissions", tab: "Admissions", title: "Admissions that don't live in a spreadsheet", body: "Track applicants from enquiry to enrolled, then provision the student account in one click.", points: ["Applicant intake forms", "Review & status pipeline", "Accept → enrol → learning access"] },
  { key: "fees", tab: "Fees", title: "Fees, invoices, and dues — per student", body: "Define fee structures once, generate invoices per term, and see who's paid at a glance.", points: ["Fee structures & items", "Invoices & receipts", "Dues and ledger view"] },
  { key: "staff", tab: "Staff & payroll", title: "Your people, on the record", body: "Employee records, designations, and salary structures, with payroll runs when you need them.", points: ["Employee directory", "Designations & roles", "Salary structures & payslips"] },
  { key: "learning", tab: "Learning", title: "The engine that clears confusion", body: "Everything the classroom needs: tutoring, misconception diagnosis, and pre-lesson forecasts.", points: ["Teacher-gated AI tutoring", "Forecast & confusion briefs", "Mastery tracking"] },
];
const active = ref(modules[0]);

const hierarchy = [
  { role: "Owner", note: "runs the org & subscription" },
  { role: "School Admin", note: "members, classes, settings" },
  { role: "Accountant · HR · Teachers", note: "their own modules" },
  { role: "Students · Parents", note: "learning & visibility" },
];
</script>

<template>
  <div class="overflow-hidden">
    <section class="relative">
      <div class="dot-grid pointer-events-none absolute inset-0 opacity-50" aria-hidden="true" />
      <div class="relative mx-auto max-w-content px-6 pb-14 pt-16 lg:pt-24">
        <p v-reveal class="s-eyebrow pulse-dot ml-4">For schools</p>
        <h1 v-reveal class="mt-5 max-w-4xl font-display text-4xl font-semibold leading-[1.05] text-ink-900 md:text-6xl">
          The whole school, in <Squiggle>one hierarchy.</Squiggle>
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
      </div>
    </section>

    <!-- Interactive module switcher -->
    <section class="mx-auto max-w-content px-6 py-14">
      <div v-reveal class="flex flex-wrap gap-2">
        <button
          v-for="m in modules"
          :key="m.key"
          class="s-focus rounded-full border px-4 py-2 text-sm font-semibold transition"
          :class="active.key === m.key ? 'border-primary-600 bg-primary-600 text-white' : 'border-hairline bg-surface text-ink-700 hover:border-primary-500'"
          @click="active = m"
        >
          {{ m.tab }}
        </button>
      </div>
      <div v-reveal class="mt-6 overflow-hidden rounded-lg border border-hairline bg-surface">
        <Transition name="swap" mode="out-in">
          <div :key="active.key" class="grid gap-6 p-8 md:grid-cols-[1fr_1fr]">
            <div>
              <h3 class="font-display text-2xl font-semibold text-ink-900">{{ active.title }}</h3>
              <p class="mt-3 text-sm leading-7 text-ink-700">{{ active.body }}</p>
            </div>
            <ul class="space-y-3 md:border-l md:border-hairline md:pl-8">
              <li v-for="p in active.points" :key="p" class="flex items-start gap-3 text-sm text-ink-700">
                <span class="mt-1 h-1.5 w-6 shrink-0 rounded-full bg-accent-600" aria-hidden="true" />{{ p }}
              </li>
            </ul>
          </div>
        </Transition>
      </div>
    </section>

    <!-- Hierarchy ladder -->
    <section class="border-y border-hairline bg-surface/50">
      <div class="mx-auto max-w-content px-6 py-16">
        <h2 v-reveal class="font-display text-3xl font-semibold text-ink-900">A role for everyone, access for no one extra</h2>
        <div class="relative mt-8">
          <div class="absolute bottom-4 left-2 top-4 w-px bg-hairline" aria-hidden="true" />
          <div class="space-y-3">
            <div
              v-for="(level, i) in hierarchy"
              :key="level.role"
              v-reveal
              class="card-lift relative flex flex-wrap items-center justify-between gap-2 rounded-md border border-hairline bg-surface px-5 py-4"
              :style="{ marginLeft: `${i * 1.75}rem`, transitionDelay: `${i * 90}ms` }"
            >
              <span class="absolute -left-[7px] top-1/2 h-3 w-3 -translate-y-1/2 rounded-full border-2 border-primary-600 bg-surface" aria-hidden="true" />
              <span class="font-semibold text-ink-900">{{ level.role }}</span>
              <span class="text-sm text-ink-500">{{ level.note }}</span>
            </div>
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

<style scoped>
.swap-enter-active,
.swap-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.swap-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.swap-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
@media (prefers-reduced-motion: reduce) {
  .swap-enter-active,
  .swap-leave-active {
    transition: none;
  }
}
</style>
