<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ChevronDown } from "@lucide/vue";

type Option = { label: string; value: string | number | null; hint?: string; disabled?: boolean };

const props = defineProps<{
  modelValue: string | number | null;
  options: Option[];
  placeholder?: string;
  label?: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: string | number | null]; change: [] }>();
const root = ref<HTMLElement | null>(null);
const searchInput = ref<HTMLInputElement | null>(null);
const query = ref("");
const open = ref(false);

const selected = computed(() => props.options.find((item) => item.value === props.modelValue) || null);

const filtered = computed(() => {
  const term = query.value.trim().toLowerCase();
  if (!term) return props.options;
  return props.options.filter((option) => `${option.label} ${option.hint || ""}`.toLowerCase().includes(term));
});

function toggleOptions() {
  if (open.value) {
    open.value = false;
    return;
  }
  showOptions();
}

function showOptions() {
  open.value = true;
  query.value = "";
  void nextTick(() => searchInput.value?.focus());
}

function choose(option: Option | null) {
  if (option?.disabled) return;
  emit("update:modelValue", option ? option.value : null);
  emit("change");
  open.value = false;
}

function onDocumentPointerDown(event: PointerEvent) {
  if (root.value && !root.value.contains(event.target as Node)) open.value = false;
}

onMounted(() => document.addEventListener("pointerdown", onDocumentPointerDown));
onBeforeUnmount(() => document.removeEventListener("pointerdown", onDocumentPointerDown));
</script>

<template>
  <div ref="root" class="relative block text-sm">
    <label v-if="label" class="mb-1 block">{{ label }}</label>
    <button
      type="button"
      class="s-input flex w-full items-center justify-between gap-3 text-left"
      :aria-expanded="open"
      @click="toggleOptions"
      @keydown.arrow-down.prevent="showOptions"
    >
      <span :class="selected ? 'text-ink-900' : 'text-ink-400'">{{ selected?.label || placeholder || "Choose" }}</span>
      <ChevronDown :size="17" class="text-ink-400" aria-hidden="true" />
    </button>
    <div v-if="open" class="absolute z-30 mt-2 w-full rounded-lg border border-hairline bg-surface p-2 shadow-lg">
      <input
        ref="searchInput"
        v-model="query"
        class="s-input"
        :placeholder="placeholder || 'Search'"
        @keydown.escape.prevent="open = false"
      />
      <div class="mt-2 max-h-56 overflow-auto">
        <button
          v-if="modelValue !== null"
          type="button"
          class="block w-full rounded-md px-3 py-2 text-left text-sm text-ink-500 hover:bg-primary-50"
          @click="choose(null)"
        >
          Clear selection
        </button>
        <button
          v-for="option in filtered"
          :key="`${option.value}`"
          type="button"
          class="block w-full rounded-md px-3 py-2 text-left hover:bg-primary-50 disabled:cursor-not-allowed disabled:opacity-45"
          :class="option.value === modelValue ? 'bg-primary-50 text-primary-600' : 'text-ink-800'"
          :disabled="option.disabled"
          @click="choose(option)"
        >
          <span class="block text-sm font-medium">{{ option.label }}</span>
          <span v-if="option.hint" class="block text-xs text-ink-500">{{ option.hint }}</span>
        </button>
        <p v-if="!filtered.length" class="px-3 py-4 text-sm text-ink-500">No matching option</p>
      </div>
    </div>
  </div>
</template>
