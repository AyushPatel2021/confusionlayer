<script setup lang="ts">
import { onMounted, ref } from "vue";

import SBadge from "../../../components/ui/SBadge.vue";
import SButton from "../../../components/ui/SButton.vue";
import SLoadingState from "../../../components/ui/SLoadingState.vue";
import SPageHeader from "../../../components/ui/SPageHeader.vue";
import { useSessionStore, type Invoice } from "../../../stores/session";

const session = useSessionStore();
const showForm = ref(false);
const form = ref({ recipient_name: "", amount: "", description: "" });

onMounted(() => session.loadFees());

const money = (cents: number) => `₹${(cents / 100).toLocaleString("en-IN", { minimumFractionDigits: 0 })}`;

function statusTone(s: string) {
  return s === "paid" ? "success" : s === "partial" ? "warning" : s === "void" ? "neutral" : "danger";
}

async function submit() {
  const amount_cents = Math.round(parseFloat(form.value.amount || "0") * 100);
  if (await session.createInvoice({ recipient_name: form.value.recipient_name, amount_cents, description: form.value.description || undefined })) {
    form.value = { recipient_name: "", amount: "", description: "" };
    showForm.value = false;
  }
}

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
        <SButton variant="primary" @click="showForm = !showForm">{{ showForm ? "Close" : "New invoice" }}</SButton>
      </template>
    </SPageHeader>

    <div v-if="session.feesSummary" class="grid gap-4 sm:grid-cols-4">
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Billed</p><p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ money(session.feesSummary.billed_cents) }}</p></div>
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Collected</p><p class="mt-1 font-display text-2xl font-semibold text-success">{{ money(session.feesSummary.collected_cents) }}</p></div>
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Outstanding</p><p class="mt-1 font-display text-2xl font-semibold text-accent-600">{{ money(session.feesSummary.outstanding_cents) }}</p></div>
      <div class="rounded-md border border-hairline bg-surface p-4"><p class="text-xs text-ink-500">Invoices</p><p class="mt-1 font-display text-2xl font-semibold text-ink-900">{{ session.feesSummary.invoice_count }}</p></div>
    </div>

    <form v-if="showForm" class="grid gap-3 rounded-lg border border-hairline bg-surface p-5 sm:grid-cols-3" @submit.prevent="submit">
      <label class="text-sm">Bill to<input v-model="form.recipient_name" class="s-input mt-1" required /></label>
      <label class="text-sm">Amount (₹)<input v-model="form.amount" type="number" min="0" step="1" class="s-input mt-1" required /></label>
      <label class="text-sm">Description<input v-model="form.description" class="s-input mt-1" /></label>
      <div class="sm:col-span-3"><SButton type="submit" variant="primary" :disabled="!form.recipient_name.trim() || session.loading === 'create-invoice'">Create invoice</SButton></div>
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
                <SButton variant="secondary" :disabled="session.loading === `invoice-${inv.id}`" @click="collect(inv)">Record payment</SButton>
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
