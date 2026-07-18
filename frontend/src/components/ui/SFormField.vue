<script setup lang="ts">
defineProps<{ label: string; error?: string; help?: string; required?: boolean }>();
</script>
<template><label class="block text-sm font-medium text-ink-700"><span>{{ label }}<span v-if="required" class="text-danger"> *</span></span><slot /><span v-if="help && !error" class="mt-1 block text-xs text-ink-500">{{ help }}</span><span v-if="error" class="mt-1 block text-xs text-danger">{{ error }}</span></label></template>
