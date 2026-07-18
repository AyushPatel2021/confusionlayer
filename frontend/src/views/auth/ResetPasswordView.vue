<script setup lang="ts">
import { ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import SButton from "../../components/ui/SButton.vue";
import SCard from "../../components/ui/SCard.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const token = String(route.params.token || "");
const password = ref("");
const done = ref(false);

async function submit() {
  if (await session.resetPassword(token, password.value)) done.value = true;
}
</script>

<template>
  <div class="mx-auto flex max-w-reading flex-col items-center px-6 py-20">
    <SCard raised class="w-full max-w-md">
      <p class="s-eyebrow">Password help</p>
      <h1 class="mt-2 font-display text-2xl font-semibold text-ink-900">Choose a new password</h1>

      <div v-if="done" class="mt-5 space-y-4">
        <p class="rounded-md border border-success/30 bg-success-bg px-4 py-3 text-sm text-success">
          Your password has been reset.
        </p>
        <SButton variant="primary" block @click="router.push('/login')">Sign in</SButton>
      </div>
      <form v-else class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <label class="text-sm font-medium text-ink-700" for="password">New password</label>
          <input id="password" v-model="password" type="password" autocomplete="new-password" class="s-input mt-1" minlength="8" required />
        </div>
        <p v-if="session.error" class="rounded-sm border border-danger/30 bg-danger-bg px-3 py-2 text-sm text-danger">
          {{ session.error }}
        </p>
        <SButton type="submit" variant="primary" block :disabled="session.loading === 'reset'">
          {{ session.loading === "reset" ? "Saving..." : "Reset password" }}
        </SButton>
      </form>

      <p class="mt-4 text-center text-sm text-ink-500">
        <RouterLink to="/login" class="font-semibold text-primary-600 hover:text-primary-500">Back to sign in</RouterLink>
      </p>
    </SCard>
  </div>
</template>
