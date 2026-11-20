<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand-logo">S</div>
      <h1 class="login-title">SalonFlow</h1>
      <p class="login-subtitle">美发门店智能体 · 多 Agent 经营服务管理后台</p>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            show-password
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="onSubmit">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-tip">
        没有账号？
        <el-link type="primary" @click="router.push('/register')">去注册</el-link>
      </div>
      <div class="login-default">默认账号：admin / admin123</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: 'admin', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function onSubmit() {
  if (loading.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f5ff;
  padding: 24px;
}

.login-card {
  width: 400px;
  max-width: 100%;
  background: #fff;
  border-radius: 18px;
  padding: 44px 40px 36px;
  box-shadow: 0 12px 40px rgba(31, 45, 61, 0.06);
  border: 1px solid #e6ebf5;
}

.brand-logo {
  width: 52px;
  height: 52px;
  margin: 0 auto 16px;
  border-radius: 14px;
  background: #409eff;
  color: #fff;
  font-size: 26px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-title {
  font-size: 22px;
  font-weight: 700;
  text-align: center;
  color: #1f2d3d;
}

.login-subtitle {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin: 8px 0 28px;
}

.login-btn {
  width: 100%;
  border-radius: 8px;
  font-weight: 600;
}

.login-tip {
  text-align: center;
  color: #909399;
  font-size: 13px;
}

.login-default {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 8px;
}
</style>
