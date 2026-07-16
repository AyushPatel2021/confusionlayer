<script setup lang="ts">
import SEmptyState from "../../components/ui/SEmptyState.vue";
import SPageHeader from "../../components/ui/SPageHeader.vue";
</script>

<template>
  <div class="space-y-8">
    <SPageHeader
      eyebrow="Platform admin"
      title="Admin console"
      subtitle="Cross-organization management — orgs, users, curriculum library, usage, and audit."
    />
    <SEmptyState
      title="Coming in a later milestone"
      message="The platform admin backend (orgs, users, content, usage, audit) is scheduled for M11 in the product plan."
    />
  </div>
</template>
