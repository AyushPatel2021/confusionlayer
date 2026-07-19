<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { UploadCloud } from "@lucide/vue";

import SAIWorkingState from "../../../components/ui/SAIWorkingState.vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore, type CurriculumTree } from "../../../stores/session";

const session = useSessionStore();
const router = useRouter();

const name = ref("");
const board = ref("CBSE");
const classLevel = ref("10");
const fileInput = ref<HTMLInputElement | null>(null);
const savedTree = ref<CurriculumTree | null>(null);
const assignClassroomId = ref<number | null>(null);
const dragging = ref(false);

const classroomOptions = computed(() => session.classrooms.map((classroom) => ({ label: classroom.name, value: classroom.id, hint: classroom.subject.name })));

onMounted(async () => {
  await Promise.all([session.loadClassrooms(), session.loadClassroomOptions()]);
});

async function onFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  await readFile(file);
}

async function readFile(file?: File) {
  if (file) {
    if (!name.value) name.value = file.name.replace(/\.pdf$/i, "");
    await session.importPdf(file);
    savedTree.value = null;
  }
}

async function onDrop(event: DragEvent) {
  dragging.value = false;
  const file = event.dataTransfer?.files?.[0];
  await readFile(file);
}

function removeChapter(i: number) {
  session.importDraft?.splice(i, 1);
}
function removeTopic(ci: number, ti: number) {
  session.importDraft?.[ci].topics.splice(ti, 1);
}

async function commit() {
  if (!session.importDraft) return;
  const tree = await session.commitImport({
    name: name.value,
    board: board.value,
    class_level: classLevel.value,
    chapters: session.importDraft,
  });
  if (tree) {
    savedTree.value = tree;
    assignClassroomId.value = session.classrooms[0]?.id || null;
  }
}

async function assignSavedSubject() {
  if (!savedTree.value || !assignClassroomId.value) return;
  const classroom = session.classrooms.find((item) => item.id === assignClassroomId.value);
  if (!classroom) return;
  if (await session.updateClassroom(classroom.id, { name: classroom.name, subject_id: savedTree.value.id, teacher_id: classroom.teacher.id })) {
    await session.loadClassrooms();
    await session.loadClassroomOptions();
    await router.push("/app/classrooms");
  }
}

async function refine() {
  if (!session.importDraft?.length || !name.value.trim()) return;
  await session.refineImport({
    name: name.value,
    board: board.value,
    class_level: classLevel.value,
    chapters: session.importDraft,
  });
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Curriculum | import" title="Import from a document" subtitle="Extract headings, optionally clean the outline with Codex, then review before saving." />

    <div
      class="rounded-lg border border-dashed bg-surface p-8 text-center transition"
      :class="dragging ? 'border-primary-600 bg-primary-50' : 'border-hairline'"
      @dragenter.prevent="dragging = true"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <input ref="fileInput" type="file" accept="application/pdf" class="hidden" @change="onFile" />
      <UploadCloud :size="30" class="mx-auto text-primary-600" aria-hidden="true" />
      <p class="mt-3 text-sm font-semibold text-ink-900">Drop a PDF here or choose one from your computer.</p>
      <p class="mt-1 text-sm text-ink-600">Upload a PDF up to 5MB. The file is parsed in memory and never stored.</p>
      <div class="mt-5 flex flex-wrap items-center justify-center gap-3 rounded-md border border-hairline bg-paper px-4 py-3">
        <a class="text-sm font-semibold text-primary-700 underline-offset-4 hover:underline" href="https://ncert.nic.in/textbook.php?ln=en" target="_blank" rel="noopener noreferrer">Open official NCERT textbook portal</a>
        <SButton variant="primary" :disabled="session.loading === 'import'" @click="fileInput?.click()">
          {{ session.loading === "import" ? "Reading..." : "Choose PDF" }}
        </SButton>
      </div>
      <SAIWorkingState
        v-if="session.loading === 'import'"
        class="mx-auto mt-5 max-w-2xl text-left"
        title="Reading the PDF"
        message="Slate is extracting headings and topic structure from the document in memory."
        detail="The uploaded PDF is not stored. After extraction, you can review and clean the outline before saving."
      />
      <p v-if="session.error" class="mt-3 text-sm text-danger">{{ session.error }}</p>
    </div>

    <!-- Review & edit -->
    <div v-if="session.importDraft" class="space-y-5">
      <div class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="s-eyebrow">Review the extracted structure</p>
            <p class="mt-1 text-sm text-ink-500">Use Codex cleanup when extraction includes page numbers, duplicate headings, or noisy topic names.</p>
          </div>
          <SButton variant="secondary" :disabled="!name.trim() || !session.importDraft.length || session.loading === 'refine-import'" @click="refine">
            {{ session.loading === "refine-import" ? "Cleaning..." : "Clean with Codex" }}
          </SButton>
        </div>
        <SAIWorkingState
          v-if="session.loading === 'refine-import'"
          class="mt-4"
          title="Cleaning the imported outline"
          message="Codex is removing noisy page text, duplicate headings, and unclear topic names."
          detail="You still review every chapter and topic before saving; the model is only helping prepare the draft."
        />
        <div class="mt-4 grid gap-4 sm:grid-cols-3">
          <label class="text-sm">Subject name<input v-model="name" class="s-input mt-1" /></label>
          <label class="text-sm">Board<input v-model="board" class="s-input mt-1" /></label>
          <label class="text-sm">Class<input v-model="classLevel" class="s-input mt-1" /></label>
        </div>
      </div>

      <div v-for="(chapter, ci) in session.importDraft" :key="ci" class="rounded-lg border border-hairline bg-surface p-5">
        <div class="flex items-center gap-2">
          <input v-model="chapter.title" class="s-input font-semibold" />
          <SButton variant="ghost" @click="removeChapter(ci)">Remove</SButton>
        </div>
        <ul class="mt-3 grid gap-2 md:grid-cols-2">
          <li v-for="(topic, ti) in chapter.topics" :key="ti" class="flex items-center gap-2">
            <input v-model="chapter.topics[ti]" class="s-input" />
            <button class="s-focus rounded-sm px-2 text-sm font-semibold text-ink-500 hover:text-danger" @click="removeTopic(ci, ti)">Remove</button>
          </li>
          <li v-if="!chapter.topics.length" class="text-sm text-ink-500">No topics under this chapter.</li>
        </ul>
      </div>

      <div class="flex items-center gap-3">
        <SButton variant="primary" :disabled="!name.trim() || !session.importDraft.length || session.loading === 'commit-import'" @click="commit">
          {{ session.loading === "commit-import" ? "Saving..." : "Save curriculum" }}
        </SButton>
        <p class="text-sm text-ink-500">{{ session.importDraft.length }} chapters</p>
      </div>
    </div>

    <section v-if="savedTree" class="rounded-lg border border-hairline bg-surface p-5">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="s-eyebrow">Saved subject</p>
          <h2 class="mt-1 font-display text-xl font-semibold text-ink-900">{{ savedTree.name }}</h2>
          <p class="mt-1 text-sm text-ink-500">Assign this imported subject to an existing classroom or batch now, or manage it later from Classrooms.</p>
        </div>
        <RouterLink to="/app/classrooms" class="text-sm font-semibold text-primary-700 underline-offset-4 hover:underline">Manage classroom assignments</RouterLink>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
        <SCombobox v-model="assignClassroomId" label="Classroom or batch" placeholder="Choose where this subject is taught" :options="classroomOptions" />
        <SButton class="self-end" variant="primary" :disabled="!assignClassroomId || session.loading === `classroom-${assignClassroomId}`" @click="assignSavedSubject">Assign subject</SButton>
      </div>
      <p v-if="!session.classrooms.length" class="mt-3 text-sm text-ink-500">Create a classroom first, then assign this subject.</p>
    </section>
  </div>
</template>
