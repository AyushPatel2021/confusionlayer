<script setup lang="ts">
import { RouterLink } from "vue-router";

import SButton from "../ui/SButton.vue";

withDefaults(defineProps<{ heading: string; segment?: string }>(), { segment: "" });
</script>

<template>
  <section class="border-t border-hairline">
    <div v-reveal class="mx-auto max-w-content px-6 py-20 text-center">
      <h2 class="mx-auto max-w-2xl font-display text-3xl font-semibold text-ink-900 md:text-4xl">{{ heading }}</h2>
      <div class="mt-8 flex justify-center">
        <RouterLink :to="segment ? `/signup?segment=${segment}` : '/signup'" class="nudge-host">
          <SButton variant="primary">Get started — free <span class="nudge">→</span></SButton>
        </RouterLink>
      </div>
      <p class="mt-3 text-xs text-ink-500">No card required. All plans are free right now.</p>
    </div>
  </section>
</template>
