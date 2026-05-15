<template>
  <!-- Full graph-ui (React) behavior ported to Vue — see components/graph/GraphUiViewer.vue -->
  <div class="flex h-full min-h-0 min-w-0 w-full flex-1 flex-col">
    <GraphUiViewer ref="viewerRef" :data-url="props.dataUrl" :force-dark="props.forceDark" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import GraphUiViewer from './graph/GraphUiViewer.vue'

const props = defineProps({
  dataUrl: { type: String, default: '' },
  forceDark: { type: Boolean, default: false },
})

const viewerRef = ref(null)

function selectNodeByQuery(query, options = {}) {
  return viewerRef.value?.selectNodeByQuery?.(query, options) || []
}

function selectNodeById(id) {
  return viewerRef.value?.selectNodeById?.(id)
}

function reload() {
  return viewerRef.value?.reload?.()
}

defineExpose({
  selectNodeByQuery,
  selectNodeById,
  reload,
})
</script>
