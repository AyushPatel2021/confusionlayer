<script setup lang="ts">
defineProps<{ message: string; tone?: "error" | "success" }>();
defineEmits<{ close: [] }>();
</script>
<template><div class="fixed bottom-5 right-5 z-[70] flex max-w-sm items-start gap-3 rounded-md border p-4 text-sm shadow-raised" :class="tone === 'success' ? 'border-success/30 bg-surface text-success' : 'border-danger/30 bg-surface text-danger'" role="status"><span class="flex-1">{{ message }}</span><button class="s-focus text-ink-500 hover:text-ink-900" aria-label="Dismiss notification" @click="$emit('close')">Close</button></div></template>
