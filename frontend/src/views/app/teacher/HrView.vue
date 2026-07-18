<script setup lang="ts">
import { onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const showForm = ref(false);
const form = ref({ name: "", email: "", designation_id: null as number | null, salary_structure_id: null as number | null, employment_type: "full_time", phone: "", join_date: "", salary: "" });
const editingId = ref<number | null>(null);
const period = ref("");
const designationForm = ref({ name: "", department: "" });
const salaryStructureForm = ref({ name: "", amount: "" });

onMounted(() => {
  session.loadEmployees();
  session.loadPayrollRuns();
  session.loadHrReferences();
});

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { minimumFractionDigits: 0 })}`;

async function addEmployee() {
  const salary_cents = Math.round(parseFloat(form.value.salary || "0") * 100);
  const payload = { name: form.value.name, designation_id: form.value.designation_id || undefined, salary_structure_id: form.value.salary_structure_id || undefined, employment_type: form.value.employment_type, email: form.value.email || undefined, phone: form.value.phone || undefined, join_date: form.value.join_date || undefined, salary_cents };
  const saved = editingId.value ? await session.updateEmployee(editingId.value, payload) : await session.createEmployee(payload);
  if (saved) {
    form.value = { name: "", email: "", designation_id: null, salary_structure_id: null, employment_type: "full_time", phone: "", join_date: "", salary: "" };
    editingId.value = null;
    showForm.value = false;
  }
}
function edit(employee: { id: number; name: string; email: string | null; designation_id: number | null; salary_structure_id: number | null; employment_type: string; phone: string | null; join_date: string | null; salary_cents: number }) { editingId.value = employee.id; form.value = { name: employee.name, email: employee.email || "", designation_id: employee.designation_id, salary_structure_id: employee.salary_structure_id, employment_type: employee.employment_type, phone: employee.phone || "", join_date: employee.join_date || "", salary: String(employee.salary_cents / 100) }; showForm.value = true; }
async function toggleStatus(employee: { id: number; name: string; status: string }) { const next = employee.status === "active" ? "inactive" : "active"; if (window.confirm(`${next === "inactive" ? "Deactivate" : "Reactivate"} ${employee.name}?`)) await session.setEmployeeStatus(employee.id, next); }
async function run() {
  if (period.value.trim() && (await session.runPayroll(period.value.trim()))) period.value = "";
}
async function addDesignation() { if (await session.createDesignation(designationForm.value)) designationForm.value = { name: "", department: "" }; }
async function addSalaryStructure() { if (await session.createSalaryStructure({ name: salaryStructureForm.value.name, monthly_amount_cents: Math.round(Number(salaryStructureForm.value.amount || 0) * 100) })) salaryStructureForm.value = { name: "", amount: "" }; }
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="HR & payroll" title="Staff" subtitle="Manage employees and run payroll.">
      <template #actions>
        <SButton variant="primary" @click="showForm = !showForm">{{ showForm ? "Close" : "Add employee" }}</SButton>
      </template>
    </SPageHeader>

    <form v-if="showForm" class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-3" @submit.prevent="addEmployee">
      <label class="text-sm">Name<input v-model="form.name" class="s-input mt-1" required /></label>
      <label class="text-sm">Email<input v-model="form.email" type="email" class="s-input mt-1" /></label>
      <label class="text-sm">Designation<select v-model="form.designation_id" class="s-input mt-1"><option :value="null">No designation</option><option v-for="item in session.designations" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
      <label class="text-sm">Employment type<select v-model="form.employment_type" class="s-input mt-1"><option value="full_time">Full time</option><option value="part_time">Part time</option><option value="contract">Contract</option><option value="intern">Intern</option></select></label>
      <label class="text-sm">Phone<input v-model="form.phone" class="s-input mt-1" /></label>
      <label class="text-sm">Join date<input v-model="form.join_date" type="date" class="s-input mt-1" /></label>
      <label class="text-sm">Salary structure<select v-model="form.salary_structure_id" class="s-input mt-1"><option :value="null">Custom salary</option><option v-for="item in session.salaryStructures" :key="item.id" :value="item.id">{{ item.name }} · {{ money(item.monthly_amount_cents) }}</option></select></label>
      <label v-if="!form.salary_structure_id" class="text-sm">Monthly salary (₹)<input v-model="form.salary" type="number" min="0" class="s-input mt-1" /></label>
      <div class="sm:col-span-3"><SButton type="submit" variant="primary" :disabled="!form.name.trim() || session.loading === 'create-employee'">{{ editingId ? "Save employee" : "Add employee" }}</SButton></div>
    </form>
    <div class="grid gap-4 rounded-lg border border-hairline bg-surface p-5 md:grid-cols-2"><form class="flex flex-wrap items-end gap-2" @submit.prevent="addDesignation"><label class="flex-1 text-sm">Designation<input v-model="designationForm.name" required class="s-input mt-1" /></label><label class="flex-1 text-sm">Department<input v-model="designationForm.department" class="s-input mt-1" /></label><SButton type="submit" variant="secondary">Add designation</SButton></form><form class="flex flex-wrap items-end gap-2" @submit.prevent="addSalaryStructure"><label class="flex-1 text-sm">Salary structure<input v-model="salaryStructureForm.name" required class="s-input mt-1" /></label><label class="w-28 text-sm">Monthly ₹<input v-model="salaryStructureForm.amount" required type="number" min="0" class="s-input mt-1" /></label><SButton type="submit" variant="secondary">Add structure</SButton></form></div>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <!-- Employees -->
    <div>
      <p class="s-eyebrow">Employees ({{ session.employees.length }})</p>
      <SLoadingState v-if="session.loading === 'employees' && !session.employees.length" class="mt-3" :rows="2" />
      <div v-else-if="session.employees.length" class="mt-3 overflow-hidden rounded-lg border border-hairline bg-surface">
        <table class="w-full text-sm">
          <thead class="bg-surface-sunken text-left text-xs uppercase tracking-wide text-ink-500">
            <tr><th class="px-4 py-3">Name</th><th class="px-4 py-3">Designation</th><th class="px-4 py-3">Salary</th><th class="px-4 py-3">Status</th><th></th></tr>
          </thead>
          <tbody class="divide-y divide-hairline">
            <tr v-for="e in session.employees" :key="e.id">
              <td class="px-4 py-3 font-medium text-ink-900">{{ e.name }}</td>
              <td class="px-4 py-3 text-ink-700">{{ e.designation || "N/A" }}</td>
              <td class="px-4 py-3 text-ink-700">{{ money(e.salary_cents) }}</td>
              <td class="px-4 py-3"><SBadge :tone="e.status === 'active' ? 'success' : 'neutral'">{{ e.status }}</SBadge></td>
              <td class="px-4 py-3 text-right"><SButton variant="ghost" @click="edit(e)">Edit</SButton><SButton variant="ghost" :disabled="session.loading === `employee-${e.id}`" @click="toggleStatus(e)">{{ e.status === "active" ? "Deactivate" : "Reactivate" }}</SButton></td>
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
          <span class="flex items-center gap-2 text-ink-500">{{ r.payslip_count }} payslips | net {{ money(r.total_net_cents) }} <SBadge tone="success">{{ r.status }}</SBadge><a :href="`/api/hr/payroll/${r.id}/export.csv`" class="font-semibold text-primary-700 hover:underline">CSV</a><a :href="`/api/hr/payroll/${r.id}/print`" target="_blank" class="font-semibold text-primary-700 hover:underline">Print</a></span>
        </li>
        <li v-if="!session.payrollRuns.length" class="text-sm text-ink-500">No payroll runs yet.</li>
      </ul>
    </div>
  </div>
</template>
