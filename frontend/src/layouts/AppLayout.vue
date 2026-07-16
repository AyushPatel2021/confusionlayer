<script setup lang="ts">
import { RouterView } from "vue-router";

// Thin app shell for M0. The role-aware sidebar/nav lands in M4 when the
// ConsoleView is decomposed into the real teacher/student apps; for now the
// ConsoleView renders its own header so the existing demo keeps working.
</script>

<template>
  <div class="flex min-h-screen flex-col bg-paper text-ink-900">
    <div class="flex-1">
      <RouterView />
    </div>
    <footer class="border-t border-hairline bg-surface px-5 py-3 text-center text-xs leading-5 text-ink-500">
      Slate / ConfusionLayer is an independent educational product and is not affiliated with or endorsed by CBSE or
      NCERT.
    </footer>
  </div>
</template>
