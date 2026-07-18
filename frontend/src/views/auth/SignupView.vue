<script setup lang="ts">
import { ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import SButton from "../../components/ui/SButton.vue";
import SCard from "../../components/ui/SCard.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
const router = useRouter();
const route = useRoute();

const segments = [
  { value: "school", label: "School", hint: "Admissions, fees, staff & learning" },
  { value: "institute", label: "Tuition institute", hint: "Teaching & learning" },
  { value: "individual", label: "Individual learner", hint: "Just for me" },
];

const segment = ref(typeof route.query.segment === "string" ? route.query.segment : "school");
const orgName = ref("");
const name = ref("");
const email = ref("");
const password = ref("");

async function submit() {
  const ok = await session.register({
    org_name: orgName.value,
    segment: segment.value,
    name: name.value,
    email: email.value,
    password: password.value,
  });
  if (ok) router.push("/app");
}
</script>

<template>
  <div class="mx-auto flex max-w-reading flex-col items-center px-6 py-16">
    <SCard raised class="w-full max-w-lg">
      <p class="s-eyebrow">Get started, free</p>
      <h1 class="mt-2 font-display text-2xl font-semibold text-ink-900">Create your Slate workspace</h1>

      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <span class="text-sm font-medium text-ink-700">I'm signing up as a...</span>
          <div class="mt-2 grid gap-2 sm:grid-cols-3">
            <button
              v-for="option in segments"
              :key="option.value"
              type="button"
              class="s-focus rounded-md border p-3 text-left transition"
              :class="segment === option.value ? 'border-primary-600 bg-primary-50' : 'border-hairline bg-surface hover:border-ink-300'"
              @click="segment = option.value"
            >
              <span class="block text-sm font-semibold text-ink-900">{{ option.label }}</span>
              <span class="mt-1 block text-xs text-ink-500">{{ option.hint }}</span>
            </button>
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-ink-700" for="org">{{ segment === "individual" ? "Workspace name" : "Organization name" }}</label>
          <input id="org" v-model="orgName" class="s-input mt-1" required />
        </div>
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="text-sm font-medium text-ink-700" for="name">Your name</label>
            <input id="name" v-model="name" class="s-input mt-1" required />
          </div>
          <div>
            <label class="text-sm font-medium text-ink-700" for="email">Email</label>
            <input id="email" v-model="email" type="email" autocomplete="email" class="s-input mt-1" required />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-ink-700" for="password">Password</label>
          <input id="password" v-model="password" type="password" autocomplete="new-password" class="s-input mt-1" minlength="8" required />
          <p class="mt-1 text-xs text-ink-500">At least 8 characters.</p>
        </div>
        <p v-if="session.error" class="rounded-sm border border-danger/30 bg-danger-bg px-3 py-2 text-sm text-danger">
          {{ session.error }}
        </p>
        <SButton type="submit" variant="primary" block :disabled="session.loading === 'register'">
          {{ session.loading === "register" ? "Creating..." : "Create workspace" }}
        </SButton>
        <p class="text-center text-xs text-ink-500">All plans are free. No card required.</p>
      </form>

      <p class="mt-4 text-center text-sm text-ink-500">
        Already have an account?
        <RouterLink to="/login" class="font-semibold text-primary-600 hover:text-primary-500">Sign in</RouterLink>
      </p>
    </SCard>
  </div>
</template>
