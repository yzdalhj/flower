<template>
  <div class="sections-manager">
    <div class="sections-header">
      <t-button theme="primary" @click="handleCreate">
        <template #icon><t-icon name="add" /></template>
        添加区块
      </t-button>
      <t-button theme="default" @click="handleSort" :disabled="!isOrderChanged">
        <template #icon><t-icon name="order-adjustment" /></template>
        保存排序
      </t-button>
    </div>

    <t-table
      :data="localSections"
      :columns="columns"
      row-key="id"
      hover
      drag-sort
      @drag-sort="handleDragSort"
    >
      <template #section_type="{ row }">
        <t-tag :theme="getSectionTypeTheme(row.section_type)" variant="light">
          {{ getSectionTypeLabel(row.section_type) }}
        </t-tag>
      </template>

      <template #is_active="{ row }">
        <t-switch
          :value="row.is_active"
          @change="(val: boolean) => handleToggleActive(row, val)"
        />
      </template>

      <template #content="{ row }">
        <div class="content-preview">{{ row.content.substring(0, 50) }}...</div>
      </template>

      <template #operation="{ row }">
        <t-space>
          <t-button theme="primary" variant="text" size="small" @click="handleEdit(row)">
            编辑
          </t-button>
          <t-popconfirm
            content="确定要删除这个区块吗？"
            @confirm="handleDelete(row)"
          >
            <t-button theme="danger" variant="text" size="small">
              删除
            </t-button>
          </t-popconfirm>
        </t-space>
      </template>
    </t-table>

    <!-- 区块表单对话框 -->
    <t-dialog
      v-model:visible="formVisible"
      :header="isEditing ? '编辑区块' : '添加区块'"
      width="600px"
      :confirm-btn="{ content: '保存', loading: saving }"
      @confirm="handleSubmit"
    >
      <t-form :data="formData" :rules="formRules" ref="formRef">
        <t-form-item label="区块名称" name="name">
          <t-input v-model="formData.name" placeholder="请输入区块名称" />
        </t-form-item>
        <t-form-item label="区块类型" name="section_type">
          <t-select v-model="formData.section_type" placeholder="请选择区块类型">
            <t-option key="identity" label="身份定义" value="identity" />
            <t-option key="style" label="说话风格" value="style" />
            <t-option key="guidelines" label="沟通指南" value="guidelines" />
            <t-option key="forbidden" label="禁止行为" value="forbidden" />
            <t-option key="examples" label="示例" value="examples" />
            <t-option key="custom" label="自定义" value="custom" />
          </t-select>
        </t-form-item>
        <t-form-item label="区块标题" name="title">
          <t-input v-model="formData.title" placeholder="请输入区块标题（可选）" />
        </t-form-item>
        <t-form-item label="区块内容" name="content">
          <t-textarea
            v-model="formData.content"
            placeholder="请输入区块内容，支持 {variable} 格式的变量"
            :rows="8"
          />
        </t-form-item>
        <t-form-item label="启用" name="is_active">
          <t-switch v-model="formData.is_active" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { promptTemplateApi, type PromptSection } from '@/api/promptTemplate'

const props = defineProps<{
  templateId: string
  sections: PromptSection[]
}>()

const emit = defineEmits<{
  update: []
}>()

const localSections = ref<PromptSection[]>([])
const isOrderChanged = ref(false)

// 同步props到本地数据
watch(() => props.sections, (newSections) => {
  localSections.value = [...newSections].sort((a, b) => a.sort_order - b.sort_order)
}, { immediate: true })

// 表格列定义
const columns = [
  { colKey: 'drag', width: 40, align: 'center' },
  { colKey: 'name', title: '区块名称', width: 150 },
  { colKey: 'section_type', title: '类型', width: 100 },
  { colKey: 'title', title: '标题', width: 150 },
  { colKey: 'content', title: '内容预览', ellipsis: true },
  { colKey: 'is_active', title: '启用', width: 80, align: 'center' },
  { colKey: 'operation', title: '操作', width: 120, fixed: 'right' },
]

const getSectionTypeTheme = (type: string) => {
  const themes: Record<string, string> = {
    identity: 'primary',
    style: 'success',
    guidelines: 'warning',
    forbidden: 'danger',
    examples: 'default',
    custom: 'default',
  }
  return themes[type] || 'default'
}

const getSectionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    identity: '身份',
    style: '风格',
    guidelines: '指南',
    forbidden: '禁止',
    examples: '示例',
    custom: '自定义',
  }
  return labels[type] || type
}

// 拖拽排序
const handleDragSort = ({ newData }: { newData: PromptSection[] }) => {
  localSections.value = newData.map((item, index) => ({
    ...item,
    sort_order: index,
  }))
  isOrderChanged.value = true
}

// 保存排序
const handleSort = async () => {
  try {
    const sectionOrders = localSections.value.map((section, index) => ({
      section_id: section.id,
      sort_order: index,
    }))
    await promptTemplateApi.reorderSections(props.templateId, { section_orders: sectionOrders })
    MessagePlugin.success('排序已保存')
    isOrderChanged.value = false
    emit('update')
  } catch (error) {
    MessagePlugin.error('保存排序失败')
  }
}

// 表单相关
const formVisible = ref(false)
const formRef = ref()
const saving = ref(false)
const isEditing = ref(false)
const formData = ref({
  id: '',
  name: '',
  section_type: 'custom',
  title: '',
  content: '',
  is_active: true,
})

const formRules = {
  name: [{ required: true, message: '请输入区块名称', trigger: 'blur' }],
  section_type: [{ required: true, message: '请选择区块类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入区块内容', trigger: 'blur' }],
}

const resetForm = () => {
  formData.value = {
    id: '',
    name: '',
    section_type: 'custom',
    title: '',
    content: '',
    is_active: true,
  }
}

const handleCreate = () => {
  isEditing.value = false
  resetForm()
  formVisible.value = true
}

const handleEdit = (row: PromptSection) => {
  isEditing.value = true
  formData.value = {
    id: row.id,
    name: row.name,
    section_type: row.section_type,
    title: row.title || '',
    content: row.content,
    is_active: row.is_active,
  }
  formVisible.value = true
}

const handleSubmit = async () => {
  const validateResult = await formRef.value?.validate()
  if (validateResult !== true) return

  saving.value = true
  try {
    if (isEditing.value) {
      await promptTemplateApi.updateSection(formData.value.id, {
        name: formData.value.name,
        title: formData.value.title,
        content: formData.value.content,
        is_active: formData.value.is_active,
      })
      MessagePlugin.success('更新成功')
    } else {
      await promptTemplateApi.addSection(props.templateId, {
        name: formData.value.name,
        section_type: formData.value.section_type,
        title: formData.value.title,
        content: formData.value.content,
        is_active: formData.value.is_active,
      })
      MessagePlugin.success('添加成功')
    }
    formVisible.value = false
    emit('update')
  } catch (error) {
    MessagePlugin.error(isEditing.value ? '更新失败' : '添加失败')
  } finally {
    saving.value = false
  }
}

const handleToggleActive = async (row: PromptSection, val: boolean) => {
  try {
    await promptTemplateApi.updateSection(row.id, { is_active: val })
    row.is_active = val
    MessagePlugin.success(val ? '已启用' : '已禁用')
  } catch (error) {
    MessagePlugin.error('操作失败')
  }
}

const handleDelete = async (row: PromptSection) => {
  try {
    await promptTemplateApi.deleteSection(row.id)
    MessagePlugin.success('删除成功')
    emit('update')
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}
</script>

<style scoped>
.sections-manager {
  padding: 0;
}

.sections-header {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.content-preview {
  color: #666;
  font-size: 13px;
}
</style>
