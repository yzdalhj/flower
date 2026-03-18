<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <div class="error-icon">🌸</div>
      <h1 class="error-title">页面不见了</h1>
      <p class="error-desc">
        抱歉，您访问的页面不存在或已被移除
      </p>
      <div class="error-actions">
        <t-button theme="primary" size="large" @click="goHome">
          <template #icon><t-icon name="home" /></template>
          返回首页
        </t-button>
        <t-button variant="outline" size="large" @click="goChat">
          <template #icon><t-icon name="chat" /></template>
          去聊天
        </t-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goChat = () => {
  router.push('/chat')
}
</script>

<style scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.not-found-content {
  text-align: center;
  color: white;
}

.error-code {
  font-size: 8rem;
  font-weight: 800;
  opacity: 0.3;
  line-height: 1;
}

.error-icon {
  font-size: 4rem;
  margin: -2rem 0 1rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.error-title {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.error-desc {
  font-size: 1.125rem;
  opacity: 0.8;
  margin-bottom: 2rem;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
</style>
