<template>
  <!-- Fixed viewport-bound height + overflow-hidden so DOCX scrolls inside #doc-scroll-area (same idea as SignContract viewer card). -->
  <div class="flex h-[calc(100dvh-7.5rem)] max-h-[calc(100dvh-7.5rem)] min-h-0 flex-col overflow-hidden">
    <!-- Header -->
    <div class="mb-4 shrink-0 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Prepare Document for Signing</h1>
        <p class="text-gray-500 text-sm">
          {{ contract?.title }}
          <span v-if="currentVersion" class="ml-2 text-blue-600 font-bold">
            v{{ currentVersion.version_number }}
            <span v-if="currentVersion.label"> · {{ currentVersion.label }}</span>
          </span>
          <span v-if="isDocx" class="ml-2 inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">DOCX</span>
        </p>
      </div>
      <div class="flex gap-3">
        <button @click="$router.push(`/contracts/${contractId}`)" class="px-4 py-2 text-gray-600 hover:text-gray-800">Cancel</button>
        <button
          @click="sendInvitations"
          :disabled="!versionSigners.length || sending"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ sending ? 'Sending...' : 'Send Invitations' }}
        </button>
      </div>
    </div>

    <div
      v-if="prepareLoadError"
      class="mb-3 shrink-0 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-100"
      role="alert"
    >
      {{ prepareLoadError }}
    </div>

    <div class="flex min-h-0 flex-1 gap-6 overflow-hidden lg:flex-row">
      <!-- Left Sidebar -->
      <div class="flex max-h-full min-h-0 w-full shrink-0 flex-col gap-4 overflow-hidden lg:w-64">
        <!-- Field types -->
        <div class="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 class="font-bold mb-1 text-gray-900 dark:text-white text-sm">Field Types</h3>
          <p class="mb-2 text-[10px] text-gray-400">Drag onto the document →</p>
          <div class="space-y-2">
            <div
              v-for="tool in tools"
              :key="tool.type"
              draggable="true"
              @dragstart="onDragStartTool($event, tool.type)"
              class="p-2.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-200 border border-blue-100 dark:border-blue-800 rounded-lg cursor-grab flex items-center gap-2 hover:bg-blue-100 transition text-sm select-none"
            >
              <span>{{ tool.icon }}</span>
              <span class="font-medium">{{ tool.label }}</span>
            </div>
          </div>
        </div>

        <!-- Signers -->
        <div class="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex-1 flex flex-col overflow-hidden">
          <div class="flex justify-between items-center mb-3">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm">Signers</h3>
            <button @click="showAddSigner = true" class="text-blue-600 hover:text-blue-700 text-sm font-bold">+ Add</button>
          </div>
          <div class="space-y-2 overflow-y-auto flex-1">
            <div
              v-for="vs in versionSigners" :key="vs.id"
              class="p-2.5 border rounded-lg flex flex-col gap-0.5 transition-all cursor-pointer"
              :class="selectedVersionSignerId === vs.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-100 dark:border-gray-700 hover:border-blue-300'"
              @click="selectedVersionSignerId = vs.id"
            >
              <div class="font-medium text-sm text-gray-900 dark:text-white flex items-center justify-between">
                <span>{{ vs.master_signer?.name }}</span>
                <button @click.stop="removeSigner(vs.id)" class="text-red-400 hover:text-red-600 text-xs">✕</button>
              </div>
              <div class="text-[10px] text-gray-500 truncate">{{ vs.master_signer?.email }}</div>
              <div v-if="vs.master_signer?.organization" class="text-[10px] text-gray-400 truncate">{{ vs.master_signer?.organization }}</div>
              <div class="text-[9px] font-bold mt-0.5" :class="vs.status === 'signed' ? 'text-green-500' : 'text-yellow-500'">
                {{ vs.status.toUpperCase() }}
              </div>
            </div>
            <div v-if="!versionSigners.length" class="text-xs text-gray-400 italic text-center py-4">
              No signers added yet.
            </div>
          </div>
        </div>
      </div>

      <!-- Main: Document Viewer (flex-1 min-h-0 keeps scroll inside this card, not the page) -->
      <div class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-gray-200 bg-gray-100 dark:border-gray-700 dark:bg-gray-900">

        <!-- Toolbar (shared PDF + DOCX) -->
        <div class="shrink-0 border-b bg-white p-2 dark:bg-gray-800 flex justify-between items-center gap-4">
          <div class="flex items-center gap-3">
            <!-- PDF: page navigation -->
            <template v-if="!isDocx">
              <button @click="prevPage" :disabled="currentPage <= 1" class="p-1 disabled:opacity-30 rounded hover:bg-gray-100">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
              </button>
              <span class="text-sm font-medium whitespace-nowrap">Page {{ currentPage }} / {{ totalPages }}</span>
              <button @click="nextPage" :disabled="currentPage >= totalPages" class="p-1 disabled:opacity-30 rounded hover:bg-gray-100">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
              </button>
            </template>
            <!-- DOCX: scroll indicator -->
            <template v-else>
              <span class="inline-flex items-center gap-1.5 text-sm font-medium text-gray-600 dark:text-gray-300">
                <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-3-3v6M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z"/></svg>
                DOCX
                <span class="text-gray-400 font-normal">· {{ totalPages }} page{{ totalPages !== 1 ? 's' : '' }} · scroll to read</span>
              </span>
            </template>
          </div>
          <div class="text-xs text-gray-500 truncate">
            <span v-if="selectedVersionSigner">Placing for: <strong class="text-gray-800 dark:text-gray-100">{{ selectedVersionSigner.master_signer?.name }}</strong></span>
            <span v-else class="italic">Select a signer to start placing fields</span>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="docLoading" class="flex min-h-0 flex-1 items-center justify-center gap-3 flex-col">
          <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
          <p class="text-sm text-gray-500">Loading document…</p>
        </div>

        <!-- Document area: min-h-0 + flex-1 + overflow-auto = scroll inside panel (not the app main). -->
        <div
          v-else
          id="doc-scroll-area"
          class="flex min-h-0 flex-1 justify-center overflow-y-auto overflow-x-hidden bg-gray-200 p-8 dark:bg-gray-950 items-start"
        >

          <!-- ── PDF canvas ──────────────────────────────────────────── -->
          <div
            v-if="!isDocx"
            id="pdf-container"
            class="relative shadow-2xl bg-white"
            @dragover.prevent
            @drop="onDrop"
          >
            <canvas id="pdf-canvas" class="block"></canvas>
            <component :is="FieldOverlays" :fields="filteredFields" :signers="versionSigners" :selected-id="selectedVersionSignerId" @delete="deleteField" />
          </div>

          <!-- ── DOCX scrollable view ───────────────────────────────── -->
          <!-- Direct flex child (no extra wrapper) — naturally sizes to content height -->
          <div
            v-else
            id="docx-container"
            class="relative shadow-2xl bg-white mb-8"
            :style="{ width: DOCX_PAGE_W + 'px' }"
            @dragover.prevent
            @drop="onDrop"
          >
            <!-- Full document content with A4-like margins -->
            <div
              class="docx-body"
              style="padding: 48px 56px; font-size: 13px; line-height: 1.75; color: #1a1a1a;"
              v-html="docxHtml"
            ></div>

            <!-- Visual page-break dividers (dashed lines between virtual A4 pages) -->
            <div
              v-for="p in totalPages - 1"
              :key="'pb-' + p"
              class="pointer-events-none absolute inset-x-0 z-20"
              :style="{ top: (p * DOCX_PAGE_H) + 'px' }"
            >
              <div class="border-t-2 border-dashed border-blue-300/50 relative">
                <span class="absolute right-3 -top-3 text-[9px] font-semibold text-blue-400/60 bg-white px-1 rounded">
                  page {{ p + 1 }}
                </span>
              </div>
            </div>

            <!-- Signature fields — all pages, absolutely positioned in scroll space -->
            <component
              :is="FieldOverlays"
              :fields="signatureFields"
              :signers="versionSigners"
              :selected-id="selectedVersionSignerId"
              :scroll-mode="true"
              :page-height="DOCX_PAGE_H"
              @delete="deleteField"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Add Signer Modal -->
    <div v-if="showAddSigner" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl w-[480px] shadow-2xl border dark:border-gray-700">
        <h3 class="text-lg font-bold mb-4 dark:text-white">Add Signer to This Version</h3>
        <div class="relative mb-3">
          <input v-model="signerSearch" @input="searchMasterSigners" type="text" placeholder="Search by name, email, or organization..." class="w-full border rounded-lg p-2 dark:bg-gray-900 dark:border-gray-600 dark:text-white pr-8" autofocus />
          <svg class="absolute right-2 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
        </div>
        <div v-if="masterSignerResults.length" class="max-h-44 overflow-y-auto border rounded-lg dark:border-gray-700 mb-3">
          <div v-for="ms in masterSignerResults" :key="ms.id" @click="selectMasterSigner(ms)" class="p-3 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer border-b last:border-0 dark:border-gray-700 transition">
            <div class="font-medium text-sm dark:text-white">{{ ms.name }}</div>
            <div class="text-xs text-gray-500">{{ ms.email }}</div>
            <div v-if="ms.organization" class="text-xs text-gray-400">{{ ms.organization }}</div>
          </div>
        </div>
        <div v-if="signerSearch && !masterSignerResults.length && !searchingSigners" class="text-sm text-gray-400 italic mb-3 text-center py-2">No existing signers match. Create a new one below.</div>
        <div class="relative my-4">
          <div class="absolute inset-0 flex items-center"><div class="w-full border-t dark:border-gray-600"></div></div>
          <div class="relative flex justify-center"><span class="bg-white dark:bg-gray-800 px-2 text-xs text-gray-400">or create new signer</span></div>
        </div>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div><label class="block text-xs font-medium mb-1 dark:text-gray-300">Name *</label><input v-model="newSigner.name" type="text" class="w-full border rounded-lg p-2 text-sm dark:bg-gray-900 dark:border-gray-600 dark:text-white" /></div>
            <div><label class="block text-xs font-medium mb-1 dark:text-gray-300">Email *</label><input v-model="newSigner.email" type="email" class="w-full border rounded-lg p-2 text-sm dark:bg-gray-900 dark:border-gray-600 dark:text-white" /></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="block text-xs font-medium mb-1 dark:text-gray-300">Title</label><input v-model="newSigner.title" type="text" placeholder="e.g. Director" class="w-full border rounded-lg p-2 text-sm dark:bg-gray-900 dark:border-gray-600 dark:text-white" /></div>
            <div><label class="block text-xs font-medium mb-1 dark:text-gray-300">Organization</label><input v-model="newSigner.organization" type="text" class="w-full border rounded-lg p-2 text-sm dark:bg-gray-900 dark:border-gray-600 dark:text-white" /></div>
          </div>
          <p v-if="addSignerError" class="text-red-500 text-xs">{{ addSignerError }}</p>
        </div>
        <div class="mt-5 flex justify-end gap-3">
          <button @click="closeAddSigner" class="px-4 py-2 text-gray-600 dark:text-gray-300">Cancel</button>
          <button @click="addNewSignerToVersion" :disabled="addingNewSigner" class="px-5 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition">
            {{ addingNewSigner ? 'Adding...' : 'Create & Add' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, shallowRef, defineComponent, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { toast, swalError, swalConfirm } from '../utils/swal.js'

let pdfjsLibPromise = null
const loadPdfJsLib = async () => {
  if (!pdfjsLibPromise) {
    pdfjsLibPromise = import('pdfjs-dist')
  }
  const pdfjsLib = await pdfjsLibPromise
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'
  return pdfjsLib
}

// ── A4 page dimensions (px at 96 dpi) ─────────────────────────────────────
const DOCX_PAGE_W = 860   // container width
const DOCX_PAGE_H = 1115  // A4 height ≈ 297mm at 96dpi, slightly reduced for padding

// ── Inline field overlay component ────────────────────────────────────────
const FieldOverlays = defineComponent({
  props: {
    fields:     { type: Array,          default: () => [] },
    signers:    { type: Array,          default: () => [] },
    selectedId: { type: [Number, null], default: null },
    // When true, top = page_number * pageHeight + y_pos (scroll / all-pages mode)
    scrollMode: { type: Boolean,        default: false },
    pageHeight: { type: Number,         default: 1115 },
  },
  emits: ['delete'],
  setup(props, { emit }) {
    const signerName = (vsId) => {
      const vs = props.signers.find(s => s.id === vsId)
      return vs?.master_signer?.name || 'Unassigned'
    }
    return () => props.fields.map(field => {
      const top = props.scrollMode
        ? (field.page_number || 0) * props.pageHeight + field.y_pos
        : field.y_pos
      return h('div', {
        key: field.id,
        class: [
          'absolute border-2 flex items-center justify-center text-[10px] font-bold uppercase transition-all group z-30',
          field.version_signer_id === props.selectedId
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-gray-400 bg-gray-400/10',
        ].join(' '),
        style: { left: `${field.x_pos}px`, top: `${top}px`, width: `${field.width}px`, height: `${field.height}px` },
      }, [
        h('div', { class: 'text-center leading-tight pointer-events-none' }, [
          h('div', {}, field.field_type),
          h('div', { class: 'text-[8px] opacity-60 truncate max-w-[110px]' }, signerName(field.version_signer_id)),
        ]),
        h('button', {
          class: 'absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center opacity-0 group-hover:opacity-100 transition shadow-sm z-40',
          onClick: (e) => { e.stopPropagation(); emit('delete', field.id) },
        }, '×'),
      ])
    })
  },
})

// ── Route / core state ─────────────────────────────────────────────────────
const route  = useRoute()
const router = useRouter()
/** Keep in sync if the route is reused (e.g. query-only changes). */
const contractId = computed(() => route.params.id)

const prepareLoadError = ref('')

const contract               = ref(null)
const currentVersion         = ref(null)
const versionSigners         = ref([])
const signatureFields        = ref([])
const selectedVersionSignerId = ref(null)
const currentPage            = ref(1)
const totalPages             = ref(1)
const pdfDoc                 = shallowRef(null)
const PDF_SCALE              = 1.5
const sending                = ref(false)
const docLoading             = ref(true)

// DOCX
const docxHtml = ref('')

const isDocx = computed(() => {
  let ft = (currentVersion.value?.file_type || '').toLowerCase()
  if (!ft && currentVersion.value?.file_path) {
    ft = currentVersion.value.file_path.split('.').pop().toLowerCase()
  }
  return ft === 'docx' || ft === 'doc'
})

// Signer modal state
const showAddSigner       = ref(false)
const signerSearch        = ref('')
const masterSignerResults = ref([])
const searchingSigners    = ref(false)
const addSignerError      = ref('')
const addingNewSigner     = ref(false)
const newSigner           = ref({ name: '', email: '', title: '', organization: '' })

const tools = [
  { type: 'signature', label: 'Signature', icon: '✍️' },
  { type: 'date',      label: 'Date',      icon: '📅' },
  { type: 'text',      label: 'Text Field', icon: '📄' },
  { type: 'initials',  label: 'Initials',  icon: '🔤' },
]

const selectedVersionSigner = computed(() =>
  versionSigners.value.find(vs => vs.id === selectedVersionSignerId.value) || null
)

// PDF: show only fields on the current visible page.
// DOCX: all fields are visible in the scroller — filtered in the template itself.
const filteredFields = computed(() =>
  signatureFields.value.filter(f => f.page_number === currentPage.value - 1)
)

// ── Drag & drop ────────────────────────────────────────────────────────────
const onDragStartTool = (event, type) => {
  event.dataTransfer.setData('field-type', type)
}

const onDrop = async (event) => {
  if (!selectedVersionSignerId.value) {
    toast('Please select a signer first', 'warning')
    return
  }
  if (!currentVersion.value) return

  const fieldType = event.dataTransfer.getData('field-type')
  const containerId = isDocx.value ? 'docx-container' : 'pdf-container'
  const container   = document.getElementById(containerId)
  if (!container) return

  const rect = container.getBoundingClientRect()
  const x    = Math.max(0, Math.round(event.clientX - rect.left - 75))

  let page_number, y_pos

  if (isDocx.value) {
    // In scroll mode getBoundingClientRect().top shifts as the page scrolls,
    // so clientY - rect.top already gives the absolute y from the content top.
    const absoluteY = Math.max(0, Math.round(event.clientY - rect.top - 25))
    page_number = Math.floor(absoluteY / DOCX_PAGE_H)
    y_pos       = absoluteY % DOCX_PAGE_H
  } else {
    // PDF: y is relative to the current page canvas (no scroll offset needed).
    y_pos       = Math.max(0, Math.round(event.clientY - rect.top - 25))
    page_number = currentPage.value - 1
  }

  try {
    const res = await axios.post(`/api/versions/${currentVersion.value.id}/signature-fields`, {
      version_signer_id: selectedVersionSignerId.value,
      field_type:   fieldType,
      page_number,
      x_pos:        x,
      y_pos,
      width:        150,
      height:       50,
      scale:        isDocx.value ? 1 : PDF_SCALE,
    })
    signatureFields.value.push(res.data)
  } catch (e) {
    console.error('Failed to create field:', e)
    toast('Could not place field', 'error')
  }
}

const deleteField = async (id) => {
  try {
    await axios.delete(`/api/signature-fields/${id}`)
    signatureFields.value = signatureFields.value.filter(f => f.id !== id)
  } catch (e) {
    console.error('Failed to delete field:', e)
  }
}

// ── PDF rendering ──────────────────────────────────────────────────────────
const renderPdf = async () => {
  if (!pdfDoc.value) return
  try {
    const page     = await pdfDoc.value.getPage(currentPage.value)
    const viewport = page.getViewport({ scale: PDF_SCALE })
    const canvas   = document.getElementById('pdf-canvas')
    if (!canvas) return

    // Use devicePixelRatio so the canvas is crisp on HiDPI / Retina screens.
    const dpr = window.devicePixelRatio || 1
    const cssW = viewport.width
    const cssH = viewport.height

    // Physical pixels for the backing buffer
    canvas.width  = Math.round(cssW * dpr)
    canvas.height = Math.round(cssH * dpr)
    // CSS size stays at logical pixels so layout is correct
    canvas.style.width  = `${cssW}px`
    canvas.style.height = `${cssH}px`

    const container = document.getElementById('pdf-container')
    if (container) {
      container.style.width  = `${cssW}px`
      container.style.height = `${cssH}px`
    }

    const ctx = canvas.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    await page.render({ canvasContext: ctx, viewport }).promise
  } catch (err) {
    console.error('PDF render error:', err)
  }
}

// ── DOCX page-count measurement (for page-divider lines) ──────────────────
const measureDocxPages = async () => {
  // Two ticks so v-html fully paints inside docx-container.
  await nextTick()
  await nextTick()

  const container = document.getElementById('docx-container')
  const contentH  = container ? (container.scrollHeight || container.offsetHeight || DOCX_PAGE_H) : DOCX_PAGE_H
  totalPages.value  = Math.max(1, Math.ceil(contentH / DOCX_PAGE_H))
  currentPage.value = 1
}

const loadDocxPreview = async () => {
  try {
    const fileUrl = `/api/contracts/${contractId.value}/file?version_id=${currentVersion.value.id}&t=${Date.now()}`
    const resp = await fetch(fileUrl)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const arrayBuffer = await resp.arrayBuffer()
    const mammoth = await import('mammoth')
    const result = await mammoth.default.convertToHtml({ arrayBuffer })
    docxHtml.value = result.value
    await measureDocxPages()
  } catch (e) {
    console.error('DOCX preview failed:', e)
    const msg = 'Could not load the DOCX preview. The file may be missing or corrupted.'
    prepareLoadError.value = msg
    toast(msg, 'warning')
  }
}

// ── Page navigation ────────────────────────────────────────────────────────
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    if (!isDocx.value) renderPdf()
  }
}
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    if (!isDocx.value) renderPdf()
  }
}

// ── Signer helpers ─────────────────────────────────────────────────────────
const searchMasterSigners = async () => {
  if (!signerSearch.value.trim()) { masterSignerResults.value = []; return }
  searchingSigners.value = true
  try {
    const res = await axios.get('/api/master-signers/', { params: { search: signerSearch.value } })
    const addedIds = versionSigners.value.map(vs => vs.master_signer_id)
    masterSignerResults.value = res.data.filter(ms => !addedIds.includes(ms.id))
  } catch (e) { console.error(e) }
  finally { searchingSigners.value = false }
}

const selectMasterSigner = async (ms) => {
  try {
    const res = await axios.post(`/api/versions/${currentVersion.value.id}/signers`, {
      master_signer_id: ms.id, signing_order: versionSigners.value.length + 1,
    })
    versionSigners.value.push(res.data)
    selectedVersionSignerId.value = res.data.id
    closeAddSigner()
  } catch (e) { addSignerError.value = e.response?.data?.detail || 'Failed to add signer' }
}

const addNewSignerToVersion = async () => {
  if (!newSigner.value.name || !newSigner.value.email) { addSignerError.value = 'Name and email are required.'; return }
  addingNewSigner.value = true; addSignerError.value = ''
  try {
    let ms
    try { const res = await axios.post('/api/master-signers/', newSigner.value); ms = res.data }
    catch (e) {
      if (e.response?.status === 409) {
        const all = await axios.get('/api/master-signers/', { params: { search: newSigner.value.email } })
        ms = all.data.find(s => s.email === newSigner.value.email)
        if (!ms) throw new Error('Could not find signer by email')
      } else throw e
    }
    await selectMasterSigner(ms)
  } catch (e) { addSignerError.value = e.response?.data?.detail || e.message || 'Failed to create signer' }
  finally { addingNewSigner.value = false }
}

const removeSigner = async (vsId) => {
  if (!await swalConfirm('Their signature fields will also be deleted.', 'Remove this signer?', 'Remove')) return
  try {
    await axios.delete(`/api/version-signers/${vsId}`)
    versionSigners.value  = versionSigners.value.filter(vs => vs.id !== vsId)
    signatureFields.value = signatureFields.value.filter(f => f.version_signer_id !== vsId)
    if (selectedVersionSignerId.value === vsId)
      selectedVersionSignerId.value = versionSigners.value[0]?.id || null
    toast('Signer removed from this version.')
  } catch (e) { swalError(e.response?.data?.detail || 'Failed to remove signer') }
}

const closeAddSigner = () => {
  showAddSigner.value = false; signerSearch.value = ''; masterSignerResults.value = []
  addSignerError.value = ''; newSigner.value = { name: '', email: '', title: '', organization: '' }
}

const sendInvitations = async () => {
  if (!currentVersion.value) return
  sending.value = true
  try {
    await axios.post(`/api/versions/${currentVersion.value.id}/send-invitations`)
    router.push(`/contracts/${contractId.value}`)
  } catch (e) { swalError(e.response?.data?.detail || 'Failed to send invitations') }
  finally { sending.value = false }
}

// ── Init / reload when contract or version in URL changes ───────────────────
async function loadPreparePage() {
  prepareLoadError.value = ''
  docLoading.value = true
  pdfDoc.value = null
  docxHtml.value = ''
  try {
    const id = contractId.value
    if (id == null || id === '') {
      prepareLoadError.value = 'Invalid link — contract id is missing.'
      docLoading.value = false
      return
    }

    const contractRes = await axios.get(`/api/contracts/${id}`)
    contract.value = contractRes.data

    const requestedRaw = route.query.version_id
    const requestedNum =
      requestedRaw != null && String(requestedRaw).trim() !== '' ? Number(requestedRaw) : null
    const versions = contract.value.document_versions || []
    const requestedVersion =
      requestedNum != null && !Number.isNaN(requestedNum)
        ? versions.find((v) => Number(v.id) === requestedNum)
        : null
    currentVersion.value =
      requestedVersion ||
      versions.find((v) => v.is_latest) ||
      versions.at(-1) ||
      null

    if (!currentVersion.value) {
      prepareLoadError.value =
        'This contract has no document versions yet. Upload a document on the contract page first.'
      docLoading.value = false
      return
    }

    if (!currentVersion.value.file_id) {
      prepareLoadError.value =
        'This version has no file attached. Upload or attach a document before preparing signatures.'
      docLoading.value = false
      return
    }

    const [signersRes, fieldsRes] = await Promise.all([
      axios.get(`/api/versions/${currentVersion.value.id}/signers`),
      axios.get(`/api/versions/${currentVersion.value.id}/signature-fields`),
    ])
    versionSigners.value = signersRes.data
    signatureFields.value = fieldsRes.data
    selectedVersionSignerId.value =
      versionSigners.value.length > 0 ? versionSigners.value[0].id : null

    let fileType = (currentVersion.value.file_type || '').toLowerCase()
    if (!fileType && currentVersion.value.file_path) {
      fileType = currentVersion.value.file_path.split('.').pop().toLowerCase()
    }

    if (fileType === 'docx' || fileType === 'doc') {
      docLoading.value = false
      await loadDocxPreview()
    } else {
      const pdfUrl = `/api/contracts/${id}/file?version_id=${currentVersion.value.id}`
      const pdfjsLib = await loadPdfJsLib()
      pdfDoc.value = await pdfjsLib.getDocument(pdfUrl).promise
      totalPages.value = pdfDoc.value.numPages
      currentPage.value = 1
      docLoading.value = false
      await nextTick()
      await nextTick()
      await renderPdf()
    }
  } catch (e) {
    console.error('Initialization failed:', e)
    const detail = e?.response?.data?.detail
    prepareLoadError.value =
      typeof detail === 'string'
        ? detail
        : e?.message || 'Failed to load this document for signing preparation.'
    toast(prepareLoadError.value, 'error')
    docLoading.value = false
  }
}

watch(
  () => [route.params.id, route.query.version_id],
  () => loadPreparePage(),
  { immediate: true },
)
</script>

<style scoped>
#doc-scroll-area { scrollbar-width: thin; }

/* DOCX body typography — must match preview-html endpoint styles */
.docx-body :deep(h1) { font-size: 1.5rem;  font-weight: 700; margin: 1rem 0 .5rem; }
.docx-body :deep(h2) { font-size: 1.25rem; font-weight: 700; margin: .85rem 0 .4rem; }
.docx-body :deep(h3) { font-size: 1.05rem; font-weight: 600; margin: .7rem 0 .3rem; }
.docx-body :deep(p)  { margin: .35rem 0; line-height: 1.75; }
.docx-body :deep(ul),
.docx-body :deep(ol) { padding-left: 1.5rem; margin: .35rem 0; }
.docx-body :deep(li) { margin: .15rem 0; }
.docx-body :deep(table) { border-collapse: collapse; width: 100%; margin: .7rem 0; }
.docx-body :deep(td),
.docx-body :deep(th)    { border: 1px solid #d1d5db; padding: .3rem .55rem; font-size: 12px; }
.docx-body :deep(th)    { background: #f9fafb; font-weight: 600; }
.docx-body :deep(strong) { font-weight: 700; }
.docx-body :deep(em)     { font-style: italic; }
</style>
