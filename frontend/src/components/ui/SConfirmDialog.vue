<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import SButton from "./SButton.vue";
const props = withDefaults(defineProps<{ open: boolean; title: string; message: string; confirmLabel?: string; busy?: boolean }>(), { confirmLabel: "Confirm" });
const emit = defineEmits<{ confirm: []; cancel: [] }>();
const cancelButton = ref<{ focus: () => void } | null>(null);
watch(() => props.open, async (open) => { if (open) { await nextTick(); cancelButton.value?.focus(); } });
function keydown(event: KeyboardEvent) { if (event.key === "Escape" && !props.busy) emit("cancel"); }
</script>
<template><div v-if="open" class="fixed inset-0 z-[60] flex items-center justify-center bg-ink-900/45 p-4" role="dialog" aria-modal="true" :aria-label="title" @keydown="keydown"><section class="w-full max-w-md rounded-lg border border-hairline bg-surface p-6 shadow-raised"><h2 class="font-display text-xl font-semibold text-ink-900">{{ title }}</h2><p class="mt-2 text-sm leading-6 text-ink-600">{{ message }}</p><div class="mt-6 flex justify-end gap-2"><SButton ref="cancelButton" variant="ghost" @click="$emit('cancel')">Cancel</SButton><SButton variant="primary" :disabled="busy" @click="$emit('confirm')">{{ confirmLabel }}</SButton></div></section></div></template>
