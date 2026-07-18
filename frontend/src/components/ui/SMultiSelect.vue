<script setup lang="ts">
type Option = { label: string; value: number | string; hint?: string; disabled?: boolean };

const props = withDefaults(
  defineProps<{
    modelValue: Array<number | string>;
    options: Option[];
    label?: string;
    maxHeight?: string;
  }>(),
  { label: "", maxHeight: "max-h-36" },
);

const emit = defineEmits<{ "update:modelValue": [value: Array<number | string>] }>();

function toggle(value: number | string, checked: boolean) {
  const next = checked ? [...props.modelValue, value] : props.modelValue.filter((item) => item !== value);
  emit("update:modelValue", next);
}
</script>

<template>
  <fieldset class="text-sm">
    <legend v-if="label">{{ label }}</legend>
    <div class="mt-1 grid gap-2 overflow-auto rounded-md border border-hairline p-2" :class="maxHeight">
      <label v-for="option in options" :key="`${option.value}`" class="flex items-start gap-2">
        <input
          class="mt-1"
          type="checkbox"
          :checked="modelValue.includes(option.value)"
          :disabled="option.disabled"
          @change="toggle(option.value, ($event.target as HTMLInputElement).checked)"
        />
        <span>
          <span class="block text-ink-800">{{ option.label }}</span>
          <span v-if="option.hint" class="block text-xs text-ink-500">{{ option.hint }}</span>
        </span>
      </label>
    </div>
  </fieldset>
</template>
