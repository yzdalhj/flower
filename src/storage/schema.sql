-- 数据库初始化脚本
-- AI伴侣机器人数据库模式

-- 对话记录表
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    encrypted_content BYTEA,
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_time ON conversations(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_platform ON conversations(platform);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);

-- 情绪历史表
CREATE TABLE IF NOT EXISTS emotion_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    emotion_type VARCHAR(20) NOT NULL,
    intensity FLOAT NOT NULL CHECK (intensity >= 0 AND intensity <= 10),
    trigger_reason TEXT,
    previous_emotion VARCHAR(20),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_emotion_history_user_time ON emotion_history(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_emotion_history_emotion_type ON emotion_history(emotion_type);

-- 性格配置表
CREATE TABLE IF NOT EXISTS personality_profiles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    personality VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    traits JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_personality_profiles_name ON personality_profiles(name);

-- 网络用语数据库表
CREATE TABLE IF NOT EXISTS slang_database (
    id VARCHAR(36) PRIMARY KEY,
    content VARCHAR(200) NOT NULL,
    meaning TEXT NOT NULL,
    tags JSONB NOT NULL,
    popularity FLOAT NOT NULL CHECK (popularity >= 1 AND popularity <= 10),
    usage_count INT DEFAULT 0,
    last_updated TIMESTAMP NOT NULL,
    is_outdated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_slang_database_popularity ON slang_database(popularity DESC);
CREATE INDEX IF NOT EXISTS idx_slang_database_updated ON slang_database(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_slang_database_outdated ON slang_database(is_outdated);

-- 表情包库表
CREATE TABLE IF NOT EXISTS emoji_library (
    id VARCHAR(36) PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    tags JSONB NOT NULL,
    usage_count INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_emoji_library_usage ON emoji_library(usage_count DESC);

-- 角色转换记录表
CREATE TABLE IF NOT EXISTS role_transitions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    from_profile_id VARCHAR(36),
    to_profile_id VARCHAR(36) NOT NULL,
    trigger_reason TEXT,
    scene_type VARCHAR(20),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_role_transitions_user_time ON role_transitions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_role_transitions_scene_type ON role_transitions(scene_type);

-- 客户端会话表
CREATE TABLE IF NOT EXISTS client_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    connection_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    last_heartbeat TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    reconnect_count INT DEFAULT 0,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_client_sessions_platform ON client_sessions(platform);
CREATE INDEX IF NOT EXISTS idx_client_sessions_status ON client_sessions(status);
CREATE INDEX IF NOT EXISTS idx_client_sessions_heartbeat ON client_sessions(last_heartbeat DESC);

-- 媒体缓存表
CREATE TABLE IF NOT EXISTS media_cache (
    id VARCHAR(36) PRIMARY KEY,
    media_type VARCHAR(20) NOT NULL,
    original_url VARCHAR(1000),
    cache_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    cached_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    access_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_media_cache_expires ON media_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_media_cache_type ON media_cache(media_type);

-- 连接日志表
CREATE TABLE IF NOT EXISTS connection_logs (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    event_details TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_connection_logs_session_time ON connection_logs(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_connection_logs_event_type ON connection_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_connection_logs_timestamp ON connection_logs(timestamp DESC);

-- 添加注释
COMMENT ON TABLE conversations IS '对话记录表，存储所有用户对话消息';
COMMENT ON TABLE emotion_history IS '情绪历史表，记录用户情绪状态变化';
COMMENT ON TABLE personality_profiles IS '性格配置表，存储机器人性格角色配置';
COMMENT ON TABLE slang_database IS '网络用语数据库，存储流行网络用语和梗';
COMMENT ON TABLE emoji_library IS '表情包库，存储表情包文件信息';
COMMENT ON TABLE role_transitions IS '角色转换记录表，记录动态角色转换历史';
COMMENT ON TABLE client_sessions IS '客户端会话表，管理客户端连接会话';
COMMENT ON TABLE media_cache IS '媒体缓存表，缓存富媒体文件';
COMMENT ON TABLE connection_logs IS '连接日志表，记录连接事件';
