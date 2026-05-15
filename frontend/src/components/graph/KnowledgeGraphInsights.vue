<template>
  <div class="clm-brief flex h-full min-h-0 flex-col bg-[var(--clm-bg-page)]">

    <!-- ── Loading ─────────────────────────────────────────── -->
    <div v-if="loading" class="flex flex-1 flex-col items-center justify-center gap-4">
      <div class="relative h-14 w-14">
        <svg class="clm-brief-spin absolute inset-0 h-14 w-14" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="23" fill="none" stroke="currentColor"
            class="text-[var(--clm-border)]" stroke-width="4"/>
          <circle cx="28" cy="28" r="23" fill="none" stroke="currentColor"
            class="text-[var(--clm-brand)]" stroke-width="4"
            stroke-dasharray="30 115" stroke-linecap="round"
            transform="rotate(-90 28 28)"/>
        </svg>
        <div class="absolute inset-0 flex items-center justify-center">
          <span class="text-[9px] font-black text-[var(--clm-brand)]">CLM</span>
        </div>
      </div>
      <p class="text-[13px] text-[var(--clm-text-muted)]">Building visualizations…</p>
    </div>

    <!-- ── Not found ───────────────────────────────────────── -->
    <div v-else-if="errorKind === 'not_found'"
      class="flex flex-1 flex-col items-center justify-center gap-5 px-6 py-10">
      <div class="flex h-14 w-14 items-center justify-center rounded-2xl border-2 border-dashed border-[var(--clm-border)]">
        <svg class="h-6 w-6 text-[var(--clm-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
      </div>
      <div class="max-w-xs text-center">
        <p class="font-semibold text-[var(--clm-text)]">No graph built yet</p>
        <p class="mt-1.5 text-[13px] leading-relaxed text-[var(--clm-text-muted)]">
          Press <strong class="font-semibold text-[var(--clm-text)]">Build knowledge graph</strong> to unlock all three views below.
        </p>
      </div>
    </div>

    <!-- ── Error ────────────────────────────────────────────── -->
    <div v-else-if="errorKind === 'failed'" class="flex flex-1 items-center justify-center px-6">
      <p class="text-center text-[13px] text-red-500 dark:text-red-400">{{ errorMessage }}</p>
    </div>

    <!-- ── Main ─────────────────────────────────────────────── -->
    <div v-else class="clm-brief-scroll min-h-0 flex-1 overflow-y-auto">

      <template v-if="!model.hasData">
        <p class="p-6 text-center text-[13px] text-[var(--clm-text-muted)]">No entities found. Try rebuilding the knowledge graph.</p>
      </template>

      <template v-else>

        <!-- ─ Shared KPI banner ─────────────────────────────── -->
        <div class="flex items-stretch divide-x divide-[var(--clm-border)] border-b border-[var(--clm-border)] bg-[var(--clm-bg-surface)]">
          <div v-for="kpi in kpis" :key="kpi.label"
            class="flex flex-1 flex-col items-center justify-center px-3 py-4 text-center">
            <span class="text-[26px] font-black tabular-nums leading-none text-[var(--clm-text)]">{{ kpi.value }}</span>
            <span class="mt-1.5 text-[10px] font-semibold uppercase tracking-widest text-[var(--clm-text-muted)]">{{ kpi.label }}</span>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════ -->
        <!-- SECTION 01 · Intelligence Report                   -->
        <!-- ══════════════════════════════════════════════════ -->
        <div class="clm-section-head">
          <span class="clm-section-num">01</span>
          <span class="clm-section-title">Intelligence Report</span>
          <span class="clm-section-hint">Proportional breakdown by entity type</span>
        </div>

        <div class="flex flex-col gap-6 px-4 py-5 sm:flex-row sm:items-start sm:gap-8 sm:px-6">
          <!-- Animated donut -->
          <div class="mx-auto shrink-0 sm:mx-0">
            <svg width="164" height="164" viewBox="0 0 164 164"
              role="img" aria-label="Entity type donut chart">
              <circle cx="82" cy="82" r="55" fill="none" stroke="currentColor"
                class="text-[var(--clm-bg-overlay)]" stroke-width="22"/>
              <g transform="rotate(-90 82 82)">
                <circle
                  v-for="seg in donutSegments" :key="'ds-' + seg.type"
                  cx="82" cy="82" r="55" fill="none"
                  :stroke="seg.color" stroke-width="22"
                  :stroke-dasharray="`${seg.dash} ${seg.C}`"
                  :stroke-dashoffset="seg.dashoffset"
                  stroke-linecap="butt"/>
              </g>
              <text x="82" y="76" text-anchor="middle" fill="currentColor"
                class="text-slate-900 dark:text-slate-100"
                style="font-size:27px;font-weight:900;font-family:inherit">
                {{ model.stats.nodeCount }}
              </text>
              <text x="82" y="94" text-anchor="middle" fill="currentColor"
                class="text-slate-400"
                style="font-size:11px;font-family:inherit">entities</text>
            </svg>
          </div>

          <!-- Type legend -->
          <ul class="min-w-0 flex-1 space-y-2.5">
            <li v-for="seg in donutSegments" :key="'dl-' + seg.type"
              class="flex min-w-0 items-center gap-2.5">
              <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: seg.color }"/>
              <span class="min-w-0 flex-1 truncate text-[13px] font-medium text-[var(--clm-text)]">{{ seg.type }}</span>
              <span class="shrink-0 tabular-nums text-[12px] text-[var(--clm-text-muted)]">{{ seg.count }}</span>
              <span class="w-9 shrink-0 text-right tabular-nums text-[11px] text-[var(--clm-text-muted)]">{{ seg.pct }}%</span>
            </li>
          </ul>
        </div>

        <!-- Entity card deck -->
        <div class="border-t border-[var(--clm-border)] px-4 pb-5 pt-4 sm:px-6">
          <p class="mb-3 text-[10px] font-bold uppercase tracking-widest text-[var(--clm-text-muted)]">Most important facts</p>
          <div class="clm-deck flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2">
            <div
              v-for="(ent, ei) in model.topEntities" :key="'ec-' + ent.id"
              class="snap-start shrink-0 w-[148px] overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm">
              <div class="h-[3px]" :style="{ background: ent.color }"/>
              <div class="p-3">
                <div class="mb-2 flex items-center justify-between gap-1">
                  <span class="text-[9px] font-black tabular-nums text-[var(--clm-text-muted)] opacity-50">#{{ ei + 1 }}</span>
                  <span class="rounded-full px-2 py-0.5 text-[9px] font-bold"
                    :style="{ background: ent.color + '22', color: ent.color }">{{ ent.type }}</span>
                </div>
                <p class="line-clamp-2 text-[12px] font-semibold leading-snug text-[var(--clm-text)]">{{ ent.label }}</p>
                <div class="mt-3">
                  <div class="mb-1 flex items-center justify-between">
                    <span class="text-[9px] text-[var(--clm-text-muted)]">connections</span>
                    <span class="text-[10px] font-black tabular-nums text-[var(--clm-text)]">{{ ent.connections }}</span>
                  </div>
                  <div class="h-1 overflow-hidden rounded-full bg-[var(--clm-bg-overlay)]">
                    <div class="h-1 rounded-full transition-all duration-700"
                      :style="{ width: `${Math.min(100, (ent.connections / maxConnections) * 100)}%`, background: ent.color }"/>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════ -->
        <!-- SECTION 02 · Entity Constellation                  -->
        <!-- ══════════════════════════════════════════════════ -->
        <div class="clm-section-head">
          <span class="clm-section-num">02</span>
          <span class="clm-section-title">Entity Constellation</span>
          <span class="clm-section-hint">Each dot is an entity — hover to identify it</span>
        </div>

        <div v-if="universe" class="px-3 pb-5 pt-4 sm:px-4">
          <div class="relative overflow-hidden rounded-2xl border border-[var(--clm-border)]"
            style="background:linear-gradient(150deg,#0f172a 0%,#1e1b4b 55%,#0f172a 100%)">
            <svg
              class="block h-auto w-full select-none"
              :viewBox="`0 0 ${universe.width} ${universe.height}`"
              preserveAspectRatio="xMidYMid meet"
              role="img"
              :aria-label="`Constellation of ${model.stats.nodeCount} contract entities`"
            >
              <defs>
                <radialGradient id="clm-glow-grad" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="#818cf8" stop-opacity="0.4"/>
                  <stop offset="100%" stop-color="#0f172a" stop-opacity="0"/>
                </radialGradient>
              </defs>

              <!-- orbit rings -->
              <circle
                v-for="(rr, ri) in universe.orbitRings" :key="'or-' + ri"
                :cx="universe.cx" :cy="universe.cy" :r="rr"
                fill="none" stroke="#818cf8" stroke-opacity="0.1"
                stroke-width="1" stroke-dasharray="4 12"/>

              <!-- glow halo -->
              <circle :cx="universe.cx" :cy="universe.cy" r="115" fill="url(#clm-glow-grad)"/>

              <!-- core circle -->
              <circle :cx="universe.cx" :cy="universe.cy" r="20"
                fill="#1e1b4b" stroke="#818cf8" stroke-opacity="0.55" stroke-width="1.5"/>
              <text :x="universe.cx" :y="universe.cy + 4"
                text-anchor="middle" fill="#e2e8f0" style="font-size:9px;font-weight:800;font-family:inherit">doc</text>

              <!-- edges -->
              <g fill="none">
                <path
                  v-for="(e, ei) in universe.edges" :key="'ue-' + ei"
                  :d="e.d" stroke="#818cf8" :stroke-opacity="e.opacity" stroke-width="1.1"/>
              </g>

              <!-- bodies -->
              <g>
                <circle
                  v-for="b in universe.bodies" :key="'ub-' + b.id"
                  :cx="b.x" :cy="b.y" :r="b.r"
                  :fill="b.color"
                  stroke="rgba(255,255,255,0.18)" stroke-width="0.8"
                  class="cursor-pointer"
                  @mouseenter="hoveredBody = b"
                  @mouseleave="hoveredBody = null">
                  <title>{{ b.type }}: {{ b.id }}</title>
                </circle>
              </g>
            </svg>

            <!-- tooltip -->
            <transition name="clm-fade">
              <div v-if="hoveredBody"
                class="pointer-events-none absolute bottom-3 left-3 right-3 max-w-[260px] rounded-xl border border-white/10 bg-slate-950/80 px-3 py-2 text-left backdrop-blur-sm sm:left-auto sm:right-4">
                <p class="text-[9px] font-bold uppercase tracking-wider text-indigo-300">{{ hoveredBody.type }}</p>
                <p class="mt-0.5 text-[13px] font-semibold leading-snug text-white">{{ hoveredBody.label }}</p>
              </div>
            </transition>
          </div>
          <p class="mt-2 text-center text-[11px] text-[var(--clm-text-muted)]">
            Entities are grouped by type in sectors. Bigger dots have more connections.
          </p>
        </div>

        <!-- ══════════════════════════════════════════════════ -->
        <!-- SECTION 03 · Type Breakdown + Connections          -->
        <!-- ══════════════════════════════════════════════════ -->
        <div class="clm-section-head">
          <span class="clm-section-num">03</span>
          <span class="clm-section-title">Type Breakdown</span>
          <span class="clm-section-hint">Counts per category + full connection list</span>
        </div>

        <!-- Horizontal bar chart -->
        <div class="px-4 py-5 sm:px-6">
          <div class="space-y-3">
            <div v-for="row in model.typesByCount.slice(0, 12)" :key="'tb-' + row.type" class="min-w-0">
              <div class="mb-1.5 flex items-center gap-2.5">
                <span class="h-2 w-2 shrink-0 rounded-full" :style="{ background: row.color }"/>
                <span class="min-w-0 flex-1 truncate text-[12px] font-medium text-[var(--clm-text)]">{{ row.type }}</span>
                <span class="shrink-0 tabular-nums text-[11px] text-[var(--clm-text-muted)]">{{ row.count }}</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-[var(--clm-bg-overlay)]">
                <div class="h-2 rounded-full transition-all duration-700"
                  :style="{ width: `${row.pct}%`, background: row.color }"/>
              </div>
            </div>
          </div>
        </div>

        <!-- Most connected chips -->
        <div class="border-t border-[var(--clm-border)] px-4 pb-4 pt-4 sm:px-6">
          <p class="mb-3 text-[10px] font-bold uppercase tracking-widest text-[var(--clm-text-muted)]">Most connected</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="ent in model.topEntities" :key="'chip-' + ent.id"
              class="inline-flex max-w-full items-center gap-1.5 rounded-full border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-2.5 py-1.5 text-[11px] shadow-sm">
              <span class="h-2 w-2 shrink-0 rounded-full" :style="{ background: ent.color }"/>
              <span class="min-w-0 truncate font-medium text-[var(--clm-text)]">{{ ent.label }}</span>
              <span class="shrink-0 text-[10px] text-[var(--clm-text-muted)]">{{ ent.type }}</span>
              <span class="shrink-0 rounded bg-[var(--clm-bg-overlay)] px-1.5 py-px text-[9px] font-bold tabular-nums text-[var(--clm-text-muted)]">{{ ent.connections }}</span>
            </span>
          </div>
        </div>

        <!-- Numbered connection grid — scrollable, shows every connection -->
        <div class="border-t border-[var(--clm-border)] px-4 pb-10 pt-4 sm:px-6">
          <div class="mb-3 flex items-center justify-between gap-3">
            <p class="text-[10px] font-bold uppercase tracking-widest text-[var(--clm-text-muted)]">How things connect</p>
            <span class="shrink-0 rounded-full bg-[var(--clm-brand)]/10 px-2.5 py-0.5 text-[10px] font-bold tabular-nums text-[var(--clm-brand)]">
              {{ connections.length }}
            </span>
          </div>

          <!-- Fixed-height scroller — all connections, no truncation -->
          <div class="clm-conn-scroll grid gap-2 overflow-y-auto sm:grid-cols-2"
            style="max-height: 480px">
            <div
              v-for="(c, ci) in connections" :key="'cn-' + ci"
              class="group flex items-start gap-3 rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-3.5 py-3 shadow-sm transition-colors hover:border-[var(--clm-brand)]/40 hover:bg-[var(--clm-bg-surface-elevated)]">
              <span class="mt-0.5 shrink-0 text-[10px] font-black tabular-nums text-[var(--clm-text-muted)] opacity-35 group-hover:opacity-60">
                {{ String(ci + 1).padStart(2, '0') }}
              </span>
              <p class="min-w-0 text-[13px] leading-snug text-[var(--clm-text)]">
                <span class="font-semibold">{{ c.fromLabel }}</span>
                <span class="mx-1.5 text-[12px] italic text-[var(--clm-brand)]">{{ c.relation }}</span>
                <span class="font-semibold">{{ c.toLabel }}</span>
              </p>
            </div>
          </div>

          <p v-if="connections.length === 0"
            class="py-6 text-center text-[12px] text-[var(--clm-text-muted)]">No connections found.</p>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { buildGraphInsights, buildDonutSegments } from '../../utils/graphInsights.js'
import { buildUniverseScene } from '../../utils/graphUniverseLayout.js'

defineEmits(['switch-to-map'])

const props = defineProps({
  dataUrl:   { type: String, default: '' },
  reloadKey: { type: Number, default: 0 },
})

const loading    = ref(true)
const chunks     = ref(null)
const fetchError = ref(null)
const hoveredBody = ref(null)

const errorKind    = computed(() => fetchError.value?.kind ?? null)
const errorMessage = computed(() => fetchError.value?.message || 'Something went wrong.')

const model         = computed(() => buildGraphInsights(chunks.value))
const donutSegments = computed(() => buildDonutSegments(model.value?.typesByCount || []))
const universe      = computed(() => (chunks.value && model.value?.hasData) ? buildUniverseScene(chunks.value) : null)

const kpis = computed(() => [
  { value: model.value?.stats?.nodeCount     ?? 0, label: 'Entities'   },
  { value: model.value?.stats?.linkCount     ?? 0, label: 'Relations'  },
  { value: model.value?.stats?.categoryCount ?? 0, label: 'Categories' },
])

const maxConnections = computed(() =>
  Math.max(1, ...(model.value?.topEntities?.map((e) => e.connections) || [1]))
)

const connections = computed(() => model.value?.connections || [])

async function load() {
  const url = (props.dataUrl || '').trim()
  hoveredBody.value = null
  if (!url) {
    loading.value    = false
    chunks.value     = null
    fetchError.value = { kind: 'not_found' }
    return
  }
  loading.value    = true
  fetchError.value = null
  chunks.value     = null
  try {
    const res = await fetch(url, { cache: 'no-store' })
    if (res.status === 404) { fetchError.value = { kind: 'not_found' };                                          return }
    if (!res.ok)            { fetchError.value = { kind: 'failed', message: `HTTP ${res.status}` };              return }
    const data = await res.json()
    if (!Array.isArray(data)) { fetchError.value = { kind: 'failed', message: 'Unexpected response format.' };   return }
    chunks.value = data
  } catch (e) {
    fetchError.value = { kind: 'failed', message: e?.message || 'Network error' }
  } finally {
    loading.value = false
  }
}

watch(() => [props.dataUrl, props.reloadKey], () => load(), { immediate: true })
defineExpose({ reload: load })
</script>

<style scoped>
.clm-brief-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgb(148 163 184 / 0.4) transparent;
}
.dark .clm-brief-scroll {
  scrollbar-color: rgb(71 85 105 / 0.45) transparent;
}

.clm-deck {
  scrollbar-width: thin;
  scrollbar-color: rgb(148 163 184 / 0.3) transparent;
}

.clm-conn-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgb(148 163 184 / 0.5) transparent;
  padding-right: 4px;
}
.dark .clm-conn-scroll {
  scrollbar-color: rgb(71 85 105 / 0.55) transparent;
}
.clm-conn-scroll::-webkit-scrollbar       { width: 5px; }
.clm-conn-scroll::-webkit-scrollbar-track { background: transparent; }
.clm-conn-scroll::-webkit-scrollbar-thumb { border-radius: 9999px; background: rgb(148 163 184 / 0.45); }
.dark .clm-conn-scroll::-webkit-scrollbar-thumb { background: rgb(71 85 105 / 0.55); }

/* ── Section divider headers ─────────────────────────────── */
.clm-section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  border-top: 1px solid var(--clm-border);
  border-bottom: 1px solid var(--clm-border);
  background: var(--clm-bg-overlay);
}

.clm-section-num {
  font-size: 9px;
  font-weight: 900;
  letter-spacing: 0.12em;
  color: var(--clm-text-muted);
  opacity: 0.5;
  font-variant-numeric: tabular-nums;
  font-family: inherit;
  flex-shrink: 0;
}

.clm-section-title {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--clm-text);
  flex-shrink: 0;
}

.clm-section-hint {
  font-size: 11px;
  color: var(--clm-text-muted);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Spinner ─────────────────────────────────────────────── */
.clm-brief-spin {
  animation: clm-rotate 1.3s linear infinite;
}
@keyframes clm-rotate { to { transform: rotate(360deg); } }

/* ── Tooltip fade ────────────────────────────────────────── */
.clm-fade-enter-active,
.clm-fade-leave-active { transition: opacity 0.15s; }
.clm-fade-enter-from,
.clm-fade-leave-to    { opacity: 0; }

/* ── Donut draw-in ───────────────────────────────────────── */
.clm-brief-donut circle {
  transition: stroke-dasharray 0.65s ease, stroke-dashoffset 0.65s ease;
}
</style>
