<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between clm-card p-4 rounded-2xl">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Signers Registry</h1>
        <p class="text-gray-500 text-sm mt-1">Global list of people who can sign contracts. Reused across all versions.</p>
      </div>
      <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition">
        + New Signer
      </button>
    </div>

    <!-- Search -->
    <div class="bg-white dark:bg-gray-800 px-4 py-3 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 clm-page-shell">
      <input
        v-model="search"
        @input="fetchSigners"
        type="text"
        placeholder="Search by name, email, or organization..."
        class="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-900 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-2 focus:ring-[var(--clm-brand)]"
      />
    </div>

    <!-- Table -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden clm-page-shell">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400 uppercase tracking-wide text-[0.72rem] font-semibold">
            <th class="px-4 py-2.5">Name</th>
            <th class="px-4 py-2.5">Email</th>
            <th class="px-4 py-2.5">Title</th>
            <th class="px-4 py-2.5">Organization</th>
            <th class="px-4 py-2.5">Phone</th>
            <th class="px-4 py-2.5">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y dark:divide-gray-700">
          <tr v-if="loading">
            <td colspan="6" class="px-4 py-8 text-center text-gray-400">Loading...</td>
          </tr>
          <tr v-else-if="signers.length === 0">
            <td colspan="6" class="px-4 py-8 text-center text-gray-400">No signers found. Add one to get started.</td>
          </tr>
          <tr
            v-for="signer in signers"
            :key="signer.id"
            class="text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700 transition"
          >
            <td class="px-4 py-3 font-medium">{{ signer.name }}</td>
            <td class="px-4 py-3 text-gray-500 text-[0.85rem]">{{ signer.email }}</td>
            <td class="px-4 py-3 text-gray-500 text-[0.85rem]">{{ signer.title || '—' }}</td>
            <td class="px-4 py-3 text-gray-500 text-[0.85rem]">{{ signer.organization || '—' }}</td>
            <td class="px-4 py-3 text-gray-500 text-[0.85rem]">{{ signer.phone || '—' }}</td>
            <td class="px-4 py-3">
              <div class="flex gap-3">
                <button @click="openEdit(signer)" class="text-blue-600 hover:text-blue-800 font-medium text-sm">Edit</button>
                <button @click="deactivate(signer.id)" class="text-red-500 hover:text-red-700 font-medium text-sm">Remove</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl w-[480px] shadow-2xl border dark:border-gray-700">
        <h3 class="text-lg font-bold mb-5 dark:text-white">{{ editingId ? 'Edit Signer' : 'New Signer' }}</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1 dark:text-gray-300">Full Name *</label>
              <input v-model="form.name" type="text" class="w-full border rounded-lg p-2 dark:bg-gray-900 dark:border-gray-600 dark:text-white" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1 dark:text-gray-300">Email *</label>
              <input v-model="form.email" type="email" :disabled="!!editingId" class="w-full border rounded-lg p-2 dark:bg-gray-900 dark:border-gray-600 dark:text-white disabled:opacity-50" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1 dark:text-gray-300">Title / Role</label>
              <input v-model="form.title" type="text" placeholder="e.g. Director" class="w-full border rounded-lg p-2 dark:bg-gray-900 dark:border-gray-600 dark:text-white" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1 dark:text-gray-300">Phone</label>
              <input v-model="form.phone" type="text" class="w-full border rounded-lg p-2 dark:bg-gray-900 dark:border-gray-600 dark:text-white" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1 dark:text-gray-300">Organization / Ministry</label>
            <input v-model="form.organization" type="text" placeholder="e.g. Ministry of Finance" class="w-full border rounded-lg p-2 dark:bg-gray-900 dark:border-gray-600 dark:text-white" />
          </div>
          <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
        </div>
        <div class="mt-6 flex justify-end gap-3">
          <button @click="closeModal" class="px-4 py-2 text-gray-600 dark:text-gray-300">Cancel</button>
          <button @click="save" :disabled="saving" class="px-5 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition">
            {{ saving ? 'Saving...' : (editingId ? 'Save Changes' : 'Add Signer') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { toast, swalError, swalConfirm } from '../utils/swal.js'

const signers = ref([])
const search = ref('')
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const error = ref('')
const editingId = ref(null)

const form = ref({ name: '', email: '', title: '', phone: '', organization: '' })

const fetchSigners = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/master-signers/', { params: { search: search.value || undefined } })
    signers.value = res.data
  } catch (e) {
    console.error('Failed to fetch signers:', e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  form.value = { name: '', email: '', title: '', phone: '', organization: '' }
  error.value = ''
  showModal.value = true
}

const openEdit = (signer) => {
  editingId.value = signer.id
  form.value = { name: signer.name, email: signer.email, title: signer.title || '', phone: signer.phone || '', organization: signer.organization || '' }
  error.value = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  error.value = ''
}

const save = async () => {
  if (!form.value.name || !form.value.email) {
    error.value = 'Name and email are required.'
    return
  }
  saving.value = true
  error.value = ''
  try {
    if (editingId.value) {
      await axios.patch(`/api/master-signers/${editingId.value}`, form.value)
    } else {
      await axios.post('/api/master-signers/', form.value)
    }
    closeModal()
    await fetchSigners()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to save signer.'
  } finally {
    saving.value = false
  }
}

const deactivate = async (id) => {
  if (!await swalConfirm('Their historical signing records are preserved.', 'Remove this signer?', 'Remove')) return
  try {
    await axios.delete(`/api/master-signers/${id}`)
    toast('Signer removed from registry.')
    await fetchSigners()
  } catch (e) {
    swalError('Failed to remove signer.')
  }
}

onMounted(fetchSigners)
</script>
