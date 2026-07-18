<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const newSubject = ref("");
const selectedId = ref<number | null>(null);
const newChapter = ref("");
const newConcept = ref<Record<number, string>>({});

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
          <div class="flex items-center justify-between">
            <h2 class="font-display text-xl font-semibold text-ink-900">{{ tree.name }}</h2>
            <SBadge v-if="!editable" tone="neutral">read-only</SBadge>
          </div>

          <div v-for="chapter in tree.chapters" :key="chapter.id" class="rounded-lg border border-hairline bg-surface p-5">
            <p class="font-display text-base font-semibold text-ink-900">{{ chapter.order }}. {{ chapter.title }}</p>
            <ul class="mt-3 space-y-1">
              <li v-for="c in chapter.concepts" :key="c.id" class="flex items-center gap-2 text-sm text-ink-700">
                <span class="h-1 w-4 rounded-full bg-accent-600" aria-hidden="true" />{{ c.title }}
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
  </div>
</template>
