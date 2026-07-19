<script setup lang="ts">
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import SButton from "../../components/ui/SButton.vue";
import SCard from "../../components/ui/SCard.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
const router = useRouter();
const email = ref("");
const password = ref("");
const demoModels = [
  {
    key: "school",
    title: "School Owner",
    subtitle: "Full school ERP, teachers, students, attendance, fees, HR and timetable.",
    role: "owner",
    model: "school",
  },
  {
    key: "institute",
    title: "Institute Owner",
    subtitle: "Teacher-student learning workspace with classrooms, curriculum and insights.",
    role: "owner",
    model: "institute",
  },
  {
    key: "individual",
    title: "Individual Student",
    subtitle: "Self-paced learner workspace for personal curriculum and practice.",
    role: "student",
    model: "individual",
  },
  {
    key: "platform",
    title: "Platform Admin",
    subtitle: "App-owner dashboard for schools, users, content and audit visibility.",
    role: "platform_admin",
    model: "platform",
  },
] as const;

async function submit() {
  if (await session.login(email.value, password.value)) router.push("/app");
}

async function demo(option: (typeof demoModels)[number]) {
  await session.demoLogin(option.role, option.model);
  router.push(option.model === "platform" ? "/admin" : "/app");
}
</script>

<template>
  <div class="mx-auto grid max-w-6xl gap-8 px-6 py-16 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] lg:items-start">
    <SCard raised class="w-full">
      <p class="s-eyebrow">Welcome back</p>
      <h1 class="mt-2 font-display text-2xl font-semibold text-ink-900">Sign in to Slate</h1>

      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <label class="text-sm font-medium text-ink-700" for="email">Email</label>
          <input id="email" v-model="email" type="email" autocomplete="email" class="s-input mt-1" required />
        </div>
        <div>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-ink-700" for="password">Password</label>
            <RouterLink to="/forgot-password" class="text-xs font-medium text-primary-600 hover:text-primary-500">
              Forgot password?
            </RouterLink>
          </div>
          <input id="password" v-model="password" type="password" autocomplete="current-password" class="s-input mt-1" required />
        </div>
        <p v-if="session.error" class="rounded-sm border border-danger/30 bg-danger-bg px-3 py-2 text-sm text-danger">
          {{ session.error }}
        </p>
        <SButton type="submit" variant="primary" block :disabled="session.loading === 'login'">
          {{ session.loading === "login" ? "Signing in..." : "Sign in" }}
        </SButton>
      </form>

      <p class="mt-4 text-center text-sm text-ink-500">
        New to Slate?
        <RouterLink to="/signup" class="font-semibold text-primary-600 hover:text-primary-500">Create an account</RouterLink>
      </p>
    </SCard>
    <section class="space-y-4">
      <div>
        <p class="s-eyebrow">Explore a demo workspace</p>
        <h2 class="mt-2 font-display text-2xl font-semibold text-ink-900">Choose how Slate is used</h2>
      </div>
      <div class="grid gap-3 sm:grid-cols-2">
        <button
          v-for="option in demoModels"
          :key="option.key"
          type="button"
          class="s-focus rounded-lg border border-hairline bg-surface p-4 text-left transition hover:border-primary-500 hover:bg-primary-50"
          :disabled="!!session.loading"
          @click="demo(option)"
        >
          <span class="block font-display text-lg font-semibold text-ink-900">{{ option.title }}</span>
          <span class="mt-2 block text-sm leading-6 text-ink-600">{{ option.subtitle }}</span>
          <span class="mt-4 block text-sm font-semibold text-primary-700">
            {{ session.loading === `demo-${option.model}` ? "Opening..." : "Open demo" }}
          </span>
        </button>
      </div>
    </section>
  </div>
</template>
