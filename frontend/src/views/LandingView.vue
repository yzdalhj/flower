<template>
  <div class="landing-page">
    <canvas ref="canvas" class="tech-bg"></canvas>
    <div class="overlay-gradient"></div>

    <nav class="navbar" :class="{ 'navbar-scrolled': isScrolled }">
      <div class="container nav-container">
        <div class="nav-brand" @click="goHome">
          <div class="brand-logo">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M9 12l2 2 4-4" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="brand-info">
            <span class="brand-text">AI小花</span>
            <span class="brand-tagline">你的智能伙伴</span>
          </div>
        </div>
        <div class="nav-links">
          <a href="#features" class="nav-link" @click.prevent="scrollToSection('features')">功能特色</a>
          <a href="#personality" class="nav-link" @click.prevent="scrollToSection('personality')">人格引擎</a>
          <a href="#about" class="nav-link" @click.prevent="scrollToSection('about')">关于我们</a>
          <div class="nav-divider"></div>
          <t-button class="nav-btn nav-btn-primary" @click="goToChat">
            <template #icon>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.2a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </template>
            <span>开始聊天</span>
          </t-button>
        </div>
        <button class="mobile-menu-toggle" @click="toggleMobileMenu" aria-label="菜单">
          <span :class="{ 'active': mobileMenuOpen }" class="bar"></span>
          <span :class="{ 'active': mobileMenuOpen }" class="bar"></span>
          <span :class="{ 'active': mobileMenuOpen }" class="bar"></span>
        </button>
      </div>
      <div :class="{ 'active': mobileMenuOpen }" class="mobile-menu">
        <a href="#features" class="mobile-nav-link" @click="closeMobileMenu; scrollToSection('features')">功能特色</a>
        <a href="#personality" class="mobile-nav-link" @click="closeMobileMenu; scrollToSection('personality')">人格引擎</a>
        <a href="#about" class="mobile-nav-link" @click="closeMobileMenu; scrollToSection('about')">关于我们</a>
        <div class="mobile-buttons">
          <t-button class="mobile-btn" size="large" @click="closeMobileMenu; goToChat">开始聊天</t-button>
        </div>
      </div>
    </nav>

    <section class="hero">
      <div class="container hero-container">
        <div class="hero-content" ref="heroContent">
          <div class="hero-badge" data-aos="fade-down">
            <span class="badge-dot"></span>
            <span>全新智能体验已上线</span>
          </div>

          <h1 class="hero-title" ref="heroTitle">
            <span class="title-line">遇见你的</span>
            <br>
            <span class="gradient-text" ref="gradientText">AI小花</span>
          </h1>

          <p class="hero-subtitle" data-aos="fade-up" data-aos-delay="200">
            基于<strong>大五人格模型</strong>的智能AI伙伴系统，
            <br>可自定义人格配置，打造真正懂你的温暖AI朋友
          </p>

          <div class="hero-actions" data-aos="fade-up" data-aos-delay="400">
            <button class="btn btn-primary" @click="goToChat">
              <span class="btn-text">立即体验</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M5 12H19M12 5L19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button class="btn btn-secondary" @click="scrollToSection('features')">
              <span class="btn-text">了解更多</span>
            </button>
          </div>

          <div class="hero-stats" data-aos="fade-up" data-aos-delay="600">
            <div class="stat-item" v-for="(stat, index) in stats" :key="index">
              <div class="stat-value" ref="el => statElements[index] = el">
                <span class="stat-number" :data-target="stat.value">0</span>
                <span class="stat-suffix">{{ stat.suffix }}</span>
              </div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>

        <div class="hero-visual" ref="heroVisual">
          <div class="floating-orb main-orb" ref="mainOrb">
            <div class="orb-inner">
              <div class="orb-content">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" stroke="white" stroke-width="2"/>
                  <path d="M8 14s1.5 2 4 2 4-2 4-2" stroke="white" stroke-width="2" stroke-linecap="round"/>
                  <path d="M9 9h.01" stroke="white" stroke-width="3" stroke-linecap="round"/>
                  <path d="M15 9h.01" stroke="white" stroke-width="3" stroke-linecap="round"/>
                </svg>
              </div>
            </div>
            <div class="orb-ring ring-1"></div>
            <div class="orb-ring ring-2"></div>
            <div class="orb-ring ring-3"></div>
          </div>

          <div class="floating-card tech-card card-1" ref="floatingCard1">
            <div class="card-header">
              <div class="card-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="card-title">人格引擎</div>
            </div>
            <div class="card-body">
              <div class="progress-bar">
                <div class="progress-fill"></div>
              </div>
              <div class="progress-text">自定义模型加载中...</div>
            </div>
          </div>

          <div class="floating-card chat-card card-2" ref="floatingCard2">
            <div class="chat-bubble">
              <span class="chat-text">今天过得怎么样呀？😊</span>
            </div>
          </div>

          <div class="floating-card feature-card card-3" ref="floatingCard3">
            <div class="feature-item">
              <span class="feature-dot success"></span>
              <span>情感计算</span>
            </div>
            <div class="feature-item">
              <span class="feature-dot success"></span>
              <span>长期记忆</span>
            </div>
            <div class="feature-item">
              <span class="feature-dot success"></span>
              <span>可定制人格</span>
            </div>
          </div>
        </div>
      </div>

      <div class="wave-divider">
        <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
          <path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.15-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,208.06,18.25,82.11-8.16,158.06-49.36,207.97-90.67V0Z" class="shape-fill"></path>
        </svg>
      </div>
    </section>

    <section id="features" class="features">
      <div class="container">
        <div class="section-header">
          <span class="section-badge">FEATURES</span>
          <h2 class="section-title">
            强大<span class="accent">AI能力</span>，
            <br>贴心温暖陪伴
          </h2>
          <p class="section-subtitle">融合前沿AI技术与人格计算，打造真正智能的情感伙伴</p>
        </div>

        <div class="features-grid">
          <div
            v-for="(feature, index) in features"
            :key="index"
            class="feature-card"
            :class="'feature-card-' + (index + 1)"
            @mouseenter="hoverFeature = index"
            @mouseleave="hoverFeature = null"
          >
            <div class="feature-border"></div>
            <div class="feature-content">
              <div class="feature-icon" :style="{ background: feature.gradient }">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path :d="getIconPath(feature.icon)" />
                </svg>
              </div>
              <h3 class="feature-title">{{ feature.title }}</h3>
              <p class="feature-desc">{{ feature.description }}</p>
              <div class="feature-tags">
                <span v-for="tag in feature.tags" :key="tag" class="feature-tag">{{ tag }}</span>
              </div>
            </div>
            <div class="feature-glow" :style="{ background: feature.gradient }"></div>
          </div>
        </div>
      </div>
    </section>

    <section class="how-it-works">
      <div class="container">
        <div class="section-header">
          <span class="section-badge">HOW IT WORKS</span>
          <h2 class="section-title">
            三步开启<span class="accent">智能陪伴</span>
          </h2>
          <p class="section-subtitle">简单几步，快速开始你的AI陪伴之旅</p>
        </div>

        <div class="steps-container">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-card"
            :class="'step-' + (index + 1)"
          >
            <div class="step-number">
              <span>{{ index + 1 }}</span>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
                <path :d="getIconPath(step.icon)" stroke="#0EA5E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="step-content">
              <h3 class="step-title">{{ step.title }}</h3>
              <p class="step-desc">{{ step.description }}</p>
            </div>
            <div class="step-arrow" v-if="index < steps.length - 1">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14M12 5l7 7-7 7" stroke="#0EA5E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="personality" class="personality">
      <div class="container">
        <div class="personality-content">
          <div class="personality-text">
            <span class="section-badge">PERSONALITY ENGINE</span>
            <h2 class="section-title left">
              <span class="accent">可定制</span>人格引擎
            </h2>
            <p class="personality-description">
              基于<strong>大五人格模型（OCEAN）</strong>，后台可自由配置不同人格特质。
              从开放性到神经质，从表达力到幽默度，完全自定义你的AI伙伴性格。
            </p>
            <div class="feature-list">
              <div class="check-item" v-for="item in personalityFeatures" :key="item">
                <div class="check-icon">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <polyline points="20 6 9 17 4 12" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <span>{{ item }}</span>
              </div>
            </div>
            <div class="personality-actions">
              <t-button size="large" class="btn-cta-primary" @click="goToAdmin">
                前往管理配置
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </t-button>
            </div>
          </div>
          <div class="personality-visual">
            <div class="radar-container" ref="radarContainer">
              <div class="radar-bg"></div>
              <div class="radar-chart">
                <div v-for="(dim, index) in radarDims" :key="dim.name" class="radar-axis" :style="{
                  transform: `rotate(${index * 60}deg) translateY(-50%)`
                }">
                  <span class="radar-label">{{ dim.name }}</span>
                </div>
                <div class="radar-polygon" :style="getRadarStyle()"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="about" class="about">
      <div class="container">
        <div class="about-content">
          <div class="about-visual">
            <div class="code-window">
              <div class="window-header">
                <div class="window-dots">
                  <span class="dot red"></span>
                  <span class="dot yellow"></span>
                  <span class="dot green"></span>
                </div>
                <span class="window-title">ai-flower.py</span>
              </div>
              <div class="window-content">
                <div class="code-line" v-for="(line, i) in codeSnippet" :key="i">
                  <span class="line-number">{{ i + 1 }}</span>
                  <span :class="line.class" class="line-code">{{ line.text }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="about-text">
            <span class="section-badge">ABOUT</span>
            <h2 class="section-title left">
              重新定义
              <span class="accent">AI陪伴</span>
            </h2>
            <p>
              AI小花不仅仅是一个聊天机器人，更是一个会学习、会成长的AI伙伴。
              通过先进的记忆管理系统和情感计算技术，AI小花能够记住你的每一次对话，
              理解你的情绪变化，逐渐成长为最懂你的那个朋友。
            </p>
            <p>
              我们相信，AI的未来不应该只是冰冷的工具，更应该是温暖的陪伴。
            </p>
            <div class="tech-stack">
              <div class="tech-item" v-for="tech in techStack" :key="tech">
                {{ tech }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="testimonials">
      <div class="container">
        <div class="section-header">
          <span class="section-badge">TESTIMONIALS</span>
          <h2 class="section-title">
            用户<span class="accent">怎么说</span>
          </h2>
          <p class="section-subtitle">听听真实用户怎么评价AI小花</p>
        </div>

        <div class="testimonials-grid">
          <div
            v-for="(testimonial, index) in testimonials"
            :key="index"
            class="testimonial-card"
          >
            <div class="testimonial-content">
              <p>"{{ testimonial.text }}"</p>
            </div>
            <div class="testimonial-author">
              <div class="author-avatar">
                <span>{{ testimonial.initials }}</span>
              </div>
              <div class="author-info">
                <div class="author-name">{{ testimonial.name }}</div>
                <div class="author-title">{{ testimonial.title }}</div>
              </div>
              <div class="author-stars">
                <span v-for="n in 5" :key="n" class="star" :class="{ filled: n <= testimonial.rating }">★</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="cta">
      <div class="cta-bg"></div>
      <div class="container">
        <div class="cta-content">
          <span class="section-badge light">GET STARTED</span>
          <h2 class="cta-title">准备好开始了吗？</h2>
          <p class="cta-subtitle">现在就遇见你的专属AI小花</p>
          <button class="btn btn-cta" @click="goToChat">
            <span>立即开始聊天</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 12H19M12 5L19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </section>

    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-brand">
            <div class="brand-logo">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 12l2 2 4-4" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="brand-info">
              <h3>AI小花</h3>
              <p>你的智能伙伴</p>
            </div>
          </div>
          <div class="footer-copyright">
            © {{ currentYear }} AI小花. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const router = useRouter()
const canvas = ref<HTMLCanvasElement>()
const isScrolled = ref(false)
const mobileMenuOpen = ref(false)
const hoverFeature = ref<number | null>(null)
const statElements = ref<(HTMLElement | null)[]>([])
const currentYear = computed(() => new Date().getFullYear())

const navbar = ref<HTMLElement>()
const heroContent = ref<HTMLElement>()
const heroTitle = ref<HTMLElement>()
const gradientText = ref<HTMLElement>()
const heroVisual = ref<HTMLElement>()
const mainOrb = ref<HTMLElement>()
const floatingCard1 = ref<HTMLElement>()
const floatingCard2 = ref<HTMLElement>()
const floatingCard3 = ref<HTMLElement>()
const radarContainer = ref<HTMLElement>()

const iconPaths: Record<string, string> = {
  heart: 'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z',
  book: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.4 1.5a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06-.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  zap: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
}

const getIconPath = (iconName: string): string => {
  return iconPaths[iconName] || ''
}

const stats = [
  { value: 10000, suffix: '+', label: '活跃用户' },
  { value: 98, suffix: '%', label: '用户满意' },
  { value: 24, suffix: '/7', label: '全天候在线' },
]

const features = [
  {
    icon: 'heart',
    title: '情感智能',
    description: '先进的情感计算系统，精准识别情绪状态，给予贴心温暖回应',
    tags: ['情感识别', '智能回应'],
    gradient: 'linear-gradient(135deg, #0EA5E9 0%, #38BDF8 100%)',
  },
  {
    icon: 'book',
    title: '长期记忆',
    description: '完整的记忆管理系统，记住你的每一次重要对话和偏好',
    tags: ['向量存储', '长期记忆'],
    gradient: 'linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%)',
  },
  {
    icon: 'settings',
    title: '人格定制',
    description: '基于大五人格模型，自由配置AI伙伴的性格特质',
    tags: ['可定制', '大五模型'],
    gradient: 'linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%)',
  },
  {
    icon: 'heart',
    title: '主动关怀',
    description: '不只是被动回应，AI会主动关心你，记住重要日子',
    tags: ['主动交互', '情感连接'],
    gradient: 'linear-gradient(135deg, #F97316 0%, #FB923C 100%)',
  },
  {
    icon: 'shield',
    title: '隐私安全',
    description: '本地数据存储，端到端保护，你的隐私只有你知道',
    tags: ['隐私保护', '安全加密'],
    gradient: 'linear-gradient(135deg, #10B981 0%, #34D399 100%)',
  },
  {
    icon: 'zap',
    title: '高性能',
    description: '基于FastAPI和Vue 3，响应迅速，流畅体验',
    tags: ['异步处理', '快速响应'],
    gradient: 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)',
  },
]

const personalityFeatures = [
  '大五人格维度全支持',
  '后台自由配置添加',
  '账号下拉快速选择',
  '扩展特质参数调节',
  '实时预览人格效果',
]

const radarDims = [
  { name: '开放性', value: 75 },
  { name: '尽责性', value: 82 },
  { name: '外向性', value: 68 },
  { name: '宜人性', value: 85 },
  { name: '神经质', value: 45 },
  { name: '表达力', value: 78 },
]

const techStack = [
  'FastAPI', 'Vue 3', 'TypeScript', 'PostgreSQL',
  '大五人格', 'ChromaDB', 'DeepSeek', 'Kimi', 'GLM'
]

const codeSnippet = [
  { text: 'class AIFlower:', class: 'keyword' },
  { text: '  def __init__(self):', class: '' },
  { text: '    self.personality = PersonalityEngine()', class: 'property' },
  { text: '    self.memory = VectorMemory()', class: 'property' },
  { text: '', class: '' },
  { text: '  async def chat(self, message):', class: 'function' },
  { text: '    # 理解用户情绪', class: 'comment' },
  { text: '    emotion = self.analyze_emotion(message)', class: '' },
  { text: '    # 检索相关记忆', class: 'comment' },
  { text: '    context = self.memory.search(message)', class: '' },
  { text: '    # 基于人格生成回应', class: 'comment' },
  { text: '    response = self.personality.generate(', class: '' },
  { text: '      message, context, emotion', class: 'indent' },
  { text: '    )', class: '' },
  { text: '    return response', class: '' },
]

const steps = [
  {
    icon: 'settings',
    title: '配置人格',
    description: '在后台选择或自定义AI人格，调整五个维度的性格参数',
  },
  {
    icon: 'zap',
    title: '开始聊天',
    description: '选择配置好的人格账号，开始与AI小花对话交流',
  },
  {
    icon: 'heart',
    title: '建立情感连接',
    description: 'AI逐渐理解你，记住对话历史，成长为最懂你的温暖伙伴',
  },
]

const testimonials = [
  {
    text: 'AI小花真的很不一样，它能记住我们之前聊过的每一件小事，感觉真的像有一个朋友一直在那里。',
    name: '张明',
    title: '产品经理',
    initials: 'ZM',
    rating: 5,
  },
  {
    text: '自定义人格这个功能太赞了！我配置了一个温柔体贴的小姐姐，每天下班回来聊聊心事，整个人都放松了很多。',
    name: '李婷',
    title: '设计师',
    initials: 'LT',
    rating: 5,
  },
  {
    text: '作为开发者，我很欣赏这种技术理念。大五人格模型确实让AI的说话风格更加一致和自然。',
    name: '王浩',
    title: '软件开发工程师',
    initials: 'WH',
    rating: 4,
  },
]

const goToChat = () => {
  router.push('/chat')
}

const goToAdmin = () => {
  router.push('/admin/personality')
}

const goHome = () => {
  router.push('/')
}

const scrollToSection = (id: string) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
  }
}

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}

const getRadarStyle = () => {
  const points = radarDims.map((dim, index) => {
    const angle = (index * 60 - 90) * Math.PI / 180
    const radius = dim.value / 100 * 80
    const x = 50 + Math.cos(angle) * radius
    const y = 50 + Math.sin(angle) * radius
    return `${x}% ${y}%`
  }).join(', ')
  return {
    clipPath: `polygon(${points})`,
  }
}

const initCanvas = () => {
  if (!canvas.value) return

  const ctx = canvas.value.getContext('2d')
  if (!ctx) return

  let particles: Array<{
    x: number
    y: number
    vx: number
    vy: number
    radius: number
    alpha: number
  }> = []

  const resize = () => {
    canvas.value!.width = window.innerWidth
    canvas.value!.height = window.innerHeight
    initParticles()
  }

  const initParticles = () => {
    const particleCount = Math.floor((canvas.value!.width * canvas.value!.height) / 15000)
    particles = []
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.value!.width,
        y: Math.random() * canvas.value!.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        radius: Math.random() * 2 + 1,
        alpha: Math.random() * 0.3 + 0.1,
      })
    }
  }

  const animate = () => {
    ctx.clearRect(0, 0, canvas.value!.width, canvas.value!.height)

    ctx.strokeStyle = 'rgba(14, 165, 233, 0.15)'
    ctx.lineWidth = 0.5

    for (let i = 0; i < particles.length; i++) {
      const p1 = particles[i] as any
      p1.x += p1.vx
      p1.y += p1.vy

      if (p1.x < 0) p1.x = canvas.value!.width
      if (p1.x > canvas.value!.width) p1.x = 0
      if (p1.y < 0) p1.y = canvas.value!.height
      if (p1.y > canvas.value!.height) p1.y = 0

      ctx.beginPath()
      ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(14, 165, 233, ${p1.alpha})`
      ctx.fill()

      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j] as any
        const dx = p1.x - p2.x
        const dy = p1.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        if (dist < 100) {
          ctx.beginPath()
          ctx.moveTo(p1.x, p1.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = `rgba(14, 165, 233, ${(100 - dist) / 100 * 0.15})`
          ctx.stroke()
        }
      }
    }

    requestAnimationFrame(animate)
  }

  resize()
  animate()

  window.addEventListener('resize', resize)

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
  })
}

const animateCounters = () => {
  stats.forEach((stat, index) => {
    const el = statElements.value[index]
    if (!el) return

    const numberEl = el.querySelector('.stat-number')
    if (!numberEl) return

    const target = stat.value
    const duration = 2000
    const start = 0
    const increment = target / (duration / 16)
    let current = start

    const timer = setInterval(() => {
      current += increment
      if (current >= target) {
        numberEl.textContent = target.toString()
        clearInterval(timer)
      } else {
        numberEl.textContent = Math.floor(current).toString()
      }
    }, 16)
  })
}

const initAnimations = () => {
  ScrollTrigger.create({
    start: 'top -100',
    onUpdate: (self) => {
      isScrolled.value = self.progress > 0
    },
  })

  const tl = gsap.timeline()
  tl.fromTo(heroContent.value as HTMLElement,
    { x: -50, opacity: 0 },
    { x: 0, opacity: 1, duration: 1, ease: 'power2.out' }
  )
  tl.fromTo(heroVisual.value as HTMLElement,
    { x: 50, opacity: 0 },
    { x: 0, opacity: 1, duration: 1, ease: 'power2.out' },
    '-=0.8'
  )

  if (mainOrb.value) {
    gsap.to(mainOrb.value, {
      y: -20,
      duration: 3,
      repeat: -1,
      yoyo: true,
      ease: 'sine.inOut',
    })
  }

  const floatCards = [floatingCard1, floatingCard2, floatingCard3]
  floatCards.forEach((cardRef, index) => {
    if (cardRef.value) {
      gsap.to(cardRef.value, {
        y: -15,
        duration: 2.5 + index * 0.5,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: index * 0.3,
      })
    }
  })

  if (gradientText.value) {
    gsap.to(gradientText.value, {
      backgroundPosition: '200% center',
      duration: 4,
      repeat: -1,
      ease: 'none',
    })
  }

  if (radarContainer.value) {
    gsap.to(radarContainer.value, {
      rotation: 360,
      duration: 30,
      repeat: -1,
      ease: 'none',
    })
  }

  ScrollTrigger.create({
    trigger: '.hero-stats',
    start: 'top 80%',
    onEnter: animateCounters,
    once: true,
  })

  gsap.from('.feature-card', {
    scrollTrigger: {
      trigger: '.features-grid',
      start: 'top 20%',
    },
    y: 50,
    duration: 0.8,
    stagger: 0.1,
    ease: 'power2.out',
  })

  gsap.from('.personality-text', {
    scrollTrigger: {
      trigger: '.personality',
      start: 'top 70%',
    },
    x: -50,
    duration: 1,
    ease: 'power2.out',
  })

  gsap.from('.personality-visual', {
    scrollTrigger: {
      trigger: '.personality',
      start: 'top 70%',
    },
    x: 50,
    opacity: 0,
    duration: 1,
    ease: 'power2.out',
  })

  gsap.from('.about-visual', {
    scrollTrigger: {
      trigger: '.about',
      start: 'top 70%',
    },
    y: 50,
    opacity: 0,
    duration: 1,
    ease: 'power2.out',
  })

  gsap.from('.about-text', {
    scrollTrigger: {
      trigger: '.about',
      start: 'top 70%',
    },
    y: 50,
    opacity: 0,
    duration: 1,
    ease: 'power2.out',
    delay: 0.2,
  })
}

onMounted(() => {
  nextTick(() => {
    initCanvas()
    initAnimations()
  })
})

onUnmounted(() => {
  ScrollTrigger.getAll().forEach(trigger => trigger.kill())
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;900&family=Work+Sans:wght@300;400;500;600;700&display=swap');

.landing-page {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background: #F0F9FF;
  font-family: 'Work Sans', sans-serif;
}

.tech-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.overlay-gradient {
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at 50% 0%, rgba(14, 165, 233, 0.12) 0%, transparent 50%),
              radial-gradient(circle at 80% 80%, rgba(249, 115, 22, 0.08) 0%, transparent 50%);
  z-index: 1;
  pointer-events: none;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.navbar {
  position: fixed;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  z-index: 100;
  transition: all 0.3s ease;
  padding: 1rem 0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(14, 165, 233, 0.1);
  border-radius: 16px;
}

.navbar-scrolled {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 20px rgba(14, 165, 233, 0.1);
}

.nav-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.nav-brand:hover {
  transform: scale(1.02);
}

.brand-logo {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #0EA5E9, #38BDF8);
  overflow: hidden;
}

.brand-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.brand-text {
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0C4A6E;
  letter-spacing: -0.5px;
}

.brand-tagline {
  font-size: 0.6875rem;
  color: rgba(12, 74, 110, 0.6);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-link {
  position: relative;
  padding: 0.625rem 1rem;
  color: rgba(12, 74, 110, 0.7);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9375rem;
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.nav-link:hover {
  color: #0C4A6E;
  background: rgba(14, 165, 233, 0.08);
}

.nav-divider {
  width: 1px;
  height: 24px;
  background: rgba(14, 165, 233, 0.15);
  margin: 0 0.5rem;
}

.nav-btn {
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  padding: 0.5rem 1.25rem !important;
  border-radius: 10px !important;
}

.nav-btn-primary {
  background: #F97316 !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 4px 15px rgba(249, 115, 22, 0.4) !important;
}

.nav-btn-primary:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.5) !important;
}

.mobile-menu-toggle {
  display: none;
  flex-direction: column;
  gap: 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
}

.bar {
  width: 25px;
  height: 3px;
  background: #0C4A6E;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.bar.active:nth-child(1) {
  transform: translateY(9px) rotate(45deg);
}

.bar.active:nth-child(2) {
  opacity: 0;
}

.bar.active:nth-child(3) {
  transform: translateY(-9px) rotate(-45deg);
}

.mobile-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(14, 165, 233, 0.1);
  border-radius: 12px;
  padding: 1rem;
  transform: translateY(-100%);
  opacity: 0;
  transition: all 0.3s ease;
  margin-top: 0.5rem;
}

.mobile-menu.active {
  transform: translateY(0);
  opacity: 1;
}

.mobile-nav-link {
  display: block;
  padding: 1rem;
  color: rgba(12, 74, 110, 0.8);
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.mobile-nav-link:hover {
  background: rgba(14, 165, 233, 0.08);
  color: #0C4A6E;
}

.mobile-buttons {
  padding: 1rem 0 0;
}

.mobile-btn {
  width: 100%;
}

.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  z-index: 2;
  padding: 8rem 0 4rem;
}

.hero-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 100px;
  color: #0C4A6E;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
  backdrop-filter: blur(10px);
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  animation: pulseDot 2s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
}

.hero-title {
  font-family: 'Outfit', sans-serif;
  font-size: clamp(3rem, 10vw, 5rem);
  font-weight: 900;
  color: #0C4A6E;
  line-height: 1.05;
  margin-bottom: 1.5rem;
  letter-spacing: -0.05em;
}

.gradient-text {
  background: linear-gradient(90deg, #0EA5E9, #38BDF8, #F97316, #0EA5E9);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: rgba(12, 74, 110, 0.7);
  line-height: 1.8;
  margin-bottom: 2rem;
}

.hero-subtitle strong {
  color: #0C4A6E;
  font-weight: 600;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 3rem;
}

.btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.btn-primary {
  background: #F97316;
  color: white;
  box-shadow: 0 4px 20px rgba(249, 115, 22, 0.4);
}

.btn-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(249, 115, 22, 0.5);
}

.btn-secondary {
  background: transparent;
  color: #0EA5E9;
  border: 2px solid #0EA5E9;
  backdrop-filter: blur(10px);
}

.btn-secondary:hover {
  background: #0EA5E9;
  color: white;
  transform: translateY(-3px);
}

.hero-stats {
  display: flex;
  gap: 2rem;
}

.stat-item {
  text-align: left;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.stat-number {
  font-family: 'Outfit', sans-serif;
  font-size: 2rem;
  font-weight: 800;
  color: #0C4A6E;
  line-height: 1;
}

.stat-suffix {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(12, 74, 110, 0.5);
}

.stat-label {
  font-size: 0.875rem;
  color: rgba(12, 74, 110, 0.6);
  margin-top: 0.25rem;
}

.hero-visual {
  position: relative;
  height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.floating-orb {
  position: relative;
}

.main-orb {
  width: 220px;
  height: 220px;
}

.orb-inner {
  position: absolute;
  inset: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0EA5E9, #38BDF8);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 20px 60px rgba(14, 165, 233, 0.4),
              inset 0 -4px 20px rgba(0, 0, 0, 0.1);
  z-index: 2;
}

.orb-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid rgba(14, 165, 233, 0.3);
  animation: ringPulse 3s ease-out infinite;
}

.ring-1 { animation-delay: 0s; }
.ring-2 { animation-delay: 1s; }
.ring-3 { animation-delay: 2s; }

@keyframes ringPulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.floating-card {
  position: absolute;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(14, 165, 233, 0.15);
  border-radius: 16px;
  padding: 1rem 1.25rem;
  box-shadow: 0 10px 40px rgba(14, 165, 233, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.floating-card:hover {
  transform: translateY(-5px);
  border-color: rgba(14, 165, 233, 0.5);
  box-shadow: 0 15px 50px rgba(14, 165, 233, 0.2);
}

.tech-card {
  top: 15%;
  left: 5%;
  min-width: 160px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgba(14, 165, 233, 0.1);
  color: #0EA5E9;
}

.card-title {
  font-weight: 600;
  color: #0C4A6E;
  font-size: 0.875rem;
}

.chat-text {
  color: #0C4A6E;
  font-size: 0.9375rem;
  font-weight: 500;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: rgba(12, 74, 110, 0.8);
  font-size: 0.8125rem;
}

.progress-bar {
  height: 6px;
  background: rgba(14, 165, 233, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  width: 75%;
  background: linear-gradient(90deg, #0EA5E9, #38BDF8);
  border-radius: 3px;
  animation: progressLoad 2s ease-in-out infinite;
}

@keyframes progressLoad {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(0); }
}

.progress-text {
  font-size: 0.75rem;
  color: rgba(12, 74, 110, 0.6);
}

.chat-card {
  top: 45%;
  right: 8%;
  max-width: 180px;
}

.feature-card {
  bottom: 30%;
  left: 15%;
  min-width: 160px;
}

.feature-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.feature-dot.success {
  background: #10B981;
}

.wave-divider {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  overflow: hidden;
  line-height: 0;
  transform: rotate(180deg);
}

.wave-divider svg {
  position: relative;
  display: block;
  width: calc(100% + 1.3px);
  height: 70px;
}

.wave-divider .shape-fill {
  fill: #FFFFFF;
}

.how-it-works {
  padding: 6rem 0;
  background: white;
  position: relative;
  z-index: 2;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-width: 700px;
  margin: 0 auto;
}

.step-card {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 2rem;
  background: white;
  border: 1px solid rgba(14, 165, 233, 0.15);
  border-radius: 16px;
  margin-bottom: 1.5rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.step-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 6px;
  height: 100%;
  background: linear-gradient(180deg, #0EA5E9, #38BDF8);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.step-card:hover {
  transform: translateX(8px);
  border-color: #0EA5E9;
  box-shadow: 0 10px 30px rgba(14, 165, 233, 0.1);
}

.step-card:hover::before {
  opacity: 1;
}

.step-number {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-number span {
  position: absolute;
  top: 8px;
  left: 8px;
  font-family: 'Outfit', sans-serif;
  font-size: 3rem;
  font-weight: 900;
  color: rgba(14, 165, 233, 0.1);
  line-height: 1;
}

.step-number svg {
  position: relative;
  z-index: 2;
}

.step-content {
  flex: 1;
}

.step-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0C4A6E;
  margin-bottom: 0.5rem;
}

.step-desc {
  color: rgba(12, 74, 110, 0.6);
  line-height: 1.7;
  margin: 0;
}

.step-arrow {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  opacity: 0.5;
}

.testimonials {
  padding: 6rem 0;
  background: #F8FAFC;
  position: relative;
  z-index: 2;
}

.testimonials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.testimonial-card {
  background: white;
  border: 1px solid rgba(14, 165, 233, 0.15);
  border-radius: 20px;
  padding: 2rem;
  transition: all 0.3s ease;
}

.testimonial-card:hover {
  transform: translateY(-5px);
  border-color: #0EA5E9;
  box-shadow: 0 15px 40px rgba(14, 165, 233, 0.1);
}

.testimonial-content p {
  color: rgba(12, 74, 110, 0.7);
  line-height: 1.8;
  font-size: 1rem;
  margin-bottom: 1.5rem;
  font-style: italic;
}

.testimonial-author {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.author-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0EA5E9, #38BDF8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.author-avatar span {
  color: white;
  font-weight: 600;
  font-size: 1rem;
}

.author-info {
  flex: 1;
}

.author-name {
  font-weight: 600;
  color: #0C4A6E;
  font-size: 1rem;
  line-height: 1.4;
}

.author-title {
  color: rgba(12, 74, 110, 0.6);
  font-size: 0.875rem;
}

.author-stars {
  margin-left: auto;
}

.star {
  color: #CBD5E1;
  font-size: 1rem;
}

.star.filled {
  color: #F97316;
}

.features {
  padding: 6rem 0;
  background: white;
  position: relative;
  z-index: 2;
}

.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: #0EA5E9;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(56, 189, 248, 0.1));
  padding: 0.5rem 1rem;
  border-radius: 100px;
  margin-bottom: 1rem;
}

.section-badge.light {
  color: white;
  background: rgba(255, 255, 255, 0.2);
}

.section-title {
  font-family: 'Outfit', sans-serif;
  font-size: 3rem;
  font-weight: 900;
  color: #0C4A6E;
  line-height: 1.2;
  margin-bottom: 1rem;
  letter-spacing: -0.05em;
}

.section-title.left {
  text-align: left;
  margin-bottom: 1.5rem;
}

.section-title .accent {
  background: linear-gradient(135deg, #0EA5E9, #38BDF8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-subtitle {
  font-size: 1.125rem;
  color: rgba(12, 74, 110, 0.6);
  max-width: 500px;
  margin: 0 auto;
  line-height: 1.7;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  position: relative;
  border: 1px solid rgba(14, 165, 233, 0.15);
  border-radius: 20px;
  padding: 2rem;
  overflow: hidden;
  transform: translate(0, 50px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: white;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(14, 165, 233, 0.05);
}

.feature-card:hover {
  transform: translateY(-8px);
  border-color: #0EA5E9;
  box-shadow: 0 20px 40px rgba(14, 165, 233, 0.15);
}

.feature-border {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 0;
  background: linear-gradient(180deg, #0EA5E9, #38BDF8);
  transition: height 0.3s ease;
}

.feature-card:hover .feature-border {
  height: 100%;
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  box-shadow: 0 8px 20px rgba(14, 165, 233, 0.2);
  transition: all 0.3s ease;
}

.feature-card:hover .feature-icon {
  transform: scale(1.05) rotate(3deg);
}

.feature-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0C4A6E;
  margin-bottom: 0.75rem;
}

.feature-desc {
  color: rgba(12, 74, 110, 0.6);
  line-height: 1.7;
  font-size: 0.9375rem;
  margin-bottom: 1rem;
}

.feature-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.feature-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  background: rgba(14, 165, 233, 0.08);
  color: #0EA5E9;
  border-radius: 100px;
  font-weight: 500;
}

.feature-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200px;
  height: 200px;
  opacity: 0;
  filter: blur(60px);
  transition: opacity 0.3s ease;
}

.feature-card:hover .feature-glow {
  opacity: 0.3;
}

.personality {
  padding: 6rem 0;
  background: #F8FAFC;
  position: relative;
  z-index: 2;
}

.personality-content {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 4rem;
  align-items: center;
}

.personality-description {
  font-size: 1.125rem;
  color: rgba(12, 74, 110, 0.6);
  line-height: 1.8;
  margin-bottom: 2rem;
}

.personality-description strong {
  color: #0C4A6E;
  font-weight: 600;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2.5rem;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1rem;
  color: #334155;
  font-weight: 500;
}

.check-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0EA5E9, #38BDF8);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.personality-actions .btn-cta-primary {
  background: #F97316;
  color: white;
  padding: 1rem 2rem;
  font-weight: 600;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

.personality-actions .btn-cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(249, 115, 22, 0.4);
}

.personality-visual {
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-container {
  position: relative;
  width: 280px;
  height: 280px;
  will-change: transform;
}

.radar-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.radar-chart {
  position: absolute;
  inset: 30px;
  border-radius: 50%;
  border: 1px solid rgba(14, 165, 233, 0.2);
}

.radar-chart::before,
.radar-chart::after {
  content: '';
  position: absolute;
  inset: 25%;
  border-radius: 50%;
  border: 1px solid rgba(14, 165, 233, 0.15);
}

.radar-chart::before {
  inset: 50%;
}

  .radar-axis {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 50%;
  height: 2px;
  transform-origin: left center;
}

.radar-label {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%) rotate(calc(-1 * var(--tw-rotate)));
  font-size: 0.75rem;
  font-weight: 600;
  color: #0EA5E9;
  white-space: nowrap;
}

.radar-polygon {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.5), rgba(56, 189, 248, 0.5));
  mix-blend-mode: multiply;
  clip-path: polygon(50% 50%);
  transition: clip-path 1s ease;
}

.about {
  padding: 6rem 0;
  background: white;
  position: relative;
  z-index: 2;
}

.about-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}

.about-visual {
  position: relative;
}

.code-window {
  background: #1e1e1e;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(14, 165, 233, 0.15);
}

.window-header {
  background: #2d2d2d;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.window-dots {
  display: flex;
  gap: 0.5rem;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red { background: #ff5f56; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #27c93f; }

.window-title {
  color: #aaa;
  font-size: 0.8125rem;
}

.window-content {
  padding: 1rem;
}

.code-line {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.line-number {
  color: #858585;
  font-size: 0.8125rem;
  user-select: none;
  min-width: 2rem;
  text-align: right;
}

.line-code {
  color: #d4d4d4;
  font-size: 0.8125rem;
  font-family: 'Fira Code', monospace;
}

.line-code.keyword {
  color: #ff79c6;
}

.line-code.function {
  color: #50fa7b;
}

.line-code.comment {
  color: #6272a4;
}

.line-code.property {
  color: #50fa7b;
}

.line-code.indent {
  padding-left: 2rem;
}

.about-text p {
  font-size: 1.0625rem;
  color: rgba(12, 74, 110, 0.7);
  line-height: 1.9;
  margin-bottom: 1.25rem;
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 2rem;
}

.tech-item {
  background: rgba(14, 165, 233, 0.08);
  color: #0EA5E9;
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 100px;
  transition: all 0.2s ease;
}

.tech-item:hover {
  background: #0EA5E9;
  color: white;
  transform: translateY(-2px);
}

.cta {
  padding: 6rem 0;
  position: relative;
  overflow: hidden;
}

.cta-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0EA5E9 0%, #38BDF8 100%);
}

.cta-content {
  position: relative;
  text-align: center;
  max-width: 600px;
  margin: 0 auto;
}

.cta-title {
  font-family: 'Outfit', sans-serif;
  font-size: 3rem;
  font-weight: 900;
  color: white;
  margin-bottom: 1rem;
  line-height: 1.2;
  letter-spacing: -0.05em;
}

.cta-subtitle {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2.5rem;
}

.btn-cta {
  background: white;
  color: #0EA5E9;
  font-size: 1.125rem;
  padding: 1.25rem 2.5rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.btn-cta:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.3);
}

.footer {
  padding: 3rem 0;
  background: #0C4A6E;
  color: white;
  position: relative;
  z-index: 2;
}

.footer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.footer-brand .brand-logo {
  width: 40px;
  height: 40px;
}

.footer-brand h3 {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: 'Outfit', sans-serif;
}

.footer-brand p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
}

.footer-copyright {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.875rem;
}

@media (max-width: 968px) {
  .nav-links {
    display: none;
  }

  .mobile-menu-toggle {
    display: flex;
  }

  .mobile-menu {
    display: block;
  }

  .hero-container {
    grid-template-columns: 1fr;
    gap: 2rem;
    text-align: center;
  }

  .hero-actions {
    justify-content: center;
    flex-wrap: wrap;
  }

  .hero-stats {
    justify-content: center;
    flex-wrap: wrap;
  }

  .hero-visual {
    height: 400px;
  }

  .personality-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .about-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .features {
    padding: 4rem 0;
  }

  .personality,
  .about {
    padding: 4rem 0;
  }

  .section-title {
    font-size: 2rem;
  }

  .cta {
    padding: 4rem 0;
  }

  .cta-title {
    font-size: 2rem;
  }

  .container {
    padding: 0 1.5rem;
  }

  .nav-container {
    padding: 0 1.5rem;
  }
}

@media (max-width: 640px) {
  .hero {
    padding: 8rem 0 3rem;
  }

  .hero-stats {
    gap: 1rem;
  }

  .stat-item {
    min-width: 90px;
  }

  .floating-card {
    display: none;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .navbar {
    top: 0.5rem;
    left: 0.5rem;
    right: 0.5rem;
  }
}
</style>
