import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 统一 axios 实例：注入 token、拦截统一响应结构 {code, message, data}
const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端约定 code === 0 表示成功
    if (res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.message || error.message || '网络错误'

    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 并发多个请求同时 401 时避免重复跳转
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
