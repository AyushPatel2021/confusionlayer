<script setup lang="ts">
import { onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const showForm = ref(false);
const form = ref({ name: "", email: "", designation: "", salary: "" });
const period = ref("");

onMounted(() => {
  session.loadEmployees();
  session.loadPayrollRuns();
});

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { minimumFractionDigits: 0 })}`;

async function addEmployee() {
  const salary_cents = Math.round(parseFloat(form.value.salary || "0") * 100);
  if (await session.createEmployee({ name: form.value.name, email: form.value.email || undefined, designation: form.value.designation || undefined, salary_cents })) {
    form.value = { name: "", email: "", designation: "", salary: "" };
    showForm.value = false;
  }
}
async function run() {
  if (period.value.trim() && (await session.runPayroll(period.value.trim()))) period.value = "";
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="HR & payroll" title="Staff" subtitle="Manage employees and run payroll.">
      <template #actions>
        <SButton variant="primary" @click="showForm = !showForm">{{ showForm ? "Close" : "Add employee" }}</SButton>
      </template>
    </SPageHeader>

    <form v-if="showForm" class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-4" @submit.prevent="addEmployee">
      <label class="text-sm">Name<input v-model="form.name" class="s-input mt-1" required /></label>
      <label class="text-sm">Email<input v-model="form.email" type="email" class="s-input mt-1" /></label>
      <label class="text-sm">Designation<input v-model="form.designation" class="s-input mt-1" /></label>
      <label class="text-sm">Monthly salary (₹)<input v-model="form.salary" type="number" min="0" class="s-input mt-1" /></label>
      <div class="sm:col-span-4"><SButton type="submit" variant="primary" :disabled="!form.name.trim() || session.loading === 'create-employee'">Add employee</SButton></div>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <!-- Employees -->
    <div>
      <p class="s-eyebrow">Employees ({{ session.employees.length }})</p>
      <SLoadingState v-if="session.loading === 'employees' && !session.employees.length" class="mt-3" :rows="2" />
      <div v-else-if="session.employees.length" class="mt-3 overflow-hidden rounded-lg border border-hairline bg-surface">
        <table class="w-full text-sm">
          <thead class="bg-surface-sunken text-left text-xs uppercase tracking-wide text-ink-500">
            <tr><th class="px-4 py-3">Name</th><th class="px-4 py-3">Designation</th><th class="px-4 py-3">Salary</th><th class="px-4 py-3">Status</th></tr>
          </thead>
          <tbody class="divide-y divide-hairline">
            <tr v-for="e in session.employees" :key="e.id">
              <td class="px-4 py-3 font-medium text-ink-900">{{ e.name }}</td>
              <td class="px-4 py-3 text-ink-700">{{ e.designation || "N/A" }}</td>
              <td class="px-4 py-3 text-ink-700">{{ money(e.salary_cents) }}</td>
              <td class="px-4 py-3"><SBadge :tone="e.status === 'active' ? 'success' : 'neutral'">{{ e.status }}</SBadge></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="mt-3 text-sm text-ink-500">No employees yet.</p>
    </div>

    <!-- Payroll -->
    <div>
      <div class="flex flex-wrap items-end justify-between gap-3">
        <p class="s-eyebrow">Payroll runs</p>
        <form class="flex items-end gap-2" @submit.prevent="run">
          <label class="text-sm">Period<input v-model="period" class="s-input mt-1" placeholder="2026-07" /></label>
          <SButton type="submit" variant="primary" :disabled="!period.trim() || session.loading === 'run-payroll'">Run payroll</SButton>
        </form>
      </div>
      <ul class="mt-3 space-y-2">
        <li v-for="r in session.payrollRuns" :key="r.id" class="flex items-center justify-between rounded-md border border-hairline bg-surface px-4 py-3 text-sm">
          <span class="font-medium text-ink-900">{{ r.period }}</span>
          <span class="text-ink-500">{{ r.payslip_count }} payslips | net {{ money(r.total_net_cents) }} <SBadge tone="success">{{ r.status }}</SBadge></span>
        </li>
        <li v-if="!session.payrollRuns.length" class="text-sm text-ink-500">No payroll runs yet.</li>
      </ul>
    </div>
  </div>
</template>
