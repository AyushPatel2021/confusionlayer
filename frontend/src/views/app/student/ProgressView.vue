<script setup lang="ts">
import Progress from "../../../components/Progress.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Student | mastery over time" title="My progress" />
    <Progress />
  </div>
</template>
