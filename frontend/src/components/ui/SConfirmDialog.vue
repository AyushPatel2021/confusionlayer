<script setup lang="ts">
import SButton from "./SButton.vue";
withDefaults(defineProps<{ open: boolean; title: string; message: string; confirmLabel?: string; busy?: boolean }>(), { confirmLabel: "Confirm" });
defineEmits<{ confirm: []; cancel: [] }>();
</script>
<template><div v-if="open" class="fixed inset-0 z-[60] flex items-center justify-center bg-ink-900/45 p-4" role="dialog" aria-modal="true"><section class="w-full max-w-md rounded-lg border border-hairline bg-surface p-6 shadow-raised"><h2 class="font-display text-xl font-semibold text-ink-900">{{ title }}</h2><p class="mt-2 text-sm leading-6 text-ink-600">{{ message }}</p><div class="mt-6 flex justify-end gap-2"><SButton variant="ghost" @click="$emit('cancel')">Cancel</SButton><SButton variant="primary" :disabled="busy" @click="$emit('confirm')">{{ confirmLabel }}</SButton></div></section></div></template>
