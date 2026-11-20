import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/',
    component: () => import('../layout/index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '工作台' }
      },
      {
        path: 'member',
        name: 'Member',
        component: () => import('../views/member/index.vue'),
        meta: { title: '会员管理' }
      },
      {
        path: 'technician',
        name: 'Technician',
        component: () => import('../views/technician/index.vue'),
        meta: { title: '技师管理' }
      },
      {
        path: 'reserve',
        name: 'Reserve',
        component: () => import('../views/reserve/index.vue'),
        meta: { title: '预约管理' }
      },
      {
        path: 'order',
        name: 'Order',
        component: () => import('../views/order/index.vue'),
        meta: { title: '订单管理' }
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('../views/inventory/index.vue'),
        meta: { title: '库存管理' }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('../views/chat/history.vue'),
        meta: { title: '小助理' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/knowledge/index.vue'),
        meta: { title: '知识库管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录跳转登录页，已登录访问登录/注册页跳转首页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const isAuthPage = to.path === '/login' || to.path === '/register'
  if (!isAuthPage && !token) return '/login'
  if (isAuthPage && token) return '/'
  return true
})

export default router
