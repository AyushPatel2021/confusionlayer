<script setup lang="ts">
defineProps<{ modelValue: string; tabs: Array<{ value: string; label: string }> }>();
defineEmits<{ 'update:modelValue': [value: string] }>();
</script>
<template><div class="flex gap-1 border-b border-hairline" role="tablist"><button v-for="tab in tabs" :key="tab.value" class="s-focus border-b-2 px-3 py-2 text-sm font-semibold" :class="modelValue === tab.value ? 'border-primary-600 text-primary-700' : 'border-transparent text-ink-500 hover:text-ink-900'" role="tab" :aria-selected="modelValue === tab.value" @click="$emit('update:modelValue', tab.value)">{{ tab.label }}</button></div></template>
