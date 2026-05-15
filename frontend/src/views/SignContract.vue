<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Review & Sign Document</h1>
        <p class="text-gray-500 mt-1">Please review the document and apply your signatures where indicated.</p>
      </div>
      <div class="text-right">
        <div class="text-lg font-bold text-gray-900 dark:text-white">{{ currentSigner?.name }}</div>
        <div class="text-sm text-gray-500">{{ currentSigner?.email }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Document viewer -->
      <div class="lg:col-span-3 bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden flex flex-col h-[900px]">
        <!-- Toolbar -->
        <div class="p-4 border-b dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900">
          <div class="flex items-center gap-3">
            <span class="font-bold text-gray-700 dark:text-gray-200">Document Review</span>
            <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
            <span v-if="isDocx" class="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">DOCX</span>
          </div>
          <div class="flex items-center gap-3">
            <template v-if="!isDocx">
              <button @click="prevPage" :disabled="currentPage <= 1" class="p-1 disabled:opacity-30 rounded hover:bg-gray-200">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
              </button>
              <span class="text-xs font-medium">Page {{ currentPage }} / {{ totalPages }}</span>
              <button @click="nextPage" :disabled="currentPage >= totalPages" class="p-1 disabled:opacity-30 rounded hover:bg-gray-200">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
              </button>
            </template>
            <template v-else>
              <span class="inline-flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-300">
                <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-3-3v6M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z"/></svg>
                DOCX
                <span class="text-gray-400 font-normal">· {{ totalPages }} page{{ totalPages !== 1 ? 's' : '' }} · scroll to read</span>
              </span>
            </template>
          </div>
        </div>

        <!-- Loading state -->
        <div v-if="loading" class="flex flex-1 items-center justify-center gap-3 flex-col">
          <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
          <p class="text-sm text-gray-500">Loading document…</p>
        </div>

        <!-- Document area: items-start so DOCX grows to content height and overflow-auto scrolls -->
        <div v-else class="flex-1 overflow-auto p-8 flex justify-center items-start bg-gray-100 dark:bg-gray-950" id="doc-scroll-area">

          <!-- ── PDF canvas ──────────────────────────────────────────── -->
          <div v-if="!isDocx" id="pdf-container" class="relative shadow-xl bg-white h-fit">
            <canvas id="pdf-canvas" class="block"></canvas>
            <SignFieldOverlay
              v-for="field in filteredFields" :key="field.id"
              :field="field"
              :signer-name="isTokenMode ? getSignerName(field.version_signer_id) : getSignerName(field.signer_id)"
              :is-mine="isMyField(field)"
              @click="onFieldClick(field)"
            />
          </div>

          <!-- ── DOCX scrollable view (same pattern as Prepare Signature) ── -->
          <div
            v-else
            id="docx-container"
            class="relative shadow-xl bg-white mb-8"
            :style="{ width: DOCX_PAGE_W + 'px' }"
          >
            <div
              class="docx-body"
              style="padding: 48px 56px; font-size: 13px; line-height: 1.75; color: #1a1a1a;"
              v-html="docxHtml"
            ></div>

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

            <SignFieldOverlay
              v-for="field in signatureFields" :key="field.id"
              :field="field"
              :signer-name="isTokenMode ? getSignerName(field.version_signer_id) : getSignerName(field.signer_id)"
              :is-mine="isMyField(field)"
              :scroll-mode="true"
              :page-height="DOCX_PAGE_H"
              @click="onFieldClick(field)"
            />
          </div>
        </div>
      </div>

      <!-- Right: Required Actions -->
      <div class="space-y-6">
        <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 h-[900px] flex flex-col">
          <h3 class="font-bold text-gray-900 dark:text-white mb-4">Required Actions</h3>
          <div class="space-y-3 flex-1 overflow-y-auto pr-2">
            <div
              v-for="field in myFields" :key="field.id"
              @click="goToField(field)"
              class="p-4 border rounded-xl cursor-pointer transition-all transform hover:scale-[1.02]"
              :class="field.is_signed ? 'border-green-100 bg-green-50 dark:bg-green-900/20' : 'border-blue-100 bg-blue-50 dark:bg-blue-900/20 hover:border-blue-300'"
            >
              <div class="flex items-center justify-between">
                <span class="text-sm font-bold capitalize dark:text-gray-200">{{ field.field_type }}</span>
                <span v-if="field.is_signed" class="text-green-600 text-xs font-bold">✓ DONE</span>
                <span v-else class="text-blue-600 text-xs font-bold">PENDING</span>
              </div>
              <div class="text-xs text-gray-500 mt-2 flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                Page {{ field.page_number + 1 }}
              </div>
            </div>
            <div v-if="myFields.length === 0" class="text-center py-10">
              <div class="text-4xl mb-4">🎉</div>
              <p class="text-sm text-gray-500">No actions required for you in this document.</p>
            </div>
          </div>

          <div class="mt-6 pt-6 border-t dark:border-gray-700">
            <button
              @click="submitSigning"
              :disabled="!isAllSigned"
              class="w-full py-4 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 disabled:opacity-50 transition shadow-lg shadow-green-200 dark:shadow-none transform active:scale-95"
            >
              Finish & Complete
            </button>
            <p v-if="!isAllSigned" class="text-[10px] text-center text-gray-400 mt-3 italic">
              Please complete all required fields to finish.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Signature Modal -->
    <div v-if="showSignModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
      <div class="bg-white dark:bg-gray-800 rounded-2xl w-[450px] shadow-2xl overflow-hidden border dark:border-gray-700">
        <div class="p-6 border-b dark:border-gray-700 flex justify-between items-center">
          <h3 class="text-lg font-bold dark:text-white">Adopt Your Signature</h3>
          <button @click="showSignModal = false" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>
        <div class="p-6">
          <div class="mb-4 bg-gray-50 dark:bg-gray-900 rounded-xl border-2 border-dashed border-gray-200 dark:border-gray-700 p-2">
            <canvas ref="sigCanvas" width="400" height="150" class="bg-transparent cursor-crosshair touch-none"
              @mousedown="startDrawing" @mousemove="draw" @mouseup="stopDrawing"
              @touchstart="handleTouchStart" @touchmove="handleTouchMove" @touchend="stopDrawing"
            ></canvas>
          </div>
          <div class="flex justify-between items-center">
            <button @click="clearSignature" class="text-sm text-red-500 hover:text-red-700 font-medium">Clear Canvas</button>
            <div class="text-xs text-gray-400">Sign using mouse or touch</div>
          </div>
          <div class="mt-8 space-y-4">
            <p class="text-[10px] text-gray-500 leading-relaxed">
              By clicking "Adopt and Sign", I agree that the signature and initials will be the electronic representation of my signature and initials for all purposes when I (or my agent) use them on documents, including legally binding contracts - just the same as a pen-and-paper signature or initial.
            </p>
            <button @click="saveSignature" class="w-full py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-lg shadow-blue-200 dark:shadow-none">
              Adopt and Sign
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Date/Text Input Modal -->
    <div v-if="showInputModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
      <div class="bg-white dark:bg-gray-800 rounded-2xl w-96 shadow-2xl overflow-hidden border dark:border-gray-700 p-6">
        <h3 class="text-lg font-bold mb-4 dark:text-white capitalize">Enter {{ activeField?.field_type }}</h3>
        <input v-model="inputValue" :type="activeField?.field_type === 'date' ? 'date' : 'text'"
          class="w-full border rounded-xl p-3 mb-6 dark:bg-gray-900 dark:border-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
          ref="modalInput"
        />
        <div class="flex gap-3">
          <button @click="showInputModal = false" class="flex-1 py-2 text-gray-600 font-medium">Cancel</button>
          <button @click="saveInputValue" class="flex-1 py-2 bg-blue-600 text-white rounded-lg font-bold">Apply</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, shallowRef, defineComponent, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { toast } from '../utils/swal.js'

let pdfjsLibPromise = null
const loadPdfJsLib = async () => {
  if (!pdfjsLibPromise) {
    pdfjsLibPromise = import('pdfjs-dist')
  }
  const pdfjsLib = await pdfjsLibPromise
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'
  return pdfjsLib
}

// ── A4 virtual page constants ──────────────────────────────────────────────
const DOCX_PAGE_W = 860
const DOCX_PAGE_H = 1115

// ── Inline field overlay component ────────────────────────────────────────
const SignFieldOverlay = defineComponent({
  props: {
    field:      { type: Object,  required: true },
    signerName: { type: String,  default: '' },
    isMine:     { type: Boolean, default: false },
    /** When true, top = page_number * pageHeight + y_pos (full DOCX scroll) */
    scrollMode: { type: Boolean, default: false },
    pageHeight: { type: Number,  default: 1115 },
  },
  emits: ['click'],
  setup(props, { emit }) {
    return () => h('div', {
      class: [
        'absolute border-2 border-dashed flex items-center justify-center transition-all group z-30',
        props.field.is_signed
          ? 'border-green-500 bg-green-500/10'
          : props.isMine
            ? 'border-blue-500 bg-blue-500/10 animate-pulse cursor-pointer'
            : 'border-gray-400 bg-gray-400/10 cursor-default',
      ].join(' '),
      style: {
        left:   `${props.field.x_pos}px`,
        top:    `${props.scrollMode ? (props.field.page_number || 0) * props.pageHeight + props.field.y_pos : props.field.y_pos}px`,
        width:  `${props.field.width}px`,
        height: `${props.field.height}px`,
      },
      onClick: () => emit('click'),
    }, [
      h('div', {
        class: 'absolute -top-5 left-0 text-[10px] font-bold text-gray-500 whitespace-nowrap bg-white/80 px-1 rounded',
      }, props.signerName),
      props.field.is_signed
        ? (props.field.field_type === 'signature'
          ? h('div', { class: 'w-full h-full flex items-center justify-center p-1' },
              [h('img', { src: props.field.value, class: 'max-w-full max-h-full object-contain' })])
          : h('div', { class: 'text-xs font-bold text-green-700 text-center w-full break-words px-1' }, props.field.value))
        : h('div', { class: 'text-[10px] font-bold text-blue-600 uppercase text-center pointer-events-none' },
            `Click to ${props.field.field_type}`),
    ])
  },
})

// ── Route / state ──────────────────────────────────────────────────────────
const route           = useRoute()
const router          = useRouter()
const token           = route.params.token || null
const legacyContractId = route.params.id || null
const legacySignerId  = route.params.signerId ? parseInt(route.params.signerId) : null
const isTokenMode     = !!token

const contractId      = ref(legacyContractId)
const signingContext  = ref(null)
const contract        = ref(null)
const signers         = ref([])
const signatureFields = ref([])
const currentPage     = ref(1)
const totalPages      = ref(1)
const pdfDoc          = shallowRef(null)
const PDF_SCALE       = 1.5
const loading         = ref(true)

// DOCX
const docxHtml = ref('')
const fileType = ref('pdf')

const isDocx = computed(() => {
  const t = fileType.value.toLowerCase()
  return t === 'docx' || t === 'doc'
})

// Modals
const showSignModal  = ref(false)
const showInputModal = ref(false)
const activeField    = ref(null)
const inputValue     = ref('')
const sigCanvas      = ref(null)
const isDrawing      = ref(false)

// ── Computed ───────────────────────────────────────────────────────────────
const myVersionSignerId = computed(() => signingContext.value?.version_signer?.id || null)

const currentSigner = computed(() => {
  if (isTokenMode) return signingContext.value?.version_signer?.master_signer || null
  return signers.value.find(s => s.id == legacySignerId) || null
})

const getSignerName = (fieldSignerId) => {
  if (isTokenMode) {
    const vs = signingContext.value?.all_version_signers?.find(s => s.id == fieldSignerId)
    return vs?.master_signer?.name || 'Unknown'
  }
  return signers.value.find(s => s.id == fieldSignerId)?.name || 'Unknown'
}

const isMyField = (field) =>
  isTokenMode
    ? field.version_signer_id == myVersionSignerId.value
    : field.signer_id == legacySignerId

const myFields = computed(() =>
  isTokenMode
    ? signatureFields.value.filter(f => f.version_signer_id == myVersionSignerId.value)
    : signatureFields.value.filter(f => f.signer_id == legacySignerId)
)

const filteredFields = computed(() =>
  signatureFields.value.filter(f => f.page_number === currentPage.value - 1)
)

const isAllSigned = computed(() => myFields.value.every(f => f.is_signed))

// ── PDF rendering ──────────────────────────────────────────────────────────
const renderPdf = async () => {
  if (!pdfDoc.value) return
  try {
    const page     = await pdfDoc.value.getPage(currentPage.value)
    const viewport = page.getViewport({ scale: PDF_SCALE })
    const canvas   = document.getElementById('pdf-canvas')
    if (!canvas) return
    canvas.height = viewport.height
    canvas.width  = viewport.width
    const c = document.getElementById('pdf-container')
    if (c) { c.style.width = `${viewport.width}px`; c.style.height = `${viewport.height}px` }
    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise
  } catch (err) { console.error('PDF render error:', err) }
}

// ── DOCX virtual page count (for toolbar + dashed dividers) ────────────────
const measureDocxPages = async () => {
  await nextTick()
  await nextTick()
  const container = document.getElementById('docx-container')
  const contentH = container ? (container.scrollHeight || container.offsetHeight || DOCX_PAGE_H) : DOCX_PAGE_H
  totalPages.value = Math.max(1, Math.ceil(contentH / DOCX_PAGE_H))
  currentPage.value = 1
}

const loadDocxPreview = async (versionId) => {
  try {
    const fileUrl = `/api/contracts/${contractId.value}/file?version_id=${versionId}&t=${Date.now()}`
    const resp = await fetch(fileUrl)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const arrayBuffer = await resp.arrayBuffer()
    const mammoth = await import('mammoth')
    const result = await mammoth.default.convertToHtml({ arrayBuffer })
    docxHtml.value = result.value
    await measureDocxPages()
  } catch (e) {
    console.error('DOCX preview failed:', e)
    toast('Could not load DOCX preview', 'warning')
  }
}

// ── Navigation ─────────────────────────────────────────────────────────────
const prevPage = () => {
  if (currentPage.value > 1) { currentPage.value--; if (!isDocx.value) renderPdf() }
}
const nextPage = () => {
  if (currentPage.value < totalPages.value) { currentPage.value++; if (!isDocx.value) renderPdf() }
}

const goToField = async (field) => {
  if (isDocx.value) {
    await nextTick()
    const scrollEl = document.getElementById('doc-scroll-area')
    const top = (field.page_number || 0) * DOCX_PAGE_H + (field.y_pos || 0)
    scrollEl?.scrollTo({ top: Math.max(0, top - 100), behavior: 'smooth' })
    return
  }
  currentPage.value = field.page_number + 1
  await renderPdf()
}

// ── Field interaction ──────────────────────────────────────────────────────
const onFieldClick = (field) => {
  if (!isMyField(field) || field.is_signed) return
  activeField.value = field
  if (field.field_type === 'signature') {
    showSignModal.value = true
    nextTick(() => clearSignature())
  } else {
    inputValue.value    = field.field_type === 'date' ? new Date().toISOString().split('T')[0] : ''
    showInputModal.value = true
  }
}

// ── Drawing ────────────────────────────────────────────────────────────────
const startDrawing = (e) => {
  isDrawing.value = true
  const rect = sigCanvas.value.getBoundingClientRect()
  const ctx  = sigCanvas.value.getContext('2d')
  ctx.beginPath(); ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top)
}
const draw = (e) => {
  if (!isDrawing.value) return
  const rect = sigCanvas.value.getBoundingClientRect()
  const ctx  = sigCanvas.value.getContext('2d')
  ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top); ctx.stroke()
}
const handleTouchStart = (e) => { e.preventDefault(); const t = e.touches[0]; startDrawing({ clientX: t.clientX, clientY: t.clientY }) }
const handleTouchMove  = (e) => { e.preventDefault(); const t = e.touches[0]; draw({ clientX: t.clientX, clientY: t.clientY }) }
const stopDrawing      = () => { isDrawing.value = false }
const clearSignature   = () => {
  const canvas = sigCanvas.value; if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.lineWidth = 2; ctx.lineCap = 'round'; ctx.strokeStyle = '#000'
}

// ── Save / submit ──────────────────────────────────────────────────────────
const saveSignature = async () => {
  await updateField(activeField.value.id, sigCanvas.value.toDataURL())
  showSignModal.value = false
}
const saveInputValue = async () => {
  if (!inputValue.value) return
  await updateField(activeField.value.id, inputValue.value)
  showInputModal.value = false
}
const updateField = async (fieldId, value) => {
  try {
    const res = await axios.patch(`/api/signature-fields/${fieldId}`, { value, is_signed: true })
    const idx = signatureFields.value.findIndex(f => f.id === fieldId)
    if (idx !== -1) signatureFields.value[idx] = res.data
  } catch (e) { console.error('Failed to update field:', e) }
}

const submitSigning = async () => {
  try {
    if (isTokenMode) {
      await axios.post(`/api/sign/${token}/complete`)
      toast('Document signed successfully!')
      router.push(`/contracts/${contractId.value}`)
    } else {
      await axios.post(`/api/signers/${legacySignerId}/sign`)
      router.push(`/contracts/${legacyContractId}`)
    }
  } catch (e) { console.error('Failed to submit signing:', e) }
}

// ── Init ───────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    if (isTokenMode) {
      const ctxRes = await axios.get(`/api/sign/${token}`)
      signingContext.value  = ctxRes.data
      contractId.value      = ctxRes.data.contract_id
      signatureFields.value = ctxRes.data.signature_fields
      fileType.value        = ctxRes.data.file_type || 'pdf'

      if (isDocx.value) {
        loading.value = false
        await loadDocxPreview(ctxRes.data.version_id)
      } else {
        const pdfUrl = `/api/contracts/${ctxRes.data.contract_id}/file?version_id=${ctxRes.data.version_id}`
        const pdfjsLib = await loadPdfJsLib()
        pdfDoc.value = await pdfjsLib.getDocument(pdfUrl).promise
        totalPages.value = pdfDoc.value.numPages
        loading.value    = false
        await nextTick(); await renderPdf()
      }
    } else {
      // Legacy path
      const res = await axios.get(`/api/contracts/${legacyContractId}`)
      contract.value        = res.data
      signers.value         = contract.value.signers
      signatureFields.value = contract.value.signature_fields
      const latest = contract.value.document_versions?.find(v => v.is_latest) || contract.value.document_versions?.at(-1)
      fileType.value = (latest?.file_type || contract.value.file_type || 'pdf')

      if (isDocx.value) {
        contractId.value = legacyContractId
        loading.value    = false
        await loadDocxPreview(latest?.id)
      } else {
        const pdfUrl = `/api/contracts/${legacyContractId}/file`
        const pdfjsLib = await loadPdfJsLib()
        pdfDoc.value = await pdfjsLib.getDocument(pdfUrl).promise
        totalPages.value = pdfDoc.value.numPages
        loading.value    = false
        await nextTick(); await renderPdf()
      }
    }
  } catch (e) {
    console.error('Initialization failed:', e)
    loading.value = false
  }
})
</script>

<style scoped>
#doc-scroll-area { scrollbar-width: thin; }

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
