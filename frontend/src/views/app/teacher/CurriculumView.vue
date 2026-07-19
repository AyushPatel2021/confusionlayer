<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SConfirmDialog from "../../../components/ui/SConfirmDialog.vue";
import SDialog from "../../../components/ui/SDialog.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const newSubject = ref("");
const classroomFilter = ref<number | null>(null);
const selectedId = ref<number | null>(null);
const newChapter = ref("");
const newConcept = ref<Record<number, string>>({});
const renameTarget = ref<{ path: string; current: string; subjectId: number; kind: "title" | "name"; value: string } | null>(null);
const deleteTarget = ref<{ path: string; subjectId?: number; label: string } | null>(null);

const tree = computed(() => session.curriculumTree);
const editable = computed(() => tree.value && tree.value.org_id !== null && tree.value.org_id === session.user?.org_id);
const classrooms = computed(() => session.dashboard?.classrooms || []);
const classroomOptions = computed(() => classrooms.value.map((room) => ({ label: room.name, value: room.id, hint: room.subject.name })));
const scopedSubjectIds = computed(() => new Set(classrooms.value.filter((room) => !classroomFilter.value || room.id === classroomFilter.value).map((room) => room.subject.id)));
const visibleSubjects = computed(() => {
  if (!classrooms.value.length) return session.curriculumSubjects;
  return session.curriculumSubjects.filter((subject) => scopedSubjectIds.value.has(subject.id));
});
const canCreateSubject = computed(() => session.isOrgAdmin);

onMounted(async () => {
  await Promise.all([session.loadDashboard(), session.loadCurriculumSubjects()]);
  classroomFilter.value = classrooms.value[0]?.id || null;
  const firstSubject = visibleSubjects.value[0];
  if (firstSubject) await select(firstSubject.id);
});

async function addSubject() {
  if (!canCreateSubject.value) return;
  const created = await session.createSubject({ name: newSubject.value });
  if (created) {
    newSubject.value = "";
    await select(created.id);
  }
}
async function select(id: number) {
  selectedId.value = id;
  await session.loadSubjectTree(id);
}
async function addChapter() {
  if (!selectedId.value || !newChapter.value.trim()) return;
  await session.createChapter(selectedId.value, newChapter.value.trim());
  newChapter.value = "";
}
async function addConcept(chapterId: number) {
  const title = (newConcept.value[chapterId] || "").trim();
  if (!selectedId.value || !title) return;
  await session.createConcept(selectedId.value, chapterId, title);
  newConcept.value[chapterId] = "";
}
function rename(path: string, current: string, subjectId: number, kind: "title" | "name" = "title") {
  renameTarget.value = { path, current, subjectId, kind, value: current };
}
async function saveRename() {
  if (!renameTarget.value) return;
  const value = renameTarget.value.value.trim();
  if (!value) return;
  const target = renameTarget.value;
  await session.updateCurriculumItem(target.path, target.kind === "name" ? { name: value, board: tree.value?.board, class_level: tree.value?.class_level } : { title: value }, target.subjectId);
  renameTarget.value = null;
}
function remove(path: string, subjectId?: number, label = "this item") {
  deleteTarget.value = { path, subjectId, label };
}
async function confirmRemove() {
  if (!deleteTarget.value) return;
  await session.deleteCurriculumItem(deleteTarget.value.path, deleteTarget.value.subjectId);
  deleteTarget.value = null;
}
async function applyClassroomFilter() {
  const firstSubject = visibleSubjects.value[0];
  if (!firstSubject) {
    selectedId.value = null;
    session.curriculumTree = null;
    return;
  }
  if (!selectedId.value || !visibleSubjects.value.some((subject) => subject.id === selectedId.value)) {
    await select(firstSubject.id);
  }
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Curriculum" title="Subjects, chapters & topics" subtitle="Author your own curriculum, or import one from a document.">
      <template #actions>
        <RouterLink to="/app/curriculum/import"><SButton variant="secondary">Import from PDF</SButton></RouterLink>
      </template>
    </SPageHeader>

    <div class="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
      <!-- Subjects list -->
      <aside class="space-y-4">
        <SCombobox
          v-if="classroomOptions.length"
          v-model="classroomFilter"
          label="Classroom context"
          placeholder="Choose classroom"
          :options="classroomOptions"
          @change="applyClassroomFilter"
        />
        <form v-if="canCreateSubject" class="flex gap-2" @submit.prevent="addSubject">
          <input v-model="newSubject" class="s-input" placeholder="New subject name" />
          <SButton type="submit" variant="primary" :disabled="!newSubject.trim() || session.loading === 'create-subject'">Add</SButton>
        </form>
        <p v-else class="rounded-md border border-hairline bg-surface px-4 py-3 text-sm text-ink-500">Showing only curriculum connected to your assigned classroom.</p>
        <SLoadingState v-if="session.loading === 'curriculum' && !session.curriculumSubjects.length" :rows="3" />
        <ul v-else class="space-y-2">
          <li v-for="s in visibleSubjects" :key="s.id">
            <button
              class="s-focus flex w-full items-center justify-between gap-2 rounded-md border px-4 py-3 text-left text-sm transition"
              :class="selectedId === s.id ? 'border-primary-600 bg-primary-50' : 'border-hairline bg-surface hover:border-primary-500'"
              @click="select(s.id)"
            >
              <span>
                <span class="font-semibold text-ink-900">{{ s.name }}</span>
                <span class="block text-xs text-ink-500">{{ s.board }} | Class {{ s.class_level }} | {{ s.chapter_count }} chapters</span>
              </span>
              <SBadge v-if="s.shared" tone="neutral">shared</SBadge>
            </button>
          </li>
          <li v-if="!visibleSubjects.length" class="rounded-md border border-hairline bg-surface px-4 py-5 text-sm text-ink-500">No subject is connected to this classroom yet.</li>
        </ul>
      </aside>

      <!-- Tree editor -->
      <section>
        <SEmptyState v-if="!tree" title="Select a subject" message="Pick a subject on the left, or create one, to manage its chapters and topics." />
        <div v-else class="space-y-5">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="font-display text-xl font-semibold text-ink-900">{{ tree.name }}</h2>
              <p class="mt-1 text-sm text-ink-500">
                <template v-if="tree.assigned_classrooms.length">
                  Used by {{ tree.assigned_classrooms.map((item) => item.name).join(", ") }}
                </template>
                <template v-else>No classroom is using this subject yet.</template>
              </p>
            </div>
            <div class="flex items-center gap-2"><SBadge v-if="!editable" tone="neutral">read-only</SBadge><template v-if="editable"><SButton variant="ghost" @click="rename(`/api/curriculum/subjects/${tree.id}`, tree.name, tree.id, 'name')">Edit</SButton><SButton variant="ghost" @click="remove(`/api/curriculum/subjects/${tree.id}`, undefined, tree.name)">Delete</SButton></template></div>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <section class="rounded-lg border border-hairline bg-surface p-4">
              <p class="s-eyebrow">Assigned teachers</p>
              <div v-if="tree.assigned_teachers.length" class="mt-3 flex flex-wrap gap-2">
                <SBadge v-for="teacher in tree.assigned_teachers" :key="teacher.id" tone="primary">{{ teacher.name }}</SBadge>
              </div>
              <p v-else class="mt-3 text-sm text-ink-500">Assign a teacher by creating or editing a classroom for this subject.</p>
            </section>
            <section class="rounded-lg border border-hairline bg-surface p-4">
              <p class="s-eyebrow">Hierarchy</p>
              <p class="mt-2 text-sm text-ink-600">School -> Classroom -> Subject -> Teacher. Subject assignment is managed from Classrooms so one subject can be taught in multiple classes.</p>
              <RouterLink to="/app/classrooms" class="mt-3 inline-block text-sm font-semibold text-primary-700 hover:underline">Manage classroom assignments</RouterLink>
            </section>
          </div>

          <div v-for="chapter in tree.chapters" :key="chapter.id" class="rounded-lg border border-hairline bg-surface p-5">
            <div class="flex items-center justify-between gap-3"><p class="font-display text-base font-semibold text-ink-900">{{ chapter.order }}. {{ chapter.title }}</p><div v-if="editable" class="flex gap-2"><SButton variant="ghost" @click="rename(`/api/curriculum/chapters/${chapter.id}`, chapter.title, tree.id)">Edit</SButton><SButton variant="ghost" @click="remove(`/api/curriculum/chapters/${chapter.id}`, tree.id, chapter.title)">Delete</SButton></div></div>
            <ul class="mt-3 space-y-1">
              <li v-for="c in chapter.concepts" :key="c.id" class="flex items-center justify-between gap-2 text-sm text-ink-700">
                <span><span class="mr-2 inline-block h-1 w-4 rounded-full bg-accent-600" aria-hidden="true" />{{ c.title }}</span><span v-if="editable" class="flex gap-1"><SButton variant="ghost" @click="rename(`/api/curriculum/concepts/${c.id}`, c.title, tree.id)">Edit</SButton><SButton variant="ghost" @click="remove(`/api/curriculum/concepts/${c.id}`, tree.id, c.title)">Delete</SButton></span>
              </li>
              <li v-if="!chapter.concepts.length" class="text-sm text-ink-500">No topics yet.</li>
            </ul>
            <form v-if="editable" class="mt-3 flex gap-2" @submit.prevent="addConcept(chapter.id)">
              <input v-model="newConcept[chapter.id]" class="s-input" placeholder="Add a topic" />
              <SButton type="submit" variant="secondary" :disabled="session.loading === `create-concept-${chapter.id}`">Add</SButton>
            </form>
          </div>

          <form v-if="editable" class="flex gap-2" @submit.prevent="addChapter">
            <input v-model="newChapter" class="s-input" placeholder="Add a chapter" />
            <SButton type="submit" variant="primary" :disabled="!newChapter.trim() || session.loading === 'create-chapter'">Add chapter</SButton>
          </form>
        </div>
      </section>
    </div>
    <SDialog :open="!!renameTarget" title="Update name" size="sm" @close="renameTarget = null">
      <form v-if="renameTarget" class="space-y-4" @submit.prevent="saveRename">
        <label class="text-sm">Name<input v-model="renameTarget.value" class="s-input mt-1" required /></label>
        <div class="flex justify-end gap-2">
          <SButton variant="ghost" @click="renameTarget = null">Cancel</SButton>
          <SButton type="submit" variant="primary" :disabled="session.loading === 'curriculum-update'">Save</SButton>
        </div>
      </form>
    </SDialog>
    <SConfirmDialog
      :open="!!deleteTarget"
      title="Delete curriculum item"
      :message="`Delete ${deleteTarget?.label || 'this item'} and its dependent content?`"
      confirm-label="Delete"
      :busy="session.loading === 'curriculum-delete'"
      @cancel="deleteTarget = null"
      @confirm="confirmRemove"
    />
  </div>
</template>
