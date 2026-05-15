<script setup>
/**
 * Renders markdown for chat bubbles. While `streaming` is true, reparses are
 * coalesced to one requestAnimationFrame so we keep formatted output without
 * running marked+DOMPurify on every micro-task.
 */
import { ref, watch, onBeforeUnmount } from 'vue'
import { renderMd } from '../utils/chatMarkdown.js'

const props = defineProps({
  content: { type: String, default: '' },
  streaming: { type: Boolean, default: false },
})

const html = ref('')
let rafId = 0

function paint() {
  rafId = 0
  html.value = renderMd(props.content || '')
}

function schedulePaint() {
  if (rafId) return
  rafId = requestAnimationFrame(paint)
}

watch(
  () => [props.content, props.streaming],
  () => {
    if (!props.streaming) {
      if (rafId) {
        cancelAnimationFrame(rafId)
        rafId = 0
      }
      paint()
      return
    }
    schedulePaint()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<template>
  <div class="chat-md min-w-0 max-w-full break-words text-left" v-html="html" />
</template>
