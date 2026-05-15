<template>
  <div
    class="group/chat-att relative mt-2 flex w-full max-w-md overflow-hidden rounded-2xl ring-1 ring-slate-900/[0.06] transition dark:ring-white/10"
  >
    <!-- Gradient layer -->
    <div
      class="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-500/[0.07] via-transparent to-indigo-600/[0.08] opacity-100 transition group-hover/chat-att:from-blue-500/12 group-hover/chat-att:to-indigo-600/14 dark:from-blue-400/10 dark:to-indigo-500/10"
      aria-hidden="true"
    />

    <div
      class="relative flex flex-1 items-stretch gap-0 border border-slate-200/90 bg-white/95 backdrop-blur-sm dark:border-slate-700/90 dark:bg-slate-900/85"
    >
      <!-- Icon column -->
      <div
        class="flex w-14 shrink-0 flex-col items-center justify-center bg-gradient-to-b from-slate-50 to-slate-100/90 dark:from-slate-800 dark:to-slate-900/80"
      >
        <div
          class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br shadow-lg"
          :class="iconWrapClass"
        >
          <svg
            class="h-5 w-5 text-white drop-shadow-sm"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.75"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <span
          class="mt-1.5 rounded px-1 py-px text-[8px] font-black uppercase tracking-wider text-slate-500 dark:text-slate-400"
        >{{ ext }}</span>
      </div>

      <!-- Content -->
      <div class="flex min-w-0 flex-1 flex-col justify-center gap-1.5 py-3 pl-3 pr-3 sm:py-3.5 sm:pl-4 sm:pr-4">
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <p class="truncate text-[13px] font-bold leading-tight text-slate-900 dark:text-slate-50">
              {{ baseName }}
            </p>
            <p
              v-if="metaLine"
              class="mt-1 text-[10px] font-medium leading-snug text-slate-500 dark:text-slate-400"
            >
              {{ metaLine }}
            </p>
          </div>

          <!-- Action buttons -->
          <div class="flex shrink-0 items-center gap-1.5">
            <!-- Edit button (only for DOCX) -->
            <button
              v-if="isWord && href"
              type="button"
              @click.prevent="$emit('edit')"
              class="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1.5 text-[10px] font-bold text-blue-700 shadow-sm transition hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-800/50"
              title="Open in editor"
            >
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
              Edit
            </button>
            <!-- Download -->
            <a
              :href="href"
              :download="downloadName"
              class="inline-flex shrink-0 items-center gap-1 rounded-full bg-slate-900 px-2.5 py-1.5 text-[10px] font-bold text-white shadow-md transition hover:bg-blue-600 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-blue-500 dark:hover:text-white"
              :title="`Download ${downloadName}`"
            >
              Download
              <svg class="h-3.5 w-3.5 opacity-90" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  href:     { type: String, required: true },
  filename: { type: String, default: 'attachment' },
  /** e.g. "Microsoft Word · Track changes" */
  subtitle: { type: String, default: '' },
})

defineEmits(['edit'])

const downloadName = computed(() => {
  const n = String(props.filename || '').trim()
  return n || 'attachment'
})

const ext = computed(() => {
  const n = downloadName.value
  const i = n.lastIndexOf('.')
  if (i <= 0 || i === n.length - 1) return 'FILE'
  return n.slice(i + 1).toUpperCase().slice(0, 8)
})

const baseName = computed(() => {
  const n = downloadName.value
  const i = n.lastIndexOf('.')
  if (i <= 0) return n
  return n.slice(0, i) || n
})

const isPdf  = computed(() => ext.value === 'PDF')
const isWord = computed(() => ['DOC', 'DOCX', 'RTF'].includes(ext.value))

const iconWrapClass = computed(() => {
  if (isPdf.value)  return 'from-rose-500 to-red-600 shadow-rose-900/25'
  if (isWord.value) return 'from-blue-500 to-indigo-600 shadow-blue-900/25'
  return 'from-slate-500 to-slate-700 shadow-slate-900/25'
})

const metaLine = computed(() => {
  if (props.subtitle) return props.subtitle
  if (isWord.value)   return 'Microsoft Word document'
  if (isPdf.value)    return 'PDF document'
  return ''
})
</script>
