<template>
  <div class="dashboard-root mx-auto max-w-7xl space-y-8 pb-10">
    <!-- Hero -->
    <section
      class="relative overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-gradient-to-br from-[var(--clm-bg-surface)] via-[var(--clm-bg-surface-elevated)] to-[var(--clm-brand-soft)]/35 px-6 py-8 shadow-sm dark:from-[var(--clm-bg-surface)] dark:via-[var(--clm-bg-surface-elevated)] dark:to-[var(--clm-brand-soft)]/25 sm:px-8 sm:py-10"
    >
      <div
        class="pointer-events-none absolute -right-16 -top-24 h-56 w-56 rounded-full bg-[var(--clm-brand)]/10 blur-3xl dark:bg-sky-500/10"
        aria-hidden="true"
      />
      <div
        class="pointer-events-none absolute -bottom-20 -left-10 h-48 w-48 rounded-full bg-cyan-500/10 blur-3xl dark:bg-cyan-500/5"
        aria-hidden="true"
      />
      <div class="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div class="min-w-0">
          <p class="text-xs font-bold uppercase tracking-[0.2em] text-[var(--clm-text-muted)]">
            Overview
          </p>
          <h1 class="mt-2 text-balance text-2xl font-extrabold tracking-tight text-[var(--clm-text)] sm:text-3xl lg:text-4xl">
            Contract workspace
          </h1>
          <p class="mt-2 max-w-xl text-sm leading-relaxed text-[var(--clm-text-muted)] sm:text-base">
            KPIs, full pipeline visibility with lifecycle progress, and one-click access to every agreement—without leaving this page.
          </p>
        </div>
        <div class="flex flex-shrink-0 flex-wrap items-center gap-3">
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-4 py-3 text-sm font-bold text-[var(--clm-text)] transition hover:border-[var(--clm-brand)]/40 hover:bg-[var(--clm-brand-soft)]/40 dark:bg-[var(--clm-bg-overlay)]/80"
            :disabled="refreshing"
            title="Refresh dashboard data"
            @click="loadDashboard(true)"
          >
            <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': refreshing }" stroke-width="2" aria-hidden="true" />
            Refresh
          </button>
          <router-link
            to="/create-contract"
            class="inline-flex items-center justify-center gap-2 rounded-xl bg-[var(--clm-brand)] px-5 py-3 text-sm font-bold text-white shadow-lg shadow-[var(--clm-brand)]/25 transition hover:bg-[var(--clm-brand-strong)]"
          >
            <Plus class="h-4 w-4" stroke-width="2.5" aria-hidden="true" />
            New contract
          </router-link>
          <router-link
            to="/contracts"
            class="inline-flex items-center justify-center rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-4 py-3 text-sm font-bold text-[var(--clm-text)] transition hover:border-[var(--clm-brand)]/40 dark:bg-[var(--clm-bg-overlay)]/80"
          >
            Full library
          </router-link>
        </div>
      </div>
    </section>

    <!-- KPI strip -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      <article
        v-for="(tile, i) in statTiles"
        :key="tile.id"
        class="group relative overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] p-5 shadow-sm transition hover:border-[var(--clm-brand)]/25 hover:shadow-md dark:bg-[var(--clm-bg-surface-elevated)]"
      >
        <div
          class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          :class="tile.glow"
          aria-hidden="true"
        />
        <div class="relative flex items-start justify-between gap-3">
          <div
            class="flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--clm-border)]/80 bg-[var(--clm-bg-overlay)]/60 text-[var(--clm-brand)] dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)]/50 dark:text-sky-400"
          >
            <component :is="tile.icon" class="h-5 w-5" stroke-width="2" aria-hidden="true" />
          </div>
          <span class="text-[10px] font-bold uppercase tracking-wider text-[var(--clm-text-muted)]">
            {{ String(i + 1).padStart(2, '0') }}
          </span>
        </div>
        <div class="relative mt-5">
          <div
            v-if="statsLoading"
            class="h-9 w-20 animate-pulse rounded-lg bg-[var(--clm-bg-overlay)] dark:bg-[var(--clm-bg-overlay)]"
          />
          <div v-else class="text-3xl font-black tabular-nums tracking-tight text-[var(--clm-text)]">
            {{ tile.displayValue }}
          </div>
          <div class="mt-1 text-sm font-semibold text-[var(--clm-text)]">{{ tile.label }}</div>
          <p class="mt-1 text-xs leading-snug text-[var(--clm-text-muted)]">{{ tile.hint }}</p>
        </div>
      </article>
    </section>

    <!-- Status distribution -->
    <section
      v-if="!contractsLoading && allContracts.length"
      class="flex flex-wrap gap-2 rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] p-4 dark:bg-[var(--clm-bg-surface-elevated)]"
      aria-label="Filter by contract status"
    >
      <button
        type="button"
        class="rounded-full px-3 py-1.5 text-xs font-bold transition"
        :class="
          statusFilter === ''
            ? 'bg-[var(--clm-brand)] text-white shadow-sm'
            : 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)] hover:bg-[var(--clm-brand-soft)]/60'
        "
        @click="statusFilter = ''"
      >
        All · {{ allContracts.length }}
      </button>
      <button
        v-for="opt in statusFilterOptions"
        :key="opt.value"
        type="button"
        class="rounded-full px-3 py-1.5 text-xs font-bold capitalize transition"
        :class="
          statusFilter === opt.value
            ? 'bg-[var(--clm-brand)] text-white shadow-sm'
            : 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text)] hover:bg-[var(--clm-brand-soft)]/60'
        "
        @click="statusFilter = opt.value"
      >
        {{ opt.label }}
        <span class="tabular-nums opacity-80">({{ statusCounts[opt.value] || 0 }})</span>
      </button>
    </section>

    <section class="grid gap-6 lg:grid-cols-3">
      <!-- All contracts + pipeline -->
      <div class="min-w-0 lg:col-span-2">
        <div class="flex flex-col gap-4 border-b border-[var(--clm-border)] pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 class="text-lg font-bold text-[var(--clm-text)]">Contract pipeline</h2>
            <p class="mt-0.5 text-xs text-[var(--clm-text-muted)]">
              Every record with lifecycle progress—open any contract; Prepare appears when status is Signing.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <div class="relative min-w-[10rem] flex-1 sm:max-w-xs">
              <Search
                class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--clm-text-muted)]"
                stroke-width="2"
                aria-hidden="true"
              />
              <input
                v-model="searchQuery"
                type="search"
                placeholder="Search title, number, description…"
                class="w-full rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] py-2.5 pl-10 pr-3 text-sm text-[var(--clm-text)] outline-none focus:border-[var(--clm-brand)] focus:ring-2 focus:ring-[var(--clm-brand)]/20 dark:bg-[var(--clm-bg-overlay)]"
                autocomplete="off"
              />
            </div>
            <select
              v-model="sortKey"
              class="rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-3 py-2.5 text-xs font-bold text-[var(--clm-text)] outline-none focus:border-[var(--clm-brand)] dark:bg-[var(--clm-bg-overlay)]"
              aria-label="Sort contracts"
            >
              <option value="updated_desc">Recently updated</option>
              <option value="created_desc">Newest first</option>
              <option value="title_asc">Title A–Z</option>
              <option value="value_desc">Value high → low</option>
              <option value="status">Lifecycle stage</option>
            </select>
          </div>
        </div>

        <div
          class="mt-4 overflow-hidden rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm dark:bg-[var(--clm-bg-surface-elevated)]"
        >
          <div v-if="contractsLoading" class="divide-y divide-[var(--clm-divider)] p-2">
            <div v-for="n in 6" :key="n" class="animate-pulse rounded-xl p-4">
              <div class="h-5 max-w-md rounded bg-[var(--clm-bg-overlay)]" />
              <div class="mt-3 h-2 rounded-full bg-[var(--clm-bg-overlay)]" />
              <div class="mt-4 flex gap-2">
                <div class="h-9 w-20 rounded-lg bg-[var(--clm-bg-overlay)]" />
                <div class="h-9 w-20 rounded-lg bg-[var(--clm-bg-overlay)]" />
              </div>
            </div>
          </div>
          <template v-else-if="allContracts.length === 0">
            <div class="flex flex-col items-center justify-center px-6 py-16 text-center">
              <div
                class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-dashed border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/50 text-[var(--clm-text-muted)]"
              >
                <FileStack class="h-7 w-7" stroke-width="1.5" aria-hidden="true" />
              </div>
              <p class="font-semibold text-[var(--clm-text)]">No contracts yet</p>
              <p class="mt-1 max-w-sm text-sm text-[var(--clm-text-muted)]">
                Create a contract to populate the pipeline and track progress here.
              </p>
              <router-link
                to="/create-contract"
                class="mt-5 inline-flex items-center gap-2 rounded-xl bg-[var(--clm-brand)] px-4 py-2.5 text-sm font-bold text-white"
              >
                <Plus class="h-4 w-4" stroke-width="2.5" aria-hidden="true" />
                Create first contract
              </router-link>
            </div>
          </template>
          <template v-else-if="filteredSortedContracts.length === 0">
            <div class="px-6 py-14 text-center text-sm text-[var(--clm-text-muted)]">
              No contracts match your search or filter.
            </div>
          </template>
          <div v-else class="max-h-[min(70vh,560px)] overflow-y-auto overflow-x-hidden">
            <ul class="divide-y divide-[var(--clm-divider)]" role="list">
              <li
                v-for="c in filteredSortedContracts"
                :key="c.id"
                class="p-4 transition hover:bg-[var(--clm-brand-soft)]/25 dark:hover:bg-[var(--clm-brand-soft)]/15"
              >
                <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-5">
                  <div class="min-w-0 flex-1 lg:max-w-[min(100%,20rem)]">
                    <div class="flex flex-wrap items-center gap-2">
                      <p class="truncate font-semibold text-[var(--clm-text)]">{{ c.title }}</p>
                      <span
                        class="shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide"
                        :class="statusClass(c.status)"
                      >
                        {{ c.status }}
                      </span>
                    </div>
                    <p class="mt-0.5 font-mono text-xs text-[var(--clm-text-muted)]">
                      {{ c.contract_number || `ID ${c.id}` }}
                    </p>
                    <p v-if="c.description" class="mt-1 line-clamp-2 text-xs text-[var(--clm-text-muted)]">
                      {{ c.description }}
                    </p>
                    <div
                      v-if="latestContractVersion(c) || c.file_type"
                      class="mt-2 flex flex-wrap items-center gap-2"
                    >
                      <span
                        v-if="latestContractVersion(c)"
                        class="inline-flex max-w-full flex-wrap items-center gap-x-1.5 gap-y-0.5 rounded-md bg-[var(--clm-bg-overlay)] px-2 py-0.5 text-[10px] font-bold text-[var(--clm-text)]"
                      >
                        <FileType class="h-3 w-3 shrink-0 text-[var(--clm-text-muted)]" stroke-width="2" aria-hidden="true" />
                        <span class="tabular-nums">v{{ latestContractVersion(c).version_number }}</span>
                        <span
                          v-if="latestContractVersion(c).is_latest"
                          class="rounded bg-sky-500/15 px-1 py-px text-[8px] font-black uppercase leading-none text-sky-900 dark:bg-sky-500/20 dark:text-sky-200"
                        >Latest</span>
                        <span class="font-bold uppercase text-[var(--clm-text-muted)]">{{ versionFileTypeLabel(latestContractVersion(c)) }}</span>
                      </span>
                      <span
                        v-else-if="c.file_type"
                        class="inline-flex items-center gap-1 rounded-md bg-[var(--clm-bg-overlay)] px-2 py-0.5 text-[10px] font-bold uppercase text-[var(--clm-text-muted)]"
                      >
                        <FileType class="h-3 w-3" stroke-width="2" aria-hidden="true" />
                        {{ c.file_type }}
                      </span>
                    </div>
                  </div>

                  <div class="min-w-0 flex-[1.4]">
                    <p class="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-[var(--clm-text-muted)]">
                      Lifecycle progress
                    </p>
                    <div class="h-2.5 w-full overflow-hidden rounded-full bg-[var(--clm-bg-overlay)] dark:bg-[var(--clm-bg-overlay)]">
                      <div
                        class="h-full rounded-full transition-all duration-500"
                        :class="progressBarClass(c.status)"
                        :style="{ width: `${lifecycleProgressPct(c.status)}%` }"
                      />
                    </div>
                    <div
                      class="mt-2 flex gap-1 overflow-x-auto pb-0.5 text-[9px] font-bold uppercase tracking-wide text-[var(--clm-text-muted)]"
                    >
                      <span
                        v-for="step in LIFECYCLE_STEPS"
                        :key="step.key"
                        class="shrink-0"
                        :class="stepLabelClass(c.status, step.key)"
                      >
                        {{ step.label }}
                      </span>
                    </div>
                    <p v-if="isTerminalStatus(c.status)" class="mt-1 text-[10px] font-semibold text-[var(--clm-text-muted)]">
                      {{ terminalHint(c.status) }}
                    </p>
                  </div>

                  <div class="flex flex-wrap items-center gap-3 lg:w-[14rem] lg:flex-col lg:items-stretch">
                    <div class="text-xs text-[var(--clm-text-muted)]">
                      <div class="font-semibold text-[var(--clm-text)]">{{ formatMoney(c.value) }}</div>
                      <div class="mt-0.5">Updated {{ formatDate(c.updated_at || c.created_at) }}</div>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <router-link
                        :to="`/contracts/${c.id}`"
                        class="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-[var(--clm-brand)] px-3 py-2 text-xs font-bold text-white shadow-sm transition hover:bg-[var(--clm-brand-strong)] lg:flex-none"
                      >
                        <ExternalLink class="h-3.5 w-3.5" stroke-width="2" aria-hidden="true" />
                        Open
                      </router-link>
                      <router-link
                        v-if="canPrepareSignature(c.status)"
                        :to="`/prepare-signature/${c.id}`"
                        class="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs font-bold text-emerald-800 transition hover:bg-emerald-500/20 dark:text-emerald-300 lg:flex-none"
                      >
                        <PenLine class="h-3.5 w-3.5" stroke-width="2" aria-hidden="true" />
                        Prepare
                      </router-link>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Side column -->
      <div class="space-y-6">
        <div>
          <div class="border-b border-[var(--clm-border)] pb-4">
            <h2 class="text-lg font-bold text-[var(--clm-text)]">Upcoming milestones</h2>
            <p class="mt-0.5 text-xs text-[var(--clm-text-muted)]">Pending items with future due dates</p>
          </div>
          <div
            class="mt-4 space-y-3 rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] p-4 shadow-sm dark:bg-[var(--clm-bg-surface-elevated)]"
          >
            <div v-if="statsLoading" class="space-y-3">
              <div v-for="n in 4" :key="n" class="h-16 animate-pulse rounded-xl bg-[var(--clm-bg-overlay)]" />
            </div>
            <template v-else-if="upcomingMilestones.length === 0">
              <p class="py-6 text-center text-sm text-[var(--clm-text-muted)]">No upcoming milestones.</p>
            </template>
            <ul v-else class="space-y-2" role="list">
              <li v-for="m in upcomingMilestones" :key="m.id">
                <router-link
                  v-if="m.contract_id"
                  :to="`/contracts/${m.contract_id}`"
                  class="flex gap-3 rounded-xl border border-transparent p-3 transition hover:border-[var(--clm-border)] hover:bg-[var(--clm-bg-overlay)]/50"
                >
                  <div
                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--clm-brand-soft)] text-[var(--clm-brand)] dark:text-sky-400"
                  >
                    <Calendar class="h-5 w-5" stroke-width="2" aria-hidden="true" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-semibold leading-snug text-[var(--clm-text)]">{{ m.title }}</p>
                    <p class="mt-0.5 text-xs text-[var(--clm-text-muted)]">{{ m.due_label }}</p>
                    <p
                      class="mt-1 text-[10px] font-bold uppercase tracking-wide"
                      :class="milestoneStatusClass(m.status)"
                    >
                      {{ m.status }}
                    </p>
                  </div>
                </router-link>
                <div
                  v-else
                  class="flex gap-3 rounded-xl border border-[var(--clm-border)]/60 p-3 dark:border-[var(--clm-border)]"
                >
                  <div
                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--clm-brand-soft)] text-[var(--clm-brand)] dark:text-sky-400"
                  >
                    <Calendar class="h-5 w-5" stroke-width="2" aria-hidden="true" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-semibold text-[var(--clm-text)]">{{ m.title }}</p>
                    <p class="mt-0.5 text-xs text-[var(--clm-text-muted)]">{{ m.due_label }}</p>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <div>
          <div class="border-b border-[var(--clm-border)] pb-4">
            <h2 class="text-lg font-bold text-[var(--clm-text)]">CPWD Copilot</h2>
            <p class="mt-0.5 text-xs text-[var(--clm-text-muted)]">
              Premium — guideline-aware Review and Draft on each contract
            </p>
          </div>
          <div
            class="mt-4 space-y-3 rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] p-4 shadow-sm dark:bg-[var(--clm-bg-surface-elevated)]"
          >
            <div class="flex gap-3">
              <div
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-violet-500/15 text-violet-700 dark:bg-violet-500/20 dark:text-violet-300"
              >
                <Sparkles class="h-5 w-5" stroke-width="2" aria-hidden="true" />
              </div>
              <p class="min-w-0 text-sm leading-relaxed text-[var(--clm-text-muted)]">
                Open a contract, choose Review or Draft in the assistant, and turn on CPWD Copilot. The agent receives your
                guideline snapshot, compliance rows, and scoring; Draft also uses saved review items, Review does not.
              </p>
            </div>
            <router-link
              to="/contracts"
              class="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--clm-border)] px-3 py-2.5 text-xs font-semibold text-[var(--clm-text)] transition hover:bg-[var(--clm-brand-soft)]/50"
            >
              <FolderKanban class="h-4 w-4 text-[var(--clm-brand)] dark:text-sky-400" stroke-width="2" aria-hidden="true" />
              Browse contracts
            </router-link>
          </div>
        </div>

        <div
          class="rounded-2xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] p-5 shadow-sm dark:bg-[var(--clm-bg-surface-elevated)]"
        >
          <h3 class="text-sm font-bold text-[var(--clm-text)]">Workspace</h3>
          <p class="mt-1 text-xs text-[var(--clm-text-muted)]">Tools and registries</p>
          <nav class="mt-4 grid gap-2" aria-label="Workspace shortcuts">
            <router-link
              to="/contracts"
              class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-[var(--clm-text)] transition hover:bg-[var(--clm-brand-soft)]/50"
            >
              <FolderKanban class="h-4 w-4 text-[var(--clm-brand)] dark:text-sky-400" stroke-width="2" />
              All contracts
            </router-link>
            <router-link
              to="/guidelines"
              class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-[var(--clm-text)] transition hover:bg-[var(--clm-brand-soft)]/50"
            >
              <BookMarked class="h-4 w-4 text-[var(--clm-brand)] dark:text-sky-400" stroke-width="2" />
              Guidelines
            </router-link>
            <router-link
              to="/document-drive"
              class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-[var(--clm-text)] transition hover:bg-[var(--clm-brand-soft)]/50"
            >
              <HardDrive class="h-4 w-4 text-[var(--clm-brand)] dark:text-sky-400" stroke-width="2" />
              Document drive
            </router-link>
            <router-link
              to="/master-signers"
              class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-[var(--clm-text)] transition hover:bg-[var(--clm-brand-soft)]/50"
            >
              <UserCheck class="h-4 w-4 text-[var(--clm-brand)] dark:text-sky-400" stroke-width="2" />
              Signers registry
            </router-link>
            <router-link
              v-if="isAdmin"
              to="/users"
              class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-[var(--clm-text)] transition hover:bg-[var(--clm-brand-soft)]/50"
            >
              <Users class="h-4 w-4 text-[var(--clm-brand)] dark:text-sky-400" stroke-width="2" />
              User management
            </router-link>
          </nav>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import {
  Activity,
  BookMarked,
  Calendar,
  CircleDollarSign,
  ExternalLink,
  FileStack,
  FileType,
  FolderKanban,
  HardDrive,
  Hourglass,
  PenLine,
  Plus,
  RefreshCw,
  Sparkles,
  Search,
  UserCheck,
  Users,
} from 'lucide-vue-next'
import { authStore } from '../utils/auth'
import { latestContractVersion, versionFileTypeLabel } from '../utils/contractVersion.js'

/** Ordered lifecycle used for progress bar and step labels */
const LIFECYCLE_STEPS = [
  { key: 'draft', label: 'Draft' },
  { key: 'review', label: 'Review' },
  { key: 'redraft', label: 'Redraft' },
  { key: 'approved', label: 'Approved' },
  { key: 'signing', label: 'Signing' },
  { key: 'active', label: 'Active' },
]

const LIFECYCLE_ORDER = LIFECYCLE_STEPS.map((s) => s.key)

const statsLoading = ref(true)
const contractsLoading = ref(true)
const refreshing = ref(false)
const stats = ref({
  total_contracts: '—',
  active_contracts: '—',
  pending_approval: '—',
  total_value: '—',
})
const allContracts = ref([])
const upcomingMilestones = ref([])

const searchQuery = ref('')
const statusFilter = ref('')
const sortKey = ref('updated_desc')

const isAdmin = computed(() => authStore.user?.role === 'admin')

const statusFilterOptions = [
  { value: 'draft', label: 'draft' },
  { value: 'review', label: 'review' },
  { value: 'redraft', label: 'redraft' },
  { value: 'approved', label: 'approved' },
  { value: 'signing', label: 'signing' },
  { value: 'active', label: 'active' },
  { value: 'expired', label: 'expired' },
  { value: 'terminated', label: 'terminated' },
]

const statusCounts = computed(() => {
  const m = {}
  for (const c of allContracts.value) {
    const k = (c.status || 'draft').toLowerCase()
    m[k] = (m[k] || 0) + 1
  }
  return m
})

const filteredSortedContracts = computed(() => {
  let list = [...allContracts.value]
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      (c) =>
        (c.title || '').toLowerCase().includes(q) ||
        (c.contract_number || '').toLowerCase().includes(q) ||
        (c.description || '').toLowerCase().includes(q),
    )
  }
  if (statusFilter.value) {
    const f = statusFilter.value.toLowerCase()
    list = list.filter((c) => (c.status || '').toLowerCase() === f)
  }

  const lifecycleRank = (s) => {
    const i = LIFECYCLE_ORDER.indexOf((s || 'draft').toLowerCase())
    return i >= 0 ? i : 99
  }

  list.sort((a, b) => {
    switch (sortKey.value) {
      case 'title_asc':
        return (a.title || '').localeCompare(b.title || '', undefined, { sensitivity: 'base' })
      case 'value_desc':
        return (Number(b.value) || 0) - (Number(a.value) || 0)
      case 'created_desc': {
        const ta = new Date(a.created_at || 0).getTime()
        const tb = new Date(b.created_at || 0).getTime()
        return tb - ta
      }
      case 'status':
        return lifecycleRank(a.status) - lifecycleRank(b.status) || (a.title || '').localeCompare(b.title || '')
      case 'updated_desc':
      default: {
        const ua = new Date(a.updated_at || a.created_at || 0).getTime()
        const ub = new Date(b.updated_at || b.created_at || 0).getTime()
        return ub - ua
      }
    }
  })
  return list
})

const statTiles = computed(() => {
  const s = stats.value
  return [
    {
      id: 'total',
      label: 'Total contracts',
      hint: 'All agreements in the system',
      displayValue: s.total_contracts,
      icon: FileStack,
      glow: 'bg-gradient-to-br from-blue-500/5 to-transparent dark:from-sky-500/10',
    },
    {
      id: 'active',
      label: 'Active',
      hint: 'Currently in force',
      displayValue: s.active_contracts,
      icon: Activity,
      glow: 'bg-gradient-to-br from-emerald-500/5 to-transparent dark:from-emerald-400/10',
    },
    {
      id: 'pending',
      label: 'In review / signing',
      hint: 'Needs legal or signatures',
      displayValue: s.pending_approval,
      icon: Hourglass,
      glow: 'bg-gradient-to-br from-amber-500/5 to-transparent dark:from-amber-400/10',
    },
    {
      id: 'value',
      label: 'Portfolio value',
      hint: 'Sum of contract values',
      displayValue: s.total_value,
      icon: CircleDollarSign,
      glow: 'bg-gradient-to-br from-violet-500/5 to-transparent dark:from-violet-400/10',
    },
    {
      id: 'cpwd_copilot',
      label: 'CPWD Copilot',
      hint: 'Premium context for Review & Draft agents (guidelines, compliance, scoring)',
      displayValue: authStore.user?.premium_access === false ? 'Limited' : 'Available',
      icon: Sparkles,
      glow: 'bg-gradient-to-br from-violet-500/8 to-transparent dark:from-violet-400/12',
    },
  ]
})

function lifecycleIndex(status) {
  const s = (status || 'draft').toLowerCase()
  const i = LIFECYCLE_ORDER.indexOf(s)
  return i >= 0 ? i : -1
}

function lifecycleProgressPct(status) {
  const s = (status || 'draft').toLowerCase()
  if (s === 'expired' || s === 'terminated') return 100
  const i = lifecycleIndex(status)
  if (i < 0) return 6
  return Math.round(((i + 1) / LIFECYCLE_ORDER.length) * 100)
}

function progressBarClass(status) {
  const s = (status || '').toLowerCase()
  if (s === 'terminated') return 'bg-red-500 dark:bg-red-500'
  if (s === 'expired') return 'bg-amber-500 dark:bg-amber-500'
  return 'bg-gradient-to-r from-[var(--clm-brand)] to-cyan-500 dark:from-sky-500 dark:to-cyan-400'
}

function stepLabelClass(contractStatus, stepKey) {
  const s = (contractStatus || 'draft').toLowerCase()
  if (s === 'terminated') return 'text-red-500/90 line-through opacity-70'
  if (s === 'expired') return 'text-amber-600/90 opacity-80'
  const cur = lifecycleIndex(contractStatus)
  const si = LIFECYCLE_ORDER.indexOf(stepKey)
  if (cur < 0) return 'opacity-40'
  if (si < cur) return 'text-emerald-600/90 dark:text-emerald-400/90'
  if (si === cur) return 'text-[var(--clm-brand)] dark:text-sky-400'
  return 'opacity-35'
}

function isTerminalStatus(status) {
  const s = (status || '').toLowerCase()
  return s === 'expired' || s === 'terminated'
}

function terminalHint(status) {
  const s = (status || '').toLowerCase()
  if (s === 'terminated') return 'Agreement ended — bar shows closed state.'
  if (s === 'expired') return 'Past end date — renew or archive as needed.'
  return ''
}

function canPrepareSignature(status) {
  return (status || '').toLowerCase() === 'signing'
}

function formatMoney(v) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return `$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

function formatDate(d) {
  if (!d) return '—'
  try {
    return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return '—'
  }
}

function statusClass(status) {
  const map = {
    active: 'bg-[var(--clm-brand-soft)] text-[var(--clm-brand-strong)] dark:bg-sky-500/15 dark:text-sky-300',
    approved: 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300',
    draft: 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)]',
    review: 'bg-amber-500/15 text-amber-900 dark:text-amber-200',
    redraft: 'bg-orange-500/15 text-orange-900 dark:text-orange-200',
    signing: 'bg-violet-500/15 text-violet-900 dark:text-violet-200',
    expired: 'bg-red-500/10 text-red-800 dark:text-red-300',
    terminated: 'bg-red-500/15 text-red-900 dark:text-red-200',
  }
  return map[(status || '').toLowerCase()] || 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)]'
}

function milestoneStatusClass(status) {
  const map = {
    pending: 'text-amber-600 dark:text-amber-400',
    completed: 'text-emerald-600 dark:text-emerald-400',
    delayed: 'text-red-600 dark:text-red-400',
  }
  return map[status] || 'text-[var(--clm-text-muted)]'
}

async function loadDashboard(isRefresh = false) {
  if (isRefresh) {
    refreshing.value = true
  } else {
    statsLoading.value = true
    contractsLoading.value = true
  }
  try {
    const [dashRes, contractsRes] = await Promise.all([
      axios.get('/api/dashboard/stats'),
      axios.get('/api/contracts/', { params: { limit: 500, skip: 0 } }),
    ])
    const data = dashRes.data
    stats.value = {
      total_contracts: data.stats.total_contracts,
      active_contracts: data.stats.active_contracts,
      pending_approval: data.stats.pending_approval,
      total_value: data.stats.total_value,
    }
    upcomingMilestones.value = data.upcoming_milestones || []
    allContracts.value = Array.isArray(contractsRes.data) ? contractsRes.data : []
  } catch (e) {
    console.error('Failed to load dashboard', e)
  } finally {
    statsLoading.value = false
    contractsLoading.value = false
    refreshing.value = false
  }
}

onMounted(() => {
  loadDashboard(false)
})
</script>
