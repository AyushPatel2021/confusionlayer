<script setup lang="ts">
import { onMounted } from "vue";

import ForecastBrief from "../../../components/ForecastBrief.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();

onMounted(() => {
  if (!session.forecastBrief) void session.loadForecastBrief();
});
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Teacher · headline" title="Forecast brief" />
    <ForecastBrief />
  </div>
</template>
