<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore, type AdmissionApplication } from "../../../stores/session";

const session = useSessionStore();
const showForm = ref(false);
const form = ref({ applicant_name: "", applicant_email: "", grade: "", notes: "" });
const editingId = ref<number | null>(null);

const columns = [
  { key: "applied", label: "Applied", tone: "neutral" as const },
  { key: "reviewing", label: "Reviewing", tone: "info" as const },
  { key: "accepted", label: "Accepted", tone: "success" as const },
  { key: "enrolled", label: "Enrolled", tone: "primary" as const },
  { key: "rejected", label: "Rejected", tone: "danger" as const },
];

onMounted(() => session.loadApplications());

function byStatus(status: string): AdmissionApplication[] {
  return session.applications.filter((a) => a.status === status);
}

async function submit() {
  const saved = editingId.value
    ? await session.updateApplication(editingId.value, { ...form.value })
    : await session.createApplication({ ...form.value });
  if (saved) {
    form.value = { applicant_name: "", applicant_email: "", grade: "", notes: "" };
    editingId.value = null;
    showForm.value = false;
  }
}
function edit(app: AdmissionApplication) {
  editingId.value = app.id;
  form.value = { applicant_name: app.applicant_name, applicant_email: app.applicant_email || "", grade: app.grade || "", notes: app.notes || "" };
  showForm.value = true;
}
async function remove(app: AdmissionApplication) {
  if (window.confirm(`Delete ${app.applicant_name}'s application?`)) await session.deleteApplication(app.id);
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Admissions" title="Applicant pipeline" subtitle="From enquiry to enrolled. Track every applicant.">
      <template #actions>
        <SButton variant="primary" @click="showForm = !showForm">{{ showForm ? "Close" : "New application" }}</SButton>
      </template>
    </SPageHeader>

    <form v-if="showForm" class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-2" @submit.prevent="submit">
      <label class="text-sm">Applicant name<input v-model="form.applicant_name" class="s-input mt-1" required /></label>
      <label class="text-sm">Email<input v-model="form.applicant_email" type="email" class="s-input mt-1" /></label>
      <label class="text-sm">Grade applying for<input v-model="form.grade" class="s-input mt-1" /></label>
      <label class="text-sm">Notes<input v-model="form.notes" class="s-input mt-1" /></label>
      <div class="sm:col-span-2">
        <SButton type="submit" variant="primary" :disabled="!form.applicant_name.trim() || session.loading === 'create-application'">
          {{ session.loading === "create-application" ? "Adding..." : editingId ? "Save application" : "Add application" }}
        </SButton>
      </div>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <SLoadingState v-if="session.loading === 'admissions' && !session.applications.length" :rows="3" />
    <div v-else class="grid gap-4 lg:grid-cols-5">
      <div v-for="col in columns" :key="col.key" class="rounded-lg border border-hairline bg-surface/60 p-3">
        <div class="mb-3 flex items-center justify-between px-1">
          <span class="text-sm font-semibold text-ink-900">{{ col.label }}</span>
          <SBadge :tone="col.tone">{{ byStatus(col.key).length }}</SBadge>
        </div>
        <div class="space-y-3">
          <article v-for="app in byStatus(col.key)" :key="app.id" class="card-lift rounded-md border border-hairline bg-surface p-3">
            <p class="text-sm font-semibold text-ink-900">{{ app.applicant_name }}</p>
            <p v-if="app.grade" class="text-xs text-ink-500">Grade {{ app.grade }}</p>
            <p v-if="app.applicant_email" class="truncate text-xs text-ink-500">{{ app.applicant_email }}</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <SButton v-if="app.status !== 'enrolled'" variant="ghost" @click="edit(app)">Edit</SButton>
              <SButton v-if="app.status !== 'enrolled'" variant="ghost" @click="remove(app)">Delete</SButton>
              <SButton v-if="app.status === 'applied'" variant="secondary" :disabled="session.loading === `application-${app.id}`" @click="session.setApplicationStatus(app.id, 'reviewing')">Review</SButton>
              <template v-if="app.status === 'reviewing'">
                <SButton variant="primary" :disabled="session.loading === `application-${app.id}`" @click="session.setApplicationStatus(app.id, 'accepted')">Accept</SButton>
                <SButton variant="ghost" :disabled="session.loading === `application-${app.id}`" @click="session.setApplicationStatus(app.id, 'rejected')">Reject</SButton>
              </template>
              <SButton v-if="app.status === 'accepted'" variant="primary" :disabled="session.loading === `application-${app.id}`" @click="session.enrollApplication(app.id)">Enroll</SButton>
              <span v-if="app.status === 'enrolled'" class="text-xs font-semibold text-primary-600">Enrolled ✓</span>
            </div>
          </article>
          <p v-if="!byStatus(col.key).length" class="px-1 py-4 text-center text-xs text-ink-500">Empty</p>
        </div>
      </div>
    </div>
  </div>
</template>
