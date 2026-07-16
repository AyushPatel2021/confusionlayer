<script setup lang="ts">
import { useRouter } from "vue-router";

import SButton from "../../components/ui/SButton.vue";
import SCard from "../../components/ui/SCard.vue";
import { useSessionStore } from "../../stores/session";

// M0 placeholder. Real signup/login + org onboarding land in M2/M3. For now this
// screen offers the existing demo entry so the app stays usable during the rewrite.
const session = useSessionStore();
const router = useRouter();

async function demo(role: "teacher" | "student") {
  await session.demoLogin(role);
  router.push("/app");
}
</script>

<template>
  <div class="mx-auto flex max-w-reading flex-col items-center px-6 py-24">
    <SCard raised class="w-full max-w-md">
      <p class="s-eyebrow">Welcome back</p>
      <h1 class="mt-2 font-display text-2xl font-semibold text-ink-900">Sign in to Slate</h1>
      <p class="mt-2 text-sm leading-6 text-ink-500">
        Real signup, login, and organization onboarding are coming next. For now, explore the live learning
        experience with a demo role.
      </p>
      <div class="mt-6 flex flex-col gap-3">
        <SButton variant="primary" block :disabled="!!session.loading" @click="demo('teacher')">
          Continue as a teacher (demo)
        </SButton>
        <SButton variant="secondary" block :disabled="!!session.loading" @click="demo('student')">
          Continue as a student (demo)
        </SButton>
      </div>
      <p v-if="session.error" class="mt-4 rounded-sm border border-danger/30 bg-danger-bg px-3 py-2 text-sm text-danger">
        {{ session.error }}
      </p>
    </SCard>
  </div>
</template>
