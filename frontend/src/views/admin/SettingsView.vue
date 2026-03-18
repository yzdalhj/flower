<template>
  <div class="settings-view">
    <t-tabs v-model="activeTab" class="settings-tabs">
      <!-- LLM 厂商配置 -->
      <t-tab-panel value="providers" label="LLM 厂商">
        <t-card :bordered="false" class="settings-card">
          <template #actions>
            <t-space>
              <t-button theme="default" variant="outline" @click="loadProviders">
                <template #icon><t-icon name="refresh" /></template>
                刷新
              </t-button>
              <t-button theme="primary" @click="handleInitDefaults">
                <template #icon><t-icon name="add" /></template>
                初始化默认厂商
              </t-button>
              <t-button theme="primary" @click="showProviderDialog = true">
                <template #icon><t-icon name="add" /></template>
                添加厂商
              </t-button>
            </t-space>
          </template>

          <t-table
            :data="providers"
            :columns="providerColumns"
            :loading="loadingProviders"
            row-key="id"
            stripe
          >
            <template #is_enabled="{ row }">
              <t-switch v-model="row.is_enabled" @change="(val: boolean) => toggleProvider(row, val)" />
            </template>
            <template #is_default="{ row }">
              <t-tag v-if="row.is_default" theme="primary" variant="light">默认</t-tag>
              <t-button v-else theme="default" variant="text" size="small" @click="setDefaultProvider(row.id)">
                设为默认
              </t-button>
            </template>
            <template #operation="{ row }">
              <t-space>
                <t-button theme="primary" variant="text" size="small" @click="editProvider(row)">
                  编辑
                </t-button>
                <t-button theme="danger" variant="text" size="small" @click="deleteProvider(row)">
                  删除
                </t-button>
              </t-space>
            </template>
          </t-table>
        </t-card>
      </t-tab-panel>

      <!-- 系统设置 -->
      <t-tab-panel value="system" label="系统设置">
        <t-card :bordered="false" class="settings-card">
          <template #actions>
            <t-space>
              <t-button theme="default" variant="outline" @click="loadSettings">
                <template #icon><t-icon name="refresh" /></template>
                刷新
              </t-button>
              <t-button theme="default" variant="outline" @click="resetSettings">
                <template #icon><t-icon name="rollback" /></template>
                重置
              </t-button>
              <t-button theme="primary" @click="saveSettings">
                <template #icon><t-icon name="save" /></template>
                保存
              </t-button>
            </t-space>
          </template>

          <DynamicForm
            ref="formRef"
            v-model="formData"
            :config="formConfig"
            @submit="saveSettings"
          />
        </t-card>
      </t-tab-panel>
    </t-tabs>

    <!-- 厂商编辑对话框 -->
    <t-dialog
      v-model:visible="showProviderDialog"
      :header="editingProvider ? '编辑厂商' : '添加厂商'"
      width="600px"
      @confirm="saveProvider"
    >
      <DynamicForm
        ref="providerFormRef"
        v-model="providerFormData"
        :config="providerFormConfig"
      />
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import { DynamicForm } from '@/components/DynamicForm'
import { settingsApi } from '@/api'
import type { SystemSettings, LLMProvider, CreateLLMProviderRequest } from '@/api/settings'
import type { FormConfig } from '@/components/DynamicForm/types'
import type { Y } from 'vue-router/dist/index-DFCq6eJK.js'

const activeTab = ref('providers')
const formRef = ref<InstanceType<typeof DynamicForm>>()
const providerFormRef = ref<InstanceType<typeof DynamicForm>>()

// 系统设置
const formData = ref<Partial<SystemSettings>>({})
const loadingSettings = ref(false)

// LLM 厂商
const providers = ref<LLMProvider[]>([])
const loadingProviders = ref(false)
const showProviderDialog = ref(false)
const editingProvider = ref<LLMProvider | null>(null)
const providerFormData = ref<Partial<CreateLLMProviderRequest>>({})

// 厂商表格列
const providerColumns = [
  { colKey: 'display_name', title: '厂商名称', width: 150 },
  { colKey: 'name', title: '标识', width: 120 },
  { colKey: 'base_url', title: 'API地址', ellipsis: true },
  { colKey: 'default_model', title: '默认模型', width: 150 },
  { colKey: 'is_enabled', title: '启用', width: 100 },
  { colKey: 'is_default', title: '默认', width: 100 },
  { colKey: 'priority', title: '优先级', width: 80 },
  { colKey: 'operation', title: '操作', width: 150 },
]

// 系统设置表单配置
const formConfig = computed<FormConfig>(() => ({
  labelWidth: 160,
  showActions: false,
  groups: [
    { key: 'features', title: '功能开关' },
    { key: 'limits', title: '限制设置' },
  ],
  fields: [
    {
      key: 'emotion_analysis_enabled',
      label: '情感分析',
      type: 'switch',
      group: 'features',
      defaultValue: true,
      span: 12,
    },
    {
      key: 'memory_enabled',
      label: '记忆功能',
      type: 'switch',
      group: 'features',
      defaultValue: true,
      span: 12,
    },
    {
      key: 'proactive_enabled',
      label: '主动行为',
      type: 'switch',
      group: 'features',
      defaultValue: true,
      span: 12,
    },
    {
      key: 'sticker_enabled',
      label: '表情包',
      type: 'switch',
      group: 'features',
      defaultValue: true,
      span: 12,
    },
    {
      key: 'fallback_enabled',
      label: '故障切换',
      type: 'switch',
      group: 'features',
      defaultValue: true,
      span: 12,
    },
    {
      key: 'deep_thinking_enabled',
      label: '深度思考',
      type: 'switch',
      group: 'features',
      defaultValue: false,
      span: 12,
      help: '启用后AI会进行更深入的思考和推理',
    },
    {
      key: 'daily_message_limit',
      label: '每日消息限制',
      type: 'number',
      group: 'limits',
      min: 0,
      max: 10000,
      defaultValue: 1000,
    },
    {
      key: 'daily_cost_limit',
      label: '每日成本限制 (¥)',
      type: 'number',
      group: 'limits',
      min: 0,
      max: 1000,
      step: 0.1,
      defaultValue: 50,
    },
  ],
}))

// 厂商表单配置
const providerFormConfig = computed<FormConfig>(() => ({
  labelWidth: 120,
  showActions: false,
  fields: [
    {
      key: 'name',
      label: '厂商标识',
      type: 'input',
      placeholder: '如 deepseek、kimi',
      rules: [{ required: true, message: '请输入厂商标识' }],
    },
    {
      key: 'display_name',
      label: '显示名称',
      type: 'input',
      placeholder: '如 DeepSeek',
      rules: [{ required: true, message: '请输入显示名称' }],
    },
    {
      key: 'base_url',
      label: 'API地址',
      type: 'input',
      placeholder: 'https://api.example.com/v1',
      rules: [{ required: true, message: '请输入API地址' }],
    },
    {
      key: 'api_key',
      label: 'API密钥',
      type: 'password',
      placeholder: '请输入API密钥',
      rules: [{ required: true, message: '请输入API密钥' }],
    },
    {
      key: 'default_model',
      label: '默认模型',
      type: 'input',
      placeholder: '如 gpt-3.5-turbo',
      rules: [{ required: true, message: '请输入默认模型' }],
    },
    {
      key: 'priority',
      label: '优先级',
      type: 'number',
      min: 0,
      max: 100,
      defaultValue: 0,
    },
    {
      key: 'timeout',
      label: '超时时间(秒)',
      type: 'number',
      min: 5,
      max: 120,
      defaultValue: 30,
    },
    {
      key: 'max_retries',
      label: '最大重试次数',
      type: 'number',
      min: 0,
      max: 10,
      defaultValue: 3,
    },
    {
      key: 'description',
      label: '描述',
      type: 'textarea',
      rows: 3,
      placeholder: '可选描述信息',
    },
  ],
}))

// 加载厂商列表
const loadProviders = async () => {
  loadingProviders.value = true
  try {
    providers.value = await settingsApi.getProviders()
  } catch (error) {
    MessagePlugin.error('加载厂商列表失败')
    console.error(error)
  } finally {
    loadingProviders.value = false
  }
}

// 初始化默认厂商
const handleInitDefaults = async () => {
  try {
    await settingsApi.initDefaultProviders()
    MessagePlugin.success('默认厂商已初始化')
    loadProviders()
  } catch (error) {
    MessagePlugin.error('初始化失败')
    console.error(error)
  }
}

// 编辑厂商
const editProvider = (row: LLMProvider) => {
  editingProvider.value = row
  providerFormData.value = { ...row }
  showProviderDialog.value = true
}

// 保存厂商
const saveProvider = async () => {
  const valid = await providerFormRef.value?.validate()
  if (valid !== true) return

  const data = providerFormRef.value?.getFormData() as any

  try {
    if (editingProvider.value) {
      await settingsApi.updateProvider(editingProvider.value.id, data)
      MessagePlugin.success('厂商已更新')
    } else {
      await settingsApi.createProvider(data)
      MessagePlugin.success('厂商已创建')
    }
    showProviderDialog.value = false
    editingProvider.value = null
    providerFormData.value = {}
    loadProviders()
  } catch (error) {
    MessagePlugin.error('保存失败')
    console.error(error)
  }
}

// 删除厂商
const deleteProvider = (row: LLMProvider) => {
  const confirmDialog = DialogPlugin.confirm({
    header: '确认删除',
    body: `确定要删除厂商 "${row.display_name}" 吗？`,
    onConfirm: async () => {
      try {
        await settingsApi.deleteProvider(row.id)
        MessagePlugin.success('厂商已删除')
        loadProviders()
        confirmDialog.destroy()
      } catch (error) {
        MessagePlugin.error('删除失败')
        console.error(error)
      }
    },
  })
}

// 切换厂商启用状态
const toggleProvider = async (row: LLMProvider, enabled: boolean) => {
  try {
    await settingsApi.updateProvider(row.id, { is_enabled: enabled })
    MessagePlugin.success(enabled ? '厂商已启用' : '厂商已禁用')
    loadProviders()
  } catch (error) {
    MessagePlugin.error('操作失败')
    console.error(error)
  }
}

// 设为默认厂商
const setDefaultProvider = async (id: string) => {
  try {
    await settingsApi.updateProvider(id, { is_default: true })
    MessagePlugin.success('已设为默认厂商')
    loadProviders()
  } catch (error) {
    MessagePlugin.error('设置失败')
    console.error(error)
  }
}

// 加载系统设置
const loadSettings = async () => {
  loadingSettings.value = true
  try {
    const settings = await settingsApi.getSettings()
    formData.value = { ...settings }
    formRef.value?.setFormData({ ...settings })
  } catch (error) {
    MessagePlugin.error('加载设置失败')
    console.error(error)
  } finally {
    loadingSettings.value = false
  }
}

// 保存系统设置
const saveSettings = async () => {
  const valid = await formRef.value?.validate()
  if (valid !== true) return

  const data = formRef.value?.getFormData()
  if (!data) return

  try {
    await settingsApi.updateSettings(data as Partial<SystemSettings>)
    MessagePlugin.success('设置已保存')
  } catch (error) {
    MessagePlugin.error('保存设置失败')
    console.error(error)
  }
}

// 重置系统设置
const resetSettings = async () => {
  try {
    const settings = await settingsApi.resetSettings()
    formData.value = { ...settings }
    formRef.value?.setFormData({ ...settings })
    MessagePlugin.success('设置已重置为默认值')
  } catch (error) {
    MessagePlugin.error('重置设置失败')
    console.error(error)
  }
}

// 初始化
onMounted(() => {
  loadProviders()
  loadSettings()
})
</script>

<style scoped>
.settings-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.settings-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.settings-tabs :deep(.t-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.settings-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.settings-card :deep(.t-card__body) {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.settings-card :deep(.t-card__header) {
  padding: 16px 24px;
}

:deep(.t-form) {
  max-width: none;
}

:deep(.t-form__item) {
  margin-bottom: 20px;
}

:deep(.t-divider) {
  margin: 24px 0 16px;
}

:deep(.t-divider__text) {
  font-size: 15px;
  font-weight: 600;
  color: var(--td-text-color-primary);
  background: var(--td-bg-color-container);
  padding: 0 16px;
}

:deep(.t-switch) {
  margin-top: 4px;
}
</style>
