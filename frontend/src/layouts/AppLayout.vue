<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";

import AppSidebar from "../components/app/AppSidebar.vue";
import SButton from "../components/ui/SButton.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const router = useRouter();

const initials = computed(() => {
  const n = session.user?.name || session.user?.email || "?";
  return n.slice(0, 1).toUpperCase();
});

onMounted(() => {
  void session.restore();
});

async function signOut() {
  session.logout();
  router.push("/");
}
</script>

<template>
  <div class="min-h-screen bg-paper text-ink-900">
    <div class="mx-auto flex min-h-screen max-w-content">
      <!-- Sidebar -->
      <aside class="hidden w-60 shrink-0 flex-col border-r border-hairline bg-surface/60 px-4 py-6 md:flex">
        <RouterLink to="/" class="px-3 font-display text-xl font-semibold text-ink-900">Slate</RouterLink>
        <p class="mt-1 px-3 text-xs text-ink-500">{{ session.user?.org_name || "Workspace" }}</p>
        <div class="mt-8 flex-1"><AppSidebar /></div>
        <RouterLink to="/" class="px-3 text-xs text-ink-500 hover:text-primary-600">← Back to site</RouterLink>
      </aside>

      <!-- Main column -->
      <div class="flex min-w-0 flex-1 flex-col">
        <header class="flex items-center justify-between gap-4 border-b border-hairline bg-surface px-5 py-3">
          <!-- Mobile nav -->
          <div class="flex items-center gap-3 md:hidden">
            <RouterLink to="/" class="font-display text-lg font-semibold">Slate</RouterLink>
          </div>
          <div class="hidden md:block" />
          <div class="flex items-center gap-3">
            <div class="text-right">
              <p class="text-sm font-medium text-ink-900">{{ session.user?.name || session.user?.email }}</p>
              <p class="text-xs capitalize text-ink-500">{{ (session.user?.role || "").replace("_", " ") }}</p>
            </div>
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-sm font-semibold text-white">{{ initials }}</span>
            <SButton variant="ghost" @click="signOut">Sign out</SButton>
          </div>
        </header>

        <!-- Mobile sidebar links -->
        <div class="border-b border-hairline bg-surface/60 px-4 py-2 md:hidden">
          <AppSidebar />
        </div>

        <main class="flex-1 px-5 py-8 md:px-8">
          <RouterView />
        </main>

        <footer class="border-t border-hairline px-5 py-3 text-center text-xs text-ink-500">
          Slate / ConfusionLayer — independent educational product, not affiliated with CBSE or NCERT.
        </footer>
      </div>
    </div>
  </div>
</template>
