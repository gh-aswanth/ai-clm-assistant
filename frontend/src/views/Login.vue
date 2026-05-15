<template>
  <div class="login-root relative min-h-screen overflow-x-hidden bg-[var(--clm-bg-page)] text-[var(--clm-text)]">
    <!-- Ambient layers (stay subtle — motion draws the eye) -->
    <div class="login-ambient pointer-events-none absolute inset-0" aria-hidden="true">
      <div class="login-ambient__blob login-ambient__blob--a" />
      <div class="login-ambient__blob login-ambient__blob--b" />
      <div class="login-ambient__blob login-ambient__blob--c" />
      <div class="login-ambient__grid" />
    </div>

    <!-- Flex shell: journey (product story) + auth (task) -->
    <div
      class="login-shell relative z-10 mx-auto flex min-h-screen w-full max-w-[88rem] flex-col gap-12 px-5 py-12 sm:px-8 sm:py-14 lg:flex-row lg:items-center lg:justify-between lg:gap-20 lg:px-12 lg:py-16 xl:gap-24"
    >
      <!-- LEFT: CLM journey — flex column timeline -->
      <section class="login-journey flex min-w-0 flex-1 flex-col justify-center lg:max-w-[min(100%,40rem)] xl:max-w-[min(100%,44rem)]">
        <div
          v-motion
          class="mb-10 lg:mb-12"
          :initial="motion.initialFadeUp"
          :enter="motion.enterFadeUp(0)"
        >
          <div
            class="mb-5 inline-flex items-center gap-2.5 rounded-full border border-[var(--clm-brand)]/30 bg-[var(--clm-bg-surface)]/80 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-[var(--clm-brand)] shadow-sm backdrop-blur-md dark:bg-[var(--clm-bg-surface)]/60 sm:text-sm sm:tracking-[0.2em]"
          >
            <Sparkles class="h-4 w-4 shrink-0 text-amber-500 dark:text-amber-400 sm:h-5 sm:w-5" aria-hidden="true" />
            CLM platform
          </div>
          <h1 class="text-balance text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl xl:text-[3.5rem] xl:leading-[1.06]">
            <span class="bg-gradient-to-r from-[var(--clm-brand)] via-indigo-600 to-cyan-500 bg-clip-text text-transparent dark:from-sky-400 dark:via-indigo-400 dark:to-cyan-300">
              Every contract stage,
            </span>
            <span class="text-[var(--clm-text)]"> one fluid workspace.</span>
          </h1>
          <p class="mt-5 max-w-xl text-base leading-relaxed text-[var(--clm-text-muted)] sm:text-lg lg:text-xl lg:leading-relaxed">
            Follow the lifecycle as you sign in—draft through insights—built on the same rails your deals run on after login.
          </p>
        </div>

        <div class="login-timeline relative">
          <!-- Traveling “contract packet” on the rail -->
          <div
            class="login-timeline__packet"
            :class="{ 'login-timeline__packet--paused': motion.pauseAmbient }"
            aria-hidden="true"
          />

          <div class="flex flex-col gap-2 sm:gap-2.5">
            <div
              v-for="(stage, i) in stages"
              :key="stage.id"
              v-motion
              class="login-stage group flex gap-4 sm:gap-5"
              :initial="motion.initialSlide"
              :enter="motion.enterSlide(80 + i * 75)"
              :hovered="motion.hoverLift"
            >
              <div class="login-stage__rail flex w-11 shrink-0 flex-col items-center pt-1 sm:w-12">
                <div
                  class="login-stage__dot flex h-11 w-11 items-center justify-center rounded-2xl border-2 transition-all duration-300 sm:h-12 sm:w-12"
                  :class="
                    activeStage === i
                      ? 'border-[var(--clm-brand)] bg-[var(--clm-brand)]/15 shadow-[0_0_28px_-4px_var(--clm-brand)] dark:bg-[var(--clm-brand)]/25'
                      : 'border-[var(--clm-border)] bg-[var(--clm-bg-surface)]/70 dark:bg-[var(--clm-bg-overlay)]/80'
                  "
                >
                  <component :is="stage.icon" class="h-5 w-5 text-[var(--clm-brand)] sm:h-6 sm:w-6 dark:text-sky-400" aria-hidden="true" />
                </div>
                <div
                  v-if="i < stages.length - 1"
                  class="login-stage__spine mt-1.5 w-px flex-1 min-h-[14px] bg-gradient-to-b from-[var(--clm-border)] to-transparent group-last:from-transparent dark:from-slate-600"
                />
              </div>

              <div
                class="login-stage__body mb-4 flex min-w-0 flex-1 flex-col rounded-2xl border px-5 py-4 transition-colors duration-300 sm:rounded-3xl sm:px-6 sm:py-5"
                :class="
                  activeStage === i
                    ? 'border-[var(--clm-brand)]/45 bg-[var(--clm-brand)]/[0.07] dark:border-[var(--clm-brand)]/35 dark:bg-[var(--clm-brand)]/10'
                    : 'border-[var(--clm-border)]/80 bg-[var(--clm-bg-surface)]/65 backdrop-blur-md dark:border-[var(--clm-border)] dark:bg-[var(--clm-bg-surface)]/50'
                "
              >
                <div class="flex flex-wrap items-center gap-2.5">
                  <span class="text-sm font-bold text-[var(--clm-text)] sm:text-base">{{ stage.title }}</span>
                  <span
                    v-if="activeStage === i"
                    class="rounded-lg bg-[var(--clm-brand)] px-2 py-1 text-[10px] font-black uppercase tracking-wider text-white sm:text-xs"
                  >Active</span>
                </div>
                <p class="mt-2 text-xs leading-relaxed text-[var(--clm-text-muted)] sm:text-sm sm:leading-relaxed">
                  {{ stage.blurb }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Trust / flex stats row -->
        <div
          v-motion
          class="mt-10 flex flex-wrap items-stretch gap-3 sm:mt-12 sm:gap-4"
          :initial="motion.initialFade"
          :enter="motion.enterFade(520)"
        >
          <div
            v-for="stat in trustStats"
            :key="stat.label"
            class="flex min-w-[7.5rem] flex-1 flex-col rounded-2xl border border-[var(--clm-border)]/70 bg-[var(--clm-bg-surface)]/50 px-4 py-3 text-center backdrop-blur-sm dark:bg-[var(--clm-bg-overlay)]/50 sm:min-w-[8.5rem] sm:px-5 sm:py-4"
          >
            <span class="text-2xl font-black tabular-nums text-[var(--clm-brand)] dark:text-sky-400 sm:text-3xl">{{ stat.value }}</span>
            <span class="mt-1 text-[10px] font-bold uppercase tracking-wide text-[var(--clm-text-muted)] sm:text-xs">{{ stat.label }}</span>
          </div>
        </div>
      </section>

      <!-- RIGHT: Auth card -->
      <main
        class="login-auth flex w-full shrink-0 justify-center lg:w-auto lg:max-w-[min(100%,44rem)] lg:justify-end xl:max-w-[min(100%,50rem)] 2xl:max-w-[min(100%,54rem)]"
      >
        <div
          v-motion
          class="login-auth__wrap w-full max-w-2xl [perspective:1400px] sm:max-w-3xl lg:max-w-none"
          :initial="motion.initialCard"
          :enter="motion.enterCard"
        >
          <div
            class="relative flex min-h-[28rem] flex-col overflow-hidden rounded-[1.75rem] border border-white/50 bg-white/90 shadow-[0_28px_100px_-32px_rgba(15,76,129,0.5)] backdrop-blur-2xl dark:border-white/[0.1] dark:bg-[var(--clm-bg-surface)]/92 dark:shadow-[0_36px_120px_-36px_rgba(0,0,0,0.78)] sm:min-h-[32rem] sm:rounded-[2rem] lg:min-h-[36rem] xl:min-h-[38rem]"
          >
            <div class="h-1.5 w-full shrink-0 bg-gradient-to-r from-cyan-500 via-[var(--clm-brand)] to-indigo-600 opacity-90" />

            <div class="shrink-0 px-9 pb-3 pt-10 sm:px-12 sm:pb-4 sm:pt-12 lg:px-14 lg:pt-14">
              <div class="flex items-start gap-4">
                <div
                  class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--clm-brand)] to-indigo-700 text-white shadow-lg shadow-[var(--clm-brand)]/30 sm:h-16 sm:w-16 sm:rounded-3xl"
                >
                  <FileText class="h-7 w-7 sm:h-8 sm:w-8" aria-hidden="true" />
                </div>
                <div>
                  <h2 class="text-2xl font-extrabold tracking-tight text-[var(--clm-text)] sm:text-3xl">Welcome back</h2>
                  <p class="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-[var(--clm-text-muted)] sm:text-sm">
                    CLM LifeCycle
                  </p>
                </div>
              </div>
              <p class="mt-7 text-base text-[var(--clm-text-muted)] sm:mt-8 sm:text-lg lg:text-xl">
                Sign in to open your contract workspace.
              </p>
            </div>

            <div class="flex flex-1 flex-col justify-center px-9 pb-10 pt-4 sm:px-12 sm:pb-12 sm:pt-6 lg:px-14 lg:pb-14">
              <form @submit.prevent="handleLogin" class="flex flex-col gap-6 sm:gap-7" novalidate>
                <div
                  v-motion
                  :initial="motion.initialField"
                  :enter="motion.enterField(0)"
                >
                  <label class="mb-2 block text-xs font-bold uppercase tracking-wider text-[var(--clm-text-muted)] sm:text-sm">Email</label>
                  <div class="relative">
                    <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-[var(--clm-text-muted)]">
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                      </svg>
                    </span>
                    <input
                      v-model="form.email"
                      type="email"
                      autocomplete="username"
                      placeholder="you@organization.com"
                      class="w-full rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] py-3.5 pl-12 pr-4 text-base outline-none transition focus:border-[var(--clm-brand)] focus:ring-2 focus:ring-[var(--clm-brand)]/25 dark:bg-[var(--clm-bg-overlay)] sm:rounded-2xl sm:py-4 sm:pl-14 sm:text-lg"
                      :class="{ 'border-red-500 focus:ring-red-500/20': errors.email }"
                    />
                  </div>
                  <p v-if="errors.email" class="mt-1.5 text-sm font-medium text-red-600 dark:text-red-400">{{ errors.email }}</p>
                </div>

                <div
                  v-motion
                  :initial="motion.initialField"
                  :enter="motion.enterField(70)"
                >
                  <label class="mb-2 block text-xs font-bold uppercase tracking-wider text-[var(--clm-text-muted)] sm:text-sm">Password</label>
                  <div class="relative">
                    <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-[var(--clm-text-muted)]">
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    </span>
                    <input
                      v-model="form.password"
                      :type="showPassword ? 'text' : 'password'"
                      autocomplete="current-password"
                      placeholder="••••••••"
                      class="w-full rounded-xl border border-[var(--clm-border)] bg-[var(--clm-bg-surface)] py-3.5 pl-12 pr-12 text-base outline-none transition focus:border-[var(--clm-brand)] focus:ring-2 focus:ring-[var(--clm-brand)]/25 dark:bg-[var(--clm-bg-overlay)] sm:rounded-2xl sm:py-4 sm:pl-14 sm:pr-14 sm:text-lg"
                      :class="{ 'border-red-500 focus:ring-red-500/20': errors.password }"
                    />
                    <button
                      type="button"
                      class="absolute inset-y-0 right-0 flex items-center pr-4 text-[var(--clm-text-muted)] transition hover:text-[var(--clm-brand)]"
                      tabindex="-1"
                      @click="showPassword = !showPassword"
                    >
                      <svg v-if="!showPassword" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    </button>
                  </div>
                  <p v-if="errors.password" class="mt-1.5 text-sm font-medium text-red-600 dark:text-red-400">{{ errors.password }}</p>
                </div>

                <Transition name="login-alert">
                  <div
                    v-if="serverError"
                    class="flex items-start gap-3 rounded-xl border border-red-200/90 bg-red-50 px-4 py-3 dark:border-red-800/80 dark:bg-red-950/40 sm:rounded-2xl sm:px-5 sm:py-4"
                  >
                    <svg class="mt-0.5 h-5 w-5 shrink-0 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p class="text-base text-red-700 dark:text-red-300 sm:text-lg">{{ serverError }}</p>
                  </div>
                </Transition>

                <div
                  v-motion
                  :initial="motion.initialField"
                  :enter="motion.enterField(140)"
                >
                  <button
                    type="submit"
                    :disabled="loading"
                    class="group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-xl py-4 text-base font-bold text-white shadow-lg shadow-[var(--clm-brand)]/30 transition enabled:hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 sm:rounded-2xl sm:py-5 sm:text-lg"
                  >
                    <span class="absolute inset-0 bg-gradient-to-r from-[var(--clm-brand)] via-indigo-600 to-cyan-600 transition group-hover:brightness-110 group-hover:duration-300" />
                    <span class="relative flex items-center gap-2.5">
                      <svg v-if="loading" class="h-5 w-5 animate-spin sm:h-6 sm:w-6" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                      </svg>
                      {{ loading ? 'Signing in…' : 'Enter workspace' }}
                    </span>
                  </button>
                </div>
              </form>
            </div>

            <div
              class="shrink-0 border-t border-[var(--clm-border)]/60 bg-[var(--clm-bg-overlay)]/30 px-9 py-5 dark:bg-black/20 sm:px-12 sm:py-6 lg:px-14"
            >
              <p class="text-center text-xs text-[var(--clm-text-muted)] sm:text-sm">Encrypted session · Enterprise CLM</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { FileText, GitBranch, PenLine, ShieldCheck, Sparkles, Users } from 'lucide-vue-next'
import { authStore } from '../utils/auth'

const router = useRouter()

const form = reactive({ email: '', password: '' })
const errors = reactive({ email: '', password: '' })
const serverError = ref('')
const loading = ref(false)
const showPassword = ref(false)

const activeStage = ref(0)
let stageTimer = null

const reduceMotion = ref(false)

const stages = [
  {
    id: 'draft',
    title: 'Draft & align',
    blurb: 'Author in one place—templates, clauses, and drive-linked files stay version-aware.',
    icon: FileText,
  },
  {
    id: 'review',
    title: 'Review & redline',
    blurb: 'Structured feedback loops so legal and business stay in sync before commitment.',
    icon: GitBranch,
  },
  {
    id: 'compliance',
    title: 'Guideline & compliance',
    blurb: 'Framework-linked checks surface risk while the deal is still easy to change.',
    icon: ShieldCheck,
  },
  {
    id: 'sign',
    title: 'Sign & bind',
    blurb: 'Ordered e-signatures with a clear audit trail tied to the exact document version.',
    icon: PenLine,
  },
  {
    id: 'parties',
    title: 'Parties & obligations',
    blurb: 'Signers, milestones, and post-signature tasks connected to contract language.',
    icon: Users,
  },
]

const trustStats = [
  { value: '5', label: 'Lifecycle beats' },
  { value: '∞', label: 'Versions' },
  { value: '1', label: 'Source of truth' },
]

/** Spring presets for @vueuse/motion (Popmotion) — tuned for “premium SaaS” feel */
const spring = { type: 'spring', stiffness: 320, damping: 28, mass: 0.9 }
const springSoft = { type: 'spring', stiffness: 260, damping: 30, mass: 1 }
const springPop = { type: 'spring', stiffness: 400, damping: 22, mass: 0.75 }

const motion = computed(() => {
  const off = reduceMotion.value
  if (off) {
    return {
      pauseAmbient: true,
      initialFadeUp: {},
      enterFadeUp: () => ({ opacity: 1, transition: { duration: 0 } }),
      initialSlide: {},
      enterSlide: () => ({ opacity: 1, transition: { duration: 0 } }),
      hoverLift: {},
      initialFade: {},
      enterFade: () => ({ opacity: 1, transition: { duration: 0 } }),
      initialCard: {},
      enterCard: { opacity: 1, transition: { duration: 0 } },
      initialField: {},
      enterField: () => ({ opacity: 1, transition: { duration: 0 } }),
    }
  }
  return {
    pauseAmbient: false,
    initialFadeUp: { opacity: 0, y: 28, filter: 'blur(10px)' },
    enterFadeUp: (delay = 0) => ({
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: { ...spring, delay },
    }),
    initialSlide: { opacity: 0, x: -36, filter: 'blur(6px)' },
    enterSlide: (delay = 0) => ({
      opacity: 1,
      x: 0,
      filter: 'blur(0px)',
      transition: { ...springSoft, delay },
    }),
    hoverLift: {
      x: 6,
      transition: springPop,
    },
    initialFade: { opacity: 0, y: 12 },
    enterFade: (delay = 0) => ({
      opacity: 1,
      y: 0,
      transition: { ...springSoft, delay },
    }),
    initialCard: { opacity: 0, y: 40, scale: 0.94, rotateX: 6, filter: 'blur(12px)' },
    enterCard: {
      opacity: 1,
      y: 0,
      scale: 1,
      rotateX: 0,
      filter: 'blur(0px)',
      transition: { ...spring, delay: 120 },
    },
    initialField: { opacity: 0, y: 16 },
    enterField: (delay = 0) => ({
      opacity: 1,
      y: 0,
      transition: { ...springSoft, delay: 180 + delay },
    }),
  }
})

onMounted(() => {
  reduceMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  stageTimer = window.setInterval(() => {
    activeStage.value = (activeStage.value + 1) % stages.length
  }, 2800)
})

onUnmounted(() => {
  if (stageTimer) clearInterval(stageTimer)
})

function validate() {
  errors.email = ''
  errors.password = ''
  let ok = true
  if (!form.email.trim()) {
    errors.email = 'Email is required'
    ok = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errors.email = 'Enter a valid email address'
    ok = false
  }
  if (!form.password) {
    errors.password = 'Password is required'
    ok = false
  }
  return ok
}

async function handleLogin() {
  serverError.value = ''
  if (!validate()) return
  loading.value = true
  try {
    const { data } = await axios.post('/api/auth/login', {
      email: form.email.trim(),
      password: form.password,
    })
    authStore.login(data.access_token, {
      id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      role: data.role,
      premium_access: data.premium_access !== false,
    })
    router.push('/')
  } catch (err) {
    const msg = err.response?.data?.detail
    if (msg === 'Invalid credentials') {
      serverError.value = 'Incorrect email or password. Please try again.'
    } else if (msg === 'Account disabled') {
      serverError.value = 'Your account has been disabled. Contact your administrator.'
    } else {
      serverError.value = msg || 'Login failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-ambient__blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(88px);
  opacity: 0.45;
  animation: login-blob-drift 22s ease-in-out infinite;
}

.login-ambient__blob--a {
  width: min(62vw, 640px);
  height: min(62vw, 640px);
  left: -18%;
  top: -8%;
  background: rgba(15, 76, 129, 0.35);
}

.login-ambient__blob--b {
  width: min(58vw, 560px);
  height: min(58vw, 560px);
  right: -14%;
  top: 28%;
  background: rgba(99, 102, 241, 0.28);
  animation-delay: -6s;
  animation-duration: 26s;
}

.login-ambient__blob--c {
  width: min(50vw, 480px);
  height: min(50vw, 480px);
  left: 18%;
  bottom: -10%;
  background: rgba(14, 165, 233, 0.22);
  animation-delay: -11s;
  animation-duration: 20s;
}

.login-ambient__grid {
  position: absolute;
  inset: 0;
  opacity: 0.4;
  background-image:
    linear-gradient(rgba(15, 76, 129, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 76, 129, 0.07) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 45%, black 25%, transparent 75%);
}

.dark .login-ambient__blob--a {
  background: rgba(79, 156, 249, 0.2);
}
.dark .login-ambient__blob--b {
  background: rgba(129, 140, 248, 0.18);
}
.dark .login-ambient__blob--c {
  background: rgba(34, 211, 238, 0.14);
}

.dark .login-ambient__grid {
  opacity: 0.22;
  background-image:
    linear-gradient(rgba(148, 193, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 193, 255, 0.08) 1px, transparent 1px);
}

/* Packet travels along the flex timeline (rail x ≈ 18px center) */
.login-timeline {
  position: relative;
  padding-left: 0;
}

.login-timeline__packet {
  position: absolute;
  left: calc(1.375rem - 9px);
  top: 0;
  width: 18px;
  height: 18px;
  margin-left: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--clm-brand), #6366f1, #06b6d4);
  box-shadow:
    0 0 0 4px rgba(255, 255, 255, 0.35),
    0 0 32px -2px var(--clm-brand);
  z-index: 2;
  animation: login-packet-path 14s cubic-bezier(0.45, 0, 0.55, 1) infinite;
  pointer-events: none;
}

@media (min-width: 640px) {
  .login-timeline__packet {
    left: calc(1.5rem - 9px);
  }
}

.dark .login-timeline__packet {
  box-shadow:
    0 0 0 3px rgba(15, 23, 42, 0.5),
    0 0 28px 0 rgba(79, 156, 249, 0.55);
}

.login-timeline__packet--paused {
  animation: none;
  opacity: 0.85;
  top: 48%;
}

@keyframes login-blob-drift {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(4%, -3%) scale(1.06);
  }
}

/* Key stops aligned to 5 stages (taller cards + padding after “big” layout) */
@keyframes login-packet-path {
  0% {
    transform: translateY(18px);
    opacity: 1;
  }
  18% {
    transform: translateY(108px);
  }
  36% {
    transform: translateY(218px);
  }
  54% {
    transform: translateY(332px);
  }
  72% {
    transform: translateY(444px);
  }
  90% {
    transform: translateY(548px);
  }
  100% {
    transform: translateY(18px);
  }
}

.login-alert-enter-active,
.login-alert-leave-active {
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.login-alert-enter-from,
.login-alert-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.99);
}

@media (max-width: 1023px) {
  @keyframes login-packet-path {
    0%,
    100% {
      transform: translateY(14px);
    }
    50% {
      transform: translateY(260px);
    }
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-ambient__blob {
    animation: none !important;
  }
  .login-timeline__packet {
    animation: none !important;
  }
}
</style>
