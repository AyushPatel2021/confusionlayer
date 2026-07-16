<script setup lang="ts">
// An inline word with a hand-drawn underline that draws itself in on scroll.
withDefaults(defineProps<{ color?: string; thickness?: number }>(), { color: "#C1592E", thickness: 3 });
</script>

<template>
  <span v-reveal class="draw relative inline-block whitespace-nowrap" style="--len: 240">
    <slot />
    <svg
      class="pointer-events-none absolute -bottom-1.5 left-0 h-2.5 w-full"
      viewBox="0 0 200 10"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        d="M3 6 C 40 1, 80 10, 120 4 S 180 2, 197 6"
        fill="none"
        :stroke="color"
        :stroke-width="thickness"
        stroke-linecap="round"
      />
    </svg>
  </span>
</template>
