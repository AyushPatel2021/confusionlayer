<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SCombobox from "../../../components/ui/SCombobox.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import SConfirmDialog from "../../../components/ui/SConfirmDialog.vue";
import SDialog from "../../../components/ui/SDialog.vue";
import SMultiSelect from "../../../components/ui/SMultiSelect.vue";
import SStatCard from "../../../components/ui/SStatCard.vue";
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
const structureToDelete = ref<{ id: number; name: string } | null>(null);
const ledgerOpen = ref(false);
const paymentTarget = ref<Invoice | null>(null);
const paymentAmount = ref("");
const studentSelectOptions = computed(() => session.studentOptions.map((student) => ({ label: student.name, value: student.id })));
const structureOptions = computed(() => session.feeStructures.map((structure) => ({ label: structure.name, value: structure.id, hint: money(structure.amount_cents) })));
const openInvoices = computed(() => session.invoices.filter((invoice) => !invoice.voided && invoice.status !== "paid"));
const invoiceGroups = computed(() => [
  { label: "Needs collection", invoices: openInvoices.value },
  { label: "Settled", invoices: session.invoices.filter((invoice) => invoice.status === "paid") },
  { label: "Voided", invoices: session.invoices.filter((invoice) => invoice.voided) },
].filter((group) => group.invoices.length));
const collectionFocus = computed(() => [...openInvoices.value].sort((a, b) => remaining(b) - remaining(a)).slice(0, 5));
const multiselectStudents = computed({
  get: () => selectedStudentIds.value,
  set: (value: Array<number | string>) => {
    selectedStudentIds.value = value.map(Number).filter(Boolean);
  },
});

onMounted(async () => { await session.loadFees(); await session.loadStudentOptions(); });

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { minimumFractionDigits: 0 })}`;

function statusTone(s: string) {
  return s === "paid" ? "success" : s === "partial" ? "warning" : s === "void" ? "neutral" : "danger";
}

function remaining(inv: Invoice) {
  return Math.max(0, inv.amount_cents - inv.paid_cents);
}

function invoiceDate(inv: Invoice) {
  return new Date(inv.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
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
async function deleteStructure() { if (structureToDelete.value && await session.deleteFeeStructure(structureToDelete.value.id)) structureToDelete.value = null; }
async function openLedger(studentId: number | null) { if (studentId) { await session.loadFeeLedger(studentId); ledgerOpen.value = true; } }

function collect(inv: Invoice) {
  const remaining = inv.amount_cents - inv.paid_cents;
  paymentTarget.value = inv;
  paymentAmount.value = String(remaining / 100);
}
async function recordPayment() {
  if (!paymentTarget.value) return;
  const cents = Math.round(parseFloat(paymentAmount.value || "0") * 100);
  if (cents > 0 && await session.recordPayment(paymentTarget.value.id, cents, "manual")) paymentTarget.value = null;
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
      <SStatCard label="Billed" :value="money(session.feesSummary.billed_cents)" />
      <SStatCard label="Collected" :value="money(session.feesSummary.collected_cents)" tone="success" />
      <SStatCard label="Outstanding" :value="money(session.feesSummary.outstanding_cents)" tone="warning" />
      <SStatCard label="Invoices" :value="session.feesSummary.invoice_count" />
    </div>

    <section class="rounded-lg border border-hairline bg-surface p-5">
      <div class="flex items-center justify-between"><div><p class="s-eyebrow">Fee structures</p><p class="mt-1 text-sm text-ink-500">Apply a standard charge to selected students.</p></div><SButton variant="secondary" @click="showStructureForm = !showStructureForm">{{ showStructureForm ? "Close" : "New structure" }}</SButton></div>
      <form v-if="showStructureForm" class="mt-4 flex flex-wrap items-end gap-3" @submit.prevent="createStructure"><label class="flex-1 text-sm">Name<input v-model="structureForm.name" class="s-input mt-1" required /></label><label class="text-sm">Amount (₹)<input v-model="structureForm.amount" type="number" min="0" class="s-input mt-1" required /></label><SButton type="submit" variant="primary">{{ editingStructureId ? "Save changes" : "Save structure" }}</SButton></form>
      <div v-if="session.feeStructures.length" class="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto]"><SCombobox v-model="selectedStructureId" label="Structure" placeholder="Choose structure" :options="structureOptions" /><SMultiSelect v-model="multiselectStudents" label="Students" :options="studentSelectOptions" max-height="max-h-28" /><SButton class="self-end" variant="primary" :disabled="!selectedStructureId || !selectedStudentIds.length || session.loading === 'apply-fee-structure'" @click="applyStructure">Apply</SButton></div>
      <p v-else class="mt-4 text-sm text-ink-500">Create a structure to bill the same fee to several students.</p>
      <ul v-if="session.feeStructures.length" class="mt-4 divide-y divide-hairline border-t border-hairline"><li v-for="structure in session.feeStructures" :key="structure.id" class="flex items-center justify-between py-2 text-sm"><span>{{ structure.name }} <span class="text-ink-500">{{ money(structure.amount_cents) }}</span></span><span class="flex gap-1"><SButton variant="ghost" @click="editStructure(structure)">Edit</SButton><SButton variant="ghost" @click="structureToDelete = structure">Delete</SButton></span></li></ul>
    </section>

    <form v-if="showForm" class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-4" @submit.prevent="submit">
      <label class="text-sm">Bill to<input v-model="form.recipient_name" class="s-input mt-1" required /></label>
      <SCombobox v-model="form.student_id" label="Student" placeholder="External payer" :options="studentSelectOptions" @change="selectStudent" />
      <div class="sm:col-span-2"><p class="text-sm">Invoice lines</p><div v-for="(item, index) in form.line_items" :key="index" class="mt-1 flex gap-2"><input v-model="item.description" class="s-input flex-1" placeholder="Description" required /><input v-model="item.amount" type="number" min="0" step="1" class="s-input w-28" placeholder="₹" required /><SButton type="button" variant="ghost" :disabled="form.line_items.length === 1" @click="removeLineItem(index)">Remove</SButton></div><div class="mt-2 flex items-center justify-between"><SButton type="button" variant="secondary" @click="addLineItem">Add line</SButton><span class="text-sm font-semibold text-ink-900">Total {{ money(invoiceTotal) }}</span></div></div>
      <div class="sm:col-span-4"><SButton type="submit" variant="primary" :disabled="!form.recipient_name.trim() || session.loading === 'create-invoice'">{{ editingId ? "Save invoice" : "Create invoice" }}</SButton></div>
    </form>
    <p v-if="session.error" class="text-sm text-danger">{{ session.error }}</p>

    <SLoadingState v-if="session.loading === 'fees' && !session.invoices.length" :rows="3" />
    <div v-else-if="session.invoices.length" class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
      <section class="space-y-5">
        <div v-for="group in invoiceGroups" :key="group.label" class="space-y-3">
          <div class="flex items-center justify-between">
            <p class="s-eyebrow">{{ group.label }}</p>
            <p class="text-xs text-ink-500">{{ group.invoices.length }} invoice{{ group.invoices.length === 1 ? "" : "s" }}</p>
          </div>
          <article v-for="inv in group.invoices" :key="inv.id" class="rounded-lg border border-hairline bg-surface p-4">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <button v-if="inv.student_id" type="button" class="text-left font-semibold text-ink-900 hover:text-primary-700 hover:underline" @click="openLedger(inv.student_id)">{{ inv.recipient_name }}</button>
                <p v-else class="font-semibold text-ink-900">{{ inv.recipient_name }}</p>
                <p class="mt-1 text-xs text-ink-500">Invoice #{{ inv.id }} | {{ invoiceDate(inv) }}</p>
              </div>
              <SBadge :tone="statusTone(inv.status)">{{ inv.status }}</SBadge>
            </div>

            <div class="mt-4 grid gap-3 sm:grid-cols-3">
              <div class="rounded-md bg-surface-sunken px-3 py-2">
                <p class="text-xs text-ink-500">Billed</p>
                <p class="font-display text-xl font-semibold text-ink-900">{{ money(inv.amount_cents) }}</p>
              </div>
              <div class="rounded-md bg-surface-sunken px-3 py-2">
                <p class="text-xs text-ink-500">Collected</p>
                <p class="font-display text-xl font-semibold text-success">{{ money(inv.paid_cents) }}</p>
              </div>
              <div class="rounded-md bg-surface-sunken px-3 py-2">
                <p class="text-xs text-ink-500">Due</p>
                <p class="font-display text-xl font-semibold" :class="remaining(inv) ? 'text-accent-600' : 'text-ink-900'">{{ money(remaining(inv)) }}</p>
              </div>
            </div>

            <ul v-if="inv.line_items.length" class="mt-4 divide-y divide-hairline rounded-md border border-hairline">
              <li v-for="item in inv.line_items" :key="item.id" class="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                <span class="text-ink-700">{{ item.description }}</span>
                <span class="font-medium text-ink-900">{{ money(item.amount_cents) }}</span>
              </li>
            </ul>
            <p v-else-if="inv.description" class="mt-3 text-sm text-ink-500">{{ inv.description }}</p>

            <div class="mt-4 flex flex-wrap items-center justify-end gap-2">
              <template v-if="!inv.voided && inv.status !== 'paid'">
                <SButton v-if="inv.status === 'unpaid'" variant="ghost" @click="edit(inv)">Edit</SButton>
                <SButton variant="secondary" :disabled="session.loading === `invoice-${inv.id}`" @click="collect(inv)">Record payment</SButton>
                <a :href="`/api/fees/invoices/${inv.id}/print`" target="_blank" class="rounded-md px-3 py-2 text-xs font-semibold text-primary-700 hover:bg-primary-50">Print</a>
                <SButton variant="ghost" :disabled="session.loading === `invoice-${inv.id}`" @click="session.voidInvoice(inv.id)">Void</SButton>
              </template>
            </div>
          </article>
        </div>
      </section>

      <aside class="h-fit rounded-lg border border-hairline bg-surface p-5">
        <p class="s-eyebrow">Collection focus</p>
        <h2 class="mt-2 font-display text-xl font-semibold text-ink-900">{{ money(session.feesSummary?.outstanding_cents || 0) }}</h2>
        <p class="mt-1 text-sm text-ink-500">Open balance across active invoices.</p>
        <div v-if="collectionFocus.length" class="mt-4 space-y-3">
          <button v-for="inv in collectionFocus" :key="inv.id" type="button" class="w-full rounded-md border border-hairline px-3 py-2 text-left hover:border-primary-200 hover:bg-primary-50" @click="openLedger(inv.student_id)">
            <span class="block text-sm font-semibold text-ink-900">{{ inv.recipient_name }}</span>
            <span class="mt-1 flex items-center justify-between text-xs text-ink-500"><span>#{{ inv.id }}</span><span class="font-semibold text-accent-600">{{ money(remaining(inv)) }}</span></span>
          </button>
        </div>
        <p v-else class="mt-4 text-sm text-ink-500">No open invoices need follow-up.</p>
      </aside>
    </div>
    <p v-else class="text-sm text-ink-500">No invoices yet.</p>
    <section v-if="ledgerOpen && session.feeLedger" class="rounded-lg border border-hairline bg-surface p-5"><div class="flex items-start justify-between gap-4"><div><p class="s-eyebrow">Learner ledger</p><h2 class="mt-1 font-display text-xl font-semibold text-ink-900">{{ session.feeLedger.student_name }}</h2><p class="mt-1 text-sm text-ink-500">Outstanding {{ money(session.feeLedger.outstanding_cents) }}</p></div><SButton variant="ghost" @click="ledgerOpen = false">Close</SButton></div><div class="mt-4 overflow-auto"><table class="w-full text-sm"><thead class="text-left text-xs uppercase text-ink-500"><tr><th class="pb-2">Date</th><th class="pb-2">Reference</th><th class="pb-2">Debit</th><th class="pb-2">Credit</th><th class="pb-2">Balance</th></tr></thead><tbody class="divide-y divide-hairline"><tr v-for="entry in session.feeLedger.entries" :key="`${entry.reference}-${entry.occurred_at}`"><td class="py-2 text-ink-500">{{ new Date(entry.occurred_at).toLocaleDateString() }}</td><td class="py-2"><a v-if="entry.kind === 'payment'" :href="`/api/fees/payments/${entry.reference.replace('Receipt #', '')}/receipt`" target="_blank" class="font-medium text-primary-700 hover:underline">{{ entry.reference }}</a><span v-else>{{ entry.reference }}</span><span v-if="entry.description" class="ml-2 text-ink-500">{{ entry.description }}</span></td><td class="py-2">{{ entry.debit_cents ? money(entry.debit_cents) : ' ' }}</td><td class="py-2">{{ entry.credit_cents ? money(entry.credit_cents) : ' ' }}</td><td class="py-2 font-medium">{{ money(entry.balance_cents) }}</td></tr></tbody></table></div></section>
    <SDialog :open="!!paymentTarget" title="Record payment" :description="paymentTarget ? `Remaining ${money(paymentTarget.amount_cents - paymentTarget.paid_cents)} for ${paymentTarget.recipient_name}.` : ''" size="sm" @close="paymentTarget = null">
      <form class="space-y-4" @submit.prevent="recordPayment">
        <label class="text-sm">Amount (₹)<input v-model="paymentAmount" type="number" min="1" step="1" class="s-input mt-1" required /></label>
        <div class="flex justify-end gap-2">
          <SButton variant="ghost" @click="paymentTarget = null">Cancel</SButton>
          <SButton type="submit" variant="primary" :disabled="!paymentAmount || (paymentTarget ? session.loading === `invoice-${paymentTarget.id}` : false)">Record</SButton>
        </div>
      </form>
    </SDialog>
    <SConfirmDialog :open="!!structureToDelete" title="Delete fee structure" :message="`Delete ${structureToDelete?.name || 'this structure'}? Existing invoices will be retained.`" confirm-label="Delete" :busy="session.loading === 'fees'" @cancel="structureToDelete = null" @confirm="deleteStructure" />
  </div>
</template>
