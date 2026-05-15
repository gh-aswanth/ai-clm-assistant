<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-[300] flex flex-col bg-gray-50 dark:bg-gray-900"
    >
      <!-- ── Top bar ───────────────────────────────────────────────────── -->
      <div class="flex shrink-0 items-center gap-3 border-b border-gray-200 bg-white px-4 py-2.5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <!-- File name -->
        <svg class="h-5 w-5 shrink-0 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <span class="flex-1 truncate text-sm font-bold text-gray-700 dark:text-gray-200">{{ filename }}</span>

        <div class="flex items-center gap-2">
          <!-- Save as version -->
          <button
            v-if="contractId"
            type="button"
            :disabled="saving"
            @click="saveAsVersion"
            class="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-[11px] font-bold text-blue-700 transition hover:bg-blue-100 disabled:opacity-50 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
          >
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
            {{ saving ? 'Saving…' : 'Save as Version' }}
          </button>
          <!-- Download -->
          <button
            type="button"
            :disabled="downloading"
            @click="downloadDocx"
            class="inline-flex items-center gap-1.5 rounded-lg bg-gray-800 px-3 py-1.5 text-[11px] font-bold text-white transition hover:bg-gray-700 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
          >
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            {{ downloading ? 'Exporting…' : 'Download DOCX' }}
          </button>
          <!-- Close -->
          <button
            type="button"
            @click="$emit('update:modelValue', false)"
            class="grid h-8 w-8 place-items-center rounded-full text-gray-400 transition hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-200"
            title="Close editor"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
      </div>

      <!-- ── Toolbar ────────────────────────────────────────────────────── -->
      <div v-if="editor" class="flex shrink-0 flex-wrap items-center gap-0.5 border-b border-gray-200 bg-white px-3 py-1.5 dark:border-gray-700 dark:bg-gray-800">
        <!-- Heading -->
        <select
          class="rounded border-0 bg-transparent py-1 text-[11px] font-semibold text-gray-600 outline-none focus:ring-1 focus:ring-blue-400 dark:text-gray-300"
          @change="applyHeading($event.target.value)"
        >
          <option value="0">Paragraph</option>
          <option value="1">Heading 1</option>
          <option value="2">Heading 2</option>
          <option value="3">Heading 3</option>
        </select>
        <div class="mx-1 h-5 w-px bg-gray-200 dark:bg-gray-600" />
        <!-- Bold -->
        <ToolBtn :active="editor.isActive('bold')" title="Bold (⌘B)" @click="editor.chain().focus().toggleBold().run()">
          <strong class="text-[12px]">B</strong>
        </ToolBtn>
        <!-- Italic -->
        <ToolBtn :active="editor.isActive('italic')" title="Italic (⌘I)" @click="editor.chain().focus().toggleItalic().run()">
          <em class="text-[12px]">I</em>
        </ToolBtn>
        <!-- Underline -->
        <ToolBtn :active="editor.isActive('underline')" title="Underline (⌘U)" @click="editor.chain().focus().toggleUnderline().run()">
          <span class="text-[12px] underline">U</span>
        </ToolBtn>
        <div class="mx-1 h-5 w-px bg-gray-200 dark:bg-gray-600" />
        <!-- Bullet list -->
        <ToolBtn :active="editor.isActive('bulletList')" title="Bullet list" @click="editor.chain().focus().toggleBulletList().run()">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
        </ToolBtn>
        <!-- Ordered list -->
        <ToolBtn :active="editor.isActive('orderedList')" title="Numbered list" @click="editor.chain().focus().toggleOrderedList().run()">
          <svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24"><text x="2" y="8" font-size="8" font-family="monospace">1.</text><text x="2" y="15" font-size="8" font-family="monospace">2.</text><text x="2" y="22" font-size="8" font-family="monospace">3.</text><line x1="12" y1="6" x2="22" y2="6" stroke="currentColor" stroke-width="2"/><line x1="12" y1="13" x2="22" y2="13" stroke="currentColor" stroke-width="2"/><line x1="12" y1="20" x2="22" y2="20" stroke="currentColor" stroke-width="2"/></svg>
        </ToolBtn>
        <div class="mx-1 h-5 w-px bg-gray-200 dark:bg-gray-600" />
        <!-- Align -->
        <ToolBtn title="Align left"   @click="editor.chain().focus().setTextAlign('left').run()"><svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h10M4 18h14"/></svg></ToolBtn>
        <ToolBtn title="Align center" @click="editor.chain().focus().setTextAlign('center').run()"><svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M7 12h10M5 18h14"/></svg></ToolBtn>
        <ToolBtn title="Align right"  @click="editor.chain().focus().setTextAlign('right').run()"><svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M10 12h10M6 18h14"/></svg></ToolBtn>
        <div class="mx-1 h-5 w-px bg-gray-200 dark:bg-gray-600" />
        <!-- Undo / Redo -->
        <ToolBtn title="Undo (⌘Z)" @click="editor.chain().focus().undo().run()">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/></svg>
        </ToolBtn>
        <ToolBtn title="Redo (⌘⇧Z)" @click="editor.chain().focus().redo().run()">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6"/></svg>
        </ToolBtn>
      </div>

      <!-- ── Loading overlay ────────────────────────────────────────────── -->
      <div v-if="loading" class="flex flex-1 flex-col items-center justify-center gap-3">
        <div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <p class="text-sm font-medium text-gray-500">Converting document…</p>
      </div>

      <!-- ── Error state ────────────────────────────────────────────────── -->
      <div v-else-if="loadError" class="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <svg class="h-10 w-10 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
        <p class="text-sm font-bold text-red-600">Failed to load document</p>
        <p class="text-xs text-gray-500">{{ loadError }}</p>
      </div>

      <!-- ── Editor ─────────────────────────────────────────────────────── -->
      <div v-else class="flex flex-1 justify-center overflow-y-auto px-4 py-8">
        <div class="w-full max-w-3xl">
          <EditorContent
            :editor="editor"
            class="docx-editor-content min-h-[calc(100vh-160px)] rounded-xl border border-gray-200 bg-white px-10 py-10 shadow-sm outline-none dark:border-gray-700 dark:bg-gray-800"
          />
        </div>
      </div>

      <!-- ── Status bar ─────────────────────────────────────────────────── -->
      <div class="flex shrink-0 items-center justify-between border-t border-gray-200 bg-white px-4 py-1.5 text-[10px] text-gray-400 dark:border-gray-700 dark:bg-gray-800">
        <span>{{ wordCount }} words</span>
        <span v-if="statusMsg" :class="statusMsg.error ? 'text-red-500' : 'text-emerald-600'">{{ statusMsg.text }}</span>
        <span>{{ filename }}</span>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, computed, onBeforeUnmount, defineComponent, h } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import axios from 'axios'
import { toast, swalError } from '../utils/swal.js'

// ── Inline toolbar button component ───────────────────────────────────────
const ToolBtn = defineComponent({
  props: { active: Boolean, title: String },
  emits: ['click'],
  setup(props, { slots, emit }) {
    return () => h('button', {
      type: 'button',
      title: props.title,
      onClick: (e) => emit('click', e),
      class: [
        'grid h-7 w-7 place-items-center rounded transition text-gray-600 dark:text-gray-300',
        props.active
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
          : 'hover:bg-gray-100 dark:hover:bg-gray-700',
      ].join(' '),
    }, slots.default?.())
  },
})

// ── Props / emits ─────────────────────────────────────────────────────────
const props = defineProps({
  modelValue:  { type: Boolean, default: false },
  docxB64:     { type: String, default: '' },      // base64 DOCX bytes
  filename:    { type: String, default: 'document.docx' },
  contractId:  { type: [String, Number], default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

// ── State ─────────────────────────────────────────────────────────────────
const loading     = ref(false)
const loadError   = ref('')
const downloading = ref(false)
const saving      = ref(false)
const statusMsg   = ref(null)

// ── TipTap editor ─────────────────────────────────────────────────────────
const editor = useEditor({
  extensions: [
    StarterKit,
    Underline,
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
  ],
  content: '',
  editorProps: {
    attributes: { class: 'focus:outline-none prose prose-sm max-w-none dark:prose-invert' },
  },
})

onBeforeUnmount(() => editor.value?.destroy())

const wordCount = computed(() => {
  const text = editor.value?.getText() ?? ''
  return text.trim() ? text.trim().split(/\s+/).length : 0
})

// ── Load DOCX → HTML when modal opens ─────────────────────────────────────
watch(() => props.modelValue, async (open) => {
  if (!open) return
  if (!props.docxB64) { loadError.value = 'No document data provided.'; return }
  loading.value  = true
  loadError.value = ''
  try {
    const { data } = await axios.post('/api/docx-editor/to-html', {
      docx_b64: props.docxB64,
      filename: props.filename,
    })
    editor.value?.commands.setContent(data.html, false)
  } catch (e) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Conversion failed'
  } finally {
    loading.value = false
  }
})

// ── Toolbar helpers ────────────────────────────────────────────────────────
function applyHeading(level) {
  const n = Number(level)
  if (n === 0) editor.value?.chain().focus().setParagraph().run()
  else editor.value?.chain().focus().toggleHeading({ level: n }).run()
}

function showStatus(text, error = false) {
  statusMsg.value = { text, error }
  setTimeout(() => { statusMsg.value = null }, 3000)
}

// ── Export ─────────────────────────────────────────────────────────────────
async function getDocxB64() {
  const html = editor.value?.getHTML() ?? ''
  const { data } = await axios.post('/api/docx-editor/from-html', {
    html,
    filename: props.filename,
  })
  return data.docx_b64
}

async function downloadDocx() {
  downloading.value = true
  try {
    const b64 = await getDocxB64()
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
    const blob  = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = props.filename
    a.click()
    URL.revokeObjectURL(a.href)
    toast('Document downloaded')
    showStatus('Downloaded ✓')
  } catch (e) {
    const msg = e?.response?.data?.detail || 'Export failed'
    swalError(msg)
    showStatus(msg, true)
  } finally {
    downloading.value = false
  }
}

async function saveAsVersion() {
  if (!props.contractId) return
  saving.value = true
  try {
    const b64 = await getDocxB64()
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
    const blob  = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    const form  = new FormData()
    form.append('file', blob, props.filename)
    form.append('label', `Edited — ${new Date().toLocaleString()}`)
    form.append('notes', 'Saved from in-app DOCX editor')
    await axios.post(`/api/contracts/${props.contractId}/upload-version`, form)
    toast('New version saved successfully')
    showStatus('Saved as new version ✓')
    emit('saved')
  } catch (e) {
    const msg = e?.response?.data?.detail || 'Save failed'
    swalError(msg)
    showStatus(msg, true)
  } finally {
    saving.value = false
  }
}
</script>

<style>
.docx-editor-content .ProseMirror {
  outline: none;
}
.docx-editor-content .ProseMirror h1 { font-size: 1.75rem; font-weight: 700; margin: 1rem 0 .5rem; }
.docx-editor-content .ProseMirror h2 { font-size: 1.375rem; font-weight: 700; margin: .875rem 0 .375rem; }
.docx-editor-content .ProseMirror h3 { font-size: 1.125rem; font-weight: 600; margin: .75rem 0 .25rem; }
.docx-editor-content .ProseMirror p  { margin: .375rem 0; line-height: 1.7; }
.docx-editor-content .ProseMirror ul { list-style: disc; padding-left: 1.5rem; margin: .375rem 0; }
.docx-editor-content .ProseMirror ol { list-style: decimal; padding-left: 1.5rem; margin: .375rem 0; }
.docx-editor-content .ProseMirror table { border-collapse: collapse; width: 100%; margin: .75rem 0; }
.docx-editor-content .ProseMirror td,
.docx-editor-content .ProseMirror th { border: 1px solid #e5e7eb; padding: .375rem .625rem; }
.docx-editor-content .ProseMirror th { background: #f9fafb; font-weight: 600; }
</style>
