<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";

import SButton from "../../components/ui/SButton.vue";
import SCard from "../../components/ui/SCard.vue";
import { useSessionStore } from "../../stores/session";

const session = useSessionStore();
const email = ref("");
const sent = ref(false);

async function submit() {
  if (await session.forgotPassword(email.value)) sent.value = true;
}
</script>

<template>
  <div class="mx-auto flex max-w-reading flex-col items-center px-6 py-20">
    <SCard raised class="w-full max-w-md">
      <p class="s-eyebrow">Password help</p>
      <h1 class="mt-2 font-display text-2xl font-semibold text-ink-900">Reset your password</h1>

      <div v-if="sent" class="mt-5 rounded-md border border-success/30 bg-success-bg px-4 py-3 text-sm text-success">
        If an account exists for that email, we've sent a reset link. Check your inbox (and, in this demo build, the
        server logs).
      </div>
      <form v-else class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <label class="text-sm font-medium text-ink-700" for="email">Email</label>
          <input id="email" v-model="email" type="email" autocomplete="email" class="s-input mt-1" required />
        </div>
        <SButton type="submit" variant="primary" block :disabled="session.loading === 'forgot'">
          {{ session.loading === "forgot" ? "Sending…" : "Send reset link" }}
        </SButton>
      </form>

      <p class="mt-4 text-center text-sm text-ink-500">
        <RouterLink to="/login" class="font-semibold text-primary-600 hover:text-primary-500">Back to sign in</RouterLink>
      </p>
    </SCard>
  </div>
</template>
