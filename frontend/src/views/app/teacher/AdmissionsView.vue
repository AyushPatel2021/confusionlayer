<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SConfirmDialog from "../../../components/ui/SConfirmDialog.vue";
import SDatePicker from "../../../components/ui/SDatePicker.vue";
import SKanbanBoard from "../../../components/ui/SKanbanBoard.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore, type AdmissionApplication } from "../../../stores/session";

const session = useSessionStore();
const showForm = ref(false);
const form = ref({ applicant_name: "", applicant_email: "", grade: "", source: "", date_of_birth: "", notes: "" });
const editingId = ref<number | null>(null);
const applicationToDelete = ref<AdmissionApplication | null>(null);

const columns = [
  { key: "applied", label: "Applied", tone: "neutral" as const },
  { key: "reviewing", label: "Reviewing", tone: "info" as const },
  { key: "accepted", label: "Accepted", tone: "success" as const },
  { key: "enrolled", label: "Enrolled", tone: "primary" as const },
  { key: "rejected", label: "Rejected", tone: "danger" as const },
];

onMounted(async () => {
  await Promise.all([session.loadApplications(), session.loadDashboard()]);
});

const classroomOptions = computed(() => (session.dashboard?.classrooms || []).map((room) => ({ label: room.name, value: room.name, hint: room.subject.name })));
const boardItems = computed(() => session.applications.map((app) => ({ id: app.id, status: app.status, title: app.applicant_name, subtitle: app.grade ? `Class ${app.grade}` : app.source || "", meta: app.applicant_email || app.source || "" })));

async function submit() {
  const saved = editingId.value
    ? await session.updateApplication(editingId.value, { ...form.value })
    : await session.createApplication({ ...form.value });
  if (saved) {
    form.value = { applicant_name: "", applicant_email: "", grade: "", source: "", date_of_birth: "", notes: "" };
    editingId.value = null;
    showForm.value = false;
  }
}
function edit(app: AdmissionApplication) {
  editingId.value = app.id;
  form.value = { applicant_name: app.applicant_name, applicant_email: app.applicant_email || "", grade: app.grade || "", source: app.source || "", date_of_birth: app.date_of_birth || "", notes: app.notes || "" };
  showForm.value = true;
}
async function remove() {
  if (applicationToDelete.value && await session.deleteApplication(applicationToDelete.value.id)) applicationToDelete.value = null;
}
function selectBoardItem(item: { id: string | number }) {
  const app = session.applications.find((entry) => entry.id === Number(item.id));
  if (app) edit(app);
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Admissions" title="Applicant pipeline" subtitle="From enquiry to enrolled. Track every applicant.">
      <template #actions>
        <SButton variant="primary" @click="showForm = !showForm">{{ showForm ? "Close" : "New application" }}</SButton>
      </template>
    </SPageHeader>

    <form v-if="showForm" class="rounded-lg border border-hairline bg-surface p-5" @submit.prevent="submit">
      <div class="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <section class="space-y-3">
          <p class="s-eyebrow">Applicant</p>
          <label class="text-sm">Applicant name<input v-model="form.applicant_name" class="s-input mt-1" required /></label>
          <label class="text-sm">Email<input v-model="form.applicant_email" type="email" class="s-input mt-1" /></label>
          <SDatePicker v-model="form.date_of_birth" label="Date of birth" />
        </section>
        <section class="space-y-3">
          <p class="s-eyebrow">Admission target</p>
          <SCombobox v-model="form.grade" label="Class applying for" placeholder="Choose class" :options="classroomOptions" />
          <label class="text-sm">Source<input v-model="form.source" class="s-input mt-1" placeholder="Referral, walk-in..." /></label>
          <label class="text-sm">Notes<textarea v-model="form.notes" class="s-input mt-1 min-h-24 py-2" /></label>
        </section>
      </div>
      <div class="sm:col-span-2">
        <SButton type="submit" variant="primary" :disabled="!form.applicant_name.trim() || session.loading === 'create-application'">
          {{ session.loading === "create-application" ? "Adding..." : editingId ? "Save application" : "Add application" }}
        </SButton>
      </div>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <SLoadingState v-if="session.loading === 'admissions' && !session.applications.length" :rows="3" />
    <SKanbanBoard v-else :columns="columns" :items="boardItems" @select="selectBoardItem" />
    <section v-if="session.applications.length" class="rounded-lg border border-hairline bg-surface p-5">
      <p class="s-eyebrow">Quick actions</p>
      <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <article v-for="app in session.applications.filter((entry) => entry.status !== 'enrolled')" :key="app.id" class="rounded-md border border-hairline p-3">
          <p class="text-sm font-semibold text-ink-900">{{ app.applicant_name }}</p>
          <p class="text-xs text-ink-500">{{ app.grade || app.source || "Applicant" }}</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <SButton variant="ghost" @click="edit(app)">Edit</SButton>
            <SButton variant="ghost" @click="applicationToDelete = app">Delete</SButton>
            <SButton v-if="app.status === 'applied'" variant="secondary" :disabled="session.loading === `application-${app.id}`" @click="session.setApplicationStatus(app.id, 'reviewing')">Review</SButton>
            <template v-if="app.status === 'reviewing'">
              <SButton variant="primary" :disabled="session.loading === `application-${app.id}`" @click="session.setApplicationStatus(app.id, 'accepted')">Accept</SButton>
              <SButton variant="ghost" :disabled="session.loading === `application-${app.id}`" @click="session.setApplicationStatus(app.id, 'rejected')">Reject</SButton>
            </template>
            <SButton v-if="app.status === 'accepted'" variant="primary" :disabled="session.loading === `application-${app.id}`" @click="session.enrollApplication(app.id)">Enroll</SButton>
          </div>
        </article>
      </div>
    </section>
    <SConfirmDialog
      :open="!!applicationToDelete"
      title="Delete application"
      :message="`Delete ${applicationToDelete?.applicant_name || 'this applicant'}'s application?`"
      confirm-label="Delete"
      :busy="!!applicationToDelete && session.loading === `application-${applicationToDelete.id}`"
      @cancel="applicationToDelete = null"
      @confirm="remove"
    />
  </div>
</template>
