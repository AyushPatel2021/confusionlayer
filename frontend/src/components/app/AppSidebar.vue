<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";

import { useSessionStore } from "../../stores/session";

const session = useSessionStore();

defineProps<{ compact?: boolean }>();

const links = computed(() => {
  if (session.isStudent) {
    return [
      { to: "/app/learn", label: "Learn" },
      { to: "/app/explore", label: "Explore" },
      { to: "/app/progress", label: "My progress" },
    ];
  }
  if (session.isParent) {
    return [{ to: "/app/family", label: "My family" }];
  }
  const items = [
    { to: "/app/teacher", label: "Classroom" },
    { to: "/app/curriculum", label: "Curriculum" },
    { to: "/app/teacher/forecast", label: "Forecast brief" },
    { to: "/app/teacher/confusion", label: "Confusion brief" },
  ];
  if (session.isOrgAdmin && session.user?.segment === "school") {
    items.push(
      { to: "/app/admissions", label: "Admissions" },
      { to: "/app/fees", label: "Fees" },
      { to: "/app/hr", label: "HR & payroll" },
    );
  }
  if (session.isOrgAdmin) {
    items.push({ to: "/app/settings/members", label: "Members" }, { to: "/app/settings/billing", label: "Plan & billing" });
  }
  return items;
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
      :title="compact ? link.label : undefined"
    >
      <span v-if="compact" class="block text-center font-mono text-xs">{{ link.label.slice(0, 2).toUpperCase() }}</span>
      <span v-else>{{ link.label }}</span>
    </RouterLink>
  </nav>
</template>
