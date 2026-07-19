<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div class="min-h-screen bg-paper text-ink-900">
    <header class="border-b border-hairline bg-surface">
      <div class="mx-auto flex max-w-content items-center justify-between gap-4 px-6 py-4">
        <div class="flex items-center gap-2.5">
          <img src="/slate_logo.svg" alt="" class="h-9 w-9 object-contain" />
          <span class="font-display text-lg font-semibold">Slate</span>
          <span class="text-xs font-semibold uppercase tracking-wide text-accent-600">Platform Admin</span>
        </div>
        <RouterLink to="/" class="text-sm font-medium text-ink-700 hover:text-primary-600">Exit admin</RouterLink>
      </div>
    </header>
    <main class="mx-auto max-w-content px-6 py-8">
      <RouterView />
    </main>
  </div>
</template>
