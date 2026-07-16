import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { useSessionStore } from "../stores/session";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: () => import("../layouts/PublicLayout.vue"),
    children: [
      { path: "", name: "landing", component: () => import("../views/marketing/LandingView.vue") },
      { path: "schools", name: "schools", component: () => import("../views/marketing/SchoolsView.vue") },
      { path: "institutes", name: "institutes", component: () => import("../views/marketing/InstitutesView.vue") },
      { path: "students", name: "students", component: () => import("../views/marketing/StudentsView.vue") },
      { path: "pricing", name: "pricing", component: () => import("../views/marketing/PricingView.vue") },
      { path: "about", name: "about", component: () => import("../views/marketing/AboutView.vue") },
      { path: "login", name: "login", component: () => import("../views/auth/LoginView.vue") },
      { path: "signup", name: "signup", component: () => import("../views/auth/SignupView.vue") },
      { path: "forgot-password", name: "forgot-password", component: () => import("../views/auth/ForgotPasswordView.vue") },
      { path: "reset-password/:token", name: "reset-password", component: () => import("../views/auth/ResetPasswordView.vue") },
      { path: "accept-invite/:token", name: "accept-invite", component: () => import("../views/auth/AcceptInviteView.vue") },
    ],
  },
  {
    path: "/app",
    component: () => import("../layouts/AppLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      { path: "", redirect: () => useSessionStore().roleHome },
      // Student
      { path: "learn", name: "learn", component: () => import("../views/app/student/LearnView.vue") },
      { path: "learn/:conceptId", name: "concept", component: () => import("../views/app/student/ConceptView.vue") },
      { path: "explore", name: "explore", component: () => import("../views/app/student/ExploreView.vue") },
      { path: "progress", name: "progress", component: () => import("../views/app/student/ProgressView.vue") },
      // Teacher
      { path: "teacher", name: "teacher-classroom", component: () => import("../views/app/teacher/ClassroomView.vue") },
      { path: "curriculum", name: "curriculum", component: () => import("../views/app/teacher/CurriculumView.vue") },
      { path: "curriculum/import", name: "curriculum-import", component: () => import("../views/app/teacher/CurriculumImportView.vue") },
      { path: "admissions", name: "admissions", component: () => import("../views/app/teacher/AdmissionsView.vue") },
      // Org settings
      { path: "settings/members", name: "settings-members", component: () => import("../views/app/settings/MembersView.vue") },
      { path: "settings/billing", name: "settings-billing", component: () => import("../views/app/settings/BillingView.vue") },
      { path: "teacher/forecast", name: "teacher-forecast", component: () => import("../views/app/teacher/ForecastBriefView.vue") },
      { path: "teacher/confusion", name: "teacher-confusion", component: () => import("../views/app/teacher/ConfusionBriefView.vue") },
    ],
  },
  {
    path: "/admin",
    component: () => import("../layouts/AdminLayout.vue"),
    // Role-gating to platform_admin lands with the admin backend (M11); require auth now.
    meta: { requiresAuth: true, roles: ["platform_admin", "admin"] },
    children: [{ path: "", name: "admin-home", component: () => import("../views/admin/AdminHomeView.vue") }],
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

// Guard scaffolding — structured now, enforced from M2. Reads the session store
// so flipping meta.requiresAuth on will start gating without further changes.
router.beforeEach((to) => {
  const session = useSessionStore();
  if (to.meta.requiresAuth && !session.token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  return true;
});
