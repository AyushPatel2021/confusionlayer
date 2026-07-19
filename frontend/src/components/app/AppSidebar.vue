<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import {
  AlertTriangle,
  BookOpen,
  BriefcaseBusiness,
  CalendarClock,
  CalendarCheck,
  ChartNoAxesCombined,
  ClipboardCheck,
  Compass,
  CreditCard,
  FolderKanban,
  GraduationCap,
  ReceiptText,
  Settings,
  School,
  CalendarDays,
  TrendingUp,
  UserRoundCog,
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
        { to: "/app/dashboard", label: "Overview", icon: ChartNoAxesCombined },
        { to: "/app/learn", label: "Learn", icon: BookOpen },
        ...(session.isIndividualLearner ? [{ to: "/app/curriculum", label: "Curriculum", icon: FolderKanban }] : []),
        { to: "/app/explore", label: "Explore", icon: Compass },
        { to: "/app/progress", label: "My progress", icon: TrendingUp },
        { to: "/app/map", label: "Confusion map", icon: AlertTriangle },
        { to: "/app/exam-outcome", label: "Exam outlook", icon: ClipboardCheck },
        { to: "/app/exam-practice", label: "Exam practice", icon: ClipboardCheck },
      ] },
    ];
  }
  if (session.isParent) {
    return [{ label: "Family", items: [{ to: "/app/dashboard", label: "Overview", icon: ChartNoAxesCombined }, { to: "/app/family", label: "My family", icon: UsersRound }] }];
  }
  if (session.user?.role === "accountant") {
    return [
      { label: "Accounts", items: [
        { to: "/app/dashboard", label: "Overview", icon: ChartNoAxesCombined },
        { to: "/app/fees", label: "Fees", icon: ReceiptText },
      ] },
      { label: "Workspace", items: [{ to: "/app/account", label: "Account", icon: UserRoundCog }] },
    ];
  }
  if (session.user?.role === "hr") {
    return [
      { label: "HR", items: [
        { to: "/app/dashboard", label: "Overview", icon: ChartNoAxesCombined },
        { to: "/app/hr", label: "HR & payroll", icon: BriefcaseBusiness },
      ] },
      { label: "Workspace", items: [{ to: "/app/account", label: "Account", icon: UserRoundCog }] },
    ];
  }
  const canUseTeacherWorkspace = session.user?.role === "teacher" || session.user?.role === "school_admin";
  const classroomItems = [
    { to: "/app/dashboard", label: "Overview", icon: ChartNoAxesCombined },
    { to: "/app/curriculum", label: "Curriculum", icon: FolderKanban },
  ];
  if (canUseTeacherWorkspace) {
    classroomItems.splice(
      1,
      0,
      { to: "/app/teacher", label: "Classroom", icon: GraduationCap },
      { to: "/app/teacher/students", label: "Student insights", icon: UsersRound },
      { to: "/app/teacher/forecast", label: "Forecast brief", icon: CalendarClock },
      { to: "/app/teacher/confusion", label: "Confusion brief", icon: AlertTriangle },
    );
  }
  if (session.user?.role !== "owner" && session.user?.segment === "school") {
    classroomItems.splice(canUseTeacherWorkspace ? 3 : 1, 0, { to: "/app/attendance", label: "Attendance", icon: CalendarCheck });
  }
  const groups = [{ label: "Teaching", items: classroomItems }];
  if (session.isOrgAdmin && session.user?.segment === "school") {
    classroomItems.splice(1, 0, { to: "/app/classrooms", label: "Classrooms", icon: School });
    groups.push({ label: "School office", items: [
      { to: "/app/admissions", label: "Admissions", icon: ClipboardCheck },
      { to: "/app/fees", label: "Fees", icon: ReceiptText },
      { to: "/app/hr", label: "HR & payroll", icon: BriefcaseBusiness },
      { to: "/app/operations", label: "Timetable", icon: CalendarDays },
    ] });
  }
  if (session.user?.role === "owner" && ["school", "institute"].includes(session.user.segment || "")) {
    groups.push({ label: "Workspace", items: [
      { to: "/app/settings/members", label: "Members", icon: Users },
      { to: "/app/settings/billing", label: "Plan & billing", icon: CreditCard },
      { to: "/app/settings/workspace", label: "Workspace settings", icon: Settings },
      { to: "/app/account", label: "Account", icon: UserRoundCog },
    ] });
  } else if (session.user?.role === "owner") {
    groups.push({ label: "Workspace", items: [{ to: "/app/settings/billing", label: "Plan & billing", icon: CreditCard }, { to: "/app/settings/workspace", label: "Workspace settings", icon: Settings }, { to: "/app/account", label: "Account", icon: UserRoundCog }] });
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
