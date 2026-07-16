import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { useSessionStore } from "../stores/session";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: () => import("../layouts/PublicLayout.vue"),
    children: [
      { path: "", name: "landing", component: () => import("../views/marketing/LandingView.vue") },
      { path: "login", name: "login", component: () => import("../views/auth/LoginView.vue") },
    ],
  },
  {
    path: "/app",
    component: () => import("../layouts/AppLayout.vue"),
    // meta.requiresAuth is intentionally off in M0 so the demo stays reachable;
    // it is enforced once real auth lands (M2).
    meta: { requiresAuth: false },
    children: [{ path: "", name: "app-console", component: () => import("../views/app/ConsoleView.vue") }],
  },
  {
    path: "/admin",
    component: () => import("../layouts/AdminLayout.vue"),
    meta: { requiresAuth: false, roles: ["platform_admin", "admin"] },
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
