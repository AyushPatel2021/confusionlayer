<script setup lang="ts">
import { onMounted } from "vue";
import { RouterLink, RouterView } from "vue-router";

import SButton from "../components/ui/SButton.vue";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();

onMounted(() => void session.restore());
</script>

<template>
  <div class="flex min-h-screen flex-col bg-paper text-ink-900">
    <header class="border-b border-hairline bg-paper/80 backdrop-blur">
      <div class="mx-auto flex max-w-content items-center justify-between gap-4 px-6 py-4">
        <RouterLink to="/" class="flex items-center gap-2">
          <img src="/slate_logo.svg" alt="Slate" class="h-9 w-auto" />
        </RouterLink>
        <nav class="hidden items-center gap-7 text-sm font-medium text-ink-700 md:flex">
          <RouterLink class="link-underline transition-colors hover:text-primary-600" to="/schools">Schools</RouterLink>
          <RouterLink class="link-underline transition-colors hover:text-primary-600" to="/institutes">Institutes</RouterLink>
          <RouterLink class="link-underline transition-colors hover:text-primary-600" to="/students">Students</RouterLink>
          <RouterLink class="link-underline transition-colors hover:text-primary-600" to="/pricing">Pricing</RouterLink>
          <RouterLink class="link-underline transition-colors hover:text-primary-600" to="/about">About</RouterLink>
        </nav>
        <div class="flex items-center gap-2">
          <RouterLink v-if="session.isAuthenticated" :to="session.roleHome"><SButton variant="primary">Open workspace</SButton></RouterLink>
          <template v-else>
            <RouterLink to="/login"><SButton variant="ghost">Sign in</SButton></RouterLink>
            <RouterLink to="/signup"><SButton variant="primary">Get started</SButton></RouterLink>
          </template>
        </div>
      </div>
    </header>

    <main class="flex-1">
      <RouterView />
    </main>

    <footer class="border-t border-hairline">
      <div class="mx-auto max-w-content px-6 py-10">
        <div class="flex flex-wrap items-start justify-between gap-6">
          <div>
            <img src="/slate_logo.svg" alt="Slate" class="h-9 w-auto" />
            <p class="mt-1 text-xs text-ink-500">Run your school, clear the confusion.</p>
          </div>
          <nav class="flex flex-wrap gap-x-8 gap-y-2 text-sm text-ink-700">
            <RouterLink class="link-underline hover:text-primary-600" to="/schools">Schools</RouterLink>
            <RouterLink class="link-underline hover:text-primary-600" to="/institutes">Institutes</RouterLink>
            <RouterLink class="link-underline hover:text-primary-600" to="/students">Students</RouterLink>
            <RouterLink class="link-underline hover:text-primary-600" to="/pricing">Pricing</RouterLink>
            <RouterLink class="link-underline hover:text-primary-600" to="/about">About</RouterLink>
            <RouterLink v-if="!session.isAuthenticated" class="link-underline hover:text-primary-600" to="/login">Sign in</RouterLink>
            <RouterLink v-else class="link-underline hover:text-primary-600" :to="session.roleHome">Open workspace</RouterLink>
          </nav>
        </div>
        <p class="mt-8 max-w-reading text-xs leading-5 text-ink-500">
          Slate is an independent educational product and is not affiliated with or endorsed by CBSE or NCERT.
          Curriculum references are used for educational alignment.
        </p>
      </div>
    </footer>
  </div>
</template>
