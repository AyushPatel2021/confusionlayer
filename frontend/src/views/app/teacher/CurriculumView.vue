<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SConfirmDialog from "../../../components/ui/SConfirmDialog.vue";
import SDialog from "../../../components/ui/SDialog.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const newSubject = ref("");
const selectedId = ref<number | null>(null);
const newChapter = ref("");
const newConcept = ref<Record<number, string>>({});
const renameTarget = ref<{ path: string; current: string; subjectId: number; kind: "title" | "name"; value: string } | null>(null);
const deleteTarget = ref<{ path: string; subjectId?: number; label: string } | null>(null);

const tree = computed(() => session.curriculumTree);
const editable = computed(() => tree.value && tree.value.org_id !== null && tree.value.org_id === session.user?.org_id);

onMounted(() => session.loadCurriculumSubjects());

async function addSubject() {
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
        <form class="flex gap-2" @submit.prevent="addSubject">
          <input v-model="newSubject" class="s-input" placeholder="New subject name" />
          <SButton type="submit" variant="primary" :disabled="!newSubject.trim() || session.loading === 'create-subject'">Add</SButton>
        </form>
        <SLoadingState v-if="session.loading === 'curriculum' && !session.curriculumSubjects.length" :rows="3" />
        <ul v-else class="space-y-2">
          <li v-for="s in session.curriculumSubjects" :key="s.id">
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
        </ul>
      </aside>

      <!-- Tree editor -->
      <section>
        <SEmptyState v-if="!tree" title="Select a subject" message="Pick a subject on the left, or create one, to manage its chapters and topics." />
        <div v-else class="space-y-5">
          <div class="flex items-center justify-between gap-3">
            <h2 class="font-display text-xl font-semibold text-ink-900">{{ tree.name }}</h2>
            <div class="flex items-center gap-2"><SBadge v-if="!editable" tone="neutral">read-only</SBadge><template v-if="editable"><SButton variant="ghost" @click="rename(`/api/curriculum/subjects/${tree.id}`, tree.name, tree.id, 'name')">Edit</SButton><SButton variant="ghost" @click="remove(`/api/curriculum/subjects/${tree.id}`, undefined, tree.name)">Delete</SButton></template></div>
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
