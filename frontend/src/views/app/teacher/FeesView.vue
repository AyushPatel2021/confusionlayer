<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore, type Invoice } from "../../../stores/session";

const session = useSessionStore();
const showForm = ref(false);
type DraftLineItem = { description: string; amount: string };
const emptyForm = () => ({ recipient_name: "", student_id: null as number | null, line_items: [{ description: "", amount: "" }] as DraftLineItem[] });
const form = ref(emptyForm());
const editingId = ref<number | null>(null);
const invoiceTotal = computed(() => form.value.line_items.reduce((total, item) => total + Math.round(parseFloat(item.amount || "0") * 100), 0));
const showStructureForm = ref(false);
const structureForm = ref({ name: "", amount: "" });
const selectedStructureId = ref<number | null>(null);
const selectedStudentIds = ref<number[]>([]);
const editingStructureId = ref<number | null>(null);

onMounted(async () => { await session.loadFees(); await session.loadStudentOptions(); });

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { minimumFractionDigits: 0 })}`;

function statusTone(s: string) {
  return s === "paid" ? "success" : s === "partial" ? "warning" : s === "void" ? "neutral" : "danger";
}

async function submit() {
  const line_items = form.value.line_items.filter((item) => item.description.trim()).map((item) => ({ description: item.description.trim(), amount_cents: Math.round(parseFloat(item.amount || "0") * 100) }));
  const amount_cents = invoiceTotal.value;
  const saved = editingId.value
    ? await session.updateInvoice(editingId.value, { recipient_name: form.value.recipient_name, student_id: form.value.student_id || undefined, amount_cents, line_items })
    : await session.createInvoice({ recipient_name: form.value.recipient_name, student_id: form.value.student_id || undefined, amount_cents, line_items });
  if (saved) {
    form.value = emptyForm();
    editingId.value = null;
    showForm.value = false;
  }
}
function edit(inv: Invoice) { editingId.value = inv.id; form.value = { recipient_name: inv.recipient_name, student_id: inv.student_id, line_items: inv.line_items.length ? inv.line_items.map((item) => ({ description: item.description, amount: String(item.amount_cents / 100) })) : [{ description: inv.description || "Invoice", amount: String(inv.amount_cents / 100) }] }; showForm.value = true; }
function selectStudent() { const student = session.studentOptions.find((item) => item.id === form.value.student_id); if (student) form.value.recipient_name = student.name; }
function addLineItem() { form.value.line_items.push({ description: "", amount: "" }); }
function removeLineItem(index: number) { if (form.value.line_items.length > 1) form.value.line_items.splice(index, 1); }
async function createStructure() { const payload = { name: structureForm.value.name, amount_cents: Math.round(parseFloat(structureForm.value.amount || "0") * 100) }; const saved = editingStructureId.value ? await session.updateFeeStructure(editingStructureId.value, payload) : await session.createFeeStructure(payload); if (saved) { structureForm.value = { name: "", amount: "" }; editingStructureId.value = null; showStructureForm.value = false; } }
async function applyStructure() { if (selectedStructureId.value && selectedStudentIds.value.length) await session.applyFeeStructure(selectedStructureId.value, selectedStudentIds.value); }
function editStructure(structure: { id: number; name: string; amount_cents: number }) { editingStructureId.value = structure.id; structureForm.value = { name: structure.name, amount: String(structure.amount_cents / 100) }; showStructureForm.value = true; }
async function deleteStructure(structure: { id: number; name: string }) { if (window.confirm(`Delete ${structure.name}? Existing invoices will be kept.`)) await session.deleteFeeStructure(structure.id); }

async function collect(inv: Invoice) {
  const remaining = inv.amount_cents - inv.paid_cents;
  const raw = window.prompt(`Record a payment for ${inv.recipient_name} (remaining ₹${(remaining / 100).toFixed(0)}):`, (remaining / 100).toFixed(0));
  if (raw == null) return;
  const cents = Math.round(parseFloat(raw) * 100);
  if (cents > 0) await session.recordPayment(inv.id, cents, "manual");
}
</script>

<template>
  <div class="space-y-8">
    <SPageHeader eyebrow="Fees & accounting" title="Invoices" subtitle="Bill students, record payments, and track dues.">
      <template #actions>
        <a href="/api/fees/export.csv" class="text-sm font-semibold text-primary-700 hover:underline">Export CSV</a>
        <SButton variant="primary" @click="showForm = !showForm">{{ showForm ? "Close" : "New invoice" }}</SButton>
      </template>
    </SPageHeader>

    <div v-if="session.feesSummary" class="grid gap-4 sm:grid-cols-4">
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Billed</p><p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ money(session.feesSummary.billed_cents) }}</p></div>
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Collected</p><p class="mt-1 font-display text-2xl font-semibold text-success">{{ money(session.feesSummary.collected_cents) }}</p></div>
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Outstanding</p><p class="mt-1 font-display text-2xl font-semibold text-accent-600">{{ money(session.feesSummary.outstanding_cents) }}</p></div>
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Invoices</p><p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ session.feesSummary.invoice_count }}</p></div>
    </div>

    <section class="rounded-lg border border-hairline bg-surface p-5">
      <div class="flex items-center justify-between"><div><p class="s-eyebrow">Fee structures</p><p class="mt-1 text-sm text-ink-500">Apply a standard charge to selected students.</p></div><SButton variant="secondary" @click="showStructureForm = !showStructureForm">{{ showStructureForm ? "Close" : "New structure" }}</SButton></div>
      <form v-if="showStructureForm" class="mt-4 flex flex-wrap items-end gap-3" @submit.prevent="createStructure"><label class="flex-1 text-sm">Name<input v-model="structureForm.name" class="s-input mt-1" required /></label><label class="text-sm">Amount (₹)<input v-model="structureForm.amount" type="number" min="0" class="s-input mt-1" required /></label><SButton type="submit" variant="primary">{{ editingStructureId ? "Save changes" : "Save structure" }}</SButton></form>
      <div v-if="session.feeStructures.length" class="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto]"><label class="text-sm">Structure<select v-model="selectedStructureId" class="s-input mt-1"><option :value="null">Choose structure</option><option v-for="structure in session.feeStructures" :key="structure.id" :value="structure.id">{{ structure.name }} · {{ money(structure.amount_cents) }}</option></select></label><fieldset class="text-sm"><legend>Students</legend><div class="mt-1 flex max-h-28 flex-wrap gap-x-4 overflow-auto rounded-md border border-hairline p-2"><label v-for="student in session.studentOptions" :key="student.id" class="flex items-center gap-2"><input v-model="selectedStudentIds" type="checkbox" :value="student.id" />{{ student.name }}</label></div></fieldset><SButton class="self-end" variant="primary" :disabled="!selectedStructureId || !selectedStudentIds.length || session.loading === 'apply-fee-structure'" @click="applyStructure">Apply</SButton></div>
      <p v-else class="mt-4 text-sm text-ink-500">Create a structure to bill the same fee to several students.</p>
      <ul v-if="session.feeStructures.length" class="mt-4 divide-y divide-hairline border-t border-hairline"><li v-for="structure in session.feeStructures" :key="structure.id" class="flex items-center justify-between py-2 text-sm"><span>{{ structure.name }} <span class="text-ink-500">{{ money(structure.amount_cents) }}</span></span><span class="flex gap-1"><SButton variant="ghost" @click="editStructure(structure)">Edit</SButton><SButton variant="ghost" @click="deleteStructure(structure)">Delete</SButton></span></li></ul>
    </section>

    <form v-if="showForm" class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-4" @submit.prevent="submit">
      <label class="text-sm">Bill to<input v-model="form.recipient_name" class="s-input mt-1" required /></label>
      <label class="text-sm">Student<select v-model="form.student_id" class="s-input mt-1" @change="selectStudent"><option :value="null">External payer</option><option v-for="student in session.studentOptions" :key="student.id" :value="student.id">{{ student.name }}</option></select></label>
      <div class="sm:col-span-2"><p class="text-sm">Invoice lines</p><div v-for="(item, index) in form.line_items" :key="index" class="mt-1 flex gap-2"><input v-model="item.description" class="s-input flex-1" placeholder="Description" required /><input v-model="item.amount" type="number" min="0" step="1" class="s-input w-28" placeholder="₹" required /><SButton type="button" variant="ghost" :disabled="form.line_items.length === 1" @click="removeLineItem(index)">Remove</SButton></div><div class="mt-2 flex items-center justify-between"><SButton type="button" variant="secondary" @click="addLineItem">Add line</SButton><span class="text-sm font-semibold text-ink-900">Total {{ money(invoiceTotal) }}</span></div></div>
      <div class="sm:col-span-4"><SButton type="submit" variant="primary" :disabled="!form.recipient_name.trim() || session.loading === 'create-invoice'">{{ editingId ? "Save invoice" : "Create invoice" }}</SButton></div>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <SLoadingState v-if="session.loading === 'fees' && !session.invoices.length" :rows="3" />
    <div v-else-if="session.invoices.length" class="overflow-hidden rounded-lg border border-hairline bg-surface">
      <table class="w-full text-sm">
        <thead class="bg-surface-sunken text-left text-xs uppercase tracking-wide text-ink-500">
          <tr><th class="px-4 py-3">Bill to</th><th class="px-4 py-3">Amount</th><th class="px-4 py-3">Paid</th><th class="px-4 py-3">Status</th><th class="px-4 py-3"></th></tr>
        </thead>
        <tbody class="divide-y divide-hairline">
          <tr v-for="inv in session.invoices" :key="inv.id">
            <td class="px-4 py-3">
              <p class="font-medium text-ink-900">{{ inv.recipient_name }}</p>
              <p v-if="inv.description" class="text-xs text-ink-500">{{ inv.description }}</p>
            </td>
            <td class="px-4 py-3 text-ink-700">{{ money(inv.amount_cents) }}</td>
            <td class="px-4 py-3 text-ink-700">{{ money(inv.paid_cents) }}</td>
            <td class="px-4 py-3"><SBadge :tone="statusTone(inv.status)">{{ inv.status }}</SBadge></td>
            <td class="px-4 py-3 text-right">
              <template v-if="!inv.voided && inv.status !== 'paid'">
                <SButton v-if="inv.status === 'unpaid'" variant="ghost" @click="edit(inv)">Edit</SButton>
                <SButton variant="secondary" :disabled="session.loading === `invoice-${inv.id}`" @click="collect(inv)">Record payment</SButton>
                <a :href="`/api/fees/invoices/${inv.id}/print`" target="_blank" class="text-xs font-semibold text-primary-700 hover:underline">Print</a>
                <SButton variant="ghost" :disabled="session.loading === `invoice-${inv.id}`" @click="session.voidInvoice(inv.id)">Void</SButton>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="text-sm text-ink-500">No invoices yet.</p>
  </div>
</template>
