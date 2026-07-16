<script setup lang="ts">
import { onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const email = ref("");
const role = ref("teacher");
const roles = ["teacher", "student", "school_admin", "accountant", "hr", "parent"];

onMounted(() => session.loadMembers());

async function invite() {
  if (await session.inviteMember(email.value, role.value)) email.value = "";
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Settings" title="Members" subtitle="Invite people to your organization and manage their roles." />

    <form class="flex flex-wrap items-end gap-3 rounded-lg border border-hairline bg-surface p-5" @submit.prevent="invite">
      <label class="flex-1 text-sm">Email<input v-model="email" type="email" class="s-input mt-1" required /></label>
      <label class="text-sm">Role
        <select v-model="role" class="s-input mt-1 capitalize">
          <option v-for="r in roles" :key="r" :value="r">{{ r.replace("_", " ") }}</option>
        </select>
      </label>
      <SButton type="submit" variant="primary" :disabled="!email.trim() || session.loading === 'invite-member'">
        {{ session.loading === "invite-member" ? "Inviting…" : "Send invite" }}
      </SButton>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <SLoadingState v-if="session.loading === 'members' && !session.members.length" :rows="3" />
    <div v-else class="space-y-6">
      <div>
        <p class="s-eyebrow">Members ({{ session.members.length }})</p>
        <ul class="mt-3 divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface">
          <li v-for="m in session.members" :key="m.id" class="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
            <div>
              <p class="text-sm font-semibold text-ink-900">{{ m.name || m.email }}</p>
              <p class="text-xs text-ink-500">{{ m.email }}</p>
            </div>
            <SBadge :tone="m.role === 'owner' ? 'primary' : 'neutral'">{{ m.role.replace("_", " ") }}</SBadge>
          </li>
        </ul>
      </div>

      <div v-if="session.pendingInvites.length">
        <p class="s-eyebrow">Pending invitations ({{ session.pendingInvites.length }})</p>
        <ul class="mt-3 divide-y divide-hairline overflow-hidden rounded-lg border border-dashed border-hairline bg-surface">
          <li v-for="p in session.pendingInvites" :key="p.id" class="flex items-center justify-between gap-2 px-5 py-3">
            <span class="text-sm text-ink-700">{{ p.email }}</span>
            <SBadge tone="warning">{{ p.role.replace("_", " ") }} · pending</SBadge>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
