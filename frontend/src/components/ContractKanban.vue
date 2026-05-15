<template>
  <div
    class="contract-kanban -mx-1 flex snap-x snap-mandatory gap-3 overflow-x-auto overflow-y-hidden scroll-smooth pb-2 pl-1 pr-6 pt-1 sm:gap-4"
    role="region"
    aria-label="Contract status board"
  >
    <div
      v-for="col in allKanbanColumns"
      :key="col.key"
      class="flex w-[min(100vw-2.5rem,272px)] shrink-0 snap-start flex-col rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/35 shadow-sm dark:bg-[var(--clm-bg-surface-elevated)]/80"
      :class="dragOverKey === col.key ? 'ring-2 ring-[var(--clm-brand)]/50 ring-offset-2 ring-offset-[var(--clm-bg-page)] dark:ring-offset-[var(--clm-bg-page)]' : ''"
      @dragover.prevent="onDragOver(col.key)"
      @dragleave="onDragLeave($event, col.key)"
      @drop.prevent="onDrop($event, col.key)"
    >
      <header
        class="sticky top-0 z-[1] rounded-t-2xl border-b border-[var(--clm-border)] px-4 py-3"
        :class="col.headerClass"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="min-w-0">
            <h3 class="truncate text-sm font-extrabold capitalize tracking-tight text-[var(--clm-text)]">
              {{ col.label }}
            </h3>
            <p class="mt-0.5 text-[10px] font-medium leading-tight text-[var(--clm-text-muted)]">
              {{ col.hint }}
            </p>
          </div>
          <span
            class="shrink-0 rounded-lg bg-[var(--clm-bg-surface)] px-2 py-1 text-xs font-black tabular-nums text-[var(--clm-brand)] shadow-sm dark:bg-[var(--clm-bg-overlay)] dark:text-sky-300"
          >
            {{ countInColumn(col.key) }}
          </span>
        </div>
      </header>

      <div class="flex min-h-[220px] flex-1 flex-col gap-3 p-3">
        <template v-if="!contractsInColumn(col.key).length">
          <div
            class="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-[var(--clm-border)]/80 px-3 py-10 text-center"
          >
            <p class="text-[11px] font-semibold text-[var(--clm-text-muted)]">No contracts</p>
            <p class="mt-1 text-[10px] text-[var(--clm-text-muted)]/90">Drop a card here to set status to {{ col.label }}</p>
          </div>
        </template>
        <template v-else>
          <article
            v-for="c in contractsInColumn(col.key)"
            :key="c.id"
          draggable="true"
          class="kanban-card group relative overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-md transition hover:border-[var(--clm-brand)]/35 hover:shadow-lg dark:bg-[var(--clm-bg-surface-elevated)]"
          :class="[
            draggingId === c.id ? 'scale-[0.98] opacity-60' : '',
            updatingIds.includes(c.id) ? 'pointer-events-none opacity-70' : '',
          ]"
          @dragstart="onDragStart($event, c)"
          @dragend="onDragEnd"
        >
          <div
            class="h-1 w-full bg-gradient-to-r opacity-90"
            :class="col.accentBar"
            aria-hidden="true"
          />
          <div class="p-3.5 pt-3">
            <div class="flex items-start gap-2">
              <div
                class="mt-0.5 flex cursor-grab touch-none text-[var(--clm-text-muted)] active:cursor-grabbing"
                title="Drag to move"
                aria-hidden="true"
              >
                <GripVertical class="h-4 w-4 shrink-0" stroke-width="2" />
              </div>
              <div class="min-w-0 flex-1">
                <router-link
                  :to="`/contracts/${c.id}`"
                  class="block font-bold leading-snug text-[var(--clm-text)] underline-offset-2 hover:underline"
                  @click.stop
                >
                  {{ c.title || 'Untitled contract' }}
                </router-link>
                <p class="mt-1 font-mono text-[11px] text-[var(--clm-text-muted)]">
                  {{ c.contract_number || `ID ${c.id}` }}
                </p>
              </div>
              <span
                class="shrink-0 rounded-md px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wide"
                :class="statusPillClass(c.status)"
              >
                {{ statusBoardLabel(c.status) }}
              </span>
            </div>

            <p v-if="c.description" class="mt-2 line-clamp-2 text-xs leading-relaxed text-[var(--clm-text-muted)]">
              {{ c.description }}
            </p>

            <div
              v-if="c.guideline_framework_title || c.guideline_framework_slug"
              class="mt-2 flex items-start gap-1.5 rounded-lg border border-[var(--clm-border)]/60 bg-[var(--clm-brand-soft)]/25 px-2.5 py-2 dark:bg-[var(--clm-brand-soft)]/15"
            >
              <BookMarked class="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--clm-brand)] dark:text-sky-400" stroke-width="2" />
              <div class="min-w-0 text-[11px] leading-snug">
                <span class="font-bold text-[var(--clm-text)]">{{ c.guideline_framework_title || 'Guideline pack' }}</span>
                <span v-if="c.guideline_framework_slug" class="mt-0.5 block font-mono text-[10px] text-[var(--clm-text-muted)]">
                  {{ c.guideline_framework_slug }}
                </span>
              </div>
            </div>

            <div class="mt-2 flex flex-wrap items-center gap-2">
              <span
                v-if="latestContractVersion(c)"
                class="inline-flex max-w-full flex-wrap items-center gap-x-1.5 gap-y-0.5 rounded-md bg-[var(--clm-bg-overlay)] px-2 py-0.5 text-[10px] font-bold text-[var(--clm-text)]"
              >
                <FileType class="h-3 w-3 shrink-0 text-[var(--clm-text-muted)]" stroke-width="2" aria-hidden="true" />
                <span class="tabular-nums">v{{ latestContractVersion(c).version_number }}</span>
                <span
                  v-if="latestContractVersion(c).is_latest"
                  class="rounded bg-sky-500/15 px-1 py-px text-[8px] font-black uppercase leading-none text-sky-900 dark:bg-sky-500/20 dark:text-sky-200"
                >Latest</span>
                <span class="font-bold uppercase text-[var(--clm-text-muted)]">{{ versionFileTypeLabel(latestContractVersion(c)) }}</span>
              </span>
              <span
                v-else-if="c.file_type"
                class="inline-flex items-center gap-1 rounded-md bg-[var(--clm-bg-overlay)] px-2 py-0.5 text-[10px] font-bold uppercase text-[var(--clm-text-muted)]"
              >
                <FileType class="h-3 w-3" stroke-width="2" aria-hidden="true" />
                {{ c.file_type }}
              </span>
              <span class="text-[10px] text-[var(--clm-text-muted)]">
                Updated {{ formatShortDate(c.updated_at || c.created_at) }}
              </span>
            </div>

            <div class="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--clm-bg-overlay)]">
              <div
                class="h-full rounded-full transition-all"
                :class="progressBarClass(c.status)"
                :style="{ width: `${lifecycleProgressPct(c.status)}%` }"
              />
            </div>

            <div class="mt-3 flex flex-wrap gap-2 border-t border-[var(--clm-border)]/60 pt-3">
              <router-link
                :to="`/contracts/${c.id}`"
                class="inline-flex flex-1 items-center justify-center gap-1 rounded-xl bg-[var(--clm-brand)] px-3 py-2 text-[11px] font-bold text-white transition hover:bg-[var(--clm-brand-strong)]"
                @click.stop
              >
                <ExternalLink class="h-3.5 w-3.5" stroke-width="2" aria-hidden="true" />
                Open
              </router-link>
              <router-link
                v-if="canPrepare(c.status)"
                :to="`/prepare-signature/${c.id}`"
                class="inline-flex flex-1 items-center justify-center gap-1 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-[11px] font-bold text-emerald-800 dark:text-emerald-300"
                @click.stop
              >
                <PenLine class="h-3.5 w-3.5" stroke-width="2" aria-hidden="true" />
                Prepare
              </router-link>
            </div>
          </div>
          </article>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  BookMarked,
  ExternalLink,
  FileType,
  GripVertical,
  PenLine,
} from 'lucide-vue-next'
import { latestContractVersion, versionFileTypeLabel } from '../utils/contractVersion.js'

const props = defineProps({
  contracts: {
    type: Array,
    default: () => [],
  },
  updatingIds: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['status-change'])

const LIFECYCLE_ORDER = ['draft', 'review', 'redraft', 'approved', 'signing', 'active']

/** All status columns (always visible in Kanban). */
const allKanbanColumns = [
  {
    key: 'draft',
    label: 'Draft',
    hint: 'Authoring & intake',
    headerClass: 'bg-slate-500/10 dark:bg-slate-500/15',
    accentBar: 'from-slate-400 to-slate-600',
  },
  {
    key: 'review',
    label: 'Review',
    hint: 'Legal / business review',
    headerClass: 'bg-amber-500/10 dark:bg-amber-500/15',
    accentBar: 'from-amber-400 to-orange-500',
  },
  {
    key: 'redraft',
    label: 'Redraft',
    hint: 'Revisions in progress',
    headerClass: 'bg-orange-500/10 dark:bg-orange-500/15',
    accentBar: 'from-orange-400 to-red-400',
  },
  {
    key: 'approved',
    label: 'Approval',
    hint: 'Approval, pre-execution',
    headerClass: 'bg-teal-500/10 dark:bg-teal-500/15',
    accentBar: 'from-teal-400 to-emerald-600',
  },
  {
    key: 'signing',
    label: 'Signing',
    hint: 'Out for e-sign',
    headerClass: 'bg-violet-500/10 dark:bg-violet-500/15',
    accentBar: 'from-violet-500 to-indigo-600',
  },
  {
    key: 'active',
    label: 'Signed',
    hint: 'Fully executed · in force',
    headerClass: 'bg-emerald-500/10 dark:bg-emerald-500/15',
    accentBar: 'from-emerald-400 to-cyan-500',
  },
  {
    key: 'expired',
    label: 'Expired',
    hint: 'Past end date',
    headerClass: 'bg-amber-600/10 dark:bg-amber-600/15',
    accentBar: 'from-amber-500 to-yellow-600',
  },
  {
    key: 'terminated',
    label: 'Terminated',
    hint: 'Closed / ended',
    headerClass: 'bg-red-500/10 dark:bg-red-500/15',
    accentBar: 'from-red-500 to-rose-700',
  },
]

const draggingId = ref(null)
const dragOverKey = ref(null)

function normStatus(s) {
  return (s || 'draft').toLowerCase()
}

/** Card badge text (matches column titles; API still uses `active` for executed contracts). */
function statusBoardLabel(s) {
  const x = normStatus(s)
  if (x === 'active') return 'signed'
  return x
}

function effectiveColumnKey(c) {
  const s = normStatus(c.status)
  return allKanbanColumns.some((col) => col.key === s) ? s : 'draft'
}

const sortedList = computed(() => {
  const list = [...props.contracts]
  list.sort((a, b) => {
    const ua = new Date(a.updated_at || a.created_at || 0).getTime()
    const ub = new Date(b.updated_at || b.created_at || 0).getTime()
    return ub - ua
  })
  return list
})

function contractsInColumn(key) {
  return sortedList.value.filter((c) => effectiveColumnKey(c) === key)
}

function countInColumn(key) {
  return contractsInColumn(key).length
}

function onDragStart(e, contract) {
  draggingId.value = contract.id
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('application/x-contract-id', String(contract.id))
  e.dataTransfer.setData('text/plain', String(contract.id))
  try {
    e.dataTransfer.setData(
      'application/json',
      JSON.stringify({ id: contract.id, status: normStatus(contract.status) }),
    )
  } catch {
    /* ignore */
  }
}

function onDragEnd() {
  draggingId.value = null
  dragOverKey.value = null
}

function onDragOver(key) {
  dragOverKey.value = key
}

function onDragLeave(e, key) {
  const related = e.relatedTarget
  if (related && e.currentTarget?.contains(related)) return
  if (dragOverKey.value === key) dragOverKey.value = null
}

function onDrop(e, targetStatus) {
  dragOverKey.value = null
  const raw = e.dataTransfer.getData('application/x-contract-id') || e.dataTransfer.getData('text/plain')
  const id = parseInt(raw, 10)
  if (!id) return
  const c = props.contracts.find((x) => x.id === id)
  if (!c) return
  const prev = normStatus(c.status)
  if (prev === targetStatus) return
  emit('status-change', { contractId: id, nextStatus: targetStatus, previousStatus: c.status })
}

function formatShortDate(d) {
  if (!d) return '—'
  try {
    return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return '—'
  }
}

function lifecycleIndex(status) {
  const s = normStatus(status)
  const i = LIFECYCLE_ORDER.indexOf(s)
  return i >= 0 ? i : -1
}

function lifecycleProgressPct(status) {
  const s = normStatus(status)
  if (s === 'expired' || s === 'terminated') return 100
  const i = lifecycleIndex(status)
  if (i < 0) return 8
  return Math.round(((i + 1) / LIFECYCLE_ORDER.length) * 100)
}

function progressBarClass(status) {
  const s = normStatus(status)
  if (s === 'terminated') return 'bg-red-500'
  if (s === 'expired') return 'bg-amber-500'
  return 'bg-gradient-to-r from-[var(--clm-brand)] to-cyan-500 dark:from-sky-500 dark:to-cyan-400'
}

function statusPillClass(status) {
  const map = {
    active: 'bg-[var(--clm-brand-soft)] text-[var(--clm-brand-strong)] dark:bg-sky-500/15 dark:text-sky-300',
    approved: 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300',
    draft: 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)]',
    review: 'bg-amber-500/15 text-amber-900 dark:text-amber-200',
    redraft: 'bg-orange-500/15 text-orange-900 dark:text-orange-200',
    signing: 'bg-violet-500/15 text-violet-900 dark:text-violet-200',
    expired: 'bg-red-500/10 text-red-800 dark:text-red-300',
    terminated: 'bg-red-500/15 text-red-900 dark:text-red-200',
  }
  return map[normStatus(status)] || 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)]'
}

function canPrepare(status) {
  return normStatus(status) === 'signing'
}
</script>

<style scoped>
.contract-kanban {
  scrollbar-width: thin;
  scrollbar-color: var(--clm-border) transparent;
}
.contract-kanban::-webkit-scrollbar {
  height: 8px;
}
.contract-kanban::-webkit-scrollbar-thumb {
  background: var(--clm-border);
  border-radius: 999px;
}
</style>
