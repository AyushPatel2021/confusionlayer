<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import SConfirmDialog from "../../../components/ui/SConfirmDialog.vue";
import SStatCard from "../../../components/ui/SStatCard.vue";
import { useSessionStore } from "../../../stores/session";

const session = useSessionStore();
const showForm = ref(false);
const form = ref({ name: "", email: "", designation_id: null as number | null, salary_structure_id: null as number | null, employment_type: "full_time", phone: "", join_date: "", salary: "" });
const editingId = ref<number | null>(null);
const period = ref("");
const designationForm = ref({ name: "", department: "" });
const salaryStructureForm = ref({ name: "", amount: "" });
const statusTarget = ref<{ id: number; name: string; status: string } | null>(null);
const designationOptions = computed(() => session.designations.map((item) => ({ label: item.name, value: item.id, hint: item.department || "No department" })));
const salaryStructureOptions = computed(() => session.salaryStructures.map((item) => ({ label: item.name, value: item.id, hint: money(item.monthly_amount_cents) })));
const designationById = computed(() => new Map(session.designations.map((item) => [item.id, item])));
const salaryStructureById = computed(() => new Map(session.salaryStructures.map((item) => [item.id, item])));
const activeEmployees = computed(() => session.employees.filter((employee) => employee.status === "active"));
const departments = computed(() => {
  const names = new Set(session.designations.map((item) => item.department || "Unassigned"));
  session.employees.forEach((employee) => names.add(designationById.value.get(employee.designation_id || 0)?.department || "Unassigned"));
  return [...names];
});
const monthlyPayroll = computed(() => activeEmployees.value.reduce((total, employee) => total + employee.salary_cents, 0));
const groupedEmployees = computed(() => departments.value.map((department) => ({
  department,
  designations: session.designations.filter((item) => (item.department || "Unassigned") === department),
  employees: session.employees.filter((employee) => (designationById.value.get(employee.designation_id || 0)?.department || "Unassigned") === department),
})).filter((group) => group.designations.length || group.employees.length));

onMounted(() => {
  session.loadEmployees();
  session.loadPayrollRuns();
  session.loadHrReferences();
});

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { minimumFractionDigits: 0 })}`;
const employmentLabel = (value: string) => value.replace("_", " ");
const salaryStructureLabel = (id: number | null) => id ? salaryStructureById.value.get(id)?.name || "Custom salary" : "Custom salary";

function syncSalaryFromStructure() {
  const structure = form.value.salary_structure_id ? salaryStructureById.value.get(form.value.salary_structure_id) : null;
  if (structure) form.value.salary = String(structure.monthly_amount_cents / 100);
}

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
async function toggleStatus() { if (statusTarget.value) { await session.setEmployeeStatus(statusTarget.value.id, statusTarget.value.status === "active" ? "inactive" : "active"); statusTarget.value = null; } }
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

    <div class="grid gap-4 sm:grid-cols-3">
      <SStatCard label="Active staff" :value="activeEmployees.length" />
      <SStatCard label="Departments" :value="departments.length" />
      <SStatCard label="Monthly payroll" :value="money(monthlyPayroll)" tone="warning" />
    </div>

    <form v-if="showForm" class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-3" @submit.prevent="addEmployee">
      <label class="text-sm">Name<input v-model="form.name" class="s-input mt-1" required /></label>
      <label class="text-sm">Email<input v-model="form.email" type="email" class="s-input mt-1" /></label>
      <SCombobox v-model="form.designation_id" label="Designation" placeholder="Choose designation" :options="designationOptions" />
      <label class="text-sm">Employment type<select v-model="form.employment_type" class="s-input mt-1"><option value="full_time">Full time</option><option value="part_time">Part time</option><option value="contract">Contract</option><option value="intern">Intern</option></select></label>
      <label class="text-sm">Phone<input v-model="form.phone" class="s-input mt-1" /></label>
      <label class="text-sm">Join date<input v-model="form.join_date" type="date" class="s-input mt-1" /></label>
      <SCombobox v-model="form.salary_structure_id" label="Salary structure" placeholder="Custom salary" :options="salaryStructureOptions" @change="syncSalaryFromStructure" />
      <label class="text-sm">Monthly salary (₹)<input v-model="form.salary" type="number" min="0" class="s-input mt-1" :disabled="!!form.salary_structure_id" /></label>
      <div class="sm:col-span-3"><SButton type="submit" variant="primary" :disabled="!form.name.trim() || session.loading === 'create-employee'">{{ editingId ? "Save employee" : "Add employee" }}</SButton></div>
    </form>
    <div class="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
      <section class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Reference hierarchy</p>
        <form class="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]" @submit.prevent="addDesignation">
          <label class="text-sm">Designation<input v-model="designationForm.name" required class="s-input mt-1" /></label>
          <label class="text-sm">Department<input v-model="designationForm.department" class="s-input mt-1" /></label>
          <SButton class="self-end" type="submit" variant="secondary">Add designation</SButton>
        </form>
        <div class="mt-4 space-y-3">
          <div v-for="group in groupedEmployees" :key="group.department" class="rounded-md border border-hairline p-3">
            <div class="flex items-center justify-between gap-3">
              <p class="font-semibold text-ink-900">{{ group.department }}</p>
              <span class="text-xs text-ink-500">{{ group.employees.length }} staff</span>
            </div>
            <div class="mt-3 flex flex-wrap gap-2">
              <SBadge v-for="designation in group.designations" :key="designation.id" tone="neutral">{{ designation.name }}</SBadge>
              <span v-if="!group.designations.length" class="text-sm text-ink-500">No designations yet.</span>
            </div>
          </div>
        </div>
      </section>
      <section class="rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Salary structures</p>
        <form class="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_140px_auto]" @submit.prevent="addSalaryStructure">
          <label class="text-sm">Structure<input v-model="salaryStructureForm.name" required class="s-input mt-1" /></label>
          <label class="text-sm">Monthly ₹<input v-model="salaryStructureForm.amount" required type="number" min="0" class="s-input mt-1" /></label>
          <SButton class="self-end" type="submit" variant="secondary">Add</SButton>
        </form>
        <ul class="mt-4 divide-y divide-hairline border-t border-hairline">
          <li v-for="structure in session.salaryStructures" :key="structure.id" class="flex items-center justify-between py-3 text-sm">
            <span class="font-medium text-ink-900">{{ structure.name }}</span>
            <span class="text-ink-500">{{ money(structure.monthly_amount_cents) }}</span>
          </li>
          <li v-if="!session.salaryStructures.length" class="py-3 text-sm text-ink-500">No salary structures yet.</li>
        </ul>
      </section>
    </div>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <!-- Employees -->
    <div>
      <p class="s-eyebrow">Employees ({{ session.employees.length }})</p>
      <SLoadingState v-if="session.loading === 'employees' && !session.employees.length" class="mt-3" :rows="2" />
      <div v-else-if="session.employees.length" class="mt-3 space-y-4">
        <section v-for="group in groupedEmployees" :key="group.department" class="rounded-lg border border-hairline bg-surface p-5">
          <div class="flex items-center justify-between gap-3">
            <h2 class="font-display text-xl font-semibold text-ink-900">{{ group.department }}</h2>
            <span class="text-sm text-ink-500">{{ group.employees.length }} employee{{ group.employees.length === 1 ? "" : "s" }}</span>
          </div>
          <div class="mt-4 grid gap-3 lg:grid-cols-2">
            <article v-for="e in group.employees" :key="e.id" class="rounded-md border border-hairline p-4">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 class="font-semibold text-ink-900">{{ e.name }}</h3>
                  <p class="mt-1 text-sm text-ink-500">{{ e.designation || "No designation" }} | {{ employmentLabel(e.employment_type) }}</p>
                  <p v-if="e.email || e.phone" class="mt-1 text-xs text-ink-500">{{ e.email || e.phone }}</p>
                </div>
                <SBadge :tone="e.status === 'active' ? 'success' : 'neutral'">{{ e.status }}</SBadge>
              </div>
              <div class="mt-4 grid gap-3 sm:grid-cols-2">
                <div class="rounded-md bg-surface-sunken px-3 py-2">
                  <p class="text-xs text-ink-500">Salary structure</p>
                  <p class="text-sm font-semibold text-ink-900">{{ salaryStructureLabel(e.salary_structure_id) }}</p>
                </div>
                <div class="rounded-md bg-surface-sunken px-3 py-2">
                  <p class="text-xs text-ink-500">Monthly salary</p>
                  <p class="text-sm font-semibold text-ink-900">{{ money(e.salary_cents) }}</p>
                </div>
              </div>
              <div class="mt-4 flex justify-end gap-2">
                <SButton variant="ghost" @click="edit(e)">Edit</SButton>
                <SButton variant="ghost" :disabled="session.loading === `employee-${e.id}`" @click="statusTarget = e">{{ e.status === "active" ? "Deactivate" : "Reactivate" }}</SButton>
              </div>
            </article>
            <p v-if="!group.employees.length" class="text-sm text-ink-500">No employees assigned to this department.</p>
          </div>
        </section>
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
    <SConfirmDialog :open="!!statusTarget" :title="statusTarget?.status === 'active' ? 'Deactivate employee' : 'Reactivate employee'" :message="`${statusTarget?.name || 'This employee'} will remain in historical payroll records.`" :confirm-label="statusTarget?.status === 'active' ? 'Deactivate' : 'Reactivate'" @cancel="statusTarget = null" @confirm="toggleStatus" />
  </div>
</template>
