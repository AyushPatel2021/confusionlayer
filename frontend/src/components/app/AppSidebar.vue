<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import {
  AlertTriangle,
  BookOpen,
  BriefcaseBusiness,
  ChartNoAxesCombined,
  ClipboardCheck,
  Compass,
  CreditCard,
  FolderKanban,
  GraduationCap,
  ReceiptText,
  Users,
  UsersRound,
} from "@lucide/vue";

import { useSessionStore } from "../../stores/session";

const session = useSessionStore();

defineProps<{ compact?: boolean }>();

const links = computed(() => {
  if (session.isStudent) {
    return [
      { label: "Learning", items: [
        { to: "/app/learn", label: "Learn", icon: BookOpen },
        { to: "/app/explore", label: "Explore", icon: Compass },
        { to: "/app/progress", label: "My progress", icon: ChartNoAxesCombined },
      ] },
    ];
  }
  if (session.isParent) {
    return [{ label: "Family", items: [{ to: "/app/family", label: "My family", icon: UsersRound }] }];
  }
  const classroomItems = [
    { to: "/app/teacher", label: "Classroom", icon: GraduationCap },
    { to: "/app/curriculum", label: "Curriculum", icon: FolderKanban },
    { to: "/app/teacher/forecast", label: "Forecast brief", icon: ChartNoAxesCombined },
    { to: "/app/teacher/confusion", label: "Confusion brief", icon: AlertTriangle },
  ];
  const groups = [{ label: "Teaching", items: classroomItems }];
  if (session.isOrgAdmin && session.user?.segment === "school") {
    groups.push({ label: "School office", items: [
      { to: "/app/admissions", label: "Admissions", icon: ClipboardCheck },
      { to: "/app/fees", label: "Fees", icon: ReceiptText },
      { to: "/app/hr", label: "HR & payroll", icon: BriefcaseBusiness },
    ] });
  }
  if (session.user?.role === "owner" && session.user.segment === "school") {
    groups.push({ label: "Workspace", items: [
      { to: "/app/settings/members", label: "Members", icon: Users },
      { to: "/app/settings/billing", label: "Plan & billing", icon: CreditCard },
    ] });
  } else if (session.user?.role === "owner") {
    groups.push({ label: "Workspace", items: [{ to: "/app/settings/billing", label: "Plan & billing", icon: CreditCard }] });
  }
  return groups;
});
</script>

<template>
  <nav class="space-y-5">
    <section v-for="group in links" :key="group.label">
      <p v-if="!compact" class="mb-1 px-3 text-xs font-semibold uppercase tracking-wide text-ink-500">{{ group.label }}</p>
      <div class="space-y-1">
        <RouterLink
          v-for="link in group.items"
          :key="link.to"
          :to="link.to"
          class="s-focus flex items-center rounded-md px-3 py-2.5 text-sm font-medium text-ink-700 transition-colors hover:bg-primary-50 hover:text-primary-700"
          :class="compact ? 'justify-center' : 'gap-3'"
          active-class="bg-primary-50 text-primary-700"
          :title="compact ? link.label : undefined"
        >
          <component :is="link.icon" :size="19" stroke-width="1.8" aria-hidden="true" />
          <span v-if="!compact" class="truncate">{{ link.label }}</span>
        </RouterLink>
      </div>
    </section>
  </nav>
</template>
