<template>
  <div>

    <!-- Page header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-lg font-bold text-[var(--clm-text)]">User Management</h2>
        <p class="text-sm text-[var(--clm-muted)] mt-0.5">Manage platform accounts and access roles</p>
      </div>
      <button
        @click="openCreate"
        class="clm-btn-primary px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Add User
      </button>
    </div>

    <!-- Users table -->
    <div class="clm-card rounded-xl shadow-sm overflow-hidden">
      <div v-if="loading" class="py-16 text-center text-[var(--clm-muted)] text-sm">Loading users…</div>
      <div v-else-if="users.length === 0" class="py-16 text-center text-[var(--clm-muted)] text-sm">
        No users found.
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b clm-border bg-[var(--clm-bg)]">
            <th class="text-left px-6 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)]">User</th>
            <th class="text-left px-6 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)]">Role</th>
            <th class="text-left px-6 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)]">Status</th>
            <th class="text-left px-6 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)]">Created</th>
            <th class="px-6 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in users"
            :key="user.id"
            class="border-b last:border-0 clm-border hover:bg-[var(--clm-bg)] transition"
          >
            <!-- Avatar + name/email -->
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-[var(--clm-brand)] flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  {{ initials(user.full_name) }}
                </div>
                <div>
                  <div class="font-semibold text-[var(--clm-text)]">{{ user.full_name }}</div>
                  <div class="text-xs text-[var(--clm-muted)]">{{ user.email }}</div>
                </div>
              </div>
            </td>
            <!-- Role -->
            <td class="px-6 py-4">
              <span :class="roleClass(user.role)" class="px-2.5 py-1 rounded-full text-xs font-semibold capitalize">
                {{ user.role }}
              </span>
            </td>
            <!-- Status -->
            <td class="px-6 py-4">
              <span :class="user.is_active ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'"
                class="px-2.5 py-1 rounded-full text-xs font-semibold">
                {{ user.is_active ? 'Active' : 'Disabled' }}
              </span>
            </td>
            <!-- Created -->
            <td class="px-6 py-4 text-[var(--clm-muted)] text-xs">{{ formatDate(user.created_at) }}</td>
            <!-- Actions -->
            <td class="px-6 py-4">
              <div class="flex items-center gap-2 justify-end">
                <button
                  @click="toggleActive(user)"
                  :title="user.is_active ? 'Disable account' : 'Enable account'"
                  class="clm-icon-btn text-xs"
                >
                  <svg v-if="user.is_active" class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/>
                  </svg>
                  <svg v-else class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </button>
                <button
                  v-if="user.id !== currentUser?.id"
                  @click="confirmDelete(user)"
                  title="Delete user"
                  class="clm-icon-btn"
                >
                  <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / Add User Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
        <div class="clm-card rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">

          <!-- Modal header -->
          <div class="px-6 py-5 border-b clm-border flex items-center justify-between">
            <h3 class="font-bold text-[var(--clm-text)]">Add New User</h3>
            <button @click="closeModal" class="clm-icon-btn">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Modal body -->
          <form @submit.prevent="submitCreate" class="px-6 py-6 space-y-4">

            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)] mb-1.5">Full Name</label>
              <input
                v-model="form.full_name"
                type="text"
                placeholder="Jane Doe"
                class="clm-input w-full px-3 py-2.5 text-sm rounded-lg"
                :class="{ 'border-red-500': formErrors.full_name }"
              />
              <p v-if="formErrors.full_name" class="mt-1 text-xs text-red-500">{{ formErrors.full_name }}</p>
            </div>

            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)] mb-1.5">Email Address</label>
              <input
                v-model="form.email"
                type="email"
                placeholder="jane@organization.com"
                class="clm-input w-full px-3 py-2.5 text-sm rounded-lg"
                :class="{ 'border-red-500': formErrors.email }"
              />
              <p v-if="formErrors.email" class="mt-1 text-xs text-red-500">{{ formErrors.email }}</p>
            </div>

            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)] mb-1.5">Password</label>
              <input
                v-model="form.password"
                type="password"
                placeholder="••••••••"
                class="clm-input w-full px-3 py-2.5 text-sm rounded-lg"
                :class="{ 'border-red-500': formErrors.password }"
              />
              <p v-if="formErrors.password" class="mt-1 text-xs text-red-500">{{ formErrors.password }}</p>
            </div>

            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-[var(--clm-muted)] mb-1.5">Role</label>
              <select v-model="form.role" class="clm-input w-full px-3 py-2.5 text-sm rounded-lg">
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            <div v-if="createError" class="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
              <svg class="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <p class="text-sm text-red-600 dark:text-red-400">{{ createError }}</p>
            </div>

            <div class="flex gap-3 pt-2">
              <button type="button" @click="closeModal" class="flex-1 clm-btn-secondary py-2.5 rounded-lg text-sm font-semibold">
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="flex-1 clm-btn-primary py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-60"
              >
                <svg v-if="saving" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                {{ saving ? 'Creating…' : 'Create User' }}
              </button>
            </div>

          </form>
        </div>
      </div>
    </Teleport>

    <!-- Delete confirm modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
        <div class="clm-card rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden">
          <div class="px-6 py-6">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.999L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16.001c-.77 1.332.193 2.999 1.732 2.999z"/>
                </svg>
              </div>
              <div>
                <h3 class="font-bold text-[var(--clm-text)]">Delete User</h3>
                <p class="text-sm text-[var(--clm-muted)]">This action cannot be undone.</p>
              </div>
            </div>
            <p class="text-sm text-[var(--clm-text)] mb-6">
              Are you sure you want to permanently delete <span class="font-semibold">{{ deleteTarget.full_name }}</span>
              (<span class="font-mono text-xs">{{ deleteTarget.email }}</span>)?
            </p>
            <div class="flex gap-3">
              <button @click="deleteTarget = null" class="flex-1 clm-btn-secondary py-2.5 rounded-lg text-sm font-semibold">
                Cancel
              </button>
              <button
                @click="doDelete"
                :disabled="deleting"
                class="flex-1 bg-red-600 hover:bg-red-700 text-white py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-60 transition"
              >
                <svg v-if="deleting" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                {{ deleting ? 'Deleting…' : 'Delete' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { authStore } from '../utils/auth'

const users = ref([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const createError = ref('')
const deleteTarget = ref(null)
const deleting = ref(false)

const currentUser = computed(() => authStore.user)

const form = reactive({ full_name: '', email: '', password: '', role: 'user' })
const formErrors = reactive({ full_name: '', email: '', password: '' })

function authHeaders() {
  return authStore.headers()
}

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/auth/users', { headers: authHeaders() })
    users.value = data
  } catch {
    users.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)

function initials(name) {
  return name?.split(' ').slice(0, 2).map(w => w[0]?.toUpperCase()).join('') || '?'
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function roleClass(role) {
  return role === 'admin'
    ? 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300'
    : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
}

function openCreate() {
  form.full_name = ''
  form.email = ''
  form.password = ''
  form.role = 'user'
  formErrors.full_name = ''
  formErrors.email = ''
  formErrors.password = ''
  createError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

function validateForm() {
  formErrors.full_name = ''
  formErrors.email = ''
  formErrors.password = ''
  let ok = true
  if (!form.full_name.trim()) { formErrors.full_name = 'Full name is required'; ok = false }
  if (!form.email.trim()) {
    formErrors.email = 'Email is required'; ok = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    formErrors.email = 'Enter a valid email address'; ok = false
  }
  if (!form.password) {
    formErrors.password = 'Password is required'; ok = false
  } else if (form.password.length < 6) {
    formErrors.password = 'Password must be at least 6 characters'; ok = false
  }
  return ok
}

async function submitCreate() {
  createError.value = ''
  if (!validateForm()) return
  saving.value = true
  try {
    const { data } = await axios.post('/api/auth/users', {
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      password: form.password,
      role: form.role,
    }, { headers: authHeaders() })
    users.value.unshift(data)
    closeModal()
  } catch (err) {
    createError.value = err.response?.data?.detail || 'Failed to create user'
  } finally {
    saving.value = false
  }
}

async function toggleActive(user) {
  try {
    const { data } = await axios.put(`/api/auth/users/${user.id}`,
      { is_active: !user.is_active },
      { headers: authHeaders() }
    )
    const idx = users.value.findIndex(u => u.id === user.id)
    if (idx !== -1) users.value[idx] = data
  } catch {
    // ignore
  }
}

function confirmDelete(user) {
  deleteTarget.value = user
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await axios.delete(`/api/auth/users/${deleteTarget.value.id}`, { headers: authHeaders() })
    users.value = users.value.filter(u => u.id !== deleteTarget.value.id)
    deleteTarget.value = null
  } catch {
    // ignore
  } finally {
    deleting.value = false
  }
}
</script>
