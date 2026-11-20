import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi } from '../api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token
  },

  actions: {
    async login(payload) {
      const res = await loginApi(payload)
      this.setSession(res.data)
    },

    async register(payload) {
      const res = await registerApi(payload)
      this.setSession(res.data)
    },

    setSession(data) {
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },

    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
