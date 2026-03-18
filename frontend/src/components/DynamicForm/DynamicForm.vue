<template>
  <div class="dynamic-form">
    <!-- 操作按钮 - 右上角 -->
    <div v-if="config.showActions !== false" class="form-actions">
      <t-space>
        <t-button
          v-if="config.showReset !== false"
          theme="default"
          @click="handleReset"
        >
          <template #icon><t-icon name="refresh" /></template>
          {{ config.resetText || '重置' }}
        </t-button>
        <t-button
          theme="primary"
          :loading="submitting"
          @click="handleSubmitClick"
        >
          <template #icon><t-icon name="save" /></template>
          {{ config.submitText || '保存' }}
        </t-button>
      </t-space>
    </div>

    <t-form
      ref="formRef"
      :data="formData"
      :label-width="config.labelWidth || 150"
      :rules="formRules"
      @submit="handleSubmit"
    >
      <template v-for="group in groupedFields" :key="group.key">
        <t-divider v-if="group.title">{{ group.title }}</t-divider>

        <div class="form-row">
          <div
            v-for="field in group.fields"
            :key="field.key"
            class="form-col"
            :style="{ width: getColWidth(field.span) }"
          >
            <t-form-item
              :label="field.label"
              :name="field.key"
              :help="field.help"
            >
              <!-- 输入框 -->
              <t-input
                v-if="field.type === 'input' || field.type === 'password'"
                v-model="formData[field.key]"
                :type="field.type"
                :placeholder="field.placeholder"
                :disabled="field.disabled"
                :clearable="field.clearable !== false"
              />

              <!-- 数字输入 -->
              <t-input-number
                v-else-if="field.type === 'number'"
                v-model="formData[field.key]"
                :min="field.min"
                :max="field.max"
                :step="field.step || 1"
                :placeholder="field.placeholder"
                :disabled="field.disabled"
              />

              <!-- 开关 -->
              <t-switch
                v-else-if="field.type === 'switch'"
                v-model="formData[field.key]"
                :disabled="field.disabled"
              />

              <!-- 选择器 -->
              <t-select
                v-else-if="field.type === 'select'"
                v-model="formData[field.key]"
                :options="field.options"
                :placeholder="field.placeholder"
                :disabled="field.disabled"
                :clearable="field.clearable !== false"
              />

              <!-- 文本域 -->
              <t-textarea
                v-else-if="field.type === 'textarea'"
                v-model="formData[field.key]"
                :placeholder="field.placeholder"
                :disabled="field.disabled"
                :rows="field.rows || 4"
              />

              <!-- 单选框 -->
              <t-radio-group
                v-else-if="field.type === 'radio'"
                v-model="formData[field.key]"
                :options="field.options"
                :disabled="field.disabled"
              />

              <!-- 自定义组件 -->
              <component
                v-else-if="field.type === 'component' && field.component"
                :is="field.component.component"
                v-model="formData[field.key]"
                v-bind="field.component.props"
                v-on="field.component.events || {}"
              />

              <!-- 自定义插槽 -->
              <slot
                v-else-if="field.type === 'custom'"
                :name="field.key"
                :field="field"
                :value="formData[field.key]"
                :on-change="(val: unknown) => handleFieldChange(field.key, val)"
              />
            </t-form-item>
          </div>
        </div>
      </template>
    </t-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, h } from 'vue'
import { MessagePlugin, Icon as TIcon } from 'tdesign-vue-next'
import type { FormInstanceFunctions } from 'tdesign-vue-next'
import type { FormConfig, FormField, FormFieldGroup } from './types'

const props = defineProps<{
  config: FormConfig
  modelValue?: Record<string, unknown>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, unknown>): void
  (e: 'submit', data: Record<string, unknown>): void
  (e: 'reset'): void
  (e: 'change', key: string, value: unknown): void
}>()

const formRef = ref<FormInstanceFunctions>()
const formData = ref<Record<string, unknown>>({})
const submitting = ref(false)
const originalData = ref<Record<string, unknown>>({})

// 计算列宽度
const getColWidth = (span?: number): string => {
  if (!span || span >= 24) return '100%'
  return `${(span / 24) * 100}%`
}

// 按分组组织字段
const groupedFields = computed<FormFieldGroup[]>(() => {
  const groups: FormFieldGroup[] = []
  const fields = props.config.fields || []

  // 按 group 分组
  const groupMap = new Map<string, FormField[]>()
  const ungrouped: FormField[] = []

  fields.forEach(field => {
    if (field.group) {
      if (!groupMap.has(field.group)) {
        groupMap.set(field.group, [])
      }
      groupMap.get(field.group)!.push(field)
    } else {
      ungrouped.push(field)
    }
  })

  // 添加有分组的字段
  props.config.groups?.forEach(groupConfig => {
    const groupFields = groupMap.get(groupConfig.key) || []
    if (groupFields.length > 0) {
      groups.push({
        key: groupConfig.key,
        title: groupConfig.title,
        fields: groupFields,
      })
    }
  })

  // 添加未分组的字段
  if (ungrouped.length > 0) {
    groups.push({
      key: 'default',
      title: '',
      fields: ungrouped,
    })
  }

  return groups
})

// 表单校验规则
const formRules = computed(() => {
  const rules: Record<string, unknown[]> = {}

  props.config.fields?.forEach(field => {
    if (field.rules && field.rules.length > 0) {
      rules[field.key] = field.rules
    }
  })

  return rules
})

// 初始化表单数据
const initFormData = () => {
  const data: Record<string, unknown> = {}

  props.config.fields?.forEach(field => {
    if (field.defaultValue !== undefined) {
      data[field.key] = field.defaultValue
    } else {
      // 根据类型设置默认值
      switch (field.type) {
        case 'switch':
          data[field.key] = false
          break
        case 'number':
          data[field.key] = field.min || 0
          break
        case 'select':
        case 'radio':
          data[field.key] = field.options?.[0]?.value
          break
        default:
          data[field.key] = ''
      }
    }
  })

  formData.value = { ...data, ...props.modelValue }
  originalData.value = JSON.parse(JSON.stringify(formData.value))
}

// 字段值变化
const handleFieldChange = (key: string, value: unknown) => {
  formData.value[key] = value
  emit('change', key, value)
  emit('update:modelValue', { ...formData.value })
}

// 点击提交按钮
const handleSubmitClick = async () => {
  const valid = await formRef.value?.validate()
  if (valid !== true) return

  submitting.value = true
  try {
    emit('submit', { ...formData.value })
    originalData.value = JSON.parse(JSON.stringify(formData.value))
  } finally {
    submitting.value = false
  }
}

// 表单提交事件（回车触发）
const handleSubmit = () => {
  handleSubmitClick()
}

// 重置表单
const handleReset = () => {
  formData.value = JSON.parse(JSON.stringify(originalData.value))
  formRef.value?.reset()
  emit('reset')
}

// 设置表单数据
const setFormData = (data: Record<string, unknown>) => {
  formData.value = { ...formData.value, ...data }
  originalData.value = JSON.parse(JSON.stringify(formData.value))
}

// 获取表单数据
const getFormData = () => {
  return { ...formData.value }
}

// 校验表单
const validate = async () => {
  return await formRef.value?.validate()
}

// 暴露方法
defineExpose({
  setFormData,
  getFormData,
  validate,
  reset: handleReset,
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    formData.value = { ...formData.value, ...newVal }
  }
}, { deep: true })

// 初始化
onMounted(() => {
  initFormData()
})
</script>

<style scoped>
.dynamic-form {
  width: 100%;
  position: relative;
}

.form-actions {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 10;
  padding: 8px 0;
  background: transparent;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  row-gap: 8px;
}

.form-col {
  padding-right: 16px;
  box-sizing: border-box;
}

.form-col:last-child {
  padding-right: 0;
}
:deep(.t-form__item) {
  margin-bottom: 20px;
  min-height: 45px;
}

:deep(.t-form__item__help) {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.5;
  min-height: 12px;
}

:deep(.t-form__status) {
  margin-top: 4px;
}

:deep(.t-input),
:deep(.t-input-number),
:deep(.t-select),
:deep(.t-textarea) {
  width: 100%;
}

:deep(.t-input-number) {
  width: 100%;
}

:deep(.t-divider) {
  margin: 24px 0 16px;
}

:deep(.t-divider__text) {
  font-weight: 600;
  color: var(--td-text-color-primary);
}
</style>
