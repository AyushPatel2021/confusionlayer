<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const email = ref("");
const role = ref("teacher");
const roles = ["teacher", "student", "school_admin", "accountant", "hr", "parent"];
const inviteDepartment = ref("Teaching & learning");
const departmentOptions = ["Teaching & learning", "Admissions", "Accounts", "HR", "Front-office", "Family", "Learning", "Workspace"];
const departmentsForRole: Record<string, string> = { teacher: "Teaching & learning", student: "Learning", school_admin: "Front-office", accountant: "Accounts", hr: "HR", parent: "Family" };
const guardianEmail = ref("");
const guardianStudentId = ref("");
const guardianDone = ref(false);
const query = ref("");
const department = ref("all");
const visibleMembers = computed(() => session.members.filter((member) => {
  const matchesQuery = `${member.name || ""} ${member.email} ${member.role}`.toLowerCase().includes(query.value.toLowerCase());
  return matchesQuery && (department.value === "all" || member.department === department.value);
}));
const departments = computed(() => [...new Set(session.members.map((member) => member.department))]);

onMounted(() => session.loadMembers());

async function invite() {
  if (await session.inviteMember(email.value, role.value, inviteDepartment.value)) email.value = "";
}
function roleChanged() { inviteDepartment.value = departmentsForRole[role.value] || "Workspace"; }

async function link() {
  const id = Number(guardianStudentId.value);
  if (!guardianEmail.value.trim() || !id) return;
  guardianDone.value = false;
  if (await session.linkGuardian(guardianEmail.value.trim(), id)) {
    guardianEmail.value = "";
    guardianStudentId.value = "";
    guardianDone.value = true;
  }
}

function setRole(userId: number, event: Event) {
  const role = (event.target as HTMLSelectElement).value;
  void session.changeMemberRole(userId, role);
}
function setDepartment(userId: number, event: Event) { void session.changeMemberDepartment(userId, (event.target as HTMLSelectElement).value); }
function removeMember(member: { id: number; name: string | null; email: string }) { if (window.confirm(`Remove ${member.name || member.email} from this workspace? The account will be deactivated and historical records retained.`)) void session.removeMember(member.id); }
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Settings" title="Members" subtitle="Invite people to your organization and manage their roles."><template #actions><a href="/api/org/members/export.csv" class="text-sm font-semibold text-primary-700 hover:underline">Export CSV</a></template></SPageHeader>

    <form class="flex flex-wrap items-end gap-3 rounded-lg border border-hairline bg-surface p-5" @submit.prevent="invite">
      <label class="flex-1 text-sm">Email<input v-model="email" type="email" class="s-input mt-1" required /></label>
      <label class="text-sm">Role
        <select v-model="role" class="s-input mt-1 capitalize" @change="roleChanged">
          <option v-for="r in roles" :key="r" :value="r">{{ r.replace("_", " ") }}</option>
        </select>
      </label>
      <label class="text-sm">Department<select v-model="inviteDepartment" class="s-input mt-1"><option v-for="item in departmentOptions" :key="item" :value="item">{{ item }}</option></select></label>
      <SButton type="submit" variant="primary" :disabled="!email.trim() || session.loading === 'invite-member'">
        {{ session.loading === "invite-member" ? "Inviting..." : "Send invite" }}
      </SButton>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <div v-if="session.user?.segment === 'school'" class="rounded-lg border border-hairline bg-surface p-5">
      <p class="s-eyebrow">Link a parent to a student</p>
      <p class="mt-1 text-xs text-ink-500">Connect an invited parent account to a student so they can follow along.</p>
      <form class="mt-3 flex flex-wrap items-end gap-3" @submit.prevent="link">
        <label class="flex-1 text-sm">Parent email<input v-model="guardianEmail" type="email" class="s-input mt-1" /></label>
        <label class="text-sm">Student ID<input v-model="guardianStudentId" type="number" class="s-input mt-1" /></label>
        <SButton type="submit" variant="secondary" :disabled="session.loading === 'link-guardian'">Link</SButton>
      </form>
      <p v-if="guardianDone" class="mt-2 text-sm text-success">Linked.</p>
    </div>

    <div class="flex flex-wrap gap-3 rounded-lg border border-hairline bg-surface p-4">
      <input v-model="query" class="s-input flex-1" placeholder="Search members" aria-label="Search members" />
      <select v-model="department" class="s-input"><option value="all">All departments</option><option v-for="item in departments" :key="item" :value="item">{{ item }}</option></select>
    </div>
    <SLoadingState v-if="session.loading === 'members' && !session.members.length" :rows="3" />
    <div v-else class="space-y-6">
      <div>
        <p class="s-eyebrow">Members ({{ session.members.length }})</p>
        <ul class="mt-3 divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface">
          <li v-for="m in visibleMembers" :key="m.id" class="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
            <div>
              <p class="text-sm font-semibold text-ink-900">{{ m.name || m.email }}</p>
              <p class="text-xs text-ink-500">{{ m.email }} | {{ m.department }}</p>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <select v-if="m.role !== 'owner' && !['teacher', 'student'].includes(m.role)" :value="m.role" class="s-input py-1 text-xs" @change="setRole(m.id, $event)">
                <option v-for="item in roles" :key="item" :value="item">{{ item.replace('_', ' ') }}</option>
              </select>
              <select v-if="m.role !== 'owner'" :value="m.department" class="s-input py-1 text-xs" @change="setDepartment(m.id, $event)"><option v-for="item in departmentOptions" :key="item" :value="item">{{ item }}</option></select>
              <SBadge :tone="m.status === 'active' ? 'success' : 'neutral'">{{ m.status }}</SBadge>
              <SButton v-if="m.role !== 'owner'" variant="ghost" :disabled="session.loading === `member-status-${m.id}`" @click="session.changeMemberStatus(m.id, m.status === 'active' ? 'inactive' : 'active')">{{ m.status === 'active' ? 'Deactivate' : 'Activate' }}</SButton>
              <SButton v-if="m.role !== 'owner'" variant="ghost" :disabled="session.loading === `member-remove-${m.id}`" @click="removeMember(m)">Remove</SButton>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="session.pendingInvites.length">
        <p class="s-eyebrow">Pending invitations ({{ session.pendingInvites.length }})</p>
        <ul class="mt-3 divide-y divide-hairline overflow-hidden rounded-lg border border-dashed border-hairline bg-surface">
          <li v-for="p in session.pendingInvites" :key="p.id" class="flex items-center justify-between gap-2 px-5 py-3">
            <span class="text-sm text-ink-700">{{ p.email }}</span>
            <SBadge tone="warning">{{ p.role.replace("_", " ") }} | {{ p.department }} | pending</SBadge>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
