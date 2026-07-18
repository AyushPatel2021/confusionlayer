<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ChevronDown, ChevronRight, LogOut, Menu, PanelLeftClose, PanelLeftOpen, Settings, X } from "@lucide/vue";
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

const initials = computed(() => (session.user?.name || "User").split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase());
const displayName = computed(() => session.user?.name || "User");
const displayRole = computed(() => (session.user?.role || "member").replace(/_/g, " "));
const pageTitle = computed(() => (typeof route.meta.title === "string" ? route.meta.title : "Workspace"));
const workspaceName = computed(() => session.user?.org_name || (session.isStudent ? "Learning" : session.isParent ? "Family" : "Workspace"));
const settingsPath = computed(() => session.user?.role === "owner" && session.user.segment === "school" ? "/app/settings/members" : "/app/settings/billing");
const canOpenSettings = computed(() => session.user?.role === "owner");
const breadcrumbItems = computed(() => {
  const parts = route.path.replace(/^\/app\/?/, "").split("/").filter(Boolean);
  const labels: Record<string, string> = {
    teacher: "Teaching",
    settings: "Settings",
    learn: "Learning",
    curriculum: "Curriculum",
  };
  const items = [{ label: "Workspace", to: "/app/dashboard" }];
  let path = "/app";
  for (const [index, part] of parts.entries()) {
    path += `/${part}`;
    const label = index === parts.length - 1 ? pageTitle.value : labels[part] || part.replace(/-/g, " ");
    if (items[items.length - 1]?.label !== label) items.push({ label, to: path });
  }
  return items;
});

onMounted(() => void session.restore());

watch(
  () => route.fullPath,
  () => {
    mobileNavOpen.value = false;
    profileOpen.value = false;
  },
);

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value;
}

function closeProfile(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (!target.closest("[data-profile-menu]")) profileOpen.value = false;
}

async function signOut() {
  await session.logout();
  await router.push("/");
}
</script>

<template>
  <div class="min-h-screen bg-paper text-ink-900" @click="closeProfile">
    <aside
      class="fixed inset-y-0 left-0 z-40 hidden flex-col border-r border-hairline bg-surface transition-[width] duration-200 md:flex"
      :class="sidebarCollapsed ? 'w-20' : 'w-72'"
    >
      <div class="flex h-16 items-center border-b border-hairline px-4" :class="sidebarCollapsed ? 'justify-center' : 'justify-between'">
        <RouterLink to="/app" class="font-display text-xl font-semibold text-ink-900" :title="sidebarCollapsed ? 'Slate workspace' : undefined">
          {{ sidebarCollapsed ? "S" : "Slate" }}
        </RouterLink>
        <button
          v-if="!sidebarCollapsed"
          class="s-focus flex h-9 w-9 items-center justify-center rounded-md text-ink-500 hover:bg-primary-50 hover:text-primary-700"
          title="Collapse sidebar"
          aria-label="Collapse sidebar"
          @click.stop="toggleSidebar"
        ><PanelLeftClose :size="19" /></button>
      </div>
      <div v-if="!sidebarCollapsed" class="border-b border-hairline px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Workspace</p>
        <p class="mt-1 truncate text-sm font-semibold text-ink-900">{{ workspaceName }}</p>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto px-3 py-5">
        <AppSidebar :compact="sidebarCollapsed" />
      </div>
      <div v-if="sidebarCollapsed" class="border-t border-hairline p-3">
        <button class="s-focus flex h-10 w-full items-center justify-center rounded-md text-ink-500 hover:bg-primary-50 hover:text-primary-700" title="Expand sidebar" aria-label="Expand sidebar" @click.stop="toggleSidebar">
          <PanelLeftOpen :size="19" />
        </button>
      </div>
    </aside>

    <div v-if="mobileNavOpen" class="fixed inset-0 z-50 bg-ink-900/40 md:hidden" role="presentation" @click="mobileNavOpen = false" />
    <aside class="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col border-r border-hairline bg-surface transition-transform duration-200 md:hidden" :class="mobileNavOpen ? 'translate-x-0' : '-translate-x-full'">
      <div class="flex h-16 items-center justify-between border-b border-hairline px-4">
        <RouterLink to="/app" class="font-display text-xl font-semibold text-ink-900">Slate</RouterLink>
        <button class="s-focus flex h-9 w-9 items-center justify-center rounded-md text-ink-600 hover:bg-primary-50" title="Close menu" aria-label="Close menu" @click="mobileNavOpen = false"><X :size="20" /></button>
      </div>
      <div class="border-b border-hairline px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">Workspace</p>
        <p class="mt-1 truncate text-sm font-semibold text-ink-900">{{ workspaceName }}</p>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto px-3 py-5"><AppSidebar /></div>
    </aside>

    <div class="min-h-screen transition-[padding] duration-200" :class="sidebarCollapsed ? 'md:pl-20' : 'md:pl-72'">
      <header class="sticky top-0 z-30 border-b border-hairline bg-surface/95 backdrop-blur">
        <div class="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div class="flex min-w-0 items-center gap-3">
            <button class="s-focus flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-ink-600 hover:bg-primary-50 md:hidden" title="Open menu" aria-label="Open menu" @click.stop="mobileNavOpen = true"><Menu :size="20" /></button>
            <div class="min-w-0">
              <div class="flex min-w-0 items-center gap-1.5 text-xs font-medium text-ink-500" aria-label="Breadcrumb">
                <template v-for="(item, index) in breadcrumbItems" :key="item.to">
                  <ChevronRight v-if="index" :size="14" class="shrink-0 text-ink-400" aria-hidden="true" />
                  <RouterLink v-if="index < breadcrumbItems.length - 1" :to="item.to" class="max-w-28 truncate hover:text-primary-700">{{ item.label }}</RouterLink>
                  <span v-else class="max-w-36 truncate text-ink-700">{{ item.label }}</span>
                </template>
              </div>
              <h1 class="truncate font-display text-xl font-semibold text-ink-900">{{ pageTitle }}</h1>
            </div>
          </div>

          <div data-profile-menu class="relative shrink-0">
            <button class="s-focus flex items-center gap-2 rounded-md p-1.5 hover:bg-primary-50" aria-haspopup="menu" :aria-expanded="profileOpen" @click.stop="profileOpen = !profileOpen">
              <span class="hidden text-right sm:block">
                <span class="block max-w-44 truncate text-sm font-semibold text-ink-900">{{ displayName }}</span>
                <span class="block text-xs capitalize text-ink-500">{{ displayRole }}</span>
              </span>
              <span class="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-xs font-semibold text-white">{{ initials }}</span>
              <ChevronDown :size="16" class="hidden text-ink-500 sm:block" aria-hidden="true" />
            </button>
            <div v-if="profileOpen" class="absolute right-0 mt-2 w-56 rounded-md border border-hairline bg-surface p-2 shadow-raised" role="menu">
              <div class="border-b border-hairline px-3 py-2.5">
                <p class="truncate text-sm font-semibold text-ink-900">{{ displayName }}</p>
                <p class="mt-1 text-xs capitalize text-ink-500">{{ displayRole }}</p>
              </div>
              <RouterLink v-if="canOpenSettings" :to="settingsPath" class="mt-2 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-ink-700 hover:bg-primary-50 hover:text-primary-700" role="menuitem"><Settings :size="17" /> Workspace settings</RouterLink>
              <SButton class="mt-1" variant="ghost" block @click="signOut"><LogOut :size="17" class="mr-2" />Sign out</SButton>
            </div>
          </div>
        </div>
      </header>

      <main class="min-w-0 px-4 py-6 sm:px-6 lg:px-8"><RouterView /></main>
    </div>
  </div>
</template>
