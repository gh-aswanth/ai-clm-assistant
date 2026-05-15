<template>
  <div class="guidelines-value text-[var(--clm-text)]">
    <ul v-if="isObject" class="space-y-2 border-l-2 border-[var(--clm-border)] pl-3">
      <li v-for="(v, k) in value" :key="String(k)" class="text-sm">
        <span class="font-semibold text-[var(--clm-text-muted)]">{{ humanize(k) }}</span>
        <div class="mt-1">
          <GuidelinesValue v-if="isNested(v)" :value="v" />
          <span v-else class="text-[var(--clm-text)]">{{ formatPrimitive(v) }}</span>
        </div>
      </li>
    </ul>
    <ul v-else-if="isArray" class="list-disc space-y-1 pl-5 text-sm">
      <li v-for="(item, i) in value" :key="i">
        <GuidelinesValue v-if="isNested(item)" :value="item" />
        <span v-else>{{ formatPrimitive(item) }}</span>
      </li>
    </ul>
    <span v-else class="text-sm">{{ formatPrimitive(value) }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import GuidelinesValue from './GuidelinesValue.vue'

const props = defineProps({
  value: { type: null, required: true },
})

const isObject = computed(
  () => props.value !== null && typeof props.value === 'object' && !Array.isArray(props.value),
)
const isArray = computed(() => Array.isArray(props.value))

function isNested(x) {
  return x !== null && typeof x === 'object'
}

function humanize(k) {
  return String(k).replace(/_/g, ' ')
}

function formatPrimitive(x) {
  if (x === true) return 'Yes'
  if (x === false) return 'No'
  if (x === null || x === undefined) return '—'
  if (typeof x === 'number' && Number.isFinite(x)) return String(x)
  return String(x)
}
</script>
