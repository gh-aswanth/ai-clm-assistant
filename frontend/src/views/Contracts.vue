<template>
  <div
    class="overflow-hidden rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] shadow-sm dark:bg-[var(--clm-bg-surface-elevated)] clm-page-shell"
  >
    <div
      class="flex flex-col gap-4 border-b border-[var(--clm-border)] p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h3 class="text-lg font-bold text-[var(--clm-text)]">All contracts</h3>
        <p class="mt-0.5 text-xs text-[var(--clm-text-muted)]">
          <template v-if="viewMode === 'list'">Table view with signers and actions.</template>
          <template v-else>
            Drag cards between columns to change status. The board scrolls horizontally; scroll right to reach Signed, Expired, and Terminated. Search filters cards.
          </template>
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <div
          class="inline-flex rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-overlay)]/50 p-1 dark:bg-[var(--clm-bg-overlay)]/40"
          role="group"
          aria-label="Contract layout"
        >
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold transition"
            :class="
              viewMode === 'list'
                ? 'bg-[var(--clm-bg-surface)] text-[var(--clm-text)] shadow-sm dark:bg-[var(--clm-bg-surface-elevated)]'
                : 'text-[var(--clm-text-muted)] hover:text-[var(--clm-text)]'
            "
            @click="viewMode = 'list'"
          >
            <List class="h-4 w-4" stroke-width="2" aria-hidden="true" />
            List
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold transition"
            :class="
              viewMode === 'kanban'
                ? 'bg-[var(--clm-bg-surface)] text-[var(--clm-text)] shadow-sm dark:bg-[var(--clm-bg-surface-elevated)]'
                : 'text-[var(--clm-text-muted)] hover:text-[var(--clm-text)]'
            "
            @click="viewMode = 'kanban'"
          >
            <LayoutGrid class="h-4 w-4" stroke-width="2" aria-hidden="true" />
            Kanban
          </button>
        </div>
        <input
          v-model="search"
          type="search"
          placeholder="Search…"
          class="min-w-[10rem] flex-1 rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-3 py-2.5 text-sm text-[var(--clm-text)] outline-none focus:border-[var(--clm-brand)] focus:ring-2 focus:ring-[var(--clm-brand)]/20 dark:bg-[var(--clm-bg-overlay)] sm:max-w-xs sm:flex-none"
          autocomplete="off"
        />
      </div>
    </div>

    <div v-if="loading" class="p-8">
      <div class="space-y-3">
        <div v-for="n in 5" :key="n" class="h-24 animate-pulse rounded-xl bg-[var(--clm-bg-overlay)]" />
      </div>
    </div>

    <template v-else-if="viewMode === 'kanban'">
      <div class="p-4">
        <div
          v-if="!contracts.length"
          class="py-16 text-center text-sm text-[var(--clm-text-muted)]"
        >
          No contracts yet.
        </div>
        <div
          v-else-if="!kanbanFilteredContracts.length"
          class="py-16 text-center text-sm text-[var(--clm-text-muted)]"
        >
          No contracts match your search.
        </div>
        <template v-else>
          <ContractKanban
            :contracts="kanbanFilteredContracts"
            :updating-ids="kanbanUpdatingIds"
            @status-change="onKanbanStatusChange"
          />
          <p class="mt-3 text-center text-[11px] text-[var(--clm-text-muted)]">
            Drag a card onto a column to update status. Scroll the board sideways for Signed and other stages. Prepare appears only for contracts in Signing.
          </p>
        </template>
      </div>
    </template>

    <div v-else class="space-y-3 p-4">
      <div
        v-for="contract in filteredContracts"
        :key="contract.id"
        class="group rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)]/90 p-4 transition hover:shadow-md dark:bg-[var(--clm-bg-overlay)]/40"
      >
        <div class="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_120px_150px_220px_auto]">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h4 class="font-semibold text-[var(--clm-text)]">{{ contract.title }}</h4>
              <span
                class="rounded-full px-2 py-0.5 text-[0.72rem] font-semibold"
                :class="statusClass(contract.status)"
              >
                {{ contract.status }}
              </span>
            </div>
            <p class="mt-1 text-xs text-[var(--clm-text-muted)]">{{ contract.contract_number || '—' }}</p>
            <p class="mt-1 line-clamp-2 text-[0.75rem] text-[var(--clm-text-muted)]">{{ contract.description }}</p>
          </div>

          <div class="text-sm text-[var(--clm-text-muted)]">
            <div class="font-medium text-[var(--clm-text)]">Value</div>
            <div>${{ contract.value?.toLocaleString() }}</div>
          </div>
          <div class="text-sm text-[var(--clm-text-muted)]">
            <div class="font-medium text-[var(--clm-text)]">End date</div>
            <div>{{ formatDate(contract.end_date) }}</div>
          </div>

          <div class="text-sm">
            <div class="mb-1 font-medium text-[var(--clm-text)]">Latest version signers</div>
            <div v-if="contract.document_versions?.filter((v) => v.is_latest)?.length" class="space-y-1.5">
              <div
                v-for="vs in contract.document_versions.find((v) => v.is_latest)?.version_signers"
                :key="vs.id"
                class="flex items-center justify-between gap-2"
              >
                <div class="flex min-w-0 items-center gap-1.5">
                  <span class="h-2 w-2 rounded-full" :class="statusDot(vs.status)" />
                  <span class="truncate text-[0.78rem]">{{ vs.master_signer?.name }}</span>
                </div>
                <span
                  class="rounded-full border border-[var(--clm-border)] px-2 py-0.5 text-[0.68rem]"
                  :class="
                    vs.status === 'signed'
                      ? 'bg-emerald-500/10 text-emerald-800 dark:text-emerald-300'
                      : 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)]'
                  "
                >
                  {{ vs.status }}
                </span>
              </div>
            </div>
            <div v-else class="text-[0.75rem] italic text-[var(--clm-text-muted)]">No latest version yet</div>
          </div>

          <div class="flex flex-wrap items-start justify-end gap-2">
            <router-link
              :to="'/contracts/' + contract.id"
              class="inline-flex rounded-lg bg-[var(--clm-brand)]/10 px-3 py-2 text-sm font-semibold text-[var(--clm-brand)] hover:bg-[var(--clm-brand)]/20 dark:text-sky-400"
            >
              Open
            </router-link>
            <router-link
              v-if="(contract.status || '').toLowerCase() === 'signing'"
              :to="'/prepare-signature/' + contract.id"
              class="inline-flex rounded-lg bg-emerald-600/10 px-3 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-600/20 dark:text-emerald-400"
            >
              Prepare
            </router-link>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-lg bg-red-600/10 px-3 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-600/20 dark:text-red-400"
              title="Delete contract"
              @click.stop="deleteContract(contract)"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Delete
            </button>
          </div>
        </div>
      </div>

      <div v-if="!filteredContracts.length" class="py-10 text-center text-sm text-[var(--clm-text-muted)]">
        No contracts found.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { LayoutGrid, List } from 'lucide-vue-next'
import { toast, swalConfirm, swalError } from '../utils/swal.js'
import ContractKanban from '../components/ContractKanban.vue'

const contracts = ref([])
const search = ref('')
const loading = ref(true)
const viewMode = ref('kanban')
const kanbanUpdatingIds = ref([])

const filteredContracts = computed(() => {
  if (!search.value.trim()) return contracts.value
  const q = search.value.toLowerCase()
  return contracts.value.filter(
    (c) =>
      c.title?.toLowerCase().includes(q) ||
      c.contract_number?.toLowerCase().includes(q) ||
      c.description?.toLowerCase().includes(q) ||
      c.guideline_framework_slug?.toLowerCase().includes(q) ||
      c.guideline_framework_title?.toLowerCase().includes(q),
  )
})

const kanbanFilteredContracts = computed(() => {
  if (!search.value.trim()) return contracts.value
  const q = search.value.toLowerCase()
  return contracts.value.filter(
    (c) =>
      c.title?.toLowerCase().includes(q) ||
      c.contract_number?.toLowerCase().includes(q) ||
      c.description?.toLowerCase().includes(q) ||
      c.guideline_framework_slug?.toLowerCase().includes(q) ||
      c.guideline_framework_title?.toLowerCase().includes(q),
  )
})

const statusClass = (status) => {
  switch (status?.toLowerCase()) {
    case 'active':
      return 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300'
    case 'review':
      return 'bg-amber-500/15 text-amber-900 dark:text-amber-200'
    case 'signing':
      return 'bg-violet-500/15 text-violet-900 dark:text-violet-200'
    case 'draft':
      return 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)]'
    case 'redraft':
      return 'bg-orange-500/15 text-orange-900 dark:text-orange-200'
    case 'approved':
      return 'bg-blue-500/15 text-blue-900 dark:text-blue-200'
    case 'expired':
      return 'bg-red-500/10 text-red-800 dark:text-red-300'
    case 'terminated':
      return 'bg-red-500/15 text-red-900 dark:text-red-200'
    default:
      return 'bg-[var(--clm-bg-overlay)] text-[var(--clm-text-muted)]'
  }
}

const statusDot = (status) => {
  switch (status) {
    case 'signed':
      return 'bg-green-500'
    case 'invited':
      return 'bg-yellow-500'
    case 'declined':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
}

const formatDate = (d) => (d ? new Date(d).toISOString().split('T')[0] : '—')

const deleteContract = async (contract) => {
  const confirmed = await swalConfirm(
    `This will permanently delete "${contract.title}" and all its versions, signers, and compliance records.`,
    'Delete Contract?',
    'Delete',
  )
  if (!confirmed) return
  try {
    await axios.delete(`/api/contracts/${contract.id}`)
    contracts.value = contracts.value.filter((c) => c.id !== contract.id)
    toast('Contract deleted')
  } catch (e) {
    console.error('Failed to delete contract:', e)
    swalError('Could not delete contract')
  }
}

async function onKanbanStatusChange({ contractId, nextStatus, previousStatus }) {
  const c = contracts.value.find((x) => x.id === contractId)
  if (!c) return
  const prev = c.status ?? previousStatus
  if ((prev || '').toLowerCase() === (nextStatus || '').toLowerCase()) return
  if (!kanbanUpdatingIds.value.includes(contractId)) {
    kanbanUpdatingIds.value = [...kanbanUpdatingIds.value, contractId]
  }
  c.status = nextStatus
  try {
    await axios.patch(`/api/contracts/${contractId}/status`, { status: nextStatus })
    toast('Status updated')
  } catch (e) {
    c.status = prev
    console.error(e)
    const msg = e.response?.data?.detail
    swalError(typeof msg === 'string' ? msg : 'Could not update contract status.')
  } finally {
    kanbanUpdatingIds.value = kanbanUpdatingIds.value.filter((id) => id !== contractId)
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/contracts/', { params: { limit: 500, skip: 0 } })
    contracts.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    console.error('Failed to fetch contracts:', e)
  } finally {
    loading.value = false
  }
})
</script>
