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
const demoRoles = ["owner", "school_admin", "accountant", "hr", "teacher", "student", "parent"] as const;

async function submit() {
  if (await session.login(email.value, password.value)) router.push("/app");
}

async function demo(role: "owner" | "school_admin" | "accountant" | "hr" | "teacher" | "student" | "parent") {
  await session.demoLogin(role);
  router.push("/app");
}
</script>

<template>
  <div class="mx-auto flex max-w-reading flex-col items-center px-6 py-20">
    <SCard raised class="w-full max-w-md">
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

      <div class="mt-6 border-t border-hairline pt-5">
        <p class="text-center text-xs font-medium uppercase tracking-wide text-ink-500">Or explore the sample school</p>
        <div class="mt-3 grid grid-cols-2 gap-2">
          <SButton v-for="role in demoRoles" :key="role" variant="secondary" block :disabled="!!session.loading" @click="demo(role)">{{ role.replace('_', ' ') }} demo</SButton>
        </div>
      </div>
    </SCard>
  </div>
</template>
