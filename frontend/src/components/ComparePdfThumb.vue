<template>
  <div
    class="relative flex min-h-0 min-w-0 overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-[0_2px_8px_-2px_rgba(15,23,42,0.08)] dark:border-slate-600/90 dark:bg-slate-900/70 dark:shadow-black/20"
    :class="compact ? 'flex-row items-stretch' : 'flex-col'"
  >
    <!-- Accent stripe + meta (compact = horizontal) -->
    <div
      v-if="compact"
      class="flex w-[4rem] shrink-0 flex-col justify-center gap-0.5 border-r border-slate-100 bg-slate-50/90 px-2 py-1.5 dark:border-slate-700 dark:bg-slate-800/80"
    >
      <span
        class="inline-flex w-fit items-center rounded-md px-1.5 py-0.5 text-[9px] font-black text-white"
        :class="label === 'A' ? 'bg-sky-600' : 'bg-violet-600'"
      >{{ label }}</span>
      <span
        v-if="subtitle"
        class="line-clamp-2 text-[7px] font-medium leading-tight text-slate-500 dark:text-slate-400"
        :title="subtitle"
      >{{ subtitle }}</span>
    </div>

    <div class="relative flex min-w-0 flex-1 flex-col">
      <!-- Non-compact header overlay (badges) -->
      <div
        v-if="!compact"
        class="pointer-events-none absolute left-3 top-3 z-10 flex max-w-[calc(100%-1.5rem)] flex-col items-start gap-1"
      >
        <span
          class="inline-flex items-center rounded-lg px-2 py-1 text-[10px] font-black text-white shadow-sm"
          :class="label === 'A' ? 'bg-sky-600' : 'bg-violet-600'"
        >Side {{ label }}</span>
        <span
          v-if="subtitle"
          class="max-w-full truncate rounded-md bg-white/95 px-2 py-0.5 text-[9px] font-semibold text-slate-600 shadow-sm ring-1 ring-slate-200/80 dark:bg-slate-800/95 dark:text-slate-200 dark:ring-slate-600"
          :title="subtitle"
        >{{ subtitle }}</span>
      </div>

      <div
        class="relative flex min-w-0 flex-1 items-center justify-center bg-gradient-to-b from-slate-100/95 via-slate-50/90 to-slate-100/80 dark:from-slate-950/80 dark:via-slate-900/60 dark:to-slate-950/80"
        :class="
          compact
            ? 'max-h-[3.75rem] min-h-[3.25rem] px-1 py-1'
            : 'min-h-[11rem] px-3 pb-3 pt-14 sm:min-h-[12rem]'
        "
        ref="containerRef"
      >
        <!-- ── No version selected ──────────────────────────────── -->
        <div
          v-if="!versionId"
          class="mx-2 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300/80 bg-white/60 px-3 py-4 text-center dark:border-slate-600 dark:bg-slate-900/40"
          :class="compact ? 'py-2' : ''"
        >
          <p
            class="font-medium leading-snug text-slate-500 dark:text-slate-400"
            :class="compact ? 'px-0.5 text-[7px]' : 'text-[10px]'"
          >
            {{ compact ? 'Pick a version' : 'Choose a version to see the first page' }}
          </p>
        </div>

        <!-- ── PDF canvas ──────────────────────────────────────── -->
        <canvas
          v-else-if="isPdf"
          v-show="showCanvas"
          ref="canvasRef"
          class="rounded-lg object-contain object-center shadow-sm ring-1 ring-black/5 dark:ring-white/10"
          :class="compact ? 'max-h-[3.5rem] w-full' : 'max-h-[11rem] w-full'"
        />
        <p
          v-else-if="isPdf && loading"
          class="font-medium text-slate-500 dark:text-slate-400"
          :class="compact ? 'text-[7px]' : 'text-[10px]'"
        >{{ compact ? '…' : 'Loading preview…' }}</p>
        <p
          v-else-if="isPdf && error"
          class="max-w-[95%] text-center leading-snug text-red-600 dark:text-red-400"
          :class="compact ? 'px-0.5 text-[7px]' : 'px-2 text-[10px]'"
          :title="error"
        >{{ compact ? 'Preview failed' : error }}</p>

        <!-- ── DOCX: compact badge ─────────────────────────────── -->
        <div
          v-else-if="isDocx && compact"
          class="flex flex-col items-center gap-0.5"
        >
          <span class="rounded-md bg-blue-100 px-1.5 py-0.5 text-[7px] font-black text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">DOCX</span>
          <span v-if="docxLoading" class="text-[6px] text-slate-400">loading…</span>
        </div>

        <!-- ── DOCX: scaled iframe preview ────────────────────── -->
        <template v-else-if="isDocx && !compact">
          <div
            v-if="docxLoading"
            class="flex flex-col items-center gap-2"
          >
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
            <p class="text-[10px] text-slate-500">Loading DOCX preview…</p>
          </div>
          <div
            v-else-if="docxError"
            class="px-3 text-center text-[10px] leading-snug text-red-500"
          >{{ docxError }}</div>
          <!-- Scaled-down iframe inside a clipping wrapper -->
          <div
            v-else-if="docxPreviewUrl"
            class="docx-thumb-clip pointer-events-none overflow-hidden rounded-lg shadow-sm ring-1 ring-black/5"
            :style="clipStyle"
          >
            <iframe
              :src="docxPreviewUrl"
              :style="iframeStyle"
              sandbox="allow-same-origin allow-scripts"
              title="DOCX preview"
              class="block border-0 bg-white"
              @load="onIframeLoad"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onUnmounted, onMounted, nextTick } from 'vue'

let pdfjsLibPromise = null
const loadPdfJsLib = async () => {
  if (!pdfjsLibPromise) {
    pdfjsLibPromise = import('pdfjs-dist')
  }
  const pdfjsLib = await pdfjsLibPromise
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'
  return pdfjsLib
}

const IFRAME_W = 680   // virtual width the iframe is rendered at
const IFRAME_H = 960   // virtual height

const props = defineProps({
  contractId: { type: [String, Number], required: true },
  versionId:  { type: String, default: '' },
  label:      { type: String, default: 'Preview' },
  subtitle:   { type: String, default: '' },
  fileType:   { type: String, default: '' },
  maxWidth:   { type: Number, default: 260 },
  maxHeight:  { type: Number, default: 168 },
  compact:    { type: Boolean, default: false },
})

// ── Derived type flags ─────────────────────────────────────────────────────
const normalizedType = computed(() => (props.fileType || '').trim().toLowerCase())
const isPdf  = computed(() => !normalizedType.value || normalizedType.value === 'pdf')
const isDocx = computed(() => normalizedType.value === 'docx' || normalizedType.value === 'doc')

// ── PDF state ──────────────────────────────────────────────────────────────
const canvasRef  = ref(null)
const loading    = ref(false)
const error      = ref('')
const showCanvas = ref(false)

const effMaxW = computed(() => (props.compact ? 108 : props.maxWidth))
const effMaxH = computed(() => (props.compact ? 68  : props.maxHeight))

let loadToken = 0

async function loadPdfPreview() {
  loadToken += 1
  const token = loadToken
  error.value       = ''
  showCanvas.value  = false

  const vid = props.versionId
  if (!vid || props.contractId == null || props.contractId === '') return
  if (!isPdf.value) return

  loading.value = true
  try {
    await new Promise((r) => requestAnimationFrame(r))
    const canvas = canvasRef.value
    if (!canvas || token !== loadToken) { loading.value = false; return }

    const url = `/api/contracts/${props.contractId}/file?version_id=${encodeURIComponent(vid)}&t=${Date.now()}`
    const pdfjsLib = await loadPdfJsLib()
    const pdf  = await pdfjsLib.getDocument(url).promise
    if (token !== loadToken) return

    const page = await pdf.getPage(1)
    if (token !== loadToken) return

    const baseViewport = page.getViewport({ scale: 1 })
    const dpr = typeof window !== 'undefined' ? Math.min(window.devicePixelRatio || 1, 2) : 1
    const scaleCss = Math.min(
      effMaxW.value / baseViewport.width,
      effMaxH.value / baseViewport.height,
      1.35
    )
    const cssViewport    = page.getViewport({ scale: scaleCss })
    const bitmapViewport = page.getViewport({ scale: scaleCss * dpr })
    const ctx = canvas.getContext('2d', { alpha: false })
    canvas.width  = Math.floor(bitmapViewport.width)
    canvas.height = Math.floor(bitmapViewport.height)
    canvas.style.width  = `${Math.floor(cssViewport.width)}px`
    canvas.style.height = `${Math.floor(cssViewport.height)}px`
    await page.render({ canvasContext: ctx, viewport: bitmapViewport }).promise
    if (token !== loadToken) return
    showCanvas.value = true
  } catch (e) {
    if (token !== loadToken) return
    console.warn('ComparePdfThumb PDF:', e)
    error.value = 'Could not load this PDF'
  } finally {
    if (token === loadToken) loading.value = false
  }
}

// ── DOCX state ─────────────────────────────────────────────────────────────
const docxPreviewUrl = ref('')
const docxLoading    = ref(false)
const docxError      = ref('')
const containerRef   = ref(null)
const containerW     = ref(240)
const containerH     = ref(168)

let mammothPromise = null
const loadMammoth = () => {
  if (!mammothPromise) mammothPromise = import('mammoth')
  return mammothPromise
}

const DOCX_CSS = 'html,body{background:#fff;color:#1a1a1a;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:24px 32px;max-width:820px;margin:auto;line-height:1.75;font-size:14px}h1,h2,h3,h4,h5,h6{color:#111;margin-top:1.4em}p{margin:0.6em 0}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:6px 10px}a{color:#2563eb}img{max-width:100%;height:auto}'

const iframeScale = computed(() => Math.min(
  containerW.value / IFRAME_W,
  containerH.value / IFRAME_H,
))

const clipStyle = computed(() => ({
  width:  `${Math.round(IFRAME_W * iframeScale.value)}px`,
  height: `${Math.round(IFRAME_H * iframeScale.value)}px`,
}))

const iframeStyle = computed(() => ({
  width:             `${IFRAME_W}px`,
  height:            `${IFRAME_H}px`,
  transform:         `scale(${iframeScale.value})`,
  transformOrigin:   'top left',
  display:           'block',
}))

function onIframeLoad() {
  docxLoading.value = false
}

function measureContainer() {
  if (!containerRef.value) return
  const r = containerRef.value.getBoundingClientRect()
  if (r.width  > 10) containerW.value = r.width  - 24
  if (r.height > 10) containerH.value = r.height - 24
}

async function loadDocxPreview() {
  docxPreviewUrl.value = ''
  docxError.value      = ''
  const vid = props.versionId
  if (!vid || props.contractId == null || props.contractId === '') return
  if (!isDocx.value) return
  if (props.compact) return

  docxLoading.value = true
  await nextTick()
  measureContainer()

  try {
    const fileUrl = `/api/contracts/${props.contractId}/file?version_id=${encodeURIComponent(vid)}&t=${Date.now()}`
    const resp = await fetch(fileUrl)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const arrayBuffer = await resp.arrayBuffer()

    const mammoth = await loadMammoth()
    const result = await mammoth.default.convertToHtml({ arrayBuffer })
    const fullHtml = `<html><head><meta charset="utf-8"><style>${DOCX_CSS}</style></head><body>${result.value}</body></html>`
    const blob = new Blob([fullHtml], { type: 'text/html' })
    docxPreviewUrl.value = URL.createObjectURL(blob)
    docxLoading.value = false
  } catch (e) {
    console.warn('ComparePdfThumb DOCX mammoth:', e)
    docxError.value = 'Could not render DOCX preview'
    docxLoading.value = false
  }
}

// ── Unified watcher ────────────────────────────────────────────────────────
watch(
  () => [props.contractId, props.versionId, props.fileType, props.compact],
  () => {
    if (isPdf.value)  loadPdfPreview()
    if (isDocx.value) loadDocxPreview()
  },
  { immediate: true }
)

onMounted(() => measureContainer())
onUnmounted(() => { loadToken += 1 })
</script>
