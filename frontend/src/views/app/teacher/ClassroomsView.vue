<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SConfirmDialog from "../../../components/ui/SConfirmDialog.vue";
import SEmptyState from "../../../components/ui/SEmptyState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const name = ref("");
const subjectId = ref<number | null>(null);
const teacherId = ref<number | null>(null);
const selectedStudents = ref<Record<number, number | null>>({});
const editingId = ref<number | null>(null);
const editName = ref("");
const editSubjectId = ref<number | null>(null);
const editTeacherId = ref<number | null>(null);
const classroomToDelete = ref<{ id: number; name: string } | null>(null);
const options = computed(() => session.classroomOptions);
const subjectOptions = computed(() => (options.value?.subjects || []).map((subject) => ({ label: subject.name, value: subject.id })));
const teacherOptions = computed(() => (options.value?.teachers || []).map((teacher) => ({ label: teacher.name, value: teacher.id })));
const studentOptions = computed(() => (options.value?.students || []).map((student) => ({ label: student.name, value: student.id })));

onMounted(async () => {
  await Promise.all([session.loadClassrooms(), session.loadClassroomOptions()]);
});

async function create() {
  if (!name.value.trim() || !subjectId.value || !teacherId.value) return;
  if (await session.createClassroom({ name: name.value.trim(), subject_id: subjectId.value, teacher_id: teacherId.value })) {
    name.value = "";
    subjectId.value = null;
    teacherId.value = null;
  }
}

function startEdit(classroom: { id: number; name: string; subject: { id: number }; teacher: { id: number } }) {
  editingId.value = classroom.id;
  editName.value = classroom.name;
  editSubjectId.value = classroom.subject.id;
  editTeacherId.value = classroom.teacher.id;
}

async function saveEdit() {
  if (!editingId.value || !editName.value.trim() || !editSubjectId.value || !editTeacherId.value) return;
  if (await session.updateClassroom(editingId.value, { name: editName.value.trim(), subject_id: editSubjectId.value, teacher_id: editTeacherId.value })) editingId.value = null;
}

async function remove(classroomId: number) {
  if (await session.deleteClassroom(classroomId)) classroomToDelete.value = null;
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="School setup" title="Classrooms" subtitle="Assign a curriculum subject and class teacher, then enrol students." />
    <form class="grid gap-4 rounded-lg border border-hairline bg-surface p-5 md:grid-cols-4" @submit.prevent="create">
      <label class="text-sm font-medium text-ink-700">Classroom name<input v-model="name" class="s-input mt-1" placeholder="Class 10 A" required /></label>
      <SCombobox v-model="subjectId" label="Subject" placeholder="Select subject" :options="subjectOptions" />
      <SCombobox v-model="teacherId" label="Class teacher" placeholder="Select teacher" :options="teacherOptions" />
      <div class="flex items-end"><SButton block type="submit" :disabled="!name.trim() || !subjectId || !teacherId || session.loading === 'create-classroom'">Create classroom</SButton></div>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>
    <SEmptyState v-if="!session.classrooms.length && session.loading !== 'classrooms'" title="No classrooms yet" message="Create a classroom to connect teachers, curriculum, and students." />
    <section v-for="classroom in session.classrooms" :key="classroom.id" class="rounded-lg border border-hairline bg-surface p-5">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div><h2 class="font-display text-xl font-semibold text-ink-900">{{ classroom.name }}</h2><p class="mt-1 text-sm text-ink-500">{{ classroom.subject.name }} | {{ classroom.teacher.name }}</p></div>
        <div class="flex items-center gap-3"><span class="text-sm font-medium text-ink-600">{{ classroom.students.length }} enrolled</span><button class="s-focus text-sm font-semibold text-primary-700 hover:underline" @click="startEdit(classroom)">Edit</button><button class="s-focus text-sm font-semibold text-danger hover:underline" @click="classroomToDelete = classroom">Delete</button></div>
      </div>
      <form v-if="editingId === classroom.id" class="mt-5 grid gap-3 rounded-md border border-hairline bg-paper p-4 md:grid-cols-4" @submit.prevent="saveEdit">
        <input v-model="editName" class="s-input" aria-label="Classroom name" required />
        <select v-model="editSubjectId" class="s-input" aria-label="Subject"><option v-for="subject in options?.subjects" :key="subject.id" :value="subject.id">{{ subject.name }}</option></select>
        <select v-model="editTeacherId" class="s-input" aria-label="Class teacher"><option v-for="teacher in options?.teachers" :key="teacher.id" :value="teacher.id">{{ teacher.name }}</option></select>
        <div class="flex gap-2"><SButton type="submit" variant="secondary">Save</SButton><SButton variant="ghost" @click="editingId = null">Cancel</SButton></div>
      </form>
      <div class="mt-5 grid gap-3 md:grid-cols-[1fr_auto]">
        <SCombobox v-model="selectedStudents[classroom.id]" placeholder="Select a student to enrol" :options="studentOptions.map((student) => ({ ...student, disabled: classroom.students.some((enrolled) => enrolled.id === student.value) }))" />
        <SButton variant="secondary" :disabled="!selectedStudents[classroom.id] || session.loading === `enroll-${classroom.id}`" @click="session.enrollClassroomStudent(classroom.id, selectedStudents[classroom.id]!)">Enrol student</SButton>
      </div>
      <ul v-if="classroom.students.length" class="mt-4 divide-y divide-hairline rounded-md border border-hairline">
        <li v-for="student in classroom.students" :key="student.id" class="flex items-center justify-between gap-4 px-4 py-3 text-sm"><span class="font-medium text-ink-800">{{ student.name }}</span><button class="s-focus text-sm font-semibold text-danger hover:underline" @click="session.removeClassroomStudent(classroom.id, student.id)">Remove</button></li>
      </ul>
    </section>
    <SConfirmDialog
      :open="!!classroomToDelete"
      title="Delete classroom"
      :message="`Delete ${classroomToDelete?.name || 'this classroom'}? Its enrolments and chapter unlocks will be removed.`"
      confirm-label="Delete"
      :busy="!!classroomToDelete && session.loading === `classroom-${classroomToDelete.id}`"
      @cancel="classroomToDelete = null"
      @confirm="classroomToDelete && remove(classroomToDelete.id)"
    />
  </div>
</template>
