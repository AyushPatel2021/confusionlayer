<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";

import { useSessionStore } from "../../stores/session";

const session = useSessionStore();

const links = computed(() => {
  if (session.isStudent) {
    return [
      { to: "/app/learn", label: "Learn" },
      { to: "/app/explore", label: "Explore" },
      { to: "/app/progress", label: "My progress" },
    ];
  }
  return [
    { to: "/app/teacher", label: "Classroom" },
    { to: "/app/teacher/forecast", label: "Forecast brief" },
    { to: "/app/teacher/confusion", label: "Confusion brief" },
  ];
});
</script>

<template>
  <nav class="flex flex-col gap-1">
    <RouterLink
      v-for="link in links"
      :key="link.to"
      :to="link.to"
      class="s-focus rounded-md px-3 py-2 text-sm font-medium text-ink-700 transition-colors hover:bg-primary-50 hover:text-primary-600"
      active-class="bg-primary-50 text-primary-600"
    >
      {{ link.label }}
    </RouterLink>
  </nav>
</template>
