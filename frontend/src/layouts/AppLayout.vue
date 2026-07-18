<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";

import AppSidebar from "../components/app/AppSidebar.vue";
import SButton from "../components/ui/SButton.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const sidebarCollapsed = ref(false);
const mobileNavOpen = ref(false);
const profileOpen = ref(false);

const initials = computed(() => {
  const n = session.user?.name || session.user?.email || "?";
  return n.slice(0, 1).toUpperCase();
});
const displayName = computed(() => session.user?.name || session.user?.email || "User");
const displayRole = computed(() => (session.user?.role || "member").replace("_", " "));
const pageTitle = computed(() => (typeof route.meta.title === "string" ? route.meta.title : "Workspace"));
const breadcrumbs = computed(() => {
  const items = [{ label: "Workspace", to: session.roleHome || "/app" }];
  if (pageTitle.value !== "Workspace") items.push({ label: pageTitle.value, to: route.fullPath });
  return items;
});

onMounted(() => {
  void session.restore();
});

watch(
  () => route.fullPath,
  () => {
    mobileNavOpen.value = false;
    profileOpen.value = false;
  },
);

async function signOut() {
  session.logout();
  router.push("/");
}
</script>

<template>
  <div class="min-h-screen bg-paper text-ink-900">
    <aside
      class="fixed inset-y-0 left-0 z-40 hidden flex-col border-r border-hairline bg-surface transition-[width] duration-200 md:flex"
      :class="sidebarCollapsed ? 'w-24' : 'w-72'"
    >
      <div class="flex h-16 items-center justify-between border-b border-hairline px-4">
        <RouterLink to="/" class="font-display text-xl font-semibold text-ink-900">{{ sidebarCollapsed ? "S" : "Slate" }}</RouterLink>
        <button class="s-focus rounded-md border border-hairline px-2 py-1 text-xs font-semibold text-ink-600 hover:border-primary-500 hover:text-primary-600" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? "Open" : "Close" }}
        </button>
      </div>
      <div v-if="!sidebarCollapsed" class="border-b border-hairline px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Workspace</p>
        <p class="mt-1 truncate text-sm font-medium text-ink-900">{{ session.user?.org_name || "Workspace" }}</p>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto px-3 py-4">
        <AppSidebar :compact="sidebarCollapsed" />
      </div>
      <div class="border-t border-hairline px-4 py-4">
        <RouterLink to="/" class="text-xs font-medium text-ink-500 hover:text-primary-600">{{ sidebarCollapsed ? "Site" : "Back to site" }}</RouterLink>
      </div>
    </aside>

    <div
      v-if="mobileNavOpen"
      class="fixed inset-0 z-50 bg-ink-900/40 md:hidden"
      role="presentation"
      @click="mobileNavOpen = false"
    />
    <aside
      class="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col border-r border-hairline bg-surface transition-transform duration-200 md:hidden"
      :class="mobileNavOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="flex h-16 items-center justify-between border-b border-hairline px-4">
        <RouterLink to="/" class="font-display text-xl font-semibold text-ink-900">Slate</RouterLink>
        <button class="s-focus rounded-md border border-hairline px-3 py-1.5 text-sm font-semibold text-ink-700" @click="mobileNavOpen = false">Close</button>
      </div>
      <div class="border-b border-hairline px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Workspace</p>
        <p class="mt-1 truncate text-sm font-medium text-ink-900">{{ session.user?.org_name || "Workspace" }}</p>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto px-3 py-4">
        <AppSidebar />
      </div>
    </aside>

    <div class="min-h-screen transition-[padding] duration-200" :class="sidebarCollapsed ? 'md:pl-24' : 'md:pl-72'">
      <header class="sticky top-0 z-30 border-b border-hairline bg-surface/95 backdrop-blur">
        <div class="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div class="flex min-w-0 items-center gap-3">
            <button class="s-focus rounded-md border border-hairline px-3 py-1.5 text-sm font-semibold text-ink-700 md:hidden" @click="mobileNavOpen = true">Menu</button>
            <div class="min-w-0">
              <nav class="flex items-center gap-2 text-xs font-medium text-ink-500" aria-label="Breadcrumb">
                <RouterLink
                  v-for="(item, i) in breadcrumbs"
                  :key="`${item.label}-${i}`"
                  :to="item.to"
                  class="truncate hover:text-primary-600"
                >
                  {{ item.label }}
                  <span v-if="i < breadcrumbs.length - 1" class="ml-2 text-ink-300">/</span>
                </RouterLink>
              </nav>
              <h1 class="mt-0.5 truncate font-display text-xl font-semibold text-ink-900">{{ pageTitle }}</h1>
            </div>
          </div>

          <div class="relative shrink-0">
            <button class="s-focus flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-primary-50" @click="profileOpen = !profileOpen">
              <span class="hidden text-right sm:block">
                <span class="block max-w-44 truncate text-sm font-medium text-ink-900">{{ displayName }}</span>
                <span class="block text-xs capitalize text-ink-500">{{ displayRole }}</span>
              </span>
              <span class="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-sm font-semibold text-white">{{ initials }}</span>
            </button>
            <div
              v-if="profileOpen"
              class="absolute right-0 mt-2 w-64 rounded-lg border border-hairline bg-surface p-2 shadow-raised"
            >
              <div class="border-b border-hairline px-3 py-3">
                <p class="truncate text-sm font-semibold text-ink-900">{{ displayName }}</p>
                <p class="truncate text-xs text-ink-500">{{ session.user?.email }}</p>
                <p class="mt-1 text-xs capitalize text-ink-500">{{ displayRole }}</p>
              </div>
              <RouterLink to="/app/settings/members" class="mt-2 block rounded-md px-3 py-2 text-sm font-medium text-ink-700 hover:bg-primary-50 hover:text-primary-600">Settings</RouterLink>
              <SButton class="mt-1" variant="ghost" block @click="signOut">Sign out</SButton>
            </div>
          </div>
        </div>
      </header>

      <main class="min-w-0 px-4 py-6 sm:px-6 lg:px-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>
