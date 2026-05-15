import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../utils/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { hideSidebar: true, public: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/contracts', name: 'Contracts', component: () => import('../views/Contracts.vue') },
  { path: '/contracts/:id', name: 'Contract Detail', component: () => import('../views/ContractDetail.vue') },
  { path: '/prepare-signature/:id', name: 'Prepare Signature', component: () => import('../views/PrepareSignature.vue') },
  { path: '/guidelines', name: 'Contract Guidelines', component: () => import('../views/Guidelines.vue') },
  // Token-based signing — no contract ID or signer ID exposed in URL
  { path: '/sign/:token', name: 'Sign Contract', component: () => import('../views/SignContract.vue'), meta: { hideSidebar: true, public: true } },
  // Legacy route kept so old links still work
  { path: '/sign/:id/:signerId', name: 'Sign Contract Legacy', component: () => import('../views/SignContract.vue'), meta: { hideSidebar: true, public: true } },
  { path: '/templates', name: 'Templates', component: () => import('../views/Templates.vue') },
  {
    path: '/create-contract',
    name: 'Create Contract',
    component: () => import('../views/CreateContract.vue'),
    meta: { appFillHeight: true },
  },
  { path: '/master-signers', name: 'Signers Registry', component: () => import('../views/MasterSigners.vue') },
  { path: '/document-drive', name: 'Document Drive', component: () => import('../views/DocumentDriveList.vue') },
  { path: '/document-drive/:driveId', name: 'Drive Record', component: () => import('../views/DocumentDriveRecord.vue') },
  { path: '/users', name: 'User Management', component: () => import('../views/Users.vue'), meta: { adminOnly: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const isPublic = to.meta.public === true

  if (!authStore.token && !isPublic) {
    return next('/login')
  }

  if (authStore.token && to.path === '/login') {
    return next('/')
  }

  if (to.meta.adminOnly && authStore.user?.role !== 'admin') {
    return next('/')
  }

  next()
})

export default router
