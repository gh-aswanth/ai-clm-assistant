<template>
  <div
    class="gfe"
    :class="{ 'gfe--root': depth === 0 }"
    :data-depth="depth"
  >

    <!-- ── OBJECT ──────────────────────────────────────────────── -->
    <template v-if="isObj">

      <!-- Primitive fields: column grid -->
      <div class="gfe-columns">
        <div v-for="k in primitiveKeys" :key="k" class="gfe-col-card">
          <div class="gfe-col-card__rail" aria-hidden="true" />
          <div class="gfe-col-card__inner">
            <div class="gfe-col-card__head">
              <span class="gfe-col-card__label" :title="k">{{ humanize(k) }}</span>
              <button type="button" class="gfe-icon-btn gfe-icon-btn--danger" title="Remove field" @click="removeKey(k)">
                <svg class="gfe-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              </button>
            </div>
            <input v-if="typeof data[k] === 'number'" type="number" :value="data[k]"
              @change="set(k, Number($event.target.value))" class="gfe-field" />
            <label v-else-if="typeof data[k] === 'boolean'" class="gfe-toggle">
              <input type="checkbox" :checked="data[k]" @change="set(k, $event.target.checked)" class="gfe-toggle__input" />
              <span class="gfe-toggle__ui" />
              <span class="gfe-toggle__text">{{ data[k] ? 'Yes' : 'No' }}</span>
            </label>
            <input v-else type="text" :value="String(data[k] ?? '')"
              @change="set(k, $event.target.value)" class="gfe-field gfe-field--mono" />
          </div>
        </div>

        <div v-if="showColAdd" class="gfe-col-card gfe-col-card--draft">
          <div class="gfe-col-card__inner gfe-col-card__inner--flush">
            <input v-model="colKey" ref="colKeyRef" type="text" placeholder="snake_case name"
              @keydown.enter.prevent="confirmColAdd" @keydown.escape="cancelColAdd"
              class="gfe-field gfe-field--mono" />
            <div class="gfe-inline-actions">
              <button type="button" @click="colType='text'" class="gfe-seg" :class="{ 'gfe-seg--on': colType==='text' }">Text</button>
              <button type="button" @click="colType='number'" class="gfe-seg" :class="{ 'gfe-seg--on': colType==='number' }">Num</button>
              <button type="button" @click="confirmColAdd" :disabled="!colKey.trim()" class="gfe-btn gfe-btn--solid gfe-btn--sm" title="Confirm">OK</button>
              <button type="button" @click="cancelColAdd" class="gfe-btn gfe-btn--ghost gfe-btn--sm" title="Cancel">Esc</button>
            </div>
          </div>
        </div>

        <button v-else type="button" @click="openColAdd" class="gfe-slot gfe-slot--column" title="Add column field">
          <span class="gfe-slot__glyph" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" class="gfe-slot__svg"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </span>
          <span class="gfe-slot__label">Column</span>
          <span class="gfe-slot__hint">scalar field</span>
        </button>
      </div>

      <!-- Row blocks: nested objects & tag arrays -->
      <div v-for="k in complexKeys" :key="k" class="gfe-block">
        <header class="gfe-block__head">
          <div class="gfe-block__lead">
            <span class="gfe-block__orbit" aria-hidden="true" />
            <div class="gfe-block__titles">
              <span class="gfe-block__key font-mono">{{ k }}</span>
              <span class="gfe-block__title">{{ humanize(k) }}</span>
            </div>
          </div>
          <div class="gfe-block__meta">
            <span class="gfe-pill" :class="Array.isArray(data[k]) ? 'gfe-pill--tags' : 'gfe-pill--nest'">
              {{ Array.isArray(data[k]) ? 'Tags' : 'Nested' }}
            </span>
            <button type="button" class="gfe-icon-btn gfe-icon-btn--danger" :title="`Remove ${humanize(k)}`" @click="removeKey(k)">
              <svg class="gfe-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>
        </header>
        <div class="gfe-block__body">
          <GuidelineFieldEditor :data="data[k]" :depth="depth+1" @change="set(k, $event)" />
        </div>
      </div>

      <div v-if="showRowAdd" class="gfe-row-draft">
        <div class="gfe-row-draft__fields">
          <input v-model="rowKey" ref="rowKeyRef" type="text" placeholder="Section key (snake_case)"
            @keydown.enter.prevent="confirmRowAdd" @keydown.escape="cancelRowAdd"
            class="gfe-field gfe-field--mono gfe-row-draft__input" />
          <div class="gfe-seg-row">
            <button type="button" @click="rowType='tags'" class="gfe-seg gfe-seg--lg" :class="{ 'gfe-seg--on': rowType==='tags' }">Tags</button>
            <button type="button" @click="rowType='nested'" class="gfe-seg gfe-seg--lg" :class="{ 'gfe-seg--on': rowType==='nested' }">Nested</button>
          </div>
        </div>
        <div class="gfe-row-draft__actions">
          <button type="button" @click="confirmRowAdd" :disabled="!rowKey.trim()" class="gfe-btn gfe-btn--solid">Add block</button>
          <button type="button" @click="cancelRowAdd" class="gfe-btn gfe-btn--ghost">Cancel</button>
        </div>
      </div>

      <button v-if="!showRowAdd" type="button" @click="openRowAdd" class="gfe-slot gfe-slot--row">
        <span class="gfe-slot__glyph" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" class="gfe-slot__svg"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </span>
        <span class="gfe-slot__label">Add row</span>
        <span class="gfe-slot__hint">tags · nested object</span>
      </button>
    </template>

    <!-- ── ARRAY of primitives (tags) ───────────────────────────── -->
    <template v-else-if="isArr && isPrimArray">
      <div class="gfe-tag-cloud" role="list">
        <div v-for="(item, i) in data" :key="i" class="gfe-tag-pill" role="listitem">
          <input
            :type="typeof item === 'number' ? 'number' : 'text'"
            :value="String(item ?? '')"
            @change="arrSet(i, typeof item === 'number' ? Number($event.target.value) : $event.target.value)"
            class="gfe-tag-pill__input"
            :placeholder="typeof item === 'number' ? '0' : 'tag_key'"
          />
          <button type="button" @click="arrRemove(i)" class="gfe-tag-pill__remove" title="Remove tag">
            <svg viewBox="0 0 12 12" fill="none" class="gfe-icon gfe-icon--xs" aria-hidden="true"><path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          </button>
        </div>
        <button type="button" @click="arrAddPrim" class="gfe-tag-add">
          <svg viewBox="0 0 16 16" fill="none" class="gfe-icon" aria-hidden="true"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          Add
        </button>
      </div>
    </template>

    <!-- ── ARRAY of objects ──────────────────────────────────────── -->
    <template v-else-if="isArr">
      <div class="gfe-list">
        <div v-for="(item, i) in data" :key="i" class="gfe-list-card">
          <header class="gfe-list-card__head">
            <span class="gfe-list-card__idx">{{ i + 1 }}</span>
            <span class="gfe-list-card__label">Entry</span>
            <button type="button" @click="arrRemove(i)" class="gfe-icon-btn gfe-icon-btn--danger" title="Remove entry">
              <svg class="gfe-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </header>
          <div class="gfe-list-card__body">
            <GuidelineFieldEditor :data="data[i]" :depth="depth+1" @change="arrObjSet(i, $event)" />
          </div>
        </div>
        <button type="button" @click="arrAddObj" class="gfe-slot gfe-slot--compact">
          <svg viewBox="0 0 16 16" fill="none" class="gfe-icon" aria-hidden="true"><path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          Add item
        </button>
      </div>
    </template>

    <!-- ── primitive fallback ──────────────────────────────────── -->
    <input v-else type="text" :value="String(data ?? '')"
      @change="$emit('change', $event.target.value)" class="gfe-field" />
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import GuidelineFieldEditor from './GuidelineFieldEditor.vue'

const props = defineProps({ data: { required: true }, depth: { type: Number, default: 0 } })
const emit = defineEmits(['change'])

const isObj = computed(() => props.data !== null && typeof props.data === 'object' && !Array.isArray(props.data))
const isArr = computed(() => Array.isArray(props.data))
const isPrimArray = computed(() => isArr.value && props.data.every(x => x === null || typeof x !== 'object'))

const primitiveKeys = computed(() => isObj.value
  ? Object.keys(props.data).filter(k => { const v = props.data[k]; return v === null || typeof v !== 'object' }) : [])
const complexKeys = computed(() => isObj.value
  ? Object.keys(props.data).filter(k => { const v = props.data[k]; return v !== null && typeof v === 'object' }) : [])

const showColAdd = ref(false)
const colKey = ref('')
const colType = ref('text')
const colKeyRef = ref(null)

function openColAdd() { showColAdd.value = true; colKey.value = ''; colType.value = 'text'; nextTick(() => colKeyRef.value?.focus()) }
function cancelColAdd() { showColAdd.value = false; colKey.value = '' }
function confirmColAdd() {
  const slug = slugify(colKey.value)
  if (!slug) return
  const c = clone(props.data)
  if (!(slug in c)) c[slug] = colType.value === 'number' ? 0 : ''
  emit('change', c)
  colKey.value = ''; showColAdd.value = false
}

const showRowAdd = ref(false)
const rowKey = ref('')
const rowType = ref('tags')
const rowKeyRef = ref(null)

function openRowAdd() { showRowAdd.value = true; rowKey.value = ''; rowType.value = 'tags'; nextTick(() => rowKeyRef.value?.focus()) }
function cancelRowAdd() { showRowAdd.value = false; rowKey.value = '' }
function confirmRowAdd() {
  const slug = slugify(rowKey.value)
  if (!slug) return
  const c = clone(props.data)
  if (!(slug in c)) c[slug] = rowType.value === 'tags' ? [] : {}
  emit('change', c)
  rowKey.value = ''; showRowAdd.value = false
}

function slugify(s) { return s.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '') }
function humanize(k) { return String(k).replace(/_/g, ' ') }
function clone(v) { return JSON.parse(JSON.stringify(v)) }

function set(k, val) { const c = clone(props.data); c[k] = val; emit('change', c) }
function removeKey(k) { const c = clone(props.data); delete c[k]; emit('change', c) }

function arrSet(i, val) { const c = clone(props.data); c[i] = val; emit('change', c) }
function arrObjSet(i, val) { const c = clone(props.data); c[i] = val; emit('change', c) }
function arrRemove(i) { const c = clone(props.data); c.splice(i, 1); emit('change', c) }
function arrAddPrim() {
  const c = clone(props.data)
  c.push(c.length && typeof c[c.length - 1] === 'number' ? 0 : '')
  emit('change', c)
}
function arrAddObj() {
  const c = clone(props.data)
  const tpl = c.length ? clone(c[c.length - 1]) : {}
  c.push(Object.fromEntries(Object.entries(tpl).map(([k, v]) => [k, typeof v === 'number' ? 0 : typeof v === 'boolean' ? false : ''])))
  emit('change', c)
}
</script>

<style scoped>
.gfe {
  --gfe-accent: var(--clm-brand, #2563eb);
  --gfe-accent-soft: color-mix(in srgb, var(--gfe-accent) 22%, transparent);
  --gfe-surface: var(--clm-bg-surface-elevated, #fff);
  --gfe-muted: var(--clm-text-muted, #64748b);
  --gfe-text: var(--clm-text, #0f172a);
  --gfe-border: var(--clm-border, #e2e8f0);
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.gfe--root {
  position: relative;
  padding: 0.85rem 1rem 0.65rem;
  border-radius: 1rem;
  background:
    radial-gradient(120% 80% at 0% 0%, color-mix(in srgb, var(--gfe-accent) 8%, transparent) 0%, transparent 55%),
    radial-gradient(90% 60% at 100% 100%, color-mix(in srgb, var(--gfe-accent) 5%, transparent) 0%, transparent 50%),
    var(--clm-bg-overlay, #f8fafc);
  border: 1px solid color-mix(in srgb, var(--gfe-border) 85%, var(--gfe-accent));
  box-shadow:
    0 1px 0 color-mix(in srgb, #fff 40%, transparent) inset,
    0 12px 28px -18px color-mix(in srgb, var(--gfe-text) 25%, transparent);
}

:global(.dark) .gfe--root {
  box-shadow:
    0 1px 0 color-mix(in srgb, #fff 6%, transparent) inset,
    0 16px 40px -20px #000;
}

/* ── Column grid ─────────────────────────────────────────────── */
.gfe-columns {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 0.5rem 0.55rem;
  align-items: stretch;
}

.gfe-col-card {
  position: relative;
  border-radius: 0.65rem;
  background: var(--gfe-surface);
  border: 1px solid var(--gfe-border);
  box-shadow: 0 2px 6px -2px color-mix(in srgb, var(--gfe-text) 12%, transparent);
  transition: border-color 0.15s ease, box-shadow 0.2s ease, transform 0.2s ease;
  overflow: hidden;
}
.gfe-col-card:hover {
  border-color: color-mix(in srgb, var(--gfe-accent) 35%, var(--gfe-border));
  box-shadow: 0 8px 20px -12px color-mix(in srgb, var(--gfe-accent) 45%, transparent);
  transform: translateY(-1px);
}

.gfe-col-card__rail {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--gfe-accent), color-mix(in srgb, var(--gfe-accent) 45%, transparent));
  opacity: 0.85;
}

.gfe-col-card__inner {
  padding: 0.45rem 0.5rem 0.5rem 0.65rem;
  margin-left: 3px;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}
.gfe-col-card__inner--flush {
  margin-left: 0;
  padding: 0.5rem 0.55rem;
}
.gfe-col-card--draft {
  border-style: dashed;
  background: color-mix(in srgb, var(--gfe-accent-soft) 40%, var(--gfe-surface));
  box-shadow: none;
}
.gfe-col-card--draft:hover {
  transform: none;
}

.gfe-col-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.25rem;
  min-width: 0;
}
.gfe-col-card__label {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--gfe-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gfe-field {
  width: 100%;
  min-width: 0;
  border-radius: 0.45rem;
  border: 1px solid var(--gfe-border);
  background: var(--clm-bg-surface, #fff);
  padding: 0.35rem 0.5rem;
  font-size: 11px;
  color: var(--gfe-text);
  outline: none;
  transition: border-color 0.12s, box-shadow 0.12s;
}
.gfe-field--mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 10px;
}
.gfe-field:focus {
  border-color: var(--gfe-accent);
  box-shadow: 0 0 0 2px var(--gfe-accent-soft);
}

.gfe-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  user-select: none;
  padding: 0.15rem 0;
  color: var(--gfe-text);
}
.gfe-toggle__input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.gfe-toggle__ui {
  width: 1.85rem;
  height: 1rem;
  border-radius: 999px;
  background: var(--gfe-border);
  position: relative;
  transition: background 0.15s;
  flex-shrink: 0;
}
.gfe-toggle__ui::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: calc(1rem - 4px);
  height: calc(1rem - 4px);
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 2px color-mix(in srgb, var(--gfe-text) 20%, transparent);
  transition: transform 0.15s ease;
}
.gfe-toggle__input:checked + .gfe-toggle__ui {
  background: var(--gfe-accent);
}
.gfe-toggle__input:checked + .gfe-toggle__ui::after {
  transform: translateX(0.85rem);
}
.gfe-toggle__text {
  font-size: 11px;
  font-weight: 600;
}

.gfe-inline-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
}

/* ── Add slots ───────────────────────────────────────────────── */
.gfe-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.15rem;
  min-height: 4.5rem;
  border-radius: 0.65rem;
  border: 1px dashed color-mix(in srgb, var(--gfe-muted) 45%, var(--gfe-border));
  background: color-mix(in srgb, var(--gfe-surface) 70%, transparent);
  color: var(--gfe-muted);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s, transform 0.15s;
}
.gfe-slot:hover {
  color: var(--gfe-accent);
  border-color: color-mix(in srgb, var(--gfe-accent) 50%, var(--gfe-border));
  background: color-mix(in srgb, var(--gfe-accent) 6%, var(--gfe-surface));
  transform: translateY(-1px);
}
.gfe-slot--row {
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 0.5rem 0.75rem;
  min-height: auto;
  padding: 0.55rem 0.85rem;
  align-items: center;
}
.gfe-slot--row .gfe-slot__glyph {
  margin: 0;
}
.gfe-slot--compact {
  flex-direction: row;
  min-height: auto;
  padding: 0.4rem 0.75rem;
  gap: 0.35rem;
  align-self: flex-start;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.gfe-slot__glyph {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.5rem;
  background: var(--gfe-accent-soft);
  color: var(--gfe-accent);
}
.gfe-slot__svg {
  width: 1rem;
  height: 1rem;
}
.gfe-slot__label {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.gfe-slot__hint {
  font-size: 9px;
  opacity: 0.75;
  font-weight: 500;
}

/* ── Row blocks ────────────────────────────────────────────── */
.gfe-block {
  border-radius: 0.75rem;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--gfe-border) 92%, var(--gfe-accent));
  background: var(--clm-bg-surface, #fff);
  box-shadow: 0 4px 14px -8px color-mix(in srgb, var(--gfe-text) 18%, transparent);
}
.gfe-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.45rem 0.65rem 0.45rem 0.55rem;
  background: linear-gradient(
    105deg,
    color-mix(in srgb, var(--gfe-accent) 10%, var(--clm-bg-overlay, #f1f5f9)) 0%,
    var(--clm-bg-overlay, #f1f5f9) 48%
  );
  border-bottom: 1px solid var(--gfe-border);
}
.gfe-block__lead {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
}
.gfe-block__orbit {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--gfe-accent);
  box-shadow: 0 0 0 3px var(--gfe-accent-soft);
  flex-shrink: 0;
}
.gfe-block__titles {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  min-width: 0;
}
.gfe-block__key {
  font-size: 9px;
  color: var(--gfe-muted);
  opacity: 0.9;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gfe-block__title {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--gfe-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gfe-block__meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}
.gfe-pill {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.2rem 0.45rem;
  border-radius: 999px;
  border: 1px solid var(--gfe-border);
}
.gfe-pill--tags {
  background: color-mix(in srgb, #a855f7 12%, transparent);
  border-color: color-mix(in srgb, #a855f7 28%, var(--gfe-border));
  color: #7c3aed;
}
:global(.dark) .gfe-pill--tags {
  color: #c4b5fd;
  background: color-mix(in srgb, #a855f7 18%, transparent);
}
.gfe-pill--nest {
  background: color-mix(in srgb, #0ea5e9 12%, transparent);
  border-color: color-mix(in srgb, #0ea5e9 28%, var(--gfe-border));
  color: #0369a1;
}
:global(.dark) .gfe-pill--nest {
  color: #7dd3fc;
  background: color-mix(in srgb, #0ea5e9 18%, transparent);
}
.gfe-block__body {
  padding: 0.55rem 0.6rem 0.65rem;
  background: color-mix(in srgb, var(--clm-bg-overlay, #f8fafc) 55%, var(--clm-bg-surface, #fff));
}

/* Nested depth tint */
.gfe[data-depth='1'] .gfe-block__body {
  background: color-mix(in srgb, var(--gfe-accent) 4%, var(--clm-bg-surface, #fff));
}
.gfe[data-depth='2'] .gfe-block__body {
  background: color-mix(in srgb, var(--gfe-accent) 7%, var(--clm-bg-surface, #fff));
}

.gfe-row-draft {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.5rem 0.75rem;
  padding: 0.55rem 0.65rem;
  border-radius: 0.65rem;
  border: 1px dashed color-mix(in srgb, var(--gfe-accent) 35%, var(--gfe-border));
  background: color-mix(in srgb, var(--gfe-accent) 5%, var(--clm-bg-overlay, #f8fafc));
}
.gfe-row-draft__fields {
  flex: 1;
  min-width: 180px;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.gfe-row-draft__input {
  max-width: 100%;
}
.gfe-row-draft__actions {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

/* ── Segmented controls ─────────────────────────────────────── */
.gfe-seg-row {
  display: flex;
  gap: 0.25rem;
}
.gfe-seg {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.2rem 0.5rem;
  border-radius: 0.35rem;
  border: 1px solid var(--gfe-border);
  background: var(--gfe-surface);
  color: var(--gfe-muted);
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.gfe-seg--lg {
  padding: 0.35rem 0.65rem;
  font-size: 10px;
}
.gfe-seg--on {
  background: var(--gfe-accent);
  border-color: var(--gfe-accent);
  color: #fff;
}

.gfe-btn {
  font-size: 10px;
  font-weight: 700;
  padding: 0.35rem 0.65rem;
  border-radius: 0.45rem;
  border: none;
  cursor: pointer;
  transition: opacity 0.12s, transform 0.12s;
}
.gfe-btn--sm {
  padding: 0.2rem 0.45rem;
  font-size: 9px;
}
.gfe-btn--solid {
  background: var(--gfe-accent);
  color: #fff;
}
.gfe-btn--solid:hover:not(:disabled) {
  filter: brightness(1.05);
}
.gfe-btn--solid:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.gfe-btn--ghost {
  background: transparent;
  color: var(--gfe-muted);
  border: 1px solid var(--gfe-border);
}

/* ── Icon buttons ──────────────────────────────────────────── */
.gfe-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  border-radius: 0.35rem;
  background: color-mix(in srgb, var(--gfe-text) 6%, transparent);
  color: var(--gfe-muted);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.gfe-icon-btn:hover {
  background: color-mix(in srgb, var(--gfe-text) 10%, transparent);
  color: var(--gfe-text);
}
.gfe-icon-btn--danger {
  color: #f87171;
}
.gfe-icon-btn--danger:hover {
  background: color-mix(in srgb, #ef4444 14%, transparent);
  color: #dc2626;
}
.gfe-icon {
  width: 0.85rem;
  height: 0.85rem;
}
.gfe-icon--xs {
  width: 0.65rem;
  height: 0.65rem;
}

/* ── Tag cloud ───────────────────────────────────────────────── */
.gfe-tag-cloud {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}
.gfe-tag-pill {
  display: inline-flex;
  align-items: stretch;
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--gfe-muted) 25%, var(--gfe-border));
  background: linear-gradient(180deg, var(--gfe-surface) 0%, color-mix(in srgb, var(--clm-bg-overlay, #f8fafc) 80%, var(--gfe-surface)) 100%);
  box-shadow: 0 1px 2px color-mix(in srgb, var(--gfe-text) 6%, transparent);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.gfe-tag-pill:focus-within {
  border-color: color-mix(in srgb, var(--gfe-accent) 55%, var(--gfe-border));
  box-shadow: 0 0 0 2px var(--gfe-accent-soft);
}
.gfe-tag-pill__input {
  border: none;
  background: transparent;
  padding: 0.28rem 0.15rem 0.28rem 0.65rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 10px;
  color: var(--gfe-text);
  min-width: 4.5rem;
  max-width: 11rem;
  outline: none;
}
.gfe-tag-pill__remove {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.4rem;
  border: none;
  background: color-mix(in srgb, var(--gfe-text) 4%, transparent);
  color: #f87171;
  cursor: pointer;
  transition: background 0.12s;
}
.gfe-tag-pill__remove:hover {
  background: color-mix(in srgb, #ef4444 12%, transparent);
}
.gfe-tag-add {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.28rem 0.55rem 0.28rem 0.45rem;
  border-radius: 999px;
  border: 1px dashed color-mix(in srgb, var(--gfe-muted) 40%, var(--gfe-border));
  background: transparent;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--gfe-muted);
  cursor: pointer;
  transition: color 0.12s, border-color 0.12s, background 0.12s;
}
.gfe-tag-add:hover {
  color: var(--gfe-accent);
  border-color: color-mix(in srgb, var(--gfe-accent) 45%, var(--gfe-border));
  background: var(--gfe-accent-soft);
}

/* ── Object list ───────────────────────────────────────────── */
.gfe-list {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}
.gfe-list-card {
  border-radius: 0.6rem;
  border: 1px solid var(--gfe-border);
  overflow: hidden;
  background: var(--gfe-surface);
}
.gfe-list-card__head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.5rem;
  background: var(--clm-bg-overlay, #f1f5f9);
  border-bottom: 1px solid var(--gfe-border);
}
.gfe-list-card__idx {
  font-size: 10px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #fff;
  background: var(--gfe-accent);
  min-width: 1.35rem;
  height: 1.35rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.3rem;
}
.gfe-list-card__label {
  flex: 1;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--gfe-muted);
}
.gfe-list-card__body {
  padding: 0.45rem 0.5rem;
}
</style>
