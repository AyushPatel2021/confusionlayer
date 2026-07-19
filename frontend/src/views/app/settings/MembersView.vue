<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SConfirmDialog from "../../../components/ui/SConfirmDialog.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import SStatCard from "../../../components/ui/SStatCard.vue";
import { displayRoleLabel, roleLabels, useSessionStore, type Role } from "../../../stores/session";

const session = useSessionStore();
const email = ref("");
const role = ref("teacher");
const roles = ["teacher", "student", "school_admin", "accountant", "hr", "parent"];
const inviteDepartment = ref("Teaching & learning");
const departmentOptions = ["Teaching & learning", "Admissions", "Accounts", "HR", "Front-office", "Family", "Learning", "Workspace"];
const departmentsForRole: Record<string, string> = { teacher: "Teaching & learning", student: "Learning", school_admin: "Front-office", accountant: "Accounts", hr: "HR", parent: "Family" };
const guardianEmail = ref("");
const guardianStudentId = ref<number | null>(null);
const guardianDone = ref(false);
const query = ref("");
const department = ref("all");
const memberToRemove = ref<{ id: number; name: string | null; email: string } | null>(null);
const visibleMembers = computed(() => session.members.filter((member) => {
  const matchesQuery = `${member.name || ""} ${member.email} ${member.role}`.toLowerCase().includes(query.value.toLowerCase());
  return matchesQuery && (department.value === "all" || member.department === department.value);
}));
const departments = computed(() => [...new Set(session.members.map((member) => member.department))]);
const activeMembers = computed(() => session.members.filter((member) => member.status === "active"));
const roleMix = computed(() => roles.map((item) => ({
  role: item,
  count: session.members.filter((member) => member.role === item).length,
})).filter((item) => item.count));
const roleOptions = computed(() => roles.map((item) => ({ label: roleLabel(item), value: item })));
const departmentSelectOptions = computed(() => [{ label: "All departments", value: "all" }, ...departments.value.map((item) => ({ label: item, value: item }))]);
const departmentOptionsForCombobox = computed(() => departmentOptions.map((item) => ({ label: item, value: item })));
const studentSelectOptions = computed(() => session.studentOptions.map((student) => ({ label: student.name, value: student.id })));
const departmentGroups = computed(() => {
  const source = visibleMembers.value;
  const names = department.value === "all" ? departments.value : [department.value];
  return names.map((name) => ({
    name,
    members: source.filter((member) => member.department === name),
  })).filter((group) => group.members.length);
});
const roleLabel = (role: string) => roleLabels[role as Role] || role.replace("_", " ");
const memberDisplayRole = (role: string) => displayRoleLabel({ role: role as Role, segment: session.user?.segment || null });

onMounted(async () => {
  await session.loadMembers();
  if (session.user?.segment === "school") await session.loadStudentOptions();
});

async function invite() {
  if (await session.inviteMember(email.value, role.value, inviteDepartment.value)) email.value = "";
}
function roleChanged() { inviteDepartment.value = departmentsForRole[role.value] || "Workspace"; }

async function link() {
  const id = guardianStudentId.value;
  if (!guardianEmail.value.trim() || !id) return;
  guardianDone.value = false;
  if (await session.linkGuardian(guardianEmail.value.trim(), id)) {
    guardianEmail.value = "";
    guardianStudentId.value = null;
    guardianDone.value = true;
  }
}

function setRoleValue(userId: number, value: string | number | null) {
  if (typeof value === "string") void session.changeMemberRole(userId, value);
}
function setDepartmentValue(userId: number, value: string | number | null) {
  if (typeof value === "string") void session.changeMemberDepartment(userId, value);
}
async function removeMember() {
  if (!memberToRemove.value) return;
  await session.removeMember(memberToRemove.value.id);
  memberToRemove.value = null;
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Settings" title="Members" subtitle="Invite people to your organization and manage their roles."><template #actions><a href="/api/org/members/export.csv" class="text-sm font-semibold text-primary-700 hover:underline">Export CSV</a></template></SPageHeader>

    <div class="grid gap-4 sm:grid-cols-4">
      <SStatCard label="Total members" :value="session.members.length" />
      <SStatCard label="Active" :value="activeMembers.length" tone="success" />
      <SStatCard label="Pending" :value="session.pendingInvites.length" tone="warning" />
      <SStatCard label="Departments" :value="departments.length" />
    </div>

    <section class="grid gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,0.8fr)]">
      <form class="rounded-lg border border-hairline bg-surface p-5" @submit.prevent="invite">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="s-eyebrow">Invite member</p>
            <p class="mt-1 text-sm text-ink-500">Send role-based access for staff, learners, and families.</p>
          </div>
          <SButton type="submit" variant="primary" :disabled="!email.trim() || session.loading === 'invite-member'">
            {{ session.loading === "invite-member" ? "Inviting..." : "Send invite" }}
          </SButton>
        </div>
        <div class="mt-4 grid gap-3 md:grid-cols-[minmax(0,1.4fr)_minmax(0,0.8fr)_minmax(0,1fr)]">
          <label class="text-sm">Email<input v-model="email" type="email" class="s-input mt-1" required /></label>
          <SCombobox v-model="role" label="Role" placeholder="Choose role" :options="roleOptions" @change="roleChanged" />
          <SCombobox v-model="inviteDepartment" label="Department" placeholder="Choose department" :options="departmentOptionsForCombobox" />
        </div>
      </form>

      <aside class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Role mix</p>
        <div class="mt-4 space-y-3">
          <div v-for="item in roleMix" :key="item.role" class="flex items-center justify-between gap-3">
            <span class="text-sm font-medium text-ink-700">{{ roleLabel(item.role) }}</span>
            <SBadge tone="neutral">{{ item.count }}</SBadge>
          </div>
          <p v-if="!roleMix.length" class="text-sm text-ink-500">No members yet.</p>
        </div>
      </aside>
    </section>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <div v-if="session.user?.segment === 'school'" class="rounded-lg border border-hairline bg-surface p-5">
      <p class="s-eyebrow">Link a parent to a student</p>
      <p class="mt-1 text-xs text-ink-500">Connect an invited parent account to a student so they can follow along.</p>
      <form class="mt-3 flex flex-wrap items-end gap-3" @submit.prevent="link">
        <label class="flex-1 text-sm">Parent email<input v-model="guardianEmail" type="email" class="s-input mt-1" /></label>
        <SCombobox v-model="guardianStudentId" label="Student" placeholder="Choose student" :options="studentSelectOptions" />
        <SButton type="submit" variant="secondary" :disabled="session.loading === 'link-guardian'">Link</SButton>
      </form>
      <p v-if="guardianDone" class="mt-2 text-sm text-success">Linked.</p>
    </div>

    <section class="rounded-lg border border-hairline bg-surface p-5">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="s-eyebrow">Find members</p>
          <p class="mt-1 text-sm text-ink-500">Search by name, email, or role, then narrow the list by department.</p>
        </div>
        <SBadge tone="neutral">{{ visibleMembers.length }} shown</SBadge>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-[minmax(0,1.5fr)_minmax(14rem,0.7fr)]">
        <label class="text-sm font-medium text-ink-700">Search<input v-model="query" class="s-input mt-1" placeholder="Name, email, or role" aria-label="Search members" /></label>
        <SCombobox v-model="department" label="Department" placeholder="All departments" :options="departmentSelectOptions" />
      </div>
    </section>
    <SLoadingState v-if="session.loading === 'members' && !session.members.length" :rows="3" />
    <div v-else class="space-y-6">
      <div>
        <div class="flex items-center justify-between gap-3">
          <p class="s-eyebrow">Members ({{ visibleMembers.length }})</p>
          <span class="text-xs text-ink-500">{{ department === "all" ? "Grouped by department" : department }}</span>
        </div>
        <div v-if="departmentGroups.length" class="mt-3 grid gap-4 xl:grid-cols-2">
          <section v-for="group in departmentGroups" :key="group.name" class="rounded-lg border border-hairline bg-surface">
            <div class="flex items-center justify-between border-b border-hairline px-5 py-4">
              <h2 class="font-display text-lg font-semibold text-ink-900">{{ group.name }}</h2>
              <SBadge tone="neutral">{{ group.members.length }}</SBadge>
            </div>
            <div class="divide-y divide-hairline">
              <article v-for="m in group.members" :key="m.id" class="p-4">
                <div class="flex flex-wrap items-start justify-between gap-3">
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold text-ink-900">{{ m.name || m.email }}</p>
                    <p class="mt-1 truncate text-xs text-ink-500">{{ m.email }}</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <SBadge tone="primary">{{ memberDisplayRole(m.role) }}</SBadge>
                    <SBadge :tone="m.status === 'active' ? 'success' : 'neutral'">{{ m.status }}</SBadge>
                  </div>
                </div>
                <div v-if="m.role !== 'owner'" class="mt-4 grid gap-2 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1fr)_auto_auto]">
                  <SCombobox v-if="!['teacher', 'student'].includes(m.role)" :model-value="m.role" placeholder="Role" :options="roleOptions" @update:model-value="setRoleValue(m.id, $event)" />
                  <div v-else class="rounded-md bg-surface-sunken px-3 py-2 text-xs text-ink-500">Role managed by profile</div>
                  <SCombobox :model-value="m.department" placeholder="Department" :options="departmentOptionsForCombobox" @update:model-value="setDepartmentValue(m.id, $event)" />
                  <SButton variant="ghost" :disabled="session.loading === `member-status-${m.id}`" @click="session.changeMemberStatus(m.id, m.status === 'active' ? 'inactive' : 'active')">{{ m.status === 'active' ? 'Deactivate' : 'Activate' }}</SButton>
                  <SButton variant="ghost" :disabled="session.loading === `member-remove-${m.id}`" @click="memberToRemove = m">Remove</SButton>
                </div>
              </article>
            </div>
          </section>
        </div>
        <p v-else class="mt-3 rounded-lg border border-dashed border-hairline bg-surface p-6 text-sm text-ink-500">No members match the current filters.</p>
      </div>

      <div v-if="session.pendingInvites.length">
        <p class="s-eyebrow">Pending invitations ({{ session.pendingInvites.length }})</p>
        <div class="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <article v-for="p in session.pendingInvites" :key="p.id" class="rounded-lg border border-dashed border-hairline bg-surface p-4">
            <p class="truncate text-sm font-semibold text-ink-900">{{ p.email }}</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <SBadge tone="warning">Pending</SBadge>
              <SBadge tone="neutral">{{ roleLabel(p.role) }}</SBadge>
              <SBadge tone="neutral">{{ p.department }}</SBadge>
            </div>
          </article>
        </div>
      </div>
    </div>
    <SConfirmDialog
      :open="!!memberToRemove"
      title="Remove member"
      :message="`Remove ${memberToRemove?.name || memberToRemove?.email || 'this member'} from this workspace? The account will be deactivated and historical records retained.`"
      confirm-label="Remove"
      :busy="!!memberToRemove && session.loading === `member-remove-${memberToRemove.id}`"
      @cancel="memberToRemove = null"
      @confirm="removeMember"
    />
  </div>
</template>
