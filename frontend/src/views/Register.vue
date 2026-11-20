<template>
  <div class="register-page">
    <el-card class="register-card">
      <div class="register-title">注册账号</div>
      <div class="register-subtitle">SalonFlow 美发门店智能体</div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="real_name">
          <el-input v-model="form.real_name" placeholder="姓名（选填）" :prefix-icon="Avatar" />
        </el-form-item>
        <el-form-item prop="phone">
          <el-input v-model="form.phone" placeholder="手机号（选填）" :prefix-icon="Phone" />
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
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            show-password
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="register-btn" :loading="loading" @click="onSubmit">
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-tip">
        已有账号？
        <el-link type="primary" @click="router.push('/login')">去登录</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Avatar, Phone, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', real_name: '', phone: '', password: '', confirmPassword: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

async function onSubmit() {
  if (loading.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.register({
      username: form.username,
      password: form.password,
      real_name: form.real_name,
      phone: form.phone
    })
    ElMessage.success('注册成功')
    router.push('/')
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 400px;
  padding: 12px 8px;
}

.register-title {
  font-size: 22px;
  font-weight: 600;
  text-align: center;
  color: #303133;
}

.register-subtitle {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin: 8px 0 24px;
}

.register-btn {
  width: 100%;
}

.register-tip {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
}
</style>
