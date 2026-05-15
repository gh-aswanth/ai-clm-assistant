<template>
  <!-- Fills main: header + padded shell from App when meta.appFillHeight; two columns share height -->
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden lg:flex-row lg:gap-6">
      <!-- Left: PDF/Doc viewer -->
      <div
        class="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 lg:max-w-[50%]"
      >
        <div class="p-4 border-b dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900">
          <h2 class="font-semibold text-gray-700 dark:text-gray-200">Contract Document</h2>
          <div v-if="!fileUrl" class="flex items-center gap-2">
            <button @click="showDrivePicker = true" class="flex items-center gap-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 px-3.5 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-gray-700 transition text-sm font-medium">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
              Select from Drive
            </button>
            <label class="cursor-pointer flex items-center gap-1.5 bg-blue-600 text-white px-3.5 py-2 rounded-lg hover:bg-blue-700 transition text-sm font-medium">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              Upload PDF/DOCX
              <input type="file" class="hidden" @change="handleFileUpload" accept=".pdf,.docx" />
            </label>
          </div>
          <div v-else class="flex items-center gap-2">
            <span v-if="driveSourceLabel" class="text-[11px] text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/40 px-2 py-0.5 rounded-full font-medium">
              <svg class="w-3 h-3 inline -mt-0.5 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
              {{ driveSourceLabel }}
            </span>
            <span class="text-sm text-gray-500 truncate max-w-[200px]">{{ selectedFile?.name }}</span>
            <button @click="resetFile" class="text-red-500 hover:text-red-700 text-sm font-medium">Remove</button>
          </div>
        </div>
        <div
          v-if="contractCreateUploading"
          class="border-b border-gray-100 bg-blue-50/80 px-4 py-2.5 dark:border-gray-700 dark:bg-blue-950/25"
        >
          <div class="mb-1.5 flex items-center justify-between gap-2 text-[11px] font-semibold text-blue-800 dark:text-blue-200">
            <span>Uploading document…</span>
            <span class="tabular-nums">{{ contractCreateUploadProgress }}%</span>
          </div>
          <div class="h-1.5 overflow-hidden rounded-full bg-blue-100 dark:bg-blue-900/50">
            <div
              class="h-full rounded-full bg-blue-600 transition-all duration-200 dark:bg-sky-500"
              :style="{ width: `${contractCreateUploadProgress}%` }"
            />
          </div>
        </div>
        
        <div class="flex-1 bg-gray-200 dark:bg-gray-900 overflow-auto flex items-center justify-center relative">
          <div v-if="!fileUrl" class="text-center p-8 max-w-sm mx-auto">
            <div class="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 flex items-center justify-center mx-auto mb-5">
              <svg class="h-8 w-8 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p class="text-gray-500 dark:text-gray-400 font-medium text-sm">No document selected</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5">Upload a file or choose from Document Drive</p>
            <div class="flex items-center justify-center gap-3 mt-5">
              <button @click="showDrivePicker = true" class="flex items-center gap-1.5 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 transition px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/50">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                Browse Drive
              </button>
              <span class="text-[10px] text-gray-300 dark:text-gray-600 font-medium">OR</span>
              <label class="flex items-center gap-1.5 text-xs font-semibold text-gray-600 dark:text-gray-300 hover:text-gray-800 transition px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 cursor-pointer">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                Upload File
                <input type="file" class="hidden" @change="handleFileUpload" accept=".pdf,.docx" />
              </label>
            </div>
          </div>
          <div v-else-if="fileType === 'pdf'" class="w-full h-full bg-white">
            <iframe :src="fileUrl" class="w-full h-full bg-white" frameborder="0"></iframe>
          </div>
          <div v-else-if="fileType === 'docx' && docxRendering" class="text-center p-8">
            <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-sm text-gray-400">Rendering document...</p>
          </div>
          <div v-else-if="fileType === 'docx' && docxHtmlUrl" class="w-full h-full bg-white">
            <iframe :src="docxHtmlUrl" class="w-full h-full bg-white border-0" frameborder="0"></iframe>
          </div>
          <div v-else-if="fileType === 'docx'" class="text-center p-8">
            <p class="text-gray-500 font-medium">Could not render DOCX</p>
            <p class="text-sm text-gray-400 mt-2">The document will still be submitted for validation.</p>
          </div>
        </div>
      </div>

      <!-- Right: playground + validation (stacks on small screens) -->
      <div
        class="flex min-h-0 w-full min-w-0 flex-1 flex-col gap-4 overflow-hidden lg:max-w-[50%] lg:flex-[1]"
      >
        <!-- Review Controls: scroll form, keep trigger button visible -->
        <div
          class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <div class="shrink-0 border-b border-gray-100 px-6 py-4 dark:border-gray-700">
            <h2 class="text-lg font-bold text-gray-900 dark:text-white">Review Playground</h2>
          </div>
          <div class="min-h-0 flex-1 overflow-y-auto overscroll-contain px-6 py-4">
            <div class="shrink-0 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Contract Title</label>
              <input v-model="contractData.title" type="text" class="w-full px-4 py-2 border rounded-lg dark:bg-gray-900 dark:border-gray-700 dark:text-white" placeholder="e.g. Highway Construction Agreement" />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
              <input v-model="contractData.startDate" type="date" class="w-full px-4 py-2 border rounded-lg dark:bg-gray-900 dark:border-gray-700 dark:text-white" />
            </div>

            <div>
              <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">Guideline framework</label>
              <p class="mb-2 text-xs text-gray-500 dark:text-gray-400">
                Tap the card to attach the compliance rulebook used for this contract (same idea as a file attachment).
              </p>
              <div
                class="relative overflow-hidden rounded-xl border-2 border-dashed border-blue-200/90 bg-gradient-to-br from-blue-50/95 via-white to-slate-50/80 shadow-[0_1px_0_rgba(15,76,129,0.06),0_12px_32px_-18px_rgba(37,99,235,0.25)] transition-colors dark:border-blue-500/35 dark:from-blue-950/50 dark:via-gray-900 dark:to-slate-950/80 dark:shadow-[0_12px_36px_-20px_rgba(0,0,0,0.65)]"
                :class="[
                  frameworksLoading || !frameworks.length ? 'opacity-[0.65]' : '',
                  !frameworksLoading && frameworks.length ? 'hover:border-blue-400/90 dark:hover:border-blue-400/50' : '',
                ]"
              >
                <div
                  class="pointer-events-none absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-blue-600 via-indigo-500 to-cyan-500 dark:from-sky-400 dark:via-blue-500 dark:to-indigo-500"
                  aria-hidden="true"
                />
                <div
                  class="pointer-events-none absolute right-3 top-3 text-blue-400/50 dark:text-blue-400/35"
                  aria-hidden="true"
                >
                  <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m6.364-6.364l-3.293 3.293a1 1 0 01-1.414 0l-1.586-1.586a1 1 0 010-1.414z"
                    />
                  </svg>
                </div>
                <div class="pointer-events-none flex items-start gap-3 py-3.5 pl-4 pr-10 sm:pl-5 sm:pr-12">
                  <div
                    class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white shadow-md ring-1 ring-blue-100/90 dark:bg-gray-800/90 dark:ring-blue-900/40"
                  >
                    <svg
                      v-if="!frameworksLoading"
                      class="h-6 w-6 text-blue-600 dark:text-sky-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      stroke-width="1.75"
                      aria-hidden="true"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A9 9 0 0112 21c2.305 0 4.408-.867 6-2.292m0-14.25A8.966 8.966 0 0118 3.75c1.052 0 2.062.18 3 .512v14.25A9 9 0 0118 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
                      />
                    </svg>
                    <span
                      v-else
                      class="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent dark:border-sky-400"
                      aria-hidden="true"
                    />
                  </div>
                  <div class="min-w-0 flex-1 pt-0.5">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="text-[15px] font-bold leading-snug text-gray-900 dark:text-white">
                        <template v-if="frameworksLoading">Loading frameworks…</template>
                        <template v-else-if="!frameworks.length">No framework attached</template>
                        <template v-else-if="selectedFramework">{{ selectedFramework.title }}</template>
                        <template v-else>Choose a framework</template>
                      </span>
                      <span
                        v-if="selectedFramework?.is_default"
                        class="rounded-md bg-blue-600/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-blue-700 dark:bg-sky-500/15 dark:text-sky-300"
                      >
                        Default
                      </span>
                      <span
                        v-if="selectedFramework?.version_label"
                        class="rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-semibold tabular-nums text-gray-600 dark:bg-gray-700 dark:text-gray-300"
                      >
                        v{{ selectedFramework.version_label }}
                      </span>
                    </div>
                    <p class="mt-1 line-clamp-2 text-xs leading-relaxed text-gray-600 dark:text-gray-400">
                      <template v-if="frameworksLoading">Fetching guideline packs from the server…</template>
                      <template v-else-if="!frameworks.length">
                        Add guideline data or check your connection, then refresh this page.
                      </template>
                      <template v-else-if="selectedFramework?.summary">{{ selectedFramework.summary }}</template>
                      <template v-else-if="selectedFramework">
                        Framework ruleset linked to section checks below. Tap to swap packs.
                      </template>
                      <template v-else>Select the rulebook to attach — sections and scoring use this pack.</template>
                    </p>
                    <p
                      v-if="selectedFramework && !frameworksLoading"
                      class="mt-1.5 inline-flex max-w-full items-center gap-1.5 rounded-lg bg-gray-100/90 px-2 py-1 font-mono text-[10px] text-gray-500 dark:bg-gray-800/80 dark:text-gray-400"
                    >
                      <svg class="h-3 w-3 shrink-0 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      <span class="truncate">{{ selectedFramework.slug }}</span>
                    </p>
                  </div>
                  <div class="shrink-0 pt-1 text-gray-400 dark:text-gray-500" aria-hidden="true">
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
                <select
                  v-model="selectedFrameworkSlug"
                  :disabled="frameworksLoading || !frameworks.length"
                  class="absolute inset-0 z-[1] h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed"
                  aria-label="Guideline framework"
                >
                  <option v-if="!frameworks.length" value="">No frameworks available</option>
                  <option v-for="f in frameworks" :key="f.slug" :value="f.slug">
                    {{ f.title }}{{ f.version_label ? ` — v${f.version_label}` : '' }}
                  </option>
                </select>
              </div>
              <p v-if="guidelineLoadError" class="mt-2 text-xs text-amber-600 dark:text-amber-400">{{ guidelineLoadError }}</p>
            </div>
            </div>

            <div class="mt-3 flex flex-col lg:mt-4">
              <div class="mb-1 flex flex-wrap items-end justify-between gap-2">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Guidelines / rules</label>
                <span
                  v-if="sectionOptions.length"
                  class="text-xs font-semibold tabular-nums text-blue-600 dark:text-blue-400"
                >
                  {{ selectedRuleKeys.length }} / {{ sectionOptions.length }} selected
                </span>
              </div>
              <p class="mb-2 shrink-0 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
                Browse sections by category, filter the list, and multi-select the checks to run on this contract.
              </p>
              <div v-if="sectionsLoading" class="py-8 text-center text-sm text-gray-400">
                Loading sections…
              </div>
              <div
                v-else-if="!sectionOptions.length"
                class="rounded-xl border border-dashed border-gray-200 py-8 text-center text-sm text-gray-400 dark:border-gray-600 dark:text-gray-500"
              >
                No sections for this framework.
              </div>
              <div
                v-else
                class="flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-gray-50/80 dark:border-gray-600 dark:bg-gray-900/50"
              >
                <div
                  class="flex flex-wrap items-center gap-2 border-b border-gray-200 bg-white px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
                >
                  <div class="relative min-w-[8rem] flex-1">
                    <svg
                      class="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      stroke-width="2"
                      aria-hidden="true"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                    <input
                      v-model="guidelineSearchQuery"
                      type="search"
                      autocomplete="off"
                      placeholder="Filter by title or key…"
                      class="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500"
                    />
                  </div>
                  <div class="flex flex-wrap items-center gap-1">
                    <button
                      type="button"
                      class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-blue-600 transition hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-950/50"
                      @click="selectAllRules"
                    >
                      All
                    </button>
                    <button
                      type="button"
                      class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-gray-600 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700/80"
                      @click="clearAllRules"
                    >
                      Clear
                    </button>
                    <button
                      type="button"
                      class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-gray-600 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700/80"
                      @click="expandAllGuidelineGroups"
                    >
                      Expand
                    </button>
                    <button
                      type="button"
                      class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-gray-600 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700/80"
                      @click="collapseAllGuidelineGroups"
                    >
                      Collapse
                    </button>
                  </div>
                </div>
                <div>
                  <template v-if="filteredGuidelineGroups.length">
                    <div
                      v-for="group in filteredGuidelineGroups"
                      :key="group.id"
                      class="border-b border-gray-200 last:border-b-0 dark:border-gray-600/80"
                    >
                      <div
                        class="flex items-stretch gap-0 bg-white/90 dark:bg-gray-800/90"
                      >
                        <button
                          type="button"
                          class="flex min-w-0 flex-1 items-center gap-2 px-3 py-2.5 text-left transition hover:bg-gray-50 dark:hover:bg-gray-700/50"
                          @click="toggleGuidelineGroup(group.id)"
                        >
                          <svg
                            class="h-4 w-4 shrink-0 text-gray-500 transition-transform dark:text-gray-400"
                            :class="isGuidelineGroupOpen(group.id) ? 'rotate-180' : ''"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="2"
                            aria-hidden="true"
                          >
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                          </svg>
                          <div class="min-w-0 flex-1">
                            <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ group.label }}</div>
                            <div v-if="group.hint" class="text-[11px] text-gray-500 dark:text-gray-400">{{ group.hint }}</div>
                          </div>
                          <span
                            class="shrink-0 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-bold tabular-nums text-blue-700 dark:bg-blue-950/80 dark:text-blue-300"
                          >
                            {{ guidelineGroupSelectedCount(group) }}/{{ group.items.length }}
                          </span>
                        </button>
                        <div
                          class="flex shrink-0 flex-col justify-center gap-0.5 border-l border-gray-100 px-2 py-1.5 dark:border-gray-600"
                          @click.stop
                        >
                          <button
                            type="button"
                            class="whitespace-nowrap rounded-md px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-950/40"
                            @click="selectAllInGuidelineGroup(group)"
                          >
                            Group all
                          </button>
                          <button
                            type="button"
                            class="whitespace-nowrap rounded-md px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700/60"
                            @click="clearGuidelineGroup(group)"
                          >
                            Group none
                          </button>
                        </div>
                      </div>
                      <div
                        v-show="isGuidelineGroupOpen(group.id)"
                        class="border-t border-gray-100 bg-gray-50/90 px-2 py-2 dark:border-gray-700 dark:bg-gray-900/60"
                      >
                        <ul class="space-y-0.5" role="list">
                          <li v-for="sec in group.items" :key="sec.section_key">
                            <label
                              class="flex cursor-pointer items-start gap-3 rounded-lg px-2 py-2 transition hover:bg-white dark:hover:bg-gray-800"
                            >
                              <input
                                type="checkbox"
                                class="mt-0.5 h-4 w-4 shrink-0 rounded border-gray-300 text-blue-600 focus:ring-blue-500/30 dark:border-gray-500 dark:bg-gray-900 dark:text-blue-500"
                                :checked="selectedRuleKeys.includes(sec.section_key)"
                                @change="toggleRule(sec.section_key)"
                              />
                              <span class="min-w-0 flex-1">
                                <span class="block text-sm font-medium text-gray-900 dark:text-gray-100">{{
                                  sec.section_title
                                }}</span>
                                <span class="mt-0.5 block font-mono text-[11px] text-gray-400 dark:text-gray-500">{{
                                  sec.section_key
                                }}</span>
                              </span>
                            </label>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </template>
                  <div
                    v-else
                    class="px-4 py-10 text-center text-sm text-gray-500 dark:text-gray-400"
                  >
                    No sections match your filter.
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div
            class="shrink-0 border-t border-gray-100 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-900/50"
          >
            <button
              type="button"
              @click="triggerReview"
              :disabled="!selectedFile || isReviewing"
              class="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 font-bold text-white transition hover:bg-blue-700 disabled:opacity-50"
            >
              <span v-if="isReviewing" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
              <template v-if="isReviewing">{{ selectedDriveFileId ? 'Creating Contract...' : 'Analyzing Document...' }}</template>
              <template v-else>
                <svg v-if="selectedDriveFileId" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
                {{ selectedDriveFileId ? 'Proceed' : 'Trigger Review & Validate' }}
              </template>
            </button>
          </div>
        </div>

        <!-- Validation: grows when there are results; compact strip when idle -->
        <div
          :class="[
            'space-y-4 pr-2 overscroll-contain',
            validationResults.length > 0 || isReviewing ? 'min-h-0 flex-1 overflow-y-auto' : 'shrink-0',
          ]"
        >
          <h3 v-if="validationResults.length > 0" class="font-bold text-gray-700 dark:text-gray-300">Validation Findings</h3>
          
          <div 
            v-for="(result, index) in validationResults" 
            :key="index"
            @click="goToPage(result.page_number)"
            class="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border-l-4 cursor-pointer hover:shadow-md transition"
            :class="{
              'border-red-500': result.status === 'failed',
              'border-yellow-500': result.status === 'warning',
              'border-green-500': result.status === 'passed'
            }"
          >
            <div class="flex justify-between items-start">
              <div>
                <h4 class="font-bold text-gray-900 dark:text-white">{{ result.check_name }}</h4>
                <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">{{ result.findings }}</p>
              </div>
              <span 
                class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                :class="{
                  'bg-red-100 text-red-700': result.status === 'failed',
                  'bg-yellow-100 text-yellow-700': result.status === 'warning',
                  'bg-green-100 text-green-700': result.status === 'passed'
                }"
              >
                {{ result.status }}
              </span>
            </div>
            <div v-if="result.page_number" class="mt-2 text-[10px] text-gray-400 flex items-center gap-1">
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
              Page {{ result.page_number }}
            </div>
          </div>

          <div
            v-if="!isReviewing && validationResults.length === 0"
            class="rounded-lg border border-dashed border-gray-200 py-6 text-center text-sm text-gray-400 dark:border-gray-600 dark:text-gray-500"
          >
            Run validation to see results here
          </div>
        </div>
      </div>
    </div>

    <!-- Drive File Picker Modal -->
    <Teleport to="body">
      <Transition name="dp-fade">
        <div v-if="showDrivePicker" class="fixed inset-0 z-[9998] bg-black/40 backdrop-blur-[2px]" @click="showDrivePicker = false"></div>
      </Transition>
      <Transition name="dp-scale">
        <div v-if="showDrivePicker" class="fixed inset-0 z-[9999] flex items-center justify-center p-6">
          <div class="dp-modal" @click.stop>
            <!-- Header -->
            <div class="dp-header">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-900/40 flex items-center justify-center flex-shrink-0">
                  <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                </div>
                <div>
                  <h3 class="text-sm font-bold text-gray-900 dark:text-white">Select from Document Drive</h3>
                  <p class="text-[11px] text-gray-400 mt-0.5">Choose a PDF or DOCX file from your drives</p>
                </div>
              </div>
              <button @click="showDrivePicker = false" class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>

            <!-- Drive selector -->
            <div class="dp-drive-bar">
              <label class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mr-2">Drive</label>
              <select v-model="dpSelectedDriveId" class="dp-drive-select" @change="onDriveChange">
                <option :value="null" disabled>Select a drive...</option>
                <option v-for="d in dpDrives" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>

            <!-- Body: folder tree + file list -->
            <div class="dp-body">
              <!-- Folder sidebar -->
              <div class="dp-folder-pane">
                <div v-if="dpFoldersLoading" class="p-4 text-center">
                  <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p class="text-[11px] text-gray-400 mt-2">Loading folders...</p>
                </div>
                <div v-else-if="!dpFolders.length" class="p-4 text-center text-[11px] text-gray-400">
                  No folders in this drive
                </div>
                <div v-else class="dp-folder-list">
                  <template v-for="item in dpFlatFolders" :key="item.folder.id">
                    <button
                      class="dp-folder-item"
                      :class="dpActiveFolderId === item.folder.id ? 'dp-folder-active' : ''"
                      :style="{ paddingLeft: (10 + item.depth * 16) + 'px' }"
                      @click="dpSelectFolder(item.folder)"
                    >
                      <button v-if="item.hasChildren" @click.stop="dpToggleExpand(item.folder.id)" class="dp-expand-btn">
                        <svg class="w-2.5 h-2.5 transition-transform duration-150" :class="item.isExpanded ? 'rotate-90' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
                      </button>
                      <span v-else class="w-[14px] flex-shrink-0"></span>
                      <svg v-if="dpActiveFolderId === item.folder.id" class="w-[14px] h-[14px] text-blue-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/></svg>
                      <svg v-else class="w-[14px] h-[14px] text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                      <span class="text-[11px] font-medium truncate">{{ item.folder.name }}</span>
                      <span class="text-[10px] text-gray-400 ml-auto flex-shrink-0 tabular-nums">{{ dpFolderFileCount(item.folder) }}</span>
                    </button>
                  </template>
                </div>
              </div>

              <!-- File list -->
              <div class="dp-file-pane">
                <!-- Search -->
                <div class="dp-file-search">
                  <svg class="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/></svg>
                  <input v-model="dpFileSearch" type="text" placeholder="Search files..." class="dp-file-search-input" />
                </div>

                <div v-if="!dpActiveFolderId" class="dp-file-empty">
                  <svg class="w-8 h-8 text-gray-200 dark:text-gray-700 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                  <p class="text-[11px] text-gray-400 mt-2">Select a folder to browse files</p>
                </div>
                <div v-else-if="dpFilesLoading" class="dp-file-empty">
                  <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p class="text-[11px] text-gray-400 mt-2">Loading files...</p>
                </div>
                <div v-else-if="!dpFilteredFiles.length" class="dp-file-empty">
                  <svg class="w-8 h-8 text-gray-200 dark:text-gray-700 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                  <p class="text-[11px] text-gray-400 mt-2">No matching PDF/DOCX files</p>
                </div>
                <div v-else class="dp-file-list">
                  <button
                    v-for="file in dpFilteredFiles" :key="file.id"
                    class="dp-file-row"
                    :class="dpSelectedFileId === file.id ? 'dp-file-selected' : ''"
                    @click="dpSelectedFileId = file.id"
                    @dblclick="confirmDrivePick"
                  >
                    <div class="dp-file-icon" :class="dpFileIconClass(file.content_type)">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-[12px] font-medium text-gray-800 dark:text-gray-200 truncate">{{ file.original_filename }}</p>
                      <p class="text-[10px] text-gray-400 mt-0.5">{{ dpFormatBytes(file.size_bytes) }} &middot; {{ dpExtLabel(file.original_filename) }}</p>
                    </div>
                    <div v-if="dpSelectedFileId === file.id" class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                      <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="dp-footer">
              <div class="text-[11px] text-gray-400 flex-1 min-w-0 truncate">
                <template v-if="dpPickedFileName">
                  Selected: <span class="font-semibold text-gray-600 dark:text-gray-300">{{ dpPickedFileName }}</span>
                </template>
                <template v-else>Double-click or select a file and click "Use this file"</template>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <button @click="showDrivePicker = false" class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition">Cancel</button>
                <button @click="confirmDrivePick" :disabled="!dpSelectedFileId || dpPickLoading"
                  class="px-5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition disabled:opacity-40 disabled:pointer-events-none flex items-center gap-2">
                  <span v-if="dpPickLoading" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  {{ dpPickLoading ? 'Loading...' : 'Use this file' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { swalError, swalConfirm } from '../utils/swal.js'

const router = useRouter()
const selectedFile = ref(null)
const fileUrl = ref(null)
const fileType = ref('')
const docxHtmlUrl = ref(null)
const docxRendering = ref(false)
const isReviewing = ref(false)
const validationResults = ref([])
/** HTTP upload progress for POST /contracts/ (local file only; same idea as version upload on detail). */
const contractCreateUploading = ref(false)
const contractCreateUploadProgress = ref(0)

const frameworks = ref([])
const frameworksLoading = ref(true)
const sectionsLoading = ref(false)
const selectedFrameworkSlug = ref('')
const selectedFramework = computed(() => {
  const slug = selectedFrameworkSlug.value
  if (!slug) return null
  return frameworks.value.find((f) => f.slug === slug) || null
})
const sectionOptions = ref([])
const selectedRuleKeys = ref([])
const guidelineLoadError = ref('')
const guidelineSearchQuery = ref('')
const guidelineAccordionOpen = ref(new Set())

/** Curated groups for CPWD-style keys; unknown keys land in “Other”. */
const GUIDELINE_SECTION_GROUPS = [
  {
    id: 'commercial',
    label: 'Commercial & financial',
    hint: 'Limits, payment, decision thresholds',
    keys: ['financial_limits', 'measurement_payment', 'decision_thresholds'],
  },
  {
    id: 'legal',
    label: 'Compliance & legal',
    hint: 'Clauses, eligibility, requirements',
    keys: ['mandatory_clauses', 'compliance_requirements', 'contractor_eligibility'],
  },
  {
    id: 'technical',
    label: 'Technical & execution',
    hint: 'Standards and field work',
    keys: ['technical_standards', 'work_execution_standards'],
  },
  {
    id: 'admin',
    label: 'Administration & documentation',
    hint: 'Contract admin, records, defects',
    keys: ['contract_administration', 'documentation_requirements', 'defect_liability'],
  },
  {
    id: 'risk',
    label: 'Risk & validation',
    hint: 'Scoring weights and critical checks',
    keys: ['validation_weights', 'critical_issues'],
  },
]

const guidelineKeyToGroupId = GUIDELINE_SECTION_GROUPS.reduce((acc, g) => {
  for (const k of g.keys) acc[k] = g.id
  return acc
}, {})

function buildGuidelineGroupsFromOptions(options) {
  const byId = new Map(
    GUIDELINE_SECTION_GROUPS.map((g) => [g.id, { id: g.id, label: g.label, hint: g.hint, items: [] }]),
  )
  const otherItems = []
  for (const sec of options) {
    const gid = guidelineKeyToGroupId[sec.section_key]
    if (gid && byId.has(gid)) {
      byId.get(gid).items.push(sec)
    } else {
      otherItems.push(sec)
    }
  }
  const out = []
  for (const g of GUIDELINE_SECTION_GROUPS) {
    const gr = byId.get(g.id)
    if (gr.items.length) out.push(gr)
  }
  if (otherItems.length) {
    out.push({
      id: 'other',
      label: 'Other sections',
      hint: 'Additional rules in this framework',
      items: otherItems,
    })
  }
  return out
}

const filteredGuidelineGroups = computed(() => {
  const q = guidelineSearchQuery.value.trim().toLowerCase()
  const groups = buildGuidelineGroupsFromOptions(sectionOptions.value)
  if (!q) return groups
  return groups
    .map((g) => ({
      ...g,
      items: g.items.filter(
        (s) =>
          (s.section_title || '').toLowerCase().includes(q) ||
          (s.section_key || '').toLowerCase().includes(q),
      ),
    }))
    .filter((g) => g.items.length > 0)
})

function initGuidelineAccordion() {
  guidelineAccordionOpen.value = new Set(
    buildGuidelineGroupsFromOptions(sectionOptions.value).map((g) => g.id),
  )
}

function isGuidelineGroupOpen(id) {
  return guidelineAccordionOpen.value.has(id)
}

function toggleGuidelineGroup(id) {
  const next = new Set(guidelineAccordionOpen.value)
  next.has(id) ? next.delete(id) : next.add(id)
  guidelineAccordionOpen.value = next
}

function expandAllGuidelineGroups() {
  guidelineAccordionOpen.value = new Set(filteredGuidelineGroups.value.map((g) => g.id))
}

function collapseAllGuidelineGroups() {
  guidelineAccordionOpen.value = new Set()
}

function guidelineGroupSelectedCount(group) {
  return group.items.filter((s) => selectedRuleKeys.value.includes(s.section_key)).length
}

function selectAllInGuidelineGroup(group) {
  const next = new Set(selectedRuleKeys.value)
  for (const it of group.items) next.add(it.section_key)
  selectedRuleKeys.value = [...next]
}

function clearGuidelineGroup(group) {
  const drop = new Set(group.items.map((i) => i.section_key))
  selectedRuleKeys.value = selectedRuleKeys.value.filter((k) => !drop.has(k))
}

function selectAllRules() {
  selectedRuleKeys.value = sectionOptions.value.map((s) => s.section_key)
}

function clearAllRules() {
  selectedRuleKeys.value = []
}

const driveSourceLabel = ref('')
const selectedDriveFileId = ref(null)

const contractData = reactive({
  title: '',
  startDate: new Date().toISOString().substr(0, 10),
  endDate: new Date(Date.now() + 31536000000).toISOString().substr(0, 10),
})

// ── Drive File Picker state ──
const showDrivePicker = ref(false)
const dpDrives = ref([])
const dpDrivesLoading = ref(false)
const dpSelectedDriveId = ref(null)
const dpFolders = ref([])
const dpFoldersLoading = ref(false)
const dpActiveFolderId = ref(null)
const dpActiveFiles = ref([])
const dpFilesLoading = ref(false)
const dpSelectedFileId = ref(null)
const dpFileSearch = ref('')
const dpExpandedIds = ref(new Set())
const dpPickLoading = ref(false)

const ALLOWED_EXTS = ['pdf', 'docx']

const dpExtLabel = (name) => {
  if (!name) return '?'
  const ext = name.split('.').pop()
  return ext && ext.length <= 5 ? ext.toUpperCase() : '?'
}

const dpFormatBytes = (v) => {
  const n = Number(v || 0)
  if (n === 0) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB']
  let s = n, i = 0
  while (s >= 1024 && i < u.length - 1) { s /= 1024; i++ }
  return `${s.toFixed(s >= 10 || i === 0 ? 0 : 1)} ${u[i]}`
}

const dpFileIconClass = (ct) => {
  if (!ct) return 'bg-gray-100 dark:bg-gray-800 text-gray-400'
  if (ct.includes('pdf')) return 'bg-red-50 dark:bg-red-900/30 text-red-500'
  if (ct.includes('word') || ct.includes('document')) return 'bg-blue-50 dark:bg-blue-900/30 text-blue-500'
  return 'bg-gray-100 dark:bg-gray-800 text-gray-400'
}

const dpIsAllowed = (file) => {
  const ext = (file.original_filename || '').split('.').pop().toLowerCase()
  return ALLOWED_EXTS.includes(ext)
}

const dpFolderFileCount = (folder) => {
  return (folder.files || []).filter(dpIsAllowed).length
}

const dpFlatFolders = computed(() => {
  const roots = dpFolders.value.filter(f => !f.parent_id)
  const result = []
  const walk = (parentId, depth) => {
    const children = dpFolders.value
      .filter(f => f.parent_id === parentId)
      .sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
    for (const folder of children) {
      const hasChildren = dpFolders.value.some(f => f.parent_id === folder.id)
      const isExpanded = dpExpandedIds.value.has(folder.id)
      result.push({ folder, depth, hasChildren, isExpanded })
      if (hasChildren && isExpanded) walk(folder.id, depth + 1)
    }
  }
  roots.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
  for (const root of roots) {
    const hasChildren = dpFolders.value.some(f => f.parent_id === root.id)
    const isExpanded = dpExpandedIds.value.has(root.id)
    result.push({ folder: root, depth: 0, hasChildren, isExpanded })
    if (hasChildren && isExpanded) walk(root.id, 1)
  }
  return result
})

const dpFilteredFiles = computed(() => {
  let files = dpActiveFiles.value.filter(dpIsAllowed)
  const q = dpFileSearch.value.trim().toLowerCase()
  if (q) files = files.filter(f => f.original_filename.toLowerCase().includes(q))
  return files
})

const dpPickedFileName = computed(() => {
  if (!dpSelectedFileId.value) return ''
  const f = dpActiveFiles.value.find(f => f.id === dpSelectedFileId.value)
  return f?.original_filename || ''
})

const dpToggleExpand = (id) => {
  const s = new Set(dpExpandedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  dpExpandedIds.value = s
}

const dpSelectFolder = async (folder) => {
  dpActiveFolderId.value = folder.id
  dpSelectedFileId.value = null
  dpFileSearch.value = ''
  // Expand parents
  const s = new Set(dpExpandedIds.value)
  let cur = folder
  while (cur?.parent_id) {
    s.add(cur.parent_id)
    cur = dpFolders.value.find(f => f.id === cur.parent_id)
  }
  dpExpandedIds.value = s

  dpFilesLoading.value = true
  try {
    const { data } = await axios.get(`/api/document-drive-folders/${folder.id}`)
    dpActiveFiles.value = data.files || []
  } catch {
    dpActiveFiles.value = []
  } finally {
    dpFilesLoading.value = false
  }
}

const onDriveChange = async () => {
  dpActiveFolderId.value = null
  dpActiveFiles.value = []
  dpSelectedFileId.value = null
  dpExpandedIds.value = new Set()
  if (!dpSelectedDriveId.value) { dpFolders.value = []; return }
  dpFoldersLoading.value = true
  try {
    const { data } = await axios.get(`/api/document-drives/${dpSelectedDriveId.value}/folders`)
    dpFolders.value = data || []
  } catch {
    dpFolders.value = []
  } finally {
    dpFoldersLoading.value = false
  }
}

const loadDrives = async () => {
  dpDrivesLoading.value = true
  try {
    const { data } = await axios.get('/api/document-drives')
    dpDrives.value = data || []
    if (dpDrives.value.length === 1) {
      dpSelectedDriveId.value = dpDrives.value[0].id
      await onDriveChange()
    }
  } catch {
    dpDrives.value = []
  } finally {
    dpDrivesLoading.value = false
  }
}

watch(showDrivePicker, (v) => {
  if (v && !dpDrives.value.length) loadDrives()
})

const confirmDrivePick = async () => {
  if (!dpSelectedFileId.value) return
  dpPickLoading.value = true
  try {
    const meta = dpActiveFiles.value.find(f => f.id === dpSelectedFileId.value)
    if (!meta) return

    // Download blob only for local preview — backend will use the existing file path
    const resp = await axios.get(`/api/document-drive-files/${dpSelectedFileId.value}/download`, { responseType: 'blob' })
    const blob = resp.data
    const file = new File([blob], meta.original_filename, { type: meta.content_type || blob.type })

    selectedFile.value = file
    selectedDriveFileId.value = meta.id
    fileType.value = meta.original_filename.endsWith('.pdf') ? 'pdf' : 'docx'
    fileUrl.value = URL.createObjectURL(file)

    if (fileType.value === 'docx') renderDocx(file)

    const driveName = dpDrives.value.find(d => d.id === dpSelectedDriveId.value)?.name || 'Drive'
    const folderName = dpFolders.value.find(f => f.id === dpActiveFolderId.value)?.name || ''
    driveSourceLabel.value = folderName ? `${driveName} / ${folderName}` : driveName

    if (!contractData.title) {
      contractData.title = meta.original_filename.split('.')[0]
    }

    showDrivePicker.value = false
  } catch (e) {
    console.error('Failed to load file from drive:', e)
    swalError('Could not load file from drive')
  } finally {
    dpPickLoading.value = false
  }
}

async function loadFrameworks() {
  frameworksLoading.value = true
  guidelineLoadError.value = ''
  try {
    const { data } = await axios.get('/api/guidelines/frameworks')
    frameworks.value = Array.isArray(data) ? data : []
    const def = frameworks.value.find((f) => f.is_default) || frameworks.value[0]
    selectedFrameworkSlug.value = def?.slug || ''
    if (!frameworks.value.length) {
      guidelineLoadError.value = 'Add guideline data (run DB migration) to enable framework selection.'
    }
  } catch {
    guidelineLoadError.value = 'Could not load guideline frameworks. Section chips will be empty.'
    frameworks.value = []
    selectedFrameworkSlug.value = ''
  } finally {
    frameworksLoading.value = false
  }
}

async function loadSectionIndex(slug) {
  if (!slug) {
    sectionOptions.value = []
    selectedRuleKeys.value = []
    return
  }
  sectionsLoading.value = true
  try {
    const { data } = await axios.get(`/api/guidelines/frameworks/${slug}/views/section-index`)
    sectionOptions.value = Array.isArray(data) ? data : []
    const keys = new Set(sectionOptions.value.map((s) => s.section_key))
    selectedRuleKeys.value = selectedRuleKeys.value.filter((k) => keys.has(k))
    if (selectedRuleKeys.value.length === 0 && sectionOptions.value.length) {
      selectedRuleKeys.value = sectionOptions.value.slice(0, 2).map((s) => s.section_key)
    }
  } catch {
    sectionOptions.value = []
    selectedRuleKeys.value = []
  } finally {
    sectionsLoading.value = false
  }
}

watch(selectedFrameworkSlug, (slug) => {
  selectedRuleKeys.value = []
  guidelineSearchQuery.value = ''
  loadSectionIndex(slug)
})

watch(
  sectionOptions,
  () => {
    initGuidelineAccordion()
  },
  { deep: true },
)

const DOCX_WRAPPER_CSS = `html,body{background:#fff;color:#1a1a1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;padding:24px 32px;max-width:820px;margin:auto;line-height:1.75;font-size:14px}h1,h2,h3,h4,h5,h6{color:#111;margin-top:1.4em}p{margin:0.6em 0}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:6px 10px}a{color:#2563eb}img{max-width:100%;height:auto}`

async function renderDocx(file) {
  docxRendering.value = true
  docxHtmlUrl.value = null
  try {
    const mammoth = await import('mammoth')
    const arrayBuffer = await file.arrayBuffer()
    const result = await mammoth.default.convertToHtml({ arrayBuffer })
    const fullHtml = `<html><head><meta charset="utf-8"><style>${DOCX_WRAPPER_CSS}</style></head><body>${result.value}</body></html>`
    const blob = new Blob([fullHtml], { type: 'text/html' })
    docxHtmlUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    console.error('DOCX render failed:', e)
    docxHtmlUrl.value = null
  } finally {
    docxRendering.value = false
  }
}

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    selectedDriveFileId.value = null
    driveSourceLabel.value = ''
    fileType.value = file.name.endsWith('.pdf') ? 'pdf' : 'docx'
    fileUrl.value = URL.createObjectURL(file)
    if (!contractData.title) {
      contractData.title = file.name.split('.')[0]
    }
    if (fileType.value === 'docx') renderDocx(file)
  }
}

const resetFile = () => {
  selectedFile.value = null
  fileUrl.value = null
  fileType.value = ''
  validationResults.value = []
  driveSourceLabel.value = ''
  selectedDriveFileId.value = null
  if (docxHtmlUrl.value) { URL.revokeObjectURL(docxHtmlUrl.value); docxHtmlUrl.value = null }
  docxRendering.value = false
}

const toggleRule = (sectionKey) => {
  const index = selectedRuleKeys.value.indexOf(sectionKey)
  if (index === -1) {
    selectedRuleKeys.value.push(sectionKey)
  } else {
    selectedRuleKeys.value.splice(index, 1)
  }
}

function buildReviewDescription() {
  const fw = selectedFrameworkSlug.value
  const titles = sectionOptions.value
    .filter((s) => selectedRuleKeys.value.includes(s.section_key))
    .map((s) => s.section_title)
  const parts = []
  if (fw) parts.push(`Guideline framework: ${fw}`)
  if (titles.length) parts.push(`Sections: ${titles.join(', ')}`)
  return parts.join(' | ') || 'Review playground'
}

onMounted(async () => {
  await loadFrameworks()
})

const triggerReview = async () => {
  if (!selectedFile.value) return
  
  isReviewing.value = true
  validationResults.value = []
  
  const formData = new FormData()
  formData.append('title', contractData.title)
  formData.append('start_date', new Date(contractData.startDate).toISOString())
  formData.append('end_date', new Date(contractData.endDate).toISOString())
  formData.append('description', buildReviewDescription())

  if (selectedFrameworkSlug.value) {
    formData.append('guideline_framework_slug', selectedFrameworkSlug.value)
  }
  if (selectedRuleKeys.value.length) {
    formData.append('guideline_rule_keys', selectedRuleKeys.value.join(','))
  }

  const fromDrive = !!selectedDriveFileId.value

  if (fromDrive) {
    formData.append('drive_file_id', String(selectedDriveFileId.value))
  } else {
    formData.append('file', selectedFile.value)
  }

  if (!fromDrive) {
    contractCreateUploading.value = true
    contractCreateUploadProgress.value = 0
  }

  try {
    const response = await axios.post('/api/contracts/', formData, {
      onUploadProgress: fromDrive
        ? undefined
        : (e) => {
            if (e.total) contractCreateUploadProgress.value = Math.round((e.loaded * 100) / e.total)
          },
    })
    const contractId = response.data.id

    if (fromDrive) {
      isReviewing.value = false
      router.push(`/contracts/${contractId}`)
      return
    }

    if (fileType.value === 'pdf') {
      fileUrl.value = `/api/contracts/${contractId}/file`
    }
    
    setTimeout(async () => {
      validationResults.value = response.data.compliance_records
      isReviewing.value = false
      router.push(`/contracts/${contractId}`)
    }, 1500)
  } catch (error) {
    console.error('Error uploading contract:', error)
    swalError('Failed to create contract.')
    isReviewing.value = false
  } finally {
    contractCreateUploading.value = false
    contractCreateUploadProgress.value = 0
  }
}

const goToPage = (page) => {
  if (page && fileType.value === 'pdf') {
    // In a real implementation with a PDF viewer like pdf.js, we would jump to the page.
    // For iframe, we can append #page=N to the URL
    // We also use a timestamp to force iframe reload if needed
    const baseUrl = fileUrl.value.split('#')[0].split('?')[0]
    const timestamp = new Date().getTime()
    fileUrl.value = `${baseUrl}?t=${timestamp}#page=${page}`
  }
}
</script>

<style scoped>
/* ── Drive Picker Modal ────────────────────────────────────────────── */
.dp-modal {
  width: 100%;
  max-width: 780px;
  max-height: 85vh;
  background: white;
  border-radius: 16px;
  box-shadow: 0 25px 60px -12px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
:root.dark .dp-modal {
  background: #111827;
  box-shadow: 0 25px 60px -12px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06);
}

.dp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}
:root.dark .dp-header { border-color: #374151; }

.dp-drive-bar {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}
:root.dark .dp-drive-bar { background: #0f172a; border-color: #374151; }

.dp-drive-select {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  font-size: 12px;
  color: #374151;
  outline: none;
}
:root.dark .dp-drive-select { background: #1f2937; border-color: #374151; color: #e5e7eb; }
.dp-drive-select:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }

.dp-body {
  display: grid;
  grid-template-columns: 220px 1fr;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.dp-folder-pane {
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
  background: #fafbfc;
}
:root.dark .dp-folder-pane { border-color: #374151; background: #0d1117; }

.dp-folder-list {
  padding: 6px 0;
}

.dp-folder-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  width: 100%;
  text-align: left;
  cursor: pointer;
  transition: all 0.12s;
  border: 1px solid transparent;
  border-radius: 6px;
  margin: 0 4px;
  width: calc(100% - 8px);
}
.dp-folder-item:hover { background: #f3f4f6; }
:root.dark .dp-folder-item:hover { background: #1f2937; }
.dp-folder-active {
  background: rgba(59,130,246,0.08) !important;
  border-color: rgba(59,130,246,0.2);
}
:root.dark .dp-folder-active {
  background: rgba(59,130,246,0.15) !important;
  border-color: rgba(59,130,246,0.3);
}

.dp-expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  border-radius: 3px;
  color: #9ca3af;
}
.dp-expand-btn:hover { background: rgba(0,0,0,0.06); color: #6b7280; }

.dp-file-pane {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dp-file-search {
  position: relative;
  padding: 10px 14px;
  border-bottom: 1px solid #f3f4f6;
}
:root.dark .dp-file-search { border-color: #1f2937; }
.dp-file-search-input {
  width: 100%;
  padding: 6px 10px 6px 30px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  font-size: 12px;
  color: #374151;
  outline: none;
}
:root.dark .dp-file-search-input { background: #1f2937; border-color: #374151; color: #e5e7eb; }
.dp-file-search-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.12); }

.dp-file-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 40px 20px;
  text-align: center;
}

.dp-file-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}

.dp-file-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  width: 100%;
  text-align: left;
  cursor: pointer;
  transition: all 0.12s;
  border: 1.5px solid transparent;
}
.dp-file-row:hover { background: #f9fafb; }
:root.dark .dp-file-row:hover { background: #1f2937; }
.dp-file-selected {
  background: rgba(59,130,246,0.06) !important;
  border-color: #3b82f6;
}
:root.dark .dp-file-selected {
  background: rgba(59,130,246,0.12) !important;
}

.dp-file-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dp-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  background: #fafbfc;
}
:root.dark .dp-footer { border-color: #374151; background: #0d1117; }

/* ── Transitions ────────────────────────────────────────────────────── */
.dp-fade-enter-active,
.dp-fade-leave-active { transition: opacity 0.2s ease; }
.dp-fade-enter-from,
.dp-fade-leave-to { opacity: 0; }

.dp-scale-enter-active { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.dp-scale-leave-active { transition: all 0.15s ease; }
.dp-scale-enter-from { opacity: 0; transform: scale(0.95) translateY(8px); }
.dp-scale-leave-to { opacity: 0; transform: scale(0.97); }
</style>
