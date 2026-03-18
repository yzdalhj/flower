<template>
  <div class="personality-view">
    <ProTable
      ref="tableRef"
      :config="tableConfig"
      @submit="handleSubmit"
      @delete="handleDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import ProTable from '@/components/ProTable/ProTable.vue'
import type { ProTableColumn, ProTableConfig } from '@/components/ProTable/types'
import { personalityApi } from '@/api/personality'

const tableRef = ref<InstanceType<typeof ProTable>>()

// 表格列配置
const columns: ProTableColumn[] = [
  {
    colKey: 'name',
    title: '人格名称',
    width: 150,
    search: true,
    form: {
      component: 'input',
      rules: [{ required: true, message: '请输入人格名称' }],
    },
  },
  {
    colKey: 'is_active',
    title: '状态',
    width: 100,
    form: {
      component: 'switch',
      defaultValue: true,
    },
  },
   {
    colKey: 'description',
    title: '描述',
    ellipsis: true,
    form: {
      span: 12,
      component: 'textarea',
    },
  },
  {
    colKey: 'is_system',
    title: '类型',
    width: 100,
  },
  {
    colKey: 'usage_count',
    title: '使用次数',
    width: 100,
  },
  {
    colKey: 'openness',
    title: '开放性',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'conscientiousness',
    title: '尽责性',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'extraversion',
    title: '外向性',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'agreeableness',
    title: '宜人性',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'neuroticism',
    title: '神经质',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'expressiveness',
    title: '表达丰富度',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'humor',
    title: '幽默程度',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'sarcasm',
    title: '吐槽倾向',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 30,
    },
  },
  {
    colKey: 'verbosity',
    title: '话痨程度',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'empathy',
    title: '共情深度',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 70,
    },
  },
  {
    colKey: 'warmth',
    title: '温暖度',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 70,
    },
  },
  {
    colKey: 'emotional_stability',
    title: '情绪稳定性',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 60,
    },
  },
  {
    colKey: 'assertiveness',
    title: '主动性',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 50,
    },
  },
  {
    colKey: 'casualness',
    title: '随意度',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 60,
    },
  },
  {
    colKey: 'formality',
    title: '正式程度',
    hideInTable: true,
    form: {
      component: 'number',
      defaultValue: 30,
    },
  },
]

// 表格配置
const tableConfig: ProTableConfig = {
  columns: columns,
  cardTitle: '人格引擎管理',
  toolbar: {
    create: { text: '创建人格', icon: 'add' },
    refresh: true,
    density: true,
    columnSetting: true,
  },
  formDialog: {
    width: '800px',
    top: '5vh',
  },
  request: async (params) => {
    const response = await personalityApi.getConfigs(params.filters?.is_active as boolean)
    return {
      data: response.configs,
      total: response.total,
    }
  },
}

// 提交表单
const handleSubmit = async (data: any, isEdit: boolean) => {
  const configData = {
    name: data.name,
    description: data.description,
    is_active: data.is_active,
    openness: data.openness,
    conscientiousness: data.conscientiousness,
    extraversion: data.extraversion,
    agreeableness: data.agreeableness,
    neuroticism: data.neuroticism,
    expressiveness: data.expressiveness,
    humor: data.humor,
    sarcasm: data.sarcasm,
    verbosity: data.verbosity,
    empathy: data.empathy,
    warmth: data.warmth,
    emotional_stability: data.emotional_stability,
    assertiveness: data.assertiveness,
    casualness: data.casualness,
    formality: data.formality,
  }

  if (isEdit) {
    await personalityApi.updateConfig(data.id, configData)
    MessagePlugin.success('人格配置已更新')
  } else {
    await personalityApi.createConfig(configData)
    MessagePlugin.success('人格配置已创建')
  }
  tableRef.value?.refresh()
}

// 删除
const handleDelete = async (row: any) => {
  await personalityApi.deleteConfig(row.id as string)
  MessagePlugin.success('人格配置已删除')
  tableRef.value?.refresh()
}
</script>

<style scoped>
.personality-view {
  padding: 24px;
}
</style>
