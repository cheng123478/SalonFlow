<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">SalonFlow</div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/member">
          <el-icon><User /></el-icon>
          <span>会员管理</span>
        </el-menu-item>
        <el-menu-item index="/technician">
          <el-icon><Service /></el-icon>
          <span>技师管理</span>
        </el-menu-item>
        <el-menu-item index="/reserve">
          <el-icon><Calendar /></el-icon>
          <span>预约管理</span>
        </el-menu-item>
        <el-menu-item index="/order">
          <el-icon><Tickets /></el-icon>
          <span>订单管理</span>
        </el-menu-item>
        <el-menu-item index="/inventory">
          <el-icon><Box /></el-icon>
          <span>库存管理</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>小助理</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ $route.meta.title || 'SalonFlow' }}</div>
        <el-dropdown @command="onCommand">
          <span class="user-info">
            <el-avatar :size="28">{{ (userStore.user?.real_name || 'U')[0] }}</el-avatar>
            <span class="username">{{ userStore.user?.real_name || userStore.user?.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>

    <AgentWidget />
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import AgentWidget from '../components/AgentWidget.vue'

const router = useRouter()
const userStore = useUserStore()

function onCommand(command) {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background-color: #001529;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.aside :deep(.el-menu) {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
  background: #fff;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  outline: none;
}

.username {
  font-size: 14px;
  color: #303133;
}

.main {
  background: #f5f7fa;
}
</style>
