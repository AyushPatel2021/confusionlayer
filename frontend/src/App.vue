<script setup lang="ts">
import { computed } from "vue";
import { RouterView } from "vue-router";
import SToast from "./components/ui/SToast.vue";
import { useSessionStore } from "./stores/session";
const session = useSessionStore();
const error = computed(() => session.error);
</script>

<template>
  <RouterView />
  <SToast v-if="error" :message="error" @close="session.error = ''" />
</template>
