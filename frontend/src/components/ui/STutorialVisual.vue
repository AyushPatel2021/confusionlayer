<script setup lang="ts">
import Chart from "chart.js/auto";
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

const props = defineProps<{ visual?: string }>();

const canvas = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

type Series = { label: string; values: number[] };
type ParsedChart = { xLabel: string; labels: string[]; series: Series[] };

const cleanVisual = computed(() => (props.visual || "").trim());
const parsed = computed(() => parseVisualTable(cleanVisual.value));

watch(parsed, () => void renderChart(), { immediate: true });
onBeforeUnmount(() => chart?.destroy());

async function renderChart() {
  await nextTick();
  chart?.destroy();
  chart = null;
  if (!canvas.value || !parsed.value) return;
  chart = new Chart(canvas.value, {
    type: "line",
    data: {
      labels: parsed.value.labels,
      datasets: parsed.value.series.map((item, index) => ({
        label: item.label,
        data: item.values,
        borderColor: ["#0F6E6E", "#C65B38", "#B98222", "#334155"][index % 4],
        backgroundColor: "transparent",
        tension: 0.3,
        pointRadius: 4,
        borderWidth: 2,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { ticks: { precision: 2 } },
      },
      plugins: {
        legend: { position: "bottom", labels: { boxWidth: 10, boxHeight: 10 } },
        tooltip: { intersect: false, mode: "index" },
      },
    },
  });
}

function parseVisualTable(text: string): ParsedChart | null {
  const rows = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseRow)
    .filter((row): row is { label: string; cells: string[] } => !!row && row.cells.length >= 3);

  if (rows.length < 2) return null;
  const xRow = rows.find((row) => row.cells.some((cell) => Number.isFinite(toNumber(cell))));
  if (!xRow) return null;
  const labels = xRow.cells.map(stripOuterPunctuation);
  if (labels.length < 3) return null;

  const series = rows
    .filter((row) => row !== xRow)
    .map((row) => ({ label: row.label, values: row.cells.map(toNumber) }))
    .filter((row): row is Series => row.values.length === labels.length && row.values.every((value) => Number.isFinite(value)));

  if (!series.length) return null;
  return { xLabel: xRow.label, labels, series };
}

function parseRow(line: string): { label: string; cells: string[] } | null {
  const colonMatch = line.match(/^([^:|]+)[:|]\s*(.+)$/);
  if (colonMatch) return { label: colonMatch[1].trim(), cells: splitCells(colonMatch[2]) };
  const parts = line.split(/\s{2,}|\t+/).map((part) => part.trim()).filter(Boolean);
  if (parts.length >= 4) return { label: parts[0], cells: parts.slice(1) };
  return null;
}

function splitCells(value: string): string[] {
  return value.split(/\s{2,}|\s+\|\s+|\t+|\s+/).map((part) => part.trim()).filter(Boolean);
}

function stripOuterPunctuation(value: string): string {
  return value.replace(/^[,;]+|[,;]+$/g, "");
}

function toNumber(value: string): number {
  const cleaned = stripOuterPunctuation(value)
    .replace(/deg\b/gi, "")
    .replace(/[^\d.+\-eE]/g, "");
  if (!cleaned || cleaned === "." || cleaned === "-" || cleaned === "+") return Number.NaN;
  return Number(cleaned);
}
</script>

<template>
  <div v-if="cleanVisual" class="rounded-lg border border-hairline bg-surface p-5">
    <p class="s-eyebrow">Visual lab</p>
    <div v-if="parsed" class="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)]">
      <div class="rounded-md border border-hairline bg-paper p-4">
        <p class="text-sm font-semibold text-ink-900">Relationship chart</p>
        <p class="mt-1 text-xs text-ink-500">Generated from the tutorial's visual table.</p>
        <div class="mt-3 h-72"><canvas ref="canvas" /></div>
      </div>
      <div class="rounded-md border border-hairline bg-ink-900 p-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-paper/70">Source visual</p>
        <pre class="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-5 text-paper">{{ cleanVisual }}</pre>
      </div>
    </div>
    <div v-else class="mt-4 rounded-md border border-hairline bg-ink-900 p-5">
      <pre class="overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-5 text-paper">{{ cleanVisual }}</pre>
    </div>
  </div>
</template>
