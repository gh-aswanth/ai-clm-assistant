<template>
  <GlDataGrid :data="value" :depth="depth" />
</template>

<script setup>
import GlDataGrid from './GlDataGrid.vue'

defineProps({
  value: { default: null },
  depth: { type: Number, default: 0 },
})
</script>
