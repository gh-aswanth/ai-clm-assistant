<template>
  <div
    class="min-w-0 max-w-full space-y-6 transition-[padding] duration-200 ease-out"
    :style="contractPageChatInset"
  >
    <div class="flex min-w-0 max-w-full flex-row gap-4">
      <!-- Main Content Area (shrinks when docked chat is wide; padding-right reserves space for fixed rail) -->
      <div
        :class="showChat ? 'min-w-0 flex-1' : 'w-full'"
        class="mx-auto w-full max-w-[min(100%,88rem)] space-y-6 transition-all duration-300"
      >
        <!-- Header -->
        <div class="flex flex-col gap-4 rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] p-4 shadow-sm sm:p-6 lg:flex-row lg:items-center lg:justify-between lg:gap-6">
          <div class="min-w-0">
            <h1 class="text-2xl font-bold leading-tight text-[var(--clm-text)] sm:text-3xl">{{ contract?.title }}</h1>
            <p class="mt-1 text-sm text-[var(--clm-text-muted)] sm:text-base">{{ contract?.description }}</p>
          </div>
          <div class="flex flex-shrink-0 flex-wrap items-center gap-2 sm:gap-3">
            <button
              v-if="['review','redraft'].includes((contract?.status || '').toLowerCase())"
              @click="showChat = !showChat"
              class="flex items-center gap-2 rounded-lg bg-[var(--clm-bg-overlay)] px-4 py-2 font-bold text-[var(--clm-text)] transition hover:bg-[var(--clm-bg-surface-elevated)]"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
              {{ showChat ? 'Hide Chat' : 'AI Agent Chat' }}
            </button>
            <button v-if="latestVersion?.signed_file_path || contract?.signed_file_path" @click="downloadSigned" class="rounded-lg bg-[var(--clm-success)] px-6 py-2 font-bold text-white transition hover:opacity-90">
              Download Signed Document
            </button>
          </div>
        </div>

        <!-- Background-task activity banner -->
        <Transition name="clm-bg-task-banner">
          <div v-if="bgTasks.length" class="flex flex-col gap-2">
            <div
              v-for="task in bgTasks"
              :key="task.id"
              class="flex items-center gap-3 rounded-xl border px-4 py-2.5 text-sm font-medium shadow-sm transition-all"
              :class="task.status === 'running'
                ? 'border-[var(--clm-brand)]/30 bg-[var(--clm-brand)]/5 text-[var(--clm-brand)]'
                : task.status === 'done'
                  ? 'border-emerald-400/30 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300'
                  : 'border-red-400/30 bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300'"
            >
              <!-- spinner / icon -->
              <span v-if="task.status === 'running'" class="shrink-0">
                <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
              </span>
              <span v-else-if="task.status === 'done'" class="shrink-0">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
              </span>
              <span v-else class="shrink-0">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
              </span>
              <!-- label -->
              <span class="truncate">
                <template v-if="task.type === 'chunking_started'">Chunking <strong>{{ task.filename }}</strong>…</template>
                <template v-else-if="task.type === 'chunking_done'">Chunked <strong>{{ task.filename }}</strong></template>
                <template v-else-if="task.type === 'chunking_failed'">Chunking failed for <strong>{{ task.filename }}</strong></template>
                <template v-else-if="task.type === 'compliance_started'">Running compliance checks on <strong>{{ task.filename }}</strong>…</template>
                <template v-else-if="task.type === 'compliance_done'">Compliance complete for <strong>{{ task.filename }}</strong></template>
                <template v-else-if="task.type === 'compliance_failed'">Compliance check failed for <strong>{{ task.filename }}</strong></template>
                <template v-else-if="task.type === 'scoring_started'">Running scoring on <strong>{{ task.filename }}</strong>…</template>
                <template v-else-if="task.type === 'scoring_done'">Scoring complete for <strong>{{ task.filename }}</strong></template>
                <template v-else-if="task.type === 'scoring_failed'">Scoring failed for <strong>{{ task.filename }}</strong></template>
                <template v-else-if="task.type === 'graph_build_started'">Building knowledge graph for <strong>{{ task.filename }}</strong>…</template>
                <template v-else-if="task.type === 'graph_build_done'">Knowledge graph built for <strong>{{ task.filename }}</strong></template>
                <template v-else-if="task.type === 'graph_build_failed'">Graph build failed for <strong>{{ task.filename }}</strong></template>
                <template v-else>{{ task.filename }} — {{ task.status }}</template>
              </span>
            </div>
          </div>
        </Transition>

        <!-- Contract Status Bar -->
        <div v-if="contract?.status" class="rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm">
          <div class="flex items-center justify-between border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-2">
            <div>
              <span class="text-[10px] font-black uppercase tracking-widest text-[var(--clm-text-muted)]">Contract Status</span>
              <p class="mt-0.5 text-[10px] text-[var(--clm-text-muted)]/90">
                Use the <strong class="font-bold text-[var(--clm-text)]">Next milestone</strong> card to move forward, or tap a step to <strong class="font-bold text-[var(--clm-text)]">jump</strong> directly.
              </p>
            </div>
            <span v-if="updatingStatus" class="shrink-0 text-[10px] text-[var(--clm-text-muted)]">Saving…</span>
          </div>
          <div class="flex min-w-0 flex-col gap-4 px-4 py-4 sm:flex-row sm:items-stretch sm:gap-0 sm:px-6">
            <div class="flex min-w-0 flex-1 items-stretch overflow-x-auto pb-1 sm:pb-0">
              <template v-for="(step, idx) in contractStatusSteps" :key="step.value">
                <!-- connector between steps + timeline label -->
                <div
                  v-if="idx > 0"
                  class="flex min-w-[4.25rem] flex-1 flex-col items-stretch gap-1 self-start sm:min-w-[4.75rem]"
                >
                  <div
                    class="mt-[13px] h-0.5 w-full shrink-0 rounded-full"
                    :class="contractStatusStepIndex >= 0 && contractStatusStepIndex >= idx ? 'bg-[var(--clm-brand)]' : 'bg-[var(--clm-border)]'"
                  />
                  <span
                    class="w-full px-0.5 text-center text-[9px] font-semibold leading-snug tracking-tight text-balance"
                    :class="connectorSegmentLabelClass(idx)"
                  >{{ connectorSegmentLabel(idx) }}</span>
                </div>

                <!-- step node (optional jump; primary path is Next action) -->
                <button
                  type="button"
                  :disabled="updatingStatus"
                  @click="setContractStatus(step.value)"
                  class="group flex shrink-0 flex-col items-center gap-0.5 transition-opacity"
                  :class="updatingStatus ? 'opacity-50' : ''"
                  :title="`Jump straight to “${step.label}” (skips intermediate stages)`"
                >
                  <!-- circle -->
                  <div
                    class="flex h-7 w-7 items-center justify-center rounded-full border-2 transition-all duration-200"
                    :class="
                      contractStatusStepIndex === idx   ? 'border-transparent text-white ' + step.circleBg + ' shadow-md' :
                      contractStatusStepIndex > idx     ? 'border-[var(--clm-brand)] bg-[var(--clm-brand)] text-white' :
                                                      'border-[var(--clm-border)] bg-[var(--clm-bg-surface)] text-[var(--clm-text-muted)] group-hover:border-[var(--clm-brand)]/60'
                    "
                  >
                    <svg v-if="contractStatusStepIndex > idx" class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                    <span v-else class="text-[10px] font-bold leading-none">{{ idx + 1 }}</span>
                  </div>
                  <!-- label -->
                  <span
                    class="max-w-[4.5rem] text-center text-[9px] font-bold uppercase leading-tight tracking-wide"
                    :class="
                      contractStatusStepIndex === idx   ? step.labelColor :
                      contractStatusStepIndex > idx     ? 'text-[var(--clm-brand)]' :
                                                      'text-[var(--clm-text-muted)]'
                    "
                  >{{ step.label }}</span>
                  <span
                    v-if="contractStatusStepIndex === idx"
                    class="max-w-[6rem] text-center text-[8px] font-bold uppercase leading-tight tracking-wide text-[var(--clm-brand)]"
                  >You are here</span>
                </button>
              </template>
            </div>

          </div>
        </div>

        <div
          class="grid grid-cols-1 gap-6"
          :class="activeTab === 'graph' ? '' : 'lg:grid-cols-3'"
        >
          <!-- Left-side feature strip (extra panel on contract area) -->
          <div v-if="contract && activeTab !== 'graph'" class="lg:col-span-3">
            <div
              class="clm-pulse-strip min-w-0 overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm ring-1 ring-[var(--clm-brand)]/[0.06] dark:ring-[var(--clm-brand)]/15"
            >
              <!--
                Layout uses .clm-pulse-strip container queries (style.css): follows real width after
                chat + preview padding, not viewport breakpoints — avoids crushed 3-column strip.
              -->
              <div class="clm-pulse-strip__grid min-w-0">
                <!-- Contract pulse -->
                <div
                  class="clm-pulse-strip__pulse flex min-h-0 min-w-0 flex-col bg-gradient-to-b from-[var(--clm-bg-overlay)]/30 to-transparent p-4 sm:p-5 lg:bg-gradient-to-br lg:from-[var(--clm-bg-overlay)]/25 lg:to-transparent"
                >
                  <div class="flex flex-wrap items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="text-[10px] font-black uppercase tracking-[0.16em] text-[var(--clm-text-muted)] sm:text-[11px]">
                        Contract pulse
                      </p>
                      <p class="mt-0.5 text-[10px] text-[var(--clm-text-muted)]/90">Live snapshot</p>
                    </div>
                    <span
                      class="shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-bold capitalize leading-none shadow-sm"
                      :class="statusHeroClass(contract?.status)"
                    >
                      {{ contract?.status || '—' }}
                    </span>
                  </div>
                  <div class="mt-4 grid min-w-0 grid-cols-2 gap-2 sm:gap-3">
                    <div
                      class="rounded-xl border border-[var(--clm-border)]/70 bg-[var(--clm-bg-surface)]/80 p-3 shadow-[0_1px_0_rgba(15,23,42,0.04)] backdrop-blur-[2px] sm:p-3.5 dark:bg-[var(--clm-bg-overlay)]/50 dark:shadow-none"
                    >
                      <p class="text-[10px] font-semibold uppercase tracking-wide text-[var(--clm-text-muted)]">Signers</p>
                      <p class="mt-1.5 flex flex-wrap items-baseline gap-x-1.5 gap-y-0 text-xl font-black tabular-nums text-[var(--clm-text)] sm:text-2xl">
                        <span>{{ latestVersionSignerCount }}</span>
                        <span class="text-[11px] font-semibold normal-case tracking-normal text-[var(--clm-text-muted)]">total</span>
                      </p>
                      <p class="mt-1.5 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                        {{ latestVersionSignedSignerCount }} signed
                      </p>
                    </div>
                    <div
                      class="rounded-xl border border-[var(--clm-border)]/70 bg-[var(--clm-bg-surface)]/80 p-3 shadow-[0_1px_0_rgba(15,23,42,0.04)] backdrop-blur-[2px] sm:p-3.5 dark:bg-[var(--clm-bg-overlay)]/50 dark:shadow-none"
                    >
                      <p class="text-[10px] font-semibold uppercase tracking-wide text-[var(--clm-text-muted)]">Contract stage</p>
                      <p class="mt-1.5 text-xl font-black tabular-nums text-[var(--clm-text)] sm:text-2xl">
                        {{ completedMilestonesCount
                        }}<span class="text-[var(--clm-text-muted)]">/</span>{{ totalMilestonesCount }}
                      </p>
                      <p class="mt-1.5 text-[11px] text-[var(--clm-text-muted)]">stages</p>
                    </div>
                  </div>
                  <div class="mt-auto pt-4">
                    <div class="mb-1.5 flex items-center justify-between gap-2">
                      <p class="text-[10px] font-semibold uppercase tracking-wide text-[var(--clm-text-muted)]">
                        Signer progress
                      </p>
                      <span class="text-[11px] font-bold tabular-nums text-[var(--clm-text-muted)]">
                        {{ latestSignerCompletionPct }}%
                      </span>
                    </div>
                    <div class="h-2 overflow-hidden rounded-full bg-[var(--clm-bg-overlay)] ring-1 ring-[var(--clm-border)]/40">
                      <div
                        class="h-full min-w-0 rounded-full bg-gradient-to-r from-[var(--clm-brand)] to-indigo-600 transition-[width] duration-300 ease-out"
                        :style="{ width: `${latestSignerCompletionPct}%` }"
                      />
                    </div>
                  </div>
                </div>

                <!-- Next milestone -->
                <div
                  class="clm-pulse-strip__milestone flex min-h-0 min-w-0 flex-col bg-gradient-to-br from-[var(--clm-brand)]/[0.08] via-[var(--clm-bg-surface)] to-transparent p-4 sm:p-5 dark:from-[var(--clm-brand)]/12 dark:via-[var(--clm-bg-surface)]"
                >
                  <div class="flex min-h-0 min-w-0 flex-1 flex-row items-start gap-3">
                    <span class="mt-1 inline-flex min-h-[2.75rem] w-1 shrink-0 rounded-full bg-[var(--clm-brand)] shadow-sm shadow-[var(--clm-brand)]/25 sm:min-h-[3.25rem]" aria-hidden="true" />
                    <div class="min-w-0 flex-1">
                      <p class="text-[10px] font-black uppercase tracking-[0.16em] text-[var(--clm-text-muted)] sm:text-[11px]">
                        Next milestone
                      </p>
                      <template v-if="nextMilestone">
                        <p class="mt-2 break-words text-sm font-bold leading-snug text-[var(--clm-text)] sm:text-base">
                          {{ nextMilestone.title }}
                        </p>
                        <p class="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-[var(--clm-text-muted)]">
                          <span class="inline-flex max-w-full items-center gap-1.5 rounded-lg bg-[var(--clm-bg-overlay)]/90 px-2.5 py-1 font-medium text-[var(--clm-text)] ring-1 ring-[var(--clm-border)]/50">
                            <svg class="h-3.5 w-3.5 shrink-0 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            <span class="min-w-0 truncate">Due {{ formatDate(nextMilestone.due_date) }}</span>
                          </span>
                        </p>
                        <p class="mt-2 line-clamp-3 text-[11px] leading-relaxed text-[var(--clm-text-muted)] sm:line-clamp-2 lg:line-clamp-3">
                          {{ nextMilestone.description }}
                        </p>
                      </template>
                      <p v-else class="mt-2 text-sm italic text-[var(--clm-text-muted)]">No schedule yet.</p>
                    </div>
                  </div>
                  <div class="mt-4 flex w-full min-w-0 flex-col gap-2 sm:mt-5">
                    <button
                      v-if="nextContractStatusStep"
                      type="button"
                      :disabled="updatingStatus"
                      class="inline-flex w-full min-w-0 items-center justify-center gap-2 rounded-xl border border-[var(--clm-brand)]/30 bg-[var(--clm-brand-soft)] px-3 py-2.5 text-[11px] font-black tracking-wide text-[var(--clm-brand-strong)] shadow-sm shadow-[var(--clm-brand)]/20 ring-1 ring-[var(--clm-brand)]/10 transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--clm-brand)]/45 hover:bg-[var(--clm-brand)]/18 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:border-[var(--clm-brand)]/40 dark:bg-[var(--clm-brand)]/20 dark:text-[var(--clm-text)] dark:hover:bg-[var(--clm-brand)]/28"
                      @click="advanceToNextContractStatus"
                    >
                      <span class="min-w-0 text-balance">Go to next stage: {{ nextContractStatusStep.label }}</span>
                      <svg class="h-3.5 w-3.5 shrink-0 opacity-90" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </button>
                    <p v-else class="text-[11px] leading-snug text-[var(--clm-text-muted)]">
                      This contract is already at the last stage on this path.
                    </p>
                  </div>
                </div>

                <!-- Quick links -->
                <div class="clm-pulse-strip__quick @container flex min-h-0 min-w-0 flex-col p-3 sm:p-4">
                  <div>
                    <p class="text-[10px] font-black uppercase tracking-[0.16em] text-[var(--clm-text-muted)] sm:text-[11px]">
                      Quick links
                    </p>
                  </div>
                  <nav
                    class="mt-2.5 grid min-w-0 gap-1.5"
                    aria-label="Contract quick navigation"
                  >
                    <button
                      v-for="tab in contractTabs"
                      :key="tab.id"
                      type="button"
                      :title="tab.premium ? `${tab.label} (Premium)` : tab.label"
                      :aria-label="tab.premium ? `${tab.label}, premium` : tab.label"
                      :aria-current="activeTab === tab.id || undefined"
                      @click="selectTab(tab.id)"
                      class="group relative flex min-w-0 flex-col items-center justify-center overflow-hidden rounded-xl border p-1.5 shadow-sm transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--clm-brand)]/45 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--clm-bg-surface)] active:scale-[0.97] sm:p-2"
                      :class="
                        activeTab === tab.id
                          ? 'border-[var(--clm-brand)]/45 bg-gradient-to-br from-[var(--clm-brand-soft)] via-[var(--clm-bg-surface)] to-[var(--clm-brand)]/[0.12] text-[var(--clm-brand-strong)] shadow-[0_4px_12px_-2px_rgba(37,99,235,0.2)] ring-1 ring-[var(--clm-brand)]/20 dark:from-[var(--clm-brand-soft)] dark:via-[var(--clm-bg-surface)] dark:to-[var(--clm-brand)]/20 dark:text-[var(--clm-text)] dark:shadow-[0_4px_14px_-3px_rgba(59,130,246,0.3)]'
                          : 'border-[var(--clm-border)]/60 bg-[var(--clm-bg-surface)]/90 text-[var(--clm-text-muted)] backdrop-blur-[2px] hover:-translate-y-0.5 hover:border-[var(--clm-brand)]/35 hover:bg-[var(--clm-bg-overlay)] hover:text-[var(--clm-text)] hover:shadow-md dark:bg-[var(--clm-bg-overlay)]/40'
                      "
                    >
                      <span
                        class="pointer-events-none absolute inset-0 opacity-0 transition duration-200 group-hover:opacity-100"
                        aria-hidden="true"
                      >
                        <span class="absolute inset-x-2 -top-px h-px bg-gradient-to-r from-transparent via-[var(--clm-brand)]/25 to-transparent opacity-60" />
                      </span>
                      <span
                        v-if="tab.premium"
                        class="pointer-events-none absolute right-1 top-1 z-10 h-1.5 w-1.5 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 shadow-sm ring-1 ring-[var(--clm-bg-surface)] dark:ring-[var(--clm-bg-surface)]"
                        aria-hidden="true"
                      />
                      <span
                        class="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--clm-bg-overlay)]/80 ring-1 ring-[var(--clm-border)]/50 transition duration-200 group-hover:bg-[var(--clm-bg-overlay)] sm:h-9 sm:w-9"
                        :class="
                          activeTab === tab.id
                            ? 'bg-[var(--clm-brand)]/[0.12] ring-[var(--clm-brand)]/30 group-hover:bg-[var(--clm-brand)]/[0.14]'
                            : ''
                        "
                      >
                      <!-- Overview -->
                      <svg
                        v-if="tab.id === 'overview'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                      </svg>
                      <!-- Contract Changes -->
                      <svg
                        v-else-if="tab.id === 'milestones'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                      <!-- CPWD Copilot -->
                      <svg
                        v-else-if="tab.id === 'cpwd-copilot'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <!-- Guidelines -->
                      <svg
                        v-else-if="tab.id === 'guidelines'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      <!-- Compliance -->
                      <svg
                        v-else-if="tab.id === 'compliance'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      <!-- History -->
                      <svg
                        v-else-if="tab.id === 'history'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <!-- Scoring -->
                      <svg
                        v-else-if="tab.id === 'scoring'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      <!-- Graph -->
                      <svg
                        v-else-if="tab.id === 'graph'"
                        class="h-4.5 w-4.5 shrink-0 sm:h-5 sm:w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                      </span>
                      <span class="mt-1.5 hidden text-[9px] font-bold leading-none tracking-tight @[18rem]:block">
                        {{ tab.label }}
                      </span>
                    </button>
                  </nav>
                  <!-- Guideline widget shown when a framework is attached to this contract -->
                  <div v-if="contract?.guideline_framework_slug" class="mt-auto border-t border-[var(--clm-border)] pt-3">
                    <GuidelineAttachmentWidget
                      :framework="{
                        slug: contract.guideline_framework_slug,
                        title: contract.guideline_framework_title || contract.guideline_framework_slug,
                        version_label: null,
                      }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

            <!-- Right Side: tabs & status — full width when preview is in slide-over (not on Graph tab) -->
            <div
              class="min-w-0 space-y-6"
              :class="activeTab === 'graph' ? 'lg:col-span-1' : 'lg:col-span-3'"
            >
              <!-- Tabs Navigation — segmented control -->
              <div
                class="flex flex-wrap gap-1 rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.45)] backdrop-blur-sm dark:shadow-[inset_0_1px_0_rgba(0,0,0,0.45)]"
                role="tablist"
                aria-label="Contract sections"
              >
                <button
                  v-for="tab in contractTabs"
                  :key="tab.id"
                  type="button"
                  role="tab"
                  :aria-selected="activeTab === tab.id"
                  @click="selectTab(tab.id)"
                  class="min-w-[4.25rem] flex-1 rounded-lg px-2 py-2.5 text-center text-[11px] font-semibold tracking-tight transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--clm-brand)]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--clm-bg-overlay)] dark:focus-visible:ring-offset-[var(--clm-bg-surface)]"
                  :class="
                    activeTab === tab.id
                      ? 'bg-[var(--clm-bg-surface)] text-[var(--clm-text)] shadow-sm ring-1 ring-[var(--clm-border)] dark:bg-[var(--clm-brand-soft)] dark:text-[var(--clm-text)] dark:ring-[var(--clm-brand)]/35'
                      : 'text-[var(--clm-text-muted)] hover:bg-[var(--clm-bg-surface)]/90 hover:text-[var(--clm-text)] dark:hover:bg-[var(--clm-bg-surface-elevated)]'
                  "
                >
                  <span class="inline-flex flex-col items-center gap-0.5 leading-tight">
                    <span
                      v-if="tab.premium"
                      class="text-[8px] font-black uppercase tracking-wider text-amber-600 dark:text-amber-400"
                    >Premium</span>
                    <span>{{ tab.label }}</span>
                  </span>
                </button>
              </div>

              <!-- Tab Content -->
              <div class="space-y-6">
                <!-- Overview Tab -->
                <div v-if="activeTab === 'overview'" class="space-y-5">
                  <WorkingVersionPicker
                    v-if="sortedDocumentVersions.length"
                    :versions="sortedDocumentVersions"
                    :selected-id="selectedVersionId"
                    @select="(v) => viewVersion(v)"
                  />

                  <!-- Contract status — hero + metrics rail -->
                  <section
                    class="overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm ring-1 ring-[var(--clm-border)]/40 backdrop-blur-sm dark:ring-[var(--clm-brand)]/12"
                  >
                    <div class="relative">
                      <div
                        class="pointer-events-none absolute inset-0 bg-gradient-to-br from-[var(--clm-brand)]/[0.08] via-transparent to-indigo-500/[0.07] dark:from-[var(--clm-brand)]/[0.12] dark:to-indigo-600/10"
                        aria-hidden="true"
                      />
                      <div class="relative px-4 py-5 sm:px-6 sm:py-6">
                        <p class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--clm-text-muted)]">
                          Contract status
                        </p>
                        <div class="mt-4 flex flex-col gap-6 lg:flex-row lg:items-stretch lg:gap-8">
                          <div class="flex shrink-0 items-center gap-4 lg:max-w-md">
                        <div
                          class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border"
                          :class="statusHeroClass(contract?.status)"
                        >
                          <svg
                            v-if="(contract?.status || '').toLowerCase() === 'active'"
                            class="h-7 w-7"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="2"
                            aria-hidden="true"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <svg
                            v-else-if="(contract?.status || '').toLowerCase() === 'signing'"
                            class="h-7 w-7"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="2"
                            aria-hidden="true"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                          <svg
                            v-else-if="(contract?.status || '').toLowerCase() === 'draft'"
                            class="h-7 w-7"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="2"
                            aria-hidden="true"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                          </svg>
                          <svg
                            v-else
                            class="h-7 w-7"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="2"
                            aria-hidden="true"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                            />
                          </svg>
                        </div>
                            <div class="min-w-0 flex-1">
                              <p class="text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--clm-text-muted)]">
                                Current phase
                              </p>
                              <p class="mt-1 text-2xl font-bold capitalize tracking-tight text-[var(--clm-text)] sm:text-3xl">
                                {{ contract?.status || '—' }}
                              </p>
                            </div>
                          </div>

                          <dl class="min-w-0 flex-1 rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/70 px-5 py-3 backdrop-blur-sm dark:bg-[var(--clm-bg-overlay)]/90">
                            <dt class="text-[10px] font-bold uppercase tracking-wide text-[var(--clm-text-muted)]">Start</dt>
                            <dd class="mt-1 text-base font-bold text-[var(--clm-text)] sm:text-lg">{{ formatDate(contract?.start_date) }}</dd>
                          </dl>
                        </div>
                      </div>
                    </div>
                  </section>

                  <!-- Signers by version — only visible in signing/signed states -->
                  <section
                    v-if="['signing','approved','active'].includes((contract?.status || '').toLowerCase())"
                    ref="overviewSignersSectionRef"
                    tabindex="-1"
                    class="scroll-mt-24 overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-gradient-to-b from-[var(--clm-bg-surface)] to-[var(--clm-bg-overlay)]/60 shadow-sm outline-none ring-offset-2 ring-offset-[var(--clm-bg-page)] focus-visible:ring-2 focus-visible:ring-[var(--clm-brand)] dark:to-[var(--clm-bg-overlay)]/40"
                  >
                    <!-- header -->
                    <header class="flex items-center justify-between gap-2 border-b border-[var(--clm-border)] px-4 py-2.5">
                      <div class="flex items-center gap-2.5">
                        <h3 class="text-[10px] font-black uppercase tracking-[0.18em] text-[var(--clm-text-muted)]">Signers</h3>
                        <span v-if="selectedVersion" class="rounded-full bg-[var(--clm-brand)]/10 px-1.5 py-px text-[9px] font-bold text-[var(--clm-brand)] tabular-nums">
                          v{{ selectedVersion.version_number }}<span v-if="selectedVersion.is_latest"> · Latest</span>
                        </span>
                      </div>
                      <div class="relative z-10 flex items-center gap-1.5">
                        <button
                          v-if="selectedVersion && (contract?.status || '').toLowerCase() === 'signing'"
                          type="button"
                          class="inline-flex items-center gap-1 rounded-lg border border-[var(--clm-border)] px-2.5 py-1 text-[10px] font-bold text-[var(--clm-text-muted)] transition hover:bg-[var(--clm-bg-overlay)] hover:text-[var(--clm-text)]"
                          title="Configure signature fields on document"
                          @click="goPrepareSignature"
                        >
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                          Prepare
                        </button>
                      </div>
                    </header>

                    <!-- version tabs -->
                    <div v-if="contract?.document_versions?.length" class="px-3 sm:px-4">
                      <div class="-mb-px flex gap-1 overflow-x-auto border-b border-[var(--clm-border)]" role="tablist">
                        <button
                          v-for="ver in contract?.document_versions"
                          :key="ver.id"
                          type="button"
                          role="tab"
                          :aria-selected="selectedVersionId === ver.id"
                          @click="selectAndViewVersion(ver)"
                          class="-mb-px flex shrink-0 items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition"
                          :class="selectedVersionId === ver.id ? 'border-[var(--clm-brand)] text-[var(--clm-text)]' : 'border-transparent text-[var(--clm-text-muted)] hover:border-[var(--clm-border)] hover:text-[var(--clm-text)]'"
                        >
                          <span class="tabular-nums">v{{ ver.version_number }}</span>
                          <span v-if="ver.is_latest" class="rounded bg-sky-500/15 px-1 py-px text-[8px] font-black uppercase text-sky-800 dark:bg-sky-500/20 dark:text-sky-200">Latest</span>
                        </button>
                      </div>
                    </div>

                    <!-- signer rows -->
                    <div class="pt-1 pb-1">
                      <div v-if="selectedVersion">
                        <!-- empty -->
                        <div v-if="!selectedVersion.version_signers?.length" class="flex items-center justify-center gap-3 px-5 py-6 text-center">
                          <div>
                            <p class="text-[11px] text-[var(--clm-text-muted)]">No signers yet for this version.</p>
                            <p class="mt-1 text-[10px] text-[var(--clm-text-muted)]/80">Use <strong class="font-bold text-[var(--clm-text)]">Add Signer</strong> above. While the contract is in <strong class="font-bold text-[var(--clm-text)]">Signing</strong>, use <strong class="font-bold text-[var(--clm-text)]">Prepare</strong> to place signature fields.</p>
                          </div>
                        </div>

                        <!-- signer list (compact rows) -->
                        <ul v-else class="divide-y divide-[var(--clm-border)]" aria-label="Signers">
                          <li
                            v-for="vs in selectedVersion.version_signers"
                            :key="vs.id"
                            class="group flex items-center gap-3 px-4 py-2.5 transition hover:bg-[var(--clm-bg-overlay)]/50"
                          >
                            <!-- avatar -->
                            <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--clm-bg-overlay)] text-[11px] font-bold text-[var(--clm-text)] ring-1 ring-[var(--clm-border)]">
                              {{ vs.master_signer?.name?.charAt(0) || '?' }}
                            </div>
                            <!-- name + meta -->
                            <div class="min-w-0 flex-1">
                              <p class="truncate text-[12px] font-semibold text-[var(--clm-text)]">{{ vs.master_signer?.name }}</p>
                              <p class="truncate text-[10px] text-[var(--clm-text-muted)]">{{ vs.master_signer?.email }}<span v-if="vs.master_signer?.organization"> · {{ vs.master_signer?.organization }}</span></p>
                            </div>
                            <!-- status + actions -->
                            <div class="flex shrink-0 items-center gap-2">
                              <span
                                class="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase"
                                :class="vs.status === 'signed' ? 'bg-emerald-500/15 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300' : vs.status === 'declined' ? 'bg-red-500/15 text-red-800 dark:bg-red-500/20 dark:text-red-300' : 'bg-amber-500/15 text-amber-900 dark:bg-amber-500/20 dark:text-amber-200'"
                              >{{ vs.status }}</span>
                              <template v-if="vs.status !== 'signed'">
                                <button type="button" class="text-[10px] font-semibold text-sky-600 hover:underline dark:text-sky-400" @click="copySigningLink(vs.token)">Copy link</button>
                                <router-link :to="`/sign/${vs.token}`" class="text-[10px] font-semibold text-emerald-700 hover:underline dark:text-emerald-400">Sign</router-link>
                                <button type="button" class="hidden text-[10px] font-bold text-red-500 hover:underline group-hover:block" @click="removeSignerFromVersion(vs.id)">Remove</button>
                              </template>
                              <template v-else>
                                <span class="text-[10px] text-[var(--clm-text-muted)]">{{ vs.signed_at ? new Date(vs.signed_at).toLocaleDateString() : '' }}</span>
                              </template>
                            </div>
                          </li>
                        </ul>
                      </div>
                      <div v-else class="px-5 py-6 text-center text-[11px] text-slate-400 dark:text-[var(--clm-text-muted)]">No document versions yet.</div>
                    </div>
                  </section>
                </div>

                <!-- Milestones Tab -->
                <div v-if="activeTab === 'milestones'" class="rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm overflow-hidden">
                  <!-- Header bar -->
                  <div class="flex items-center justify-between border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-2.5">
                    <div class="flex items-center gap-2.5">
                      <h3 class="text-[11px] font-bold uppercase tracking-widest text-[var(--clm-text)]">Contract Changes</h3>
                      <span class="rounded-full bg-[var(--clm-brand)]/10 px-2 py-0.5 text-[10px] font-bold text-[var(--clm-brand)]">
                        {{ contract?.milestones?.filter(m => m.status?.toLowerCase() === 'completed').length || 0 }} / {{ contract?.milestones?.length || 0 }}
                      </span>
                    </div>
                    <button @click="showMilestoneModal = true" class="inline-flex items-center gap-1 rounded-lg bg-[var(--clm-brand)] px-2.5 py-1 text-[10px] font-bold text-white transition hover:bg-[var(--clm-brand-strong)]">
                      <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                      Add
                    </button>
                  </div>

                  <!-- Empty state -->
                  <div v-if="!contract?.milestones?.length" class="py-10 text-center text-sm text-[var(--clm-text-muted)]">
                    No milestones yet
                  </div>

                  <!-- Compact milestone rows -->
                  <div v-else>
                    <div
                      v-for="(milestone, idx) in contract?.milestones"
                      :key="milestone.id"
                      class="group relative flex items-center gap-3 px-4 py-2 transition hover:bg-[var(--clm-bg-overlay)]"
                      :class="idx < contract.milestones.length - 1 ? 'border-b border-[var(--clm-border)]' : ''"
                    >
                      <!-- Status dot + connector line -->
                      <div class="relative flex w-5 shrink-0 flex-col items-center">
                        <div
                          class="h-2.5 w-2.5 rounded-full ring-2 ring-[var(--clm-bg-surface)] transition"
                          :class="milestone.status?.toLowerCase() === 'completed' ? 'bg-green-500' : milestone.status?.toLowerCase() === 'delayed' ? 'bg-red-400' : 'bg-blue-400'"
                        ></div>
                        <!-- Vertical line connecting dots (all but last) -->
                        <div
                          v-if="idx < contract.milestones.length - 1"
                          class="absolute top-3.5 h-[calc(100%+0.5rem)] w-px bg-[var(--clm-border)]"
                        ></div>
                      </div>

                      <!-- Title -->
                      <div class="min-w-0 flex-1">
                        <span class="truncate text-[12px] font-semibold text-[var(--clm-text)]">{{ milestone.title }}</span>
                        <span v-if="milestone.description" class="ml-1.5 hidden truncate text-[10px] text-[var(--clm-text-muted)] group-hover:inline">· {{ milestone.description }}</span>
                      </div>

                      <!-- Due date -->
                      <span class="shrink-0 text-[10px] tabular-nums text-[var(--clm-text-muted)]">{{ formatDate(milestone.due_date) }}</span>

                      <!-- Status badge (static) + select (on hover) -->
                      <div class="shrink-0">
                        <span
                          class="block text-[9px] font-bold uppercase tracking-wide group-hover:hidden"
                          :class="milestone.status?.toLowerCase() === 'completed' ? 'text-green-600' : milestone.status?.toLowerCase() === 'delayed' ? 'text-red-500' : 'text-blue-500'"
                        >{{ milestone.status }}</span>
                        <select
                          class="hidden group-hover:block rounded border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] py-0.5 pl-1.5 pr-5 text-[10px] font-bold text-[var(--clm-text)] focus:outline-none"
                          :value="milestone.status"
                          @change="updateMilestone(milestone, $event.target.value)"
                        >
                          <option value="pending">PENDING</option>
                          <option value="completed">COMPLETED</option>
                          <option value="delayed">DELAYED</option>
                        </select>
                      </div>

                      <!-- Expand toggle for description -->
                      <button
                        v-if="milestone.description"
                        @click="milestone.isOpen = !milestone.isOpen"
                        class="shrink-0 rounded p-0.5 text-[var(--clm-text-muted)] transition hover:text-[var(--clm-text)]"
                      >
                        <svg class="h-3.5 w-3.5 transition-transform" :class="{ 'rotate-180': milestone.isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                      </button>
                    </div>

                    <!-- Description expansion panel (below its row) -->
                    <template v-for="milestone in contract?.milestones" :key="`desc-${milestone.id}`">
                      <div
                        v-if="milestone.isOpen && milestone.description"
                        class="border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-10 py-2 text-[11px] leading-relaxed text-[var(--clm-text-muted)]"
                      >
                        {{ milestone.description }}
                      </div>
                    </template>
                  </div>
                </div>

                <!-- CPWD Copilot (premium) — agent-side context injection -->
                <div
                  v-if="activeTab === 'cpwd-copilot'"
                  class="space-y-4 overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] p-5 shadow-sm dark:border-[var(--clm-border)]"
                >
                  <div>
                    <p class="text-sm font-semibold text-[var(--clm-text)]">How it works</p>
                    <p class="mt-2 text-sm leading-relaxed text-[var(--clm-text-muted)]">
                      With Review or Draft open in the assistant, enable CPWD Copilot below the agent strip. Each message then
                      includes guideline snapshot, compliance rows for the working version, and latest scoring. Draft also adds
                      saved review items to the context pack; Review does not, so the agent is not primed with items you
                      previously saved—use “Save to review items” only when you want to keep something for redraft.
                    </p>
                  </div>
                  <label class="flex cursor-pointer items-start gap-3 rounded-xl border border-amber-200/80 bg-amber-50/40 p-3 dark:border-amber-900/40 dark:bg-amber-950/25">
                    <input v-model="cpwdCopilotEnabled" type="checkbox" class="mt-0.5 rounded border-amber-400 text-amber-700 focus:ring-amber-500" />
                    <span class="min-w-0">
                      <span class="text-sm font-medium text-[var(--clm-text)]">Enable CPWD Copilot for this contract</span>
                      <span class="mt-1 block text-xs text-[var(--clm-text-muted)]">
                        Preference is saved in this browser. Send a bearer token with requests when your deployment enforces premium access.
                      </span>
                      <span
                        v-if="authStore.user && authStore.user.premium_access === false"
                        class="mt-2 block text-xs text-red-600 dark:text-red-400"
                      >
                        This account is not marked for premium access; the server may reject augmentation if enforcement is on.
                      </span>
                    </span>
                  </label>
                </div>

                <!-- Guidelines Tab (editable snapshot for AI automation) -->
                <div v-if="activeTab === 'guidelines'" class="space-y-6">
                  <ContractGuidelinesPanel
                    :contract-id="contractId"
                    :guideline-framework-slug="contract?.guideline_framework_slug"
                    :guideline-framework-title="contract?.guideline_framework_title"
                    :guideline-financial-limits="contract?.guideline_financial_limits"
                    :guideline-mandatory-clauses="contract?.guideline_mandatory_clauses"
                    :guideline-technical-standards="contract?.guideline_technical_standards"
                    :guideline-compliance-requirements="contract?.guideline_compliance_requirements"
                    :guideline-contractor-eligibility="contract?.guideline_contractor_eligibility"
                    :guideline-work-execution-standards="contract?.guideline_work_execution_standards"
                    :guideline-measurement-payment="contract?.guideline_measurement_payment"
                    :guideline-contract-administration="contract?.guideline_contract_administration"
                    :guideline-defect-liability="contract?.guideline_defect_liability"
                    :guideline-documentation-requirements="contract?.guideline_documentation_requirements"
                    :guideline-decision-thresholds="contract?.guideline_decision_thresholds"
                    :guideline-validation-weights="contract?.guideline_validation_weights"
                    :guideline-critical-issues="contract?.guideline_critical_issues"
                    @saved="onGuidelineSaved"
                    @send-to-agent="onGuidelineSendToAgent"
                  />
                </div>

                <!-- Scoring Tab -->
                <div v-if="activeTab === 'scoring'">
                  <div class="overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm">

                    <WorkingVersionPicker
                      v-if="sortedDocumentVersions.length"
                      :versions="sortedDocumentVersions"
                      :selected-id="selectedVersionId"
                      embedded
                      @select="(v) => viewVersion(v)"
                    />

                    <!-- header bar -->
                    <div class="flex items-center justify-between border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-2.5">
                      <h3 class="text-[11px] font-bold uppercase tracking-widest text-[var(--clm-text)]">Contract Scoring</h3>
                      <div class="flex items-center gap-2">
                        <button
                          @click="triggerScoring"
                          :disabled="scoringTriggering || scoringLoading || scoringBackgroundRunning"
                          class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[10px] font-bold text-white transition disabled:opacity-50"
                          :class="scoringTriggering || scoringBackgroundRunning ? 'bg-amber-600' : 'bg-[var(--clm-brand)] hover:opacity-90'"
                        >
                          <span v-if="scoringTriggering || scoringBackgroundRunning" class="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                          <svg v-else class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                          {{ scoringTriggering ? 'Running Agents…' : scoringBackgroundRunning ? 'Scoring in progress…' : (scoringData ? 'Re-run Scoring' : 'Trigger Scoring') }}
                        </button>
                        <button v-if="scoringData" @click="showScoringRaw = !showScoringRaw" class="text-[10px] font-bold text-[var(--clm-text-muted)] hover:text-[var(--clm-brand)]">
                          {{ showScoringRaw ? 'Hide JSON' : 'Raw JSON' }}
                        </button>
                      </div>
                    </div>

                    <!-- loading -->
                    <div v-if="scoringLoading || scoringTriggering || scoringBackgroundRunning" class="flex flex-col items-center justify-center gap-2 py-8">
                      <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--clm-brand)] border-t-transparent"></div>
                      <span class="text-[11px] text-[var(--clm-text-muted)]">{{ scoringTriggering ? 'Running multi-agent scoring workflow…' : scoringBackgroundRunning ? 'Running multi-agent scoring workflow in the background…' : 'Loading…' }}</span>
                    </div>

                    <!-- error -->
                    <div v-else-if="scoringError" class="flex items-center justify-between px-4 py-3">
                      <span class="text-[11px] text-amber-600 dark:text-amber-400">{{ scoringError }}</span>
                      <button @click="fetchScoring" class="rounded bg-[var(--clm-brand)] px-2.5 py-1 text-[10px] font-bold text-white">Retry</button>
                    </div>

                    <!-- data -->
                    <div v-else-if="scoringData">

                      <!-- financial one-liner -->
                      <div v-if="scoringData.finance_analysis" class="border-b border-[var(--clm-border)] px-4 py-2.5">
                        <button
                          type="button"
                          class="flex w-full items-center gap-3 text-left"
                          @click="scoringData.finance_analysis._expanded = !scoringData.finance_analysis._expanded"
                        >
                          <span class="text-[10px] font-bold uppercase text-[var(--clm-text-muted)]">Financial</span>
                          <span class="text-base font-black text-[var(--clm-text)]">{{ scoringData.finance_analysis.overall_compliance_score }}%</span>
                          <span class="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase" :class="(scoringData.finance_analysis.approval_recommendation || '').toLowerCase() === 'approve' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'">{{ scoringData.finance_analysis.approval_recommendation || '—' }}</span>
                          <span v-if="scoringData.finance_analysis.executive_summary" class="hidden flex-1 text-[10px] text-[var(--clm-text-muted)] sm:block" :class="scoringData.finance_analysis._expanded ? 'whitespace-pre-wrap' : 'truncate'">{{ scoringData.finance_analysis.executive_summary }}</span>
                          <svg class="h-3.5 w-3.5 shrink-0 text-[var(--clm-text-muted)] transition-transform" :class="{ 'rotate-180': scoringData.finance_analysis._expanded }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                        </button>
                      </div>

                      <!-- validation rows -->
                      <div v-if="scoringData.validation_results?.length">
                        <!-- section label -->
                        <div class="border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-1.5">
                          <span class="text-[9px] font-bold uppercase tracking-widest text-[var(--clm-text-muted)]">Validation by category</span>
                        </div>

                        <div v-for="(vr, idx) in scoringData.validation_results" :key="idx" class="border-b border-[var(--clm-border)] last:border-0">
                          <!-- category row -->
                          <button
                            type="button"
                            @click="vr._open = !vr._open"
                            class="flex w-full items-center gap-2 px-4 py-2 text-left transition hover:bg-[var(--clm-bg-overlay)]"
                          >
                            <div class="h-2 w-2 shrink-0 rounded-full" :class="(vr.compliance_status || '').toLowerCase() === 'pass' ? 'bg-green-500' : (vr.compliance_status || '').toLowerCase() === 'fail' ? 'bg-red-400' : 'bg-amber-400'"></div>
                            <span class="flex-1 truncate text-[12px] font-semibold capitalize text-[var(--clm-text)]">{{ (vr.agent_type || '').replace(/_/g, ' ') }}</span>
                            <span class="shrink-0 text-[12px] font-black tabular-nums" :class="scoreColor(vr.overall_score)">{{ typeof vr.overall_score === 'number' ? vr.overall_score.toFixed(1) : vr.overall_score }}%</span>
                            <span class="shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase" :class="statusBadgeClass(vr.compliance_status)">{{ vr.compliance_status || '—' }}</span>
                            <svg class="h-3.5 w-3.5 shrink-0 text-[var(--clm-text-muted)] transition-transform" :class="{ 'rotate-180': vr._open }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                          </button>

                          <!-- expanded content -->
                          <div v-show="vr._open" class="border-t border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]">

                            <!-- category score chips -->
                            <div v-if="vr.category_scores && typeof vr.category_scores === 'object'" class="flex flex-wrap gap-1.5 border-b border-[var(--clm-border)] px-4 py-2">
                              <span v-for="(score, cat) in vr.category_scores" :key="cat" class="rounded bg-[var(--clm-bg-surface-elevated)] px-2 py-0.5 text-[10px] font-medium text-[var(--clm-text)]">
                                {{ (cat + '').replace(/_/g, ' ') }}: <strong>{{ typeof score === 'number' ? score.toFixed(0) : score }}</strong>
                              </span>
                            </div>

                            <!-- findings -->
                            <div v-if="vr.findings?.length">
                              <div class="border-b border-[var(--clm-border)] px-4 py-1 text-[9px] font-bold uppercase tracking-widest text-[var(--clm-text-muted)]">Findings</div>
                              <div v-for="(group, gi) in mergedFindingsByCategory(vr.findings)" :key="gi" class="border-b border-[var(--clm-border)] last:border-0">
                                <button type="button" @click="toggleScoringAccordion(`vr-${idx}-g-${gi}`)" class="flex w-full items-center gap-2 pl-7 pr-4 py-1.5 text-left transition hover:bg-[var(--clm-bg-surface-elevated)]">
                                  <span class="flex-1 truncate text-[11px] font-medium text-[var(--clm-text)]">{{ group.category }}</span>
                                  <span v-if="group.items.length > 1" class="shrink-0 text-[9px] text-[var(--clm-text-muted)]">({{ group.items.length }})</span>
                                  <span class="shrink-0 rounded px-1 py-0.5 text-[8px] font-bold uppercase" :class="(group.worstStatus || '').toUpperCase() === 'NON_COMPLIANT' || (group.worstStatus || '').toUpperCase() === 'CRITICAL' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' : (group.worstStatus || '').toUpperCase() === 'PARTIAL' || (group.worstStatus || '').toUpperCase().includes('HIGH') ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' : 'bg-gray-200 text-gray-600 dark:bg-gray-600 dark:text-gray-300'">{{ group.worstStatus }}</span>
                                  <svg class="h-3 w-3 shrink-0 text-[var(--clm-text-muted)] transition-transform" :class="{ 'rotate-180': openScoringAccordions[`vr-${idx}-g-${gi}`] }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                                </button>
                                <div v-show="openScoringAccordions[`vr-${idx}-g-${gi}`]" class="border-t border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] pl-10 pr-4 py-2 space-y-1">
                                  <div v-for="(item, ii) in group.items" :key="ii" class="text-[11px] leading-relaxed text-[var(--clm-text-muted)]">
                                    <span v-if="group.items.length > 1" class="mr-1 font-semibold">{{ ii + 1 }}.</span>{{ item.issue || item.finding }}
                                  </div>
                                </div>
                              </div>
                            </div>

                            <!-- recommendations -->
                            <div v-if="vr.recommendations?.length">
                              <div class="border-b border-[var(--clm-border)] px-4 py-1 text-[9px] font-bold uppercase tracking-widest text-[var(--clm-text-muted)]">Recommendations</div>
                              <div v-for="(rec, ri) in vr.recommendations" :key="ri" class="border-b border-[var(--clm-border)] last:border-0">
                                <button type="button" @click="toggleScoringAccordion(`vr-${idx}-r-${ri}`)" class="flex w-full items-center gap-2 pl-7 pr-4 py-1.5 text-left transition hover:bg-[var(--clm-bg-surface-elevated)]">
                                  <span class="line-clamp-1 flex-1 text-[11px] font-medium text-[var(--clm-text)]">{{ accordionRecTitle(rec, ri) }}</span>
                                  <svg class="h-3 w-3 shrink-0 text-[var(--clm-text-muted)] transition-transform" :class="{ 'rotate-180': openScoringAccordions[`vr-${idx}-r-${ri}`] }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                                </button>
                                <div v-show="openScoringAccordions[`vr-${idx}-r-${ri}`]" class="border-t border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] pl-10 pr-4 py-2 text-[11px] leading-relaxed text-[var(--clm-text-muted)]">
                                  {{ typeof rec === 'string' ? rec : (rec.recommendation || rec) }}
                                </div>
                              </div>
                            </div>

                          </div>
                        </div>
                      </div>

                      <!-- raw JSON -->
                      <pre v-if="showScoringRaw" class="border-t border-[var(--clm-border)] max-h-80 overflow-auto bg-[#0a1628] px-4 py-3 text-[10px] text-green-300">{{ JSON.stringify(scoringData, null, 2) }}</pre>
                    </div>

                    <div v-else class="flex flex-col items-center gap-3 px-4 py-10 text-center">
                      <svg class="h-8 w-8 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                      <p class="text-[11px] text-[var(--clm-text-muted)]">No scoring data yet.</p>
                      <button @click="triggerScoring" :disabled="scoringTriggering" class="flex items-center gap-1.5 rounded-lg bg-[var(--clm-brand)] px-4 py-2 text-[11px] font-bold text-white transition hover:opacity-90 disabled:opacity-50">
                        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        Trigger Scoring
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Knowledge graph: per-version JSON from GET …/knowledge-graph (same version picker as Compliance / Scoring) -->
                <div v-if="activeTab === 'graph'" class="space-y-3">
                  <div
                    class="flex h-[min(80vh,calc(100vh-14rem))] min-h-[40vh] flex-col overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm"
                  >
                    <WorkingVersionPicker
                      v-if="sortedDocumentVersions.length"
                      :versions="sortedDocumentVersions"
                      :selected-id="selectedVersionId"
                      embedded
                      @select="(v) => viewVersion(v)"
                    />
                    <div class="flex min-w-0 flex-col gap-2 border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between sm:gap-3 sm:px-4">
                      <div class="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
                        <h3 class="shrink-0 text-[11px] font-bold uppercase tracking-widest text-[var(--clm-text)]">Knowledge graph</h3>
                        <div
                          class="inline-flex rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-page)] p-0.5"
                          role="tablist"
                          aria-label="Graph view"
                        >
                          <button
                            type="button"
                            role="tab"
                            class="rounded-md px-3 py-1.5 text-[11px] font-bold transition"
                            :class="graphViewMode === 'overview' ? 'bg-[var(--clm-bg-surface-elevated)] text-[var(--clm-text)] shadow-sm' : 'text-[var(--clm-text-muted)] hover:text-[var(--clm-text)]'"
                            :aria-selected="graphViewMode === 'overview'"
                            @click="graphViewMode = 'overview'"
                          >
                            Overview
                          </button>
                          <button
                            type="button"
                            role="tab"
                            class="rounded-md px-3 py-1.5 text-[11px] font-bold transition"
                            :class="graphViewMode === 'map' ? 'bg-[var(--clm-bg-surface-elevated)] text-[var(--clm-text)] shadow-sm' : 'text-[var(--clm-text-muted)] hover:text-[var(--clm-text)]'"
                            :aria-selected="graphViewMode === 'map'"
                            @click="graphViewMode = 'map'"
                          >
                            Interactive map
                          </button>
                        </div>
                      </div>
                      <button
                        type="button"
                        class="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-[var(--clm-brand)] px-3 py-1.5 text-[10px] font-bold text-white transition hover:opacity-90 disabled:opacity-50"
                        :disabled="knowledgeGraphBuilding || !selectedVersionId || !workingVersion?.file_id"
                        :title="workingVersion?.file_id ? `Build graph from chunks for v${workingVersion.version_number}` : 'Select a version with a document'"
                        @click="buildKnowledgeGraph"
                      >
                        <span
                          v-if="knowledgeGraphBuilding"
                          class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"
                        />
                        <svg v-else class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                        {{ knowledgeGraphBuilding ? 'Building…' : 'Build knowledge graph' }}
                      </button>
                    </div>
                  <div class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--clm-bg-page)] lg:flex-row">
                  <div class="min-h-0 min-w-0 flex-1 bg-[var(--clm-bg-page)]">
                    <KnowledgeGraphInsights
                      v-if="graphViewMode === 'overview'"
                      ref="knowledgeGraphInsightsRef"
                      class="h-full"
                      :data-url="knowledgeGraphDataUrl"
                      :reload-key="knowledgeGraphReloadKey"
                      @switch-to-map="graphViewMode = 'map'"
                    />
                    <ContractGraphExplorer
                      v-else
                      ref="graphExplorerRef"
                      class="h-full"
                      :data-url="knowledgeGraphDataUrl"
                    />
                  </div>
                  <aside
                    v-if="showGraphChatPanel && !showChat"
                    class="flex min-h-0 w-full shrink-0 flex-col border-t border-[var(--clm-border)] bg-gradient-to-b from-[var(--clm-bg-overlay)] to-[var(--clm-bg-surface)] lg:h-full lg:w-[clamp(290px,34vw,430px)] lg:border-l lg:border-t-0"
                  >
                    <div class="border-b border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-4 py-3 backdrop-blur dark:bg-[var(--clm-bg-surface-elevated)]">
                      <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.08em] text-[var(--clm-text-muted)]">
                        <span class="inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/40"></span>
                        <span class="text-[var(--clm-text)]">Graph Copilot</span>
                        <button
                          type="button"
                          class="ml-auto inline-flex rounded-full border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-2.5 py-1 font-semibold text-[10px] text-[var(--clm-text-muted)] shadow-sm transition hover:text-[var(--clm-text)]"
                          @click="showGraphChatPanel = false"
                        >
                          Collapse
                        </button>
                      </div>
                      <p class="mt-1 text-[10px] text-[var(--clm-text-muted)]">Ask about entities, relationships, or clause structure.</p>
                    </div>
                    <div class="clm-agent-chat-scroll min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-3" id="graph-chat-messages">
                      <div
                        v-for="(msg, idx) in chatMessages.graph"
                        :key="`graph-msg-${idx}`"
                        class="flex flex-col"
                        :class="msg.role === 'user' ? 'items-end' : 'items-start'"
                      >
                        <template v-if="String(msg.content || '').trim().length > 0 || (msg.contextValues && msg.contextValues.length > 0)">
                          <div class="mb-1 px-2 text-[10px] font-semibold text-[var(--clm-text-muted)]">{{ msg.role === 'user' ? 'You' : 'Graph QA' }}</div>
                          <div
                            class="max-w-[96%] rounded-3xl px-3 py-2 text-sm shadow-sm"
                            :class="msg.role === 'user' ? 'rounded-br-lg bg-gradient-to-r from-blue-600 to-blue-700 text-white' : 'rounded-bl-lg border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] text-[var(--clm-text)] shadow-lg shadow-black/5'"
                          >
                            <div v-if="String(msg.content || '').trim().length > 0">
                              <div v-if="msg.role === 'assistant' && msg.markdown" class="chat-md text-left" v-html="renderMd(msg.content)" />
                              <div v-else>{{ msg.content }}</div>
                            </div>
                            <div v-if="msg.role === 'assistant' && msg.contextValues?.length" class="mt-2 flex flex-wrap gap-1.5">
                              <button
                                v-for="(ctxVal, cIdx) in msg.contextValues"
                                :key="`ctx-${idx}-${cIdx}`"
                                type="button"
                                class="rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-[10px] font-semibold text-blue-700 transition hover:bg-blue-100 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-200 dark:hover:bg-blue-900/45"
                                @click="selectGraphNodeFromValue(ctxVal)"
                              >
                                {{ ctxVal }}
                              </button>
                            </div>
                          </div>
                        </template>
                      </div>
                      <div v-if="isTyping" class="flex flex-col items-start">
                        <div class="mb-1 px-2 text-[10px] font-semibold text-[var(--clm-text-muted)]">Graph QA is thinking...</div>
                        <div class="rounded-3xl rounded-bl-lg border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] px-3 py-2 shadow-sm">
                          <div class="flex gap-1">
                            <div class="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--clm-text-muted)]" style="animation-delay: 0s"></div>
                            <div class="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--clm-text-muted)]" style="animation-delay: 0.2s"></div>
                            <div class="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--clm-text-muted)]" style="animation-delay: 0.4s"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="sticky bottom-0 border-t border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-4 py-3 backdrop-blur">
                      <form @submit.prevent="sendGraphMessage" class="flex gap-2">
                        <input
                          v-model="graphUserInput"
                          type="text"
                          placeholder="Ask Graph QA..."
                          class="clm-agent-input flex-1 rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-3 py-2 text-sm text-[var(--clm-text)] placeholder:text-[var(--clm-text-muted)]"
                        >
                        <button
                          type="submit"
                          :disabled="!graphUserInput.trim() || isTyping"
                          class="grid h-10 w-10 place-items-center rounded-full bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
                        </button>
                      </form>
                    </div>
                  </aside>
                  <aside
                    v-else-if="!showChat"
                    class="flex h-full w-10 shrink-0 flex-col items-center border-t border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] py-3 lg:w-12 lg:border-l lg:border-t-0"
                  >
                    <button
                      type="button"
                      class="inline-flex rotate-[-90deg] whitespace-nowrap rounded-full border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] px-3 py-1.5 text-[11px] font-black tracking-wide text-[var(--clm-text-muted)] shadow-sm transition hover:border-[var(--clm-brand)] hover:text-[var(--clm-brand)]"
                      @click="openPreviousChatbotForGraph"
                    >
                      AI CHAT
                    </button>
                  </aside>
                  </div>
                  </div>
                </div>

                <!-- Compliance Tab -->
                <div v-if="activeTab === 'compliance'" class="space-y-4">

                  <!-- ── Guideline compliance (LLM checks) ─────────────────── -->
                  <div class="overflow-hidden rounded-3xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-[0_1px_0_rgba(255,255,255,0.06)_inset,0_24px_48px_-24px_rgba(15,23,42,0.12)] ring-1 ring-black/[0.04] dark:shadow-[0_24px_48px_-24px_rgba(0,0,0,0.45)] dark:ring-white/[0.06]">
                    <WorkingVersionPicker
                      v-if="sortedDocumentVersions.length"
                      :versions="sortedDocumentVersions"
                      :selected-id="selectedVersionId"
                      embedded
                      @select="(v) => viewVersion(v)"
                    />

                    <!-- Hero + summary -->
                    <div class="relative border-b border-[var(--clm-border)] bg-gradient-to-br from-violet-500/[0.07] via-[var(--clm-bg-overlay)]/80 to-cyan-500/[0.06] px-4 py-5 sm:px-6 sm:py-6">
                      <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_100%_0%,rgba(139,92,246,0.12),transparent_55%),radial-gradient(ellipse_70%_50%_at_0%_100%,rgba(6,182,212,0.08),transparent_50%)] dark:from-transparent" />
                      <div class="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                        <div class="min-w-0 space-y-1.5">
                          <p class="text-[10px] font-black uppercase tracking-[0.22em] text-violet-600/90 dark:text-violet-300/90">
                            Compliance intelligence
                          </p>
                          <h3 class="text-lg font-black tracking-tight text-[var(--clm-text)] sm:text-xl">
                            Guideline checks
                          </h3>
                          <p class="max-w-xl text-[13px] leading-relaxed text-[var(--clm-text-muted)]">
                            Live validation against your playbook. Open the source in preview, filter by outcome, and drill into AI findings.
                          </p>
                        </div>
                        <div
                          v-if="complianceRecordsForVersion.length"
                          class="flex shrink-0 items-center gap-4 sm:gap-5"
                        >
                          <div
                            class="relative grid h-[4.5rem] w-[4.5rem] shrink-0 place-items-center rounded-full bg-[var(--clm-bg-surface-elevated)] shadow-inner ring-2 ring-[var(--clm-border)]/60"
                            :title="`${compliancePassRatePercent}% of checks passed`"
                          >
                            <svg class="absolute inset-0 h-full w-full -rotate-90" viewBox="0 0 36 36" aria-hidden="true">
                              <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" stroke-width="2.5" class="text-[var(--clm-border)]/80" />
                              <circle
                                cx="18" cy="18" r="15.5"
                                fill="none"
                                stroke="url(#clmComplianceRingGrad)"
                                stroke-width="2.5"
                                stroke-linecap="round"
                                :stroke-dasharray="`${(compliancePassRatePercent / 100) * 97.4} 97.4`"
                                class="transition-[stroke-dasharray] duration-500"
                              />
                              <defs>
                                <linearGradient id="clmComplianceRingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                  <stop offset="0%" stop-color="#8b5cf6" />
                                  <stop offset="100%" stop-color="#06b6d4" />
                                </linearGradient>
                              </defs>
                            </svg>
                            <div class="relative text-center">
                              <span class="block text-lg font-black tabular-nums leading-none text-[var(--clm-text)]">{{ compliancePassRatePercent }}%</span>
                              <span class="mt-0.5 block text-[8px] font-bold uppercase tracking-wider text-[var(--clm-text-muted)]">pass rate</span>
                            </div>
                          </div>
                          <div class="min-w-0 space-y-1 text-[11px] text-[var(--clm-text-muted)]">
                            <p>
                              <span class="font-bold text-[var(--clm-text)]">{{ filteredComplianceRecords.length }}</span>
                              <span v-if="complianceRecordsFilter.trim() || complianceOutcomeFilter !== 'all'"> shown</span>
                              <span v-else> checks</span>
                              <span class="text-[var(--clm-text-muted)]"> · v{{ workingVersion?.version_number ?? '—' }}</span>
                            </p>
                            <p v-if="complianceRecordsFilter.trim() || complianceOutcomeFilter !== 'all'" class="text-[10px]">
                              of {{ complianceRecordsForVersion.length }} for this version
                            </p>
                          </div>
                        </div>
                      </div>

                      <!-- Outcome counts -->
                      <div
                        v-if="complianceRecordsForVersion.length"
                        class="relative mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4"
                      >
                        <button
                          type="button"
                          class="group flex flex-col rounded-2xl border px-3 py-2.5 text-left transition focus:outline-none focus:ring-2 focus:ring-violet-500/40"
                          :class="complianceOutcomeFilter === 'all'
                            ? 'border-violet-500/50 bg-[var(--clm-bg-surface-elevated)] shadow-sm ring-1 ring-violet-500/20'
                            : 'border-[var(--clm-border)]/80 bg-[var(--clm-bg-surface)]/60 hover:border-[var(--clm-brand)]/30 hover:bg-[var(--clm-bg-surface-elevated)]'"
                          @click="setComplianceOutcomeFilter('all')"
                        >
                          <span class="text-[9px] font-bold uppercase tracking-wider text-[var(--clm-text-muted)]">Total</span>
                          <span class="text-xl font-black tabular-nums text-[var(--clm-text)]">{{ complianceOutcomeCounts.total }}</span>
                        </button>
                        <button
                          type="button"
                          class="group flex flex-col rounded-2xl border px-3 py-2.5 text-left transition focus:outline-none focus:ring-2 focus:ring-emerald-500/35"
                          :class="complianceOutcomeFilter === 'passed'
                            ? 'border-emerald-500/45 bg-emerald-500/[0.07] shadow-sm ring-1 ring-emerald-500/25'
                            : 'border-[var(--clm-border)]/80 bg-[var(--clm-bg-surface)]/60 hover:border-emerald-500/35'"
                          @click="setComplianceOutcomeFilter('passed')"
                        >
                          <span class="text-[9px] font-bold uppercase tracking-wider text-emerald-700/80 dark:text-emerald-400/90">Passed</span>
                          <span class="text-xl font-black tabular-nums text-emerald-700 dark:text-emerald-400">{{ complianceOutcomeCounts.passed }}</span>
                        </button>
                        <button
                          type="button"
                          class="group flex flex-col rounded-2xl border px-3 py-2.5 text-left transition focus:outline-none focus:ring-2 focus:ring-amber-500/35"
                          :class="complianceOutcomeFilter === 'warning'
                            ? 'border-amber-500/45 bg-amber-500/[0.08] shadow-sm ring-1 ring-amber-500/25'
                            : 'border-[var(--clm-border)]/80 bg-[var(--clm-bg-surface)]/60 hover:border-amber-500/40'"
                          @click="setComplianceOutcomeFilter('warning')"
                        >
                          <span class="text-[9px] font-bold uppercase tracking-wider text-amber-700/85 dark:text-amber-400/90">Warning</span>
                          <span class="text-xl font-black tabular-nums text-amber-700 dark:text-amber-400">{{ complianceOutcomeCounts.warning }}</span>
                        </button>
                        <button
                          type="button"
                          class="group flex flex-col rounded-2xl border px-3 py-2.5 text-left transition focus:outline-none focus:ring-2 focus:ring-red-500/35"
                          :class="complianceOutcomeFilter === 'failed'
                            ? 'border-red-500/45 bg-red-500/[0.07] shadow-sm ring-1 ring-red-500/25'
                            : 'border-[var(--clm-border)]/80 bg-[var(--clm-bg-surface)]/60 hover:border-red-500/35'"
                          @click="setComplianceOutcomeFilter('failed')"
                        >
                          <span class="text-[9px] font-bold uppercase tracking-wider text-red-700/85 dark:text-red-400/90">Failed</span>
                          <span class="text-xl font-black tabular-nums text-red-700 dark:text-red-400">{{ complianceOutcomeCounts.failed }}</span>
                        </button>
                      </div>
                    </div>

                    <!-- Toolbar -->
                    <div
                      v-if="complianceRecordsForVersion.length"
                      class="flex flex-col gap-3 border-b border-[var(--clm-border)] bg-[var(--clm-bg-surface)]/90 px-4 py-3 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between sm:px-5"
                    >
                      <div class="relative min-w-0 flex-1 sm:max-w-md">
                        <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--clm-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                          v-model="complianceRecordsFilter"
                          type="search"
                          autocomplete="off"
                          placeholder="Search checks, findings, page…"
                          class="w-full rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] py-2.5 pl-10 pr-3 text-xs text-[var(--clm-text)] shadow-sm placeholder:text-[var(--clm-text-muted)] focus:border-[var(--clm-brand)] focus:outline-none focus:ring-2 focus:ring-[var(--clm-brand)]/20"
                        >
                      </div>
                      <div class="flex flex-wrap items-center gap-2">
                        <label class="sr-only" for="compliance-sort">Sort list</label>
                        <select
                          id="compliance-sort"
                          v-model="complianceListSort"
                          class="rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] px-2.5 py-2 text-[11px] font-bold text-[var(--clm-text)] shadow-sm focus:border-[var(--clm-brand)] focus:outline-none focus:ring-2 focus:ring-[var(--clm-brand)]/20"
                        >
                          <option value="priority">Sort: issues first</option>
                          <option value="name">Sort: A–Z</option>
                          <option value="page">Sort: page order</option>
                        </select>
                        <button
                          type="button"
                          class="rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] px-2.5 py-2 text-[11px] font-bold text-[var(--clm-text)] shadow-sm transition hover:border-[var(--clm-brand)]/40"
                          @click="complianceExpandAllFindings"
                        >
                          Expand all
                        </button>
                        <button
                          type="button"
                          class="rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] px-2.5 py-2 text-[11px] font-bold text-[var(--clm-text)] shadow-sm transition hover:border-[var(--clm-brand)]/40"
                          @click="complianceCollapseAllFindings"
                        >
                          Collapse
                        </button>
                        <button
                          type="button"
                          class="inline-flex shrink-0 items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 px-3.5 py-2.5 text-xs font-bold text-white shadow-md transition hover:from-violet-500 hover:to-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
                          :disabled="!workingVersion?.file_id || complianceRerunLoading"
                          :title="workingVersion?.file_id ? `Re-run LLM checks using v${workingVersion.version_number} (file #${workingVersion.file_id})` : 'Select a version with a document'"
                          @click="rerunComplianceChecks"
                        >
                          <span
                            v-if="complianceRerunLoading"
                            class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"
                          />
                          <svg
                            v-else
                            class="h-3.5 w-3.5 shrink-0 opacity-90"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            aria-hidden="true"
                          >
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span class="tabular-nums">Re-run compliance</span>
                        </button>
                      </div>
                    </div>

                    <!-- Check cards -->
                    <div v-if="complianceRecordsForVersion.length" class="space-y-2.5 p-3 sm:p-4">
                      <div
                        v-for="rec in complianceDisplayRecords"
                        :key="rec.id"
                        class="min-w-0 overflow-hidden rounded-2xl border border-[var(--clm-border)]/90 bg-[var(--clm-bg-surface-elevated)]/90 shadow-sm transition hover:border-[var(--clm-brand)]/25 hover:shadow-md"
                      >
                        <div
                          class="group flex min-w-0 items-stretch gap-0"
                        >
                          <div
                            class="w-1 shrink-0 self-stretch"
                            :class="{
                              'bg-emerald-500': complianceRecordOutcomeKey(rec) === 'passed',
                              'bg-amber-400': complianceRecordOutcomeKey(rec) === 'warning',
                              'bg-red-500': complianceRecordOutcomeKey(rec) === 'failed',
                              'bg-slate-400 dark:bg-slate-500': !['passed','warning','failed'].includes(complianceRecordOutcomeKey(rec)),
                            }"
                            aria-hidden="true"
                          />
                          <div class="flex min-w-0 flex-1 flex-col gap-2 px-3 py-3 sm:flex-row sm:items-center sm:gap-3 sm:px-4 sm:py-3.5">
                            <div class="min-w-0 flex-1 space-y-1">
                              <div class="flex flex-wrap items-center gap-2">
                                <p class="text-left text-[13px] font-bold leading-snug text-[var(--clm-text)] sm:text-sm">
                                  {{ rec.check_name }}
                                </p>
                                <span
                                  v-if="rec.page_number != null"
                                  class="inline-flex items-center rounded-md bg-[var(--clm-bg-overlay)] px-1.5 py-px text-[10px] font-semibold tabular-nums text-[var(--clm-text-muted)] ring-1 ring-[var(--clm-border)]/60"
                                >
                                  p.{{ rec.page_number }}
                                </span>
                              </div>
                              <p
                                v-if="rec.findings && !rec.isOpen"
                                class="line-clamp-2 text-[11px] leading-relaxed text-[var(--clm-text-muted)]"
                              >
                                {{ rec.findings }}
                              </p>
                            </div>
                            <div class="flex shrink-0 flex-wrap items-center justify-end gap-1 sm:gap-1.5">
                              <span
                                class="inline-flex items-center rounded-lg px-2 py-1 text-[10px] font-black uppercase tracking-wide ring-1 ring-inset"
                                :class="{
                                  'bg-emerald-500/10 text-emerald-800 ring-emerald-500/25 dark:text-emerald-300': complianceRecordOutcomeKey(rec) === 'passed',
                                  'bg-amber-500/12 text-amber-900 ring-amber-500/30 dark:text-amber-200': complianceRecordOutcomeKey(rec) === 'warning',
                                  'bg-red-500/10 text-red-800 ring-red-500/25 dark:text-red-300': complianceRecordOutcomeKey(rec) === 'failed',
                                  'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)] ring-[var(--clm-border)]': !['passed','warning','failed'].includes(complianceRecordOutcomeKey(rec)),
                                }"
                              >{{ (rec.status || '—').toString() }}</span>
                              <button
                                v-if="primaryVersionId && workingVersion?.file_id"
                                type="button"
                                class="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-[var(--clm-text-muted)] ring-1 ring-transparent transition hover:bg-[var(--clm-bg-overlay)] hover:text-[var(--clm-brand)] hover:ring-[var(--clm-border)]"
                                title="Open document preview and highlight source"
                                @click.stop="openComplianceChunkInPreview(rec)"
                              >
                                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                                </svg>
                              </button>
                              <button
                                v-if="rec.findings"
                                type="button"
                                :aria-expanded="rec.isOpen"
                                class="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-[var(--clm-text-muted)] ring-1 ring-transparent transition hover:bg-[var(--clm-bg-overlay)] hover:text-[var(--clm-text)] hover:ring-[var(--clm-border)]"
                                @click="rec.isOpen = !rec.isOpen"
                              >
                                <svg class="h-4 w-4 transition-transform duration-200" :class="{ 'rotate-180': rec.isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                              </button>
                            </div>
                          </div>
                        </div>
                        <div
                          v-if="rec.isOpen && rec.findings"
                          class="border-t border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/50 px-3 pb-4 pt-3 sm:px-5"
                        >
                          <p class="mb-2 text-[9px] font-black uppercase tracking-[0.2em] text-[var(--clm-text-muted)]">Findings</p>
                          <div
                            class="rounded-2xl border px-4 py-3 text-sm leading-relaxed text-[var(--clm-text)] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
                            :class="complianceRecordVisuals(rec.status).panel"
                          >
                            {{ rec.findings }}
                          </div>
                        </div>
                      </div>

                      <div
                        v-if="filteredComplianceRecords.length === 0"
                        class="rounded-2xl border border-dashed border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/40 px-4 py-10 text-center"
                      >
                        <p class="text-sm font-medium text-[var(--clm-text)]">No checks match your filters</p>
                        <p class="mt-1 text-xs text-[var(--clm-text-muted)]">Try another outcome, search term, or clear filters.</p>
                        <div class="mt-4 flex flex-wrap justify-center gap-2">
                          <button
                            type="button"
                            class="rounded-xl bg-[var(--clm-brand)] px-3 py-1.5 text-xs font-bold text-white shadow-sm"
                            @click="complianceRecordsFilter = ''; setComplianceOutcomeFilter('all')"
                          >
                            Clear filters
                          </button>
                        </div>
                      </div>
                    </div>

                    <div
                      v-else
                      class="mx-4 mb-6 mt-2 rounded-2xl border border-dashed border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/30 px-6 py-12 text-center"
                    >
                      <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-600 dark:text-violet-300">
                        <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                      </div>
                      <p class="text-sm font-semibold text-[var(--clm-text)]">No compliance checks for this version yet</p>
                      <p class="mt-1 text-xs text-[var(--clm-text-muted)]">
                        Run analysis from the workflow or chat, or switch document version above.
                      </p>
                    </div>
                  </div>

                  <!-- ── Automated Scoring Findings ────────────────────────── -->
                  <div class="overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm">
                    <!-- header bar -->
                    <div class="flex items-center justify-between border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-2.5">
                      <h3 class="text-[11px] font-bold uppercase tracking-widest text-[var(--clm-text)]">Scoring Findings</h3>
                      <button
                        type="button"
                        class="rounded-lg border border-[var(--clm-border)] px-2.5 py-1 text-[10px] font-bold text-[var(--clm-text-muted)] transition hover:bg-[var(--clm-bg-overlay)] hover:text-[var(--clm-text)]"
                        @click="selectTab('scoring')"
                      >Full scoring ↗</button>
                    </div>

                    <!-- loading / error states -->
                    <div v-if="scoringLoading || scoringBackgroundRunning" class="flex items-center justify-center gap-2 py-6">
                      <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--clm-brand)] border-t-transparent"></div>
                      <span class="text-[11px] text-[var(--clm-text-muted)]">Loading…</span>
                    </div>
                    <div v-else-if="scoringError" class="flex items-center justify-between px-4 py-3 text-[11px]">
                      <span class="text-amber-600 dark:text-amber-400">{{ scoringError }}</span>
                      <button type="button" class="rounded bg-[var(--clm-brand)] px-2.5 py-1 text-[10px] font-bold text-white" @click="fetchScoring">Retry</button>
                    </div>

                    <div v-else-if="scoringData">
                      <!-- financial summary one-liner -->
                      <div
                        v-if="scoringData.finance_analysis"
                        class="border-b border-[var(--clm-border)] px-4 py-2"
                      >
                        <button
                          type="button"
                          class="flex w-full items-center gap-3 text-left"
                          @click="scoringData.finance_analysis._expanded = !scoringData.finance_analysis._expanded"
                        >
                          <span class="text-[10px] font-bold uppercase text-[var(--clm-text-muted)]">Financial</span>
                          <span class="text-base font-black text-[var(--clm-text)]">{{ scoringData.finance_analysis.overall_compliance_score }}%</span>
                          <span
                            class="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase"
                            :class="(scoringData.finance_analysis.approval_recommendation || '').toLowerCase() === 'approve' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'"
                          >{{ scoringData.finance_analysis.approval_recommendation || '—' }}</span>
                          <span v-if="scoringData.finance_analysis.executive_summary" class="hidden flex-1 text-[10px] text-[var(--clm-text-muted)] sm:block" :class="scoringData.finance_analysis._expanded ? 'whitespace-pre-wrap' : 'truncate'">{{ scoringData.finance_analysis.executive_summary }}</span>
                          <svg class="h-3.5 w-3.5 shrink-0 text-[var(--clm-text-muted)] transition-transform" :class="{ 'rotate-180': scoringData.finance_analysis._expanded }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                        </button>
                      </div>

                      <!-- validation result rows -->
                      <div v-if="scoringData.validation_results?.length">
                        <div
                          v-for="(vr, idx) in scoringData.validation_results"
                          :key="`comp-vr-${idx}`"
                          class="border-b border-[var(--clm-border)] last:border-0"
                        >
                          <!-- row header (always visible) -->
                          <button
                            type="button"
                            class="flex w-full items-center gap-2 px-4 py-2 text-left transition hover:bg-[var(--clm-bg-overlay)]"
                            @click="toggleScoringAccordion(`comp-vr-${idx}`)"
                          >
                            <div
                              class="h-2 w-2 shrink-0 rounded-full"
                              :class="(vr.compliance_status || '').toLowerCase() === 'pass' ? 'bg-green-500' : (vr.compliance_status || '').toLowerCase() === 'fail' ? 'bg-red-400' : 'bg-amber-400'"
                            ></div>
                            <span class="flex-1 truncate text-[12px] font-semibold capitalize text-[var(--clm-text)]">
                              {{ (vr.agent_type || '').replace(/_/g, ' ') || 'Validation' }}
                            </span>
                            <span class="shrink-0 text-[11px] font-black tabular-nums" :class="scoreColor(vr.overall_score)">
                              {{ typeof vr.overall_score === 'number' ? vr.overall_score.toFixed(1) : vr.overall_score }}%
                            </span>
                            <span
                              class="shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase"
                              :class="statusBadgeClass(vr.compliance_status)"
                            >{{ vr.compliance_status || '—' }}</span>
                            <svg class="h-3.5 w-3.5 shrink-0 text-[var(--clm-text-muted)] transition-transform" :class="{ 'rotate-180': openScoringAccordions[`comp-vr-${idx}`] }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                          </button>

                          <!-- expanded: finding category rows -->
                          <div v-show="openScoringAccordions[`comp-vr-${idx}`]" class="border-t border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]">
                            <div v-if="vr.findings?.length">
                              <div
                                v-for="(group, gi) in mergedFindingsByCategory(vr.findings)"
                                :key="`comp-g-${idx}-${gi}`"
                                class="border-b border-[var(--clm-border)] last:border-0"
                              >
                                <!-- category row -->
                                <button
                                  type="button"
                                  class="flex w-full items-center gap-2 pl-8 pr-4 py-1.5 text-left transition hover:bg-[var(--clm-bg-surface-elevated)]"
                                  @click="toggleScoringAccordion(`comp-vr-${idx}-g-${gi}`)"
                                >
                                  <span class="flex-1 truncate text-[11px] font-medium text-[var(--clm-text)]">{{ group.category }}</span>
                                  <span v-if="group.items.length > 1" class="shrink-0 text-[9px] text-[var(--clm-text-muted)]">({{ group.items.length }})</span>
                                  <span
                                    class="shrink-0 rounded px-1 py-0.5 text-[8px] font-bold uppercase"
                                    :class="(group.worstStatus || '').toUpperCase() === 'NON_COMPLIANT' || (group.worstStatus || '').toUpperCase() === 'CRITICAL' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' : (group.worstStatus || '').toUpperCase() === 'PARTIAL' || (group.worstStatus || '').toUpperCase().includes('HIGH') ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' : 'bg-gray-200 text-gray-600 dark:bg-gray-600 dark:text-gray-300'"
                                  >{{ group.worstStatus }}</span>
                                  <svg class="h-3 w-3 shrink-0 text-[var(--clm-text-muted)] transition-transform" :class="{ 'rotate-180': openScoringAccordions[`comp-vr-${idx}-g-${gi}`] }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                                </button>
                                <!-- finding items -->
                                <div v-show="openScoringAccordions[`comp-vr-${idx}-g-${gi}`]" class="border-t border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] pl-10 pr-4 py-2 space-y-1">
                                  <div
                                    v-for="(item, ii) in group.items"
                                    :key="ii"
                                    class="text-[11px] leading-relaxed text-[var(--clm-text-muted)]"
                                  >
                                    <span v-if="group.items.length > 1" class="mr-1 font-semibold text-[var(--clm-text-muted)]">{{ ii + 1 }}.</span>
                                    {{ item.issue || item.finding }}
                                  </div>
                                </div>
                              </div>
                            </div>
                            <p v-else class="pl-8 pr-4 py-2 text-[11px] italic text-[var(--clm-text-muted)]">No findings.</p>
                          </div>
                        </div>
                      </div>
                      <p v-else class="px-4 py-4 text-center text-[11px] text-[var(--clm-text-muted)]">No validation results in scoring data.</p>
                    </div>
                    <p v-else class="px-4 py-5 text-center text-[11px] text-[var(--clm-text-muted)]">
                      No scoring data yet — run scoring first or use Retry above.
                    </p>
                  </div>

                </div>

                <!-- History Tab -->
                <div v-if="activeTab === 'history'" class="overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm">
                  <!-- header bar -->
                  <div class="flex items-center justify-between border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-2.5">
                    <div class="flex items-center gap-2.5">
                      <h3 class="text-[11px] font-bold uppercase tracking-widest text-[var(--clm-text)]">Version History</h3>
                      <span class="rounded-full bg-[var(--clm-brand)]/10 px-2 py-0.5 text-[10px] font-bold text-[var(--clm-brand)]">
                        {{ contract?.document_versions?.length || 0 }} versions
                      </span>
                    </div>
                    <div class="flex items-center gap-1.5">
                      <button @click="showVersionDrivePicker = true" class="inline-flex items-center gap-1 rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-2.5 py-1 text-[10px] font-bold text-[var(--clm-text)] transition hover:border-[var(--clm-brand)] hover:bg-[var(--clm-brand)]/5">
                        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                        From Drive
                      </button>
                      <!-- Upload button / progress bar -->
                      <template v-if="!versionUploading">
                        <label class="inline-flex cursor-pointer items-center gap-1 rounded-lg bg-[var(--clm-brand)] px-2.5 py-1 text-[10px] font-bold text-white transition hover:bg-[var(--clm-brand-strong)]">
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                          Upload
                          <input type="file" class="hidden" @change="uploadVersion" accept=".pdf,.docx">
                        </label>
                      </template>
                      <template v-else>
                        <div class="flex items-center gap-2 rounded-lg border border-[var(--clm-brand)]/30 bg-[var(--clm-brand)]/5 px-2.5 py-1">
                          <svg class="h-3 w-3 animate-spin text-[var(--clm-brand)]" viewBox="0 0 24 24" fill="none">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                          </svg>
                          <div class="w-20 overflow-hidden rounded-full bg-[var(--clm-brand)]/20 h-1.5">
                            <div class="h-full rounded-full bg-[var(--clm-brand)] transition-all duration-200" :style="{ width: versionUploadProgress + '%' }"></div>
                          </div>
                          <span class="text-[10px] font-bold tabular-nums text-[var(--clm-brand)]">{{ versionUploadProgress }}%</span>
                        </div>
                      </template>
                    </div>
                  </div>

                  <!-- timeline -->
                  <div class="relative">
                    <!-- vertical connector rail -->
                    <div class="absolute left-[1.85rem] top-0 h-full w-px bg-[var(--clm-border)]"></div>

                    <!-- HEAD row -->
                    <div class="relative flex items-center gap-3 px-4 py-2.5 border-b border-[var(--clm-border)]">
                      <div class="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--clm-brand)] text-white shadow-sm ring-2 ring-[var(--clm-bg-surface)]">
                        <svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                      </div>
                      <span class="flex-1 text-[12px] font-semibold text-[var(--clm-text)]">Current Version</span>
                      <span class="text-[10px] tabular-nums text-[var(--clm-text-muted)]">{{ formatDate(contract?.updated_at) }}</span>
                      <span class="rounded bg-[var(--clm-brand)]/15 px-1.5 py-0.5 font-mono text-[9px] font-bold text-[var(--clm-brand)]">HEAD</span>
                    </div>

                    <!-- version rows -->
                    <div
                      v-for="(version, vi) in contract?.document_versions"
                      :key="version.id"
                    >
                      <!-- main row -->
                      <div
                        class="group relative flex items-center gap-3 px-4 py-2 transition hover:bg-[var(--clm-bg-overlay)]"
                        :class="vi < (contract?.document_versions?.length || 0) - 1 || version.isOpen ? 'border-b border-[var(--clm-border)]' : ''"
                      >
                        <!-- version badge dot -->
                        <div
                          class="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[9px] font-bold ring-2 ring-[var(--clm-bg-surface)]"
                          :class="version.is_latest ? 'bg-[var(--clm-brand)] text-white' : 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)] border border-[var(--clm-border)]'"
                        >v{{ version.version_number }}</div>

                        <!-- label + notes inline -->
                        <div class="min-w-0 flex-1">
                          <span class="text-[12px] font-semibold text-[var(--clm-text)]">{{ version.label || `Version v${version.version_number}` }}</span>
                          <span v-if="version.notes" class="ml-1.5 hidden truncate text-[10px] text-[var(--clm-text-muted)] group-hover:inline">· {{ version.notes }}</span>
                        </div>

                        <!-- badges -->
                        <span v-if="version.is_latest" class="shrink-0 rounded bg-blue-600 px-1.5 py-0.5 text-[8px] font-bold text-white">LATEST</span>
                        <span v-if="version.signed_file_path" class="shrink-0 rounded bg-green-600 px-1.5 py-0.5 text-[8px] font-bold text-white">SIGNED</span>

                        <!-- per-version background processing indicator -->
                        <span
                          v-if="processingVersions[version.file_id]"
                          class="inline-flex shrink-0 items-center gap-1 rounded-full border border-[var(--clm-brand)]/30 bg-[var(--clm-brand)]/8 px-1.5 py-0.5"
                        >
                          <svg class="h-2.5 w-2.5 animate-spin text-[var(--clm-brand)]" viewBox="0 0 24 24" fill="none">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                          </svg>
                          <span class="text-[8px] font-bold text-[var(--clm-brand)]">
                            {{ processingVersions[version.file_id].stage === 'chunking' ? 'Chunking…' : 'Processing…' }}
                          </span>
                        </span>

                        <!-- date -->
                        <time class="shrink-0 text-[10px] tabular-nums text-[var(--clm-text-muted)]">{{ formatDate(version.created_at) }}</time>

                        <!-- action links (always visible) -->
                        <div class="flex shrink-0 items-center gap-2">
                          <button @click="viewVersion(version)" class="text-[10px] font-bold text-[var(--clm-brand)] hover:underline">View</button>
                          <button
                            v-if="['docx','doc'].includes((version.file_type || '').toLowerCase())"
                            type="button"
                            @click="openVersionEditor(version)"
                            class="text-[10px] font-bold text-amber-600 hover:underline"
                          >Edit</button>
                          <button v-if="version.signed_file_path" @click="downloadVersionSigned(version.id)" class="text-[10px] font-bold text-green-600 hover:underline">Signed↓</button>
                          <button
                            v-if="(contract?.document_versions?.length || 0) > 1"
                            type="button"
                            @click="removeDocumentVersion(version)"
                            class="text-[10px] font-bold text-red-500 hover:underline"
                          >Remove</button>
                        </div>

                        <!-- expand signers -->
                        <button
                          @click="version.isOpen = !version.isOpen"
                          class="shrink-0 rounded p-0.5 text-[var(--clm-text-muted)] transition hover:text-[var(--clm-text)]"
                          :title="version.isOpen ? 'Hide signers' : 'Show signers'"
                        >
                          <svg class="h-3.5 w-3.5 transition-transform" :class="{ 'rotate-180': version.isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                        </button>
                      </div>

                      <!-- expanded: signer sub-rows -->
                      <div
                        v-if="version.isOpen"
                        class="border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]"
                      >
                        <div v-if="version.version_signers?.length">
                          <div
                            v-for="vs in version.version_signers"
                            :key="vs.id"
                            class="flex items-center gap-2 border-b border-[var(--clm-border)] py-1.5 pl-14 pr-4 last:border-0"
                          >
                            <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="vs.status === 'signed' ? 'bg-green-500' : vs.status === 'declined' ? 'bg-red-400' : 'bg-amber-400'"></span>
                            <span class="flex-1 text-[11px] font-medium text-[var(--clm-text)]">{{ vs.master_signer?.name }}</span>
                            <span class="text-[10px] text-[var(--clm-text-muted)]">{{ vs.master_signer?.organization }}</span>
                            <span class="text-[10px] font-bold" :class="vs.status === 'signed' ? 'text-green-600' : 'text-[var(--clm-text-muted)]'">
                              {{ vs.status === 'signed' ? '✓ Signed' : vs.status }}
                            </span>
                          </div>
                        </div>
                        <p v-else class="py-2 pl-14 pr-4 text-[10px] italic text-[var(--clm-text-muted)]">No signers for this version</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
      </div>

      <!-- Agent chat → body: position:fixed inside <main overflow-y-auto> was clipped to a thin strip on the right. -->
      <Teleport to="body">
        <div
          v-if="showChat"
          class="clm-agent-chat-shell box-border fixed flex min-h-0 flex-col overflow-hidden"
          :class="
            agentChatFullscreen
              ? 'clm-agent-chat-shell--fs inset-0 z-[240] max-w-none bg-[var(--clm-bg-surface)] pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)] dark:bg-[var(--clm-bg-page)]'
              : dockedAgentChatShellClass
          "
          :style="dockChatShellStyle"
        >
        <div
          v-if="!agentChatFullscreen && isLgChatDock"
          @mousedown="startResizing"
          class="absolute left-0 top-0 bottom-0 w-2 cursor-ew-resize z-20"
          title="Resize chat panel"
        ></div>

        <div class="border-b border-gray-100/80 bg-[linear-gradient(135deg,#0f4c81,#0a3760)] px-3 py-3 text-white sm:px-4 sm:py-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div class="min-w-0 flex-1">
              <p class="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.12em] text-white/90">
                <span class="h-2 w-2 rounded-full bg-emerald-300 shadow-sm shadow-emerald-300/70 animate-pulse"></span>
                Intelligent Contract Copilot
              </p>
              <h3 class="mt-1 text-lg font-black">AI Agents</h3>
              <p class="text-[11px] text-white/90">
                {{ agentChatFullscreen ? 'Full screen — Esc or the button below restores the sidebar layout.' : 'Keep work moving without leaving this contract view.' }}
              </p>
            </div>
            <div class="flex shrink-0 items-center justify-end gap-1.5 sm:gap-2">
              <button
                type="button"
                @click="agentChatFullscreen = !agentChatFullscreen"
                class="grid h-8 w-8 place-items-center rounded-full border border-white/20 bg-white/10 transition hover:bg-white/20"
                :title="agentChatFullscreen ? 'Exit full screen' : 'Full screen chat'"
              >
                <svg v-if="!agentChatFullscreen" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
                </svg>
                <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25"/>
                </svg>
              </button>
              <button type="button" @click="showAgentConfig = !showAgentConfig" class="grid h-8 w-8 place-items-center rounded-full border border-white/20 bg-white/10 transition hover:bg-white/20" title="Configure Agents">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
              </button>
              <button type="button" @click="showChat = false; agentChatFullscreen = false" class="grid h-8 w-8 place-items-center rounded-full border border-white/20 bg-white/10 transition hover:bg-white/20" title="Close assistant">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Full-screen: readable column width; docked: display:contents (no extra box). -->
        <div
          class="min-h-0 min-w-0"
          :class="agentChatFullscreen ? 'flex flex-1 flex-col overflow-hidden' : 'contents'"
        >
          <div
            class="min-h-0 min-w-0"
            :class="
              agentChatFullscreen
                ? 'mx-auto flex w-full max-w-6xl flex-1 flex-col overflow-hidden px-4 sm:px-6 md:max-w-7xl 2xl:max-w-[min(100%,96rem)]'
                : 'contents'
            "
          >
        <div class="px-3 py-2 bg-gradient-to-b from-white/90 to-gray-50 dark:from-gray-800 dark:to-gray-900/30">
          <div class="flex gap-2 overflow-x-auto pb-1">
            <button
              v-for="agent in activeAgents"
              :key="agent.id"
              @click="selectedAgent = agent.id"
              class="inline-flex flex-none items-center gap-1 rounded-full px-3 py-1.5 text-[11px] font-bold transition shadow-sm"
              :class="selectedAgent === agent.id
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-500 hover:bg-blue-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="selectedAgent === agent.id ? 'bg-emerald-300' : 'bg-gray-300'"></span>
              {{ agent.name }}
            </button>
          </div>
        </div>

        <div v-if="showAgentConfig" class="border-y border-gray-100 bg-white px-4 py-4">
          <h4 class="text-xs font-black uppercase tracking-[0.1em] text-gray-500">Configure Agents</h4>
          <div class="space-y-2 mt-2">
            <div v-for="agent in availableAgents" :key="agent.id" class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 p-2 rounded-lg">
              <span class="text-xs font-medium dark:text-white">{{ agent.name }}</span>
              <button @click="toggleAgent(agent)" class="px-2 py-1 text-[10px] font-bold rounded" :class="isAgentActive(agent.id) ? 'bg-red-100 text-red-600 hover:bg-red-200' : 'bg-green-100 text-green-600 hover:bg-green-200'">{{ isAgentActive(agent.id) ? 'Remove' : 'Add' }}</button>
            </div>
            <div class="mt-3">
              <input v-model="newAgentName" type="text" placeholder="Custom Agent Name..." class="clm-agent-input w-full">
              <button @click="addNewAgent" class="mt-2 w-full py-2 bg-blue-600 text-white text-xs font-black tracking-wide rounded hover:bg-blue-700 transition">Add custom agent</button>
            </div>
          </div>
        </div>

        <!-- CPWD Copilot toggle (Review / Draft) -->
        <div
          v-if="(selectedAgent === 'review' || selectedAgent === 'draft') && !reviewContextFullSpace"
          class="shrink-0 border-b border-amber-200/50 bg-amber-50/30 px-2.5 py-2 dark:border-amber-900/30 dark:bg-amber-950/20"
        >
          <label class="flex cursor-pointer items-start gap-2">
            <input v-model="cpwdCopilotEnabled" type="checkbox" class="mt-0.5 rounded border-amber-400 text-amber-700 focus:ring-amber-500" />
            <span class="min-w-0 text-[10px] leading-snug text-amber-950/90 dark:text-amber-100/90">
              <span class="font-bold">CPWD Copilot</span>
              <span class="font-normal text-amber-900/75 dark:text-amber-200/80">
                — inject guidelines, compliance, and scoring (premium). Draft also includes saved review items.
              </span>
            </span>
          </label>
        </div>

        <!-- Review / Draft: compact scoring context row (hidden while full-space picker is open) -->
        <div
          v-if="(selectedAgent === 'review' || selectedAgent === 'draft') && !reviewContextFullSpace"
          class="shrink-0 border-b border-gray-200/80 bg-white/95 px-2.5 py-1.5 dark:border-gray-700 dark:bg-gray-900/95"
        >
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-slate-200/90 bg-slate-50/90 px-2 py-1.5 text-left transition hover:bg-slate-100 dark:border-gray-700 dark:bg-gray-800/80 dark:hover:bg-gray-800"
              @click="openReviewContextPanel"
            >
              <span class="text-[10px] font-black uppercase tracking-wide text-slate-700 dark:text-slate-200">Context</span>
              <span class="truncate text-[9px] text-slate-500 dark:text-slate-400">
                <template v-if="selectedReviewContextCount">
                  {{ selectedReviewFindingCount }}F · {{ selectedReviewRecommendationCount }}R selected
                </template>
                <template v-else>Tap to select scoring items</template>
              </span>
              <svg class="ml-auto h-3.5 w-3.5 shrink-0 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
              </svg>
            </button>
            <button
              v-if="selectedReviewContextCount"
              type="button"
              class="shrink-0 rounded-md px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-gray-800"
              @click="clearReviewScoringSelection"
            >
              Clear
            </button>
          </div>
        </div>

        <!-- Document comparison: compact-first workspace (full hide available) -->
        <div
          v-if="selectedAgent === 'compare' && compareTopPanelHidden"
          class="flex shrink-0 items-center justify-between gap-2 border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-3 py-2 dark:border-gray-700"
        >
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-lg border border-sky-300/80 bg-sky-50 px-3 py-1.5 text-[10px] font-black uppercase tracking-wide text-sky-800 shadow-sm transition hover:bg-sky-100 dark:border-sky-800/80 dark:bg-sky-950/50 dark:text-sky-200 dark:hover:bg-sky-950/70"
            @click="compareTopPanelHidden = false"
          >
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            Show compare controls
          </button>
          <p class="hidden min-w-0 flex-1 truncate text-center text-[10px] text-[var(--clm-text-muted)] sm:block">
            <template v-if="selectedCompareVersionA && selectedCompareVersionB">
              A vs B selected — chat uses full height
            </template>
            <template v-else>Pick versions when you expand</template>
          </p>
          <button
            type="button"
            class="inline-flex shrink-0 items-center gap-1 rounded-lg bg-sky-600 px-3 py-1.5 text-[10px] font-black uppercase tracking-wide text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!canRunCompareNow || compareTyping"
            @click="runCompareNow()"
          >
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            Run
          </button>
        </div>

        <div
          v-if="selectedAgent === 'compare' && !compareTopPanelHidden"
          class="shrink-0 border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-3 py-3 dark:border-gray-700"
          :class="comparePanelDense ? 'py-2' : 'sm:py-3.5'"
        >
          <div class="flex flex-col gap-3">
            <div class="flex items-center justify-between gap-3">
              <div class="min-w-0">
                <p class="text-[11px] font-black uppercase tracking-[0.14em] text-[var(--clm-text-muted)]">
                  Compare versions
                </p>
                <p class="mt-0.5 text-[10px] leading-relaxed text-slate-600 dark:text-slate-400">
                  Pick baseline and compare versions, then run a focused diff.
                </p>
              </div>
              <div class="flex flex-wrap items-center justify-end gap-2">
                <span
                  class="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide"
                  :class="compareTyping ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/35 dark:text-emerald-300'"
                >
                  {{ compareTyping ? 'Running' : 'Ready' }}
                </span>
                <button
                  type="button"
                  class="inline-flex items-center gap-1 rounded-lg border border-slate-200/90 bg-white px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wide text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  @click="compareSetupExpanded = !compareSetupExpanded"
                >
                  <svg class="h-3.5 w-3.5 opacity-75" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h18M3 12h18M3 17h18" />
                  </svg>
                  {{ compareSetupExpanded ? 'Less' : 'More' }}
                </button>
                <button
                  type="button"
                  class="inline-flex items-center gap-1 rounded-lg border border-slate-300/90 bg-slate-100 px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wide text-slate-700 transition hover:bg-slate-200 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  title="Hide entire compare panel for maximum chat space"
                  @click="compareTopPanelHidden = true"
                >
                  <svg class="h-3.5 w-3.5 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                  </svg>
                  Hide panel
                </button>
              </div>
            </div>
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)_auto]">
              <label class="block min-w-0 rounded-xl border border-sky-300/70 bg-sky-50/80 px-3 py-2.5 dark:border-sky-800/70 dark:bg-sky-950/35">
                <span class="inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wide text-sky-800 dark:text-sky-200">
                  <span class="rounded-md bg-sky-600 px-1.5 py-0.5 text-white">A</span>
                  Baseline
                </span>
                <select
                  v-model="compareVersionAId"
                  class="clm-agent-input mt-1.5 w-full rounded-lg border border-sky-200/90 bg-white py-2 pl-2.5 pr-8 text-[11px] text-slate-900 dark:border-sky-800/60 dark:bg-slate-950 dark:text-slate-100"
                >
                  <option value="" disabled>Choose version A…</option>
                  <option v-for="v in sortedDocumentVersions" :key="'cmp-a-modern-' + v.id" :value="String(v.id)">
                    {{ formatVersionCompareLabel(v) }}
                  </option>
                </select>
              </label>

              <button
                type="button"
                class="inline-flex items-center justify-center rounded-lg border border-slate-300/70 bg-white px-2 py-2 text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                :disabled="!compareVersionAId || !compareVersionBId"
                title="Swap A and B"
                @click="swapCompareVersions"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-3-3m3 3l-3 3M16 17H4m0 0l3-3m-3 3l3 3"/>
                </svg>
              </button>

              <label class="block min-w-0 rounded-xl border border-violet-300/70 bg-violet-50/80 px-3 py-2.5 dark:border-violet-800/70 dark:bg-violet-950/35">
                <span class="inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wide text-violet-800 dark:text-violet-200">
                  <span class="rounded-md bg-violet-600 px-1.5 py-0.5 text-white">B</span>
                  Compare
                </span>
                <select
                  v-model="compareVersionBId"
                  class="clm-agent-input mt-1.5 w-full rounded-lg border border-violet-200/90 bg-white py-2 pl-2.5 pr-8 text-[11px] text-slate-900 dark:border-violet-800/60 dark:bg-slate-950 dark:text-slate-100"
                >
                  <option value="" disabled>Choose version B…</option>
                  <option
                    v-for="v in sortedDocumentVersions"
                    :key="'cmp-b-modern-' + v.id"
                    :value="String(v.id)"
                    :disabled="String(v.id) === compareVersionAId"
                  >
                    {{ formatVersionCompareLabel(v) }}
                  </option>
                </select>
              </label>

              <button
                type="button"
                class="inline-flex items-center justify-center gap-1.5 rounded-xl bg-sky-600 px-3 py-2 text-[10px] font-black uppercase tracking-wide text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
                :disabled="!canRunCompareNow || compareTyping"
                @click="runCompareNow()"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                Run
              </button>
            </div>

            <div class="flex flex-wrap items-center gap-2 text-[10px]">
              <button
                type="button"
                class="rounded-lg border border-slate-200/90 bg-white px-2.5 py-1 font-bold uppercase tracking-wide text-slate-600 transition hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                @click="compareDocPreviewsVisible = !compareDocPreviewsVisible"
              >
                {{ compareDocPreviewsVisible ? 'Hide previews' : 'Show previews' }}
              </button>
              <button
                type="button"
                class="rounded-lg border border-slate-200/90 bg-white px-2.5 py-1 font-bold uppercase tracking-wide text-slate-600 transition hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                @click="resetCompareSelection"
              >
                Reset
              </button>
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                A: {{ selectedCompareVersionA ? formatVersionCompareLabel(selectedCompareVersionA) : 'Not selected' }}
              </span>
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                B: {{ selectedCompareVersionB ? formatVersionCompareLabel(selectedCompareVersionB) : 'Not selected' }}
              </span>
            </div>

            <div v-if="compareSetupExpanded" class="rounded-xl border border-slate-200/80 bg-white/70 p-2.5 dark:border-slate-700 dark:bg-slate-900/40">
              <p class="mb-2 text-[10px] font-black uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Smart compare prompts
              </p>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="preset in comparePromptPresets"
                  :key="preset"
                  type="button"
                  class="rounded-full border border-slate-200/90 bg-slate-50 px-2.5 py-1 text-[10px] font-semibold text-slate-700 transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-sky-700 dark:hover:bg-sky-950/35 dark:hover:text-sky-200"
                  :disabled="!canRunCompareNow || compareTyping"
                  @click="runCompareNow(preset)"
                >
                  {{ preset }}
                </button>
              </div>
            </div>

            <div
              v-if="compareDocPreviewsVisible && sortedDocumentVersions.length >= 2"
              :class="comparePanelDense ? 'mt-1.5' : ''"
              class="rounded-xl border border-slate-200/90 bg-white/85 p-2 shadow-sm dark:border-slate-700 dark:bg-slate-900/45"
            >
              <div class="grid grid-cols-1 gap-2 sm:grid-cols-2 sm:gap-0" :class="compareThumbCompact ? 'sm:gap-2' : ''">
                <div :class="compareThumbCompact ? '' : 'sm:pr-2 sm:border-r sm:border-slate-200/80 dark:sm:border-slate-600/80'">
                  <ComparePdfThumb
                    label="A"
                    :compact="compareThumbCompact"
                    :contract-id="contractId"
                    :version-id="compareVersionAId"
                    :subtitle="selectedCompareVersionA ? formatVersionCompareLabel(selectedCompareVersionA) : ''"
                    :file-type="selectedCompareVersionA?.file_type || ''"
                  />
                </div>
                <div :class="compareThumbCompact ? '' : 'sm:pl-2'">
                  <ComparePdfThumb
                    label="B"
                    :compact="compareThumbCompact"
                    :contract-id="contractId"
                    :version-id="compareVersionBId"
                    :subtitle="selectedCompareVersionB ? formatVersionCompareLabel(selectedCompareVersionB) : ''"
                    :file-type="selectedCompareVersionB?.file_type || ''"
                  />
                </div>
              </div>
            </div>

            <p
              v-if="sortedDocumentVersions.length < 2"
              class="rounded-xl border border-amber-200/90 bg-amber-50/90 px-3 py-2 text-[10px] leading-relaxed text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-100"
            >
              Add at least <strong>two document versions</strong> to run comparison.
            </p>
          </div>
        </div>

        <!-- Review / Draft: full-height scoring picker (replaces message list until user focuses chat input or Done) -->
        <div
          v-if="(selectedAgent === 'review' || selectedAgent === 'draft') && reviewContextFullSpace"
          class="flex min-h-0 flex-1 flex-col overflow-hidden border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900"
        >
          <div class="flex shrink-0 items-start justify-between gap-2 border-b border-slate-200 px-3 py-2.5 dark:border-gray-700">
            <div class="min-w-0">
              <p class="text-[11px] font-black uppercase tracking-wide text-slate-800 dark:text-slate-100">Scoring context</p>
              <p class="mt-0.5 text-[9px] leading-snug text-slate-500 dark:text-slate-400">
                Select findings or recommendations for Review or Draft, then tap your message field below to return to chat.
              </p>
            </div>
            <div class="flex shrink-0 flex-col items-end gap-1">
              <button
                type="button"
                class="rounded-lg bg-slate-800 px-3 py-1.5 text-[10px] font-bold text-white shadow-sm transition hover:bg-slate-900 dark:bg-blue-600 dark:hover:bg-blue-500"
                @click="closeReviewContextPanel"
              >
                Done
              </button>
              <button
                v-if="selectedReviewContextCount"
                type="button"
                class="text-[9px] font-bold uppercase tracking-wide text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                @click="clearReviewScoringSelection"
              >
                Clear all
              </button>
            </div>
          </div>

          <div
            v-if="selectedAgent === 'review' || selectedAgent === 'draft'"
            class="shrink-0 border-b border-amber-200/50 bg-amber-50/30 px-3 py-2 dark:border-amber-900/30 dark:bg-amber-950/20"
          >
            <label class="flex cursor-pointer items-start gap-2">
              <input v-model="cpwdCopilotEnabled" type="checkbox" class="mt-0.5 rounded border-amber-400 text-amber-700 focus:ring-amber-500" />
              <span class="min-w-0 text-[10px] leading-snug text-amber-950/90 dark:text-amber-100/90">
                <span class="font-bold">CPWD Copilot</span>
                <span class="font-normal text-amber-900/75 dark:text-amber-200/80">
                  — premium context (Review: no saved review items; Draft: includes them).
                </span>
              </span>
            </label>
          </div>

          <DraftRedlineProgress
            v-if="selectedAgent === 'draft' && draftTyping && reviewContextFullSpace"
            :active="draftTyping"
            :finalizing="draftRedlineFinalizing"
            :todo-lines="draftTodoProgressLines"
            class="mx-3 mb-2 mt-1 shrink-0"
          />

          <div class="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden px-2.5 pb-2 pt-2">
            <p v-if="scoringLoading || scoringTriggering || scoringBackgroundRunning" class="flex flex-1 items-center justify-center text-center text-[10px] text-slate-500 dark:text-slate-400">{{ scoringTriggering ? 'Running scoring…' : scoringBackgroundRunning ? 'Background scoring…' : 'Loading scoring…' }}</p>
            <div
              v-else-if="!scoringData"
              class="flex flex-1 flex-col items-center justify-center gap-2 px-2"
            >
              <button
                type="button"
                class="rounded-lg bg-slate-800 px-4 py-2 text-[10px] font-bold text-white dark:bg-blue-600"
                @click="fetchScoring"
              >
                Load scoring
              </button>
              <button
                type="button"
                class="rounded-lg bg-blue-600 px-4 py-2 text-[10px] font-bold text-white hover:bg-blue-700"
                @click="triggerScoring"
                :disabled="scoringTriggering"
              >
                Trigger Scoring
              </button>
            </div>

            <template v-else>
              <div
                v-if="reviewSelectableFindings.length || reviewSelectableRecommendations.length"
                class="flex shrink-0 rounded-md bg-slate-100 p-0.5 dark:bg-gray-800"
                role="tablist"
                aria-label="Scoring context type"
              >
                <button
                  v-if="reviewSelectableFindings.length"
                  type="button"
                  role="tab"
                  :aria-selected="reviewContextTab === 'findings'"
                  class="relative flex min-w-0 flex-1 items-center justify-center gap-1 rounded px-2 py-1.5 text-[10px] font-black uppercase tracking-wide transition"
                  :class="reviewContextTab === 'findings'
                    ? 'bg-white text-amber-800 shadow-sm dark:bg-gray-700 dark:text-amber-200'
                    : 'text-slate-500 dark:text-slate-400'"
                  @click="reviewContextTab = 'findings'"
                >
                  Findings
                  <span class="tabular-nums opacity-80">{{ reviewSelectableFindings.length }}</span>
                  <span
                    v-if="selectedReviewFindingCount"
                    class="absolute -right-0.5 -top-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-amber-500 px-0.5 text-[8px] font-black text-white"
                  >{{ selectedReviewFindingCount }}</span>
                </button>
                <button
                  v-if="reviewSelectableRecommendations.length"
                  type="button"
                  role="tab"
                  :aria-selected="reviewContextTab === 'recommendations'"
                  class="relative flex min-w-0 flex-1 items-center justify-center gap-1 rounded px-2 py-1.5 text-[10px] font-black uppercase tracking-wide transition"
                  :class="reviewContextTab === 'recommendations'
                    ? 'bg-white text-indigo-800 shadow-sm dark:bg-gray-700 dark:text-indigo-200'
                    : 'text-slate-500 dark:text-slate-400'"
                  @click="reviewContextTab = 'recommendations'"
                >
                  Recs
                  <span class="tabular-nums opacity-80">{{ reviewSelectableRecommendations.length }}</span>
                  <span
                    v-if="selectedReviewRecommendationCount"
                    class="absolute -right-0.5 -top-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-indigo-500 px-0.5 text-[8px] font-black text-white"
                  >{{ selectedReviewRecommendationCount }}</span>
                </button>
              </div>

              <div
                v-show="reviewContextTab === 'findings' && reviewSelectableFindings.length"
                class="flex min-h-0 flex-1 flex-col overflow-hidden"
              >
                <div class="mb-1.5 flex shrink-0 items-center justify-end px-0.5">
                  <button
                    type="button"
                    class="rounded-md border border-amber-300/90 bg-amber-50 px-2.5 py-1 text-[9px] font-black uppercase tracking-wide text-amber-950 shadow-sm transition hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-45 dark:border-amber-800/80 dark:bg-amber-950/40 dark:text-amber-100 dark:hover:bg-amber-950/60"
                    :disabled="allReviewFindingsSelected"
                    @click="selectAllReviewFindings"
                  >
                    Select all findings
                  </button>
                </div>
                <ul class="min-h-0 flex-1 space-y-0.5 overflow-y-auto rounded-lg border border-amber-200/80 bg-amber-50/30 py-1 dark:border-amber-900/40 dark:bg-amber-950/20">
                  <li v-for="(f, fi) in reviewSelectableFindings" :key="f.id">
                    <button
                      type="button"
                      :aria-pressed="selectedReviewFindingIds.includes(f.id)"
                      class="group flex w-full items-start gap-2 px-2.5 py-2 text-left transition"
                      :class="selectedReviewFindingIds.includes(f.id) ? 'bg-amber-100/90 dark:bg-amber-950/45' : 'hover:bg-amber-50/80 dark:hover:bg-amber-950/25'"
                      @click="toggleReviewFindingId(f.id)"
                    >
                      <span
                        class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border transition"
                        :class="selectedReviewFindingIds.includes(f.id)
                          ? 'border-amber-500 bg-amber-500 text-white'
                          : 'border-amber-300/90 bg-white text-transparent dark:border-amber-800 dark:bg-gray-900'"
                      >
                        <svg class="h-2.5 w-2.5 stroke-[3]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                      </span>
                      <span class="min-w-0 flex-1 text-[11px] font-medium leading-snug text-slate-800 dark:text-slate-100">
                        <span class="mr-1.5 inline-block w-4 text-[9px] font-black text-amber-600 dark:text-amber-400">{{ fi + 1 }}</span>{{ f.preview }}
                      </span>
                    </button>
                  </li>
                </ul>
              </div>

              <div
                v-show="reviewContextTab === 'recommendations' && reviewSelectableRecommendations.length"
                class="flex min-h-0 flex-1 flex-col overflow-hidden"
              >
                <div class="mb-1.5 flex shrink-0 items-center justify-end px-0.5">
                  <button
                    type="button"
                    class="rounded-md border border-indigo-300/90 bg-indigo-50 px-2.5 py-1 text-[9px] font-black uppercase tracking-wide text-indigo-950 shadow-sm transition hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-45 dark:border-indigo-800/80 dark:bg-indigo-950/40 dark:text-indigo-100 dark:hover:bg-indigo-950/60"
                    :disabled="allReviewRecommendationsSelected"
                    @click="selectAllReviewRecommendations"
                  >
                    Select all recommendations
                  </button>
                </div>
                <ul class="min-h-0 flex-1 space-y-0.5 overflow-y-auto rounded-lg border border-indigo-200/80 bg-indigo-50/30 py-1 dark:border-indigo-900/40 dark:bg-indigo-950/20">
                  <li v-for="(r, ri) in reviewSelectableRecommendations" :key="r.id">
                    <button
                      type="button"
                      :aria-pressed="selectedReviewRecommendationIds.includes(r.id)"
                      class="group flex w-full items-start gap-2 px-2.5 py-2 text-left transition"
                      :class="selectedReviewRecommendationIds.includes(r.id) ? 'bg-indigo-100/90 dark:bg-indigo-950/45' : 'hover:bg-indigo-50/80 dark:hover:bg-indigo-950/25'"
                      @click="toggleReviewRecommendationId(r.id)"
                    >
                      <span
                        class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border transition"
                        :class="selectedReviewRecommendationIds.includes(r.id)
                          ? 'border-indigo-500 bg-indigo-500 text-white'
                          : 'border-indigo-300/90 bg-white text-transparent dark:border-indigo-800 dark:bg-gray-900'"
                      >
                        <svg class="h-2.5 w-2.5 stroke-[3]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                      </span>
                      <span class="min-w-0 flex-1 text-[11px] font-medium leading-snug text-slate-800 dark:text-slate-100">
                        <span class="mr-1.5 inline-block w-4 text-[9px] font-black text-indigo-600 dark:text-indigo-400">{{ ri + 1 }}</span>{{ r.preview }}
                      </span>
                    </button>
                  </li>
                </ul>
              </div>

              <p
                v-if="!reviewSelectableFindings.length && !reviewSelectableRecommendations.length"
                class="flex flex-1 items-center justify-center py-6 text-center text-[10px] text-slate-500 dark:text-slate-400"
              >
                No findings or recommendations.
              </p>
            </template>
          </div>
        </div>

        <!-- Review agent: streaming todo list (write_todos from /ws/review) -->
        <div
          v-if="selectedAgent === 'review' && reviewTodos.length > 0 && !reviewContextFullSpace"
          class="max-h-40 shrink-0 overflow-y-auto border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-3"
        >
          <p class="text-[10px] font-black uppercase tracking-wider text-[var(--clm-text-muted)]">Live plan</p>
          <ul class="mt-2 space-y-2">
            <li
              v-for="(todo, ti) in reviewTodos"
              :key="ti"
              class="flex gap-2 text-[11px] leading-snug text-[var(--clm-text)]"
            >
              <span
                class="mt-0.5 shrink-0 text-base leading-none"
                :class="reviewTodoIconClass(todo.status)"
                :title="todo.status"
              >{{ reviewTodoStatusGlyph(todo.status) }}</span>
              <span class="min-w-0 flex-1">{{ todo.content }}</span>
            </li>
          </ul>
        </div>

        <!-- Draft agent: same live plan UI as review (/ws/draft) -->
        <div
          v-if="selectedAgent === 'draft' && draftTodos.length > 0 && !reviewContextFullSpace"
          class="max-h-40 shrink-0 overflow-y-auto border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-3"
        >
          <p class="text-[10px] font-black uppercase tracking-wider text-[var(--clm-text-muted)]">Drafting plan</p>
          <ul class="mt-2 space-y-2">
            <li
              v-for="(todo, ti) in draftTodos"
              :key="`draft-todo-${ti}`"
              class="flex gap-2 text-[11px] leading-snug text-[var(--clm-text)]"
            >
              <span
                class="mt-0.5 shrink-0 text-base leading-none"
                :class="reviewTodoIconClass(todo.status)"
                :title="todo.status"
              >{{ reviewTodoStatusGlyph(todo.status) }}</span>
              <span class="min-w-0 flex-1">{{ todo.content }}</span>
            </li>
          </ul>
        </div>

        <div
          v-if="selectedAgent === 'draft' && draftTyping && !reviewContextFullSpace"
          class="shrink-0 border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-4 py-3"
        >
          <DraftRedlineProgress
            :active="draftTyping"
            :finalizing="draftRedlineFinalizing"
            :todo-lines="draftTodoProgressLines"
          />
        </div>

        <div
          v-if="!((selectedAgent === 'review' || selectedAgent === 'draft') && reviewContextFullSpace)"
          class="clm-agent-chat-scroll min-h-0 min-w-0 flex-1 overflow-x-hidden overflow-y-auto overscroll-y-contain space-y-4 bg-gray-100/60 sm:px-4 dark:bg-gray-900/40"
          :class="
            selectedAgent === 'compare'
              ? compareTopPanelHidden
                ? 'px-3 py-3 sm:py-4'
                : 'px-3 pt-5 pb-4 sm:pt-6 sm:pb-5'
              : 'px-3 py-3 sm:py-4'
          "
          id="chat-messages"
        >
          <!-- Agent guide + suggested queries (engagement layer) -->
          <div
            v-if="agentGuideUi"
            class="clm-agent-guide relative mb-4 overflow-hidden rounded-2xl border border-indigo-200/60 bg-gradient-to-br from-white via-indigo-50/40 to-violet-50/50 shadow-md shadow-indigo-900/5 dark:border-indigo-900/40 dark:from-slate-900/90 dark:via-indigo-950/40 dark:to-violet-950/30"
          >
            <div
              class="pointer-events-none absolute inset-0 opacity-40 dark:opacity-25 clm-agent-guide-shimmer"
              aria-hidden="true"
            />
            <div class="relative px-3 py-3 sm:px-4 sm:py-3.5">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="text-[10px] font-black uppercase tracking-[0.18em] text-indigo-600 dark:text-indigo-300">
                    {{ agentGuideUi.kicker }}
                  </p>
                  <h4 class="mt-1 text-sm font-black leading-tight text-slate-900 dark:text-white">
                    {{ agentGuideUi.title }}
                  </h4>
                  <p class="mt-1.5 text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                    {{ agentGuideUi.purpose }}
                  </p>
                </div>
                <button
                  type="button"
                  class="shrink-0 rounded-lg border border-slate-200/90 bg-white/90 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-slate-500 transition hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
                  @click="agentGuideCollapsed = !agentGuideCollapsed"
                >
                  {{ agentGuideCollapsed ? 'Show' : 'Hide' }}
                </button>
              </div>
              <Transition name="clm-agent-guide-collapse">
                <div v-show="!agentGuideCollapsed" class="mt-3 space-y-3">
                  <ul class="space-y-2">
                    <li
                      v-for="(step, si) in agentGuideUi.steps"
                      :key="'ag-step-' + si"
                      class="flex gap-2.5 rounded-xl border border-white/80 bg-white/70 px-2.5 py-2 text-[11px] leading-snug text-slate-700 shadow-sm dark:border-slate-700/80 dark:bg-slate-900/50 dark:text-slate-200"
                    >
                      <span
                        class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-[10px] font-black text-white shadow-sm"
                      >{{ si + 1 }}</span>
                      <span class="min-w-0">
                        <span class="font-bold text-slate-800 dark:text-white">{{ step.label }}</span>
                        <span class="mt-0.5 block text-[10px] text-slate-500 dark:text-slate-400">{{ step.detail }}</span>
                      </span>
                    </li>
                  </ul>
                  <div>
                    <p class="mb-2 text-[10px] font-black uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Try a suggestion
                    </p>
                    <div class="flex flex-wrap gap-1.5">
                      <button
                        v-for="(sq, i) in agentSuggestedQueries"
                        :key="'agent-sq-' + i"
                        type="button"
                        class="group max-w-full rounded-full border border-indigo-200/90 bg-white/90 px-2.5 py-1.5 text-left text-[10px] font-semibold leading-snug text-indigo-800 shadow-sm transition hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-md dark:border-indigo-800/80 dark:bg-indigo-950/40 dark:text-indigo-100 dark:hover:bg-indigo-900/50"
                        :disabled="suggestedQueryDisabled"
                        :title="suggestedQueryDisabled ? 'Wait for the assistant to finish this reply.' : 'Tap to send'"
                        @click="applyAgentSuggestedQuery(sq)"
                      >
                        <span class="mr-1 inline-block opacity-0 transition group-hover:opacity-100">→</span>
                        {{ sq }}
                      </button>
                    </div>
                  </div>
                </div>
              </Transition>
            </div>
          </div>

          <div v-for="(msg, idx) in chatMessages[selectedAgent]" :key="idx" class="flex flex-col" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
            <div class="mb-1 flex items-center gap-2 px-2 text-[10px] font-semibold text-gray-400">
              <span class="h-2.5 w-2.5 rounded-full" :class="msg.role === 'user' ? 'bg-emerald-400' : 'bg-indigo-400'"></span>
              {{ msg.role === 'user' ? 'You' : getAgentName(selectedAgent) }}
              <span
                v-if="msg.role === 'assistant' && (msg.reviewStreaming || msg.draftStreaming || msg.compareStreaming)"
                class="rounded-full bg-amber-500/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-amber-700 dark:text-amber-300"
              >Streaming</span>
            </div>
            <div class="max-w-[min(96vw,100%)] min-w-0 sm:max-w-[96%] rounded-[1.4rem] px-3 py-2.5 text-sm shadow-lg shadow-gray-900/4 sm:px-4" :class="msg.role === 'user' ? 'rounded-br-lg bg-gradient-to-r from-blue-600 to-blue-700 text-white' : 'rounded-bl-lg border border-white/70 bg-white/95 text-gray-700 dark:bg-gray-800 dark:text-gray-200'">
              <div class="clm-agent-message-body">
                <ChatMarkdown
                  v-if="!msg.isAccordion && msg.role === 'assistant' && msg.markdown"
                  :content="msg.content || ''"
                  :streaming="!!msg.reviewStreaming || !!msg.draftStreaming || !!msg.compareStreaming"
                />
                <div v-else-if="!msg.isAccordion">{{ msg.content }}</div>
              </div>

              <div
                v-if="msg.attachments?.length"
                class="mt-3 flex flex-col gap-2.5"
              >
                <ChatAttachmentCard
                  v-for="(att, ai) in msg.attachments"
                  :key="`chat-att-${idx}-${ai}`"
                  :href="chatAttachmentDataUrl(att)"
                  :filename="att.filename || 'attachment'"
                  :subtitle="chatAttachmentSubtitle(att)"
                  @edit="openDocxEditor(att)"
                />
              </div>

              <div
                v-if="msg.role === 'assistant' && selectedAgent === 'graph' && msg.contextValues?.length"
                class="mt-2 flex flex-wrap gap-1.5"
              >
                <button
                  v-for="(ctxVal, cIdx) in msg.contextValues"
                  :key="`graph-ctx-${idx}-${cIdx}`"
                  type="button"
                  class="rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-[10px] text-blue-700 transition hover:bg-blue-100 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-200 dark:hover:bg-blue-900/45"
                  @click="selectGraphNodeFromValue(ctxVal)"
                >
                  {{ ctxVal }}
                </button>
              </div>

              <div v-if="msg.isAccordion" class="space-y-2">
                <p class="text-[10px] font-black uppercase text-gray-500 mb-2">{{ msg.content }}</p>
                <div v-for="comp in msg.complaints" :key="comp.id" class="overflow-hidden border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900">
                  <button @click="comp.isOpen = !comp.isOpen" class="w-full px-3 py-2 flex justify-between items-center gap-2 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition">
                    <span class="text-xs font-bold truncate pr-2 dark:text-white">{{ comp.check_name }}</span>
                    <svg class="w-3 h-3 text-gray-500 shrink-0 transition-transform" :class="{ 'rotate-180': comp.isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                  </button>
                  <div v-if="comp.isOpen" class="px-3 py-2 border-t border-gray-100 dark:border-gray-700 text-[11px] text-gray-600 dark:text-gray-400 whitespace-pre-wrap leading-relaxed">
                    {{ comp.findings }}
                  </div>
                </div>
              </div>

              <div v-if="msg.role === 'assistant' && selectedAgent === 'complaints' && idx === chatMessages.complaints.length - 1 && complaintLibrary.length > 0" class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                <div class="flex items-center justify-between">
                  <p class="text-[10px] font-black text-gray-400 uppercase">Select from Database:</p>
                  <button @click="showComplaintModal = true" class="text-[10px] font-black text-blue-600 hover:underline">OPEN SELECTOR</button>
                </div>
              </div>

              <!-- Save + Generate Fix — review agent assistant messages only -->
              <div
                v-if="selectedAgent === 'review' && shouldShowReviewActionButtons(idx, msg) && msg.content && !msg.reviewStreaming && !isReviewAgentErrorMessage(msg)"
                class="mt-2.5 flex items-center gap-2 border-t border-gray-100 pt-2 dark:border-gray-700"
              >
                <button
                  type="button"
                  class="flex items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-gray-500 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/30 dark:hover:text-indigo-300"
                  :class="{ 'opacity-50 pointer-events-none': savedReviewMsgIds.has(idx) }"
                  @click="saveReviewItem(msg, idx)"
                  :title="savedReviewMsgIds.has(idx) ? 'Saved' : 'Save as actionable review item'"
                >
                  <svg v-if="!savedReviewMsgIds.has(idx)" class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                  <svg v-else class="h-3 w-3 text-indigo-500" fill="currentColor" viewBox="0 0 24 24"><path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                  {{ savedReviewMsgIds.has(idx) ? 'Saved' : 'Save to review items' }}
                </button>
                <button
                  v-if="!isGenerateFixResponseMessage(msg)"
                  type="button"
                  class="flex items-center gap-1 rounded-lg border border-violet-200 bg-violet-50 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-violet-700 transition hover:border-violet-400 hover:bg-violet-100 hover:text-violet-800 dark:border-violet-700 dark:bg-violet-900/30 dark:text-violet-300 dark:hover:border-violet-500 dark:hover:bg-violet-900/45 dark:hover:text-violet-200"
                  :disabled="reviewTyping"
                  @click="generateFixFromReviewMessage(msg)"
                  title="Generate actionable items from this review response"
                >
                  <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 4v16m8-8H4"/></svg>
                  Generate Fix
                </button>
                <span v-if="savedReviewMsgIds.has(idx)" class="text-[9px] text-indigo-500">✓ Added to redraft context</span>
              </div>
            </div>

            <!-- ── Review items badges (draft agent user messages) ─── -->
            <div v-if="msg.reviewItems?.length" class="mt-1.5 flex flex-wrap items-center gap-1.5 w-full max-w-[min(96vw,100%)] sm:max-w-[96%]">
              <span class="text-[9px] font-bold uppercase tracking-wide text-slate-400">Review items:</span>
              <span
                v-for="ri in msg.reviewItems" :key="ri.id"
                class="inline-flex items-center gap-1 rounded-full bg-violet-50 px-2 py-0.5 text-[9px] font-semibold text-violet-700 ring-1 ring-violet-200 dark:bg-violet-900/30 dark:text-violet-300 dark:ring-violet-700/40"
              >
                <span v-if="ri.severity" class="h-1.5 w-1.5 rounded-full" :class="ri.severity==='critical'?'bg-red-500':ri.severity==='moderate'?'bg-amber-500':'bg-gray-400'"></span>
                {{ (ri.title || 'Finding').slice(0, 40) }}
              </span>
            </div>

            <!-- ── Guideline section cards (outside bubble) ────────── -->
            <div v-if="msg.guidelineSections?.length" class="mt-1.5 w-full max-w-[min(96vw,100%)] sm:max-w-[96%]">
              <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
                <div class="flex items-center gap-1.5 border-b border-slate-100 px-2.5 py-1.5 dark:border-slate-800">
                  <svg class="h-3 w-3 shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                  <span class="text-[9px] font-bold uppercase tracking-wide text-slate-400">Guideline context · {{ msg.guidelineSections.length }} {{ msg.guidelineSections.length === 1 ? 'section' : 'sections' }}</span>
                  <span class="ml-1 rounded-full bg-amber-100 px-2 py-px text-[8px] font-bold text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">Compliance analysis</span>
                  <span v-if="msg.guidelineNote" class="ml-auto truncate text-[9px] italic text-slate-400">{{ msg.guidelineNote }}</span>
                </div>
                <div class="divide-y divide-slate-100 dark:divide-slate-800">
                  <GuidelineSectionCard
                    v-for="gs in msg.guidelineSections"
                    :key="gs.key"
                    :section="gs"
                  />
                </div>
              </div>
            </div>

            <div v-if="msg.complianceChecks?.length" class="mt-1.5 w-full max-w-[min(96vw,100%)] sm:max-w-[96%]">
              <div class="overflow-hidden rounded-xl border border-amber-200/80 bg-amber-50/40 shadow-sm dark:border-amber-800/50 dark:bg-amber-950/20">
                <div class="flex flex-wrap items-center gap-1.5 border-b border-amber-200/80 px-2.5 py-1.5 dark:border-amber-800/50">
                  <svg class="h-3 w-3 shrink-0 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                  <span class="text-[9px] font-bold uppercase tracking-wide text-amber-800 dark:text-amber-300">Compliance context · {{ msg.complianceChecks.length }} {{ msg.complianceChecks.length === 1 ? 'check' : 'checks' }}</span>
                </div>
                <ul class="divide-y divide-amber-200/60 dark:divide-amber-900/40">
                  <li v-for="chk in msg.complianceChecks" :key="chk.id" class="px-2.5 py-2">
                    <div class="flex flex-wrap items-center gap-1.5">
                      <span
                        class="h-1.5 w-1.5 shrink-0 rounded-full"
                        :class="(chk.status||'').toLowerCase()==='passed' ? 'bg-green-500' : (chk.status||'').toLowerCase()==='warning' ? 'bg-amber-400' : 'bg-red-400'"
                      />
                      <span class="min-w-0 flex-1 text-[11px] font-semibold text-gray-800 dark:text-gray-100">{{ chk.check_name }}</span>
                      <span class="shrink-0 text-[9px] font-bold uppercase text-amber-800 dark:text-amber-300">{{ chk.status }}</span>
                      <span v-if="chk.page_number != null" class="shrink-0 text-[9px] tabular-nums text-gray-400">p.{{ chk.page_number }}</span>
                    </div>
                    <p v-if="chk.findings" class="mt-1 line-clamp-4 text-[10px] leading-snug text-gray-600 dark:text-gray-400">{{ chk.findings }}</p>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <div
            v-if="
              (selectedAgent === 'review' && reviewTyping) ||
              (selectedAgent === 'draft' && draftTyping) ||
              (selectedAgent === 'compare' && compareTyping) ||
              (selectedAgent !== 'review' && selectedAgent !== 'draft' && selectedAgent !== 'compare' && isTyping)
            "
            class="flex flex-col items-start"
          >
            <div class="text-[10px] text-gray-400 mb-1 px-2">
              {{ getAgentName(selectedAgent) }} is thinking...
            </div>
            <div class="rounded-3xl rounded-bl-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-700">
              <div class="flex gap-1">
                <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="shrink-0 border-t border-gray-100 bg-white/90 dark:border-gray-700 dark:bg-gray-800/80 pb-[max(0.5rem,env(safe-area-inset-bottom))]">

          <!-- ── Guideline picker popover ────────────────────────────── -->
          <Transition enter-active-class="transition duration-150 ease-out" enter-from-class="opacity-0 translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-100 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
            <div v-if="glPickerOpen && selectedAgent === 'review'" class="mx-3 mb-2 mt-2 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-600 dark:bg-gray-800">
              <div class="flex items-center justify-between border-b border-gray-100 px-3 py-2 dark:border-gray-700">
                <p class="text-[11px] font-black uppercase tracking-wide text-gray-500 dark:text-gray-400">Select guideline sections to include</p>
                <button type="button" @click="glPickerOpen = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>
              <div v-if="availableGlSections.length === 0" class="px-3 py-4 text-center text-[11px] text-gray-400">
                No guideline data on this contract yet — go to the <strong>Guidelines</strong> tab to load one.
              </div>
              <div v-else class="grid grid-cols-2 gap-px bg-gray-100 dark:bg-gray-700">
                <label
                  v-for="s in availableGlSections" :key="s.key"
                  class="flex cursor-pointer items-center gap-2 bg-white px-3 py-2 transition hover:bg-blue-50 dark:bg-gray-800 dark:hover:bg-gray-700"
                >
                  <input type="checkbox" :checked="glSelectedKeys.has(s.key)" @change="glToggleKey(s.key)" class="h-3.5 w-3.5 rounded accent-blue-600" />
                  <span class="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded bg-gray-100 text-[8px] font-black uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">{{ s.abbr }}</span>
                  <span class="truncate text-[11px] font-semibold text-gray-700 dark:text-gray-200">{{ s.title }}</span>
                </label>
              </div>
              <div class="flex items-center justify-between gap-2 border-t border-gray-100 px-3 py-2 dark:border-gray-700">
                <button type="button" @click="glSelectedKeys = new Set()" class="text-[10px] font-semibold text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">Clear all</button>
                <div class="flex items-center gap-1.5">
                  <button
                    type="button"
                    class="text-[10px] font-semibold text-blue-600 hover:text-blue-800 dark:text-blue-300 dark:hover:text-blue-200"
                    :disabled="availableGlSections.length === 0 || reviewTyping"
                    @click="selectAllGuidelineSections"
                  >
                    {{ glSelectedKeys.size === availableGlSections.length ? 'Clear all' : 'Select all' }}
                  </button>
                  <button
                    type="button"
                    class="rounded-lg bg-gray-900 px-3 py-1.5 text-[11px] font-bold text-white shadow-sm hover:bg-black disabled:opacity-50"
                    :disabled="glSelectedKeys.size === 0 || reviewTyping"
                    @click="runSelectedGuidelinesNow"
                  >
                    Run ({{ glSelectedKeys.size }} selected)
                  </button>
                  <button type="button" @click="glPickerOpen = false" class="rounded-lg bg-blue-600 px-3 py-1.5 text-[11px] font-bold text-white shadow-sm hover:bg-blue-700">
                    Done ({{ glSelectedKeys.size }} selected)
                  </button>
                </div>
              </div>
            </div>
          </Transition>

          <!-- ── Selected section widgets strip ─────────────────────── -->
          <div v-if="glSelectedKeys.size > 0 && selectedAgent === 'review'" class="flex items-center gap-1.5 overflow-x-auto px-3 py-2">
            <span class="shrink-0 text-[10px] font-bold uppercase text-gray-400">Context:</span>
            <span
              v-for="s in glSelectedList" :key="s.key"
              class="group inline-flex shrink-0 items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-[10px] font-bold text-blue-700 ring-1 ring-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:ring-blue-700/40"
            >
              <span class="h-1.5 w-1.5 rounded-full bg-blue-500 dark:bg-blue-400"></span>
              {{ s.title }}
              <button type="button" @click="glRemoveKey(s.key)" class="ml-0.5 leading-none text-blue-400 opacity-60 transition hover:text-red-500 hover:opacity-100">×</button>
            </span>
            <button type="button" @click="glClearAll()" class="shrink-0 text-[10px] text-gray-400 hover:text-red-400">Clear</button>
          </div>

          <!-- ── Compliance picker popover ───────────────────────────── -->
          <Transition enter-active-class="transition duration-150 ease-out" enter-from-class="opacity-0 translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-100 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
            <div v-if="cpPickerOpen && selectedAgent === 'review'" class="mx-3 mb-2 mt-2 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-600 dark:bg-gray-800">
              <div class="flex items-start justify-between gap-2 border-b border-gray-100 px-3 py-2 dark:border-gray-700">
                <div class="min-w-0 pr-2">
                  <p class="text-[11px] font-black uppercase tracking-wide text-gray-500 dark:text-gray-400">Compliance for Review agent</p>
                  <p class="mt-0.5 text-[10px] leading-snug text-gray-400 dark:text-gray-500">Same as Guidelines: pick checks, then Send or Run.</p>
                </div>
                <button type="button" @click="cpPickerOpen = false" class="shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>
              <div v-if="complianceRecordsForVersion.length === 0" class="px-3 py-4 text-center text-[11px] text-gray-400">
                No compliance checks for this version yet — run compliance first.
              </div>
              <div v-else class="max-h-56 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700">
                <label
                  v-for="rec in complianceRecordsForVersion" :key="rec.id"
                  class="flex cursor-pointer items-center gap-2.5 px-3 py-2 transition hover:bg-amber-50 dark:hover:bg-gray-700"
                >
                  <input type="checkbox" :checked="cpSelectedIds.has(rec.id)" @change="cpToggleId(rec.id)" class="h-3.5 w-3.5 rounded accent-amber-500 shrink-0" />
                  <span
                    class="h-2 w-2 shrink-0 rounded-full"
                    :class="(rec.status||'').toLowerCase()==='passed' ? 'bg-green-500' : (rec.status||'').toLowerCase()==='warning' ? 'bg-amber-400' : 'bg-red-400'"
                  ></span>
                  <span class="min-w-0 flex-1 truncate text-[11px] font-semibold text-gray-700 dark:text-gray-200">{{ rec.check_name }}</span>
                  <span class="shrink-0 text-[9px] font-bold uppercase" :class="(rec.status||'').toLowerCase()==='passed' ? 'text-green-600' : (rec.status||'').toLowerCase()==='warning' ? 'text-amber-500' : 'text-red-500'">{{ rec.status }}</span>
                </label>
              </div>
              <div class="flex items-center justify-between gap-2 border-t border-gray-100 px-3 py-2 dark:border-gray-700">
                <button type="button" @click="cpClearAll()" class="text-[10px] font-semibold text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">Clear all</button>
                <div class="flex items-center gap-1.5">
                  <button
                    type="button"
                    class="text-[10px] font-semibold text-amber-600 hover:text-amber-800 dark:text-amber-300 dark:hover:text-amber-200"
                    :disabled="complianceRecordsForVersion.length === 0 || reviewTyping"
                    @click="selectAllComplianceChecks"
                  >
                    {{ cpSelectedIds.size === complianceRecordsForVersion.length ? 'Clear all' : 'Select all' }}
                  </button>
                  <button
                    type="button"
                    class="rounded-lg bg-gray-900 px-3 py-1.5 text-[11px] font-bold text-white shadow-sm hover:bg-black disabled:opacity-50"
                    :disabled="cpSelectedIds.size === 0 || reviewTyping"
                    @click="runSelectedComplianceNow"
                  >
                    Run ({{ cpSelectedIds.size }} selected)
                  </button>
                  <button type="button" @click="cpPickerOpen = false" class="rounded-lg bg-amber-500 px-3 py-1.5 text-[11px] font-bold text-white shadow-sm hover:bg-amber-600">
                    Done ({{ cpSelectedIds.size }} selected)
                  </button>
                </div>
              </div>
            </div>
          </Transition>

          <!-- ── Selected compliance checks strip ────────────────────── -->
          <div v-if="cpSelectedIds.size > 0 && selectedAgent === 'review'" class="flex items-center gap-1.5 overflow-x-auto px-3 py-2">
            <span class="shrink-0 text-[10px] font-bold uppercase text-gray-400">Checks:</span>
            <span
              v-for="rec in cpSelectedList" :key="rec.id"
              class="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-bold text-amber-700 ring-1 ring-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-700/40"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="(rec.status||'').toLowerCase()==='passed' ? 'bg-green-500' : (rec.status||'').toLowerCase()==='warning' ? 'bg-amber-400' : 'bg-red-400'"></span>
              {{ rec.check_name.slice(0, 32) }}{{ rec.check_name.length > 32 ? '…' : '' }}
              <button type="button" @click="cpRemoveId(rec.id)" class="ml-0.5 leading-none text-amber-400 opacity-60 transition hover:text-red-500 hover:opacity-100">×</button>
            </span>
            <button type="button" @click="cpClearAll()" class="shrink-0 text-[10px] text-gray-400 hover:text-red-400">Clear</button>
          </div>

          <!-- ── Normal input form ───────────────────────────────────── -->
          <div class="px-3 py-3 sm:px-4">
            <!-- Context attach buttons row (review agent only) -->
            <div v-if="selectedAgent === 'review'" class="mb-2 flex flex-wrap items-center gap-2">
              <!-- Guidelines chip -->
              <button
                type="button"
                @click="glPickerOpen = !glPickerOpen; cpPickerOpen = false"
                class="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[10px] font-bold transition"
                :class="glSelectedKeys.size > 0
                  ? 'border-blue-300 bg-blue-50 text-blue-600 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'"
              >
                <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                Guidelines
                <span v-if="glSelectedKeys.size > 0" class="ml-0.5 rounded-full bg-blue-600 px-1.5 py-px text-[9px] font-black text-white">{{ glSelectedKeys.size }}</span>
              </button>
              <span v-if="availableGlSections.length === 0" class="text-[10px] text-gray-400">
                (no guideline data — add via Guidelines tab)
              </span>

              <!-- Compliance chip -->
              <button
                type="button"
                @click="cpPickerOpen = !cpPickerOpen; glPickerOpen = false"
                class="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[10px] font-bold transition"
                :class="cpSelectedIds.size > 0
                  ? 'border-amber-300 bg-amber-50 text-amber-600 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                  : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-amber-300 hover:bg-amber-50 hover:text-amber-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'"
              >
                <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                Compliance
                <span v-if="cpSelectedIds.size > 0" class="ml-0.5 rounded-full bg-amber-500 px-1.5 py-px text-[9px] font-black text-white">{{ cpSelectedIds.size }}</span>
              </button>
              <span v-if="complianceRecordsForVersion.length === 0 && cpPickerOpen" class="text-[10px] text-gray-400">
                (no compliance data yet)
              </span>
            </div>

            <!-- ── Draft agent: review items picker ──────────────────── -->
            <div v-if="selectedAgent === 'draft'" class="mb-2">
              <div class="flex items-center gap-2 mb-1.5">
                <button
                  type="button"
                  @click="draftItemPickerOpen = !draftItemPickerOpen"
                  class="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[10px] font-bold transition"
                  :class="selectedDraftItemIds.size > 0
                    ? 'border-violet-300 bg-violet-50 text-violet-700 dark:border-violet-700 dark:bg-violet-900/30 dark:text-violet-300'
                    : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-violet-300 hover:bg-violet-50 hover:text-violet-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'"
                >
                  <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
                  Review items
                  <span v-if="selectedDraftItemIds.size > 0" class="rounded-full px-1.5 py-px text-[9px] font-black text-white" style="background:var(--clm-brand)">{{ selectedDraftItemIds.size }}</span>
                </button>
                <span v-if="contractReviewItems.length === 0" class="text-[10px] text-gray-400">(no saved review items yet)</span>
              </div>

              <!-- picker dropdown -->
              <Transition enter-active-class="transition duration-100 ease-out" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-75 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
                <div v-if="draftItemPickerOpen && contractReviewItems.length > 0" class="mb-2 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-600 dark:bg-gray-800">
                  <div class="flex items-center justify-between border-b border-gray-100 px-3 py-2 dark:border-gray-700">
                    <p class="text-[11px] font-black uppercase tracking-wide text-gray-500 dark:text-gray-400">Select review items to include in redraft</p>
                    <button type="button" @click="draftItemPickerOpen = false" class="text-gray-400 hover:text-gray-600">
                      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                  </div>
                <div class="flex items-center justify-between border-b border-gray-100 px-3 py-2 dark:border-gray-700">
                  <button
                    type="button"
                    class="text-[10px] font-semibold text-violet-600 hover:text-violet-800 dark:text-violet-300 dark:hover:text-violet-200"
                    @click="selectAllDraftReviewItems"
                  >
                    {{ selectedDraftItemIds.size === contractReviewItems.length ? 'Clear all' : 'Select all' }}
                  </button>
                  <span class="text-[10px] text-gray-400">{{ contractReviewItems.length }} total</span>
                </div>
                  <div class="max-h-52 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700">
                    <label
                      v-for="item in contractReviewItems" :key="item.id"
                      class="flex cursor-pointer items-start gap-2.5 px-3 py-2 hover:bg-violet-50 dark:hover:bg-gray-700 transition"
                    >
                      <input type="checkbox" :checked="selectedDraftItemIds.has(item.id)" @change="toggleDraftItem(item.id)" class="mt-0.5 h-3.5 w-3.5 rounded accent-violet-600 shrink-0" />
                      <div class="min-w-0 flex-1">
                        <p class="text-[11px] font-semibold text-gray-800 dark:text-gray-100 truncate">{{ item.title || 'Review finding' }}</p>
                        <p class="mt-0.5 text-[10px] text-gray-500 dark:text-gray-400 line-clamp-2">{{ item.content.slice(0, 160) }}{{ item.content.length > 160 ? '…' : '' }}</p>
                      </div>
                      <span v-if="item.severity" class="shrink-0 rounded px-1.5 py-px text-[8px] font-bold uppercase" :class="item.severity === 'critical' ? 'bg-red-100 text-red-700' : item.severity === 'moderate' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'">{{ item.severity }}</span>
                      <button type="button" @click.prevent="deleteReviewItem(item.id)" class="shrink-0 text-gray-300 hover:text-red-400 transition" title="Delete">
                        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                      </button>
                    </label>
                  </div>
                  <div class="flex items-center justify-between border-t border-gray-100 px-3 py-2 dark:border-gray-700">
                    <button type="button" @click="selectedDraftItemIds = new Set()" class="text-[10px] font-semibold text-gray-400 hover:text-gray-600">Clear all</button>
                <div class="flex items-center gap-1.5">
                  <button
                    type="button"
                    class="rounded-lg bg-gray-900 px-3 py-1.5 text-[11px] font-bold text-white shadow-sm hover:bg-black disabled:opacity-50"
                    :disabled="selectedDraftItemIds.size === 0 || draftTyping"
                    @click="runDraftSelectedItemsNow"
                  >
                    Run ({{ selectedDraftItemIds.size }} selected)
                  </button>
                  <button type="button" @click="draftItemPickerOpen = false" class="rounded-lg px-3 py-1.5 text-[11px] font-bold text-white shadow-sm" style="background:var(--clm-brand)">Done ({{ selectedDraftItemIds.size }} selected)</button>
                </div>
                  </div>
                </div>
              </Transition>

              <!-- selected items strip -->
              <div v-if="selectedDraftItemIds.size > 0" class="flex flex-wrap items-center gap-1.5">
                <span class="shrink-0 text-[10px] font-bold uppercase text-gray-400">Items:</span>
                <span
                  v-for="item in contractReviewItems.filter(i => selectedDraftItemIds.has(i.id))" :key="item.id"
                  class="inline-flex items-center gap-1 rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-700 ring-1 ring-violet-200 dark:bg-violet-900/30 dark:text-violet-300 dark:ring-violet-700/40"
                >
                  {{ (item.title || 'Review finding').slice(0, 30) }}
                  <button type="button" @click="selectedDraftItemIds.delete(item.id); selectedDraftItemIds = new Set(selectedDraftItemIds)" class="text-violet-400 hover:text-red-500">×</button>
                </span>
              </div>
            </div>

            <form @submit.prevent="sendMessage" class="flex gap-2">
              <input
                v-model="userInput"
                type="text"
                :placeholder="
                  mainChatInputLocked && selectedAgent === 'compare'
                    ? 'Comparison in progress…'
                    : mainChatInputLocked && selectedAgent === 'draft'
                      ? 'Draft in progress — your .docx will appear shortly…'
                      : mainChatInputLocked && selectedAgent === 'review'
                        ? 'Review in progress…'
                        : selectedAgent === 'review'
                          ? cpSelectedIds.size > 0 && glSelectedKeys.size > 0
                            ? 'Add a question (optional — guideline + compliance included)…'
                            : cpSelectedIds.size > 0
                              ? 'Add a question (optional — compliance context included)…'
                              : glSelectedKeys.size > 0
                                ? 'Add a question (optional — guideline context included)…'
                                : 'Your question (required)…'
                          : selectedAgent === 'draft'
                            ? 'Drafting request (optional scoring context above)…'
                            : selectedAgent === 'compare'
                              ? 'What to compare? (optional — defaults to a full summary)…'
                              : 'Ask ' + getAgentName(selectedAgent) + '...'
                "
                :disabled="mainChatInputLocked"
                :title="mainChatInputLocked ? 'Wait for the assistant to finish this reply.' : undefined"
                class="clm-agent-input flex-1 dark:bg-gray-800 dark:text-white dark:border-gray-600 placeholder:text-gray-400 dark:placeholder:text-gray-500 disabled:cursor-not-allowed disabled:opacity-60"
                @focus="onMainChatInputPointer"
                @mousedown="onMainChatInputPointer"
              >
              <button
                type="submit"
                :disabled="mainChatSendDisabled"
                class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-blue-600 text-white transition hover:bg-blue-700 disabled:opacity-50 shadow-lg shadow-blue-500/30"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
              </button>
            </form>
          </div>
        </div>
          </div>
        </div>
      </div>
      </Teleport>
    </div>
  </div>

  <!-- Document preview: right slide-over (Teleport avoids clipping by main scroll) -->
  <Teleport to="body">
    <template v-if="contract && activeTab !== 'graph'">
      <div
        v-show="documentPreviewDrawerOpen"
        class="fixed inset-0 z-[118] bg-slate-950/25 backdrop-blur-[1px] transition-opacity lg:hidden"
        aria-hidden="true"
        @click="documentPreviewDrawerOpen = false"
      />
      <button
        v-show="!documentPreviewDrawerOpen"
        type="button"
        :style="documentPreviewPeekStyle"
        class="fixed top-[calc(50%+3.5rem)] z-[119] flex -translate-y-1/2 items-center gap-2 rounded-l-xl border border-r-0 border-[var(--clm-border)] bg-[var(--clm-bg-surface)] py-2.5 pl-2 pr-3 text-[10px] font-black uppercase tracking-wider text-[var(--clm-brand)] shadow-lg transition hover:bg-[var(--clm-bg-overlay)] sm:top-[calc(50%+4.5rem)] sm:flex-col sm:gap-1 sm:px-2.5 sm:py-3.5 sm:pr-2.5 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface-elevated)]"
        title="Open document preview"
        @click="documentPreviewDrawerOpen = true"
      >
        <svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        <span class="whitespace-nowrap leading-tight sm:whitespace-normal sm:text-center sm:leading-snug">Preview</span>
      </button>
      <div
        :style="documentPreviewDrawerShellStyle"
        class="fixed right-0 top-16 z-[120] flex h-[calc(100dvh-4rem)] max-h-[calc(100dvh-4rem)] max-w-[100dvw] flex-col border-l border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-[-12px_0_40px_-12px_rgba(15,76,129,0.18)] transition-[transform,width] duration-300 ease-out dark:bg-[var(--clm-bg-page)] sm:top-24 sm:h-[calc(100dvh-6rem)] sm:max-h-[calc(100dvh-6rem)]"
        :class="documentPreviewDrawerOpen ? 'translate-x-0' : 'translate-x-full pointer-events-none'"
      >
        <div
          class="flex h-full min-h-0 min-w-0 flex-1 flex-row overflow-hidden sm:rounded-tl-2xl"
        >
          <div class="flex h-full min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div class="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] px-3 py-2.5 sm:gap-x-4 sm:px-4 sm:py-3">
            <div class="flex min-w-0 flex-wrap items-center gap-2 min-[480px]:gap-3 sm:gap-4">
              <span class="text-xs font-bold text-[var(--clm-text)] sm:text-sm">Document Preview</span>
              <div v-if="loading" class="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-[var(--clm-brand)] border-t-transparent"></div>
              <div class="flex rounded-lg bg-[var(--clm-bg-page)] p-0.5 ring-1 ring-[var(--clm-border)]">
                <button type="button" class="rounded-md px-2 py-1 text-[10px] font-bold transition sm:px-3" :class="!showSigned ? 'bg-[var(--clm-bg-surface-elevated)] text-[var(--clm-brand)] shadow-sm' : 'text-[var(--clm-text-muted)]'" @click="showSigned = false">ORIGINAL</button>
                <button
                  type="button"
                  class="rounded-md px-2 py-1 text-[10px] font-bold transition disabled:opacity-30 sm:px-3"
                  :disabled="!latestVersion?.signed_file_path && !contract?.signed_file_path"
                  :class="showSigned ? 'bg-[var(--clm-bg-surface-elevated)] text-[var(--clm-success)] shadow-sm' : 'text-[var(--clm-text-muted)]'"
                  @click="showSigned = true"
                >SIGNED</button>
              </div>
            </div>
            <div class="flex w-full min-w-0 shrink-0 flex-wrap items-center justify-end gap-x-2 gap-y-2 text-[var(--clm-text-muted)] min-[480px]:w-auto sm:gap-x-4">
              <div v-if="!isDocxPreview" class="flex items-center gap-0.5 min-[420px]:gap-1">
                <button type="button" class="rounded-lg p-1 transition hover:bg-[var(--clm-bg-surface-elevated)] hover:text-[var(--clm-text)] disabled:opacity-30" :disabled="currentPage <= 1" @click="prevPage">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                </button>
                <span class="text-xs font-medium text-[var(--clm-text-muted)]">Page {{ currentPage }} / {{ totalPages }}</span>
                <button type="button" class="rounded-lg p-1 transition hover:bg-[var(--clm-bg-surface-elevated)] hover:text-[var(--clm-text)] disabled:opacity-30" :disabled="currentPage >= totalPages" @click="nextPage">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </button>
              </div>
              <span v-if="isDocxPreview" class="rounded-full bg-blue-50 px-2.5 py-1 text-[10px] font-bold text-blue-600 ring-1 ring-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:ring-blue-800">DOCX</span>
              <button
                v-if="!isDocxPreview"
                type="button"
                class="grid h-9 w-9 place-items-center rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-page)] text-[var(--clm-text-muted)] transition hover:bg-[var(--clm-bg-surface-elevated)] hover:text-[var(--clm-text)]"
                :title="documentPreviewCanvasVisible ? 'Hide document page' : 'Show document page'"
                :aria-pressed="documentPreviewCanvasVisible"
                @click="documentPreviewCanvasVisible = !documentPreviewCanvasVisible"
              >
                <svg v-if="documentPreviewCanvasVisible" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                </svg>
                <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
              </button>
              <button
                type="button"
                class="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-page)] px-2 py-1 text-[10px] font-bold text-[var(--clm-text-muted)] transition hover:border-[var(--clm-brand)] hover:text-[var(--clm-brand)] disabled:cursor-not-allowed disabled:opacity-40"
                :class="contractPreviewChunksDrawerOpen ? 'border-[var(--clm-brand)] text-[var(--clm-brand)]' : ''"
                title="Document chunks (same CLM indexing as Document Drive)"
                :disabled="!primaryVersionId"
                @click="toggleContractPreviewChunksDrawer"
              >
                <svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
                <span class="hidden min-[380px]:inline">Chunks</span>
                <span v-if="contractPreviewChunks.length" class="rounded-full bg-[var(--clm-brand)]/15 px-1.5 py-px text-[9px] font-black text-[var(--clm-brand)]">{{ contractPreviewChunks.length }}</span>
              </button>
              <button
                type="button"
                class="grid h-9 w-9 place-items-center rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-page)] text-[var(--clm-text-muted)] transition hover:bg-[var(--clm-bg-surface-elevated)] hover:text-[var(--clm-text)]"
                title="Hide preview panel"
                @click="documentPreviewDrawerOpen = false"
              >
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>
          <div id="pdf-scroll-container" class="flex min-h-0 flex-1 flex-basis-0 flex-col justify-start overflow-auto bg-[var(--clm-bg-page)] p-3 min-[480px]:p-4 lg:p-6">
            <!-- DOCX preview: render via mammoth -->
            <template v-if="isDocxPreview && docxRendering">
              <div class="flex flex-1 items-center justify-center">
                <div class="text-center">
                  <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                  <p class="text-sm text-gray-400">Rendering document...</p>
                </div>
              </div>
            </template>
            <template v-else-if="isDocxPreview && docxPreviewUrl">
              <iframe
                ref="docxPreviewIframeRef"
                :src="docxPreviewUrl"
                class="h-full w-full min-h-0 rounded-lg border border-[var(--clm-border)] bg-white shadow-xl shadow-black/10"
                title="Document preview"
                sandbox="allow-same-origin allow-scripts"
                @load="onContractDocxIframeLoad"
              />
            </template>
            <!-- DOCX loaded but render failed (file missing or corrupt) -->
            <template v-else-if="isDocxPreview && docxRenderFailed">
              <div class="flex flex-1 items-center justify-center">
                <div class="text-center space-y-3">
                  <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
                    <svg class="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                  </div>
                  <p class="text-sm font-semibold text-[var(--clm-text)]">Document could not be rendered</p>
                  <p class="text-xs text-[var(--clm-text-muted)]">The file may be missing or corrupt on the server.</p>
                  <button @click="loadPdf()" class="mt-1 rounded-lg border border-[var(--clm-border)] px-3 py-1.5 text-xs font-medium text-[var(--clm-text)] hover:bg-[var(--clm-bg-overlay)] transition">
                    Retry
                  </button>
                </div>
              </div>
            </template>
            <template v-else-if="documentPreviewCanvasVisible">
              <div
                id="pdf-container"
                class="relative flex h-full min-h-0 w-full rounded-lg shadow-xl shadow-black/15 ring-1 ring-[var(--clm-border)] dark:shadow-black/40"
              >
                <canvas id="pdf-canvas" class="block rounded-lg bg-white"></canvas>
                <div
                  v-for="field in filteredFields"
                  :key="field.id"
                  class="absolute flex flex-col items-center justify-center overflow-hidden border-2 border-dashed p-1 transition-all"
                  :class="field.is_signed ? 'border-green-500 bg-green-500/5' : 'border-slate-400/60 bg-slate-900/[0.04]'"
                  :style="getFieldStyle(field)"
                >
                  <template v-if="field.is_signed">
                    <div class="absolute -top-4 left-0 z-10 whitespace-nowrap rounded bg-slate-900/85 px-1.5 py-0.5 text-[8px] font-bold text-white shadow-sm">
                      {{ getSignerName(field) }}
                    </div>
                    <img v-if="field.field_type === 'signature'" :src="field.value" class="max-h-full max-w-full object-contain" />
                    <span v-else class="w-full break-words px-1 text-center text-[10px] font-bold text-green-700">{{ field.value }}</span>
                  </template>
                  <template v-else>
                    <div class="absolute -top-4 left-0 z-10 whitespace-nowrap rounded bg-slate-900/85 px-1.5 py-0.5 text-[8px] font-bold text-white/90 shadow-sm">
                      {{ getSignerName(field) }}
                    </div>
                    <span class="w-full px-1 text-center text-[8px] font-bold uppercase text-slate-500">{{ field.field_type }}</span>
                  </template>
                </div>
              </div>
            </template>
            <div
              v-else-if="!isDocxPreview"
              class="flex w-full max-w-sm flex-col items-center justify-center gap-4 self-center py-16 text-center text-sm text-[var(--clm-text-muted)]"
            >
              <p>Document page is hidden.</p>
              <button
                type="button"
                class="rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-surface-elevated)] px-4 py-2 text-xs font-bold text-[var(--clm-brand)] shadow-sm transition hover:bg-[var(--clm-bg-overlay)]"
                @click="documentPreviewCanvasVisible = true"
              >
                Show document page
              </button>
            </div>
          </div>
          </div>

          <aside
            v-if="contractPreviewChunksDrawerOpen"
            class="flex h-full min-h-0 w-[min(100vw,320px)] shrink-0 flex-col border-l border-[var(--clm-border)] bg-[var(--clm-bg-overlay)] sm:w-[360px]"
            :style="{ width: Math.min(contractPreviewChunksDrawerWidth, 420) + 'px' }"
          >
            <div class="flex items-start justify-between gap-2 border-b border-[var(--clm-border)] px-3 py-2.5">
              <div class="min-w-0">
                <p class="text-[11px] font-bold text-[var(--clm-text)]">Document chunks</p>
                <p class="text-[10px] text-[var(--clm-text-muted)]">{{ contractPreviewChunks.length }} section{{ contractPreviewChunks.length !== 1 ? 's' : '' }} · CLM indexing</p>
              </div>
              <button type="button" class="rounded-lg p-1 text-[var(--clm-text-muted)] hover:bg-[var(--clm-bg-surface-elevated)] hover:text-[var(--clm-text)]" title="Close chunks" @click="contractPreviewChunksDrawerOpen = false">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
            <div class="min-h-0 flex-1 overflow-y-auto px-2 py-2">
              <div v-if="contractChunksLoading" class="flex flex-col items-center justify-center gap-2 py-10 text-[11px] text-[var(--clm-text-muted)]">
                <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--clm-brand)] border-t-transparent"></div>
                Loading chunks…
              </div>
              <p v-else-if="!primaryVersionId" class="px-2 py-6 text-center text-[11px] text-[var(--clm-text-muted)]">Select a document version to load chunks.</p>
              <p v-else-if="!contractPreviewChunks.length" class="px-2 py-6 text-center text-[11px] text-[var(--clm-text-muted)]">No chunks yet — wait for indexing after upload, or open the file once.</p>
              <div v-else class="space-y-1.5">
                <div
                  v-for="ch in contractPreviewChunks"
                  :key="ch.id"
                  :data-chunk-card-id="ch.id"
                  class="rounded-lg border border-transparent px-2 py-1.5 transition hover:bg-[var(--clm-bg-surface)]"
                  :class="contractActiveChunkId === ch.id ? 'border-[var(--clm-brand)]/40 bg-[var(--clm-brand)]/5' : ''"
                >
                  <div class="flex items-start gap-2">
                    <span class="shrink-0 text-[10px] font-black text-[var(--clm-brand)]">#{{ ch.chunk_index + 1 }}</span>
                    <p class="min-w-0 flex-1 text-[10px] leading-snug text-[var(--clm-text)]">{{ (ch.content || '').slice(0, 100) }}{{ (ch.content || '').length > 100 ? '…' : '' }}</p>
                    <button
                      type="button"
                      class="shrink-0 rounded p-0.5 text-[var(--clm-text-muted)] hover:text-[var(--clm-brand)]"
                      title="Locate in preview"
                      @click="scrollContractChunkToPreview(ch)"
                    >
                      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </template>
  </Teleport>

  <!-- Complaint Selection Modal -->
  <div v-if="showComplaintModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
    <div class="bg-white dark:bg-gray-800 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
      <div class="p-4 border-b dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900">
        <h3 class="font-bold text-gray-900 dark:text-white uppercase text-xs tracking-widest">Select Complaints</h3>
        <button @click="showComplaintModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="p-4 max-h-[400px] overflow-y-auto">
        <div v-if="complaintLibrary.length === 0" class="text-center py-8 text-gray-400 text-sm">No complaints found in database</div>
        <div v-for="comp in complaintLibrary" :key="comp.id" 
             class="mb-2 rounded-xl border overflow-hidden transition-all"
             :class="isComplaintSelected(comp.id) ? 'border-blue-500' : 'border-gray-100 dark:border-gray-700'">
          <div @click="comp.showDetails = !comp.showDetails" class="p-3 flex items-center gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50">
            <div @click.stop="toggleComplaintSelection(comp)" class="w-5 h-5 rounded border flex items-center justify-center shrink-0"
                 :class="isComplaintSelected(comp.id) ? 'bg-blue-600 border-blue-600' : 'border-gray-300 dark:border-gray-600'">
              <svg v-if="isComplaintSelected(comp.id)" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            </div>
            <div class="flex-1">
              <div class="text-xs font-bold dark:text-white">{{ comp.check_name }}</div>
            </div>
            <svg class="w-3 h-3 transition-transform text-gray-400" :class="{ 'rotate-180': comp.showDetails }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </div>
          <div v-if="comp.showDetails" class="px-3 pb-3 pt-0 text-[10px] text-gray-500 dark:text-gray-400 bg-gray-50/50 dark:bg-gray-900/30">
            <div class="pt-2 border-t border-gray-100 dark:border-gray-700 whitespace-pre-wrap">
              {{ comp.findings }}
            </div>
          </div>
        </div>
      </div>
      <div class="p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex gap-3">
        <button @click="showComplaintModal = false" class="flex-1 py-2 text-xs font-bold text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition">CANCEL</button>
        <button @click="applySelectedComplaints" :disabled="selectedComplaints.length === 0" class="flex-1 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl hover:bg-blue-700 transition disabled:opacity-50 shadow-lg shadow-blue-500/30">
          APPLY ({{ selectedComplaints.length }})
        </button>
      </div>
    </div>
  </div>
  <!-- Add Signer Modal -->
  <div v-if="showAddSignerModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="showAddSignerModal = false">
    <div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-900 shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between border-b border-gray-100 dark:border-gray-700 px-5 py-3.5">
        <h3 class="text-xs font-black uppercase tracking-widest text-gray-800 dark:text-white">Add Signer — v{{ selectedVersion?.version_number }}</h3>
        <button @click="showAddSignerModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="p-5 space-y-4">
        <!-- Search existing master signers -->
        <div>
          <label class="block text-[10px] font-bold uppercase text-gray-500 dark:text-gray-400 mb-1.5">Search existing signers</label>
          <input
            v-model="signerSearch"
            @input="searchMasterSigners"
            type="text"
            placeholder="Name or email…"
            class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:border-[var(--clm-brand)] focus:outline-none"
          />
          <!-- results list -->
          <div v-if="masterSignerResults.length" class="mt-1.5 max-h-36 overflow-y-auto rounded-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
            <button
              v-for="ms in masterSignerResults"
              :key="ms.id"
              type="button"
              class="flex w-full items-center gap-2.5 px-3 py-2 text-left transition hover:bg-gray-50 dark:hover:bg-gray-700"
              @click="selectMasterSigner(ms)"
            >
              <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--clm-brand)]/10 text-[10px] font-bold text-[var(--clm-brand)]">{{ ms.name?.charAt(0) }}</div>
              <div class="min-w-0 flex-1">
                <p class="truncate text-[11px] font-semibold text-gray-900 dark:text-white">{{ ms.name }}</p>
                <p class="truncate text-[10px] text-gray-400">{{ ms.email }}<span v-if="ms.organization"> · {{ ms.organization }}</span></p>
              </div>
            </button>
          </div>
          <p v-else-if="signerSearch.length > 1 && !signerSearchLoading" class="mt-1 text-[10px] text-gray-400">No existing signers found.</p>
        </div>

        <!-- Divider -->
        <div class="flex items-center gap-3">
          <div class="flex-1 border-t border-gray-100 dark:border-gray-700"></div>
          <span class="text-[10px] font-bold uppercase text-gray-400">or create new</span>
          <div class="flex-1 border-t border-gray-100 dark:border-gray-700"></div>
        </div>

        <!-- New signer form -->
        <div class="space-y-2.5">
          <div>
            <label class="block text-[10px] font-bold uppercase text-gray-500 dark:text-gray-400 mb-1">Name *</label>
            <input v-model="newSignerForm.name" type="text" placeholder="Full name" class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:border-[var(--clm-brand)] focus:outline-none" />
          </div>
          <div>
            <label class="block text-[10px] font-bold uppercase text-gray-500 dark:text-gray-400 mb-1">Email *</label>
            <input v-model="newSignerForm.email" type="email" placeholder="email@example.com" class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:border-[var(--clm-brand)] focus:outline-none" />
          </div>
          <div>
            <label class="block text-[10px] font-bold uppercase text-gray-500 dark:text-gray-400 mb-1">Organization</label>
            <input v-model="newSignerForm.organization" type="text" placeholder="Company / department" class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:border-[var(--clm-brand)] focus:outline-none" />
          </div>
        </div>
      </div>

      <div class="flex gap-2 border-t border-gray-100 dark:border-gray-700 px-5 py-3.5">
        <button type="button" @click="showAddSignerModal = false" class="flex-1 rounded-xl border border-gray-200 dark:border-gray-700 py-2 text-xs font-bold text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition uppercase">Cancel</button>
        <button
          type="button"
          :disabled="isAddingSignerLoading || (!newSignerForm.name.trim() || !newSignerForm.email.trim())"
          @click="createAndAddSigner"
          class="flex-1 rounded-xl bg-[var(--clm-brand)] py-2 text-xs font-bold text-white transition hover:bg-[var(--clm-brand-strong)] disabled:opacity-50"
        >
          <span v-if="isAddingSignerLoading">Adding…</span>
          <span v-else>Add Signer</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Milestone Creation Modal -->
  <div v-if="showMilestoneModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
    <div class="bg-white dark:bg-gray-800 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
      <div class="p-4 border-b dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900">
        <h3 class="font-bold text-gray-900 dark:text-white uppercase text-xs tracking-widest">Add Milestone</h3>
        <button @click="showMilestoneModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <form @submit.prevent="addMilestone" class="p-6 space-y-4">
        <div>
          <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Milestone Title</label>
          <input v-model="newMilestone.title" type="text" required placeholder="e.g. Initial Delivery" class="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
        </div>
        <div>
          <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Description</label>
          <textarea v-model="newMilestone.description" rows="3" placeholder="Describe the milestone expectations..." class="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"></textarea>
        </div>
        <div>
          <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Due Date</label>
          <input v-model="newMilestone.due_date" type="date" required class="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
        </div>
        <div class="pt-2 flex gap-3">
          <button type="button" @click="showMilestoneModal = false" class="flex-1 py-2 text-xs font-bold text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition uppercase">Cancel</button>
          <button type="submit" :disabled="isSubmittingMilestone" class="flex-1 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl hover:bg-blue-700 transition disabled:opacity-50 shadow-lg shadow-blue-500/30 uppercase">
            {{ isSubmittingMilestone ? 'Saving...' : 'Add Milestone' }}
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- DOCX Editor Modal -->
  <DocxEditorModal
    v-model="docxEditorOpen"
    :docx-b64="docxEditorB64"
    :filename="docxEditorFilename"
    :contract-id="contractId"
    @saved="reloadContract"
  />

  <!-- Version Drive Picker Modal -->
  <Teleport to="body">
    <Transition name="vdp-fade">
      <div v-if="showVersionDrivePicker" class="fixed inset-0 z-[9998] bg-black/40 backdrop-blur-[2px]" @click="showVersionDrivePicker = false"></div>
    </Transition>
    <Transition name="vdp-scale">
      <div v-if="showVersionDrivePicker" class="fixed inset-0 z-[9999] flex items-center justify-center p-6">
        <div class="vdp-modal" @click.stop>
          <div class="flex items-center justify-between px-5 py-3.5 border-b border-[var(--clm-border)]">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-xl bg-blue-50 dark:bg-blue-900/40 flex items-center justify-center">
                <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
              </div>
              <div>
                <h3 class="text-sm font-bold text-[var(--clm-text)]">Add Version from Drive</h3>
                <p class="text-[11px] text-gray-400">Choose a PDF or DOCX file</p>
              </div>
            </div>
            <button @click="showVersionDrivePicker = false" class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="flex items-center gap-2 px-5 py-2.5 bg-[var(--clm-bg-overlay)] border-b border-[var(--clm-border)]">
            <label class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Drive</label>
            <select v-model="vdpSelectedDriveId" class="flex-1 px-2.5 py-1.5 border border-[var(--clm-border)] rounded-lg bg-[var(--clm-bg-surface-elevated)] text-[12px] text-[var(--clm-text)] outline-none" @change="vdpOnDriveChange">
              <option :value="null" disabled>Select a drive...</option>
              <option v-for="d in vdpDrives" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="vdp-body">
            <div class="vdp-folder-pane">
              <div v-if="vdpFoldersLoading" class="p-4 text-center"><div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div></div>
              <div v-else-if="!vdpFolders.length" class="p-4 text-center text-[11px] text-gray-400">No folders</div>
              <div v-else class="py-1.5">
                <template v-for="item in vdpFlatFolders" :key="item.folder.id">
                  <button class="vdp-folder-item" :class="vdpActiveFolderId === item.folder.id ? 'vdp-folder-active' : ''" :style="{paddingLeft:(10+item.depth*16)+'px'}" @click="vdpSelectFolder(item.folder)">
                    <button v-if="item.hasChildren" @click.stop="vdpToggleExpand(item.folder.id)" class="w-[14px] h-[14px] flex items-center justify-center flex-shrink-0 rounded text-gray-400"><svg class="w-2.5 h-2.5 transition-transform duration-150" :class="item.isExpanded?'rotate-90':''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg></button>
                    <span v-else class="w-[14px] flex-shrink-0"></span>
                    <svg v-if="vdpActiveFolderId===item.folder.id" class="w-[14px] h-[14px] text-blue-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/></svg>
                    <svg v-else class="w-[14px] h-[14px] text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                    <span class="text-[11px] font-medium truncate">{{ item.folder.name }}</span>
                    <span class="text-[10px] text-gray-400 ml-auto flex-shrink-0">{{ vdpFolderFileCount(item.folder) }}</span>
                  </button>
                </template>
              </div>
            </div>
            <div class="vdp-file-pane">
              <div class="relative px-3 py-2.5 border-b border-[var(--clm-border)]/50">
                <svg class="w-3.5 h-3.5 text-gray-400 absolute left-6 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/></svg>
                <input v-model="vdpFileSearch" type="text" placeholder="Search files..." class="w-full pl-7 pr-3 py-1.5 border border-[var(--clm-border)] rounded-lg bg-[var(--clm-bg-overlay)] text-[12px] text-[var(--clm-text)] outline-none focus:border-blue-400" />
              </div>
              <div v-if="!vdpActiveFolderId" class="flex-1 flex items-center justify-center p-8 text-[11px] text-gray-400">Select a folder</div>
              <div v-else-if="vdpFilesLoading" class="flex-1 flex items-center justify-center p-8"><div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>
              <div v-else-if="!vdpFilteredFiles.length" class="flex-1 flex items-center justify-center p-8 text-[11px] text-gray-400">No matching PDF/DOCX files</div>
              <div v-else class="flex-1 overflow-y-auto p-1.5">
                <button v-for="file in vdpFilteredFiles" :key="file.id" class="vdp-file-row" :class="vdpSelectedFileId===file.id?'vdp-file-selected':''" @click="vdpSelectedFileId=file.id" @dblclick="confirmVersionDrivePick">
                  <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" :class="vdpFileIconClass(file.content_type)"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg></div>
                  <div class="flex-1 min-w-0"><p class="text-[12px] font-medium text-[var(--clm-text)] truncate">{{ file.original_filename }}</p><p class="text-[10px] text-gray-400 mt-0.5">{{ vdpFormatBytes(file.size_bytes) }} · {{ vdpExtLabel(file.original_filename) }}</p></div>
                  <div v-if="vdpSelectedFileId===file.id" class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg></div>
                </button>
              </div>
            </div>
          </div>
          <div class="flex items-center justify-between gap-3 px-5 py-3 border-t border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]">
            <div class="text-[11px] text-gray-400 flex-1 min-w-0 truncate">
              <template v-if="vdpPickedFileName">Selected: <span class="font-semibold text-[var(--clm-text)]">{{ vdpPickedFileName }}</span></template>
              <template v-else>Pick a file to add as a new version</template>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <button @click="showVersionDrivePicker = false" class="px-3.5 py-1.5 text-[11px] font-medium text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition">Cancel</button>
              <button @click="confirmVersionDrivePick" :disabled="!vdpSelectedFileId||vdpPickLoading" class="px-4 py-1.5 text-[11px] font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition disabled:opacity-40 flex items-center gap-1.5">
                <span v-if="vdpPickLoading" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                {{ vdpPickLoading ? 'Adding...' : 'Add as Version' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { authStore } from '../utils/auth'
import { toast, swalError, swalConfirm } from '../utils/swal.js'
import { startNotifications, stopNotifications, onNotification } from '../utils/notificationSocket.js'
import {
  appendPdfTextLayer,
  locateChunkInPreview,
  chunkTextMatchesInRoot,
  clearHighlights,
  injectHighlightStylesIntoDocument,
  CHUNK_HL_MARK_CLASS,
} from '../utils/chunkTextLocate.js'
import { renderMd } from '../utils/chatMarkdown.js'
import ContractGraphExplorer from '../components/ContractGraphExplorer.vue'
import KnowledgeGraphInsights from '../components/graph/KnowledgeGraphInsights.vue'
import ChatMarkdown from '../components/ChatMarkdown.vue'
import ChatAttachmentCard from '../components/ChatAttachmentCard.vue'
import DocxEditorModal from '../components/DocxEditorModal.vue'
import ContractGuidelinesPanel from '../components/ContractGuidelinesPanel.vue'
import GuidelineAttachmentWidget from '../components/GuidelineAttachmentWidget.vue'
import GuidelineSectionCard from '../components/GuidelineSectionCard.vue'
import DraftRedlineProgress from '../components/DraftRedlineProgress.vue'
import ComparePdfThumb from '../components/ComparePdfThumb.vue'
import WorkingVersionPicker from '../components/WorkingVersionPicker.vue'

let pdfjsLibPromise = null
const loadPdfJsLib = async () => {
  if (!pdfjsLibPromise) {
    pdfjsLibPromise = import('pdfjs-dist')
  }
  const pdfjsLib = await pdfjsLibPromise
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'
  return pdfjsLib
}

const route = useRoute()
const router = useRouter()
const contractId = route.params.id

function goPrepareSignature() {
  const v = selectedVersion.value
  if (contractId == null || contractId === '' || !v?.id) return
  router.push({
    path: `/prepare-signature/${contractId}`,
    query: { version_id: String(v.id) },
  })
}

/** Premium CPWD context pack for Review/Draft WebSockets; persisted per contract in this browser. */
const cpwdCopilotEnabled = ref(true)
function cpwdCopilotStorageKey() {
  return `clm_cpwd_copilot_v1_${String(route.params.id || '')}`
}
function loadCpwdCopilotPref() {
  try {
    const raw = localStorage.getItem(cpwdCopilotStorageKey())
    cpwdCopilotEnabled.value = !(raw === '0' || raw === 'false')
  } catch {
    cpwdCopilotEnabled.value = true
  }
}
watch(
  () => String(route.params.id || ''),
  () => loadCpwdCopilotPref(),
  { immediate: true },
)
watch(cpwdCopilotEnabled, (v) => {
  try {
    localStorage.setItem(cpwdCopilotStorageKey(), v ? '1' : '0')
  } catch {
    /* ignore */
  }
})

const graphExplorerRef = ref(null)
const knowledgeGraphInsightsRef = ref(null)
/** Overview tab: Signers card — focused when contract moves to Signing. */
const overviewSignersSectionRef = ref(null)
/** Non-technical overview vs force-directed explorer. */
const graphViewMode = ref('overview')
const knowledgeGraphReloadKey = ref(0)

// ── DOCX editor modal ──────────────────────────────────────────────────────
const docxEditorOpen    = ref(false)
const docxEditorB64     = ref('')
const docxEditorFilename = ref('document.docx')

function openDocxEditor(att) {
  docxEditorB64.value      = att.data || ''
  docxEditorFilename.value = att.filename || 'document.docx'
  docxEditorOpen.value     = true
}

async function openVersionEditor(version) {
  // Fetch the raw file bytes, base64-encode them, then open the editor
  try {
    const url = `/api/contracts/${contractId}/file?version_id=${version.id}`
    const resp = await axios.get(url, { responseType: 'arraybuffer' })
    const bytes = new Uint8Array(resp.data)
    let binary = ''
    bytes.forEach(b => { binary += String.fromCharCode(b) })
    docxEditorB64.value      = btoa(binary)
    docxEditorFilename.value = `v${version.version_number}_${version.label || 'document'}.docx`
    docxEditorOpen.value     = true
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Could not load file for editing')
  }
}

async function reloadContract() {
  try {
    const response = await axios.get(`/api/contracts/${contractId}`)
    contract.value = response.data
  } catch { /* silent */ }
}

// ── Background-task notification state ──────────────────────────────────────
/** Live background tasks for this contract: { id, type, filename, status } */
const bgTasks = ref([])
/** Map of file_id → { stage: 'chunking'|'processing', filename } for per-version row indicators */
const processingVersions = ref({})
/** file_id → Set of completed post-chunk task bases ('compliance' | 'scoring' | 'graph_build'). */
const _postChunkDoneTypes = {}
const _POST_CHUNK_TASK_BASES = ['compliance', 'scoring', 'graph_build']

function _bgTaskKey(msg) {
  return `${msg.type.replace(/_started|_done|_failed/, '')}-${msg.file_id}`
}

function handleNotification(msg) {
  // route.params.id is always a string; cast both sides before comparing
  if (Number(msg.contract_id) !== Number(contractId)) return

  const key = _bgTaskKey(msg)
  const isStart = msg.type.endsWith('_started')
  const isDone  = msg.type.endsWith('_done')
  const isFail  = msg.type.endsWith('_failed')

  const taskBase = msg.type.replace(/_started|_done|_failed/, '')
  const isPostChunkTask = ['compliance', 'scoring', 'graph_build'].includes(taskBase)

  if (isStart) {
    bgTasks.value = bgTasks.value.filter(t => t.id !== key)
    bgTasks.value.push({ id: key, type: msg.type, filename: msg.filename, status: 'running' })
    if (msg.type.startsWith('chunking')) {
      processingVersions.value = { ...processingVersions.value, [msg.file_id]: { stage: 'chunking', filename: msg.filename } }
    } else if (isPostChunkTask) {
      processingVersions.value = { ...processingVersions.value, [msg.file_id]: { stage: 'processing', filename: msg.filename } }
      // Compliance and scoring start together in parallel; if only compliance WS was received, still show Scoring-tab progress.
      if (msg.type === 'compliance_started' || msg.type === 'scoring_started') {
        scoringBackgroundRunning.value = true
      }
    }
    return
  }

  bgTasks.value = bgTasks.value.map(t =>
    t.id === key ? { ...t, status: isDone ? 'done' : 'failed' } : t
  )

  if (isDone) {
    if (msg.type === 'chunking_done') {
      delete _postChunkDoneTypes[msg.file_id]
      // Parallel tasks (compliance + scoring + graph_build) will start next
      processingVersions.value = { ...processingVersions.value, [msg.file_id]: { stage: 'processing', filename: msg.filename } }
      toast(`Document chunked: ${msg.filename}`)
      reloadContract().then(() => {
        _detectAndShowInitialProcessing()
      })
    } else if (isPostChunkTask) {
      const fid = msg.file_id
      if (!_postChunkDoneTypes[fid]) _postChunkDoneTypes[fid] = new Set()
      _postChunkDoneTypes[fid].add(taskBase)
      if (_POST_CHUNK_TASK_BASES.every((t) => _postChunkDoneTypes[fid].has(t))) {
        const next = { ...processingVersions.value }
        delete next[fid]
        processingVersions.value = next
        delete _postChunkDoneTypes[fid]
        scoringBackgroundRunning.value = false
      }
      if (msg.type === 'compliance_done') {
        toast(`Compliance checks complete: ${msg.filename}`)
        reloadContract()
      } else if (msg.type === 'scoring_done') {
        scoringBackgroundRunning.value = false
        toast(`Scoring complete: ${msg.filename}`)
        fetchScoring()
        reloadContract()
      } else if (msg.type === 'graph_build_done') {
        toast(`Knowledge graph built: ${msg.filename}`)
        knowledgeGraphReloadKey.value += 1
        knowledgeGraphInsightsRef.value?.reload?.()
        reloadContract()
      }
    }
  } else if (isFail) {
    if (isPostChunkTask) {
      delete _postChunkDoneTypes[msg.file_id]
      const next = { ...processingVersions.value }
      delete next[msg.file_id]
      processingVersions.value = next
      if (taskBase === 'scoring') {
        scoringBackgroundRunning.value = false
      }
    } else {
      // chunking failed — clear indicator immediately
      const next = { ...processingVersions.value }
      delete next[msg.file_id]
      processingVersions.value = next
    }
    swalError(msg.message || 'Background processing failed.')
  }

  // Auto-dismiss activity banner entry after 4 s
  setTimeout(() => {
    bgTasks.value = bgTasks.value.filter(t => t.id !== key)
  }, 4000)
}

const _INITIAL_PROCESSING_MAX_AGE_MS = 10 * 60 * 1000

/**
 * After creating a contract (or missing early WebSocket events), infer in-flight work so the
 * History row + activity banner match an in-session upload. Chunking is separate; post-chunk work
 * runs compliance, scoring, and graph in parallel — do not hide the widget as soon as compliance
 * rows exist, or scoring/graph would appear "stuck" with no indicator.
 */
async function _detectAndShowInitialProcessing() {
  const c = contract.value
  if (!c?.document_versions?.length) return

  const latest =
    c.document_versions.find((v) => v.is_latest) ||
    c.document_versions[c.document_versions.length - 1]
  const fid = latest?.file_id
  if (fid == null) return

  const createdMs = latest.created_at ? new Date(latest.created_at).getTime() : 0
  if (!createdMs || Date.now() - createdMs > _INITIAL_PROCESSING_MAX_AGE_MS) return

  const records = Array.isArray(c.compliance_records) ? c.compliance_records : []
  const complianceForLatest = records.filter(
    (r) =>
      String(r.record_type || 'compliance') === 'compliance' &&
      (r.document_version_id == null || Number(r.document_version_id) === Number(latest.id)),
  )
  const complianceDone = complianceForLatest.length > 0

  let chunks = []
  try {
    const { data } = await axios.get(`/api/versions/${latest.id}/chunks`)
    chunks = Array.isArray(data) ? data : []
  } catch {
    chunks = []
  }

  const filename = latest.label || 'document'

  if (!chunks.length) {
    scoringBackgroundRunning.value = false
    processingVersions.value = { ...processingVersions.value, [fid]: { stage: 'chunking', filename } }
    const ck = `chunking-${fid}`
    bgTasks.value = bgTasks.value.filter((t) => t.id !== ck)
    bgTasks.value.push({ id: ck, type: 'chunking_started', filename, status: 'running' })
    return
  }

  const [scoringRes, graphRes] = await Promise.allSettled([
    axios.get(`/api/contracts/${c.id}/scoring`, { params: { version_id: latest.id } }),
    axios.get(`/api/contracts/${c.id}/versions/${latest.id}/knowledge-graph`),
  ])

  const scoringDone =
    scoringRes.status === 'fulfilled' && scoringRes.value.data?.result_json != null
  const graphDone = graphRes.status === 'fulfilled'

  if (complianceDone && scoringDone && graphDone) {
    scoringBackgroundRunning.value = false
    return
  }

  processingVersions.value = { ...processingVersions.value, [fid]: { stage: 'processing', filename } }

  const pending = []
  if (!complianceDone) pending.push({ key: `compliance-${fid}`, type: 'compliance_started', filename })
  if (!scoringDone) pending.push({ key: `scoring-${fid}`, type: 'scoring_started', filename })
  if (!graphDone) pending.push({ key: `graph_build-${fid}`, type: 'graph_build_started', filename })

  for (const t of pending) {
    bgTasks.value = bgTasks.value.filter((x) => x.id !== t.key)
    bgTasks.value.push({ id: t.key, type: t.type, filename: t.filename, status: 'running' })
  }

  scoringBackgroundRunning.value = !scoringDone
}

const contract = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const pdfDoc = shallowRef(null)
/** Current PDF.js viewport scale (fit-to-width); signature overlays use field.scale vs this. */
const pdfPageRenderScale = ref(1.5)
const showSigned = ref(false)
/** When the current preview is a DOCX this holds the blob URL for the mammoth-rendered iframe. */
const docxPreviewUrl = ref('')
const docxRendering = ref(false)
/** True when the currently-loaded preview is a DOCX (not PDF). */
const isDocxPreview = ref(false)

let mammothPromise = null
const loadMammoth = () => {
  if (!mammothPromise) mammothPromise = import('mammoth')
  return mammothPromise
}

const DOCX_CSS = 'html,body{background:#fff;color:#1a1a1a;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:24px 32px;max-width:820px;margin:auto;line-height:1.75;font-size:14px}h1,h2,h3,h4,h5,h6{color:#111;margin-top:1.4em}p{margin:0.6em 0}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:6px 10px}a{color:#2563eb}img{max-width:100%;height:auto}'

/** True when a DOCX was attempted but failed to render (file missing or parse error). */
const docxRenderFailed = ref(false)

async function renderDocxFromUrl(fileUrl) {
  if (docxPreviewUrl.value) { URL.revokeObjectURL(docxPreviewUrl.value) }
  docxPreviewUrl.value = ''
  docxRenderFailed.value = false
  docxRendering.value = true
  try {
    const resp = await fetch(fileUrl)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const arrayBuffer = await resp.arrayBuffer()
    const mammoth = await loadMammoth()
    const result = await mammoth.default.convertToHtml({ arrayBuffer })
    const fullHtml = `<html><head><meta charset="utf-8"><style>${DOCX_CSS}</style></head><body>${result.value}</body></html>`
    const blob = new Blob([fullHtml], { type: 'text/html' })
    docxPreviewUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    console.warn('DOCX mammoth render failed:', e)
    docxPreviewUrl.value = ''
    docxRenderFailed.value = true
    throw e   // re-throw so callers can react
  } finally {
    docxRendering.value = false
  }
}

/**
 * Reliably determine whether a version's file is DOCX or PDF.
 * Priority: version.file_type → version.file_path extension → contract.file_type
 */
function resolveFileType(version) {
  const direct = (version?.file_type || '').toLowerCase()
  if (['docx', 'doc', 'pdf'].includes(direct)) return direct

  const pathExt = (version?.file_path || '').split('.').pop().toLowerCase()
  if (['docx', 'doc', 'pdf'].includes(pathExt)) return pathExt

  const contractFt = (contract.value?.file_type || '').toLowerCase()
  if (['docx', 'doc', 'pdf'].includes(contractFt)) return contractFt

  return 'pdf'
}
const activeTab = ref('overview')
const selectedVersionId = ref(null)

/** Persisted per contract in localStorage — primary version for agents, scoring, preview. */
function workingVersionStorageKey() {
  return `clm_contract_${contractId}_working_version_id`
}

function persistWorkingVersionId(vid) {
  if (vid == null) return
  try {
    localStorage.setItem(workingVersionStorageKey(), String(vid))
  } catch (_) {
    /* ignore quota / private mode */
  }
}

function applyWorkingVersionFromStorageOrLatest() {
  const versions = contract.value?.document_versions || []
  if (!versions.length) {
    selectedVersionId.value = null
    return
  }
  let stored = null
  try {
    const raw = localStorage.getItem(workingVersionStorageKey())
    if (raw) stored = parseInt(raw, 10)
  } catch (_) {}
  if (stored != null && !Number.isNaN(stored) && versions.some((v) => v.id === stored)) {
    selectedVersionId.value = stored
    return
  }
  const latest = versions.find((v) => v.is_latest) || versions.at(-1)
  selectedVersionId.value = latest?.id ?? null
  if (latest?.id != null) persistWorkingVersionId(latest.id)
}

const contractTabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'milestones', label: 'Contract Changes' },
  { id: 'cpwd-copilot', label: 'CPWD Copilot', premium: true },
  { id: 'guidelines', label: 'Guidelines' },
  { id: 'compliance', label: 'Compliance' },
  { id: 'history', label: 'History' },
  { id: 'scoring', label: 'Scoring' },
  { id: 'graph', label: 'Graph' },
]

const statusHeroClass = (status) => {
  const s = (status || '').toLowerCase()
  if (s === 'active') {
    return 'border-emerald-200/90 bg-gradient-to-br from-emerald-50 to-emerald-50/30 text-emerald-700 shadow-sm shadow-emerald-900/[0.06] dark:border-emerald-700/50 dark:from-emerald-950/40 dark:to-[var(--clm-bg-surface)] dark:text-emerald-300'
  }
  if (s === 'signing') {
    return 'border-amber-200/90 bg-gradient-to-br from-amber-50 to-amber-50/30 text-amber-800 shadow-sm shadow-amber-900/[0.06] dark:border-amber-700/50 dark:from-amber-950/40 dark:to-[var(--clm-bg-surface)] dark:text-amber-300'
  }
  if (s === 'draft') {
    return 'border-[var(--clm-border)] bg-gradient-to-br from-[var(--clm-bg-overlay)] to-[var(--clm-bg-surface)] text-[var(--clm-text-muted)] shadow-sm dark:from-[var(--clm-bg-overlay)] dark:to-[var(--clm-bg-surface-elevated)] dark:text-[var(--clm-text-muted)]'
  }
  if (s === 'review') {
    return 'border-amber-200/90 bg-gradient-to-br from-amber-50 to-amber-50/20 text-amber-800 shadow-sm dark:border-amber-700/45 dark:from-amber-950/35 dark:to-[var(--clm-bg-surface)] dark:text-amber-200'
  }
  if (s === 'redraft') {
    return 'border-orange-200/90 bg-gradient-to-br from-orange-50 to-orange-50/20 text-orange-800 shadow-sm dark:border-orange-800/45 dark:from-orange-950/35 dark:to-[var(--clm-bg-surface)] dark:text-orange-200'
  }
  if (s === 'approved') {
    return 'border-teal-200/90 bg-gradient-to-br from-teal-50 to-teal-50/20 text-teal-800 shadow-sm dark:border-teal-700/45 dark:from-teal-950/35 dark:to-[var(--clm-bg-surface)] dark:text-teal-300'
  }
  if (s === 'expired') {
    return 'border-amber-300/80 bg-gradient-to-br from-amber-100 to-amber-50/30 text-amber-900 shadow-sm dark:border-amber-800/50 dark:from-amber-950/40 dark:to-[var(--clm-bg-surface)] dark:text-amber-200'
  }
  if (s === 'terminated') {
    return 'border-red-200/90 bg-gradient-to-br from-red-50 to-red-50/20 text-red-800 shadow-sm dark:border-red-800/50 dark:from-red-950/40 dark:to-[var(--clm-bg-surface)] dark:text-red-300'
  }
  return 'border-[var(--clm-border)] bg-gradient-to-br from-[var(--clm-brand-soft)] to-[var(--clm-bg-surface)] text-[var(--clm-brand-strong)] shadow-sm dark:border-[var(--clm-brand)]/35 dark:from-[var(--clm-brand-soft)] dark:to-[var(--clm-bg-surface)] dark:text-[var(--clm-brand)]'
}

const latestVersion = computed(() =>
  contract.value?.document_versions?.find(v => v.is_latest) ||
  contract.value?.document_versions?.at(-1) || null
)

const selectedVersion = computed(() =>
  contract.value?.document_versions?.find(v => v.id === selectedVersionId.value) || null
)

/** Resolved version for UI + APIs when `selectedVersionId` is missing or stale. */
const workingVersion = computed(() => {
  const versions = contract.value?.document_versions || []
  if (!versions.length) return null
  return (
    versions.find((v) => v.id === selectedVersionId.value) ||
    versions.find((v) => v.is_latest) ||
    versions.at(-1) ||
    null
  )
})

/** Single id for review / draft / scoring WebSockets and related API params. */
const primaryVersionId = computed(() => workingVersion.value?.id ?? null)

/** Knowledge graph JSON for the selected document version (backend ``version_knowledge_graphs``). */
const knowledgeGraphDataUrl = computed(() => {
  const vid = selectedVersionId.value
  if (!contractId || vid == null) return ''
  return `/api/contracts/${contractId}/versions/${vid}/knowledge-graph`
})

const knowledgeGraphBuilding = ref(false)

async function buildKnowledgeGraph() {
  const vid = selectedVersionId.value
  if (!vid) {
    toast('Select a document version first.', 'warning')
    return
  }
  knowledgeGraphBuilding.value = true
  try {
    await axios.post(`/api/contracts/${contractId}/versions/${vid}/knowledge-graph/build`)
    toast('Knowledge graph built for this version.')
    knowledgeGraphReloadKey.value += 1
    await nextTick()
    knowledgeGraphInsightsRef.value?.reload?.()
    graphExplorerRef.value?.reload?.()
  } catch (e) {
    const detail = e?.response?.data?.detail
    swalError(typeof detail === 'string' ? detail : (e?.message || 'Build failed'))
  } finally {
    knowledgeGraphBuilding.value = false
  }
}

watch(
  () => graphViewMode.value,
  (mode) => {
    if (mode === 'map') {
      nextTick(() => graphExplorerRef.value?.reload?.())
    }
  }
)

const latestVersionSignerCount = computed(() =>
  latestVersion.value?.version_signers?.length || 0
)

const latestVersionSignedSignerCount = computed(() =>
  latestVersion.value?.version_signers
    ? latestVersion.value.version_signers.filter(s => (s.status || '').toLowerCase() === 'signed').length
    : 0
)

const latestSignerCompletionPct = computed(() => {
  if (!latestVersionSignerCount.value) return 0
  return Math.min(
    100,
    Math.round((latestVersionSignedSignerCount.value / latestVersionSignerCount.value) * 100)
  )
})

/** Same order as Kanban columns and contract status PATCH values (backend ContractStatus enum). */
const CONTRACT_STAGES = ['draft', 'review', 'redraft', 'approved', 'signing', 'active', 'expired', 'terminated']
const totalMilestonesCount = CONTRACT_STAGES.length
const completedMilestonesCount = computed(() => {
  const status = (contract.value?.status || '').toLowerCase()
  const idx = CONTRACT_STAGES.indexOf(status)
  return idx >= 0 ? idx + 1 : 0
})

const nextMilestone = computed(() => {
  const list = [...(contract.value?.milestones || [])]
  if (!list.length) return null
  const dueTime = (m) => {
    if (!m?.due_date) return Number.MAX_SAFE_INTEGER
    const t = new Date(m.due_date).getTime()
    return Number.isNaN(t) ? Number.MAX_SAFE_INTEGER : t
  }
  const pending = list
    .filter((m) => (m.status || '').toLowerCase() !== 'completed')
    .sort((a, b) => dueTime(a) - dueTime(b))
  return pending[0] || list.sort((a, b) => dueTime(a) - dueTime(b))[0] || null
})

// Resizable Chat Sidebar
/** Default docked rail width (px); compact sidebar; drag the left edge to widen. */
const chatWidth = ref(800)
const isResizing = ref(false)

const startResizing = (e) => {
  if (!isLgChatDock.value) return
  isResizing.value = true
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResizing)
}

const handleMouseMove = (e) => {
  if (!isResizing.value || !isLgChatDock.value) return
  const newWidth = window.innerWidth - e.clientX
  const minW = 280
  const minRemainingForContract = 200
  const maxW = Math.max(minW, window.innerWidth - minRemainingForContract)
  if (newWidth >= minW && newWidth <= maxW) {
    chatWidth.value = newWidth
  }
}

const stopResizing = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResizing)
}

/** Viewport width for responsive agent rail (Tailwind lg = 1024px) */
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

let pdfFitResizeRaf = 0
let pdfFitResizeDebounce = 0

function getChunkMatchHints(chunk) {
  const total = Math.max(1, contractPreviewChunks.value.length)
  return {
    chunkIndex: Math.max(0, Number(chunk?.chunk_index) || 0),
    totalChunks: total,
  }
}

/** Compliance row when preview was opened via compliance “eye” — used for Ask AI from highlight. */
const previewComplianceContextRec = shallowRef(null)

const CHUNK_FRAME_ROOT_CLASS = 'clm-chunk-hl-frame-root'

function ensureMainDocChunkFrameStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById('clm-chunk-frame-styles')) return
  const style = document.createElement('style')
  style.id = 'clm-chunk-frame-styles'
  style.textContent = `
    @keyframes clm-chunk-hl-ring-breathe {
      0%, 100% {
        box-shadow:
          0 0 0 2px rgba(37, 99, 235, 0.4),
          0 12px 40px -10px rgba(37, 99, 235, 0.25);
        border-color: rgba(37, 99, 235, 0.52);
      }
      50% {
        box-shadow:
          0 0 0 3px rgba(37, 99, 235, 0.28),
          0 16px 48px -8px rgba(37, 99, 235, 0.32);
        border-color: rgba(59, 130, 246, 0.75);
      }
    }
    .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ring {
      animation: clm-chunk-hl-ring-breathe 2.6s ease-in-out infinite;
    }
    @media (prefers-reduced-motion: reduce) {
      .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ring {
        animation: none !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.42);
      }
    }
    .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ask:hover {
      filter: brightness(1.06);
      transform: translateY(-1px);
    }
    .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ask:active {
      transform: translateY(0);
      filter: brightness(0.96);
    }
  `
  document.head.appendChild(style)
}

function ensureIframeChunkFrameStyles(doc) {
  if (!doc || doc.getElementById('clm-chunk-frame-styles')) return
  const style = doc.createElement('style')
  style.id = 'clm-chunk-frame-styles'
  style.textContent = `
    @keyframes clm-chunk-hl-ring-breathe {
      0%, 100% {
        box-shadow:
          0 0 0 2px rgba(37, 99, 235, 0.4),
          0 12px 40px -10px rgba(37, 99, 235, 0.25);
        border-color: rgba(37, 99, 235, 0.52);
      }
      50% {
        box-shadow:
          0 0 0 3px rgba(37, 99, 235, 0.28),
          0 16px 48px -8px rgba(37, 99, 235, 0.32);
        border-color: rgba(59, 130, 246, 0.75);
      }
    }
    .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ring {
      animation: clm-chunk-hl-ring-breathe 2.6s ease-in-out infinite;
    }
    @media (prefers-reduced-motion: reduce) {
      .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ring {
        animation: none !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.42);
      }
    }
    .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ask:hover {
      filter: brightness(1.06);
      transform: translateY(-1px);
    }
    .${CHUNK_FRAME_ROOT_CLASS} .clm-chunk-hl-frame-ask:active {
      transform: translateY(0);
      filter: brightness(0.96);
    }
  `
  doc.head.appendChild(style)
}

function removePreviewHighlightFrame() {
  document.getElementById('pdf-container')?.querySelectorAll(`.${CHUNK_FRAME_ROOT_CLASS}`).forEach((n) => n.remove())
  const idoc = docxPreviewIframeRef.value?.contentDocument
  idoc?.querySelectorAll(`.${CHUNK_FRAME_ROOT_CLASS}`).forEach((n) => n.remove())
}

/**
 * Union of mark client rects, positioned for `position:absolute` inside `ancestorEl`
 * (ancestor should be `position: relative` or equivalent). Uses viewport rects; do **not**
 * add scrollTop/scrollLeft — mark and ancestor move together when the document scrolls.
 */
function unionMarkRectsVsViewportBox(marks, ancestorEl, padOpts = {}) {
  if (!marks?.length || !ancestorEl) return null
  const padX = padOpts.padX ?? 6
  const padTop = padOpts.padTop ?? 5
  const padBottom = padOpts.padBottom ?? 14
  const aRect = ancestorEl.getBoundingClientRect()
  let minL = Infinity
  let minT = Infinity
  let maxR = -Infinity
  let maxB = -Infinity
  for (const m of marks) {
    if (!m?.isConnected) continue
    const r = m.getBoundingClientRect()
    minL = Math.min(minL, r.left)
    minT = Math.min(minT, r.top)
    maxR = Math.max(maxR, r.right)
    maxB = Math.max(maxB, r.bottom)
  }
  if (minL === Infinity) return null
  return {
    left: minL - aRect.left - padX,
    top: minT - aRect.top - padTop,
    width: maxR - minL + padX * 2,
    height: maxB - minT + padTop + padBottom,
  }
}

function buildChunkHighlightFrameEl(doc, box, frameOpts = {}) {
  const reserveTop = Math.max(0, Number(frameOpts.reserveTop) || 0)
  const root = doc.createElement('div')
  root.className = CHUNK_FRAME_ROOT_CLASS
  const minW = 88
  const minH = 36
  const w = Math.max(box.width, minW)
  const h = Math.max(box.height, minH)
  root.style.cssText = `position:absolute;left:${box.left}px;top:${box.top}px;width:${w}px;height:${h}px;z-index:25;pointer-events:none;box-sizing:border-box;overflow:visible;`

  const ring = doc.createElement('div')
  ring.className = 'clm-chunk-hl-frame-ring'
  ring.setAttribute('aria-hidden', 'true')
  const bleed = 6
  const ringTop = Math.max(0, reserveTop - bleed)
  ring.style.cssText =
    reserveTop > 0
      ? `position:absolute;left:${-bleed}px;right:${-bleed}px;top:${ringTop}px;bottom:${-bleed}px;border-radius:14px;pointer-events:none;box-sizing:border-box;border:2px solid rgba(37,99,235,0.5);background:rgba(37,99,235,0.04);transition:transform 0.2s ease;`
      : `position:absolute;inset:${-bleed}px;border-radius:14px;pointer-events:none;box-sizing:border-box;border:2px solid rgba(37,99,235,0.5);background:rgba(37,99,235,0.04);transition:transform 0.2s ease;`

  root.appendChild(ring)

  const btn = doc.createElement('button')
  btn.type = 'button'
  btn.className = 'clm-chunk-hl-frame-ask'
  btn.title = 'Ask AI about this highlight'
  const chipBase =
    'z-index:2;pointer-events:auto;display:inline-flex;align-items:center;gap:5px;padding:6px 12px;font-size:11px;font-weight:700;border-radius:9999px;border:none;background:linear-gradient(135deg,#2563eb,#4f46e5);color:#fff;cursor:pointer;box-shadow:0 4px 18px rgba(37,99,235,0.38),0 1px 2px rgba(15,23,42,0.08);letter-spacing:0.02em;transition:filter 0.15s ease,transform 0.15s ease;white-space:nowrap;'
  btn.style.cssText =
    reserveTop > 0
      ? `position:absolute;top:6px;right:8px;bottom:auto;left:auto;${chipBase}`
      : `position:absolute;bottom:calc(100% + 10px);top:auto;left:auto;right:8px;${chipBase}`
  btn.innerHTML =
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg><span>Ask AI</span>'
  btn.addEventListener('click', (e) => {
    e.preventDefault()
    e.stopPropagation()
    sendPreviewHighlightAskAi()
  })
  root.appendChild(btn)
  return root
}

function attachPreviewHighlightFrame(marks) {
  removePreviewHighlightFrame()
  const filtered = (marks || []).filter((m) => m?.isConnected)
  if (!filtered.length) return

  if (isDocxPreview.value) {
    const idoc = docxPreviewIframeRef.value?.contentDocument
    if (!idoc?.body) return
    injectHighlightStylesIntoDocument(idoc)
    ensureIframeChunkFrameStyles(idoc)
    if (!idoc.body.style.position) idoc.body.style.position = 'relative'
    let box = unionMarkRectsVsViewportBox(filtered, idoc.body)
    if (!box) return
    /* Room for chip above ring when selection is flush with top of body */
    const chipClearance = 44
    let reserveTop = 0
    if (box.top < chipClearance) {
      const lift = chipClearance - box.top
      reserveTop = lift
      box = { ...box, top: box.top - lift, height: box.height + lift }
    }
    idoc.body.appendChild(buildChunkHighlightFrameEl(idoc, box, { reserveTop }))
    return
  }

  ensureMainDocChunkFrameStyles()
  const container = document.getElementById('pdf-container')
  if (!container) return
  let box = unionMarkRectsVsViewportBox(filtered, container)
  if (!box) return
  const chipClearance = 44
  let reserveTop = 0
  if (box.top < chipClearance) {
    const lift = chipClearance - box.top
    reserveTop = lift
    box = { ...box, top: box.top - lift, height: box.height + lift }
  }
  container.appendChild(buildChunkHighlightFrameEl(document, box, { reserveTop }))
}

function collectChunkHighlightPlainText() {
  const roots = []
  if (isDocxPreview.value) {
    const doc = docxPreviewIframeRef.value?.contentDocument
    if (doc?.body) roots.push(doc.body)
  } else {
    const el = document.getElementById('clm-pdf-text-layer')
    if (el) roots.push(el)
  }
  const texts = []
  for (const root of roots) {
    root.querySelectorAll(`.${CHUNK_HL_MARK_CLASS}`).forEach((m) => texts.push(m.textContent || ''))
  }
  return texts.join(' ').replace(/\s+/g, ' ').trim()
}

function showPreviewAskAiAfterHighlight(marks) {
  nextTick(() => {
    requestAnimationFrame(() => {
      let list = (marks || []).filter((m) => m?.isConnected)
      if (!list.length) {
        if (isDocxPreview.value) {
          const doc = docxPreviewIframeRef.value?.contentDocument
          const nl = doc?.body?.querySelectorAll(`.${CHUNK_HL_MARK_CLASS}`)
          if (nl?.length) list = Array.from(nl)
        } else {
          const nl = document.getElementById('clm-pdf-text-layer')?.querySelectorAll(`.${CHUNK_HL_MARK_CLASS}`)
          if (nl?.length) list = Array.from(nl)
        }
      }
      attachPreviewHighlightFrame(list)
    })
  })
}

function hidePreviewAskAiButton() {
  removePreviewHighlightFrame()
}

function buildSingleComplianceContextBlock(rec) {
  const lines = ['[COMPLIANCE CONTEXT]', '']
  const statusLabel = (rec.status || 'unknown').toUpperCase()
  lines.push(`### ${rec.check_name} [${statusLabel}]`)
  if (rec.findings) lines.push(String(rec.findings).trim())
  if (rec.page_number != null) lines.push(`(Page ${rec.page_number})`)
  lines.push('')
  lines.push('[END COMPLIANCE CONTEXT]')
  return lines.join('\n')
}

async function sendPreviewHighlightAskAi() {
  if (reviewTyping.value) return
  const excerpt = collectChunkHighlightPlainText()
  if (!excerpt) {
    toast('No highlighted text in preview.', 'warning')
    return
  }
  selectedAgent.value = 'review'
  showChat.value = true

  const rec = previewComplianceContextRec.value
  const parts = []
  if (rec) {
    parts.push(buildSingleComplianceContextBlock(rec), CP_ANALYSIS_PROMPT)
  }
  const defaultQ = rec
    ? 'Analyze this excerpt in relation to the compliance check above.'
    : 'Analyze this contract excerpt and note risks, gaps, or suggested improvements.'
  parts.push(`--- User question ---\n${defaultQ}`)

  const fIds = [...new Set(selectedReviewFindingIds.value || [])]
  const rIds = [...new Set(selectedReviewRecommendationIds.value || [])]
  const backendMsg = formatReviewBackendMessage(parts.join('\n\n'), fIds, rIds)

  const displayQuery = rec ? `Ask AI · ${rec.check_name}` : 'Ask AI · highlighted excerpt'
  const userMsg = { role: 'user', content: displayQuery, fromPreviewHighlight: true }
  if (rec) {
    userMsg.complianceChecks = [
      {
        id: rec.id,
        check_name: rec.check_name,
        status: rec.status,
        findings: rec.findings ?? null,
        page_number: rec.page_number ?? null,
      },
    ]
  }

  chatMessages.value.review.push(userMsg)
  reviewTyping.value = true
  reviewTodos.value = []
  try {
    const ws = await ensureReviewSocket()
    ws.send(
      JSON.stringify(
        buildReviewWsPayload(backendMsg, { comprehensiveContractOverride: excerpt })
      )
    )
    nextTick(scrollChatToBottom)
  } catch (e) {
    reviewTyping.value = false
    clearReviewPlanUI()
    chatMessages.value.review.push({
      role: 'assistant',
      content: `**Connection error:** ${e?.message || e}`,
      markdown: true,
    })
    nextTick(scrollChatToBottom)
  }
}

function schedulePdfFitRerender() {
  if (typeof window === 'undefined') return
  if (!pdfDoc.value || activeTab.value === 'graph' || !documentPreviewDrawerOpen.value || !documentPreviewCanvasVisible.value) return
  cancelAnimationFrame(pdfFitResizeRaf)
  clearTimeout(pdfFitResizeDebounce)
  pdfFitResizeDebounce = window.setTimeout(() => {
    pdfFitResizeDebounce = 0
    pdfFitResizeRaf = requestAnimationFrame(() => {
      pdfFitResizeRaf = requestAnimationFrame(() => {
        pdfFitResizeRaf = 0
        void renderPdf()
      })
    })
  }, 100)
}

function reapplyActiveChunkHighlight() {
  if (suppressChunkHighlightReapply.value) return
  const id = contractActiveChunkId.value
  if (id == null) return
  const chunk = contractPreviewChunks.value.find((c) => c.id === id)
  if (!chunk) return
  const { marks } = locateChunkInPreview({
    chunk,
    isPdf: !isDocxPreview.value,
    getHighlightRoot: () => {
      if (isDocxPreview.value) {
        const doc = docxPreviewIframeRef.value?.contentDocument
        return doc?.body || null
      }
      return document.getElementById('clm-pdf-text-layer')
    },
    getPdfScrollEl: () => document.getElementById('pdf-scroll-container'),
    getPreviewIframe: () => docxPreviewIframeRef.value,
    matchHints: getChunkMatchHints(chunk),
  })
  showPreviewAskAiAfterHighlight(marks)
}

/** Wait until the preview slide-over has width (drawer translate/width transition) before fitting PDF. */
async function waitForPreviewDrawerLayout() {
  await nextTick()
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
  const scrollEl = typeof document !== 'undefined' ? document.getElementById('pdf-scroll-container') : null
  if (!scrollEl) return
  for (let i = 0; i < 30; i++) {
    const rect = scrollEl.getBoundingClientRect()
    if (rect.width >= 120) return
    await new Promise((r) => requestAnimationFrame(r))
  }
}

function syncContractViewportWidth() {
  if (typeof window === 'undefined') return
  viewportWidth.value = window.innerWidth
  const maxChat = Math.max(280, window.innerWidth - 200)
  if (chatWidth.value > maxChat) chatWidth.value = maxChat
  schedulePdfFitRerender()
}

const isLgChatDock = computed(() => viewportWidth.value >= 1024)

const versionUploading = ref(false)
const versionUploadProgress = ref(0) // 0–100 during HTTP upload

const uploadVersion = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  // Reset the input so re-selecting the same file fires change again
  event.target.value = ''

  const formData = new FormData()
  formData.append('file', file)
  formData.append('notes', 'New document version uploaded')

  versionUploading.value = true
  versionUploadProgress.value = 0

  try {
    const response = await axios.post(`/api/contracts/${contractId}/upload-version`, formData, {
      onUploadProgress: (e) => {
        if (e.total) versionUploadProgress.value = Math.round((e.loaded * 100) / e.total)
      },
    })
    contract.value = response.data
    const nv =
      response.data?.document_versions?.find((v) => v.is_latest) ||
      response.data?.document_versions?.at(-1)
    if (nv?.id != null) {
      selectedVersionId.value = nv.id
      persistWorkingVersionId(nv.id)
    }
    toast('Version uploaded — processing in background…')
    await loadPdf()
  } catch (error) {
    console.error('Failed to upload version:', error)
    swalError('Upload failed')
  } finally {
    versionUploading.value = false
    versionUploadProgress.value = 0
  }
}

// ── Version Upload from Drive ────────────────────────────────────────────
const showVersionDrivePicker = ref(false)
const vdpDrives = ref([])
const vdpSelectedDriveId = ref(null)
const vdpFolders = ref([])
const vdpFoldersLoading = ref(false)
const vdpActiveFolderId = ref(null)
const vdpActiveFiles = ref([])
const vdpFilesLoading = ref(false)
const vdpSelectedFileId = ref(null)
const vdpFileSearch = ref('')
const vdpExpandedIds = ref(new Set())
const vdpPickLoading = ref(false)

const VDP_EXTS = ['pdf', 'docx']
const vdpExtLabel = (n) => { const e = (n||'').split('.').pop(); return e && e.length <= 5 ? e.toUpperCase() : '?' }
const vdpFormatBytes = (v) => { const n = Number(v||0); if (!n) return '0 B'; const u = ['B','KB','MB','GB']; let s=n,i=0; while(s>=1024&&i<u.length-1){s/=1024;i++} return `${s.toFixed(s>=10||i===0?0:1)} ${u[i]}` }
const vdpFileIconClass = (ct) => { if (!ct) return 'bg-gray-100 dark:bg-gray-800 text-gray-400'; if (ct.includes('pdf')) return 'bg-red-50 dark:bg-red-900/30 text-red-500'; if (ct.includes('word')||ct.includes('document')) return 'bg-blue-50 dark:bg-blue-900/30 text-blue-500'; return 'bg-gray-100 dark:bg-gray-800 text-gray-400' }
const vdpIsAllowed = (f) => VDP_EXTS.includes((f.original_filename||'').split('.').pop().toLowerCase())
const vdpFolderFileCount = (folder) => {
  let count = (folder.files || []).filter(vdpIsAllowed).length
  const children = vdpFolders.value.filter(f => f.parent_id === folder.id)
  for (const child of children) count += vdpFolderFileCount(child)
  return count
}

const vdpFlatFolders = computed(() => {
  const result = []
  const walk = (pid, depth) => {
    const ch = vdpFolders.value.filter(f => f.parent_id === pid).sort((a,b) => (a.created_at||'').localeCompare(b.created_at||''))
    for (const folder of ch) {
      const hc = vdpFolders.value.some(f => f.parent_id === folder.id)
      const ex = vdpExpandedIds.value.has(folder.id)
      result.push({ folder, depth, hasChildren: hc, isExpanded: ex })
      if (hc && ex) walk(folder.id, depth + 1)
    }
  }
  const roots = vdpFolders.value.filter(f => !f.parent_id).sort((a,b) => (a.created_at||'').localeCompare(b.created_at||''))
  for (const r of roots) {
    const hc = vdpFolders.value.some(f => f.parent_id === r.id)
    const ex = vdpExpandedIds.value.has(r.id)
    result.push({ folder: r, depth: 0, hasChildren: hc, isExpanded: ex })
    if (hc && ex) walk(r.id, 1)
  }
  return result
})

const vdpFilteredFiles = computed(() => {
  let files = vdpActiveFiles.value.filter(vdpIsAllowed)
  const q = vdpFileSearch.value.trim().toLowerCase()
  if (q) files = files.filter(f => f.original_filename.toLowerCase().includes(q))
  return files
})

const vdpPickedFileName = computed(() => {
  if (!vdpSelectedFileId.value) return ''
  return vdpActiveFiles.value.find(f => f.id === vdpSelectedFileId.value)?.original_filename || ''
})

const vdpToggleExpand = (id) => { const s = new Set(vdpExpandedIds.value); s.has(id)?s.delete(id):s.add(id); vdpExpandedIds.value = s }

const vdpSelectFolder = async (folder) => {
  vdpActiveFolderId.value = folder.id
  vdpSelectedFileId.value = null
  vdpFileSearch.value = ''
  const s = new Set(vdpExpandedIds.value)
  let cur = folder
  while (cur?.parent_id) { s.add(cur.parent_id); cur = vdpFolders.value.find(f => f.id === cur.parent_id) }
  vdpExpandedIds.value = s
  vdpFilesLoading.value = true
  try { const { data } = await axios.get(`/api/document-drive-folders/${folder.id}`); vdpActiveFiles.value = data.files || [] }
  catch { vdpActiveFiles.value = [] }
  finally { vdpFilesLoading.value = false }
}

const vdpOnDriveChange = async () => {
  vdpActiveFolderId.value = null; vdpActiveFiles.value = []; vdpSelectedFileId.value = null; vdpExpandedIds.value = new Set()
  if (!vdpSelectedDriveId.value) { vdpFolders.value = []; return }
  vdpFoldersLoading.value = true
  try { const { data } = await axios.get(`/api/document-drives/${vdpSelectedDriveId.value}/folders`); vdpFolders.value = data || [] }
  catch { vdpFolders.value = [] }
  finally { vdpFoldersLoading.value = false }
}

watch(showVersionDrivePicker, async (v) => {
  if (v && !vdpDrives.value.length) {
    try { const { data } = await axios.get('/api/document-drives'); vdpDrives.value = data || []; if (vdpDrives.value.length === 1) { vdpSelectedDriveId.value = vdpDrives.value[0].id; await vdpOnDriveChange() } }
    catch { vdpDrives.value = [] }
  }
})

const confirmVersionDrivePick = async () => {
  if (!vdpSelectedFileId.value) return
  vdpPickLoading.value = true
  try {
    const meta = vdpActiveFiles.value.find(f => f.id === vdpSelectedFileId.value)
    if (!meta) return
    const formData = new FormData()
    formData.append('drive_file_id', String(meta.id))
    formData.append('notes', 'Version added from Document Drive')
    const response = await axios.post(`/api/contracts/${contractId}/upload-version`, formData)
    contract.value = response.data
    const nv =
      response.data?.document_versions?.find((v) => v.is_latest) ||
      response.data?.document_versions?.at(-1)
    if (nv?.id != null) {
      selectedVersionId.value = nv.id
      persistWorkingVersionId(nv.id)
    }
    showVersionDrivePicker.value = false
    toast('New version added from Drive')
    await loadPdf()
  } catch (e) {
    console.error('Failed to add version from drive:', e)
    swalError('Could not add version from drive')
  } finally {
    vdpPickLoading.value = false
  }
}

const removeDocumentVersion = async (version) => {
  const versions = contract.value?.document_versions || []
  if (versions.length <= 1) {
    swalError('Cannot remove the only document version.', 'Not allowed')
    return
  }
  const label = version.label || `Version v${version.version_number}`
  const ok = await swalConfirm(
    `Remove ${label}? Files and signer data for this version will be deleted. This cannot be undone.`,
    'Remove version?',
    'Remove',
  )
  if (!ok) return
  const vid = version.id
  try {
    const response = await axios.delete(`/api/contracts/${contractId}/versions/${vid}`)
    contract.value = response.data
    if (selectedVersionId.value === vid) {
      const latest =
        contract.value?.document_versions?.find((v) => v.is_latest) ||
        contract.value?.document_versions?.at(-1)
      selectedVersionId.value = latest?.id ?? null
      if (latest?.id != null) persistWorkingVersionId(latest.id)
    }
    if (String(compareVersionAId.value) === String(vid)) compareVersionAId.value = ''
    if (String(compareVersionBId.value) === String(vid)) compareVersionBId.value = ''
    toast('Version removed')
  } catch (error) {
    console.error('Failed to remove version:', error)
    const d = error.response?.data?.detail
    const msg = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x?.msg || x).join(', ') : 'Failed to remove version'
    swalError(msg)
  }
}

const updateMilestone = async (milestone, newStatus) => {
  try {
    await axios.patch(`/api/milestones/${milestone.id}`, { status: newStatus })
    milestone.status = newStatus
  } catch (error) {
    console.error('Failed to update milestone:', error)
  }
}

const addComplaint = async (findings) => {
  try {
    const vid = primaryVersionId.value
    const response = await axios.post(`/api/contracts/${contractId}/compliance`, {
      record_type: 'complaint',
      check_name: 'Manual Complaint',
      status: 'open',
      findings: findings,
      document_version_id: vid ?? undefined,
    })
    contract.value.compliance_records.push(response.data)
  } catch (error) {
    console.error('Failed to add complaint:', error)
  }
}

// Chat & Agent State
const loading = ref(true)
/** Right slide-over document preview (hidden on Graph tab). */
const documentPreviewDrawerOpen = ref(false)
/** Contract preview: document chunks side panel (same indexing as CLM / drive). */
const contractPreviewChunksDrawerOpen = ref(false)
const contractPreviewChunksDrawerWidth = ref(320)
const contractPreviewChunks = ref([])
const contractChunksLoading = ref(false)
const contractChunksExpandedIds = ref(new Set())
const contractActiveChunkId = ref(null)
/** While scanning PDF pages for a chunk, skip re-highlight after each renderPdf (text layer is rebuilt each time). */
const suppressChunkHighlightReapply = ref(false)
const docxPreviewIframeRef = ref(null)
/** When false, the PDF canvas (and signature overlays) are removed from the drawer for a cleaner view. */
const documentPreviewCanvasVisible = ref(true)
const _suppressPdfReload = ref(false)
const showChat = ref(false)
const showAgentConfig = ref(false)
const selectedAgent = ref('review')
const agentGuideCollapsed = ref(false)
const isTyping = ref(false)
const userInput = ref('')

// ── Guideline-in-chat state ────────────────────────────────────────────────
const GL_SECTION_DEFS = [
  { key: 'financial_limits',           title: 'Financial Limits',           abbr: 'FL' },
  { key: 'mandatory_clauses',          title: 'Mandatory Clauses',          abbr: 'MC' },
  { key: 'technical_standards',        title: 'Technical Standards',        abbr: 'TS' },
  { key: 'compliance_requirements',    title: 'Compliance Requirements',    abbr: 'CR' },
  { key: 'contractor_eligibility',     title: 'Contractor Eligibility',     abbr: 'CE' },
  { key: 'work_execution_standards',   title: 'Work Execution Standards',   abbr: 'WE' },
  { key: 'measurement_payment',        title: 'Measurement & Payment',      abbr: 'MP' },
  { key: 'contract_administration',    title: 'Contract Administration',    abbr: 'CA' },
  { key: 'defect_liability',           title: 'Defect Liability',           abbr: 'DL' },
  { key: 'documentation_requirements', title: 'Documentation Requirements', abbr: 'DR' },
  { key: 'decision_thresholds',        title: 'Decision Thresholds',        abbr: 'DT' },
  { key: 'validation_weights',         title: 'Validation Weights',         abbr: 'VW' },
  { key: 'critical_issues',            title: 'Critical Issues',            abbr: 'CI' },
]
const glPickerOpen   = ref(false)
const glSelectedKeys = ref(new Set())
const glConfirmMode  = ref(false)
const glInstruction  = ref('')

// ── Compliance context picker (review agent) ──────────────────────────────
const cpPickerOpen   = ref(false)
const cpSelectedIds  = ref(new Set())

// ── Review items (saved from review agent) ────────────────────────────────
const contractReviewItems  = ref([])
const savedReviewMsgIds    = ref(new Set())
const draftItemPickerOpen  = ref(false)
const selectedDraftItemIds = ref(new Set())

async function loadReviewItems() {
  if (!contract.value?.id) return
  try {
    const { data } = await axios.get(`/api/contracts/${contract.value.id}/review-items`)
    contractReviewItems.value = data || []
  } catch (_) {}
}

async function saveReviewItem(msg, idx) {
  if (savedReviewMsgIds.value.has(idx)) return
  const content = msg.content || ''
  // Extract title from first non-empty line (up to 100 chars)
  const firstLine = content.split('\n').find(l => l.replace(/[#*>\s]/g, '').length > 4) || ''
  const title = firstLine.replace(/^#+\s*/, '').replace(/\*\*/g, '').slice(0, 100) || 'Review finding'
  // Detect severity from content keywords
  const lower = content.toLowerCase()
  const severity = lower.includes('critical') || lower.includes('🔴') ? 'critical'
    : lower.includes('moderate') || lower.includes('🟡') ? 'moderate'
    : lower.includes('minor') || lower.includes('🟢') ? 'minor'
    : null
  try {
    const { data } = await axios.post(`/api/contracts/${contract.value.id}/review-items`, {
      title,
      content,
      source_query: chatMessages.value.review.slice(0, idx).filter(m => m.role === 'user').slice(-1)[0]?.content || null,
      item_type: 'finding',
      severity,
    })
    contractReviewItems.value.unshift(data)
    const s = new Set(savedReviewMsgIds.value)
    s.add(idx)
    savedReviewMsgIds.value = s
  } catch (e) {
    console.error('Failed to save review item', e)
  }
}

function buildGenerateFixPrompt(lastResponse) {
  const safeText = String(lastResponse || '').trim()
  const lines = [
    '[ACTIONABLE ITEMS EXTRACTION]',
    'You are a contract remediation assistant.',
    'From the review response below, generate practical, prioritized actionable items the writer can apply during redraft.',
    'Group outputs by severity: Critical, Moderate, and Minor.',
    'Return concise bullets with concrete text-level edits.',
    '',
    'For each item, include:',
    '- Finding: what is not compliant',
    '- Contract area / clause reference if any',
    '- Impact or risk',
    '- Recommended corrective action',
    '- Suggested replacement wording',
    '',
    'Do not provide explanations outside the list.',
    '[IMP] Always start with a description that explains the purpose and scope of the generated actionable items.',
    '',
    'Review response:',
    safeText,
  ]
  return lines.join('\n')
}

function isReviewAgentErrorMessage(msg) {
  const text = String(msg?.content || '').toLowerCase().trim()
  return text.startsWith('**error') || text.startsWith('**connection error') || text.startsWith('error:') || text.startsWith('connection error:')
}

function isGenerateFixResponseMessage(msg) {
  if (!msg || msg.role !== 'assistant') return false
  return !!msg.generatedFixResponse
}

function shouldShowReviewActionButtons(idx, msg) {
  return msg?.role === 'assistant' && (idx > 0 || !!msg?.fromGuidelineRun || !!msg?.fromComplianceRun)
}

function getLastReviewUserMessageFlags() {
  const msgs = chatMessages.value.review
  for (let i = msgs.length - 1; i >= 0; i -= 1) {
    const item = msgs[i]
    if (item?.role === 'user') {
      return {
        fromGuidelineRun: !!item.fromGuidelineRun,
        fromComplianceRun: !!item.fromComplianceRun,
        fromGeneratedFixPrompt: !!item.generatedFixPrompt,
      }
    }
  }
  return { fromGuidelineRun: false, fromComplianceRun: false, fromGeneratedFixPrompt: false }
}

function selectAllDraftReviewItems() {
  if (!contractReviewItems.value.length) {
    selectedDraftItemIds.value = new Set()
    return
  }
  if (selectedDraftItemIds.value.size === contractReviewItems.value.length) {
    selectedDraftItemIds.value = new Set()
  } else {
    selectedDraftItemIds.value = new Set(contractReviewItems.value.map(i => i.id))
  }
}

function getSelectedDraftItems() {
  return contractReviewItems.value.filter(i => selectedDraftItemIds.value.has(i.id))
}

function buildDraftReviewItemsContext(selectedItems) {
  if (!selectedItems?.length) return ''
  const lines = [
    '[REVIEW FINDINGS CONTEXT]',
    '',
    'The following issues were identified during the contract review phase.',
    'You MUST address each item in the redraft. Do not ignore any finding.',
    '',
  ]
  selectedItems.forEach((item, n) => {
    const sev = item.severity ? ` [${item.severity.toUpperCase()}]` : ''
    lines.push(`### Finding ${n + 1}${sev}: ${item.title || 'Review item'}`)
    lines.push(item.content.trim())
    lines.push('')
  })
  lines.push(
    '--- Redraft Instructions ---',
    'The system attaches the contract as **indexed document chunks** (one chunk per turn, in order). Your task is to go through **each** chunk you receive, apply fixes that follow from the saved **review items** above plus any **linked findings** and **recommendations** included in the user request, and return a **list of structured amendment/recommendation records for that chunk only** (or an empty list when no change is needed for that slice). Do not propose edits for text that was not in the attached chunk.',
    '',
    'Using the review findings above as mandatory requirements:',
    '1. **Address every finding** — revise or add clauses to comply with each identified gap that applies to the current chunk.',
    '2. **Preserve intent** — keep the contract\'s original purpose and structure; only change what is needed to fix the issues.',
    '3. **Flag changes** — in each record, briefly note which finding or recommendation the change implements.',
    '4. **Prioritise critical findings** first, then moderate, then minor.',
    '5. **Per-chunk output** — for this chunk, output the revised wording as structured replacement/addition records (not a free-form rewrite of the whole document); unchanged chunks should yield no records.',
    '[END REVIEW FINDINGS CONTEXT]',
  )
  return lines.join('\n')
}

async function runDraftSelectedItemsNow() {
  if (draftTyping.value) return
  const selectedItems = getSelectedDraftItems()
  if (selectedItems.length === 0) return

  const fIds = [...new Set(selectedReviewFindingIds.value || [])]
  const rIds = [...new Set(selectedReviewRecommendationIds.value || [])]
  const reviewItemsBlock = buildDraftReviewItemsContext(selectedItems)
  const query = `Generate redraft recommendations using selected review findings and recommendations (${fIds.length + rIds.length} item${selectedItems.length === 1 ? '' : 's'}).`
  const baseMessage = reviewItemsBlock ? `${reviewItemsBlock}\n\n--- User request ---\n${query}` : query
  const backendMessage = formatDraftBackendMessage(baseMessage, fIds, rIds)

  const displayContent = `${query}\n\n(Sent with: ${selectedItems.length} review item${selectedItems.length === 1 ? '' : 's'})`
  chatMessages.value.draft.push({
    role: 'user',
    content: displayContent,
    reviewItems: selectedItems.map(i => ({ id: i.id, title: i.title, severity: i.severity })),
  })

  userInput.value = ''
  selectedDraftItemIds.value = new Set()
  draftItemPickerOpen.value = false
  draftTyping.value = true
  draftTodos.value = []
  try {
    const ws = await ensureDraftSocket()
    const versionId = primaryVersionId.value
    ws.send(
      JSON.stringify({
        type: 'chat',
        message: backendMessage,
        contract_id: contract.value?.id ?? null,
        version_id: versionId ?? null,
      })
    )
    nextTick(scrollChatToBottom)
  } catch (e) {
    draftTyping.value = false
    clearDraftPlanUI()
    chatMessages.value.draft.push({
      role: 'assistant',
      content: `**Connection error:** ${e?.message || e}`,
      markdown: true,
    })
    nextTick(scrollChatToBottom)
  }
}

async function generateFixFromReviewMessage(msg) {
  if (reviewTyping.value) return
  const content = msg?.content || ''
  const prompt = buildGenerateFixPrompt(content)
  if (!prompt) return

  chatMessages.value.review.push({
    role: 'user',
    content: 'Generate actionable items for the last review response',
    generatedFixPrompt: true,
  })
  reviewTyping.value = true
  reviewTodos.value = []
  try {
    const ws = await ensureReviewSocket()
    ws.send(JSON.stringify(buildReviewWsPayload(prompt)))
    nextTick(scrollChatToBottom)
  } catch (e) {
    reviewTyping.value = false
    clearReviewPlanUI()
    chatMessages.value.review.push({
      role: 'assistant',
      content: `**Connection error:** ${e?.message || e}`,
      markdown: true,
    })
    nextTick(scrollChatToBottom)
  }
}

async function deleteReviewItem(id) {
  try {
    await axios.delete(`/api/review-items/${id}`)
    contractReviewItems.value = contractReviewItems.value.filter(i => i.id !== id)
    const s = new Set(selectedDraftItemIds.value)
    s.delete(id)
    selectedDraftItemIds.value = s
  } catch (_) {}
}

function toggleDraftItem(id) {
  const s = new Set(selectedDraftItemIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedDraftItemIds.value = s
}

const availableGlSections = computed(() => {
  const c = contract.value
  if (!c) return []
  return GL_SECTION_DEFS.filter(s => {
    const v = c[`guideline_${s.key}`]
    return v !== null && v !== undefined
  })
})

const glSelectedList = computed(() =>
  GL_SECTION_DEFS.filter(s => glSelectedKeys.value.has(s.key))
)

function glToggleKey(key) {
  const s = new Set(glSelectedKeys.value)
  s.has(key) ? s.delete(key) : s.add(key)
  glSelectedKeys.value = s
}

function glRemoveKey(key) {
  const s = new Set(glSelectedKeys.value)
  s.delete(key)
  glSelectedKeys.value = s
}

function glClearAll() {
  glSelectedKeys.value = new Set()
  glConfirmMode.value  = false
  glInstruction.value  = ''
  glPickerOpen.value   = false
}

function selectAllGuidelineSections() {
  const allKeys = availableGlSections.value.map((s) => s.key)
  if (!allKeys.length) {
    glSelectedKeys.value = new Set()
    return
  }
  if (glSelectedKeys.value.size === allKeys.length) {
    glSelectedKeys.value = new Set()
  } else {
    glSelectedKeys.value = new Set(allKeys)
  }
}

function glBuildContextBlock() {
  const c  = contract.value
  const fw = c?.guideline_framework_title || c?.guideline_framework_slug || 'Guideline'
  const lines = [`[GUIDELINE CONTEXT — ${fw}]`, '']
  for (const s of glSelectedList.value) {
    const data = c?.[`guideline_${s.key}`]
    if (!data) continue
    lines.push(`### ${s.title}`)
    lines.push(_flattenGuidelineValue(data))
    lines.push('')
  }
  lines.push('[END GUIDELINE CONTEXT]')
  return lines.join('\n')
}

const GL_ANALYSIS_PROMPT = `--- Guideline Analysis Instructions ---
You are a contract compliance expert. Using the guideline context provided above:

1. **Alignment check** — Verify whether the contract document aligns with each guideline section. Flag every clause, value, or requirement that is missing, non-compliant, or contradicts the guideline.
2. **Major issues** — Highlight critical gaps or deviations that pose financial, legal, or operational risk. Be specific: cite the guideline field and the corresponding contract clause (or its absence).
3. **Structured report** — Present findings as a prioritized list:
   - 🔴 Critical — must fix before signing
   - 🟡 Moderate — should fix or acknowledge
   - 🟢 Minor / informational
4. **Recommendations** — For each issue, suggest a concrete corrective action or clause amendment.

Be concise, precise, and reference guideline values (e.g. "Guideline requires max 20% advance; contract specifies 30%").`

async function glConfirmSend(overrideQuery = null, options = {}) {
  if (glSelectedKeys.value.size === 0) return
  await reviewSendContextPack({
    overrideQuery: overrideQuery ?? userInput.value,
    fromGuidelineRun: !!options.fromRun,
  })
}

async function runSelectedGuidelinesNow() {
  if (reviewTyping.value) return
  if (glSelectedKeys.value.size === 0) return
  glPickerOpen.value = false
  const directQuery = `Run guideline compliance review for: ${glSelectedList.value.map((s) => s.title).join(', ')}`
  await reviewSendContextPack({ overrideQuery: directQuery, fromGuidelineRun: true })
}

// ── Compliance context helpers ────────────────────────────────────────────
const cpSelectedList = computed(() =>
  complianceRecordsForVersion.value.filter(r => cpSelectedIds.value.has(r.id))
)

function cpToggleId(id) {
  const s = new Set(cpSelectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  cpSelectedIds.value = s
}

function cpRemoveId(id) {
  const s = new Set(cpSelectedIds.value)
  s.delete(id)
  cpSelectedIds.value = s
}

function cpClearAll() {
  cpSelectedIds.value = new Set()
  cpPickerOpen.value  = false
}

function selectAllComplianceChecks() {
  const all = complianceRecordsForVersion.value.map(r => r.id)
  if (!all.length) { cpSelectedIds.value = new Set(); return }
  cpSelectedIds.value = cpSelectedIds.value.size === all.length ? new Set() : new Set(all)
}

function cpBuildContextBlock() {
  const lines = ['[COMPLIANCE CONTEXT]', '']
  for (const rec of cpSelectedList.value) {
    const statusLabel = (rec.status || 'unknown').toUpperCase()
    lines.push(`### ${rec.check_name} [${statusLabel}]`)
    if (rec.findings) lines.push(rec.findings.trim())
    if (rec.page_number != null) lines.push(`(Page ${rec.page_number})`)
    lines.push('')
  }
  lines.push('[END COMPLIANCE CONTEXT]')
  return lines.join('\n')
}

const CP_ANALYSIS_PROMPT = `--- Compliance Validation Instructions ---
You are a contract compliance expert. For each compliance issue listed in the context above:

1. **Validate the issue** — Confirm whether the finding is accurate based on the contract text. Note if the concern is well-founded, overstated, or already addressed elsewhere.
2. **Root cause** — Briefly identify why the issue exists (missing clause, vague language, conflicting terms, regulatory gap, etc.).
3. **Recommended fix** — Provide a concrete, actionable resolution:
   - Exact clause language to add or amend (where applicable)
   - Negotiation point to raise with the counterparty
   - Process or procedural change if no contractual fix is needed
4. **Priority** — Rate each fix: 🔴 Critical (must fix before signing) / 🟡 Moderate (should fix) / 🟢 Minor.

Be concise and practical. Reference the specific check name for each recommendation.`

/** Review agent: guideline context, compliance rows, or both in one send (same UX as Guidelines). */
async function reviewSendContextPack(options = {}) {
  const {
    overrideQuery = null,
    fromGuidelineRun = false,
    fromComplianceRun = false,
  } = options
  const hasGl = glSelectedKeys.value.size > 0
  const hasCp = cpSelectedIds.value.size > 0
  if (!hasGl && !hasCp) return

  const query = String(overrideQuery != null ? overrideQuery : userInput.value).trim()
  const note = glInstruction.value.trim()
  const parts = []
  if (hasGl) {
    parts.push(glBuildContextBlock(), GL_ANALYSIS_PROMPT)
    if (note) parts.push(`--- Additional Instructions ---\n${note}`)
  }
  if (hasCp) {
    parts.push(cpBuildContextBlock(), CP_ANALYSIS_PROMPT)
  }
  if (query) parts.push(`--- User question ---\n${query}`)

  const fIds = [...new Set(selectedReviewFindingIds.value || [])]
  const rIds = [...new Set(selectedReviewRecommendationIds.value || [])]
  const backendMsg = formatReviewBackendMessage(parts.join('\n\n'), fIds, rIds)

  let displayQuery = query
  if (!displayQuery) {
    if (note && hasGl) displayQuery = note
    else {
      const bits = []
      if (hasGl) bits.push(`Guidelines: ${glSelectedList.value.map((s) => s.title).join(', ')}`)
      if (hasCp) bits.push(`Compliance: ${cpSelectedList.value.map((r) => r.check_name).join(', ')}`)
      displayQuery = bits.join(' · ') || 'Context review'
    }
  }

  const c = contract.value
  const userMsg = { role: 'user', content: displayQuery }
  if (fromGuidelineRun) userMsg.fromGuidelineRun = true
  if (fromComplianceRun) userMsg.fromComplianceRun = true
  if (hasGl) {
    userMsg.guidelineSections = glSelectedList.value.map((s) => ({
      key: s.key,
      title: s.title,
      abbr: s.abbr,
      data: c?.[`guideline_${s.key}`] ?? null,
    }))
    if (note) userMsg.guidelineNote = note
  }
  if (hasCp) {
    userMsg.complianceChecks = cpSelectedList.value.map((r) => ({
      id: r.id,
      check_name: r.check_name,
      status: r.status,
      findings: r.findings ?? null,
      page_number: r.page_number ?? null,
    }))
  }

  chatMessages.value.review.push(userMsg)
  userInput.value = ''
  if (hasGl) {
    glInstruction.value = ''
    glConfirmMode.value = false
    glPickerOpen.value = false
    glSelectedKeys.value = new Set()
  }
  if (hasCp) {
    cpPickerOpen.value = false
    cpSelectedIds.value = new Set()
  }

  reviewTyping.value = true
  reviewTodos.value = []
  try {
    const ws = await ensureReviewSocket()
    ws.send(JSON.stringify(buildReviewWsPayload(backendMsg)))
    nextTick(scrollChatToBottom)
  } catch (e) {
    reviewTyping.value = false
    clearReviewPlanUI()
    chatMessages.value.review.push({ role: 'assistant', content: `**Connection error:** ${e?.message || e}`, markdown: true })
    nextTick(scrollChatToBottom)
  }
}

async function cpConfirmSend(overrideQuery = null, options = {}) {
  if (cpSelectedIds.value.size === 0) return
  await reviewSendContextPack({
    overrideQuery: overrideQuery ?? userInput.value,
    fromComplianceRun: !!options.fromRun,
  })
}

async function runSelectedComplianceNow() {
  if (reviewTyping.value) return
  if (cpSelectedIds.value.size === 0) return
  cpPickerOpen.value = false
  const directQuery = `Validate compliance issues and generate fixes for: ${cpSelectedList.value.map((r) => r.check_name).join(', ')}`
  await reviewSendContextPack({ overrideQuery: directQuery, fromComplianceRun: true })
}

const graphUserInput = ref('')
const showGraphChatPanel = ref(false)
const newAgentName = ref('')
const complaintLibrary = ref([])
const showComplaintModal = ref(false)
const selectedComplaints = ref([])
/** Compliance tab: filter long complaint lists */
const complianceRecordsFilter = ref('')
/** Outcome filter for compliance list (mirrors contract lifecycle stepper UX). */
const complianceOutcomeFilter = ref('all')
const COMPLIANCE_VIEW_STEPS = [
  { value: 'all', label: 'All checks', circleBg: 'bg-slate-500', labelColor: 'text-slate-600 dark:text-[var(--clm-text)]' },
  { value: 'failed', label: 'Failed', circleBg: 'bg-red-500', labelColor: 'text-red-600 dark:text-red-300' },
  { value: 'warning', label: 'Warning', circleBg: 'bg-amber-500', labelColor: 'text-amber-600 dark:text-amber-300' },
  { value: 'passed', label: 'Passed', circleBg: 'bg-emerald-600', labelColor: 'text-emerald-600 dark:text-emerald-400' },
]
const complianceFilterStepIndex = computed(() =>
  COMPLIANCE_VIEW_STEPS.findIndex((s) => s.value === complianceOutcomeFilter.value),
)
const nextComplianceViewStep = computed(() => {
  const i = complianceFilterStepIndex.value
  if (i < 0 || i >= COMPLIANCE_VIEW_STEPS.length - 1) return null
  return COMPLIANCE_VIEW_STEPS[i + 1]
})
function complianceConnectorSegmentLabel(rightStepIndex) {
  const steps = COMPLIANCE_VIEW_STEPS
  const target = steps[rightStepIndex]
  const targetName = target?.label ?? 'next'
  const cur = complianceFilterStepIndex.value
  const left = rightStepIndex - 1
  if (cur < 0) return `Before “${targetName}”`
  if (cur >= rightStepIndex) return `Completed: “${targetName}”`
  if (cur === left) return `Next: “${targetName}”`
  return `Later: “${targetName}”`
}
function complianceConnectorSegmentLabelClass(rightStepIndex) {
  const cur = complianceFilterStepIndex.value
  const left = rightStepIndex - 1
  if (cur < 0) return 'text-[var(--clm-text-muted)]'
  if (cur >= rightStepIndex) return 'text-emerald-600 dark:text-emerald-400'
  if (cur === left) return 'text-[var(--clm-brand)]'
  return 'text-[var(--clm-text-muted)]'
}
function setComplianceOutcomeFilter(value) {
  complianceOutcomeFilter.value = value
}
function advanceComplianceView() {
  const next = nextComplianceViewStep.value
  if (next) complianceOutcomeFilter.value = next.value
}
/** Normalize API/LLM outcome for filtering (handles fail / failed). */
function complianceRecordOutcomeKey(rec) {
  const s = (rec.status || '').toLowerCase()
  if (s === 'fail') return 'failed'
  return s
}

/** Dot, label, and findings-panel accent classes for compliance rows (design-only). */
function complianceRecordVisuals(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'passed') {
    return {
      dot: 'bg-emerald-500 ring-2 ring-emerald-500/25',
      label: 'text-emerald-700 dark:text-emerald-400',
      panel: 'border-l-[3px] border-l-emerald-500/55 bg-emerald-500/[0.04]',
    }
  }
  if (s === 'warning') {
    return {
      dot: 'bg-amber-400 ring-2 ring-amber-400/30',
      label: 'text-amber-700 dark:text-amber-400',
      panel: 'border-l-[3px] border-l-amber-400/60 bg-amber-400/[0.06]',
    }
  }
  if (s === 'fail' || s === 'failed') {
    return {
      dot: 'bg-red-500 ring-2 ring-red-500/25',
      label: 'text-red-700 dark:text-red-400',
      panel: 'border-l-[3px] border-l-red-500/55 bg-red-500/[0.04]',
    }
  }
  return {
    dot: 'bg-slate-400 ring-2 ring-slate-400/20 dark:bg-slate-500',
    label: 'text-slate-600 dark:text-slate-400',
    panel: 'border-l-[3px] border-l-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/90',
  }
}
const complianceRerunLoading = ref(false)

async function rerunComplianceChecks() {
  const vid = primaryVersionId.value
  if (!vid || complianceRerunLoading.value) return
  complianceRerunLoading.value = true
  try {
    await axios.post(`/api/contracts/${contractId}/compliance/recompute`, { version_id: vid })
    await reloadContract()
    toast('Compliance checks updated.')
  } catch (e) {
    const d = e?.response?.data?.detail
    const msg = Array.isArray(d) ? d.map((x) => x.msg || x).join(' ') : (d || e?.message || 'Re-run failed.')
    swalError(msg)
  } finally {
    complianceRerunLoading.value = false
  }
}

/** Compliance / complaint rows for the selected working document version (LLM checks are stored per version). */
const complianceRecordsForVersion = computed(() => {
  const list = contract.value?.compliance_records || []
  const vid = primaryVersionId.value
  if (!vid) return []
  return list.filter((rec) => Number(rec.document_version_id) === Number(vid))
})

const filteredComplianceRecords = computed(() => {
  let list = complianceRecordsForVersion.value
  const outcome = complianceOutcomeFilter.value
  if (outcome && outcome !== 'all') {
    list = list.filter((rec) => complianceRecordOutcomeKey(rec) === outcome)
  }
  const q = complianceRecordsFilter.value.trim().toLowerCase()
  if (!q) return list
  return list.filter((rec) => {
    const name = String(rec.check_name || '').toLowerCase()
    const findings = String(rec.findings || '').toLowerCase()
    const status = String(rec.status || '').toLowerCase()
    const page = rec.page_number != null ? String(rec.page_number) : ''
    const cidx = rec.chunk_index != null ? String(rec.chunk_index) : ''
    return name.includes(q) || findings.includes(q) || status.includes(q) || page.includes(q) || cidx.includes(q)
  })
})

const complianceOutcomeCounts = computed(() => {
  const rows = complianceRecordsForVersion.value
  const out = { passed: 0, warning: 0, failed: 0, other: 0, total: rows.length }
  for (const rec of rows) {
    const k = complianceRecordOutcomeKey(rec)
    if (k === 'passed') out.passed++
    else if (k === 'warning') out.warning++
    else if (k === 'failed') out.failed++
    else out.other++
  }
  return out
})

const compliancePassRatePercent = computed(() => {
  const { passed, total } = complianceOutcomeCounts.value
  if (!total) return 0
  return Math.round((passed / total) * 100)
})

/** Compliance tab list ordering: issues first, A–Z, or status groups. */
const complianceListSort = ref('priority')

const complianceDisplayRecords = computed(() => {
  const list = [...filteredComplianceRecords.value]
  const sort = complianceListSort.value
  const rank = (rec) => {
    const k = complianceRecordOutcomeKey(rec)
    if (k === 'failed') return 0
    if (k === 'warning') return 1
    if (k === 'passed') return 2
    return 3
  }
  if (sort === 'name') {
    list.sort((a, b) => String(a.check_name || '').localeCompare(String(b.check_name || '')))
  } else if (sort === 'page') {
    list.sort((a, b) => {
      const pa = a.page_number != null ? Number(a.page_number) : Infinity
      const pb = b.page_number != null ? Number(b.page_number) : Infinity
      if (pa !== pb) return pa - pb
      return String(a.check_name || '').localeCompare(String(b.check_name || ''))
    })
  } else {
    list.sort((a, b) => rank(a) - rank(b) || String(a.check_name || '').localeCompare(String(b.check_name || '')))
  }
  return list
})

function complianceExpandAllFindings() {
  for (const rec of complianceDisplayRecords.value) {
    if (rec.findings) rec.isOpen = true
  }
}
function complianceCollapseAllFindings() {
  for (const rec of complianceDisplayRecords.value) {
    if (rec.findings) rec.isOpen = false
  }
}
// ── Contract Status Stepper (aligned with Kanban + PATCH /api/contracts/:id/status) ──
const CONTRACT_STATUS_STEPS_ALL = [
  { value: 'draft', label: 'Draft', circleBg: 'bg-slate-500', labelColor: 'text-slate-600 dark:text-[var(--clm-text)]' },
  { value: 'review', label: 'Review', circleBg: 'bg-amber-500', labelColor: 'text-amber-600 dark:text-amber-300' },
  { value: 'redraft', label: 'Redraft', circleBg: 'bg-orange-500', labelColor: 'text-orange-600 dark:text-orange-300' },
  { value: 'approved', label: 'Approval', circleBg: 'bg-teal-600', labelColor: 'text-teal-600 dark:text-teal-300' },
  { value: 'signing', label: 'Signing', circleBg: 'bg-violet-600', labelColor: 'text-violet-600 dark:text-violet-300' },
  { value: 'active', label: 'Signed', circleBg: 'bg-emerald-600', labelColor: 'text-emerald-600 dark:text-emerald-400' },
  { value: 'expired', label: 'Expired', circleBg: 'bg-amber-700', labelColor: 'text-amber-700 dark:text-amber-200' },
  { value: 'terminated', label: 'Terminated', circleBg: 'bg-red-600', labelColor: 'text-red-600 dark:text-red-300' },
]
const CONTRACT_STATUS_STEPS_CORE = CONTRACT_STATUS_STEPS_ALL.filter(
  (st) => st.value !== 'expired' && st.value !== 'terminated',
)
/** Expired/terminated steps hidden unless this record is already in that state (set via Kanban drag). */
const contractStatusSteps = computed(() => {
  const st = (contract.value?.status || '').toLowerCase()
  const steps = [...CONTRACT_STATUS_STEPS_CORE]
  if (st === 'expired') {
    steps.push(CONTRACT_STATUS_STEPS_ALL.find((x) => x.value === 'expired'))
  } else if (st === 'terminated') {
    steps.push(CONTRACT_STATUS_STEPS_ALL.find((x) => x.value === 'terminated'))
  }
  return steps
})
/** Index of current status in the visible stepper, or -1 if unknown. */
const contractStatusStepIndex = computed(() => {
  const s = (contract.value?.status || '').toLowerCase()
  return contractStatusSteps.value.findIndex((st) => st.value === s)
})
/** Next stage in the visible timeline (single-step advance for primary CTA). */
const nextContractStatusStep = computed(() => {
  const steps = contractStatusSteps.value
  const i = contractStatusStepIndex.value
  if (i < 0 || i >= steps.length - 1) return null
  return steps[i + 1]
})
/** Label for the connector entering step index `rightStepIndex` (between left = right-1 and right). */
function connectorSegmentLabel(rightStepIndex) {
  const steps = contractStatusSteps.value
  const target = steps[rightStepIndex]
  const targetName = target?.label ?? 'next stage'
  const cur = contractStatusStepIndex.value
  const left = rightStepIndex - 1
  if (cur < 0) return `Before “${targetName}”`
  if (cur >= rightStepIndex) return `Completed: “${targetName}”`
  if (cur === left) return `Next: “${targetName}”`
  return `Later: “${targetName}”`
}
function connectorSegmentLabelClass(rightStepIndex) {
  const cur = contractStatusStepIndex.value
  const left = rightStepIndex - 1
  if (cur < 0) return 'text-[var(--clm-text-muted)]'
  if (cur >= rightStepIndex) return 'text-emerald-600 dark:text-emerald-400'
  if (cur === left) return 'text-[var(--clm-brand)]'
  return 'text-[var(--clm-text-muted)]'
}
const updatingStatus = ref(false)

/** Open the matching agent chat when lifecycle enters Review / Redraft or Draft. */
function applyAgentForContractStatus(statusRaw) {
  const s = (statusRaw || '').toLowerCase()
  if (s === 'review') {
    selectedAgent.value = 'review'
    showChat.value = true
    return
  }
  if (s === 'redraft') {
    selectedAgent.value = 'draft'
    showChat.value = true
  }
}

async function setContractStatus(status) {
  if (!contract.value || updatingStatus.value) return
  if (contract.value.status === status) return
  updatingStatus.value = true
  try {
    const { data } = await axios.patch(`/api/contracts/${contractId}/status`, { status })
    contract.value.status = data.status
    if (!['review', 'redraft', 'draft'].includes(status.toLowerCase()) && showChat.value) {
      showChat.value = false
      agentChatFullscreen.value = false
    }
    toast(`Status updated to ${status}.`)
    if (status.toLowerCase() === 'signing') {
      selectTab('overview')
      await nextTick()
      await nextTick()
      const el = overviewSignersSectionRef.value
      if (el && typeof el.scrollIntoView === 'function') {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        el.focus({ preventScroll: true })
      }
    }
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to update status.')
  } finally {
    updatingStatus.value = false
  }
}

async function advanceToNextContractStatus() {
  const next = nextContractStatusStep.value
  if (!next) return
  await setContractStatus(next.value)
}

const showMilestoneModal = ref(false)
const isSubmittingMilestone = ref(false)

// ── Add Signer Modal ──────────────────────────────────────────────────────────
const showAddSignerModal = ref(false)
const signerSearch = ref('')
const signerSearchLoading = ref(false)
const masterSignerResults = ref([])
const isAddingSignerLoading = ref(false)
const newSignerForm = ref({ name: '', email: '', organization: '' })

function openAddSignerModal() {
  signerSearch.value = ''
  masterSignerResults.value = []
  newSignerForm.value = { name: '', email: '', organization: '' }
  showAddSignerModal.value = true
}

let signerSearchTimer = null
async function searchMasterSigners() {
  const q = signerSearch.value.trim()
  if (q.length < 2) { masterSignerResults.value = []; return }
  clearTimeout(signerSearchTimer)
  signerSearchTimer = setTimeout(async () => {
    signerSearchLoading.value = true
    try {
      const { data } = await axios.get('/api/master-signers/', { params: { search: q } })
      masterSignerResults.value = data || []
    } catch { masterSignerResults.value = [] }
    finally { signerSearchLoading.value = false }
  }, 300)
}

async function selectMasterSigner(ms) {
  if (!selectedVersion.value) return
  isAddingSignerLoading.value = true
  try {
    await axios.post(`/api/versions/${selectedVersion.value.id}/signers`, { master_signer_id: ms.id })
    await reloadContract()
    showAddSignerModal.value = false
    toast(`${ms.name} added as signer.`)
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to add signer.')
  } finally { isAddingSignerLoading.value = false }
}

async function createAndAddSigner() {
  const { name, email, organization } = newSignerForm.value
  if (!name.trim() || !email.trim()) return
  if (!selectedVersion.value) return
  isAddingSignerLoading.value = true
  try {
    let ms
    try {
      const res = await axios.post('/api/master-signers/', { name: name.trim(), email: email.trim(), organization: organization.trim() || null })
      ms = res.data
    } catch (e) {
      if (e?.response?.status === 409) {
        const res = await axios.get('/api/master-signers/', { params: { search: email.trim() } })
        ms = (res.data || []).find(s => s.email === email.trim())
        if (!ms) throw e
      } else throw e
    }
    await axios.post(`/api/versions/${selectedVersion.value.id}/signers`, { master_signer_id: ms.id })
    await reloadContract()
    showAddSignerModal.value = false
    toast(`${ms.name} added as signer.`)
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to add signer.')
  } finally { isAddingSignerLoading.value = false }
}

async function removeSignerFromVersion(vsId) {
  if (!confirm('Remove this signer from the version?')) return
  try {
    await axios.delete(`/api/version-signers/${vsId}`)
    await reloadContract()
    toast('Signer removed.')
  } catch (e) {
    swalError(e?.response?.data?.detail || 'Failed to remove signer.')
  }
}
const newMilestone = ref({
  title: '',
  description: '',
  due_date: new Date().toISOString().split('T')[0]
})

// Contract scoring (LLM result)
const scoringData = ref(null)
const scoringLoading = ref(false)
const scoringError = ref(null)
const showScoringRaw = ref(false)
const scoringTriggering = ref(false)
/** True while server-side scoring thread is running (WS or inferred); unlike scoringTriggering (manual POST). */
const scoringBackgroundRunning = ref(false)

const fetchScoring = async () => {
  if (!contract.value?.id) return
  scoringLoading.value = true
  scoringError.value = null
  try {
    const vid = primaryVersionId.value
    const params = {}
    if (vid != null) params.version_id = vid
    const response = await axios.get(`/api/contracts/${contract.value.id}/scoring`, { params })
    scoringData.value = response.data?.result_json ?? null
    if (scoringData.value?.validation_results?.length) {
      scoringData.value.validation_results.forEach(vr => { vr._open = false })
    }
  } catch (err) {
    if (err.response?.status === 404) {
      scoringData.value = null
      scoringError.value = null
    } else {
      scoringError.value = err.response?.data?.detail || err.message || 'Failed to load contract scoring.'
    }
  } finally {
    scoringLoading.value = false
  }
}

const triggerScoring = async () => {
  if (!contract.value?.id) return
  scoringTriggering.value = true
  scoringError.value = null
  try {
    const vid = primaryVersionId.value
    const params = {}
    if (vid != null) params.version_id = vid
    const response = await axios.post(`/api/contracts/${contract.value.id}/scoring`, null, { params })
    const payload = response.data?.result_json ?? response.data
    scoringData.value = payload && typeof payload === 'object' ? payload : null
    if (scoringData.value?.validation_results?.length) {
      scoringData.value.validation_results.forEach(vr => { vr._open = false })
    }
  } catch (err) {
    scoringError.value = err.response?.data?.detail || err.message || 'Scoring failed.'
  } finally {
    scoringTriggering.value = false
  }
}

const onGuidelineSaved = (updated) => {
  if (!contract.value || !updated) return
  const fields = [
    'guideline_framework_slug', 'guideline_framework_title', 'guideline_snapshot',
    'guideline_financial_limits', 'guideline_mandatory_clauses', 'guideline_technical_standards',
    'guideline_compliance_requirements', 'guideline_contractor_eligibility',
    'guideline_work_execution_standards', 'guideline_measurement_payment',
    'guideline_contract_administration', 'guideline_defect_liability',
    'guideline_documentation_requirements', 'guideline_decision_thresholds',
    'guideline_validation_weights', 'guideline_critical_issues',
  ]
  for (const f of fields) {
    if (f in updated) contract.value[f] = updated[f]
  }
}

// ── Guideline → Review Agent ──────────────────────────────────────────────

function _flattenGuidelineValue(val, depth = 0) {
  const pad = '  '.repeat(depth)
  if (Array.isArray(val)) {
    return val.map((item) =>
      typeof item === 'object' && item !== null
        ? `${pad}- \n${_flattenGuidelineValue(item, depth + 1)}`
        : `${pad}- ${item}`
    ).join('\n')
  }
  if (val !== null && typeof val === 'object') {
    return Object.entries(val).map(([k, v]) => {
      const label = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
      if (typeof v === 'object' && v !== null) {
        return `${pad}${label}:\n${_flattenGuidelineValue(v, depth + 1)}`
      }
      return `${pad}${label}: ${v}`
    }).join('\n')
  }
  return `${pad}${val}`
}

function _formatGuidelineContext({ frameworkTitle, frameworkSlug, sections }) {
  const header = frameworkTitle || frameworkSlug || 'Contract Review Guideline'
  const lines = [
    `[GUIDELINE CONTEXT — ${header}]`,
    '',
  ]
  for (const [key, data] of Object.entries(sections)) {
    const title = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    lines.push(`### ${title}`)
    lines.push(_flattenGuidelineValue(data))
    lines.push('')
  }
  lines.push('[END GUIDELINE CONTEXT]')
  lines.push('')
  lines.push('Review the contract against the guideline sections above and flag any gaps or non-compliance.')
  return lines.join('\n')
}

const onGuidelineSendToAgent = ({ sections }) => {
  // Pre-load the selected sections as chip widgets in the review chat
  glSelectedKeys.value = new Set(Object.keys(sections))
  glPickerOpen.value   = false
  glConfirmMode.value  = false
  userInput.value      = ''
  // Open review agent chat
  selectedAgent.value  = 'review'
  showChat.value       = true
  nextTick(() => {
    document.querySelector('.clm-agent-input')?.focus()
  })
}

const selectTab = (tab) => {
  activeTab.value = tab
  if (
    (tab === 'scoring' || tab === 'compliance') &&
    !scoringData.value &&
    !scoringLoading.value
  ) {
    fetchScoring()
  }
}

const scoreColor = (score) => {
  if (typeof score !== 'number') return 'text-gray-600 dark:text-gray-400'
  if (score >= 80) return 'text-green-600 dark:text-green-400'
  if (score >= 60) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

const statusBadgeClass = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'PASS' || s === 'APPROVE' || s === 'COMPLIANT') return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
  if (s === 'CONDITIONAL' || s === 'CONDITIONALLY_APPROVED' || s === 'PARTIAL') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
  if (s === 'FAIL' || s === 'NON_COMPLIANT') return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

// Scoring accordions: key -> true/false (replace object so reactivity triggers)
const openScoringAccordions = ref({})
const toggleScoringAccordion = (key) => {
  const next = { ...openScoringAccordions.value, [key]: !openScoringAccordions.value[key] }
  openScoringAccordions.value = next
}

const accordionRecTitle = (rec, index) => {
  const text = typeof rec === 'string' ? rec : (rec.recommendation || rec.category || '')
  if (!text) return `Recommendation ${index + 1}`
  return text.length > 80 ? text.slice(0, 80).trim() + '…' : text
}

/** Group findings by category and pick worst status for merged accordion */
function mergedFindingsByCategory(findings) {
  if (!findings?.length) return []
  const byCategory = {}
  const orderOf = (val) => {
    const s = (val || '').toUpperCase()
    if (/NON_COMPLIANT|CRITICAL|FAIL/.test(s)) return 3
    if (/PARTIAL|HIGH/.test(s)) return 2
    if (/MEDIUM/.test(s)) return 1
    return 0
  }
  for (const f of findings) {
    const cat = (f.category || 'Finding').trim() || 'Finding'
    if (!byCategory[cat]) {
      byCategory[cat] = { category: cat, items: [], worstStatus: null, worstOrder: -1 }
    }
    byCategory[cat].items.push(f)
    const statusVal = f.compliance || f.severity || 'PARTIAL'
    const order = orderOf(statusVal)
    if (order > byCategory[cat].worstOrder) {
      byCategory[cat].worstOrder = order
      byCategory[cat].worstStatus = statusVal
    } else if (byCategory[cat].worstStatus == null) {
      byCategory[cat].worstStatus = statusVal
    }
  }
  return Object.values(byCategory).map(g => ({
    ...g,
    worstStatus: g.worstStatus || 'PARTIAL'
  }))
}

const addMilestone = async () => {
  isSubmittingMilestone.value = true
  try {
    const payload = {
      ...newMilestone.value,
      due_date: new Date(newMilestone.value.due_date).toISOString()
    }
    await axios.post(`/api/contracts/${contractId}/milestones`, payload)
    
    // Refresh contract data to show new milestone
    const response = await axios.get(`/api/contracts/${contractId}`)
    contract.value = response.data
    // Initialize isOpen for milestones
    if (contract.value.milestones) {
      contract.value.milestones = contract.value.milestones.map(m => ({ ...m, isOpen: false }))
    }
    
    showMilestoneModal.value = false
    // Reset form
    newMilestone.value = {
      title: '',
      description: '',
      due_date: new Date().toISOString().split('T')[0]
    }
  } catch (error) {
    console.error('Failed to add milestone:', error)
    swalError('Failed to add milestone')
  } finally {
    isSubmittingMilestone.value = false
  }
}

const fetchComplaints = async () => {
  try {
    const response = await axios.get('/api/complaints')
    // Provide all complaints from the database without de-duplication
    // to ensure user can see and select any historical complaint.
    complaintLibrary.value = response.data.map(item => ({
      ...item,
      showDetails: false // Initialize the accordion state for the modal
    }))
  } catch (error) {
    console.error('Failed to fetch complaints library:', error)
  }
}

const toggleComplaintSelection = (complaint) => {
  const index = selectedComplaints.value.findIndex(c => c.id === complaint.id)
  if (index > -1) {
    selectedComplaints.value.splice(index, 1)
  } else {
    selectedComplaints.value.push(complaint)
  }
}

const isComplaintSelected = (id) => selectedComplaints.value.some(c => c.id === id)

const applySelectedComplaints = () => {
  if (selectedComplaints.value.length === 0) return
  
  const names = selectedComplaints.value.map(c => c.check_name).join(', ')
  const userMsg = `Apply following complaints: ${names}`
  
  chatMessages.value.complaints.push({ role: 'user', content: userMsg })
  
  // Create assistant response with accordions
  const complaintsData = selectedComplaints.value.map(c => ({
    ...c,
    isOpen: false
  }))
  
  chatMessages.value.complaints.push({
    role: 'assistant',
    content: 'Applied the following complaints from database:',
    isAccordion: true,
    complaints: complaintsData
  })
  
  showComplaintModal.value = false
  selectedComplaints.value = []
  
  nextTick(() => {
    const el = document.getElementById('chat-messages')
    if (el) el.scrollTop = el.scrollHeight
  })
}

const applyComplaint = (complaint) => {
  chatMessages.value.complaints.push({ role: 'user', content: `Apply complaint: ${complaint.check_name}` })
  
  chatMessages.value.complaints.push({
    role: 'assistant',
    content: 'Applied the following complaint from database:',
    isAccordion: true,
    complaints: [{ ...complaint, isOpen: true }]
  })
  
  nextTick(() => {
    const el = document.getElementById('chat-messages')
    if (el) el.scrollTop = el.scrollHeight
  })
}

const availableAgents = ref([
  { id: 'review', name: 'Review Agent' },
  { id: 'draft', name: 'Draft Agent' },
  { id: 'compare', name: 'Document comparison' },
  { id: 'complaints', name: 'Complaints Agent' },
  { id: 'graph', name: 'Graph QA' },
])

// Default active agents: Review, Compliance, Document Comparison.
// Draft Agent and Graph QA are available but inactive by default — users can enable them via Configure Agents.
const _allActiveAgents = ref([
  { id: 'review', name: 'Review Agent' },
  { id: 'draft', name: 'Draft Agent' },
  { id: 'compare', name: 'Document comparison' },
])
const activeAgents = computed(() => {
  const s = (contract.value?.status || '').toLowerCase()
  if (s === 'review') return _allActiveAgents.value.filter(a => a.id !== 'draft')
  return _allActiveAgents.value
})

watch(
  () => contract.value?.status,
  (newSt, oldSt) => {
    if (newSt == null || !contract.value) return
    const n = String(newSt).toLowerCase()
    const o = oldSt != null ? String(oldSt).toLowerCase() : ''
    if (n === o) return
    applyAgentForContractStatus(newSt)
  },
)

const chatMessages = ref({
  review: [
    { role: 'assistant', content: 'Hello! I am your Review Agent. I can help you analyze this contract for potential risks, missing clauses, or compliance issues. What would you like me to check?' }
  ],
  draft: [
    {
      role: 'assistant',
      content:
        'I am the **Draft Agent**. I can suggest amendments or help you write new sections. Replies use **markdown** (headings, lists, clause blocks). I use your contract title, description, and stored text when available.',
      markdown: true,
    },
  ],
  compare: [
    {
      role: 'assistant',
      markdown: true,
      content:
        '**Document comparison** — pick **two versions** below (**A** = baseline, **B** = comparison). Ask a question (or send empty for a default summary). The assistant reads both PDFs/DOCX files on the server and answers with **Markdown tables** comparing Document A and Document B side by side.',
    },
  ],
  complaints: [
    { role: 'assistant', content: 'Complaints Agent here. I track dispute resolution and penalty clauses. If there are performance issues, I can help you identify the relevant contract terms.' }
  ],
  graph: [
    {
      role: 'assistant',
      markdown: true,
      content:
        'I answer questions about your **contract knowledge graph** (entities and relationships). Ask things like who the parties are, how concepts relate, or what a node is connected to. Replies support **markdown** (lists, code, emphasis).',
    },
  ],
})

const graphChatSocket = ref(null)
const lastGraphReplySignature = ref('')

/** Review agent: /ws/review — streams json_data (write_todos | model), then type "done" */
const reviewChatSocket = ref(null)
const reviewTodos = ref([])
/** Typing indicator for /ws/review (separate from isTyping so other tabs stay accurate) */
const reviewTyping = ref(false)

/** Draft agent: /ws/draft — same streaming envelope as review */
const draftChatSocket = ref(null)
const draftTyping = ref(false)
const draftTodos = ref([])

/** Document comparison: /ws/compare — streams json_data { name: model } */
const compareChatSocket = ref(null)

/** Document comparison: two version IDs from `contract.document_versions` (string for native `<select>`). */
const compareVersionAId = ref('')
const compareVersionBId = ref('')
const compareTyping = ref(false)

/** After every plan todo is completed while the draft stream is still open (Word build / reply). */
const draftRedlineFinalizing = computed(() => {
  if (!draftTyping.value) return false
  const todos = draftTodos.value
  if (!todos.length) return false
  return todos.every((t) => {
    const s = String(t.status || '').toLowerCase()
    return s === 'completed' || s === 'complete' || s === 'done'
  })
})

/** Todo texts for the DOCX progress widget (in_progress first, then pending). */
const draftTodoProgressLines = computed(() => {
  const todos = draftTodos.value
  if (!todos.length) return []
  const inProg = todos.filter((t) => String(t.status || '').toLowerCase() === 'in_progress')
  const pending = todos.filter((t) => String(t.status || '').toLowerCase() === 'pending')
  const lines = [...inProg, ...pending]
    .map((t) => String(t.content || '').trim())
    .filter(Boolean)
  return lines
})

watch(compareVersionAId, (a) => {
  if (a && compareVersionBId.value === a) compareVersionBId.value = ''
})

const sortedDocumentVersions = computed(() => {
  const list = contract.value?.document_versions || []
  return [...list].sort((a, b) => (a.version_number ?? 0) - (b.version_number ?? 0))
})

function formatVersionCompareLabel(v) {
  if (!v) return ''
  const bits = [`v${v.version_number}`]
  if (v.label) bits.push(v.label)
  if (v.file_type) bits.push(String(v.file_type).toUpperCase())
  if (v.is_latest) bits.push('latest')
  return bits.join(' · ')
}

const selectedCompareVersionA = computed(() => {
  const raw = compareVersionAId.value
  if (!raw) return null
  const id = Number(raw)
  return sortedDocumentVersions.value.find((v) => v.id === id) || null
})

const selectedCompareVersionB = computed(() => {
  const raw = compareVersionBId.value
  if (!raw) return null
  const id = Number(raw)
  return sortedDocumentVersions.value.find((v) => v.id === id) || null
})

/** Shrink version previews while compare reply is loading/streaming so chat has more space. */
const comparePreviewCompact = computed(() => {
  if (selectedAgent.value !== 'compare') return false
  if (compareTyping.value) return true
  const msgs = chatMessages.value.compare
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i]
    if (m?.role === 'assistant' && m.compareStreaming) return true
  }
  return false
})

/** User can hide PDF thumbs; streaming compact only applies when thumbs are visible. */
const compareDocPreviewsVisible = ref(false)
const compareSetupExpanded = ref(false)
/** Hide the entire compare top workspace so chat uses full height; restore via slim bar. */
const compareTopPanelHidden = ref(false)
const comparePromptPresets = [
  'Summarize all material changes in a table.',
  'List financial and payment term differences.',
  'Highlight risk, liability, and penalty changes.',
  'Show deleted clauses and newly added clauses.',
]

const canRunCompareNow = computed(() => {
  return !!compareVersionAId.value && !!compareVersionBId.value && compareVersionAId.value !== compareVersionBId.value
})

function swapCompareVersions() {
  if (!compareVersionAId.value || !compareVersionBId.value) return
  const a = compareVersionAId.value
  compareVersionAId.value = compareVersionBId.value
  compareVersionBId.value = a
}

function resetCompareSelection() {
  compareVersionAId.value = ''
  compareVersionBId.value = ''
  compareDocPreviewsVisible.value = false
}

const compareThumbCompact = computed(
  () => comparePreviewCompact.value && compareDocPreviewsVisible.value
)

const comparePanelDense = computed(() => comparePreviewCompact.value)

/** Full-screen overlay for the agent chat (all agent tabs). Cleared when chat closes. */
const agentChatFullscreen = ref(false)

function onAgentChatFullscreenKeydown(e) {
  if (e.key !== 'Escape') return
  if (!agentChatFullscreen.value) return
  e.preventDefault()
  agentChatFullscreen.value = false
}

watch(agentChatFullscreen, (on) => {
  document.body.style.overflow = on ? 'hidden' : ''
  document.documentElement.classList.toggle('clm-agent-chat-fs', !!on)
  if (on) window.addEventListener('keydown', onAgentChatFullscreenKeydown, true)
  else window.removeEventListener('keydown', onAgentChatFullscreenKeydown, true)
})

/** Right offset when agent chat is docked so preview does not sit under the rail. */
const documentPreviewChatReservePx = computed(() => {
  if (!showChat.value || agentChatFullscreen.value || !isLgChatDock.value) return 0
  return chatWidth.value
})

/**
 * Width of the document preview slide-over (must match ``documentPreviewDrawerShellStyle`` width math)
 * so we can reserve the same space for main content and keep row actions (e.g. compliance eye) visible.
 */
const documentPreviewDrawerWidthPx = computed(() => {
  if (!documentPreviewDrawerOpen.value) return 0
  const vw = viewportWidth.value
  const reserve = documentPreviewChatReservePx.value
  const gutter = 16
  const available = Math.max(260, vw - reserve - gutter)
  let fraction
  if (vw < 480) fraction = 0.92
  else if (vw < 640) fraction = 0.8
  else if (vw < 1024) fraction = 0.65
  else if (vw < 1280) fraction = 0.55
  else if (vw < 1536) fraction = 0.48
  else fraction = 0.42
  let softCap
  if (vw < 640) softCap = 520
  else if (vw < 1024) softCap = 600
  else if (vw < 1280) softCap = 680
  else if (vw < 1536) softCap = 740
  else softCap = 800
  const widthPx = Math.max(300, Math.round(Math.min(available * fraction, softCap, available)))
  const chunkExtra = contractPreviewChunksDrawerOpen.value ? contractPreviewChunksDrawerWidth.value : 0
  return widthPx + chunkExtra
})

/** Reserve horizontal space so the fixed chat rail and/or document preview do not cover contract content */
const contractPageChatInset = computed(() => {
  if (agentChatFullscreen.value) return {}
  let pr = 0
  if (showChat.value && isLgChatDock.value) {
    pr += chatWidth.value + 16
  }
  if (documentPreviewDrawerOpen.value && activeTab.value !== 'graph') {
    pr += documentPreviewDrawerWidthPx.value + 12
  }
  return pr > 0 ? { paddingRight: `${pr}px` } : {}
})

/** Docked (non-fullscreen) positioning: wide screens = right rail; narrow = full-width strip */
const dockedAgentChatShellClass = computed(() => {
  if (agentChatFullscreen.value) return ''
  const base =
    'bottom-0 z-[210] border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-2xl dark:bg-[var(--clm-bg-page)]'
  if (isLgChatDock.value) {
    return `${base} right-0 top-24 rounded-l-2xl rounded-r-none transition-[width] duration-150 ease-out`
  }
  return `${base} clm-agent-chat-shell--fullbleed left-0 right-0 top-16 max-h-[100dvh] w-full max-w-[100vw] sm:top-[4.5rem]`
})

const dockChatShellStyle = computed(() => {
  if (agentChatFullscreen.value) return {}
  if (isLgChatDock.value) return { width: `${chatWidth.value}px` }
  return { width: '100%', maxWidth: '100vw' }
})

/**
 * Fluid preview width: uses most of the space left of the docked chat (or full width minus gutter),
 * with breakpoints so large monitors get a wide panel without exceeding a comfortable cap.
 */
const documentPreviewDrawerShellStyle = computed(() => {
  const vw = viewportWidth.value
  const reserve = documentPreviewChatReservePx.value
  const gutter = 16
  const available = Math.max(260, vw - reserve - gutter)

  let fraction
  if (vw < 480) fraction = 0.92
  else if (vw < 640) fraction = 0.80
  else if (vw < 1024) fraction = 0.65
  else if (vw < 1280) fraction = 0.55
  else if (vw < 1536) fraction = 0.48
  else fraction = 0.42

  let softCap
  if (vw < 640) softCap = 520
  else if (vw < 1024) softCap = 600
  else if (vw < 1280) softCap = 680
  else if (vw < 1536) softCap = 740
  else softCap = 800

  const widthPx = Math.max(300, Math.round(Math.min(available * fraction, softCap, available)))
  const chunkExtra = contractPreviewChunksDrawerOpen.value ? contractPreviewChunksDrawerWidth.value : 0
  return {
    width: `${widthPx + chunkExtra}px`,
    right: `${reserve}px`,
  }
})

const documentPreviewPeekStyle = computed(() => ({
  right: `${documentPreviewChatReservePx.value}px`,
}))

/** Lock main agent chat field while an agent run is in flight (draft/review/graph/compare). */
const mainChatInputLocked = computed(() => {
  if (selectedAgent.value === 'review') return reviewTyping.value
  if (selectedAgent.value === 'draft') return draftTyping.value
  if (selectedAgent.value === 'compare') return compareTyping.value
  return isTyping.value
})

const mainChatSendDisabled = computed(() => {
  if (mainChatInputLocked.value) return true
  if (selectedAgent.value === 'compare') {
    const a = compareVersionAId.value
    const b = compareVersionBId.value
    return !a || !b || a === b
  }
  if (
    selectedAgent.value === 'review' &&
    (glSelectedKeys.value.size > 0 || cpSelectedIds.value.size > 0)
  ) {
    return false
  }
  return !userInput.value.trim()
})

/** Review chat: multi-select findings/recommendations from contract scoring (optional WS context) */
const reviewContextFullSpace = ref(false)
const reviewContextTab = ref('findings')
const selectedReviewFindingIds = ref([])
const selectedReviewRecommendationIds = ref([])

const selectedReviewFindingCount = computed(() => new Set(selectedReviewFindingIds.value || []).size)
const selectedReviewRecommendationCount = computed(() => new Set(selectedReviewRecommendationIds.value || []).size)
const selectedReviewContextCount = computed(() => selectedReviewFindingCount.value + selectedReviewRecommendationCount.value)

function truncateReviewLabel(text, max = 200) {
  const t = String(text || '').replace(/\s+/g, ' ').trim()
  if (!t) return ''
  return t.length > max ? `${t.slice(0, max).trim()}…` : t
}

const reviewSelectableFindings = computed(() => {
  const out = []
  const vrs = scoringData.value?.validation_results || []
  vrs.forEach((vr, vri) => {
    const agent = String(vr.agent_type || `validation_${vri}`).replace(/_/g, ' ')
    ;(vr.findings || []).forEach((f, fi) => {
      const text = String(f?.issue || f?.finding || '').trim()
      if (!text) return
      const id = `f-${vri}-${fi}`
      const cat = f?.category ? String(f.category).trim() : ''
      const status = f?.compliance || f?.severity || ''
      const prefix = [agent, cat, status].filter(Boolean).join(' · ')
      const preview = prefix ? `${prefix}: ${truncateReviewLabel(text, 180)}` : truncateReviewLabel(text, 200)
      out.push({ id, agent, category: cat, status, text, preview })
    })
  })
  return out
})

const reviewSelectableRecommendations = computed(() => {
  const out = []
  const vrs = scoringData.value?.validation_results || []
  vrs.forEach((vr, vri) => {
    const agent = String(vr.agent_type || `validation_${vri}`).replace(/_/g, ' ')
    ;(vr.recommendations || []).forEach((r, ri) => {
      const text = typeof r === 'string' ? r.trim() : String(r?.recommendation || r?.category || '').trim()
      if (!text) return
      const id = `r-${vri}-${ri}`
      const preview = `${agent}: ${truncateReviewLabel(text, 200)}`
      out.push({ id, agent, text, preview })
    })
  })
  return out
})

const allReviewFindingsSelected = computed(() => {
  const list = reviewSelectableFindings.value
  if (!list.length) return false
  const sel = new Set(selectedReviewFindingIds.value)
  return list.every((f) => sel.has(f.id))
})

const allReviewRecommendationsSelected = computed(() => {
  const list = reviewSelectableRecommendations.value
  if (!list.length) return false
  const sel = new Set(selectedReviewRecommendationIds.value)
  return list.every((r) => sel.has(r.id))
})

function selectAllReviewFindings() {
  selectedReviewFindingIds.value = reviewSelectableFindings.value.map((f) => f.id)
}

function selectAllReviewRecommendations() {
  selectedReviewRecommendationIds.value = reviewSelectableRecommendations.value.map((r) => r.id)
}

function toggleReviewFindingId(id) {
  const arr = selectedReviewFindingIds.value
  const i = arr.indexOf(id)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(id)
}

function toggleReviewRecommendationId(id) {
  const arr = selectedReviewRecommendationIds.value
  const i = arr.indexOf(id)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(id)
}

function clearReviewScoringSelection() {
  selectedReviewFindingIds.value = []
  selectedReviewRecommendationIds.value = []
}

function openReviewContextPanel() {
  reviewContextFullSpace.value = true
  if (!scoringData.value && !scoringLoading.value) fetchScoring()
}

function closeReviewContextPanel() {
  reviewContextFullSpace.value = false
}

function onMainChatInputPointer() {
  if (selectedAgent.value === 'review' || selectedAgent.value === 'draft') closeReviewContextPanel()
}

/** Mutates `lines` with --findings / --recommendation blocks (same shape as /ws/review). */
function appendFindingsAndRecommendationLines(lines, findingIds, recommendationIds) {
  const findings = reviewSelectableFindings.value.filter((x) => findingIds.includes(x.id))
  const recs = reviewSelectableRecommendations.value.filter((x) => recommendationIds.includes(x.id))
  if (findings.length) {
    lines.push('--findings')
    findings.forEach((f, i) => {
      const meta = [f.agent, f.category, f.status].filter(Boolean).join(' | ')
      lines.push(`${i + 1}. ${meta ? `[${meta}] ` : ''}${f.text}`)
    })
  }
  if (recs.length) {
    lines.push('--recommendation')
    recs.forEach((r, i) => {
      lines.push(`${i + 1}. [${r.agent}] ${r.text}`)
    })
  }
}

/**
 * Backend review WS message: labeled sections; user query is mandatory.
 * --findings / --recommendation blocks only when selections exist.
 */
function formatReviewBackendMessage(userQuery, findingIds, recommendationIds) {
  const q = String(userQuery || '').trim()
  const lines = []
  appendFindingsAndRecommendationLines(lines, findingIds, recommendationIds)
  lines.push('-- user query')
  lines.push(q)
  return lines.join('\n')
}

const DRAFT_CONTEXT_CHAR_CAP = 120_000

function formatDraftBackendMessage(userQuery, findingIds, recommendationIds) {
  const q = String(userQuery || '').trim()
  const c = contract.value
  const sections = []
  const meta = []
  if (c?.title) meta.push(`Contract title: ${c.title}`)
  if (c?.contract_number) meta.push(`Contract number: ${c.contract_number}`)
  if (c?.description) meta.push(`Description:\n${c.description}`)
  if (meta.length) sections.push(meta.join('\n'))
  let body = (c?.content && String(c.content).trim()) || ''
  if (body.length > DRAFT_CONTEXT_CHAR_CAP) {
    body = `${body.slice(0, DRAFT_CONTEXT_CHAR_CAP)}\n\n[… truncated for context limit …]`
  }
  if (body) sections.push(`Contract text / notes:\n${body}`)
  const scoringLines = []
  appendFindingsAndRecommendationLines(scoringLines, findingIds, recommendationIds)
  if (scoringLines.length) sections.push(scoringLines.join('\n'))
  sections.push(`-- user request\n${q}`)
  return sections.join('\n\n')
}

watch(
  () => [showChat.value, selectedAgent.value],
  ([show, agent]) => {
    if (show && (agent === 'review' || agent === 'draft') && !scoringData.value && !scoringLoading.value) {
      fetchScoring()
    }
  }
)

watch(
  () => selectedVersionId.value,
  (newId) => {
    if (!contract.value?.id || newId == null) return
    persistWorkingVersionId(newId)
    fetchScoring()
  }
)

watch(
  () => [reviewSelectableFindings.value.length, reviewSelectableRecommendations.value.length],
  ([nf, nr]) => {
    if (reviewContextTab.value === 'findings' && nf === 0 && nr > 0) reviewContextTab.value = 'recommendations'
    if (reviewContextTab.value === 'recommendations' && nr === 0 && nf > 0) reviewContextTab.value = 'findings'
  }
)

watch(selectedAgent, (id) => {
  if (id !== 'review' && id !== 'draft') reviewContextFullSpace.value = false
  if (id === 'graph') selectTab('graph')
})

function graphWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/graph-chat`
}

function reviewWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/review`
}

function appendCpwdCopilotToPayload(payload) {
  if (!cpwdCopilotEnabled.value) return payload
  payload.cpwd_copilot = true
  const tok = authStore.token
  if (tok) payload.access_token = tok
  return payload
}

/** Review agent: /ws/review — contract text from `document_chunks` for the selected version. */
function buildReviewWsPayload(message, options = {}) {
  const { comprehensiveContractOverride, ...rest } = options
  const versionId = primaryVersionId.value
  const payload = {
    type: 'chat',
    message,
    contract_id: contract.value?.id ?? null,
    version_id: versionId ?? null,
    ...rest,
  }
  if (comprehensiveContractOverride != null && String(comprehensiveContractOverride).trim()) {
    payload.comprehensive_contract = String(comprehensiveContractOverride).trim()
  }
  return appendCpwdCopilotToPayload(payload)
}

function buildDraftWsPayload(message) {
  const versionId = primaryVersionId.value
  return appendCpwdCopilotToPayload({
    type: 'chat',
    message,
    contract_id: contract.value?.id ?? null,
    version_id: versionId ?? null,
  })
}

function draftWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/draft`
}

function compareWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/compare`
}

function reviewTodoStatusGlyph(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'completed') return '✓'
  if (s === 'in_progress') return '◐'
  return '○'
}

function reviewTodoIconClass(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'completed') return 'text-emerald-500'
  if (s === 'in_progress') return 'text-amber-500'
  return 'text-gray-400 dark:text-gray-500'
}

function normalizeReviewTodos(raw) {
  if (!Array.isArray(raw)) return []
  return raw.map((t) => ({
    content: String(t?.content ?? ''),
    status: String(t?.status ?? 'pending').toLowerCase(),
  }))
}

/** Coalesce UI work: avoid marked/DOMPurify + Vue updates on every WS token (blocks graph & main thread). */
let reviewChatScrollRaf = 0
function scheduleReviewChatScroll() {
  if (reviewChatScrollRaf) return
  reviewChatScrollRaf = requestAnimationFrame(() => {
    reviewChatScrollRaf = 0
    scrollChatToBottom()
    scrollLatestStreamingMessageToBottom()
  })
}

let reviewStreamChunkBuf = ''
let reviewStreamChunkRaf = 0

function appendReviewAssistantText(text) {
  if (!text) return
  const msgs = chatMessages.value.review
  reviewTyping.value = false
  const lastIdx = msgs.length - 1
  const last = msgs[lastIdx]
  const userFlags = getLastReviewUserMessageFlags()
  if (last && last.role === 'assistant' && last.reviewStreaming) {
    const nextContent = (last.content || '') + text
    msgs.splice(lastIdx, 1, {
      ...last,
      content: nextContent,
      markdown: true,
      reviewStreaming: true,
      fromGuidelineRun: last.fromGuidelineRun ?? userFlags.fromGuidelineRun,
      fromComplianceRun: last.fromComplianceRun ?? userFlags.fromComplianceRun,
      generatedFixResponse: last.generatedFixResponse ?? userFlags.fromGeneratedFixPrompt,
    })
  } else {
    msgs.push({
      role: 'assistant',
      content: text,
      markdown: true,
      reviewStreaming: true,
      fromGuidelineRun: userFlags.fromGuidelineRun,
      fromComplianceRun: userFlags.fromComplianceRun,
      generatedFixResponse: userFlags.fromGeneratedFixPrompt,
    })
  }
}

function flushReviewStreamChunks() {
  reviewStreamChunkRaf = 0
  if (!reviewStreamChunkBuf) return
  const batch = reviewStreamChunkBuf
  reviewStreamChunkBuf = ''
  appendReviewAssistantText(batch)
  scheduleReviewChatScroll()
}

function flushReviewStreamChunksNow() {
  if (reviewStreamChunkRaf) {
    cancelAnimationFrame(reviewStreamChunkRaf)
    reviewStreamChunkRaf = 0
  }
  if (!reviewStreamChunkBuf) return
  const batch = reviewStreamChunkBuf
  reviewStreamChunkBuf = ''
  appendReviewAssistantText(batch)
}

function appendReviewAssistantChunk(chunk) {
  let text = ''
  if (typeof chunk === 'string') text = chunk
  else if (Array.isArray(chunk)) {
    text = chunk
      .map((c) => (typeof c === 'string' ? c : c?.text ?? ''))
      .join('')
  } else if (chunk && typeof chunk === 'object' && chunk.text != null) {
    text = String(chunk.text)
  } else {
    text = String(chunk ?? '')
  }
  if (!text) return
  reviewStreamChunkBuf += text
  if (!reviewStreamChunkRaf) {
    reviewStreamChunkRaf = requestAnimationFrame(flushReviewStreamChunks)
  }
}

function finalizeReviewAssistantStream() {
  flushReviewStreamChunksNow()
  const msgs = chatMessages.value.review
  const lastIdx = msgs.length - 1
  const last = msgs[lastIdx]
  const prev = msgs[lastIdx - 1]
  const fromGuidelineRun = !!(prev && prev.role === 'user' && prev.fromGuidelineRun)
  const fromComplianceRun = !!(prev && prev.role === 'user' && prev.fromComplianceRun)
  const generatedFixResponse = !!(prev && prev.role === 'user' && prev.generatedFixPrompt)
  if (last && last.role === 'assistant' && last.reviewStreaming) {
    msgs.splice(lastIdx, 1, {
      ...last,
      markdown: true,
      reviewStreaming: false,
      fromGuidelineRun,
      fromComplianceRun,
      generatedFixResponse,
    })
  }
}

let reviewTodosRaf = 0
let reviewTodosPending = null
function queueReviewTodosUpdate(raw) {
  reviewTodosPending = raw
  if (reviewTodosRaf) return
  reviewTodosRaf = requestAnimationFrame(() => {
    reviewTodosRaf = 0
    if (reviewTodosPending != null) {
      reviewTodos.value = normalizeReviewTodos(reviewTodosPending)
      reviewTodosPending = null
    }
    scheduleReviewChatScroll()
  })
}

function flushReviewTodosQueueNow() {
  if (reviewTodosRaf) {
    cancelAnimationFrame(reviewTodosRaf)
    reviewTodosRaf = 0
  }
  if (reviewTodosPending != null) {
    reviewTodos.value = normalizeReviewTodos(reviewTodosPending)
    reviewTodosPending = null
  }
}

/** Hide review plan on errors / invalid payloads (matches draft `clearDraftPlanUI`). */
function clearReviewPlanUI() {
  flushReviewTodosQueueNow()
  reviewTodos.value = []
}

/**
 * Successful review run: apply any queued todo patch, force every item to completed,
 * then clear on the next frame so the UI does not stay stuck after the model stream ends.
 */
function finalizeReviewTodosSuccess() {
  flushReviewTodosQueueNow()
  if (reviewTodos.value.length) {
    reviewTodos.value = reviewTodos.value.map((t) => ({
      ...t,
      status: 'completed',
    }))
  }
  requestAnimationFrame(() => {
    reviewTodos.value = []
  })
}

function processReviewWsPayload(data) {
  const jd = data?.json_data
  if (!jd || typeof jd !== 'object') return
  const name = jd.name
  if (name === 'write_todos') {
    queueReviewTodosUpdate(jd.data)
    return
  }
  if (name === 'model' && jd.data != null && jd.data !== '') {
    appendReviewAssistantChunk(jd.data)
  }
}

function ensureReviewSocket() {
  return new Promise((resolve, reject) => {
    const cur = reviewChatSocket.value
    if (cur?.readyState === WebSocket.OPEN) {
      resolve(cur)
      return
    }
    if (cur) {
      try {
        cur.close()
      } catch {
        /* ignore */
      }
      reviewChatSocket.value = null
    }

    const ws = new WebSocket(reviewWsUrl())
    reviewChatSocket.value = ws

    let settled = false
    const fail = (err) => {
      if (settled) return
      settled = true
      if (reviewChatSocket.value === ws) reviewChatSocket.value = null
      reject(err)
    }
    const ok = () => {
      if (settled) return
      settled = true
      resolve(ws)
    }

    ws.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        flushReviewStreamChunksNow()
        reviewTyping.value = false
        finalizeReviewAssistantStream()
        clearReviewPlanUI()
        chatMessages.value.review.push({
          role: 'assistant',
          content: '**Error:** Invalid response from review server.',
          markdown: true,
        })
        nextTick(scrollChatToBottom)
        return
      }

      const t = String(data?.type || '').toLowerCase()
      if (t === 'error') {
        flushReviewStreamChunksNow()
        reviewTyping.value = false
        finalizeReviewAssistantStream()
        clearReviewPlanUI()
        chatMessages.value.review.push({
          role: 'assistant',
          content: `**Error:** ${data.detail || 'Unknown error'}`,
          markdown: true,
        })
        nextTick(scrollChatToBottom)
        return
      }
      if (t === 'done') {
        reviewTyping.value = false
        finalizeReviewAssistantStream()
        finalizeReviewTodosSuccess()
        clearReviewScoringSelection()
        nextTick(scrollChatToBottom)
        return
      }
      if (t === 'stream' || t === 'final') {
        processReviewWsPayload(data)
      }
    }

    ws.onopen = () => ok()
    ws.onerror = () => fail(new Error('WebSocket connection failed — is the API running?'))
    ws.onclose = () => {
      if (reviewChatSocket.value === ws) reviewChatSocket.value = null
      if (!settled) fail(new Error('WebSocket closed before opening'))
    }
  })
}

let draftChatScrollRaf = 0
function scheduleDraftChatScroll() {
  if (draftChatScrollRaf) return
  draftChatScrollRaf = requestAnimationFrame(() => {
    draftChatScrollRaf = 0
    scrollChatToBottom()
    scrollLatestStreamingMessageToBottom()
  })
}

let draftStreamChunkBuf = ''
let draftStreamChunkRaf = 0

function appendDraftAssistantText(text) {
  if (!text) return
  const msgs = chatMessages.value.draft
  draftTyping.value = false
  const lastIdx = msgs.length - 1
  const last = msgs[lastIdx]
  if (last && last.role === 'assistant' && last.draftStreaming) {
    const nextContent = (last.content || '') + text
    msgs.splice(lastIdx, 1, { ...last, content: nextContent, markdown: true, draftStreaming: true })
  } else {
    msgs.push({ role: 'assistant', content: text, markdown: true, draftStreaming: true })
  }
}

function flushDraftStreamChunks() {
  draftStreamChunkRaf = 0
  if (!draftStreamChunkBuf) return
  const batch = draftStreamChunkBuf
  draftStreamChunkBuf = ''
  appendDraftAssistantText(batch)
  scheduleDraftChatScroll()
}

function flushDraftStreamChunksNow() {
  if (draftStreamChunkRaf) {
    cancelAnimationFrame(draftStreamChunkRaf)
    draftStreamChunkRaf = 0
  }
  if (!draftStreamChunkBuf) return
  const batch = draftStreamChunkBuf
  draftStreamChunkBuf = ''
  appendDraftAssistantText(batch)
}

function appendDraftAssistantChunk(chunk) {
  let text = ''
  if (typeof chunk === 'string') text = chunk
  else if (Array.isArray(chunk)) {
    text = chunk
      .map((c) => (typeof c === 'string' ? c : c?.text ?? ''))
      .join('')
  } else if (chunk && typeof chunk === 'object' && chunk.text != null) {
    text = String(chunk.text)
  } else {
    text = String(chunk ?? '')
  }
  if (!text) return
  draftStreamChunkBuf += text
  if (!draftStreamChunkRaf) {
    draftStreamChunkRaf = requestAnimationFrame(flushDraftStreamChunks)
  }
}

function finalizeDraftAssistantStream() {
  flushDraftStreamChunksNow()
  const msgs = chatMessages.value.draft
  const lastIdx = msgs.length - 1
  const last = msgs[lastIdx]
  if (last && last.role === 'assistant' && last.draftStreaming) {
    msgs.splice(lastIdx, 1, {
      ...last,
      markdown: true,
      draftStreaming: false,
    })
  }
}

let draftTodosRaf = 0
let draftTodosPending = null
function queueDraftTodosUpdate(raw) {
  draftTodosPending = raw
  if (draftTodosRaf) return
  draftTodosRaf = requestAnimationFrame(() => {
    draftTodosRaf = 0
    if (draftTodosPending != null) {
      draftTodos.value = normalizeReviewTodos(draftTodosPending)
      draftTodosPending = null
    }
    scheduleDraftChatScroll()
  })
}

function flushDraftTodosQueueNow() {
  if (draftTodosRaf) {
    cancelAnimationFrame(draftTodosRaf)
    draftTodosRaf = 0
  }
  if (draftTodosPending != null) {
    draftTodos.value = normalizeReviewTodos(draftTodosPending)
    draftTodosPending = null
  }
}

/** Hide drafting plan: drop pending patches and clear the list (e.g. errors / disconnect). */
function clearDraftPlanUI() {
  flushDraftTodosQueueNow()
  draftTodos.value = []
}

/**
 * Successful draft run: apply any queued todo patch, force every item to completed,
 * then clear on the next frame so the UI never stays stuck on in_progress/pending.
 */
function finalizeDraftTodosSuccess() {
  flushDraftTodosQueueNow()
  if (draftTodos.value.length) {
    draftTodos.value = draftTodos.value.map((t) => ({
      ...t,
      status: 'completed',
    }))
  }
  requestAnimationFrame(() => {
    draftTodos.value = []
  })
}

function chatAttachmentDataUrl(attachment) {
  const ct =
    attachment?.contentType ||
    attachment?.content_type ||
    'application/octet-stream'
  const b64 = attachment?.data || ''
  return `data:${ct};base64,${b64}`
}

function chatAttachmentSubtitle(att) {
  const fn = String(att?.filename || '').toLowerCase()
  if (fn.endsWith('.docx') || fn.endsWith('.doc')) {
    return 'Track changes · Open in Microsoft Word'
  }
  if (fn.endsWith('.pdf')) return 'PDF document'
  return ''
}

function processDraftWsPayload(data) {
  const jd = data?.json_data
  if (!jd || typeof jd !== 'object') return
  const name = jd.name
  if (name === 'write_todos') {
    queueDraftTodosUpdate(jd.data)
    return
  }
  if (name === 'attachment' && jd.data && typeof jd.data === 'object') {
    finalizeDraftAssistantStream()
    const att = jd.data
    chatMessages.value.draft.push({
      role: 'assistant',
      content: 'Generated draft (Word, track changes):',
      markdown: false,
      attachments: [
        {
          filename: att.filename || 'draft.docx',
          contentType: att.content_type,
          data: att.data,
        },
      ],
    })
    scheduleDraftChatScroll()
    return
  }
  if (name === 'chunk_redraft' && jd.data && typeof jd.data === 'object') {
    const d = jd.data
    const ord = d.ordinal ?? '?'
    const tot = d.total ?? '?'
    const idx = d.chunk_index ?? '?'
    const n = d.findings_count ?? 0
    appendDraftAssistantChunk(
      `\n*Chunk ${ord}/${tot} (document chunk index ${idx}) — ${n} amendment record(s) for this slice.*\n`
    )
    return
  }
  if (name === 'model' && jd.data != null && jd.data !== '') {
    appendDraftAssistantChunk(jd.data)
  }
}

function ensureDraftSocket() {
  return new Promise((resolve, reject) => {
    const cur = draftChatSocket.value
    if (cur?.readyState === WebSocket.OPEN) {
      resolve(cur)
      return
    }
    if (cur) {
      try {
        cur.close()
      } catch {
        /* ignore */
      }
      draftChatSocket.value = null
    }

    const ws = new WebSocket(draftWsUrl())
    draftChatSocket.value = ws

    let settled = false
    const fail = (err) => {
      if (settled) return
      settled = true
      if (draftChatSocket.value === ws) draftChatSocket.value = null
      reject(err)
    }
    const ok = () => {
      if (settled) return
      settled = true
      resolve(ws)
    }

    ws.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        flushDraftStreamChunksNow()
        draftTyping.value = false
        finalizeDraftAssistantStream()
        clearDraftPlanUI()
        chatMessages.value.draft.push({
          role: 'assistant',
          content: '**Error:** Invalid response from draft server.',
          markdown: true,
        })
        nextTick(scrollChatToBottom)
        return
      }

      const t = String(data?.type || '').toLowerCase()
      if (t === 'error') {
        flushDraftStreamChunksNow()
        draftTyping.value = false
        finalizeDraftAssistantStream()
        clearDraftPlanUI()
        chatMessages.value.draft.push({
          role: 'assistant',
          content: `**Error:** ${data.detail || 'Unknown error'}`,
          markdown: true,
        })
        nextTick(scrollChatToBottom)
        return
      }
      if (t === 'done') {
        draftTyping.value = false
        finalizeDraftAssistantStream()
        finalizeDraftTodosSuccess()
        clearReviewScoringSelection()
        nextTick(scrollChatToBottom)
        return
      }
      if (t === 'stream' || t === 'final') {
        processDraftWsPayload(data)
      }
    }

    ws.onopen = () => ok()
    ws.onerror = () => fail(new Error('WebSocket connection failed — is the API running?'))
    ws.onclose = () => {
      if (draftChatSocket.value === ws) draftChatSocket.value = null
      if (!settled) fail(new Error('WebSocket closed before opening'))
    }
  })
}

let compareChatScrollRaf = 0
function scheduleCompareChatScroll() {
  if (compareChatScrollRaf) return
  compareChatScrollRaf = requestAnimationFrame(() => {
    compareChatScrollRaf = 0
    scrollChatToBottom()
    scrollLatestStreamingMessageToBottom()
  })
}

let compareStreamChunkBuf = ''
let compareStreamChunkRaf = 0

function appendCompareAssistantText(text) {
  if (!text) return
  const msgs = chatMessages.value.compare
  compareTyping.value = false
  const lastIdx = msgs.length - 1
  const last = msgs[lastIdx]
  if (last && last.role === 'assistant' && last.compareStreaming) {
    const nextContent = (last.content || '') + text
    msgs.splice(lastIdx, 1, { ...last, content: nextContent, markdown: true, compareStreaming: true })
  } else {
    msgs.push({ role: 'assistant', content: text, markdown: true, compareStreaming: true })
  }
}

function flushCompareStreamChunks() {
  compareStreamChunkRaf = 0
  if (!compareStreamChunkBuf) return
  const batch = compareStreamChunkBuf
  compareStreamChunkBuf = ''
  appendCompareAssistantText(batch)
  scheduleCompareChatScroll()
}

function flushCompareStreamChunksNow() {
  if (compareStreamChunkRaf) {
    cancelAnimationFrame(compareStreamChunkRaf)
    compareStreamChunkRaf = 0
  }
  if (!compareStreamChunkBuf) return
  const batch = compareStreamChunkBuf
  compareStreamChunkBuf = ''
  appendCompareAssistantText(batch)
}

function appendCompareAssistantChunk(chunk) {
  let text = ''
  if (typeof chunk === 'string') text = chunk
  else if (Array.isArray(chunk)) {
    text = chunk.map((c) => (typeof c === 'string' ? c : c?.text ?? '')).join('')
  } else if (chunk && typeof chunk === 'object' && chunk.text != null) {
    text = String(chunk.text)
  } else {
    text = String(chunk ?? '')
  }
  if (!text) return
  compareStreamChunkBuf += text
  if (!compareStreamChunkRaf) {
    compareStreamChunkRaf = requestAnimationFrame(flushCompareStreamChunks)
  }
}

function finalizeCompareAssistantStream() {
  flushCompareStreamChunksNow()
  const msgs = chatMessages.value.compare
  const lastIdx = msgs.length - 1
  const last = msgs[lastIdx]
  if (last && last.role === 'assistant' && last.compareStreaming) {
    msgs.splice(lastIdx, 1, {
      ...last,
      markdown: true,
      compareStreaming: false,
    })
  }
}

function processCompareWsPayload(data) {
  const jd = data?.json_data
  if (!jd || typeof jd !== 'object') return
  if (jd.name === 'model' && jd.data != null && jd.data !== '') {
    appendCompareAssistantChunk(jd.data)
  }
}

function ensureCompareSocket() {
  return new Promise((resolve, reject) => {
    const cur = compareChatSocket.value
    if (cur?.readyState === WebSocket.OPEN) {
      resolve(cur)
      return
    }
    if (cur) {
      try {
        cur.close()
      } catch {
        /* ignore */
      }
      compareChatSocket.value = null
    }

    const ws = new WebSocket(compareWsUrl())
    compareChatSocket.value = ws

    let settled = false
    const fail = (err) => {
      if (settled) return
      settled = true
      if (compareChatSocket.value === ws) compareChatSocket.value = null
      reject(err)
    }
    const ok = () => {
      if (settled) return
      settled = true
      resolve(ws)
    }

    ws.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        flushCompareStreamChunksNow()
        compareTyping.value = false
        finalizeCompareAssistantStream()
        chatMessages.value.compare.push({
          role: 'assistant',
          content: '**Error:** Invalid response from compare server.',
          markdown: true,
        })
        nextTick(scrollChatToBottom)
        return
      }

      const t = String(data?.type || '').toLowerCase()
      if (t === 'error') {
        flushCompareStreamChunksNow()
        compareTyping.value = false
        finalizeCompareAssistantStream()
        chatMessages.value.compare.push({
          role: 'assistant',
          content: `**Error:** ${data.detail || 'Unknown error'}`,
          markdown: true,
        })
        nextTick(scrollChatToBottom)
        return
      }
      if (t === 'done') {
        compareTyping.value = false
        finalizeCompareAssistantStream()
        nextTick(scrollChatToBottom)
        return
      }
      if (t === 'stream' || t === 'final') {
        processCompareWsPayload(data)
      }
    }

    ws.onopen = () => ok()
    ws.onerror = () => fail(new Error('WebSocket connection failed — is the API running?'))
    ws.onclose = () => {
      if (compareChatSocket.value === ws) compareChatSocket.value = null
      if (!settled) fail(new Error('WebSocket closed before opening'))
    }
  })
}

function scrollChatToBottom() {
  const ids = ['chat-messages', 'graph-chat-messages']
  for (const id of ids) {
    const el = document.getElementById(id)
    if (el) el.scrollTop = el.scrollHeight
  }
}

function scrollLatestStreamingMessageToBottom() {
  const el = document.getElementById('chat-messages')
  if (!el) return
  const bodies = Array.from(el.querySelectorAll('.clm-agent-message-body'))
  if (!bodies.length) return
  const lastBody = bodies[bodies.length - 1]
  if (!lastBody) return
  lastBody.scrollTop = lastBody.scrollHeight
}

function selectGraphNodeFromValue(value) {
  const raw = String(value || '').trim()
  if (!raw) return []

  const query = raw.includes(':') ? raw.split(':')[0].trim() : raw
  if (!query) return []

  const tries = [query]
  const cleaned = query.replace(/^[\s"'`(\[]+|[\s"'`\])}]+$/g, '').trim()
  if (cleaned && cleaned !== query) tries.push(cleaned)

  for (const candidate of tries) {
    const matches = graphExplorerRef.value?.selectNodeByQuery?.(candidate, { populateSearch: false, zoomFirst: true }) || []
    if (matches.length) return matches
  }
  return []
}

const openPreviousChatbotForGraph = () => {
  if (!isAgentActive('graph')) {
    const graphAgent = availableAgents.value.find((a) => a.id === 'graph')
    if (graphAgent) {
      _allActiveAgents.value = [..._allActiveAgents.value, graphAgent]
    } else {
      _allActiveAgents.value = [..._allActiveAgents.value, { id: 'graph', name: 'Graph QA' }]
    }
  }
  selectedAgent.value = 'graph'
  showGraphChatPanel.value = false
  showChat.value = true
  nextTick(scrollChatToBottom)
}

function autoSelectGraphFromContext(values) {
  const picked = []
  for (const value of values || []) {
    const matches = selectGraphNodeFromValue(value)
    if (matches.length) {
      picked.push(...matches)
    }
  }
  return [...new Set(picked)]
}

function collectContextValues(context, out) {
  if (context == null) return

  if (typeof context === 'string' || typeof context === 'number' || typeof context === 'boolean') {
    const text = String(context).trim()
    if (text) out.push(text)
    return
  }

  if (Array.isArray(context)) {
    for (const item of context) {
      collectContextValues(item, out)
    }
    return
  }

  if (typeof context === 'object') {
    if (Object.hasOwn(context, 'value')) {
      collectContextValues(context.value, out)
      return
    }

    for (const val of Object.values(context)) {
      collectContextValues(val, out)
    }
  }
}

function normalizeContextValues(context) {
  const out = []
  collectContextValues(context, out)
  const unique = [...new Set(out)]
  return unique.filter(Boolean)
}

function normalizeResponseText(raw) {
  if (raw == null) return ''
  if (typeof raw === 'string' || typeof raw === 'number' || typeof raw === 'boolean') {
    return String(raw).trim()
  }
  if (Array.isArray(raw)) {
    const parts = raw.map((item) => normalizeResponseText(item)).filter(Boolean)
    return parts.join('\n').trim()
  }
  if (typeof raw === 'object') {
    const preferred = raw.response ?? raw.text ?? raw.message ?? null
    if (preferred != null) {
      const p = normalizeResponseText(preferred)
      if (p) return p
    }
    const values = []
    for (const val of Object.values(raw)) {
      if (val == null) continue
      if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
        const text = String(val).trim()
        if (text) values.push(text)
      }
    }
    if (values.length) return [...new Set(values)].join(' · ')
    try {
      return JSON.stringify(raw)
    } catch {
      return ''
    }
  }
  return ''
}

function parseGraphWsPayload(data) {
  const payload = data?.json_data && typeof data.json_data === 'object' ? data.json_data : data
  const responseText = normalizeResponseText(payload?.response ?? payload?.text ?? data?.text ?? '')
  const contextValues = normalizeContextValues(payload?.context || data?.context)
  return { responseText: String(responseText || '').trim(), contextValues }
}

function pushGraphAssistant(content, markdown = true, contextValues = []) {
  const safeContent = String(content || '').trim()
  const safeContext = Array.isArray(contextValues) ? contextValues : []
  if (!safeContent && safeContext.length === 0) return
  const msgs = chatMessages.value.graph
  const lastIdx = msgs.length - 1
  const last = lastIdx >= 0 ? msgs[lastIdx] : null

  // If backend sends same response twice (plain + context), keep only one.
  if (
    last &&
    last.role === 'assistant' &&
    String(last.content || '').trim() === safeContent
  ) {
    const lastContext = Array.isArray(last.contextValues) ? last.contextValues : []
    if (safeContext.length > lastContext.length) {
      msgs[lastIdx] = { ...last, markdown, contextValues: safeContext }
    }
    return
  }

  chatMessages.value.graph.push({ role: 'assistant', content: safeContent, markdown, contextValues: safeContext })
}

function ensureGraphSocket() {
  return new Promise((resolve, reject) => {
    const cur = graphChatSocket.value
    if (cur?.readyState === WebSocket.OPEN) {
      resolve(cur)
      return
    }

    const ws = new WebSocket(graphWsUrl())
    graphChatSocket.value = ws

    let settled = false
    const fail = (err) => {
      if (settled) return
      settled = true
      if (graphChatSocket.value === ws) graphChatSocket.value = null
      reject(err)
    }
    const ok = () => {
      if (settled) return
      settled = true
      resolve(ws)
    }

    ws.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        isTyping.value = false
        pushGraphAssistant('Invalid response from graph server.', true)
        nextTick(scrollChatToBottom)
        return
      }
      const msgType = String(data?.type || '').toLowerCase()

      // Ignore non-terminal stream/control events to avoid duplicate bubbles.
      if (msgType && !['final', 'answer', 'error'].includes(msgType)) {
        return
      }

      isTyping.value = false
      if (msgType === 'error') {
        pushGraphAssistant(`**Error:** ${data.detail || 'Unknown error'}`, true, [])
      } else {
        const parsed = parseGraphWsPayload(data)
        if (parsed.responseText) {
          const signature = `${parsed.responseText}\u0001${parsed.contextValues.join('\u0001')}`
          if (signature === lastGraphReplySignature.value) {
            nextTick(scrollChatToBottom)
            return
          }
          lastGraphReplySignature.value = signature
          pushGraphAssistant(parsed.responseText, true, parsed.contextValues)
          autoSelectGraphFromContext(parsed.contextValues)
        } else {
          pushGraphAssistant(`\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``, true, [])
        }
      }
      nextTick(scrollChatToBottom)
    }

    ws.onopen = () => ok()
    ws.onerror = () => fail(new Error('WebSocket connection failed — is the API running on port 8000?'))
    ws.onclose = () => {
      if (graphChatSocket.value === ws) graphChatSocket.value = null
      if (!settled) fail(new Error('WebSocket closed before opening'))
    }
  })
}

const isAgentActive = (id) => _allActiveAgents.value.some(a => a.id === id)

const toggleAgent = (agent) => {
  if (isAgentActive(agent.id)) {
    if (_allActiveAgents.value.length > 1) {
      _allActiveAgents.value = _allActiveAgents.value.filter(a => a.id !== agent.id)
      if (selectedAgent.value === agent.id) {
        selectedAgent.value = activeAgents.value[0]?.id
      }
    }
  } else {
    _allActiveAgents.value.push(agent)
  }
}

const addNewAgent = () => {
  if (!newAgentName.value.trim()) return
  const id = 'custom_' + Date.now()
  const agent = { id, name: newAgentName.value }
  availableAgents.value.push(agent)
  _allActiveAgents.value.push(agent)
  chatMessages.value[id] = [
    { role: 'assistant', content: `Hello! I'm your new ${agent.name}. How can I help you with this contract?` }
  ]
  selectedAgent.value = id
  newAgentName.value = ''
}

const getAgentName = (id) => {
  const agent = availableAgents.value.find(a => a.id === id)
  return agent ? agent.name : 'AI Agent'
}

const agentGuideUi = computed(() => {
  const id = selectedAgent.value
  const name = getAgentName(id)
  const guides = {
    review: {
      kicker: 'Review & compliance',
      title: 'Review Agent',
      purpose:
        'Analyzes this contract for risk, missing clauses, and alignment with your guidelines and compliance checks. Ask open questions or attach scoring findings, guideline sections, or compliance rows for focused runs.',
      steps: [
        {
          label: 'Ask or attach context',
          detail:
            'Type a question in your own words, optionally add findings/recommendations from scoring, or use the guideline and compliance pickers below.',
        },
        {
          label: 'Run structured checks',
          detail:
            'Use “Run” on selected guidelines or compliance packs when you want those sections evaluated as a bundle.',
        },
        {
          label: 'Save and hand off',
          detail:
            'Save important assistant messages as review items, then switch to the Draft Agent to turn them into concrete redlines.',
        },
      ],
    },
    draft: {
      kicker: 'Redrafting',
      title: 'Draft Agent',
      purpose:
        'Produces amendments and replacement wording in structured form. It can consume saved review items and scoring context so edits map back to issues you already identified.',
      steps: [
        {
          label: 'Describe the outcome',
          detail:
            'Ask for rewrites, new clauses, or tone changes. The backend processes the document in chunks so changes stay localized.',
        },
        {
          label: 'Attach review items',
          detail:
            'Pick saved findings from review or optional scoring context so the draft targets real gaps, not generic text.',
        },
        {
          label: 'Track progress',
          detail:
            'Watch the in-chat plan and progress, then apply returned amendments in your DOCX workflow.',
        },
      ],
    },
    compare: {
      kicker: 'Version diff',
      title: 'Document comparison',
      purpose:
        'Compares two stored versions (A vs B) on the server and answers with markdown, including tables. Hide the compare workspace above if you need more room—the chat still works once versions are selected.',
      steps: [
        {
          label: 'Pick Documents',
          detail:
            'Choose two different versions. A is usually the older baseline; B is what changed.',
        },
        {
          label: 'Ask what to emphasize',
          detail:
            'Request a full material-diff summary or focus on payment, liability, scope, or added/removed clauses.',
        },
        {
          label: 'Run',
          detail:
            'Use Quick Run when shown, or send from the input. Suggested queries below fill the prompt in one tap.',
        },
      ],
    },
    complaints: {
      kicker: 'Disputes & penalties',
      title: 'Complaints Agent',
      purpose:
        'Helps you reason about dispute resolution, performance issues, and penalty-style clauses. Combine with your complaints library when you want language aligned with recorded cases.',
      steps: [
        {
          label: 'Ask about mechanisms',
          detail:
            'Question escalation paths, remedies, notice periods, and how penalties tie to events.',
        },
        {
          label: 'Use the library',
          detail:
            'When available, apply known complaints to compare similar wording or outcomes.',
        },
        {
          label: 'Escalate internally',
          detail:
            'Use replies as a briefing for legal or commercial teams before you change the agreement.',
        },
      ],
    },
    graph: {
      kicker: 'Knowledge graph',
      title: 'Graph QA',
      purpose:
        'Answers questions about entities and relationships built from your contract text. Best for “who connects to what,” themes, and exploring structure beyond keyword search.',
      steps: [
        {
          label: 'Ensure coverage',
          detail:
            'From the Knowledge graph tab, build the graph for the version you care about so answers are grounded.',
        },
        {
          label: 'Ask relationally',
          detail:
            'Parties, obligations, dates, and cross-links are easier to query here than in a linear read-through.',
        },
        {
          label: 'Combine with review',
          detail:
            'Use graph insights together with the Review Agent when you need both structure and compliance judgment.',
        },
      ],
    },
  }
  if (guides[id]) return guides[id]
  if (id.startsWith('custom_')) {
    return {
      kicker: 'Custom agent',
      title: name,
      purpose: `${name} is a flexible assistant for this contract—summaries, brainstorming, and drafting ideas that do not require a specialized pipeline.`,
      steps: [
        {
          label: 'State the goal',
          detail: 'Say what you want (summary, risk list, email draft, checklist) and who the audience is.',
        },
        {
          label: 'Know the specialists',
          detail:
            'Review, Draft, Compare, Complaints, and Graph QA cover deeper workflows; use this agent for quick, general help.',
        },
        {
          label: 'Iterate',
          detail: 'Refine with constraints: tone, length, jurisdiction, or must-include points.',
        },
      ],
    }
  }
  return null
})

const agentSuggestedQueries = computed(() => {
  const id = selectedAgent.value
  const map = {
    review: [
      'Scan the contract for high-risk clauses and suggest practical mitigations.',
      'Summarize compliance gaps and prioritize them by severity.',
      'List ambiguous or missing definitions that could cause disputes.',
    ],
    draft: [
      'Rewrite the termination clause to be clearer and fairer to both parties.',
      'Tighten liability and indemnity language without changing commercial intent.',
      'Produce a short bullet executive summary of the amendments you would propose.',
    ],
    compare: [...comparePromptPresets],
    complaints: [
      'What dispute resolution mechanisms apply to payment delays?',
      'Identify penalty clauses and explain when each is triggered.',
      'Summarize remedies available for breach of schedule or delivery obligations.',
    ],
    graph: [
      'Who are the main parties and how are they connected in the graph?',
      'Which entities are most connected to payment or financial terms?',
      'Explain how obligations relate to dates or milestones in the graph.',
    ],
  }
  if (map[id]) return map[id]
  if (id.startsWith('custom_')) {
    return [
      'Summarize the key terms I should know before signing.',
      'What risks should I discuss with legal or procurement?',
      'Draft a short checklist for contract administration after execution.',
    ]
  }
  return []
})

const suggestedQueryDisabled = computed(() => mainChatInputLocked.value)

async function applyAgentSuggestedQuery(text) {
  const q = String(text || '').trim()
  if (!q || suggestedQueryDisabled.value) return
  if (selectedAgent.value === 'compare') {
    userInput.value = q
    if (canRunCompareNow.value) await runCompareNow(q, false)
    await nextTick()
    scrollChatToBottom()
    return
  }
  userInput.value = q
  await nextTick()
  await sendMessage()
}

async function runCompareNow(queryOverride = '', clearInput = false) {
  const aId = compareVersionAId.value ? Number(compareVersionAId.value) : NaN
  const bId = compareVersionBId.value ? Number(compareVersionBId.value) : NaN
  const versions = contract.value?.document_versions || []
  const va = versions.find((v) => v.id === aId)
  const vb = versions.find((v) => v.id === bId)
  if (!va || !vb || aId === bId) {
    chatMessages.value.compare.push({
      role: 'assistant',
      markdown: true,
      content:
        '**Select two different document versions** in the pickers above (A and B), then send again.',
    })
    nextTick(scrollChatToBottom)
    return
  }
  const labelA = formatVersionCompareLabel(va)
  const labelB = formatVersionCompareLabel(vb)
  const userAsk =
    typeof queryOverride === 'string' && queryOverride.trim().length > 0
      ? queryOverride.trim()
      : 'Compare these versions and summarize material changes.'
  chatMessages.value.compare.push({ role: 'user', content: userAsk })
  if (clearInput) userInput.value = ''
  compareTyping.value = true
  try {
    const ws = await ensureCompareSocket()
    ws.send(
      JSON.stringify({
        type: 'chat',
        contract_id: Number(contractId),
        version_a_id: aId,
        version_b_id: bId,
        message: userAsk,
      })
    )
    nextTick(scrollChatToBottom)
  } catch (e) {
    compareTyping.value = false
    finalizeCompareAssistantStream()
    chatMessages.value.compare.push({
      role: 'assistant',
      content: `**Connection error:** ${e?.message || e}`,
      markdown: true,
    })
    nextTick(scrollChatToBottom)
  }
}

const sendMessage = async () => {
  const query = userInput.value.trim()
  const busy =
    selectedAgent.value === 'review'
      ? reviewTyping.value
      : selectedAgent.value === 'draft'
        ? draftTyping.value
        : selectedAgent.value === 'compare'
          ? compareTyping.value
          : isTyping.value
  if (busy) return

  const reviewHasContext =
    selectedAgent.value === 'review' &&
    (cpSelectedIds.value.size > 0 || glSelectedKeys.value.size > 0)
  if (selectedAgent.value !== 'compare' && !query && !reviewHasContext) return

  if (reviewHasContext) {
    glPickerOpen.value = false
    cpPickerOpen.value = false
    await reviewSendContextPack({ overrideQuery: query || null })
    return
  }

  if (selectedAgent.value === 'review') {
    const fIds = [...new Set(selectedReviewFindingIds.value || [])]
    const rIds = [...new Set(selectedReviewRecommendationIds.value || [])]
    const backendMessage = formatReviewBackendMessage(query, fIds, rIds)
    const parts = []
    if (fIds.length) parts.push(`${fIds.length} finding${fIds.length === 1 ? '' : 's'}`)
    if (rIds.length) parts.push(`${rIds.length} recommendation${rIds.length === 1 ? '' : 's'}`)
    const displayContent =
      parts.length > 0 ? `${query}\n\n(Sent with: ${parts.join(', ')})` : query
    chatMessages.value.review.push({ role: 'user', content: displayContent })
    userInput.value = ''
    reviewTyping.value = true
    reviewTodos.value = []
    try {
      const ws = await ensureReviewSocket()
      ws.send(JSON.stringify(buildReviewWsPayload(backendMessage)))
      nextTick(scrollChatToBottom)
    } catch (e) {
      reviewTyping.value = false
      clearReviewPlanUI()
      chatMessages.value.review.push({
        role: 'assistant',
        content: `**Connection error:** ${e?.message || e}`,
        markdown: true,
      })
      nextTick(scrollChatToBottom)
    }
    return
  }

  if (selectedAgent.value === 'draft') {
    const fIds = [...new Set(selectedReviewFindingIds.value || [])]
    const rIds = [...new Set(selectedReviewRecommendationIds.value || [])]

    // Build review-items context block if any are selected
    let reviewItemsBlock = ''
    const selectedItems = contractReviewItems.value.filter(i => selectedDraftItemIds.value.has(i.id))
    if (selectedItems.length > 0) {
      const lines = [
        '[REVIEW FINDINGS CONTEXT]',
        '',
        'The following issues were identified during the contract review phase.',
        'Across all chunks, every finding below should be reflected **where it applies** to contract text; chunks with no relevant issue should be left unchanged.',
        '',
      ]
      selectedItems.forEach((item, n) => {
        const sev = item.severity ? ` [${item.severity.toUpperCase()}]` : ''
        lines.push(`### Finding ${n + 1}${sev}: ${item.title || 'Review item'}`)
        lines.push(item.content.trim())
        lines.push('')
      })
      lines.push(
        '--- Redraft Instructions ---',
        'The backend sends **one document chunk per model call**. For each chunk, apply only the findings that relate to that slice; return no amendments for chunks where nothing applies.',
        '1. **Address applicable findings** — revise wording in the current chunk to close gaps that touch that text.',
        '2. **Preserve intent** — keep the contract\'s original purpose; only change what is needed.',
        '3. **Flag changes** — in each amendment record, note which finding(s) the slice-level edit implements.',
        '4. **Prioritise critical findings** first where they apply to the chunk, then moderate, then minor.',
        '5. **Per-chunk output only** — structured replacement for the current chunk slice, not a rewrite of the whole agreement.',
        '[END REVIEW FINDINGS CONTEXT]',
      )
      reviewItemsBlock = lines.join('\n')
    }

    const baseMessage = reviewItemsBlock
      ? `${reviewItemsBlock}\n\n--- User request ---\n${query}`
      : query

    const backendMessage = formatDraftBackendMessage(baseMessage, fIds, rIds)
    const parts = []
    if (selectedItems.length) parts.push(`${selectedItems.length} review item${selectedItems.length === 1 ? '' : 's'}`)
    if (fIds.length) parts.push(`${fIds.length} finding${fIds.length === 1 ? '' : 's'}`)
    if (rIds.length) parts.push(`${rIds.length} recommendation${rIds.length === 1 ? '' : 's'}`)
    const displayContent = parts.length > 0 ? `${query}\n\n(Sent with: ${parts.join(', ')})` : query
    chatMessages.value.draft.push({
      role: 'user',
      content: displayContent,
      reviewItems: selectedItems.length ? selectedItems.map(i => ({ id: i.id, title: i.title, severity: i.severity })) : undefined,
    })
    userInput.value = ''
    selectedDraftItemIds.value = new Set()
    draftItemPickerOpen.value = false
    draftTyping.value = true
    draftTodos.value = []
    try {
      const ws = await ensureDraftSocket()
      ws.send(JSON.stringify(buildDraftWsPayload(backendMessage)))
      nextTick(scrollChatToBottom)
    } catch (e) {
      draftTyping.value = false
      clearDraftPlanUI()
      chatMessages.value.draft.push({
        role: 'assistant',
        content: `**Connection error:** ${e?.message || e}`,
        markdown: true,
      })
      nextTick(scrollChatToBottom)
    }
    return
  }

  if (selectedAgent.value === 'compare') {
    userInput.value = ''
    await runCompareNow(query, true)
    return
  }

  const content = query
  chatMessages.value[selectedAgent.value].push({ role: 'user', content })
  userInput.value = ''

  if (selectedAgent.value === 'graph') {
    isTyping.value = true
    try {
      const ws = await ensureGraphSocket()
      ws.send(JSON.stringify({ type: 'chat', message: content }))
      nextTick(scrollChatToBottom)
    } catch (e) {
      isTyping.value = false
      pushGraphAssistant(`**Connection error:** ${e?.message || e}`, true)
      nextTick(scrollChatToBottom)
    }
    return
  }

  // Simulate AI Response (non-graph agents)
  isTyping.value = true
  setTimeout(() => {
    isTyping.value = false
    let response = ''
    const agentName = getAgentName(selectedAgent.value)

    if (content.toLowerCase().includes('hello') || content.toLowerCase().includes('hi')) {
      response = `Hello! As your ${agentName}, I've analyzed the current document state. How can I specifically assist you with the ${contract.value?.title || 'contract'}?`
    } else if (content.toLowerCase().includes('complaint') || content.toLowerCase().includes('issue')) {
      response = `I've noted the complaint regarding "${content}". I've added it to the complaints record for this contract. Would you like me to flag this to the legal department?`
      addComplaint(content)
    } else {
      response = `Based on my analysis as ${agentName}, I recommend reviewing the payment terms on page 2. I've also flagged a potential ambiguity in the force majeure clause. Would you like me to draft a more specific version?`
    }

    chatMessages.value[selectedAgent.value].push({ role: 'assistant', content: response })

    nextTick(scrollChatToBottom)
  }, 1500)
}

const sendGraphMessage = async () => {
  if (!graphUserInput.value.trim() || isTyping.value) return
  const content = graphUserInput.value.trim()
  chatMessages.value.graph.push({ role: 'user', content })
  graphUserInput.value = ''
  isTyping.value = true
  lastGraphReplySignature.value = ''
  try {
    const ws = await ensureGraphSocket()
    ws.send(JSON.stringify({ type: 'chat', message: content }))
  } catch (e) {
    isTyping.value = false
    pushGraphAssistant(`**Connection error:** ${e?.message || e}`, true)
  } finally {
    nextTick(scrollChatToBottom)
  }
}

const filteredFields = computed(() => {
  // Signed PDF already has signatures baked in — no need to overlay
  if (showSigned.value) return []

  // Use fields from the latest version (flattened from each version_signer)
  const latest = latestVersion.value
  if (latest?.version_signers?.length) {
    const allFields = latest.version_signers.flatMap(vs => vs.signature_fields_v2 || [])
    return allFields.filter(f => f.page_number === currentPage.value - 1)
  }

  // Fall back to legacy contract-level fields
  return (contract.value?.signature_fields || []).filter(f => f.page_number === currentPage.value - 1)
})

// Accept the full field object so we can check both version_signer_id and legacy signer_id
const getSignerName = (field) => {
  if (!field) return 'Unknown'
  // New version-based field
  if (field.version_signer_id) {
    const latest = latestVersion.value
    const vs = latest?.version_signers?.find(s => s.id === field.version_signer_id)
    return vs?.master_signer?.name || 'Unknown'
  }
  // Legacy field
  const signer = contract.value?.signers?.find(s => s.id === field.signer_id)
  return signer ? signer.name : 'Unknown'
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  try {
    return new Date(dateStr).toLocaleDateString()
  } catch (e) {
    return dateStr
  }
}

// token can be a UUID (new) or a signerId number (legacy)
const copySigningLink = (token) => {
  const url = `${window.location.origin}/sign/${token}`
  navigator.clipboard.writeText(url)
  toast('Signing link copied to clipboard!')
}

const getFieldStyle = (field) => {
  const baseScale = field.scale || 1.5
  const r = pdfPageRenderScale.value / baseScale
  return {
    left: `${field.x_pos * r}px`,
    top: `${field.y_pos * r}px`,
    width: `${(field.width ?? 150) * r}px`,
    height: `${(field.height ?? 50) * r}px`,
  }
}

/** CSS pixels scale so the page fits inside #pdf-scroll-container (width and height). */
function computePdfFitScale(page) {
  const scrollEl = typeof document !== 'undefined' ? document.getElementById('pdf-scroll-container') : null
  const base = page.getViewport({ scale: 1 })
  if (!scrollEl || base.width <= 0) return 1.5

  const cs = getComputedStyle(scrollEl)
  const padX = (parseFloat(cs.paddingLeft) || 0) + (parseFloat(cs.paddingRight) || 0)
  const padY = (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0)
  const rect = scrollEl.getBoundingClientRect()
  const fudge = 8
  const availW = Math.max(0, rect.width - padX - fudge)
  const availH = Math.max(0, scrollEl.clientHeight - padY - fudge)

  if (availW < 40) {
    return Math.min(3, Math.max(0.25, availW / base.width))
  }

  const scaleW = availW / base.width
  const scaleH = availH > 40 ? availH / base.height : scaleW
  // When the scroll area height is not laid out yet (e.g. drawer opening), min(scaleW, scaleH) shrinks the page badly.
  const fit = availH >= 120 ? Math.min(scaleW, scaleH) : scaleW
  return Math.min(3, Math.max(0.25, fit))
}

const renderPdf = async () => {
  if (!pdfDoc.value) return
  try {
    removePreviewHighlightFrame()
    const page = await pdfDoc.value.getPage(currentPage.value)
    const scale = computePdfFitScale(page)
    pdfPageRenderScale.value = scale

    const cssViewport = page.getViewport({ scale })
    const dpr =
      typeof window !== 'undefined' ? Math.min(window.devicePixelRatio || 1, 2.5) : 1
    const bitmapViewport = page.getViewport({ scale: scale * dpr })

    const canvas = document.getElementById('pdf-canvas')
    if (!canvas) return
    const context = canvas.getContext('2d', { alpha: false })

    canvas.width = Math.floor(bitmapViewport.width)
    canvas.height = Math.floor(bitmapViewport.height)
    canvas.style.width = `${Math.floor(cssViewport.width)}px`
    canvas.style.height = `${Math.floor(cssViewport.height)}px`

    const container = document.getElementById('pdf-container')
    if (container) {
      container.style.width = `${Math.floor(cssViewport.width)}px`
      container.style.height = `${Math.floor(cssViewport.height)}px`
    }

    await page.render({ canvasContext: context, viewport: bitmapViewport }).promise

    if (container) {
      try {
        await appendPdfTextLayer(page, cssViewport, container)
      } catch (e) {
        console.warn('PDF text layer for chunks:', e)
      }
    }
    await nextTick()
    await nextTick()
    if (!suppressChunkHighlightReapply.value && contractActiveChunkId.value != null) {
      reapplyActiveChunkHighlight()
    }
  } catch (err) {
    console.error('Error rendering PDF page:', err)
  }
}

function toggleContractPreviewChunksDrawer() {
  contractPreviewChunksDrawerOpen.value = !contractPreviewChunksDrawerOpen.value
  if (contractPreviewChunksDrawerOpen.value) {
    loadContractPreviewChunks()
  }
}

async function loadContractPreviewChunks() {
  const vid = primaryVersionId.value
  if (!vid) {
    contractPreviewChunks.value = []
    return
  }
  contractChunksLoading.value = true
  contractPreviewChunks.value = []
  try {
    const { data } = await axios.get(`/api/versions/${vid}/chunks`)
    contractPreviewChunks.value = data || []
  } catch (e) {
    console.warn('Failed to load contract chunks:', e)
    contractPreviewChunks.value = []
  } finally {
    contractChunksLoading.value = false
  }
}

async function scrollContractChunkToPreview(chunk, opts = {}) {
  if (!opts.preserveComplianceContext) {
    previewComplianceContextRec.value = null
  }
  contractActiveChunkId.value = chunk.id

  const preferred =
    opts.preferredPdfPage != null && opts.preferredPdfPage >= 1
      ? Math.floor(Number(opts.preferredPdfPage))
      : null

  suppressChunkHighlightReapply.value = true
  try {
    if (!isDocxPreview.value && pdfDoc.value) {
      const n = pdfDoc.value.numPages || 0
      const saved = currentPage.value
      const order = []
      if (preferred != null && preferred <= n) order.push(preferred)
      for (let p = 1; p <= n; p++) {
        if (p !== preferred) order.push(p)
      }
      let found = false
      for (const p of order) {
        currentPage.value = p
        await renderPdf()
        await nextTick()
        const root = document.getElementById('clm-pdf-text-layer')
        if (chunkTextMatchesInRoot(root, chunk)) {
          found = true
          break
        }
      }
      if (!found) {
        currentPage.value = saved
        await renderPdf()
        await nextTick()
      }
    }
  } finally {
    suppressChunkHighlightReapply.value = false
  }

  const { marks } = locateChunkInPreview({
    chunk,
    isPdf: !isDocxPreview.value,
    getHighlightRoot: () => {
      if (isDocxPreview.value) {
        const doc = docxPreviewIframeRef.value?.contentDocument
        return doc?.body || null
      }
      return document.getElementById('clm-pdf-text-layer')
    },
    getPdfScrollEl: () => document.getElementById('pdf-scroll-container'),
    getPreviewIframe: () => docxPreviewIframeRef.value,
    matchHints: getChunkMatchHints(chunk),
  })
  showPreviewAskAiAfterHighlight(marks)
}

async function findChunkForComplianceByPage(pageNum) {
  if (pageNum == null || Number.isNaN(Number(pageNum)) || !pdfDoc.value) return null
  suppressChunkHighlightReapply.value = true
  try {
    const n = pdfDoc.value.numPages || 0
    const p = Math.min(Math.max(1, Math.floor(Number(pageNum))), n)
    const saved = currentPage.value
    for (const ch of contractPreviewChunks.value) {
      currentPage.value = p
      await renderPdf()
      await nextTick()
      const root = document.getElementById('clm-pdf-text-layer')
      if (chunkTextMatchesInRoot(root, ch)) {
        currentPage.value = saved
        await renderPdf()
        await nextTick()
        return ch
      }
    }
    currentPage.value = saved
    await renderPdf()
    await nextTick()
    return null
  } finally {
    suppressChunkHighlightReapply.value = false
  }
}

async function openComplianceChunkInPreview(rec) {
  const vid = primaryVersionId.value
  if (!vid || !workingVersion.value?.file_id) {
    toast('Select a document version with a file first.', 'warning')
    return
  }
  documentPreviewCanvasVisible.value = true
  documentPreviewDrawerOpen.value = true
  contractPreviewChunksDrawerOpen.value = false
  await waitForPreviewDrawerLayout()
  if (!pdfDoc.value) {
    suppressChunkHighlightReapply.value = true
    try {
      await loadPdf()
    } finally {
      suppressChunkHighlightReapply.value = false
    }
  } else {
    suppressChunkHighlightReapply.value = true
    try {
      await nextTick()
      await renderPdf()
    } finally {
      suppressChunkHighlightReapply.value = false
    }
  }
  await waitForPreviewDrawerLayout()
  await loadContractPreviewChunks()
  let chunk = null
  if (rec.chunk_index != null && rec.chunk_index !== '') {
    const idx = Number(rec.chunk_index)
    if (!Number.isNaN(idx)) {
      chunk = contractPreviewChunks.value.find((c) => c.chunk_index === idx) || null
    }
  }
  if (!chunk && !isDocxPreview.value && rec.page_number != null) {
    chunk = await findChunkForComplianceByPage(Number(rec.page_number))
  }
  if (!chunk) {
    toast('Could not match this finding to a document chunk. Re-run compliance after indexing.', 'warning')
    return
  }
  previewComplianceContextRec.value = rec
  const pref = rec.page_number != null ? Number(rec.page_number) : null
  await scrollContractChunkToPreview(chunk, {
    preferredPdfPage: pref != null && !Number.isNaN(pref) ? pref : null,
    preserveComplianceContext: true,
  })
}

function onContractDocxIframeLoad() {
  const doc = docxPreviewIframeRef.value?.contentDocument
  if (doc) injectHighlightStylesIntoDocument(doc)
  nextTick(() => reapplyActiveChunkHighlight())
}

const prevPage = () => { if (currentPage.value > 1) { currentPage.value--; renderPdf() } }
const nextPage = () => { if (currentPage.value < totalPages.value) { currentPage.value++; renderPdf() } }

const viewVersion = async (version) => {
  selectedVersionId.value = version.id
  _suppressPdfReload.value = true
  loading.value = true
  showSigned.value = false
  docxRenderFailed.value = false
  try {
    const fileType = resolveFileType(version)
    const isDocx   = fileType === 'docx' || fileType === 'doc'

    if (isDocx) {
      isDocxPreview.value = true
      pdfDoc.value = null
      try {
        await renderDocxFromUrl(`/api/contracts/${contractId}/file?version_id=${version.id}&t=${Date.now()}`)
        toast(`Now viewing Version v${version.version_number}`)
      } catch {
        // docxRenderFailed is already set inside renderDocxFromUrl; the template shows the error UI
      }
      return
    }

    isDocxPreview.value = false
    docxPreviewUrl.value = ''
    const pdfUrl = `/api/contracts/${contractId}/file?version_id=${version.id}&t=${Date.now()}`
    const pdfjsLib = await loadPdfJsLib()
    pdfDoc.value = await pdfjsLib.getDocument(pdfUrl).promise
    totalPages.value = pdfDoc.value.numPages
    currentPage.value = 1
    await renderPdf()
    toast(`Now viewing Version v${version.version_number}`)
  } catch (error) {
    console.error('Failed to load version:', error)
    swalError(`Could not load document for Version v${version.version_number}. The file may be missing on the server.`, 'File Not Found')
  } finally {
    loading.value = false
    _suppressPdfReload.value = false
  }
}

const selectAndViewVersion = (ver) => {
  viewVersion(ver)
}

const downloadSigned = async () => {
  const vid = latestVersion.value?.id
  const url = vid
    ? `/api/contracts/${contractId}/file?version=signed&version_id=${vid}`
    : `/api/contracts/${contractId}/file?version=signed`
  window.open(url, '_blank')
}

const downloadVersionSigned = (versionId) => {
  window.open(`/api/contracts/${contractId}/file?version=signed&version_id=${versionId}`, '_blank')
}

const loadPdf = async () => {
  loading.value = true
  docxRenderFailed.value = false
  try {
    const ver =
      contract.value?.document_versions?.find((v) => v.id === selectedVersionId.value) ||
      contract.value?.document_versions?.find((v) => v.is_latest) ||
      contract.value?.document_versions?.at(-1)

    const fileType = resolveFileType(ver)
    const isDocx   = fileType === 'docx' || fileType === 'doc'

    if (isDocx) {
      isDocxPreview.value = true
      pdfDoc.value = null
      const vParam = ver ? `version_id=${ver.id}` : ''
      const sParam = showSigned.value ? '&version=signed' : ''
      try {
        await renderDocxFromUrl(`/api/contracts/${contractId}/file?${vParam}${sParam}&t=${Date.now()}`)
      } catch {
        // docxRenderFailed is set inside renderDocxFromUrl; template shows error state
      }
      return
    }

    isDocxPreview.value = false
    docxPreviewUrl.value = ''

    let pdfUrl
    if (showSigned.value) {
      pdfUrl = ver
        ? `/api/contracts/${contractId}/file?version=signed&version_id=${ver.id}&t=${Date.now()}`
        : `/api/contracts/${contractId}/file?version=signed&t=${Date.now()}`
    } else {
      pdfUrl = ver
        ? `/api/contracts/${contractId}/file?version_id=${ver.id}&t=${Date.now()}`
        : `/api/contracts/${contractId}/file?version=original&t=${Date.now()}`
    }

    const pdfjsLib = await loadPdfJsLib()
    pdfDoc.value = await pdfjsLib.getDocument(pdfUrl).promise
    totalPages.value = pdfDoc.value.numPages
    currentPage.value = 1
    await renderPdf()
  } catch (error) {
    console.error('Failed to load PDF:', error)
    if (showSigned.value) {
      swalError('The signed document is not yet available or could not be loaded.', 'Not Available')
      showSigned.value = false
    } else {
      toast('Document file not found on server. Please re-upload the document.', 'warning')
    }
  } finally {
    loading.value = false
  }
}

watch(showSigned, () => {
  if (!_suppressPdfReload.value) loadPdf()
})

watch(activeTab, (tab, prev) => {
  if (tab !== 'graph' && prev === 'graph' && contract.value && !_suppressPdfReload.value) {
    nextTick(() => loadPdf())
  }
})

watch(documentPreviewDrawerOpen, (open) => {
  if (!open) {
    contractPreviewChunksDrawerOpen.value = false
    hidePreviewAskAiButton()
    previewComplianceContextRec.value = null
  }
  if (open && pdfDoc.value && activeTab.value !== 'graph') {
    nextTick(() => schedulePdfFitRerender())
  }
})

watch([primaryVersionId, contractPreviewChunksDrawerOpen], () => {
  if (contractPreviewChunksDrawerOpen.value) {
    loadContractPreviewChunks()
  }
})

watch(documentPreviewCanvasVisible, (visible) => {
  if (visible && pdfDoc.value && activeTab.value !== 'graph' && documentPreviewDrawerOpen.value) {
    nextTick(() => schedulePdfFitRerender())
  }
})

watch([chatWidth, showChat, agentChatFullscreen], () => {
  schedulePdfFitRerender()
})

let _unsubNotifications = null

onUnmounted(() => {
  removePreviewHighlightFrame()
  if (pdfFitResizeRaf) {
    cancelAnimationFrame(pdfFitResizeRaf)
    pdfFitResizeRaf = 0
  }
  if (pdfFitResizeDebounce) {
    clearTimeout(pdfFitResizeDebounce)
    pdfFitResizeDebounce = 0
  }
  window.removeEventListener('resize', syncContractViewportWidth)
  document.body.style.overflow = ''
  document.documentElement.classList.remove('clm-agent-chat-fs')
  window.removeEventListener('keydown', onAgentChatFullscreenKeydown, true)
  flushReviewStreamChunksNow()
  flushDraftStreamChunksNow()
  flushCompareStreamChunksNow()
  if (reviewChatScrollRaf) {
    cancelAnimationFrame(reviewChatScrollRaf)
    reviewChatScrollRaf = 0
  }
  if (draftChatScrollRaf) {
    cancelAnimationFrame(draftChatScrollRaf)
    draftChatScrollRaf = 0
  }
  if (compareChatScrollRaf) {
    cancelAnimationFrame(compareChatScrollRaf)
    compareChatScrollRaf = 0
  }
  if (compareStreamChunkRaf) {
    cancelAnimationFrame(compareStreamChunkRaf)
    compareStreamChunkRaf = 0
  }
  if (reviewTodosRaf) {
    cancelAnimationFrame(reviewTodosRaf)
    reviewTodosRaf = 0
  }
  if (draftTodosRaf) {
    cancelAnimationFrame(draftTodosRaf)
    draftTodosRaf = 0
  }
  graphChatSocket.value?.close()
  graphChatSocket.value = null
  reviewChatSocket.value?.close()
  reviewChatSocket.value = null
  draftChatSocket.value?.close()
  draftChatSocket.value = null
  _unsubNotifications?.()
  stopNotifications()
})

onMounted(async () => {
  syncContractViewportWidth()
  window.addEventListener('resize', syncContractViewportWidth, { passive: true })

  startNotifications()
  _unsubNotifications = onNotification(handleNotification)

  try {
    const response = await axios.get(`/api/contracts/${contractId}`)
    contract.value = response.data
    showSigned.value = !!contract.value.signed_file_path

    applyWorkingVersionFromStorageOrLatest()

    // Initialize isOpen for milestones
    if (contract.value.milestones) {
      contract.value.milestones = contract.value.milestones.map(m => ({ ...m, isOpen: false }))
    }

    // ── Detect in-flight background processing on page load ──────────────
    // WebSocket *_started events may fire before this page connects. Infer work from
    // chunks + compliance/scoring/graph so the banner and version-row spinner stay accurate
    // through the whole pipeline (not only until compliance rows exist).
    await _detectAndShowInitialProcessing()

    loadReviewItems()
    await loadPdf()
    await fetchComplaints()
  } catch (error) {
    console.error('Failed to load contract:', error)
  }
})
</script>

<style scoped>
.accordion-enter-active,
.accordion-leave-active {
  transition: opacity 0.2s ease, max-height 0.25s ease;
  overflow: hidden;
}
.accordion-enter-from,
.accordion-leave-to {
  opacity: 0;
  max-height: 0;
}
.accordion-enter-to,
.accordion-leave-from {
  opacity: 1;
  max-height: 800px;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.clm-agent-chat-shell {
  background: var(--clm-bg-surface);
  border: 1px solid var(--clm-border);
  border-radius: 1rem;
  box-shadow: 0 24px 50px -32px rgba(15, 76, 129, 0.35);
}

/* Full-screen overlay: reset sidebar card chrome (scoped rules beat stray utility conflicts). */
.clm-agent-chat-shell.clm-agent-chat-shell--fs {
  border: none;
  border-radius: 0;
  box-shadow: none;
  max-height: none;
}

/* Narrow viewports: edge-to-edge dock (override card radius from .clm-agent-chat-shell). */
.clm-agent-chat-shell.clm-agent-chat-shell--fullbleed {
  border-radius: 0;
  border-left: none;
  border-right: none;
}

.clm-agent-chat-scroll {
  scrollbar-width: none;
  -ms-overflow-style: none;
  scrollbar-color: transparent transparent;
}

.dark .clm-agent-chat-scroll {
  scrollbar-color: transparent transparent;
}

.clm-agent-chat-scroll::-webkit-scrollbar {
  width: 0px;
  height: 0px;
}

.clm-agent-chat-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.clm-agent-chat-scroll::-webkit-scrollbar-thumb {
  background-color: transparent;
  border-radius: 999px;
}

.dark .clm-agent-chat-scroll::-webkit-scrollbar-thumb {
  background-color: transparent;
}

.clm-agent-input {
  border: 1px solid var(--clm-border);
  border-radius: 999px;
  background: var(--clm-bg-surface);
  color: var(--clm-text);
  padding: 0.625rem 1rem;
  outline: none;
  transition: box-shadow 160ms ease, border-color 160ms ease;
}

.clm-agent-input::placeholder {
  color: var(--clm-text-muted);
}

.clm-agent-input:focus {
  box-shadow: 0 0 0 2px rgba(15, 76, 129, 0.2);
  border-color: var(--clm-brand);
}

.clm-agent-message-body {
  max-height: 40rem;
  overflow: auto;
  overscroll-behavior: contain;
  padding-right: 0.25rem;
}

/* ── Version Drive Picker ──────────────────────────────────────────── */
.vdp-modal {
  width: 100%; max-width: 740px; max-height: 80vh;
  background: var(--clm-bg-surface); border-radius: 16px;
  box-shadow: 0 25px 60px -12px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.05);
  display: flex; flex-direction: column; overflow: hidden;
  color: var(--clm-text);
}
:root.dark .vdp-modal { box-shadow: 0 25px 60px -12px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06); }
.vdp-body { display: grid; grid-template-columns: 210px 1fr; flex: 1; min-height: 0; overflow: hidden; }
.vdp-folder-pane { border-right: 1px solid var(--clm-border); overflow-y: auto; background: var(--clm-bg-overlay); }
.vdp-file-pane { display: flex; flex-direction: column; overflow: hidden; background: var(--clm-bg-surface); }
.vdp-folder-item {
  display: flex; align-items: center; gap: 6px; padding: 6px 10px; width: calc(100% - 6px); margin: 0 3px;
  text-align: left; cursor: pointer; transition: all 0.12s; border: 1px solid transparent; border-radius: 6px;
  color: var(--clm-text);
}
.vdp-folder-item:hover { background: var(--clm-bg-surface-elevated); }
.vdp-folder-active { background: rgba(59,130,246,0.12) !important; border-color: rgba(59,130,246,0.3); }
.vdp-file-row {
  display: flex; align-items: center; gap: 10px; padding: 7px 10px; border-radius: 8px;
  width: 100%; text-align: left; cursor: pointer; transition: all 0.12s; border: 1.5px solid transparent;
}
.vdp-file-row:hover { background: var(--clm-bg-overlay); }
.vdp-file-selected { background: rgba(59,130,246,0.1) !important; border-color: #3b82f6; }
.vdp-fade-enter-active, .vdp-fade-leave-active { transition: opacity 0.2s ease; }
.vdp-fade-enter-from, .vdp-fade-leave-to { opacity: 0; }
.vdp-scale-enter-active { transition: all 0.25s cubic-bezier(0.4,0,0.2,1); }
.vdp-scale-leave-active { transition: all 0.15s ease; }
.vdp-scale-enter-from { opacity: 0; transform: scale(0.95) translateY(8px); }
.vdp-scale-leave-to { opacity: 0; transform: scale(0.97); }

/* ── Background-task activity banner ──────────────────────────────── */
.clm-bg-task-banner-enter-active,
.clm-bg-task-banner-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.clm-bg-task-banner-enter-from,
.clm-bg-task-banner-leave-to { opacity: 0; transform: translateY(-6px); }

/* Agent guide card: subtle shimmer */
@keyframes clm-agent-guide-shimmer-move {
  0% {
    transform: translateX(-40%) skewX(-12deg);
  }
  100% {
    transform: translateX(140%) skewX(-12deg);
  }
}
.clm-agent-guide-shimmer {
  background: linear-gradient(
    105deg,
    transparent 0%,
    rgba(99, 102, 241, 0.12) 45%,
    rgba(139, 92, 246, 0.18) 50%,
    rgba(99, 102, 241, 0.12) 55%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: clm-agent-guide-shimmer-move 8s ease-in-out infinite;
}

.clm-agent-guide-collapse-enter-active,
.clm-agent-guide-collapse-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}
.clm-agent-guide-collapse-enter-from,
.clm-agent-guide-collapse-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

</style>
