<script setup lang="ts">
import { computed, ref } from "vue";

type Option = { label: string; value: string | number | null; hint?: string; disabled?: boolean };

const props = defineProps<{
  modelValue: string | number | null;
  options: Option[];
  placeholder?: string;
  label?: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: string | number | null]; change: [] }>();
const query = ref("");

const filtered = computed(() => {
  const term = query.value.trim().toLowerCase();
  if (!term) return props.options;
  return props.options.filter((option) => `${option.label} ${option.hint || ""}`.toLowerCase().includes(term));
});

function select(raw: string) {
  const option = props.options.find((item) => String(item.value ?? "") === raw);
  emit("update:modelValue", option ? option.value : null);
  emit("change");
}
</script>

<template>
  <label class="block text-sm">
    <span v-if="label">{{ label }}</span>
    <input v-model="query" class="s-input mt-1" :placeholder="placeholder || 'Search'" />
    <select
      class="s-input mt-2"
      :value="modelValue ?? ''"
      @change="select(($event.target as HTMLSelectElement).value)"
    >
      <option value="">{{ placeholder || "Choose" }}</option>
      <option v-for="option in filtered" :key="`${option.value}`" :value="option.value ?? ''" :disabled="option.disabled">
        {{ option.label }}{{ option.hint ? ` - ${option.hint}` : "" }}
      </option>
    </select>
  </label>
</template>
