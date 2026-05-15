<template>
  <div
    class="clm-docx-build relative overflow-hidden rounded-2xl border border-blue-200/90 bg-white p-4 shadow-md shadow-blue-900/10 dark:border-blue-900/60 dark:bg-[var(--clm-bg-surface-elevated)] dark:shadow-black/30"
    role="status"
    aria-live="polite"
  >
    <div
      class="pointer-events-none absolute right-0 top-0 h-24 w-24 translate-x-8 -translate-y-8 rounded-full bg-blue-500/10 blur-2xl dark:bg-blue-400/10"
      aria-hidden="true"
    />
    <div
      class="pointer-events-none absolute bottom-0 left-0 h-20 w-32 -translate-x-10 translate-y-10 rounded-full bg-indigo-400/10 blur-2xl dark:bg-indigo-500/10"
      aria-hidden="true"
    />

    <div class="relative flex gap-4">
      <!-- Stacked "pages" + .docx -->
      <div class="relative h-[4.5rem] w-[3.75rem] shrink-0">
        <span
          class="clm-docx-sheet clm-docx-sheet-back absolute left-0 top-2 h-[3.35rem] w-[3.25rem] rounded-md border border-slate-200/90 bg-slate-50 dark:border-slate-600 dark:bg-slate-800/90"
          aria-hidden="true"
        />
        <span
          class="clm-docx-sheet clm-docx-sheet-mid absolute left-1 top-1 h-[3.35rem] w-[3.25rem] rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:shadow-black/40"
          aria-hidden="true"
        />
        <div
          class="clm-docx-sheet clm-docx-sheet-front absolute left-2 top-0 flex h-[3.35rem] w-[3.25rem] flex-col rounded-md border-2 border-blue-200 bg-gradient-to-br from-white to-blue-50/80 p-1.5 shadow-md shadow-blue-900/10 dark:border-blue-700 dark:from-slate-900 dark:to-blue-950/50 dark:shadow-black/50"
        >
          <div class="mb-1 flex items-center justify-between gap-1">
            <span class="h-0.5 flex-1 rounded-full bg-blue-200/80 dark:bg-blue-800/80" />
            <span class="h-0.5 w-2 rounded-full bg-blue-100 dark:bg-blue-900/80" />
          </div>
          <div class="flex flex-1 flex-col justify-center gap-0.5">
            <div class="clm-docx-track-old h-0.5 rounded-full bg-rose-200 dark:bg-rose-900/70" />
            <div class="clm-docx-track-new h-0.5 rounded-full bg-emerald-200 dark:bg-emerald-900/60" />
            <div class="mt-0.5 h-0.5 w-4/5 rounded-full bg-slate-200 dark:bg-slate-700" />
          </div>
          <span
            class="mt-auto inline-block w-fit rounded px-1 py-px text-[6px] font-black uppercase tracking-tight text-blue-700 dark:text-blue-300"
          >.docx</span>
        </div>
      </div>

      <div class="min-w-0 flex-1 space-y-2.5">
        <div class="flex flex-wrap items-center gap-2">
          <span
            class="rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-[9px] font-black tracking-wide text-blue-800 dark:border-blue-800 dark:bg-blue-950/60 dark:text-blue-200"
          >
            Microsoft Word
          </span>
          <span
            class="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-[9px] font-bold tabular-nums text-slate-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
          >
            Output · .docx
          </span>
        </div>

        <div>
          <p class="text-sm font-bold leading-snug text-[var(--clm-text)]">
            {{ headingTitle }}
          </p>
          <p class="mt-0.5 text-[11px] leading-relaxed text-[var(--clm-text-muted)]">
            {{ currentLine }}
          </p>
        </div>

        <div class="flex items-center gap-3">
          <div
            class="relative h-9 w-9 shrink-0 text-blue-600 dark:text-blue-400"
            aria-hidden="true"
          >
            <svg class="clm-docx-orbit absolute inset-0 h-full w-full opacity-35" viewBox="0 0 36 36">
              <circle
                cx="18"
                cy="18"
                r="15"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-dasharray="24 48"
              />
            </svg>
            <svg class="clm-docx-orbit-rev absolute inset-0.5 h-[calc(100%-4px)] w-[calc(100%-4px)]" viewBox="0 0 32 32">
              <circle
                cx="16"
                cy="16"
                r="13"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-dasharray="20 60"
                class="text-indigo-500 dark:text-indigo-400"
              />
            </svg>
          </div>
          <div class="min-w-0 flex-1 space-y-1">
            <div class="h-1.5 w-full overflow-hidden rounded-full bg-slate-200/90 dark:bg-slate-700/90">
              <div class="clm-docx-bar h-full w-[45%] rounded-full bg-gradient-to-r from-blue-600 via-indigo-500 to-blue-500" />
            </div>
            <p class="text-[10px] font-medium text-slate-500 dark:text-slate-400">
              Track changes and comments are written into
              <span class="font-semibold text-blue-700 dark:text-blue-300">draft_redline.docx</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'

/** Shown after every plan todo is completed while the Word build still runs */
const FINALIZING_LINES = [
  'Finalizing your redlined document…',
  'Writing Word revisions (insertions and deletions)…',
  'Embedding review comments for each change…',
  'Packaging the file for download…',
]

const FALLBACK_LINE = 'Starting your drafting run…'

const props = defineProps({
  active: { type: Boolean, default: false },
  /** True when all todos are complete but the stream is still open (DOCX / reply). */
  finalizing: { type: Boolean, default: false },
  /** Todo `content` strings for the in-progress phase (rotated in order). */
  todoLines: { type: Array, default: () => [] },
})

const lineIndex = ref(0)
let timer = null

const linesForRotation = computed(() => {
  if (props.finalizing) return FINALIZING_LINES
  const raw = Array.isArray(props.todoLines)
    ? props.todoLines.map((s) => String(s || '').trim()).filter(Boolean)
    : []
  if (raw.length) return raw
  return [FALLBACK_LINE]
})

const headingTitle = computed(() =>
  props.finalizing ? 'Finalizing your redlined document' : 'Preparing your redlined document'
)

const currentLine = computed(() => {
  const lines = linesForRotation.value
  if (!lines.length) return ''
  return lines[lineIndex.value % lines.length]
})

function startRotation() {
  stopRotation()
  lineIndex.value = 0
  const tick = () => {
    const lines = linesForRotation.value
    if (!lines.length) return
    lineIndex.value = (lineIndex.value + 1) % lines.length
  }
  timer = setInterval(tick, 2600)
}

function stopRotation() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

watch(
  () => props.active,
  (on) => {
    lineIndex.value = 0
    if (on) startRotation()
    else stopRotation()
  },
  { immediate: true }
)

watch(
  [() => props.finalizing, () => props.todoLines],
  () => {
    lineIndex.value = 0
    if (props.active) {
      stopRotation()
      startRotation()
    }
  },
  { deep: true }
)

onUnmounted(stopRotation)
</script>

<style scoped>
.clm-docx-sheet-back {
  animation: clm-docx-stack 2.4s ease-in-out infinite;
}
.clm-docx-sheet-mid {
  animation: clm-docx-stack 2.4s ease-in-out infinite 0.15s;
}
.clm-docx-sheet-front {
  animation: clm-docx-stack 2.4s ease-in-out infinite 0.3s;
}

@keyframes clm-docx-stack {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

.clm-docx-track-old {
  animation: clm-docx-fade-line 2s ease-in-out infinite;
  opacity: 0.85;
}
.clm-docx-track-new {
  animation: clm-docx-fade-line 2s ease-in-out infinite 0.35s;
  opacity: 0.85;
}

@keyframes clm-docx-fade-line {
  0%,
  100% {
    opacity: 0.45;
    transform: scaleX(0.92);
    transform-origin: left;
  }
  50% {
    opacity: 1;
    transform: scaleX(1);
    transform-origin: left;
  }
}

.clm-docx-orbit {
  animation: clm-docx-spin 2.8s linear infinite;
}
.clm-docx-orbit-rev {
  animation: clm-docx-spin-rev 2s linear infinite;
}

@keyframes clm-docx-spin {
  to {
    transform: rotate(360deg);
  }
}
@keyframes clm-docx-spin-rev {
  to {
    transform: rotate(-360deg);
  }
}

.clm-docx-bar {
  animation: clm-docx-bar-move 1.8s ease-in-out infinite;
}

@keyframes clm-docx-bar-move {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(220%);
  }
}
</style>
