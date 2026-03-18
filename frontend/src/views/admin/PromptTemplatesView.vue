<template>
  <div class="prompt-templates-view">
    <ProTable
      ref="tableRef"
      :config="tableConfig"
      @create="handleCreate"
      @edit="handleEdit"
      @delete="handleDelete"
      @submit="handleSubmit"
    />

    <!-- 区块管理对话框 -->
    <t-dialog
      v-model:visible="sectionsVisible"
      header="区块管理"
      width="1000px"
      top="10vh"
      :footer="false"
    >
      <SectionsManager
        v-if="currentTemplate"
        :template-id="currentTemplate.id"
        :sections="currentTemplate.sections || []"
        @update="handleSectionsUpdate"
      />
    </t-dialog>

    <!-- 预览对话框 -->
    <t-dialog
      v-model:visible="previewVisible"
      header="Prompt预览"
      width="900px"
      top="10vh"
      :footer="false"
    >
      <t-loading :loading="previewLoading">
        <t-textarea
          v-model="previewContent"
          :autosize="{ minRows: 10, maxRows: 25 }"
          readonly
          class="preview-textarea"
        />
      </t-loading>
    </t-dialog>

    <!-- 变量管理对话框 -->
    <t-dialog
      v-model:visible="variablesVisible"
      header="变量管理"
      width="70%"
      :footer="false"
    >
      <VariablesManager @update="fetchVariables" />
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, reactive } from 'vue'
import { MessagePlugin, Tag, Switch } from 'tdesign-vue-next'
import { ProTable } from '@/components/ProTable'
import { promptTemplateApi, type PromptTemplate } from '@/api/promptTemplate'
import SectionsManager from './components/SectionsManager.vue'
import VariablesManager from './components/VariablesManager.vue'
import type { ProTableConfig } from '@/components/ProTable'

const tableRef = ref()
const templates = ref<PromptTemplate[]>([])

// 对话框状态
const sectionsVisible = ref(false)
const previewVisible = ref(false)
const variablesVisible = ref(false)
const previewLoading = ref(false)
const previewContent = ref('')
const currentTemplate = ref<PromptTemplate | null>(null)

// 人格选项
const personalityOptions = [
  { label: '默认人格', value: 'default' },
  { label: '活泼版', value: 'cheerful' },
  { label: '温柔版', value: 'calm' },
  { label: '吐槽版', value: 'sarcastic' },
]

// 表格配置 - 使用 reactive 使 data 响应式
const tableConfig = reactive<ProTableConfig>({
  cardTitle: 'Prompt模板管理',
  columns: [
    {
      colKey: 'name',
      title: '模板名称',
      width: 200,
      search: true,
      form: {
        component: 'input',
        rules: [{ required: true, message: '请输入模板名称' }],
      },
    },
    {
      colKey: 'description',
      title: '描述',
      ellipsis: true,
      form: {
        component: 'textarea',
      },
    },
    {
      colKey: 'personality_id',
      title: '关联人格',
      width: 120,
      valueType: 'text',
      form: {
        component: 'select',
        options: personalityOptions,
      },
    },
    {
      colKey: 'is_default',
      title: '默认',
      width: 80,
      align: 'center',
      render: (value) => {
        return value
          ? h(Tag, { theme: 'success', variant: 'light' }, () => '默认')
          : h(Tag, { theme: 'default', variant: 'light' }, () => '-')
      },
      form: {
        component: 'switch',
        defaultValue: false,
      },
    },
    {
      colKey: 'is_active',
      title: '启用',
      width: 80,
      align: 'center',
      render: (value, row: any) => {
        return h(Switch, {
          modelValue: value as boolean,
          onChange: (val) => handleToggleActive(row, val as boolean),
        })
      },
    },
    {
      colKey: 'sections',
      title: '区块数',
      width: 100,
      align: 'center',
      render: (_, row: any) => {
        return h(Tag, { theme: 'primary', variant: 'light' }, () => `${row.sections?.length || 0} 个区块`)
      },
    },
    {
      colKey: 'version',
      title: '版本',
      width: 80,
      align: 'center',
      render: (value) => {
        return h(Tag, { theme: 'warning', variant: 'light' }, () => `v${value}`)
      },
    },
  ],
  data: [],
  search: true,
  pagination: true,
  index: true,
  hover: true,
  toolbar: {
    create: { text: '新建模板', icon: 'add' },
    refresh: true,
    density: true,
    columnSetting: true,
  },
  operation: {
    edit: true,
    delete: true,
    width: 280,
    actions: [
      {
        key: 'sections',
        text: '区块',
        theme: 'primary',
        variant: 'text',
        onClick: (row: any) => {
          currentTemplate.value = row
          sectionsVisible.value = true
        },
      },
      {
        key: 'preview',
        text: '预览',
        theme: 'primary',
        variant: 'text',
        onClick: (row: any) => handlePreview(row),
      },
      {
        key: 'variables',
        text: '变量',
        theme: 'default',
        variant: 'text',
        onClick: () => {
          fetchVariables()
        },
      },
    ],
  },
})

onMounted(() => {
  fetchTemplates()
})

const fetchTemplates = async () => {
  try {
    const response = await promptTemplateApi.getTemplates()
    templates.value = response.data
    tableConfig.data = response.data
  } catch (error) {
    MessagePlugin.error('获取模板列表失败')
  }
}

const handleToggleActive = async (row: PromptTemplate, val: boolean) => {
  try {
    await promptTemplateApi.updateTemplate(row.id, { is_active: val })
    row.is_active = val
    MessagePlugin.success(val ? '已启用' : '已禁用')
  } catch (error) {
    MessagePlugin.error('操作失败')
  }
}

const handleCreate = () => {
}

const handleEdit = (row: any) => {
}

const handleDelete = async (row: any) => {
  try {
    await promptTemplateApi.deleteTemplate(row.id)
    MessagePlugin.success('删除成功')
    await fetchTemplates()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}

const handleSubmit = async (data: any, isEdit: boolean) => {
  try {
    if (isEdit) {
      await promptTemplateApi.updateTemplate(data.id, {
        name: data.name,
        description: data.description,
        is_default: data.is_default,
      })
      MessagePlugin.success('更新成功')
    } else {
      await promptTemplateApi.createTemplate({
        name: data.name,
        description: data.description,
        personality_id: data.personality_id || undefined,
        is_default: data.is_default,
      })
      MessagePlugin.success('创建成功')
    }
    await fetchTemplates()
  } catch (error) {
    MessagePlugin.error(isEdit ? '更新失败' : '创建失败')
  }
}

const handleSectionsUpdate = () => {
  fetchTemplates()
}

const handlePreview = async (row: PromptTemplate) => {
  previewVisible.value = true
  previewLoading.value = true
  try {
    const response = await promptTemplateApi.buildPrompt(row.id, {
      variables: {
        personality_name: '小花',
        speaking_style: '活泼开朗，喜欢开玩笑',
        communication_guidelines: '像朋友一样聊天，不要太过正式',
        forbidden_phrases: '不要说"作为AI"',
      },
    })
    previewContent.value = response.data.prompt
  } catch (error) {
    MessagePlugin.error('预览失败')
  } finally {
    previewLoading.value = false
  }
}

const variables = ref<any[]>([])

const fetchVariables = async () => {
  try {
    const response = await promptTemplateApi.getVariables()
    variables.value = response.data
  } catch (error) {
    MessagePlugin.error('获取变量列表失败')
  }
  variablesVisible.value = true
}
</script>

<style scoped>
.prompt-templates-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  padding: 16px;
}

.preview-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  background: #f8f9fa;
}
</style>
