import { reactive, computed } from 'vue'

const _state = reactive({
  token: localStorage.getItem('clm_token') || null,
  user: (() => { try { return JSON.parse(localStorage.getItem('clm_user') || 'null') } catch { return null } })(),
})

export const authStore = {
  get token() { return _state.token },
  get user() { return _state.user },
  isAdmin: computed(() => _state.user?.role === 'admin'),
  isLoggedIn: computed(() => !!_state.token),

  login(token, user) {
    _state.token = token
    _state.user = user
    localStorage.setItem('clm_token', token)
    localStorage.setItem('clm_user', JSON.stringify(user))
  },

  logout() {
    _state.token = null
    _state.user = null
    localStorage.removeItem('clm_token')
    localStorage.removeItem('clm_user')
  },

  headers() {
    return _state.token ? { Authorization: `Bearer ${_state.token}` } : {}
  },
}
