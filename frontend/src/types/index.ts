// API响应类型
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// 账号相关类型
export interface Account {
  config: any
  id: string
  name: string
  platform: string
  status: any
  enable_text: boolean
  enable_emoji: boolean
  enable_voice: boolean
  enable_image: boolean
  enable_proactive: boolean
  enable_learning: boolean
  max_daily_messages: number
  max_daily_cost: number
  today_message_count: number
  today_cost: number
  total_message_count: number
  total_cost: number
  created_at: string
  updated_at: string
}

export interface AccountListResponse {
  total: number
  accounts: Account[]
}

export interface AccountStats {
  account_id: string
  name: string
  platform: string
  status: string
  today: {
    message_count: number
    cost: number
  }
  total: {
    message_count: number
    cost: number
  }
  limits: {
    max_daily_messages: number
    max_daily_cost: number
  }
  timestamps: {
    created_at: string
    updated_at: string
    last_message_at: string | null
  }
  error: {
    code: string
    message: string
    timestamp: string
  } | null
}

export interface LimitStatus {
  account_id: string
  status: string
  daily_limits: {
    messages: {
      used: number
      limit: number
      remaining: number
    }
    cost: {
      used: number
      limit: number
      remaining: number
    }
  }
  rate_limit: {
    max_requests: number
    window_seconds: number
  }
  can_send: boolean
}

export interface CreateAccountRequest {
  name: string
  platform: string
  platform_config: Record<string, any>
  personality_config?: Record<string, any>
  max_daily_messages?: number
  max_daily_cost?: number
  enable_text?: boolean
  enable_emoji?: boolean
  enable_voice?: boolean
  enable_image?: boolean
  enable_proactive?: boolean
  enable_learning?: boolean
}

export interface UpdateAccountRequest {
  name?: string
  platform_config?: Record<string, any>
  personality_config?: Record<string, any>
  max_daily_messages?: number
  max_daily_cost?: number
  enable_text?: boolean
  enable_emoji?: boolean
  enable_voice?: boolean
  enable_image?: boolean
  enable_proactive?: boolean
  enable_learning?: boolean
}

// 消息相关类型
export interface Message {
  id?: string
  role: 'user' | 'assistant' | string
  content: string
  content_type?: string
  emotion_valence?: number
  emotion_arousal?: number
  model_used?: string
  tokens_used?: number
  created_at?: string
}

export interface Conversation {
  id: string
  user_id: string
  account_id: string
  user_nickname?: string
  title?: string
  last_message_preview?: string
  status: string
  message_count: number
  last_message_at?: string
  messages?: Message[]
  created_at: string
  updated_at: string
}

export interface ConversationDetail extends Conversation {
  started_at: string
  ended_at?: string
  messages: Message[]
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
}

export interface ChatRequest {
  user_id: string
  account_id: string
  message: string
  conversation_id?: string
}

export interface ChatResponse {
  content: string
  model_used: string
  tokens_used: number
  conversation_id?: string
}

export interface ChatHistoryResponse {
  conversation_id: string
  messages: Message[]
}

// 记忆相关类型
export interface Memory {
  id?: string | number
  account_id?: string
  content?: string
  importance?: number
  category?: string
  created_at?: string
  updated_at?: string
}

// 仪表盘统计
export interface DashboardStats {
  total_accounts: number
  active_accounts: number
  total_messages: number
  today_messages: number
  total_cost: number
  today_cost: number
}

// 贴纸相关
export interface Sticker {
  id: string
  name: string
  url: string
  category: string
  tags: string[]
}
