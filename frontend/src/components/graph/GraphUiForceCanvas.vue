<template>
  <div ref="mountEl" class="relative h-full min-h-0 w-full min-w-0 overflow-hidden bg-[var(--clm-bg-page)]" />
</template>

<script setup>
/**
 * Embeds react-force-graph-2d (same stack as clm/graph-ui) via React 18 root — vanilla force-graph in Vue was unreliable.
 */
import { ref, shallowRef, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { createRoot } from 'react-dom/client'
import { createElement } from 'react'
import { ContractGraphRfg2d } from './ContractGraphRfg2d.jsx'
import { prepareForceGraphData } from '../../utils/graphPayloadUtils.js'

const props = defineProps({
  graphPayload: { type: Object, required: true },
  highlightNodeIds: { type: Array, default: () => [] },
  highlightLinkKeys: { type: Array, default: () => [] },
  forceDark: { type: Boolean, default: false },
})

const emit = defineEmits(['node-click', 'link-click', 'background-click', 'ready'])

const mountEl = ref(null)
let root = null
const apiRef = shallowRef(null)
const prepared = shallowRef(null)

watch(
  () => props.graphPayload,
  (p) => {
    prepared.value = prepareForceGraphData(p)
  },
  { immediate: true }
)

function renderReact() {
  if (!mountEl.value || !prepared.value?.nodes?.length) return
  if (!root) root = createRoot(mountEl.value)
  root.render(
    createElement(ContractGraphRfg2d, {
      graphData: prepared.value,
      highlightNodeIds: props.highlightNodeIds,
      highlightLinkKeys: props.highlightLinkKeys,
      forceDark: props.forceDark,
      onNodeClick: (n) => emit('node-click', n),
      onLinkClick: (l) => emit('link-click', l),
      onBackgroundClick: () => emit('background-click'),
      onReady: (api) => {
        apiRef.value = api
        emit('ready')
      },
    })
  )
}

watch(
  () => [prepared.value, props.highlightNodeIds, props.highlightLinkKeys],
  () => nextTick(renderReact),
  { deep: true }
)

onMounted(() => {
  nextTick(() => renderReact())
})

onUnmounted(() => {
  root?.unmount()
  root = null
  apiRef.value = null
})

function fitView() {
  apiRef.value?.fitView?.()
}

function nudgeRedraw() {
  apiRef.value?.nudgeRedraw?.()
}

function focusNodeById(id) {
  apiRef.value?.focusNodeById?.(id)
}

function pausePhysics() {
  apiRef.value?.pauseAnimation?.()
}

function resumePhysics() {
  apiRef.value?.resumeAnimation?.()
}

function reheatPhysics() {
  apiRef.value?.reheatSimulation?.()
  apiRef.value?.d3ReheatSimulation?.()
}

defineExpose({ fitView, nudgeRedraw, focusNodeById, pausePhysics, resumePhysics, reheatPhysics })
</script>
