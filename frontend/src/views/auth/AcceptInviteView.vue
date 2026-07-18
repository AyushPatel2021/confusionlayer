<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import SButton from "../../components/ui/SButton.vue";
import SCard from "../../components/ui/SCard.vue";
import { useSessionStore, type InvitationPreview } from "../../stores/session";

const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const token = String(route.params.token || "");
const invitation = ref<InvitationPreview | null>(null);
const loaded = ref(false);
const name = ref("");
const password = ref("");
const phone = ref("");
const rollNumber = ref("");

onMounted(async () => {
  invitation.value = await session.fetchInvitation(token);
  loaded.value = true;
});

async function submit() {
  if (await session.acceptInvitation(token, password.value, name.value, { phone: phone.value, roll_number: rollNumber.value })) router.push("/app");
}
</script>

<template>
  <div class="mx-auto flex max-w-reading flex-col items-center px-6 py-20">
    <SCard raised class="w-full max-w-md">
      <p class="s-eyebrow">You're invited</p>

      <div v-if="!loaded" class="mt-6 h-24 animate-pulse rounded-md border border-hairline bg-surface-sunken" />

      <div v-else-if="!invitation" class="mt-4">
        <h1 class="font-display text-2xl font-semibold text-ink-900">Invitation unavailable</h1>
        <p class="mt-2 text-sm text-ink-500">{{ session.error || "This invitation is invalid or has expired." }}</p>
        <RouterLink to="/login" class="mt-4 inline-block text-sm font-semibold text-primary-600">Back to sign in</RouterLink>
      </div>

      <div v-else class="mt-2">
        <h1 class="font-display text-2xl font-semibold text-ink-900">Join {{ invitation.organization_name }}</h1>
        <p class="mt-2 text-sm text-ink-500">
          Invited as <span class="font-semibold text-ink-700">{{ invitation.role }}</span> ({{ invitation.email }}).
        </p>
        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div>
            <label class="text-sm font-medium text-ink-700" for="name">Your name</label>
            <input id="name" v-model="name" class="s-input mt-1" required />
          </div>
          <div>
            <label class="text-sm font-medium text-ink-700" for="password">Create a password</label>
            <input id="password" v-model="password" type="password" autocomplete="new-password" class="s-input mt-1" minlength="8" required />
          </div>
          <div><label class="text-sm font-medium text-ink-700" for="phone">Phone (optional)</label><input id="phone" v-model="phone" class="s-input mt-1" autocomplete="tel" /></div>
          <div v-if="invitation.role === 'student'"><label class="text-sm font-medium text-ink-700" for="roll-number">Roll number (optional)</label><input id="roll-number" v-model="rollNumber" class="s-input mt-1" /></div>
          <p v-if="session.error" class="rounded-sm border border-danger/30 bg-danger-bg px-3 py-2 text-sm text-danger">
            {{ session.error }}
          </p>
          <SButton type="submit" variant="primary" block :disabled="session.loading === 'accept'">
            {{ session.loading === "accept" ? "Joining..." : "Accept invitation" }}
          </SButton>
        </form>
      </div>
    </SCard>
  </div>
</template>
