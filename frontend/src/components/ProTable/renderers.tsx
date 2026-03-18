import { h, type VNode } from 'vue'
import { Tag, Switch, Link, Image, Space, Button } from 'tdesign-vue-next'
import type { ProTableData, ProTableValueType, ValueTypeConfig, ProTableColumn } from './types'

// 日期格式化（不依赖 dayjs）
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const formatDate = (value: any, format = 'YYYY-MM-DD HH:mm:ss') => {
  if (!value) return '-'
  const date = new Date(value)
  if (isNaN(date.getTime())) return '-'

  const pad = (n: number) => n.toString().padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

// 值类型渲染器
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const valueTypeRenderers: Record<ProTableValueType, (value: any, record: ProTableData, config?: ValueTypeConfig) => VNode | string> = {
  // 纯文本
  text: (value) => {
    if (value === null || value === undefined) return '-'
    return String(value)
  },

  // 数字

  number: (value) => {
    if (value === null || value === undefined) return '-'
    const num = Number(value)
    if (isNaN(num)) return '-'
    // 可以添加千分位格式化等
    return num.toLocaleString()
  },

  // 日期
  date: (value, _, config) => {
    return formatDate(value, config?.format || 'YYYY-MM-DD')
  },

  // 日期时间
  datetime: (value, _, config) => {
    return formatDate(value, config?.format || 'YYYY-MM-DD HH:mm:ss')
  },

  // 时间
  time: (value, _, config) => {
    return formatDate(value, config?.format || 'HH:mm:ss')
  },

  // 选择器

  select: (value, _, config) => {
    if (value === null || value === undefined) return '-'
    const option = config?.options?.find(opt => opt.value === value)
    if (!option) return String(value)

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const theme = (option.color as any) || 'default'
    return h(Tag, {
      theme,
      variant: 'light',
    }, () => option.label)
  },

  // 标签

  tag: (value, _, config) => {
    if (value === null || value === undefined) return '-'

    // 支持数组形式
    const values = Array.isArray(value) ? value : [value]

    return h(Space, { size: 'small' }, () =>
      values.map((val, idx) => {
        const option = config?.options?.find(opt => opt.value === val)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const theme = (option?.color as any) || 'primary'
        return h(Tag, {
          key: idx,
          theme,
          variant: 'light',
        }, () => option?.label || String(val))
      })
    )
  },

  // 开关
  switch: (value) => {
    return h(Switch, {
      modelValue: Boolean(value),
      disabled: true,
      size: 'small',
    })
  },

  // 图片
  image: (value) => {
    if (!value) return '-'
    return h(Image, {
      src: String(value),
      fit: 'cover',
      style: { width: '60px', height: '60px', borderRadius: '4px' },
      overlayTrigger: 'hover',
    }, {
      overlayContent: () => h('div', { style: { padding: '8px' } }, '查看大图'),
    })
  },

  // 链接
  link: (value) => {
    if (!value) return '-'
    return h(Link, {
      href: String(value),
      target: '_blank',
      theme: 'primary',
    }, () => '点击访问')
  },

  // 操作列（占位，实际在组件中处理）
  operation: () => '-',

  // 自定义（占位，使用 render 函数）
  custom: () => '-',
}

// 渲染单元格

export const renderCell = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any,
  record: ProTableData,
  index: number,
  column: ProTableColumn
): VNode | string => {
  // 优先使用自定义 render
  if (column.render) {
    return column.render(value, record, index) as any
  }

  // 使用 valueType
  if (column.valueType) {
    const config: ValueTypeConfig = typeof column.valueType === 'string'
      ? { type: column.valueType }
      : column.valueType

    const renderer = valueTypeRenderers[config.type]
    if (renderer) {
      return renderer(value, record, config)
    }
  }

  // 默认文本
  if (value === null || value === undefined) return '-'
  return String(value)
}

// 渲染搜索组件

export const renderSearchComponent = (
  column: ProTableColumn,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  modelValue: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onChange: (val: any) => void
): VNode | null => {
  if (!column.search) return null

  const searchConfig = typeof column.search === 'boolean' ? {} : column.search
  const component = searchConfig.component || 'input'
  const placeholder = searchConfig.placeholder || `请输入${column.title}`

  switch (component) {
    case 'input':
      return h('t-input', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        clearable: true,
        ...searchConfig.attrs,
      })

    case 'select':
      return h('t-select', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        clearable: true,
        options: searchConfig.options || [],
        ...searchConfig.attrs,
      })

    case 'date-picker':
      return h('t-date-picker', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        clearable: true,
        ...searchConfig.attrs,
      })

    case 'date-range':
      return h('t-date-range-picker', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder: ['开始日期', '结束日期'],
        clearable: true,
        ...searchConfig.attrs,
      })

    case 'number':
      return h('t-input-number', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        ...searchConfig.attrs,
      })

    default:
      return null
  }
}

// 渲染表单组件

export const renderFormComponent = (
  column: ProTableColumn,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  modelValue: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onChange: (val: any) => void
): VNode | null => {
  if (!column.form) return null

  const formConfig = typeof column.form === 'boolean' ? {} : column.form
  const component = formConfig.component || 'input'
  const placeholder = formConfig.placeholder || `请输入${column.title}`

  switch (component) {
    case 'input':
      return h('t-input', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        clearable: true,
        ...formConfig.attrs,
      })

    case 'textarea':
      return h('t-textarea', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        clearable: true,
        rows: 4,
        ...formConfig.attrs,
      })

    case 'select':
      return h('t-select', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        clearable: true,
        options: formConfig.options || [],
        ...formConfig.attrs,
      })

    case 'radio':
      return h('t-radio-group', {
        modelValue,
        'onUpdate:modelValue': onChange,
        options: formConfig.options || [],
        ...formConfig.attrs,
      })

    case 'checkbox':
      return h('t-checkbox-group', {
        modelValue,
        'onUpdate:modelValue': onChange,
        options: formConfig.options || [],
        ...formConfig.attrs,
      })

    case 'switch':
      return h('t-switch', {
        modelValue,
        'onUpdate:modelValue': onChange,
        ...formConfig.attrs,
      })

    case 'number':
      return h('t-input-number', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        ...formConfig.attrs,
      })

    case 'date-picker':
      return h('t-date-picker', {
        modelValue,
        'onUpdate:modelValue': onChange,
        placeholder,
        clearable: true,
        ...formConfig.attrs,
      })

    default:
      return null
  }
}

// 获取表单校验规则
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const getFormRules = (columns: ProTableColumn[]): Record<string, any[]> => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rules: Record<string, any[]> = {}

  columns.forEach(column => {
    if (column.form && typeof column.form === 'object' && column.form.rules) {
      rules[column.colKey] = column.form.rules
    }
  })

  return rules
}

// 获取表单默认值
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const getFormDefaultValues = (columns: ProTableColumn[]): Record<string, any> => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const values: Record<string, any> = {}

  columns.forEach(column => {
    if (column.form && typeof column.form === 'object' && column.form.defaultValue !== undefined) {
      values[column.colKey] = column.form.defaultValue
    }
  })

  return values
}
