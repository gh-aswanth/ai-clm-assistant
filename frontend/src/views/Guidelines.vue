<template>
  <div class="gl-view flex min-h-0 gap-7">

    <!-- ── Left rail: frameworks ───────────────────────────────────── -->
    <aside class="gl-rail flex w-[15.5rem] shrink-0 flex-col gap-3">
      <div class="gl-rail__top">
        <p class="gl-rail__eyebrow">Frameworks</p>
        <button type="button" @click="openCreateFramework" class="gl-btn gl-btn--primary gl-btn--block">
          <svg class="gl-ico" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.25" d="M12 4v16m8-8H4"/></svg>
          New guideline
        </button>
      </div>

      <div v-if="frameworksLoading" class="gl-rail__loading">Loading…</div>
      <nav v-else class="gl-rail__list">
        <button
          v-for="fw in frameworks"
          :key="fw.slug"
          type="button"
          @click="selectFramework(fw.slug)"
          class="gl-fw"
          :class="{ 'gl-fw--active': activeSlug === fw.slug }"
        >
          <span class="gl-fw__dot" aria-hidden="true" />
          <span class="gl-fw__body">
            <span class="gl-fw__title">{{ fw.title }}</span>
            <span class="gl-fw__slug font-mono">{{ fw.slug }}</span>
            <span class="gl-fw__badges">
              <span v-if="fw.is_default" class="gl-badge gl-badge--ok">Default</span>
              <span v-if="fw.version_label" class="gl-badge">v{{ fw.version_label }}</span>
            </span>
          </span>
        </button>
        <p v-if="!frameworks.length" class="gl-rail__empty">No guidelines yet.</p>
      </nav>
    </aside>

    <!-- ── Main workspace ────────────────────────────────────────────── -->
    <div class="gl-workspace min-w-0 flex-1 space-y-5">

      <div v-if="bundleLoading" class="gl-panel gl-panel--ghost gl-state">
        <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--clm-brand)] border-t-transparent" />
        <span>Loading guideline…</span>
      </div>
      <div v-else-if="!bundle && !bundleLoading" class="gl-panel gl-panel--dashed gl-state gl-state--tall">
        <div class="gl-state__icon">
          <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        </div>
        <p class="gl-state__title">Select or create a framework</p>
        <p class="gl-state__hint">Choose a pack from the rail or start a new one.</p>
      </div>

      <template v-else-if="bundle">
        <!-- Hero / reference -->
        <header class="gl-hero">
          <div class="gl-hero__glow" aria-hidden="true" />
          <div class="gl-hero__top">
            <span class="gl-hero__label">Reference</span>
            <div class="gl-hero__actions">
              <button type="button" @click="openEditFramework" class="gl-btn gl-btn--quiet">Edit</button>
              <button type="button" @click="confirmDeleteFramework" class="gl-btn gl-btn--danger">Delete</button>
            </div>
          </div>
          <h1 class="gl-hero__title">{{ bundle.framework.title }}</h1>
          <p v-if="bundle.framework.summary" class="gl-hero__summary">{{ bundle.framework.summary }}</p>
          <div class="gl-hero__meta">
            <span v-if="bundle.framework.version_label" class="gl-pill">v{{ bundle.framework.version_label }}</span>
            <span class="gl-pill gl-pill--mono">{{ bundle.framework.slug }}</span>
            <span v-if="bundle.framework.is_default" class="gl-pill gl-pill--accent">Default</span>
          </div>
        </header>

        <div class="gl-stack">
          <article
            v-for="sec in bundle.sections"
            :key="sec.id"
            class="gl-sec"
          >
            <div class="gl-sec__head">
              <div class="gl-sec__lead">
                <span class="gl-sec__orbit" aria-hidden="true" />
                <div class="gl-sec__titles">
                  <span class="gl-sec__key font-mono">{{ sec.section_key }}</span>
                  <h2 class="gl-sec__title">{{ sec.title }}</h2>
                </div>
              </div>
              <div class="gl-sec__tools">
                <button type="button" @click="toggleSection(sec.id)" class="gl-btn gl-btn--quiet gl-btn--sm">
                  {{ openSections.has(sec.id) ? 'Collapse' : 'Edit' }}
                </button>
                <button type="button" @click="confirmDeleteSection(sec)" class="gl-icon-btn gl-icon-btn--danger" title="Delete section">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
              </div>
            </div>

            <div v-if="openSections.has(sec.id)" class="gl-sec__editor">
              <GuidelineFieldEditor
                :data="editingBodies[sec.id]"
                :depth="0"
                @change="editingBodies[sec.id] = $event"
              />
              <footer class="gl-sec__footer">
                <span v-if="savingSection === sec.id" class="gl-sec__saving">Saving…</span>
                <div class="gl-sec__footer-btns">
                  <button type="button" @click="resetSection(sec)" class="gl-btn gl-btn--quiet gl-btn--sm">Reset</button>
                  <button type="button" @click="saveSection(sec)" :disabled="savingSection === sec.id" class="gl-btn gl-btn--primary gl-btn--sm">Save</button>
                </div>
              </footer>
            </div>

            <div v-else class="gl-sec__preview">
              <span v-for="(v, k) in flatPreview(sec.body)" :key="k" class="gl-kv">
                <span class="gl-kv__k">{{ humanize(k) }}</span>
                <span class="gl-kv__v">{{ v }}</span>
              </span>
            </div>
          </article>

          <button type="button" @click="openAddSection" class="gl-add-sec">
            <span class="gl-add-sec__icon"><svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg></span>
            <span class="gl-add-sec__text">Add section</span>
          </button>
        </div>
      </template>
    </div>
  </div>

  <!-- ── Create / Edit Framework Modal ──────────────────────────────── -->
  <div v-if="showFrameworkModal" class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="showFrameworkModal = false">
    <div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-900 shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between border-b border-gray-100 dark:border-gray-700 px-5 py-3.5">
        <h3 class="text-xs font-black uppercase tracking-widest text-gray-800 dark:text-white">{{ frameworkModalMode === 'create' ? 'New Guideline Framework' : 'Edit Framework' }}</h3>
        <button @click="showFrameworkModal = false" class="text-gray-400 hover:text-gray-600">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="space-y-3 p-5">
        <div>
          <label class="block text-[10px] font-bold uppercase text-gray-500 mb-1">Title *</label>
          <input v-model="fwForm.title" type="text" placeholder="CPWD-aligned contract review guideline" class="gl-input" />
        </div>
        <div v-if="frameworkModalMode === 'create'">
          <label class="block text-[10px] font-bold uppercase text-gray-500 mb-1">Slug * <span class="text-[9px] font-normal normal-case">(unique identifier)</span></label>
          <input v-model="fwForm.slug" type="text" placeholder="cpwd-v2" class="gl-input font-mono" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-[10px] font-bold uppercase text-gray-500 mb-1">Version</label>
            <input v-model="fwForm.version_label" type="text" placeholder="1.0" class="gl-input" />
          </div>
          <div class="flex items-end pb-1.5">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="fwForm.is_default" class="h-4 w-4 accent-[var(--clm-brand)]" />
              <span class="text-[11px] font-semibold text-gray-700 dark:text-gray-300">Set as default</span>
            </label>
          </div>
        </div>
        <div>
          <label class="block text-[10px] font-bold uppercase text-gray-500 mb-1">Summary</label>
          <textarea v-model="fwForm.summary" rows="3" placeholder="Brief description…" class="gl-input resize-none"></textarea>
        </div>
      </div>
      <div class="flex gap-2 border-t border-gray-100 dark:border-gray-700 px-5 py-3.5">
        <button type="button" @click="showFrameworkModal = false" class="flex-1 rounded-xl border border-gray-200 dark:border-gray-700 py-2 text-xs font-bold text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition uppercase">Cancel</button>
        <button type="button" @click="submitFrameworkForm" :disabled="fwSubmitting || !fwForm.title.trim()" class="flex-1 rounded-xl py-2 text-xs font-bold text-white disabled:opacity-50 transition" style="background:var(--clm-brand)">
          {{ fwSubmitting ? 'Saving…' : frameworkModalMode === 'create' ? 'Create' : 'Save changes' }}
        </button>
      </div>
    </div>
  </div>

  <!-- ── Add Section Modal ──────────────────────────────────────────── -->
  <div v-if="showSectionModal" class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="showSectionModal = false">
    <div class="w-full max-w-sm rounded-2xl bg-white dark:bg-gray-900 shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between border-b border-gray-100 dark:border-gray-700 px-5 py-3.5">
        <h3 class="text-xs font-black uppercase tracking-widest text-gray-800 dark:text-white">Add Section</h3>
        <button @click="showSectionModal = false" class="text-gray-400 hover:text-gray-600"><svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
      </div>
      <div class="space-y-3 p-5">
        <div>
          <label class="block text-[10px] font-bold uppercase text-gray-500 mb-1">Section key * <span class="text-[9px] font-normal normal-case">(snake_case)</span></label>
          <input v-model="secForm.section_key" type="text" placeholder="financial_limits" class="gl-input font-mono" />
        </div>
        <div>
          <label class="block text-[10px] font-bold uppercase text-gray-500 mb-1">Title *</label>
          <input v-model="secForm.title" type="text" placeholder="Financial Limits" class="gl-input" />
        </div>
        <div>
          <label class="block text-[10px] font-bold uppercase text-gray-500 mb-1">Sort order</label>
          <input v-model.number="secForm.sort_order" type="number" class="gl-input w-24" />
        </div>
      </div>
      <div class="flex gap-2 border-t border-gray-100 dark:border-gray-700 px-5 py-3.5">
        <button type="button" @click="showSectionModal = false" class="flex-1 rounded-xl border border-gray-200 py-2 text-xs font-bold text-gray-600 hover:bg-gray-50 transition uppercase">Cancel</button>
        <button type="button" @click="submitAddSection" :disabled="secSubmitting || !secForm.section_key.trim() || !secForm.title.trim()" class="flex-1 rounded-xl py-2 text-xs font-bold text-white disabled:opacity-50 transition" style="background:var(--clm-brand)">
          {{ secSubmitting ? 'Adding…' : 'Add section' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import GuidelineFieldEditor from '../components/GuidelineFieldEditor.vue'
import { toast, swalError } from '../utils/swal.js'

const route = useRoute()
const router = useRouter()

// ── Framework list ──────────────────────────────────────────────────────────
const frameworks = ref([])
const frameworksLoading = ref(true)
const activeSlug = ref('')

async function loadFrameworks() {
  frameworksLoading.value = true
  try {
    const { data } = await axios.get('/api/guidelines/frameworks')
    frameworks.value = data || []
    if (!activeSlug.value && data.length) {
      const def = data.find(f => f.is_default) || data[0]
      await selectFramework(def.slug)
    }
  } finally {
    frameworksLoading.value = false
  }
}

// ── Bundle / sections ───────────────────────────────────────────────────────
const bundle = ref(null)
const bundleLoading = ref(false)
const openSections = ref(new Set())
const editingBodies = reactive({})
const savingSection = ref(null)

async function selectFramework(slug) {
  activeSlug.value = slug
  router.replace({ query: { framework: slug } })
  bundleLoading.value = true
  bundle.value = null
  openSections.value = new Set()
  try {
    const { data } = await axios.get(`/api/guidelines/frameworks/${encodeURIComponent(slug)}/bundle`)
    bundle.value = data
    for (const sec of data.sections) {
      editingBodies[sec.id] = JSON.parse(JSON.stringify(sec.body))
    }
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to load guideline')
  } finally {
    bundleLoading.value = false
  }
}

function toggleSection(id) {
  const s = new Set(openSections.value)
  s.has(id) ? s.delete(id) : s.add(id)
  openSections.value = s
}

function resetSection(sec) {
  editingBodies[sec.id] = JSON.parse(JSON.stringify(sec.body))
}

async function saveSection(sec) {
  savingSection.value = sec.id
  try {
    const { data } = await axios.patch(
      `/api/guidelines/frameworks/${activeSlug.value}/sections/${sec.id}`,
      { body: editingBodies[sec.id] }
    )
    const idx = bundle.value.sections.findIndex(s => s.id === sec.id)
    if (idx !== -1) bundle.value.sections[idx] = data
    editingBodies[sec.id] = JSON.parse(JSON.stringify(data.body))
    toast('Section saved.')
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to save section.')
  } finally {
    savingSection.value = null
  }
}

async function confirmDeleteSection(sec) {
  if (!confirm(`Delete section "${sec.title}"?`)) return
  try {
    await axios.delete(`/api/guidelines/frameworks/${activeSlug.value}/sections/${sec.id}`)
    bundle.value.sections = bundle.value.sections.filter(s => s.id !== sec.id)
    delete editingBodies[sec.id]
    toast('Section deleted.')
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to delete section.')
  }
}

// ── Framework CRUD ──────────────────────────────────────────────────────────
const showFrameworkModal = ref(false)
const frameworkModalMode = ref('create')
const fwSubmitting = ref(false)
const fwForm = reactive({ slug: '', title: '', summary: '', version_label: '', is_default: false })

function openCreateFramework() {
  frameworkModalMode.value = 'create'
  Object.assign(fwForm, { slug: '', title: '', summary: '', version_label: '', is_default: false })
  showFrameworkModal.value = true
}
function openEditFramework() {
  frameworkModalMode.value = 'edit'
  const fw = bundle.value.framework
  Object.assign(fwForm, { slug: fw.slug, title: fw.title, summary: fw.summary || '', version_label: fw.version_label || '', is_default: fw.is_default })
  showFrameworkModal.value = true
}
async function submitFrameworkForm() {
  fwSubmitting.value = true
  try {
    if (frameworkModalMode.value === 'create') {
      const { data } = await axios.post('/api/guidelines/frameworks', {
        slug: fwForm.slug, title: fwForm.title, summary: fwForm.summary || null,
        version_label: fwForm.version_label || null, is_default: fwForm.is_default,
      })
      frameworks.value.push(data)
      showFrameworkModal.value = false
      await selectFramework(data.slug)
    } else {
      const { data } = await axios.patch(`/api/guidelines/frameworks/${activeSlug.value}`, {
        title: fwForm.title, summary: fwForm.summary || null,
        version_label: fwForm.version_label || null, is_default: fwForm.is_default,
      })
      bundle.value.framework = data
      const fi = frameworks.value.findIndex(f => f.slug === activeSlug.value)
      if (fi !== -1) frameworks.value[fi] = data
      showFrameworkModal.value = false
      toast('Framework updated.')
    }
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to save framework.')
  } finally {
    fwSubmitting.value = false
  }
}
async function confirmDeleteFramework() {
  if (!confirm(`Delete framework "${bundle.value.framework.title}"? This cannot be undone.`)) return
  try {
    await axios.delete(`/api/guidelines/frameworks/${activeSlug.value}`)
    frameworks.value = frameworks.value.filter(f => f.slug !== activeSlug.value)
    bundle.value = null
    activeSlug.value = ''
    if (frameworks.value.length) await selectFramework(frameworks.value[0].slug)
    toast('Framework deleted.')
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to delete framework.')
  }
}

// ── Add Section ─────────────────────────────────────────────────────────────
const showSectionModal = ref(false)
const secSubmitting = ref(false)
const secForm = reactive({ section_key: '', title: '', sort_order: 0 })

function openAddSection() {
  Object.assign(secForm, { section_key: '', title: '', sort_order: (bundle.value?.sections?.length || 0) * 10 })
  showSectionModal.value = true
}
async function submitAddSection() {
  secSubmitting.value = true
  try {
    const { data } = await axios.post(`/api/guidelines/frameworks/${activeSlug.value}/sections`, {
      section_key: secForm.section_key, title: secForm.title, sort_order: secForm.sort_order, body: {},
    })
    bundle.value.sections.push(data)
    editingBodies[data.id] = {}
    openSections.value = new Set([...openSections.value, data.id])
    showSectionModal.value = true
    showSectionModal.value = false
    toast('Section added.')
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to add section.')
  } finally {
    secSubmitting.value = false
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function humanize(k) { return String(k).replace(/_/g, ' ') }

function flatPreview(body, depth = 0, out = {}) {
  if (!body || typeof body !== 'object') return out
  for (const [k, v] of Object.entries(body)) {
    if (v !== null && typeof v === 'object' && !Array.isArray(v) && depth < 1) {
      flatPreview(v, depth + 1, out)
    } else if (Array.isArray(v)) {
      out[k] = v.join(', ')
    } else {
      out[k] = v
    }
    if (Object.keys(out).length >= 6) break
  }
  return out
}

onMounted(async () => {
  const q = route.query.framework
  if (typeof q === 'string' && q.trim()) activeSlug.value = q.trim()
  await loadFrameworks()
  if (activeSlug.value && !bundle.value) await selectFramework(activeSlug.value)
})

watch(() => route.query.framework, async (slug) => {
  if (slug && slug !== activeSlug.value) await selectFramework(String(slug))
})
</script>

<style scoped>
/* ── Page shell ─────────────────────────────────────────────── */
.gl-view {
  --gl-brand: var(--clm-brand, #2563eb);
  --gl-brand-soft: color-mix(in srgb, var(--gl-brand) 14%, transparent);
  --gl-text: var(--clm-text, #0f172a);
  --gl-muted: var(--clm-text-muted, #64748b);
  --gl-border: var(--clm-border, #e2e8f0);
  --gl-surface: var(--clm-bg-surface, #fff);
  --gl-elev: var(--clm-bg-surface-elevated, #f8fafc);
  --gl-overlay: var(--clm-bg-overlay, #f1f5f9);
}

/* Rail */
.gl-rail {
  padding-top: 0.15rem;
}
.gl-rail__top {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.gl-rail__eyebrow {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--gl-muted);
  margin: 0;
  padding-left: 0.15rem;
}
.gl-rail__loading,
.gl-rail__empty {
  text-align: center;
  font-size: 11px;
  color: var(--gl-muted);
  padding: 1.25rem 0.5rem;
}
.gl-rail__list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  max-height: calc(100vh - 12rem);
  overflow-y: auto;
  padding-right: 0.15rem;
}

.gl-fw {
  display: flex;
  gap: 0.5rem;
  width: 100%;
  text-align: left;
  padding: 0.55rem 0.6rem 0.6rem 0.5rem;
  border-radius: 0.75rem;
  border: 1px solid var(--gl-border);
  background: var(--gl-surface);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.2s, transform 0.15s;
}
.gl-fw:hover {
  border-color: color-mix(in srgb, var(--gl-brand) 28%, var(--gl-border));
  box-shadow: 0 6px 18px -12px color-mix(in srgb, var(--gl-text) 22%, transparent);
}
.gl-fw--active {
  border-color: color-mix(in srgb, var(--gl-brand) 55%, var(--gl-border));
  background: color-mix(in srgb, var(--gl-brand) 8%, var(--gl-surface));
  box-shadow: 0 8px 22px -14px color-mix(in srgb, var(--gl-brand) 35%, transparent);
}
.gl-fw__dot {
  width: 6px;
  border-radius: 999px;
  background: var(--gl-border);
  flex-shrink: 0;
  margin-top: 0.35rem;
  align-self: stretch;
  max-height: 2.25rem;
  transition: background 0.15s;
}
.gl-fw--active .gl-fw__dot {
  background: linear-gradient(180deg, var(--gl-brand), color-mix(in srgb, var(--gl-brand) 45%, transparent));
}
.gl-fw__body {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.gl-fw__title {
  font-size: 12px;
  font-weight: 700;
  line-height: 1.25;
  color: var(--gl-text);
}
.gl-fw--active .gl-fw__title {
  color: var(--gl-brand);
}
.gl-fw__slug {
  font-size: 9px;
  color: var(--gl-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gl-fw__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.1rem;
}
.gl-badge {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  background: var(--gl-overlay);
  color: var(--gl-muted);
}
.gl-badge--ok {
  background: color-mix(in srgb, #10b981 16%, transparent);
  color: #047857;
}
:global(.dark) .gl-badge--ok {
  color: #6ee7b7;
}

/* Buttons */
.gl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.45rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, color 0.12s, opacity 0.12s;
}
.gl-btn--block {
  width: 100%;
}
.gl-btn--primary {
  background: var(--gl-brand);
  color: #fff;
}
.gl-btn--primary:hover:not(:disabled) {
  filter: brightness(1.06);
}
.gl-btn--primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.gl-btn--quiet {
  background: var(--gl-surface);
  border-color: var(--gl-border);
  color: var(--gl-muted);
}
.gl-btn--quiet:hover {
  background: var(--gl-overlay);
  color: var(--gl-text);
}
.gl-btn--danger {
  background: transparent;
  border-color: color-mix(in srgb, #f87171 45%, var(--gl-border));
  color: #ef4444;
}
.gl-btn--danger:hover {
  background: color-mix(in srgb, #ef4444 10%, transparent);
}
.gl-btn--sm {
  padding: 0.32rem 0.55rem;
  font-size: 9px;
}
.gl-ico {
  width: 0.9rem;
  height: 0.9rem;
}
.gl-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.45rem;
  border: 1px solid var(--gl-border);
  background: var(--gl-surface);
  color: var(--gl-muted);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.gl-icon-btn:hover {
  background: var(--gl-overlay);
  color: var(--gl-text);
}
.gl-icon-btn--danger {
  border-color: color-mix(in srgb, #f87171 35%, var(--gl-border));
  color: #f87171;
}
.gl-icon-btn--danger:hover {
  background: color-mix(in srgb, #ef4444 12%, transparent);
  color: #dc2626;
}

/* Panels & states */
.gl-panel {
  border-radius: 1rem;
  border: 1px solid var(--gl-border);
  background: var(--gl-surface);
}
.gl-panel--ghost {
  background: var(--gl-overlay);
}
.gl-panel--dashed {
  border-style: dashed;
}
.gl-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 3rem 1.5rem;
  font-size: 11px;
  color: var(--gl-muted);
}
.gl-state--tall {
  flex-direction: column;
  padding: 4rem 1.5rem;
  text-align: center;
}
.gl-state__icon {
  opacity: 0.35;
  color: var(--gl-muted);
}
.gl-state__title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--gl-text);
}
.gl-state__hint {
  margin: 0;
  font-size: 11px;
  color: var(--gl-muted);
  max-width: 16rem;
}

/* Hero */
.gl-hero {
  position: relative;
  overflow: hidden;
  border-radius: 1.1rem;
  border: 1px solid color-mix(in srgb, var(--gl-border) 88%, var(--gl-brand));
  background: var(--gl-surface);
  padding: 1rem 1.15rem 1.15rem;
  box-shadow:
    0 1px 0 color-mix(in srgb, #fff 50%, transparent) inset,
    0 18px 40px -28px color-mix(in srgb, var(--gl-text) 28%, transparent);
}
:global(.dark) .gl-hero {
  box-shadow: 0 1px 0 color-mix(in srgb, #fff 8%, transparent) inset, 0 20px 50px -30px #000;
}
.gl-hero__glow {
  pointer-events: none;
  position: absolute;
  inset: 0;
  background:
    radial-gradient(100% 80% at 0% 0%, color-mix(in srgb, var(--gl-brand) 12%, transparent), transparent 55%),
    radial-gradient(80% 60% at 100% 100%, color-mix(in srgb, var(--gl-brand) 7%, transparent), transparent 50%);
}
.gl-hero__top {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.35rem;
}
.gl-hero__label {
  font-size: 9px;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--gl-muted);
}
.gl-hero__actions {
  display: flex;
  gap: 0.35rem;
}
.gl-hero__title {
  position: relative;
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: var(--gl-text);
}
.gl-hero__summary {
  position: relative;
  margin: 0.4rem 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--gl-muted);
  max-width: 48rem;
}
.gl-hero__meta {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.75rem;
}
.gl-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--gl-overlay);
  color: var(--gl-text);
}
.gl-pill--mono {
  font-family: ui-monospace, monospace;
  font-size: 9px;
  font-weight: 600;
  color: var(--gl-muted);
}
.gl-pill--accent {
  background: color-mix(in srgb, #10b981 14%, transparent);
  color: #047857;
}
:global(.dark) .gl-pill--accent {
  color: #6ee7b7;
}

/* Section stack */
.gl-stack {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.gl-sec {
  border-radius: 0.85rem;
  border: 1px solid var(--gl-border);
  background: var(--gl-surface);
  overflow: hidden;
  box-shadow: 0 4px 16px -10px color-mix(in srgb, var(--gl-text) 18%, transparent);
}
.gl-sec__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.65rem;
  background: linear-gradient(105deg, color-mix(in srgb, var(--gl-brand) 8%, var(--gl-overlay)) 0%, var(--gl-overlay) 55%);
  border-bottom: 1px solid var(--gl-border);
}
.gl-sec__lead {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
}
.gl-sec__orbit {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gl-brand);
  box-shadow: 0 0 0 3px var(--gl-brand-soft);
  flex-shrink: 0;
}
.gl-sec__titles {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}
.gl-sec__key {
  font-size: 9px;
  color: var(--gl-muted);
}
.gl-sec__title {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--gl-text);
}
.gl-sec__tools {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}
.gl-sec__editor {
  padding: 0.65rem 0.65rem 0.5rem;
  background: color-mix(in srgb, var(--gl-overlay) 35%, var(--gl-surface));
}
.gl-sec__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.55rem 0 0;
  margin-top: 0.5rem;
  border-top: 1px solid var(--gl-border);
}
.gl-sec__saving {
  font-size: 10px;
  color: var(--gl-muted);
}
.gl-sec__footer-btns {
  display: flex;
  gap: 0.35rem;
  margin-left: auto;
}
.gl-sec__preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.65rem;
  padding: 0.55rem 0.65rem 0.65rem;
}
.gl-kv {
  display: inline-flex;
  align-items: baseline;
  gap: 0.25rem;
  font-size: 11px;
  padding: 0.2rem 0.45rem;
  border-radius: 0.35rem;
  background: var(--gl-overlay);
}
.gl-kv__k {
  font-weight: 700;
  color: var(--gl-text);
}
.gl-kv__v {
  color: var(--gl-muted);
  max-width: 14rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gl-add-sec {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 0.85rem;
  border: 1px dashed color-mix(in srgb, var(--gl-muted) 40%, var(--gl-border));
  background: color-mix(in srgb, var(--gl-overlay) 50%, transparent);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.gl-add-sec:hover {
  border-color: color-mix(in srgb, var(--gl-brand) 45%, var(--gl-border));
  color: var(--gl-brand);
  background: var(--gl-brand-soft);
}
.gl-add-sec__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.45rem;
  background: var(--gl-brand-soft);
  color: var(--gl-brand);
}
.gl-add-sec__text {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--gl-muted);
}
.gl-add-sec:hover .gl-add-sec__text {
  color: var(--gl-brand);
}

/* Modal inputs */
.gl-input {
  width: 100%;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: #111827;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
:global(.dark) .gl-input {
  border-color: #374151;
  background: #1f2937;
  color: #fff;
}
.gl-input::placeholder { color: #9ca3af; }
.gl-input:focus {
  border-color: var(--clm-brand);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--clm-brand) 20%, transparent);
}
</style>
