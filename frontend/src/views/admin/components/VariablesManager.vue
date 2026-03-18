<template>
  <div class="variables-manager">
    <div class="variables-header">
      <t-button theme="primary" @click="handleCreate">
        <template #icon><t-icon name="add" /></template>
        添加变量
      </t-button>
    </div>

    <t-table
      :data="variables"
      :columns="columns"
      :loading="loading"
      row-key="id"
      hover
    >
      <template #var_type="{ row }">
        <t-tag :theme="getVarTypeTheme(row.var_type)" variant="light">
          {{ row.var_type }}
        </t-tag>
      </template>

      <template #is_required="{ row }">
        <t-tag v-if="row.is_required" theme="danger" variant="light">必需</t-tag>
        <t-tag v-else theme="default" variant="light">可选</t-tag>
      </template>

      <template #default_value="{ row }">
        <span v-if="row.default_value" class="default-value">{{ row.default_value }}</span>
        <span v-else class="no-value">-</span>
      </template>

      <template #operation="{ row }">
        <t-space>
          <t-button theme="primary" variant="text" size="small" @click="handleEdit(row)">
            编辑
          </t-button>
          <t-popconfirm
            content="确定要删除这个变量吗？"
            @confirm="handleDelete(row)"
          >
            <t-button theme="danger" variant="text" size="small">
              删除
            </t-button>
          </t-popconfirm>
        </t-space>
      </template>
    </t-table>

    <!-- 变量表单对话框 -->
    <t-dialog
      v-model:visible="formVisible"
      :header="isEditing ? '编辑变量' : '添加变量'"
      width="500px"
      :confirm-btn="{ content: '保存', loading: saving }"
      @confirm="handleSubmit"
    >
      <t-form :data="formData" :rules="formRules" ref="formRef">
        <t-form-item label="变量名" name="name">
          <t-input
            v-model="formData.name"
            placeholder="请输入变量名，如：personality_name"
            :disabled="isEditing"
          />
        </t-form-item>
        <t-form-item label="变量描述" name="description">
          <t-textarea v-model="formData.description" placeholder="请输入变量描述" :rows="2" />
        </t-form-item>
        <t-form-item label="变量类型" name="var_type">
          <t-select v-model="formData.var_type" placeholder="请选择变量类型">
            <t-option key="string" label="字符串" value="string" />
            <t-option key="text" label="文本" value="text" />
            <t-option key="int" label="整数" value="int" />
            <t-option key="float" label="浮点数" value="float" />
            <t-option key="boolean" label="布尔值" value="boolean" />
            <t-option key="json" label="JSON" value="json" />
          </t-select>
        </t-form-item>
        <t-form-item label="默认值" name="default_value">
          <t-textarea v-model="formData.default_value" placeholder="请输入默认值（可选）" :rows="2" />
        </t-form-item>
        <t-form-item label="示例值" name="example">
          <t-input v-model="formData.example" placeholder="请输入示例值（可选）" />
        </t-form-item>
        <t-form-item label="必需" name="is_required">
          <t-switch v-model="formData.is_required" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { promptTemplateApi, type PromptVariable } from '@/api/promptTemplate'

const emit = defineEmits<{
  update: []
}>()

const loading = ref(false)
const variables = ref<PromptVariable[]>([])

// 表格列定义
const columns = [
  { colKey: 'name', title: '变量名', width: 150 },
  { colKey: 'description', title: '描述', ellipsis: true },
  { colKey: 'var_type', title: '类型', width: 100 },
  { colKey: 'is_required', title: '必需', width: 80, align: 'center' },
  { colKey: 'default_value', title: '默认值',  width: 120, ellipsis: true },
  { colKey: 'example', title: '示例', ellipsis: true },
  { colKey: 'operation', title: '操作', width: 120, fixed: 'right' },
]

const getVarTypeTheme = (type: string) => {
  const themes: Record<string, string> = {
    string: 'primary',
    text: 'success',
    int: 'warning',
    float: 'warning',
    boolean: 'danger',
    json: 'default',
  }
  return themes[type] || 'default'
}

// 获取变量列表
const fetchVariables = async () => {
  loading.value = true
  try {
    const response = await promptTemplateApi.getVariables()
    variables.value = response.data
  } catch (error) {
    MessagePlugin.error('获取变量列表失败')
  } finally {
    loading.value = false
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
  description: '',
  var_type: 'string',
  default_value: '',
  is_required: true,
  example: '',
})

const formRules = {
  name: [
    { required: true, message: '请输入变量名', trigger: 'blur' },
    { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '变量名只能包含字母、数字和下划线，且不能以数字开头', trigger: 'blur' },
  ],
  description: [{ required: true, message: '请输入变量描述', trigger: 'blur' }],
  var_type: [{ required: true, message: '请选择变量类型', trigger: 'change' }],
}

const resetForm = () => {
  formData.value = {
    id: '',
    name: '',
    description: '',
    var_type: 'string',
    default_value: '',
    is_required: true,
    example: '',
  }
}

const handleCreate = () => {
  isEditing.value = false
  resetForm()
  formVisible.value = true
}

const handleEdit = (row: PromptVariable) => {
  isEditing.value = true
  formData.value = {
    id: row.id,
    name: row.name,
    description: row.description,
    var_type: row.var_type,
    default_value: row.default_value || '',
    is_required: row.is_required,
    example: row.example || '',
  }
  formVisible.value = true
}

const handleSubmit = async () => {
  const validateResult = await formRef.value?.validate()
  if (validateResult !== true) return

  saving.value = true
  try {
    if (isEditing.value) {
      await promptTemplateApi.updateVariable(formData.value.id, {
        description: formData.value.description,
        default_value: formData.value.default_value || undefined,
        is_required: formData.value.is_required,
        example: formData.value.example || undefined,
      })
      MessagePlugin.success('更新成功')
    } else {
      await promptTemplateApi.createVariable({
        name: formData.value.name,
        description: formData.value.description,
        var_type: formData.value.var_type,
        default_value: formData.value.default_value || undefined,
        is_required: formData.value.is_required,
        example: formData.value.example || undefined,
      })
      MessagePlugin.success('创建成功')
    }
    formVisible.value = false
    fetchVariables()
    emit('update')
  } catch (error) {
    MessagePlugin.error(isEditing.value ? '更新失败' : '创建失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row: PromptVariable) => {
  try {
    await promptTemplateApi.deleteVariable(row.id)
    MessagePlugin.success('删除成功')
    fetchVariables()
    emit('update')
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}

onMounted(() => {
  fetchVariables()
})
</script>

<style scoped>
.variables-manager {
  padding: 0;
}

.variables-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.default-value {
  color: #333;
}

.no-value {
  color: #999;
}
</style>
