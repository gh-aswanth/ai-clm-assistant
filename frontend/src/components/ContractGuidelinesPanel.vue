<template>
  <section class="space-y-4">
    <!-- ── Header + framework selector ──────────────────────────────────── -->
    <div class="rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-5 py-4 shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--clm-border)] pb-3">
        <div>
          <h3 class="text-[11px] font-black uppercase tracking-[0.14em] text-[var(--clm-text-muted)]">Contract guidelines</h3>
          <p class="mt-0.5 text-[11px] text-[var(--clm-text-muted)]">Select framework → Load → Edit sections → Save · Check sections to send to review agent</p>
        </div>
        <span
          v-if="savedFrameworkSlug"
          class="shrink-0 rounded-full bg-[var(--clm-bg-overlay)] px-2.5 py-0.5 text-[10px] font-bold text-[var(--clm-text)]"
        >{{ savedFrameworkSlug }}</span>
      </div>

      <div class="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
        <select
          id="cg-fw"
          v-model="selectedSlug"
          :disabled="frameworksLoading"
          class="min-w-0 flex-1 rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] px-2.5 py-2 text-[12px] font-semibold text-[var(--clm-text)]"
        >
          <option value="" disabled>— choose a framework —</option>
          <option v-for="f in frameworks" :key="f.slug" :value="f.slug">
            {{ f.title }}{{ f.version_label ? ` (v${f.version_label})` : '' }}
          </option>
        </select>
        <div class="flex shrink-0 gap-2">
          <button
            type="button"
            :disabled="!selectedSlug || loadingTemplate"
            class="rounded-lg bg-[var(--clm-bg-overlay)] px-3 py-2 text-[11px] font-bold text-[var(--clm-text)] transition hover:bg-[var(--clm-bg-surface-elevated)] disabled:opacity-50"
            @click="loadFromLibrary"
          >{{ loadingTemplate ? 'Loading…' : 'Load from library' }}</button>
          <button
            type="button"
            :disabled="saving || !hasSections"
            class="clm-pulse-cta rounded-lg px-3 py-2 text-[11px] font-bold text-white shadow-sm disabled:opacity-50"
            @click="saveAll"
          >{{ saving ? 'Saving…' : 'Save' }}</button>
        </div>
      </div>

      <p v-if="loadError" class="mt-2 text-[11px] text-red-600 dark:text-red-400">{{ loadError }}</p>

      <div v-if="attachmentFramework" class="mt-3">
        <GuidelineAttachmentWidget :framework="attachmentFramework" />
      </div>
    </div>

    <!-- ── Empty state ──────────────────────────────────────────────────── -->
    <div
      v-if="!hasSections"
      class="flex items-center justify-center gap-3 rounded-2xl border border-dashed border-[var(--clm-border)] bg-[var(--clm-bg-surface)] py-8 text-center"
    >
      <p class="text-[12px] text-[var(--clm-text-muted)]">
        No guideline data — select a framework and click <strong>Load from library</strong>.
      </p>
    </div>

    <!-- ── Send-to-agent sticky bar ─────────────────────────────────────── -->
    <Transition
      enter-active-class="transition duration-150"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="selectedSections.size > 0"
        class="sticky top-2 z-10 flex items-center justify-between gap-3 rounded-xl border border-[var(--clm-brand)]/30 bg-[var(--clm-bg-surface)]/95 px-4 py-2.5 shadow-lg ring-1 ring-[var(--clm-brand)]/20 backdrop-blur-sm"
      >
        <div class="flex items-center gap-2.5">
          <span class="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--clm-brand)] text-[10px] font-black text-white">
            {{ selectedSections.size }}
          </span>
          <p class="text-[11px] font-semibold text-[var(--clm-text)]">
            {{ selectedSections.size === 1 ? '1 section' : `${selectedSections.size} sections` }} selected for review
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="text-[10px] font-semibold text-[var(--clm-text-muted)] hover:text-[var(--clm-text)] transition"
            @click="selectedSections = new Set()"
          >Clear</button>
          <button
            type="button"
            class="clm-pulse-cta inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-bold text-white shadow-sm"
            @click="sendToAgent"
          >
            <svg class="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            Send to Review Agent
          </button>
        </div>
      </div>
    </Transition>

    <!-- ── Per-section accordion cards ─────────────────────────────────── -->
    <div class="overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm">
      <div
        v-for="(sec, idx) in SECTIONS"
        :key="sec.key"
        :class="idx > 0 ? 'border-t border-[var(--clm-border)]' : ''"
      >
        <!-- Section row header -->
        <div class="flex items-stretch">
          <!-- Checkbox column -->
          <label
            class="flex cursor-pointer items-center border-r border-[var(--clm-border)] px-3 transition hover:bg-[var(--clm-bg-overlay)]/40"
            :title="sectionData[sec.key] ? `Include ${sec.title} in review query` : 'Load data first'"
          >
            <input
              type="checkbox"
              :checked="selectedSections.has(sec.key)"
              :disabled="sectionData[sec.key] === null || sectionData[sec.key] === undefined"
              @change="toggleSelectSection(sec.key)"
              class="h-3.5 w-3.5 rounded accent-[var(--clm-brand)] disabled:opacity-30"
            />
          </label>
          <!-- Header button -->
          <button
            type="button"
            class="flex flex-1 items-center justify-between px-3 py-2.5 text-left transition hover:bg-[var(--clm-bg-overlay)]/40"
            @click="toggleSection(sec.key)"
          >
            <div class="flex items-center gap-2.5">
              <span class="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded bg-[var(--clm-bg-overlay)] text-[9px] font-black uppercase tracking-wide text-[var(--clm-text-muted)]">
                {{ sec.abbr }}
              </span>
              <div class="flex items-baseline gap-2">
                <p class="text-[13px] font-semibold text-[var(--clm-text)]">{{ sec.title }}</p>
                <p class="hidden text-[10px] text-[var(--clm-text-muted)] sm:block">{{ sec.key }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span
                v-if="sectionData[sec.key] !== null && sectionData[sec.key] !== undefined"
                class="rounded-full bg-emerald-100 px-2 py-0.5 text-[9px] font-bold uppercase text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
              >✓</span>
              <svg
                class="h-3.5 w-3.5 shrink-0 text-[var(--clm-text-muted)] transition-transform duration-200"
                :class="{ 'rotate-180': openSections.has(sec.key) }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              ><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
            </div>
          </button>
        </div>

        <!-- Section body -->
        <div v-if="openSections.has(sec.key)" class="border-t border-[var(--clm-border)]">
          <!-- Field editor (default) -->
          <div v-if="!rawMode.has(sec.key)" class="px-4 py-2.5">
            <div v-if="sectionData[sec.key] !== null && sectionData[sec.key] !== undefined">
              <GuidelineFieldEditor
                :data="sectionData[sec.key]"
                :depth="0"
                @change="onSectionChange(sec.key, $event)"
              />
            </div>
            <p v-else class="py-1 text-[11px] italic text-[var(--clm-text-muted)]">
              Empty — load from library or switch to raw JSON.
            </p>
          </div>

          <!-- Raw JSON fallback -->
          <div v-else class="px-4 py-3">
            <p v-if="sectionErrors[sec.key]" class="mb-1.5 text-[11px] text-amber-700 dark:text-amber-300">
              {{ sectionErrors[sec.key] }}
            </p>
            <textarea
              v-model="sectionTexts[sec.key]"
              spellcheck="false"
              rows="10"
              @blur="syncTextToData(sec.key)"
              class="w-full resize-y rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-page)] px-3 py-2 font-mono text-[11px] leading-relaxed text-[var(--clm-text)] placeholder:text-[var(--clm-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--clm-brand)]/40"
              :placeholder="`Paste JSON for ${sec.key}…`"
            />
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-between border-t border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/30 px-4 py-2">
            <button
              type="button"
              class="text-[10px] font-semibold text-[var(--clm-text-muted)] transition hover:text-[var(--clm-brand)]"
              @click="toggleRaw(sec.key)"
            >{{ rawMode.has(sec.key) ? '← Fields view' : '{ } Raw JSON' }}</button>
            <div class="flex items-center gap-3">
              <button
                v-if="rawMode.has(sec.key)"
                type="button"
                class="text-[10px] font-semibold text-[var(--clm-brand)] hover:underline"
                @click="formatSectionText(sec.key)"
              >Format</button>
              <button
                type="button"
                class="text-[10px] font-semibold text-red-400 transition hover:text-red-600"
                @click="clearSection(sec.key)"
              >Clear</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import GuidelineFieldEditor from './GuidelineFieldEditor.vue'
import GuidelineAttachmentWidget from './GuidelineAttachmentWidget.vue'

// ── Section definitions ────────────────────────────────────────────────────
const SECTIONS = [
  { key: 'financial_limits',           title: 'Financial Limits',           abbr: 'FL' },
  { key: 'mandatory_clauses',          title: 'Mandatory Clauses',          abbr: 'MC' },
  { key: 'technical_standards',        title: 'Technical Standards',        abbr: 'TS' },
  { key: 'compliance_requirements',    title: 'Compliance Requirements',    abbr: 'CR' },
  { key: 'contractor_eligibility',     title: 'Contractor Eligibility',     abbr: 'CE' },
  { key: 'work_execution_standards',   title: 'Work Execution Standards',   abbr: 'WE' },
  { key: 'measurement_payment',        title: 'Measurement & Payment',      abbr: 'MP' },
  { key: 'contract_administration',    title: 'Contract Administration',    abbr: 'CA' },
  { key: 'defect_liability',           title: 'Defect Liability',           abbr: 'DL' },
  { key: 'documentation_requirements', title: 'Documentation Requirements', abbr: 'DR' },
  { key: 'decision_thresholds',        title: 'Decision Thresholds',        abbr: 'DT' },
  { key: 'validation_weights',         title: 'Validation Weights',         abbr: 'VW' },
  { key: 'critical_issues',            title: 'Critical Issues',            abbr: 'CI' },
]
const SECTION_KEYS = SECTIONS.map((s) => s.key)

// ── Props / emits ──────────────────────────────────────────────────────────
const props = defineProps({
  contractId: { type: [String, Number], required: true },
  guidelineFrameworkSlug:             { type: String, default: null },
  guidelineFrameworkTitle:            { type: String, default: null },
  guidelineFinancialLimits:           { default: null },
  guidelineMandatoryClauses:          { default: null },
  guidelineTechnicalStandards:        { default: null },
  guidelineComplianceRequirements:    { default: null },
  guidelineContractorEligibility:     { default: null },
  guidelineWorkExecutionStandards:    { default: null },
  guidelineMeasurementPayment:        { default: null },
  guidelineContractAdministration:    { default: null },
  guidelineDefectLiability:           { default: null },
  guidelineDocumentationRequirements: { default: null },
  guidelineDecisionThresholds:        { default: null },
  guidelineValidationWeights:         { default: null },
  guidelineCriticalIssues:            { default: null },
})

const emit = defineEmits(['saved', 'send-to-agent'])

// ── State ──────────────────────────────────────────────────────────────────
const frameworks        = ref([])
const frameworksLoading = ref(true)
const selectedSlug      = ref('')
const loadingTemplate   = ref(false)
const saving            = ref(false)
const loadError         = ref('')
const savedFrameworkSlug = ref(props.guidelineFrameworkSlug || '')

// Per-section: parsed data objects (null = no data)
const sectionData  = ref(Object.fromEntries(SECTION_KEYS.map((k) => [k, null])))
// Per-section: raw JSON text (used in raw mode)
const sectionTexts  = ref(Object.fromEntries(SECTION_KEYS.map((k) => [k, ''])))
// Per-section: error messages
const sectionErrors = ref(Object.fromEntries(SECTION_KEYS.map((k) => [k, ''])))

const openSections     = ref(new Set())
const rawMode          = ref(new Set())
const selectedSections = ref(new Set())  // sections checked for "send to agent"

// ── Computed ───────────────────────────────────────────────────────────────
const hasSections = computed(() =>
  SECTION_KEYS.some((k) => sectionData.value[k] !== null && sectionData.value[k] !== undefined)
)

const attachmentFramework = computed(() => {
  const slug = savedFrameworkSlug.value || selectedSlug.value
  if (!slug) return null
  const found = frameworks.value.find((f) => f.slug === slug)
  return found || { slug, title: props.guidelineFrameworkTitle || slug, version_label: null }
})

// ── Prop → key mapping ─────────────────────────────────────────────────────
function propKey(sectionKey) {
  return 'guideline' + sectionKey.replace(/(^|_)(\w)/g, (_, __, c) => c.toUpperCase())
}

function loadPropsIntoState() {
  for (const key of SECTION_KEYS) {
    const val = props[propKey(key)]
    if (val !== null && val !== undefined) {
      sectionData.value[key]  = val
      sectionTexts.value[key] = JSON.stringify(val, null, 2)
    }
  }
}

// ── Section mutations ──────────────────────────────────────────────────────
function onSectionChange(key, newVal) {
  sectionData.value[key] = newVal
  // Keep text in sync so switching to raw mode shows current state
  sectionTexts.value[key] = JSON.stringify(newVal, null, 2)
}

function clearSection(key) {
  sectionData.value[key]  = null
  sectionTexts.value[key] = ''
  sectionErrors.value[key] = ''
  const s = new Set(selectedSections.value)
  s.delete(key)
  selectedSections.value = s
}

function toggleSelectSection(key) {
  const s = new Set(selectedSections.value)
  s.has(key) ? s.delete(key) : s.add(key)
  selectedSections.value = s
}

function sendToAgent() {
  const fw = frameworks.value.find((f) => f.slug === (selectedSlug.value || savedFrameworkSlug.value))
  const sections = {}
  for (const key of selectedSections.value) {
    if (sectionData.value[key] !== null && sectionData.value[key] !== undefined) {
      sections[key] = sectionData.value[key]
    }
  }
  if (!Object.keys(sections).length) return
  emit('send-to-agent', {
    frameworkSlug:  fw?.slug  || savedFrameworkSlug.value || selectedSlug.value,
    frameworkTitle: fw?.title || props.guidelineFrameworkTitle || '',
    sections,
  })
}

function toggleSection(key) {
  const s = new Set(openSections.value)
  s.has(key) ? s.delete(key) : s.add(key)
  openSections.value = s
}

function toggleRaw(key) {
  const s = new Set(rawMode.value)
  if (s.has(key)) {
    // Switching back to fields: parse current text first
    syncTextToData(key)
    s.delete(key)
  } else {
    // Switching to raw: sync current data → text
    if (sectionData.value[key] !== null) {
      sectionTexts.value[key] = JSON.stringify(sectionData.value[key], null, 2)
    }
    s.add(key)
  }
  rawMode.value = s
}

function syncTextToData(key) {
  const raw = sectionTexts.value[key].trim()
  if (!raw) {
    sectionData.value[key] = null
    sectionErrors.value[key] = ''
    return
  }
  try {
    sectionData.value[key] = JSON.parse(raw)
    sectionErrors.value[key] = ''
  } catch (e) {
    sectionErrors.value[key] = e?.message || 'Invalid JSON'
  }
}

function formatSectionText(key) {
  const raw = sectionTexts.value[key].trim()
  if (!raw) return
  try {
    sectionTexts.value[key] = JSON.stringify(JSON.parse(raw), null, 2)
    sectionErrors.value[key] = ''
  } catch (e) {
    sectionErrors.value[key] = e?.message || 'Invalid JSON'
  }
}

// ── API actions ────────────────────────────────────────────────────────────
async function loadFrameworks() {
  frameworksLoading.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get('/api/guidelines/frameworks')
    frameworks.value = Array.isArray(data) ? data : []
    if (!selectedSlug.value) {
      const def = frameworks.value.find((f) => f.is_default) || frameworks.value[0]
      selectedSlug.value = props.guidelineFrameworkSlug || def?.slug || ''
    }
  } catch (e) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Failed to load frameworks'
  } finally {
    frameworksLoading.value = false
  }
}

async function loadFromLibrary() {
  if (!selectedSlug.value) return
  loadingTemplate.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get(`/api/guidelines/frameworks/${encodeURIComponent(selectedSlug.value)}/bundle`)
    for (const sec of data.sections || []) {
      if (SECTION_KEYS.includes(sec.section_key) && sec.body !== undefined) {
        sectionData.value[sec.section_key]  = sec.body
        sectionTexts.value[sec.section_key] = JSON.stringify(sec.body, null, 2)
        sectionErrors.value[sec.section_key] = ''
        const s = new Set(openSections.value)
        s.add(sec.section_key)
        openSections.value = s
      }
    }
    // Close raw mode for all sections just loaded
    const r = new Set(rawMode.value)
    for (const sec of data.sections || []) r.delete(sec.section_key)
    rawMode.value = r
  } catch (e) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Failed to load bundle'
  } finally {
    loadingTemplate.value = false
  }
}

async function saveAll() {
  saving.value = true
  loadError.value = ''

  // Flush any open raw-mode textareas first
  for (const key of rawMode.value) syncTextToData(key)
  const hasErrors = SECTION_KEYS.some((k) => sectionErrors.value[k])
  if (hasErrors) { saving.value = false; return }

  const slug = selectedSlug.value || savedFrameworkSlug.value || null
  const fw = frameworks.value.find((f) => f.slug === slug)
  const payload = {
    guideline_framework_slug:  slug,
    guideline_framework_title: fw?.title || props.guidelineFrameworkTitle || null,
  }
  for (const key of SECTION_KEYS) {
    payload[`guideline_${key}`] = sectionData.value[key] ?? null
  }

  try {
    const { data } = await axios.patch(`/api/contracts/${props.contractId}/guidelines`, payload)
    savedFrameworkSlug.value = data.guideline_framework_slug || slug || ''
    emit('saved', data)
  } catch (e) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Save failed'
  } finally {
    saving.value = false
  }
}

// ── Watchers ───────────────────────────────────────────────────────────────
watch(() => props.guidelineFrameworkSlug, (val) => {
  savedFrameworkSlug.value = val || ''
  if (val && !selectedSlug.value) selectedSlug.value = val
})

watch(
  () => SECTION_KEYS.map((k) => props[propKey(k)]),
  () => loadPropsIntoState(),
  { deep: true },
)

onMounted(async () => {
  await loadFrameworks()
  loadPropsIntoState()
  if (props.guidelineFrameworkSlug) selectedSlug.value = props.guidelineFrameworkSlug

  // Auto-load guidelines if a framework is selected but no section data exists yet
  const hasAnyData = SECTION_KEYS.some(k => sectionData.value[k] !== null && sectionData.value[k] !== undefined)
  if (selectedSlug.value && !hasAnyData) {
    await loadFromLibrary()
  }
})
</script>
