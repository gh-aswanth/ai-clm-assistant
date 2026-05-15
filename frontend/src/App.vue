<template>
  <div class="clm-shell relative flex h-screen min-h-0">
    <Teleport to="body">
      <div
        v-if="sidebarFlyout.show && isSidebarCollapsed && !$route.meta.hideSidebar"
        class="clm-sidebar-flyout pointer-events-none fixed z-[100] max-w-[16rem] rounded-lg border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] px-3 py-2 text-left text-sm font-semibold leading-snug text-[var(--clm-text)] shadow-lg dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface)] dark:shadow-[0_12px_40px_-8px_rgba(0,0,0,0.75)]"
        :style="{
          top: `${sidebarFlyout.y}px`,
          left: `${sidebarFlyout.x}px`,
          transform: 'translateY(-50%)',
        }"
      >
        <span class="block whitespace-normal break-words">{{ sidebarFlyout.text }}</span>
      </div>
    </Teleport>

    <!-- Sidebar -->
    <aside
      v-if="!$route.meta.hideSidebar"
      class="clm-sidebar clm-card relative flex h-full min-h-0 shrink-0 flex-col border-r shadow-[4px_0_24px_-12px_rgba(15,76,129,0.12)] transition-[width,box-shadow] duration-200 ease-out dark:shadow-[4px_0_28px_-12px_rgba(0,0,0,0.45)] z-30"
      :class="isSidebarCollapsed ? 'clm-sidebar--collapsed w-[4.25rem]' : 'w-[17.5rem] sm:w-72'"
    >
      <!-- Brand -->
      <div
        class="shrink-0 pb-2 pt-6"
        :class="isSidebarCollapsed ? 'flex justify-center px-2' : 'px-4 sm:px-5 sm:pt-7'"
      >
        <router-link
          to="/"
          class="group flex items-center rounded-2xl outline-none ring-[var(--clm-brand)]/25 transition hover:bg-[var(--clm-brand-soft)]/60 focus-visible:ring-2"
          :class="isSidebarCollapsed ? 'justify-center p-2' : 'gap-3 p-2 -m-2'"
          :aria-label="'Smart Contract — Home'"
          @mouseenter="showSidebarFlyout($event, 'Smart Contract — Contract workspace')"
          @mouseleave="hideSidebarFlyout"
        >
          <div
            class="flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--clm-brand)] to-indigo-700 text-white shadow-md shadow-[var(--clm-brand)]/25 dark:from-sky-500 dark:to-indigo-600"
            :class="isSidebarCollapsed ? 'h-10 w-10' : 'h-11 w-11'"
          >
            <FileStack class="h-5 w-5" aria-hidden="true" stroke-width="2" />
          </div>
          <div v-if="!isSidebarCollapsed" class="min-w-0 text-left">
            <div class="text-[15px] font-extrabold leading-tight tracking-tight text-[var(--clm-text)]">
              Smart Contract
            </div>
            <div class="mt-0.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--clm-text-muted)]">
              Contract workspace
            </div>
          </div>
        </router-link>
      </div>

      <!-- Nav groups -->
      <nav
        class="mt-2 flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto overflow-x-hidden pb-4 pt-2"
        :class="isSidebarCollapsed ? 'px-1.5' : 'px-3 sm:px-4'"
      >
        <div v-for="section in navSections" :key="section.id" class="min-w-0">
          <p
            v-if="!isSidebarCollapsed"
            class="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--clm-text-muted)] opacity-90"
          >
            {{ section.label }}
          </p>
          <ul class="flex flex-col gap-0.5" role="list">
            <li v-for="item in section.items" :key="item.to">
              <router-link
                :to="item.to"
                class="clm-nav-link--modern flex items-center rounded-xl text-sm font-semibold tracking-tight transition-colors duration-150"
                :class="[
                  isNavActive(item) ? 'clm-nav-link--active' : '',
                  isSidebarCollapsed ? 'justify-center px-2 py-2.5' : 'gap-3 px-3 py-2.5',
                ]"
                :aria-label="item.label"
                @mouseenter="showSidebarFlyout($event, item.label)"
                @mouseleave="hideSidebarFlyout"
              >
                <span
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[var(--clm-border)]/80 bg-[var(--clm-bg-surface)]/80 text-[var(--clm-brand)] shadow-sm dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-overlay)]/80 dark:text-sky-400"
                  :class="isNavActive(item) ? 'border-[var(--clm-brand)]/35 bg-[var(--clm-bg-surface)] dark:border-sky-500/30' : ''"
                >
                  <component :is="item.icon" class="h-[18px] w-[18px]" aria-hidden="true" stroke-width="2" />
                </span>
                <span v-if="!isSidebarCollapsed" class="min-w-0 truncate">{{ item.label }}</span>
              </router-link>
            </li>
          </ul>
        </div>
      </nav>

      <!-- Sidebar width toggle (always on the rail) -->
      <div
        class="shrink-0 border-t border-[var(--clm-border)] bg-[var(--clm-bg-surface)]/60 dark:bg-[var(--clm-bg-overlay)]/35"
        :class="isSidebarCollapsed ? 'px-1.5 py-2' : 'px-3 py-2 sm:px-4'"
      >
        <button
          type="button"
          class="clm-sidebar-toggle flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--clm-border)]/60 bg-[var(--clm-bg-overlay)]/30 py-2 text-[var(--clm-text-muted)] transition hover:border-[var(--clm-brand)]/35 hover:bg-[var(--clm-brand-soft)]/55 hover:text-[var(--clm-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--clm-brand)]/35 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface)]/40 dark:hover:bg-[var(--clm-bg-overlay)]/80"
          :class="isSidebarCollapsed ? 'px-2' : 'px-3'"
          :title="isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="!isSidebarCollapsed"
          :aria-label="isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="toggleSidebarCollapsed"
          @mouseenter="showSidebarFlyout($event, isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar')"
          @mouseleave="hideSidebarFlyout"
        >
          <ChevronsLeft v-if="!isSidebarCollapsed" class="h-4 w-4 shrink-0" stroke-width="2" aria-hidden="true" />
          <ChevronsRight v-else class="h-4 w-4 shrink-0" stroke-width="2" aria-hidden="true" />
          <span v-if="!isSidebarCollapsed" class="text-xs font-bold tracking-tight">Collapse</span>
        </button>
      </div>

      <!-- User -->
      <div
        class="shrink-0 border-t border-[var(--clm-border)] bg-[var(--clm-bg-surface)]/80 backdrop-blur-md dark:bg-[var(--clm-bg-overlay)]/50"
        :class="isSidebarCollapsed ? 'p-2' : 'p-4 sm:p-5'"
      >
        <div
          v-if="!isSidebarCollapsed"
          class="flex items-center gap-3 rounded-2xl border border-[var(--clm-border)]/70 bg-[var(--clm-bg-overlay)]/40 p-3 dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface)]/40"
        >
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--clm-brand)] text-xs font-bold text-white shadow-inner"
          >
            {{ userInitials }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-bold text-[var(--clm-text)]">
              {{ currentUser?.full_name || 'User' }}
            </div>
            <div class="truncate text-xs text-[var(--clm-text-muted)]">
              {{ currentUser?.email }}
            </div>
          </div>
          <button type="button" class="clm-icon-btn h-10 w-10 shrink-0 rounded-xl" title="Sign out" @click="logout">
            <LogOut class="h-4 w-4" aria-hidden="true" stroke-width="2" />
          </button>
        </div>
        <div v-else class="flex flex-col items-center gap-2">
          <div
            class="flex h-10 w-10 cursor-default items-center justify-center rounded-xl bg-[var(--clm-brand)] text-xs font-bold text-white shadow-inner"
            :aria-label="userFlyoutText"
            @mouseenter="showSidebarFlyout($event, userFlyoutText)"
            @mouseleave="hideSidebarFlyout"
          >
            {{ userInitials }}
          </div>
          <button
            type="button"
            class="clm-icon-btn flex h-9 w-9 items-center justify-center rounded-xl"
            aria-label="Sign out"
            @click="logout"
            @mouseenter="showSidebarFlyout($event, 'Sign out')"
            @mouseleave="hideSidebarFlyout"
          >
            <LogOut class="h-4 w-4" aria-hidden="true" stroke-width="2" />
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main
      class="min-h-0 flex flex-1 flex-col"
      :class="route.meta.appFillHeight ? 'overflow-hidden' : 'overflow-y-auto'"
    >
      <header v-if="!$route.meta.hideSidebar" class="clm-topbar px-6 py-3 flex justify-between items-center sticky top-0 z-20 shrink-0">
        <div class="text-xl font-semibold tracking-tight text-[var(--clm-text)]">
          {{ $route.name }}
        </div>
        <div class="flex items-center space-x-3">
          <!-- Dark / Light mode toggle -->
          <button
            @click="toggleDark"
            class="clm-icon-btn transition"
            :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            <!-- Sun: shown in dark mode, click to go light -->
            <svg v-if="isDark" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z"/>
            </svg>
            <!-- Moon: shown in light mode, click to go dark -->
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"/>
            </svg>
          </button>
          <router-link to="/create-contract" class="clm-btn-primary px-4 py-2 rounded-lg text-sm font-bold">
            New Contract
          </router-link>
        </div>
      </header>
      <div
        :class="[
          !route.meta.hideSidebar ? 'px-4 sm:px-6 lg:px-8' : '',
          !route.meta.hideSidebar && !route.meta.appFillHeight ? 'py-5 sm:py-6 lg:py-8' : '',
          !route.meta.hideSidebar && route.meta.appFillHeight ? 'flex min-h-0 flex-1 flex-col overflow-hidden pb-3 pt-3 sm:pb-4 sm:pt-4' : '',
        ]"
        class="clm-page-shell min-w-0"
      >
        <div :class="route.meta.appFillHeight ? 'flex min-h-0 flex-1 flex-col overflow-hidden' : ''">
          <router-view />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BookMarked,
  FilePlus2,
  FileStack,
  FolderKanban,
  HardDrive,
  LayoutDashboard,
  LogOut,
  ChevronsLeft,
  ChevronsRight,
  UserCheck,
  Users,
} from 'lucide-vue-next'
import { authStore } from './utils/auth'

const router = useRouter()
const route = useRoute()
const isDark = ref(false)

const currentUser = computed(() => authStore.user)

const navSections = computed(() => {
  const workspaceItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
    { to: '/contracts', label: 'Contracts', icon: FolderKanban },
    { to: '/create-contract', label: 'Create contract', icon: FilePlus2 },
    { to: '/guidelines', label: 'Guidelines', icon: BookMarked },
    { to: '/document-drive', label: 'Document drive', icon: HardDrive },
    { to: '/master-signers', label: 'Signers registry', icon: UserCheck },
  ]
  const adminItems =
    currentUser.value?.role === 'admin'
      ? [{ to: '/users', label: 'User management', icon: Users, exact: false }]
      : []
  const out = [{ id: 'workspace', label: 'Workspace', items: workspaceItems }]
  if (adminItems.length) {
    out.push({ id: 'admin', label: 'Administration', items: adminItems })
  }
  return out
})

function isNavActive(item) {
  const p = route.path
  if (item.exact) return p === '/' || p === ''
  if (p === item.to) return true
  return p.startsWith(`${item.to}/`)
}

const userInitials = computed(() => {
  const name = currentUser.value?.full_name || ''
  return name.split(' ').slice(0, 2).map(w => w[0]?.toUpperCase()).join('') || '?'
})

const userFlyoutText = computed(() => {
  const u = currentUser.value
  if (!u) return 'Signed in'
  const name = u.full_name || 'User'
  const em = (u.email || '').trim()
  return em ? `${name} — ${em}` : name
})

function logout() {
  authStore.logout()
  router.push('/login')
}
const SIDEBAR_COLLAPSED_KEY = 'clm-sidebar-collapsed'
const isSidebarCollapsed = ref(false)

const sidebarFlyout = ref({ show: false, text: '', x: 0, y: 0 })
let sidebarFlyoutTimer = null

function dismissSidebarFlyout() {
  if (sidebarFlyoutTimer) {
    clearTimeout(sidebarFlyoutTimer)
    sidebarFlyoutTimer = null
  }
  sidebarFlyout.value = { show: false, text: '', x: 0, y: 0 }
}

function showSidebarFlyout(e, text) {
  if (!isSidebarCollapsed.value || !text) return
  if (sidebarFlyoutTimer) {
    clearTimeout(sidebarFlyoutTimer)
    sidebarFlyoutTimer = null
  }
  const el = e.currentTarget
  if (!el || typeof el.getBoundingClientRect !== 'function') return
  const r = el.getBoundingClientRect()
  sidebarFlyout.value = {
    show: true,
    text,
    x: r.right + 10,
    y: r.top + r.height / 2,
  }
}

function hideSidebarFlyout() {
  sidebarFlyoutTimer = window.setTimeout(dismissSidebarFlyout, 80)
}

function toggleSidebarCollapsed() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  dismissSidebarFlyout()
  localStorage.setItem(SIDEBAR_COLLAPSED_KEY, isSidebarCollapsed.value ? '1' : '0')
}

watch(isSidebarCollapsed, (collapsed) => {
  if (!collapsed) dismissSidebarFlyout()
})

const applyTheme = (dark) => {
  if (dark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
  isDark.value = dark
  localStorage.setItem('clm-theme', dark ? 'dark' : 'light')
}

const toggleDark = () => applyTheme(!isDark.value)

onMounted(() => {
  // Restore saved preference, or respect OS preference
  const saved = localStorage.getItem('clm-theme')
  if (saved) {
    applyTheme(saved === 'dark')
  } else {
    applyTheme(window.matchMedia('(prefers-color-scheme: dark)').matches)
  }

  if (localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1') {
    isSidebarCollapsed.value = true
  }
})

onUnmounted(() => {
  if (sidebarFlyoutTimer) clearTimeout(sidebarFlyoutTimer)
})
</script>
