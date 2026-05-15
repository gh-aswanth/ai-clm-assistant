<template>
  <!-- Single static root: Vue must not patch this element's children (force-graph appends here) -->
  <div ref="rootEl" class="h-full w-full min-h-[inherit]" />
</template>

<script setup>
/**
 * Isolated mount for force-graph. Lives in its own component so parent re-renders
 * (selection, fgRef, etc.) do not reconcile away the library-injected DOM.
 */
import { ref, shallowRef, watch, onMounted, onUnmounted, nextTick } from 'vue'
import ForceGraph from 'force-graph'
import { getNodeColor } from '../utils/graphData.js'

const props = defineProps({
  graphPayload: {
    type: Object,
    required: true,
    validator: (v) => v && Array.isArray(v.nodes) && Array.isArray(v.links),
  },
  highlightAccess: {
    type: Object,
    required: true,
    validator: (v) => typeof v.nodeIds === 'function' && typeof v.linkKeys === 'function',
  },
})

const emit = defineEmits(['ready', 'node-click', 'link-click', 'background-click'])

const NODE_REL_SIZE = 5
const LINK_CURVATURE = 0.12
const DRIFT_ALPHA_TARGET = 0.012
const DRIFT_COOLDOWN_MS = 86_400_000
const CANVAS_BG = '#f1f5f9'

const rootEl = ref(null)
const graphDataRef = shallowRef(null)

function linkLabelPosition(sx, sy, tx, ty, curvature) {
  const l = Math.hypot(tx - sx, ty - sy) || 1
  const a = Math.atan2(ty - sy, tx - sx)
  const d = l * curvature
  const cx = (sx + tx) / 2 + d * Math.cos(a - Math.PI / 2)
  const cy = (sy + ty) / 2 + d * Math.sin(a - Math.PI / 2)
  return {
    midX: 0.25 * sx + 0.5 * cx + 0.25 * tx,
    midY: 0.25 * sy + 0.5 * cy + 0.25 * ty,
  }
}

function formatRel(s) {
  return (s || '').replace(/_/g, ' ')
}

function getNodeId(n) {
  return typeof n === 'string' ? n : n.id
}

function getLinkKey(link) {
  return `${getNodeId(link.source)}->${getNodeId(link.target)}`
}

function applyCompactLayoutForces(fg) {
  if (!fg) return
  fg.d3Force('link')?.distance?.(36)
  fg.d3Force('link')?.strength?.(0.82)
  fg.d3Force('charge')?.strength?.(-24)
  fg.d3Force('charge')?.distanceMax?.(220)
}

function onRenderFramePost(ctx, globalScale) {
  const data = graphDataRef.value
  if (!data?.nodes?.length) return

  const hlN = props.highlightAccess.nodeIds()
  const hlL = props.highlightAccess.linkKeys()

  ctx.save()
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  for (const link of data.links) {
    const s = link.source
    const t = link.target
    if (s.x == null || s.y == null || t.x == null || t.y == null) continue

    const { midX, midY } = linkLabelPosition(s.x, s.y, t.x, t.y, LINK_CURVATURE)
    const label = formatRel(link.type)
    const isHl = hlL.has(getLinkKey(link))

    const edgeFont = Math.max(2, Math.min(4, 3 / globalScale))
    ctx.font = `500 ${edgeFont}px system-ui, "Segoe UI", sans-serif`
    const w = ctx.measureText(label).width + 2
    const h = edgeFont + 1
    ctx.fillStyle = isHl ? 'rgba(255, 255, 255, 0.95)' : 'rgba(255, 255, 255, 0.88)'
    ctx.fillRect(midX - w / 2, midY - h / 2, w, h)
    ctx.strokeStyle = isHl ? 'rgba(59, 130, 246, 0.5)' : 'rgba(148, 163, 184, 0.6)'
    ctx.lineWidth = 1 / globalScale
    ctx.strokeRect(midX - w / 2, midY - h / 2, w, h)
    ctx.fillStyle = isHl ? '#1e3a5f' : '#334155'
    ctx.fillText(label, midX, midY)
  }

  for (const node of data.nodes) {
    const n = node
    if (n.x == null || n.y == null) continue

    const val = Math.sqrt(Math.max(0, n.val ?? 1))
    const r = val * NODE_REL_SIZE
    const isHl = hlN.has(n.id)
    const text = n.id.length > 28 ? n.id.slice(0, 28) + '…' : n.id

    const fontSize = Math.max(3, Math.min(4, 3.5 / globalScale))
    ctx.font = `${fontSize}px system-ui, "Segoe UI", sans-serif`
    const ty = n.y + r + fontSize * 0.4 + 0.5

    if (isHl) {
      ctx.beginPath()
      ctx.arc(n.x, n.y, r + 3 / globalScale, 0, 2 * Math.PI)
      ctx.strokeStyle = 'rgba(37, 99, 235, 0.45)'
      ctx.lineWidth = 1.5 / globalScale
      ctx.stroke()
    }

    ctx.lineWidth = Math.max(0.6, 0.9 / globalScale)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.95)'
    ctx.strokeText(text, n.x, ty)
    ctx.fillStyle = '#0f172a'
    ctx.fillText(text, n.x, ty)
  }

  ctx.restore()
}

let fgApi = null
let resizeObserver = null

function measureSize() {
  const el = rootEl.value
  if (!el) return { w: 640, h: 480 }
  const w = Math.max(200, el.clientWidth || el.offsetWidth || 640)
  const h = Math.max(280, el.clientHeight || el.offsetHeight || 480)
  return { w, h }
}

function fitView() {
  if (!fgApi) return
  try {
    fgApi.zoomToFit(400, 56, () => true)
  } catch {
    /* ignore */
  }
}

function nudgeRedraw() {
  if (!fgApi) return
  try {
    if (typeof fgApi.d3ReheatSimulation === 'function') fgApi.d3ReheatSimulation()
  } catch {
    /* ignore */
  }
}

function teardownGraph() {
  resizeObserver?.disconnect()
  resizeObserver = null
  fgApi?._destructor?.()
  fgApi = null
  graphDataRef.value = null
}

function buildGraph() {
  const host = rootEl.value
  const data = props.graphPayload
  if (!host || !data?.nodes?.length) return

  teardownGraph()
  graphDataRef.value = data

  const { w, h } = measureSize()
  const fg = ForceGraph(host)
    .width(w)
    .height(h)
    .graphData(data)
    .nodeId('id')
    .nodeLabel(() => '')
    .linkLabel(() => '')
    .nodeRelSize(NODE_REL_SIZE)
    .nodeColor((n) => getNodeColor(n.type))
    .linkColor((link) =>
      props.highlightAccess.linkKeys().has(getLinkKey(link)) ? 'rgba(59, 130, 246, 0.75)' : 'rgba(100, 116, 139, 0.45)'
    )
    .linkCurvature(LINK_CURVATURE)
    .linkDirectionalArrowLength(4)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalArrowColor((link) =>
      props.highlightAccess.linkKeys().has(getLinkKey(link)) ? 'rgba(37, 99, 235, 0.9)' : 'rgba(100, 116, 139, 0.55)'
    )
    .linkDirectionalParticles((link) => (props.highlightAccess.linkKeys().has(getLinkKey(link)) ? 3 : 0))
    .linkDirectionalParticleSpeed(0.014)
    .linkDirectionalParticleWidth(2)
    .linkDirectionalParticleColor((link) =>
      props.highlightAccess.linkKeys().has(getLinkKey(link)) ? 'rgba(56, 189, 248, 0.95)' : 'rgba(100, 116, 139, 0.45)'
    )
    .linkWidth((link) => (props.highlightAccess.linkKeys().has(getLinkKey(link)) ? 2 : 0.9))
    .onRenderFramePost(onRenderFramePost)
    .onNodeClick((node) => emit('node-click', node))
    .onNodeDragEnd(() => {
      fg.d3AlphaTarget(DRIFT_ALPHA_TARGET)
      applyCompactLayoutForces(fg)
    })
    .onLinkClick((link) => emit('link-click', link))
    .onBackgroundClick(() => emit('background-click'))
    .backgroundColor(CANVAS_BG)
    .enableNodeDrag(true)
    .cooldownTime(DRIFT_COOLDOWN_MS)
    .d3AlphaDecay(0.014)
    .d3VelocityDecay(0.2)
    .autoPauseRedraw(false)

  if (typeof fg.d3AlphaTarget === 'function') {
    fg.d3AlphaTarget(DRIFT_ALPHA_TARGET)
  }

  fgApi = fg

  const runLayout = () => applyCompactLayoutForces(fg)
  runLayout()
  setTimeout(runLayout, 100)
  setTimeout(runLayout, 400)
  setTimeout(() => fitView(), 500)
  setTimeout(() => fitView(), 1400)

  resizeObserver = new ResizeObserver(() => {
    if (!fgApi || !rootEl.value) return
    const sz = measureSize()
    if (sz.w < 16 || sz.h < 16) return
    fgApi.width(sz.w).height(sz.h)
    fitView()
  })
  resizeObserver.observe(rootEl.value)

  emit('ready')
}

watch(
  () => props.graphPayload,
  () => {
    nextTick(() => buildGraph())
  }
)

onMounted(() => {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => buildGraph())
  })
})

onUnmounted(() => {
  teardownGraph()
})

defineExpose({
  fitView,
  nudgeRedraw,
})
</script>
