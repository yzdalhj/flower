<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="brand">
          <span class="brand-icon">🌸</span>
          <span class="brand-text">AI小花</span>
        </div>
        <p class="brand-subtitle">管理后台登录</p>
      </div>

      <t-form
        ref="formRef"
        :data="formData"
        :rules="rules"
        label-width="0"
        @submit="handleLogin"
        class="login-form"
      >
        <t-form-item name="username">
          <t-input
            v-model="formData.username"
            placeholder="请输入用户名"
            size="large"
            clearable
            @enter="handleLogin"
          >
            <template #prefix>
              <t-icon name="user" class="input-icon" />
            </template>
          </t-input>
        </t-form-item>

        <t-form-item name="password">
          <t-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            clearable
            @enter="handleLogin"
          >
            <template #prefix>
              <t-icon name="lock" class="input-icon" />
            </template>
          </t-input>
        </t-form-item>

        <t-form-item class="submit-item">
          <t-button
            theme="primary"
            size="large"
            block
            type="submit"
            :loading="authStore.loading"
            class="login-btn"
          >
            登 录
          </t-button>
        </t-form-item>
      </t-form>

      <div class="login-tips">
        <div class="tips-content">
          <t-icon name="info-circle" class="tips-icon" />
          <div class="tips-text">
            <div class="tips-title">默认管理员账号</div>
            <div class="tips-info">
              <span>用户名：admin</span>
              <span class="divider">|</span>
              <span>密码：admin123</span>
            </div>
          </div>
        </div>
      </div>

      <div class="login-footer">
        <t-button theme="default" variant="text" class="back-btn" @click="goHome">
          <t-icon name="arrow-left" />
          返回首页
        </t-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const formRef = ref()

const formData = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', type: 'error' as const }],
  password: [{ required: true, message: '请输入密码', type: 'error' as const }],
}

// 检查是否已登录
onMounted(() => {
  if (authStore.isLoggedIn) {
    const redirect = route.query.redirect as string
    router.push(redirect || '/admin')
  }
})

const handleLogin = async () => {
  const valid = await formRef.value?.validate()
  if (valid !== true) return

  const success = await authStore.login(formData.username, formData.password)
  if (success) {
    const redirect = route.query.redirect as string
    router.push(redirect || '/admin')
  }
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 12px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.brand-icon {
  font-size: 36px;
}

.brand-text {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.brand-subtitle {
  font-size: 16px;
  color: #999;
  font-weight: 400;
}

.login-form {
  margin-bottom: 24px;
}

.login-form :deep(.t-form__item) {
  margin-bottom: 20px;
}

.login-form :deep(.t-input__inner) {
  height: 48px;
  font-size: 15px;
  border-radius: 8px;
  padding-left: 44px;
}

.login-form :deep(.t-input__prefix) {
  left: 16px;
}

.input-icon {
  font-size: 18px;
  color: #999;
}

.submit-item {
  margin-top: 24px;
  margin-bottom: 0 !important;
}

.login-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.login-tips {
  background: #f0f5ff;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
}

.tips-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tips-icon {
  font-size: 20px;
  color: #667eea;
  flex-shrink: 0;
  margin-top: 2px;
}

.tips-text {
  flex: 1;
}

.tips-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 6px;
}

.tips-info {
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}

.divider {
  color: #ccc;
}

.login-footer {
  text-align: center;
}

.back-btn {
  color: #666;
  font-size: 14px;
  transition: color 0.3s;
}

.back-btn:hover {
  color: #667eea;
}

.back-btn :deep(.t-icon) {
  margin-right: 4px;
  font-size: 14px;
}

/* 响应式适配 */
@media (max-width: 480px) {
  .login-container {
    padding: 36px 24px;
  }

  .brand-text {
    font-size: 24px;
  }

  .brand-icon {
    font-size: 30px;
  }
}
</style>
