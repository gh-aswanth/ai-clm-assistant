<template>
  <RouterLink
    v-if="framework"
    :to="{ path: '/guidelines', query: { framework: framework.slug } }"
    class="group/gw relative mt-1 block w-full min-w-0 max-w-none overflow-hidden rounded-[14px] no-underline outline-none ring-1 ring-slate-900/[0.06] transition hover:ring-blue-500/35 focus-visible:ring-2 focus-visible:ring-blue-500 dark:ring-white/10 dark:hover:ring-blue-400/40"
    :title="`Open ${framework.title} in Contract Guidelines`"
  >
    <div
      class="absolute inset-0 bg-gradient-to-br from-blue-500/[0.07] via-transparent to-indigo-600/[0.08] opacity-100 transition group-hover/gw:from-blue-500/12 group-hover/gw:to-indigo-600/14 dark:from-blue-400/10 dark:to-indigo-500/10"
      aria-hidden="true"
    />
    <div
      class="relative flex min-w-0 items-stretch gap-0 border border-slate-200/90 bg-white/95 backdrop-blur-sm dark:border-slate-700/90 dark:bg-slate-900/85"
    >
      <div
        class="flex w-12 shrink-0 flex-col items-center justify-center bg-gradient-to-b from-slate-50 to-slate-100/90 sm:w-14 dark:from-slate-800 dark:to-slate-900/80"
      >
        <div
          class="clm-guideline-att-icon grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-[var(--clm-brand)] to-indigo-600 shadow-lg shadow-blue-900/20"
        >
          <svg
            class="h-5 w-5 shrink-0 text-white drop-shadow-sm"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.75"
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
        </div>
        <span
          class="mt-1.5 rounded px-1 py-px text-[8px] font-black uppercase tracking-wider text-slate-500 dark:text-slate-400"
        >
          Guide
        </span>
      </div>

      <div class="flex min-w-0 flex-1 flex-col justify-center gap-2 py-2.5 pl-2.5 pr-2.5 sm:py-3 sm:pl-3 sm:pr-3">
        <div class="min-w-0">
          <p class="break-words text-[13px] font-bold leading-snug text-slate-900 dark:text-slate-50">
            {{ framework.title }}
          </p>
          <p class="mt-0.5 line-clamp-2 break-words text-[10px] font-medium leading-snug text-slate-500 dark:text-slate-400">
            {{ metaLine }}
          </p>
        </div>
        <span
          class="inline-flex w-full shrink-0 items-center justify-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-[10px] font-bold text-white shadow-md transition group-hover/gw:bg-blue-600 sm:w-auto sm:self-start sm:justify-center dark:bg-slate-100 dark:text-slate-900 dark:group-hover/gw:bg-blue-500 dark:group-hover/gw:text-white"
        >
          View
          <svg class="h-3.5 w-3.5 shrink-0 opacity-90" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 3h7m0 0v7m0-7L10 14M5 5v14h14"/>
          </svg>
        </span>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  framework: {
    type: Object,
    default: null,
  },
})

const metaLine = computed(() => {
  const f = props.framework
  if (!f) return ''
  const parts = []
  if (f.version_label) parts.push(`v${f.version_label}`)
  if (f.slug) parts.push(f.slug)
  return parts.join(' · ') || 'Contract review framework'
})
</script>
