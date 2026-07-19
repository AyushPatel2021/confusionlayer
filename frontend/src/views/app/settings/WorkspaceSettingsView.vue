<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const form = ref({ name: "", logo_url: "", timezone: "Asia/Kolkata", currency: "INR" });
const saved = ref(false);
const currencyOptions = [{ label: "INR", value: "INR" }, { label: "USD", value: "USD" }, { label: "GBP", value: "GBP" }];
onMounted(async () => { await session.loadOrgSettings(); if (session.orgSettings) form.value = { name: session.orgSettings.name, logo_url: session.orgSettings.logo_url || "", timezone: session.orgSettings.timezone, currency: session.orgSettings.currency }; });
watch(() => session.orgSettings, (value) => { if (value) form.value = { name: value.name, logo_url: value.logo_url || "", timezone: value.timezone, currency: value.currency }; });
async function submit() { saved.value = await session.saveOrgSettings(form.value); }
</script>

<template>
  <div class="max-w-3xl space-y-8">
    <SPageHeader eyebrow="Settings" title="Workspace settings" subtitle="Control the school name, branding, timezone, and currency used in records." />
    <form class="grid gap-5 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-2" @submit.prevent="submit">
      <label class="text-sm">School name<input v-model="form.name" class="s-input mt-1" required /></label>
      <label class="text-sm">Logo URL<input v-model="form.logo_url" class="s-input mt-1" type="url" placeholder="https://..." /></label>
      <label class="text-sm">Timezone<input v-model="form.timezone" class="s-input mt-1" required /></label>
      <SCombobox v-model="form.currency" label="Currency" placeholder="Choose currency" :options="currencyOptions" />
      <div class="sm:col-span-2 flex items-center gap-3"><SButton type="submit" variant="primary" :disabled="session.loading === 'org-settings'">Save settings</SButton><span v-if="saved" class="text-sm text-success">Saved.</span></div>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>
  </div>
</template>
