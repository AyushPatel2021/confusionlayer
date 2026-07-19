<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";

import SButton from "../../components/ui/SButton.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
import { displayRoleLabel, useSessionStore } from "../../stores/session";

const session = useSessionStore();
const profileSaved = ref(false);
const passwordSaved = ref(false);
const form = ref({ name: "", phone: "", contact_number: "", avatar_url: "" });
const passwords = ref({ current: "", next: "", confirm: "" });
const role = computed(() => displayRoleLabel(session.user));
const avatarInitials = computed(() => (form.value.name || "User").split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase());

watchEffect(() => {
  if (!session.user) return;
  form.value = {
    name: session.user.name || "",
    phone: session.user.profile?.phone || "",
    contact_number: session.user.profile?.contact_number || "",
    avatar_url: session.user.profile?.avatar_url || "",
  };
});

async function saveProfile() {
  profileSaved.value = false;
  if (await session.saveAccountProfile(form.value)) profileSaved.value = true;
}

async function changePassword() {
  passwordSaved.value = false;
  if (!passwords.value.next || passwords.value.next !== passwords.value.confirm) {
    session.error = "New passwords do not match";
    return;
  }
  if (await session.changeAccountPassword(passwords.value.current, passwords.value.next)) {
    passwords.value = { current: "", next: "", confirm: "" };
    passwordSaved.value = true;
  }
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Account" title="Profile and security" subtitle="Manage your personal details, contact fields and password." />

    <section class="grid gap-6 lg:grid-cols-[18rem_minmax(0,1fr)]">
      <aside class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex items-center gap-4">
          <img v-if="form.avatar_url" :src="form.avatar_url" alt="" class="h-16 w-16 rounded-full object-cover" />
          <div v-else class="flex h-16 w-16 items-center justify-center rounded-full bg-primary-600 font-semibold text-white">{{ avatarInitials }}</div>
          <div class="min-w-0">
            <p class="truncate font-semibold text-ink-900">{{ form.name || "User" }}</p>
            <p class="text-sm text-ink-500">{{ role }}</p>
          </div>
        </div>
        <dl class="mt-5 space-y-3 text-sm">
          <div><dt class="text-ink-500">Email</dt><dd class="font-medium text-ink-900">{{ session.user?.email }}</dd></div>
          <div><dt class="text-ink-500">Workspace</dt><dd class="font-medium text-ink-900">{{ session.user?.org_name || "Platform" }}</dd></div>
        </dl>
      </aside>

      <form class="grid gap-4 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-2" @submit.prevent="saveProfile">
        <label class="text-sm">Name<input v-model="form.name" class="s-input mt-1" required /></label>
        <label class="text-sm">Phone<input v-model="form.phone" class="s-input mt-1" autocomplete="tel" /></label>
        <label class="text-sm">Contact number<input v-model="form.contact_number" class="s-input mt-1" autocomplete="tel" /></label>
        <label class="text-sm">Profile image URL<input v-model="form.avatar_url" class="s-input mt-1" placeholder="https://..." /></label>
        <p v-if="profileSaved" class="text-sm text-success sm:col-span-2">Profile updated.</p>
        <p v-if="session.error" class="text-sm text-danger sm:col-span-2">{{ session.error }}</p>
        <div class="sm:col-span-2"><SButton type="submit" variant="primary" :disabled="!form.name.trim() || session.loading === 'account-profile'">Save profile</SButton></div>
      </form>
    </section>

    <form class="grid gap-4 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-3" @submit.prevent="changePassword">
      <label class="text-sm">Current password<input v-model="passwords.current" type="password" autocomplete="current-password" class="s-input mt-1" required /></label>
      <label class="text-sm">New password<input v-model="passwords.next" type="password" autocomplete="new-password" class="s-input mt-1" minlength="8" required /></label>
      <label class="text-sm">Confirm password<input v-model="passwords.confirm" type="password" autocomplete="new-password" class="s-input mt-1" minlength="8" required /></label>
      <p v-if="passwordSaved" class="text-sm text-success sm:col-span-3">Password updated.</p>
      <div class="sm:col-span-3"><SButton type="submit" variant="secondary" :disabled="!passwords.current || !passwords.next || session.loading === 'account-password'">Change password</SButton></div>
    </form>
  </div>
</template>
