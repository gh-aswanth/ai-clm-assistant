<script setup>
import { computed, ref, watch } from 'vue'

/**
 * Primary document version for agents, preview, and scoring.
 * Compact layout — tuned for dense contract views and many versions.
 */
const props = defineProps({
  versions: { type: Array, default: () => [] },
  selectedId: { type: [Number, String, null], default: null },
  embedded: { type: Boolean, default: false },
})

const DENSE_UI_THRESHOLD = 10

const emit = defineEmits(['select'])

const versionQuery = ref('')

watch(
  () => props.versions?.length,
  () => {
    versionQuery.value = ''
  }
)

const useDensePicker = computed(() => (props.versions?.length || 0) > DENSE_UI_THRESHOLD)

const filteredVersions = computed(() => {
  const list = props.versions || []
  const q = versionQuery.value.trim().toLowerCase()
  if (!q) return list
  return list.filter((v) => {
    const num = String(v.version_number ?? '')
    const label = String(v.label || '').toLowerCase()
    const id = String(v.id ?? '')
    return num.includes(q) || label.includes(q) || id.includes(q)
  })
})

const selectedVersion = computed(() =>
  (props.versions || []).find((x) => Number(x.id) === Number(props.selectedId))
)

const selectedSummary = computed(() => {
  const v = selectedVersion.value
  if (!v) return '—'
  const bits = [`v${v.version_number}`]
  if (v.label) bits.push(String(v.label))
  return bits.join(' · ')
})

const totalCount = computed(() => props.versions?.length || 0)

function isActive(v) {
  return Number(props.selectedId) === Number(v.id)
}

function onPick(v) {
  emit('select', v)
}

function clearSearch() {
  versionQuery.value = ''
}
</script>

<template>
  <section
    v-if="versions.length"
    :class="[
      embedded
        ? 'border-b border-[var(--clm-border)] bg-gradient-to-br from-[var(--clm-brand)]/[0.06] via-[var(--clm-bg-overlay)]/25 to-indigo-500/[0.04]'
        : 'rounded-xl border border-[var(--clm-border)] bg-gradient-to-br from-[var(--clm-bg-surface)] via-[var(--clm-bg-overlay)]/40 to-[var(--clm-bg-surface)] shadow-sm',
    ]"
    class="px-2.5 py-2 sm:px-3 sm:py-2.5"
  >
    <div
      :class="embedded ? 'flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between lg:gap-4' : 'flex flex-col gap-2.5'"
    >
      <div class="flex min-w-0 items-start gap-2">
        <div
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--clm-brand)]/22 to-indigo-600/10 text-[var(--clm-brand)] ring-1 ring-[var(--clm-brand)]/12 dark:from-[var(--clm-brand)]/18 dark:to-indigo-500/10"
          aria-hidden="true"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <div class="min-w-0 pt-px">
          <div class="flex flex-wrap items-center gap-1.5">
            <h3 class="text-[9px] font-black uppercase tracking-[0.14em] text-[var(--clm-text-muted)]">
              Working document
            </h3>
            <span
              class="inline-flex items-center rounded border border-emerald-500/20 bg-emerald-500/10 px-1 py-px text-[7px] font-bold uppercase leading-none tracking-wide text-emerald-800 dark:bg-emerald-500/12 dark:text-emerald-300"
            >
              Active
            </span>
            <span
              v-if="useDensePicker"
              class="rounded border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-1 py-px text-[7px] font-bold tabular-nums leading-none text-[var(--clm-text-muted)]"
            >
              {{ totalCount }}
            </span>
          </div>
          <p class="mt-0.5 max-w-prose text-[9px] leading-snug text-[var(--clm-text-muted)]">
            <template v-if="useDensePicker">Search below — saved in this browser.</template>
            <template v-else>Preview &amp; agents use this version. Saved in browser.</template>
          </p>
        </div>
      </div>

      <!-- Few versions: compact chips -->
      <div
        v-if="!useDensePicker"
        class="flex max-h-[min(36vh,11rem)] flex-wrap content-start gap-1.5 overflow-y-auto overflow-x-hidden pr-0.5 lg:max-w-[min(100%,26rem)] lg:justify-end"
        role="radiogroup"
        aria-label="Document version"
      >
        <button
          v-for="v in versions"
          :key="'wv-' + v.id"
          type="button"
          role="radio"
          :aria-checked="isActive(v)"
          @click="onPick(v)"
          class="relative inline-flex items-center gap-1 rounded-md border px-2 py-1 text-left text-[9px] font-bold leading-none transition focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--clm-brand)] focus-visible:ring-offset-1 dark:focus-visible:ring-offset-[var(--clm-bg-surface)]"
          :class="
            isActive(v)
              ? 'border-[var(--clm-brand)] bg-[var(--clm-brand)]/12 text-[var(--clm-brand)] ring-1 ring-[var(--clm-brand)]/30 dark:bg-[var(--clm-brand)]/15'
              : 'border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)] hover:border-[var(--clm-brand)]/40 dark:hover:border-[var(--clm-brand)]/35'
          "
        >
          <span class="tabular-nums">v{{ v.version_number }}</span>
          <span
            v-if="v.label"
            class="max-w-[5rem] truncate text-[8px] font-semibold opacity-85"
            :title="v.label"
          >{{ v.label }}</span>
          <span
            v-if="v.is_latest"
            class="rounded px-0.5 py-px text-[7px] font-black uppercase leading-none text-sky-900 bg-sky-500/20 dark:bg-sky-500/22 dark:text-sky-200"
          >Latest</span>
          <span
            v-if="isActive(v)"
            class="ml-px inline-flex h-3.5 min-w-3.5 items-center justify-center rounded-sm bg-[var(--clm-brand)] px-0.5 text-[7px] font-black leading-none text-white"
            aria-hidden="true"
          >✓</span>
        </button>
      </div>

      <!-- Many versions: summary + search + scroll -->
      <div v-else class="flex w-full min-w-0 flex-col gap-1.5 sm:max-w-none lg:max-w-[min(100%,32rem)] lg:min-w-[16rem]">
        <div
          class="flex flex-wrap items-center gap-x-1 gap-y-0.5 rounded-md border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/90 px-1.5 py-0.5"
        >
          <span class="text-[7px] font-bold uppercase leading-none text-[var(--clm-text-muted)]">Sel.</span>
          <span class="min-w-0 truncate text-[10px] font-bold leading-tight text-[var(--clm-brand)]" :title="selectedSummary">{{ selectedSummary }}</span>
          <span
            v-if="selectedVersion?.is_latest"
            class="shrink-0 rounded px-0.5 py-px text-[7px] font-black uppercase leading-none bg-sky-500/20 text-sky-900 dark:bg-sky-500/25 dark:text-sky-200"
          >Latest</span>
        </div>

        <div class="relative">
          <span class="pointer-events-none absolute left-2 top-1/2 z-10 -translate-y-1/2 text-[var(--clm-text-muted)]" aria-hidden="true">
            <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="versionQuery"
            type="search"
            autocomplete="off"
            aria-label="Filter document versions"
            placeholder="Filter versions…"
            class="w-full rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] py-1 pl-7 pr-7 text-[10px] leading-tight text-[var(--clm-text)] shadow-inner placeholder:text-[var(--clm-text-muted)] focus:border-[var(--clm-brand)] focus:outline-none focus:ring-1 focus:ring-[var(--clm-brand)]/30"
          />
          <button
            v-if="versionQuery"
            type="button"
            class="absolute right-1 top-1/2 z-10 -translate-y-1/2 rounded px-1 py-px text-[8px] font-bold text-[var(--clm-text-muted)] hover:bg-[var(--clm-bg-overlay)] hover:text-[var(--clm-text)]"
            @click="clearSearch"
          >
            Clear
          </button>
        </div>

        <div
          class="max-h-28 overflow-y-auto overflow-x-hidden rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/50 p-1 shadow-inner dark:bg-[var(--clm-bg-overlay)]/40 sm:max-h-32"
          role="listbox"
          :aria-label="'Versions, ' + filteredVersions.length + ' shown'"
        >
          <div
            v-if="filteredVersions.length"
            class="grid grid-cols-1 gap-0.5 sm:grid-cols-2 sm:gap-1 lg:grid-cols-3"
          >
            <button
              v-for="v in filteredVersions"
              :key="'wv-dense-' + v.id"
              type="button"
              role="option"
              :aria-selected="isActive(v)"
              class="flex min-w-0 items-center gap-1 rounded-md border px-1.5 py-1 text-left text-[9px] font-bold leading-tight transition focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--clm-brand)]"
              :class="
                isActive(v)
                  ? 'border-[var(--clm-brand)] bg-[var(--clm-brand)]/10 text-[var(--clm-brand)] ring-1 ring-[var(--clm-brand)]/25'
                  : 'border-transparent bg-[var(--clm-bg-overlay)] text-[var(--clm-text)] hover:bg-[var(--clm-bg-surface-elevated)] dark:hover:bg-[var(--clm-bg-surface)]'
              "
              @click="onPick(v)"
            >
              <span class="shrink-0 tabular-nums">v{{ v.version_number }}</span>
              <span v-if="v.label" class="min-w-0 flex-1 truncate text-[8px] font-semibold opacity-90" :title="v.label">{{ v.label }}</span>
              <span
                v-if="v.is_latest"
                class="shrink-0 rounded px-0.5 py-px text-[7px] font-black uppercase leading-none text-sky-900 bg-sky-500/25 dark:text-sky-100"
              >latest</span>
            </button>
          </div>
          <p v-else class="py-4 text-center text-[9px] text-slate-500 dark:text-[var(--clm-text-muted)]">
            No match.
            <button type="button" class="ml-0.5 font-bold text-[var(--clm-brand)] underline" @click="clearSearch">Clear</button>
          </p>
        </div>

        <p v-if="versionQuery && filteredVersions.length" class="text-[8px] leading-none text-[var(--clm-text-muted)]">
          {{ filteredVersions.length }}/{{ totalCount }}
        </p>
      </div>
    </div>
  </section>
</template>
