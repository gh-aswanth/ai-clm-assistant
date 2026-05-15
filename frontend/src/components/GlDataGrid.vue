<template>
  <div class="gl-grid-root">

    <!-- OBJECT ────────────────────────────────────────────────── -->
    <template v-if="isObj">
      <!-- Primitives in a compact multi-column grid -->
      <div v-if="primKeys.length" class="gl-prim-grid">
        <div v-for="k in primKeys" :key="k" class="gl-prim-cell">
          <span class="gl-prim-label">{{ humanize(k) }}</span>
          <span :class="valClass(data[k])" class="gl-prim-val">{{ fmt(data[k]) }}</span>
        </div>
      </div>

      <!-- Complex values (arrays / nested objects) as sub-sections -->
      <div v-for="k in complexKeys" :key="k" class="gl-sub">
        <div class="gl-sub-label">{{ humanize(k) }}</div>
        <div class="gl-sub-body">
          <GlDataGrid :data="data[k]" :depth="depth + 1" />
        </div>
      </div>
    </template>

    <!-- ARRAY of primitives → horizontal chip badges ──────────── -->
    <template v-else-if="isArr && isPrimArray">
      <div class="gl-chips">
        <span v-for="(item, i) in data" :key="i" :class="valClass(item)" class="gl-chip">{{ fmt(item) }}</span>
        <span v-if="!data.length" class="gl-empty">—</span>
      </div>
    </template>

    <!-- ARRAY of objects → compact sub-cards ──────────────────── -->
    <template v-else-if="isArr">
      <div class="gl-obj-arr">
        <div v-for="(item, i) in data" :key="i" class="gl-obj-card">
          <span class="gl-obj-card-n">{{ i + 1 }}</span>
          <GlDataGrid :data="item" :depth="depth + 1" />
        </div>
      </div>
    </template>

    <!-- primitive fallback -->
    <span v-else :class="valClass(data)" class="gl-prim-val">{{ fmt(data) }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import GlDataGrid from './GlDataGrid.vue'

const props = defineProps({
  data: { required: true },
  depth: { type: Number, default: 0 },
})

const isObj = computed(() => props.data !== null && typeof props.data === 'object' && !Array.isArray(props.data))
const isArr = computed(() => Array.isArray(props.data))
const isPrimArray = computed(() => isArr.value && props.data.every(x => x === null || typeof x !== 'object'))

const primKeys = computed(() => isObj.value
  ? Object.keys(props.data).filter(k => { const v = props.data[k]; return v === null || typeof v !== 'object' })
  : [])
const complexKeys = computed(() => isObj.value
  ? Object.keys(props.data).filter(k => { const v = props.data[k]; return v !== null && typeof v === 'object' })
  : [])

function humanize(k) { return String(k).replace(/_/g, ' ') }

function fmt(v) {
  if (v === null || v === undefined) return '—'
  if (v === true)  return 'Yes'
  if (v === false) return 'No'
  return String(v)
}

function valClass(v) {
  if (v === true)  return 'gl-val-yes'
  if (v === false) return 'gl-val-no'
  if (typeof v === 'number') return 'gl-val-num'
  return 'gl-val-str'
}
</script>

<style scoped>
.gl-grid-root { font-size: 10px; display: flex; flex-direction: column; gap: 4px; }

/* ── Primitive grid ─────────────────────────────────────────── */
.gl-prim-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 3px 6px;
}
.gl-prim-cell {
  display: flex; flex-direction: column; gap: 1px;
  padding: 3px 5px;
  border-radius: 5px;
  background: #fff;
  border: 1px solid #e2e8f0;
  min-width: 0;
}
.dark .gl-prim-cell { background: #1e293b; border-color: #334155; }

.gl-prim-label {
  font-size: 8px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: #94a3b8;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.dark .gl-prim-label { color: #64748b; }

.gl-prim-val {
  font-size: 10px; font-weight: 600;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* ── Value color classes ────────────────────────────────────── */
.gl-val-num  { color: #2563eb; }
.gl-val-str  { color: #1e293b; }
.gl-val-yes  { color: #16a34a; }
.gl-val-no   { color: #94a3b8; }
.dark .gl-val-num { color: #93c5fd; }
.dark .gl-val-str { color: #cbd5e1; }
.dark .gl-val-yes { color: #86efac; }
.dark .gl-val-no  { color: #475569; }

/* ── Chip (prim array) ──────────────────────────────────────── */
.gl-chips { display: flex; flex-wrap: wrap; gap: 3px; }
.gl-chip {
  border-radius: 4px; padding: 1px 6px;
  border: 1px solid #e2e8f0; background: #fff;
  font-size: 9px; font-weight: 600;
}
.dark .gl-chip { background: #1e293b; border-color: #334155; }
.gl-empty { font-size: 9px; color: #94a3b8; }

/* ── Sub-section ────────────────────────────────────────────── */
.gl-sub { display: flex; flex-direction: column; gap: 2px; }
.gl-sub-label {
  font-size: 8px; font-weight: 900; text-transform: uppercase;
  letter-spacing: 0.07em; color: #94a3b8; padding-left: 2px;
}
.dark .gl-sub-label { color: #64748b; }
.gl-sub-body {
  padding-left: 8px;
  border-left: 2px solid #e2e8f0;
}
.dark .gl-sub-body { border-color: #334155; }

/* ── Object array ───────────────────────────────────────────── */
.gl-obj-arr { display: flex; flex-direction: column; gap: 4px; }
.gl-obj-card {
  display: flex; gap: 6px; align-items: flex-start;
  padding: 4px 6px;
  border-radius: 5px;
  background: #fff; border: 1px solid #e2e8f0;
}
.dark .gl-obj-card { background: #1e293b; border-color: #334155; }
.gl-obj-card-n {
  flex-shrink: 0; width: 14px; height: 14px; border-radius: 50%;
  background: #e2e8f0; display: flex; align-items: center; justify-content: center;
  font-size: 7px; font-weight: 900; color: #64748b; margin-top: 1px;
}
.dark .gl-obj-card-n { background: #334155; }
</style>
