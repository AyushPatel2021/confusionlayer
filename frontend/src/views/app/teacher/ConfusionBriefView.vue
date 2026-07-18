<script setup lang="ts">
import { onMounted } from "vue";

import ConfusionBrief from "../../../components/ConfusionBrief.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();

onMounted(() => {
  if (!session.confusionBrief) void session.loadConfusionBrief();
});
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Teacher | reactive" title="Confusion brief" />
    <ConfusionBrief />
  </div>
</template>
