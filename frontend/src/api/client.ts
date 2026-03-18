import axios, { type AxiosInstance, type AxiosResponse, type AxiosError } from 'axios'
import { MessagePlugin } from 'tdesign-vue-next'

// 创建axios实例
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
console.log('API Base URL:', baseURL)

const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 60000, // 60秒超时，因为AI响应可能较慢
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 打印请求信息用于调试
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)

    // 从localStorage获取token（如果需要认证）
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error: AxiosError) => {
    const { response } = error

    if (response) {
      const errorData = response.data as any
      const errorMessage = errorData?.detail || errorData?.message || '请求失败'

      switch (response.status) {
        case 400:
          MessagePlugin.error(`请求错误: ${errorMessage}`)
          break
        case 401:
          // 未授权，清除token并跳转登录
          localStorage.removeItem('access_token')
          window.location.href = '/login'
          MessagePlugin.error('登录已过期，请重新登录')
          break
        case 403:
          MessagePlugin.error('没有权限执行此操作')
          break
        case 404:
          MessagePlugin.error('请求的资源不存在')
          break
        case 429:
          MessagePlugin.error('请求过于频繁，请稍后再试')
          break
        case 500:
          MessagePlugin.error(`服务器错误: ${errorMessage}`)
          break
        default:
          MessagePlugin.error(errorMessage)
      }
    } else {
      MessagePlugin.error('网络连接失败，请检查网络')
    }

    return Promise.reject(error)
  }
)

export default apiClient
