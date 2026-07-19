import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { useSessionStore } from "../stores/session";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: () => import("../layouts/PublicLayout.vue"),
    children: [
      { path: "", name: "landing", component: () => import("../views/marketing/LandingView.vue"), meta: { title: "Home" } },
      { path: "schools", name: "schools", component: () => import("../views/marketing/SchoolsView.vue"), meta: { title: "Schools" } },
      { path: "institutes", name: "institutes", component: () => import("../views/marketing/InstitutesView.vue"), meta: { title: "Institutes" } },
      { path: "students", name: "students", component: () => import("../views/marketing/StudentsView.vue"), meta: { title: "Students" } },
      { path: "pricing", name: "pricing", component: () => import("../views/marketing/PricingView.vue"), meta: { title: "Pricing" } },
      { path: "about", name: "about", component: () => import("../views/marketing/AboutView.vue"), meta: { title: "About" } },
      { path: "login", name: "login", component: () => import("../views/auth/LoginView.vue"), meta: { title: "Sign in", guestOnly: true } },
      { path: "signup", name: "signup", component: () => import("../views/auth/SignupView.vue"), meta: { title: "Get started", guestOnly: true } },
      { path: "forgot-password", name: "forgot-password", component: () => import("../views/auth/ForgotPasswordView.vue"), meta: { title: "Reset password" } },
      { path: "reset-password/:token", name: "reset-password", component: () => import("../views/auth/ResetPasswordView.vue"), meta: { title: "Set password" } },
      { path: "accept-invite/:token", name: "accept-invite", component: () => import("../views/auth/AcceptInviteView.vue"), meta: { title: "Accept invite" } },
    ],
  },
  {
    path: "/app",
    component: () => import("../layouts/AppLayout.vue"),
    meta: { requiresAuth: true, title: "Workspace" },
    children: [
      { path: "", redirect: () => useSessionStore().roleHome },
      { path: "dashboard", name: "dashboard", component: () => import("../views/app/DashboardView.vue"), meta: { title: "Overview", roles: ["owner", "school_admin", "accountant", "hr", "teacher", "student", "parent"] } },
      { path: "account", name: "account", component: () => import("../views/app/AccountView.vue"), meta: { title: "Account", roles: ["owner", "school_admin", "accountant", "hr", "teacher", "student", "parent"] } },
      // Student
      { path: "learn", name: "learn", component: () => import("../views/app/student/LearnView.vue"), meta: { title: "Learn", roles: ["student"] } },
      { path: "learn/:conceptId", name: "concept", component: () => import("../views/app/student/ConceptView.vue"), meta: { title: "Concept", roles: ["student"] } },
      { path: "explore", name: "explore", component: () => import("../views/app/student/ExploreView.vue"), meta: { title: "Explore", roles: ["student"] } },
      { path: "progress", name: "progress", component: () => import("../views/app/student/ProgressView.vue"), meta: { title: "My progress", roles: ["student"] } },
      { path: "map", name: "confusion-map", component: () => import("../views/app/student/ConfusionMapView.vue"), meta: { title: "Confusion map", roles: ["student"] } },
      { path: "exam-outcome", name: "exam-outcome", component: () => import("../views/app/student/ExamOutcomeView.vue"), meta: { title: "Exam outlook", roles: ["student"] } },
      { path: "exam-practice", name: "exam-practice", component: () => import("../views/app/student/ExamPracticeView.vue"), meta: { title: "Exam practice", roles: ["student"] } },
      // Parent
      { path: "family", name: "family", component: () => import("../views/app/family/FamilyView.vue"), meta: { title: "Family", roles: ["parent"] } },
      // Teacher
      { path: "teacher", name: "teacher-classroom", component: () => import("../views/app/teacher/ClassroomView.vue"), meta: { title: "Classroom", roles: ["teacher", "owner", "school_admin"] } },
      { path: "teacher/students", name: "teacher-students", component: () => import("../views/app/teacher/StudentInsightsView.vue"), meta: { title: "Student insights", roles: ["teacher", "owner", "school_admin"] } },
      { path: "students/:studentId", name: "student-report", component: () => import("../views/app/teacher/StudentReportView.vue"), meta: { title: "Student record", roles: ["teacher", "owner", "school_admin", "parent", "student"] } },
      { path: "attendance", name: "attendance", component: () => import("../views/app/teacher/AttendanceView.vue"), meta: { title: "Attendance", roles: ["teacher", "owner", "school_admin"], segments: ["school"] } },
      { path: "operations", name: "operations", component: () => import("../views/app/teacher/OperationsView.vue"), meta: { title: "Timetable", roles: ["owner", "school_admin"], segments: ["school"] } },
      { path: "classrooms", name: "classrooms", component: () => import("../views/app/teacher/ClassroomsView.vue"), meta: { title: "Classrooms", roles: ["owner", "school_admin"] } },
      { path: "curriculum", name: "curriculum", component: () => import("../views/app/teacher/CurriculumView.vue"), meta: { title: "Curriculum", roles: ["teacher", "owner", "school_admin"] } },
      { path: "curriculum/import", name: "curriculum-import", component: () => import("../views/app/teacher/CurriculumImportView.vue"), meta: { title: "Import curriculum", roles: ["teacher", "owner", "school_admin"] } },
      { path: "admissions", name: "admissions", component: () => import("../views/app/teacher/AdmissionsView.vue"), meta: { title: "Admissions", roles: ["owner", "school_admin"], segments: ["school"] } },
      { path: "fees", name: "fees", component: () => import("../views/app/teacher/FeesView.vue"), meta: { title: "Fees", roles: ["owner", "school_admin", "accountant"], segments: ["school"] } },
      { path: "hr", name: "hr", component: () => import("../views/app/teacher/HrView.vue"), meta: { title: "HR and payroll", roles: ["owner", "school_admin", "hr"], segments: ["school"] } },
      // Org settings
      { path: "settings/members", name: "settings-members", component: () => import("../views/app/settings/MembersView.vue"), meta: { title: "Members", roles: ["owner"], segments: ["school", "institute"] } },
      { path: "settings/billing", name: "settings-billing", component: () => import("../views/app/settings/BillingView.vue"), meta: { title: "Plan and billing", roles: ["owner"] } },
      { path: "settings/workspace", name: "settings-workspace", component: () => import("../views/app/settings/WorkspaceSettingsView.vue"), meta: { title: "Workspace settings", roles: ["owner"] } },
      { path: "teacher/forecast", name: "teacher-forecast", component: () => import("../views/app/teacher/ForecastBriefView.vue"), meta: { title: "Forecast brief", roles: ["teacher", "owner", "school_admin"] } },
      { path: "teacher/confusion", name: "teacher-confusion", component: () => import("../views/app/teacher/ConfusionBriefView.vue"), meta: { title: "Confusion brief", roles: ["teacher", "owner", "school_admin"] } },
    ],
  },
  {
    path: "/admin",
    component: () => import("../layouts/AdminLayout.vue"),
    meta: { requiresAuth: true, roles: ["platform_admin"], title: "Admin" },
    children: [{ path: "", name: "admin-home", component: () => import("../views/admin/AdminHomeView.vue"), meta: { title: "Admin" } }],
  },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: "smooth" };
    return { top: 0 };
  },
});

// Guard scaffolding, structured now, enforced from M2. Reads the session store
// so flipping meta.requiresAuth on will start gating without further changes.
router.beforeEach(async (to) => {
  const session = useSessionStore();
  if (!session.authReady) await session.restore();
  if (to.meta.guestOnly && session.isAuthenticated) return session.roleHome;
  if (to.meta.requiresAuth && !session.isAuthenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  const roles = to.meta.roles as string[] | undefined;
  const segments = to.meta.segments as string[] | undefined;
  if (roles && (!session.user || !roles.includes(session.user.role))) return session.roleHome;
  if (segments && (!session.user || !session.user.segment || !segments.includes(session.user.segment))) return session.roleHome;
  return true;
});

router.afterEach((to) => {
  const pageTitle = typeof to.meta.title === "string" ? to.meta.title : "Slate";
  document.title = pageTitle === "Home" ? "Slate" : `${pageTitle} | Slate`;
});
