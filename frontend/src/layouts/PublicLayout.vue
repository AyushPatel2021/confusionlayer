<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";

import SButton from "../components/ui/SButton.vue";
</script>

<template>
  <div class="flex min-h-screen flex-col bg-paper text-ink-900">
    <header class="border-b border-hairline bg-paper/80 backdrop-blur">
      <div class="mx-auto flex max-w-content items-center justify-between gap-4 px-6 py-4">
        <RouterLink to="/" class="flex items-baseline gap-2">
          <span class="font-display text-xl font-semibold text-ink-900">Slate</span>
          <span class="hidden text-xs font-medium text-ink-500 sm:inline">by ConfusionLayer</span>
        </RouterLink>
        <nav class="hidden items-center gap-6 text-sm font-medium text-ink-700 md:flex">
          <RouterLink class="hover:text-primary-600" to="/#schools">Schools</RouterLink>
          <RouterLink class="hover:text-primary-600" to="/#institutes">Institutes</RouterLink>
          <RouterLink class="hover:text-primary-600" to="/#students">Students</RouterLink>
        </nav>
        <div class="flex items-center gap-2">
          <RouterLink to="/login"><SButton variant="ghost">Sign in</SButton></RouterLink>
          <RouterLink to="/app"><SButton variant="primary">Open the app</SButton></RouterLink>
        </div>
      </div>
    </header>

    <main class="flex-1">
      <RouterView />
    </main>

    <footer class="border-t border-hairline">
      <div class="mx-auto max-w-content px-6 py-8 text-xs leading-5 text-ink-500">
        <p class="font-display text-sm font-semibold text-ink-700">Slate</p>
        <p class="mt-2 max-w-reading">
          Slate / ConfusionLayer is an independent educational product and is not affiliated with or endorsed by CBSE
          or NCERT. Curriculum references are used for educational alignment.
        </p>
      </div>
    </footer>
  </div>
</template>
