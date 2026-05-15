<template>
  <div class="gsc-wrap">
    <!-- header -->
    <button type="button" class="gsc-header" @click="open = !open">
      <span class="gsc-badge" :style="{ background: badge }">{{ section.abbr }}</span>
      <span class="gsc-title">{{ section.title }}</span>
      <span class="gsc-count">{{ topCount }}</span>
      <svg class="gsc-chevron" :class="{ 'rotate-180': open }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
      </svg>
    </button>

    <!-- body -->
    <div v-if="open && section.data" class="gsc-body">
      <GlDataGrid :data="section.data" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import GlDataGrid from './GlDataGrid.vue'

const props = defineProps({ section: { type: Object, required: true } })

const open = ref(false)

const topCount = computed(() => {
  const d = props.section.data
  if (!d || typeof d !== 'object') return ''
  const n = Array.isArray(d) ? d.length : Object.keys(d).length
  return `${n} fields`
})

const COLORS = ['#3b82f6','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#6366f1','#14b8a6','#f97316','#84cc16','#a855f7','#64748b']
const badge = computed(() => {
  let n = 0
  for (let i = 0; i < props.section.abbr.length; i++) n += props.section.abbr.charCodeAt(i)
  return COLORS[n % COLORS.length]
})
</script>

<style scoped>
.gsc-wrap {
  overflow: hidden;
  border-bottom: 1px solid #e2e8f0;
}
.dark .gsc-wrap { border-color: #334155; }
.gsc-wrap:last-child { border-bottom: none; }

.gsc-header {
  display: flex; align-items: center; gap: 6px;
  width: 100%; padding: 6px 10px;
  background: none; border: none; cursor: pointer; text-align: left;
  transition: background 0.1s;
}
.gsc-header:hover { background: #f8fafc; }
.dark .gsc-header:hover { background: #1e293b; }

.gsc-badge {
  flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center;
  height: 18px; min-width: 18px; padding: 0 4px;
  border-radius: 4px; font-size: 8px; font-weight: 900;
  text-transform: uppercase; color: #fff; letter-spacing: 0.04em;
}
.gsc-title {
  flex: 1; font-size: 11px; font-weight: 700;
  color: #334155; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.dark .gsc-title { color: #e2e8f0; }
.gsc-count { font-size: 9px; color: #94a3b8; flex-shrink: 0; }
.gsc-chevron {
  width: 11px; height: 11px; flex-shrink: 0; color: #94a3b8;
  transition: transform 0.15s;
}

.gsc-body {
  padding: 6px 10px 8px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
}
.dark .gsc-body { background: #111827; border-color: #1e293b; }
</style>
