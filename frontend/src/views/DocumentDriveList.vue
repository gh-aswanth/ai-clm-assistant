<template>
  <div class="min-h-screen p-4 sm:p-6 space-y-6 clm-page-shell">
    <!-- Hero header -->
    <section class="rounded-3xl border border-gray-200 dark:border-gray-700/60 overflow-hidden bg-gradient-to-br from-[#eef3ff] via-[#f8fbff] to-[#e8efff] dark:from-gray-900 dark:via-gray-900/80 dark:to-gray-800/70">
      <div class="px-6 pt-7 pb-5 sm:px-8 sm:pt-9 sm:pb-6 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div class="max-w-2xl">
          <p class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest text-sky-700 dark:text-sky-300">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
            Repository Hub
          </p>
          <h1 class="mt-2 text-2xl sm:text-3xl font-bold text-[var(--clm-text)] leading-tight">Document Drive</h1>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400 max-w-lg">
            Build structured libraries, create folder records, and upload files in one clean workspace.
          </p>
        </div>

        <div class="grid grid-cols-3 gap-3 text-sm w-full lg:w-auto">
          <div class="rounded-2xl bg-white/60 dark:bg-gray-800/50 border border-white/80 dark:border-gray-700 backdrop-blur px-4 py-3 text-center">
            <p class="text-[11px] font-medium uppercase text-gray-400 dark:text-gray-500">Repositories</p>
            <p class="text-xl font-bold text-[var(--clm-text)] mt-0.5">{{ drives.length }}</p>
          </div>
          <div class="rounded-2xl bg-white/60 dark:bg-gray-800/50 border border-white/80 dark:border-gray-700 backdrop-blur px-4 py-3 text-center">
            <p class="text-[11px] font-medium uppercase text-gray-400 dark:text-gray-500">Folders</p>
            <p class="text-xl font-bold text-[var(--clm-text)] mt-0.5">{{ totalFolderCount }}</p>
          </div>
          <div class="rounded-2xl bg-white/60 dark:bg-gray-800/50 border border-white/80 dark:border-gray-700 backdrop-blur px-4 py-3 text-center">
            <p class="text-[11px] font-medium uppercase text-gray-400 dark:text-gray-500">Files</p>
            <p class="text-xl font-bold text-[var(--clm-text)] mt-0.5">{{ totalFileCount }}</p>
          </div>
        </div>
      </div>

      <!-- Create form -->
      <div class="mx-4 mb-5 sm:mx-6 rounded-2xl bg-white/70 dark:bg-gray-900/50 border border-gray-200/80 dark:border-gray-700 backdrop-blur p-4 sm:p-5 grid gap-3 sm:grid-cols-[1.2fr_1fr_auto]">
        <input
          v-model="newDriveName"
          type="text"
          placeholder="Repository name"
          class="px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 dark:text-white text-sm focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 outline-none transition"
        />
        <input
          v-model="newDriveDescription"
          type="text"
          placeholder="Short description"
          class="px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 dark:text-white text-sm focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 outline-none transition"
        />
        <button
          @click="createDrive"
          :disabled="creating || !newDriveName.trim()"
          class="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white text-sm font-semibold disabled:opacity-40 transition shadow-sm"
        >
          {{ creating ? 'Creating...' : '+ New Repository' }}
        </button>
      </div>
    </section>

    <!-- Drive cards -->
    <section>
      <div v-if="loading" class="flex items-center gap-2 text-sm text-gray-400 py-8 justify-center">
        <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
        Loading repositories...
      </div>

      <div v-if="!loading && !drives.length" class="rounded-2xl border-2 border-dashed border-gray-200 dark:border-gray-700 p-12 text-center">
        <svg class="mx-auto w-10 h-10 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
        <p class="text-sm text-gray-400 mt-3">No repositories yet. Create your first one above.</p>
      </div>

      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="drive in drives"
          :key="drive.id"
          class="group rounded-2xl border border-gray-200/90 dark:border-gray-700/70 bg-white dark:bg-gray-900/40 overflow-hidden hover:shadow-xl hover:shadow-sky-500/5 hover:-translate-y-0.5 transition-all duration-200"
        >
          <div class="p-5 space-y-4">
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-900/40 flex items-center justify-center flex-shrink-0">
                  <svg class="w-5 h-5 text-sky-600 dark:text-sky-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                </div>
                <div class="min-w-0">
                  <h3 class="text-base font-semibold text-[var(--clm-text)] truncate">{{ drive.name }}</h3>
                  <p class="text-xs text-gray-400 mt-0.5 truncate max-w-[220px]">{{ drive.description || 'No description' }}</p>
                </div>
              </div>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 flex-shrink-0">
                #{{ drive.id }}
              </span>
            </div>

            <div class="grid grid-cols-3 rounded-xl bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-700/50 divide-x divide-gray-100 dark:divide-gray-700/50 text-center py-2.5">
              <div>
                <p class="text-lg font-bold text-[var(--clm-text)]">{{ folderCount(drive) }}</p>
                <p class="text-[10px] font-medium uppercase text-gray-400">Folders</p>
              </div>
              <div>
                <p class="text-lg font-bold text-[var(--clm-text)]">{{ fileCount(drive) }}</p>
                <p class="text-[10px] font-medium uppercase text-gray-400">Files</p>
              </div>
              <div>
                <p class="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                  <span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 relative -top-px"></span>
                  Active
                </p>
                <p class="text-[10px] font-medium uppercase text-gray-400">Status</p>
              </div>
            </div>
          </div>

          <div class="border-t border-gray-100 dark:border-gray-800 px-5 py-3 flex items-center justify-between gap-2">
            <router-link
              :to="{ name: 'Drive Record', params: { driveId: drive.id } }"
              class="flex-1 inline-flex justify-center items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold text-sky-700 dark:text-sky-300 hover:bg-sky-50 dark:hover:bg-sky-900/20 transition"
            >
              Open Drive
              <svg class="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
            </router-link>
            <button
              @click.stop="deleteDrive(drive)"
              class="p-2 rounded-xl text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
              title="Delete drive"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { swalError, swalConfirm, toast } from '../utils/swal.js'

const drives = ref([])
const loading = ref(false)
const creating = ref(false)
const newDriveName = ref('')
const newDriveDescription = ref('')

const folderCount = (drive) => drive.folders?.length || 0
const fileCount = (drive) =>
  (drive.folders || []).reduce((acc, folder) => acc + (folder.files || []).length, 0)
const totalFolderCount = computed(() =>
  drives.value.reduce((acc, d) => acc + (d.folders?.length || 0), 0)
)
const totalFileCount = computed(() =>
  drives.value.reduce(
    (acc, d) => acc + (d.folders || []).reduce((s, f) => s + (f.files || []).length, 0),
    0
  )
)

const loadDrives = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/document-drives')
    drives.value = data
  } catch (e) {
    console.error('Failed to load drives:', e)
    swalError('Could not load document drives')
  } finally {
    loading.value = false
  }
}

const createDrive = async () => {
  if (!newDriveName.value.trim()) return
  creating.value = true
  try {
    const { data } = await axios.post('/api/document-drives', {
      name: newDriveName.value.trim(),
      description: newDriveDescription.value.trim() || null,
    })
    drives.value = [data, ...drives.value]
    newDriveName.value = ''
    newDriveDescription.value = ''
    toast('Drive created')
  } catch (e) {
    console.error('Failed to create drive:', e)
    swalError('Could not create document drive')
  } finally {
    creating.value = false
  }
}

const deleteDrive = async (drive) => {
  const confirmed = await swalConfirm(
    `This will permanently delete "${drive.name}" and all its folders and files.`,
    'Delete Drive?',
    'Delete',
  )
  if (!confirmed) return
  try {
    await axios.delete(`/api/document-drives/${drive.id}`)
    drives.value = drives.value.filter(d => d.id !== drive.id)
    toast('Drive deleted')
  } catch (e) {
    console.error('Failed to delete drive:', e)
    swalError('Could not delete drive')
  }
}

onMounted(loadDrives)
</script>
