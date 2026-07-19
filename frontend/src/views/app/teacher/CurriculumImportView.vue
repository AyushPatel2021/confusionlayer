<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import SButton from "../../../components/ui/SButton.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const router = useRouter();

const name = ref("");
const board = ref("CBSE");
const classLevel = ref("10");
const fileInput = ref<HTMLInputElement | null>(null);

async function onFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) {
    if (!name.value) name.value = file.name.replace(/\.pdf$/i, "");
    await session.importPdf(file);
  }
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
  if (tree) router.push("/app/curriculum");
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

    <div class="rounded-lg border border-dashed border-hairline bg-surface p-8 text-center">
      <input ref="fileInput" type="file" accept="application/pdf" class="hidden" @change="onFile" />
      <p class="text-sm text-ink-600">Upload a PDF up to 5MB (syllabus, contents page, chapter list). The file is parsed in memory and never stored.</p>
      <a class="mt-2 inline-block text-sm font-semibold text-primary-700 hover:underline" href="https://ncert.nic.in/textbook.php?ln=en" target="_blank" rel="noopener noreferrer">Get an official NCERT syllabus or textbook PDF</a>
      <SButton class="mt-4" variant="primary" :disabled="session.loading === 'import'" @click="fileInput?.click()">
        {{ session.loading === "import" ? "Reading..." : "Choose PDF" }}
      </SButton>
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
  </div>
</template>
