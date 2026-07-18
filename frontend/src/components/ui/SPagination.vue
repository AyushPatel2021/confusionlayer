<script setup lang="ts">
import SButton from "./SButton.vue";
const props = defineProps<{ modelValue: number; total: number; pageSize?: number }>();
const emit = defineEmits<{ 'update:modelValue': [value: number] }>();
const pages = () => Math.max(1, Math.ceil(props.total / (props.pageSize || 20)));
</script>
<template><div class="flex items-center justify-between gap-3 text-sm text-ink-500"><span>Page {{ modelValue }} of {{ pages() }}</span><div class="flex gap-2"><SButton variant="ghost" :disabled="modelValue <= 1" @click="emit('update:modelValue', modelValue - 1)">Previous</SButton><SButton variant="ghost" :disabled="modelValue >= pages()" @click="emit('update:modelValue', modelValue + 1)">Next</SButton></div></div></template>
