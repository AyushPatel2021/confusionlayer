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
      { path: "login", name: "login", component: () => import("../views/auth/LoginView.vue"), meta: { title: "Sign in" } },
      { path: "signup", name: "signup", component: () => import("../views/auth/SignupView.vue"), meta: { title: "Get started" } },
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
      // Student
      { path: "learn", name: "learn", component: () => import("../views/app/student/LearnView.vue"), meta: { title: "Learn", roles: ["student"] } },
      { path: "learn/:conceptId", name: "concept", component: () => import("../views/app/student/ConceptView.vue"), meta: { title: "Concept", roles: ["student"] } },
      { path: "explore", name: "explore", component: () => import("../views/app/student/ExploreView.vue"), meta: { title: "Explore", roles: ["student"] } },
      { path: "progress", name: "progress", component: () => import("../views/app/student/ProgressView.vue"), meta: { title: "My progress", roles: ["student"] } },
      // Parent
      { path: "family", name: "family", component: () => import("../views/app/family/FamilyView.vue"), meta: { title: "Family", roles: ["parent"] } },
      // Teacher
      { path: "teacher", name: "teacher-classroom", component: () => import("../views/app/teacher/ClassroomView.vue"), meta: { title: "Classroom", roles: ["teacher", "owner", "school_admin", "admin"] } },
      { path: "curriculum", name: "curriculum", component: () => import("../views/app/teacher/CurriculumView.vue"), meta: { title: "Curriculum", roles: ["teacher", "owner", "school_admin", "admin"] } },
      { path: "curriculum/import", name: "curriculum-import", component: () => import("../views/app/teacher/CurriculumImportView.vue"), meta: { title: "Import curriculum", roles: ["teacher", "owner", "school_admin", "admin"] } },
      { path: "admissions", name: "admissions", component: () => import("../views/app/teacher/AdmissionsView.vue"), meta: { title: "Admissions", roles: ["owner", "school_admin", "admin"], segments: ["school"] } },
      { path: "fees", name: "fees", component: () => import("../views/app/teacher/FeesView.vue"), meta: { title: "Fees", roles: ["owner", "school_admin", "admin"], segments: ["school"] } },
      { path: "hr", name: "hr", component: () => import("../views/app/teacher/HrView.vue"), meta: { title: "HR and payroll", roles: ["owner", "school_admin", "admin"], segments: ["school"] } },
      // Org settings
      { path: "settings/members", name: "settings-members", component: () => import("../views/app/settings/MembersView.vue"), meta: { title: "Members", roles: ["owner"], segments: ["school"] } },
      { path: "settings/billing", name: "settings-billing", component: () => import("../views/app/settings/BillingView.vue"), meta: { title: "Plan and billing", roles: ["owner"] } },
      { path: "teacher/forecast", name: "teacher-forecast", component: () => import("../views/app/teacher/ForecastBriefView.vue"), meta: { title: "Forecast brief", roles: ["teacher", "owner", "school_admin", "admin"] } },
      { path: "teacher/confusion", name: "teacher-confusion", component: () => import("../views/app/teacher/ConfusionBriefView.vue"), meta: { title: "Confusion brief", roles: ["teacher", "owner", "school_admin", "admin"] } },
    ],
  },
  {
    path: "/admin",
    component: () => import("../layouts/AdminLayout.vue"),
    // Role-gating to platform_admin lands with the admin backend (M11); require auth now.
    meta: { requiresAuth: true, roles: ["platform_admin", "admin"], title: "Admin" },
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
  if (to.meta.requiresAuth) await session.restore();
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
