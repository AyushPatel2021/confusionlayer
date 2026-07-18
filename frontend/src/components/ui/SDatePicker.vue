<script setup lang="ts">
defineProps<{ modelValue: string; label?: string; required?: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="block text-sm">
    <span v-if="label">{{ label }}</span>
    <input
      type="date"
      class="s-input mt-1"
      :value="modelValue"
      :required="required"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
  </label>
</template>
