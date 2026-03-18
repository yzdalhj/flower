<template>
  <div class="users-view">
    <div class="users-layout">
      <!-- 左侧账号树 -->
      <aside class="account-tree">
        <div class="tree-header">
          <h3>账号列表</h3>
        </div>
        <div class="tree-content">
          <div
            v-for="account in accountTree"
            :key="account.id"
            class="account-item"
            :class="{ active: selectedAccountId === account.id }"
            @click="selectAccount(account)"
          >
            <div class="account-icon">
              {{ account.platform === 'wechat' ? '💬' : '📱' }}
            </div>
            <div class="account-info">
              <div class="account-name">{{ account.name }}</div>
              <div class="account-meta">
                <t-tag size="small" :theme="account.status === 'running' ? 'success' : 'default'">
                  {{ account.status === 'running' ? '运行中' : '已停止' }}
                </t-tag>
                <span class="user-count">{{ account.user_count }} 用户</span>
              </div>
            </div>
          </div>
          <div v-if="accountTree.length === 0" class="empty-tree">
            <t-empty description="暂无账号" />
          </div>
        </div>
      </aside>

      <!-- 右侧用户列表 -->
      <main class="users-content">
        <ProTable
          ref="proTableRef"
          :config="tableConfig"
          @submit="handleSubmit"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import ProTable from '@/components/ProTable/ProTable.vue'
import { userApi } from '@/api'
import type { User, AccountTreeItem } from '@/api/user'
import type { ProTableConfig, ProTableData } from '@/components/ProTable/types'

const proTableRef = ref<InstanceType<typeof ProTable>>()
const accountTree = ref<AccountTreeItem[]>([])
const selectedAccountId = ref<string>('')

// 加载账号树
const loadAccountTree = async () => {
  try {
    accountTree.value = await userApi.getAccountTree()
  } catch (error) {
    console.error('加载账号树失败:', error)
  }
}

// 选择账号
const selectAccount = (account: AccountTreeItem) => {
  selectedAccountId.value = account.id
  proTableRef.value?.refresh()
}

// 表格配置
const tableConfig = computed<ProTableConfig>(() => ({
  cardTitle: '用户管理',
  rowKey: 'id',
  stripe: true,
  hover: true,
  pagination: true,
  search: true,
  toolbar: {
    create: false,
    refresh: true,
    density: true,
    columnSetting: true,
  },
  operation: {
    view: true,
    edit: true,
    delete: true,
    width: 180,
  },
  descriptions: {
    column: 2,
  },
  request: async (params: { current: number; pageSize: number; filters: Record<string, unknown> }) => {
    const response = await userApi.getUsers({
      page: params.current,
      pageSize: params.pageSize,
      account_id: selectedAccountId.value || undefined,
      platform_type: (params.filters.platform_type as string) || undefined,
      relationship_stage: (params.filters.relationship_stage as string) || undefined,
    })
    return {
      data: response.data,
      total: response.total,
    }
  },
  columns: [
    {
      colKey: 'nickname',
      title: '昵称',
      width: 150,
      ellipsis: true,
      render: (value: string | null) => value || '未设置昵称',
      form: {
        component: 'input',
        placeholder: '请输入昵称',
      },
    },
    {
      colKey: 'platform_type',
      title: '平台',
      width: 100,
      search: {
        component: 'select',
        placeholder: '请选择平台',
        options: [
          { label: '微信', value: 'wechat' },
          { label: 'QQ', value: 'qq' },
          { label: 'Web', value: 'web' },
        ],
      },
      render: (value: string) => {
        const platformMap: Record<string, string> = {
          wechat: '微信',
          qq: 'QQ',
          web: 'Web',
        }
        return platformMap[value] || value
      },
      hideInDescriptions: true,
    },
    {
      colKey: 'account_name',
      title: '所属账号',
      width: 150,
      ellipsis: true,
      hideInDescriptions: true,
    },
    {
      colKey: 'relationship_stage',
      title: '关系阶段',
      width: 120,
      search: {
        component: 'select',
        placeholder: '请选择关系阶段',
        options: [
          { label: '陌生人', value: 'stranger' },
          { label: '熟人', value: 'acquaintance' },
          { label: '朋友', value: 'friend' },
          { label: '亲密', value: 'close' },
        ],
      },
      render: (value: string) => {
        const stageMap: Record<string, string> = {
          stranger: '陌生人',
          acquaintance: '熟人',
          friend: '朋友',
          close: '亲密',
        }
        return stageMap[value] || value
      },
      form: {
        component: 'select',
        placeholder: '请选择关系阶段',
        options: [
          { label: '陌生人', value: 'stranger' },
          { label: '熟人', value: 'acquaintance' },
          { label: '朋友', value: 'friend' },
          { label: '亲密', value: 'close' },
        ],
      },
    },
    {
      colKey: 'trust_score',
      title: '信任度',
      width: 150,
      render: (value: number) => {
        return h('t-progress', {
          percentage: value,
          size: 'small',
          color: value >= 70 ? '#00a870' : value >= 40 ? '#ffcc00' : '#e34d59',
        })
      },
      form: {
        component: 'number',
        placeholder: '请输入信任度(0-100)',
      },
    },
    {
      colKey: 'intimacy_score',
      title: '亲密度',
      width: 150,
      render: (value: number) => {
        return h('t-progress', {
          percentage: value,
          size: 'small',
          color: value >= 70 ? '#ff6b9d' : value >= 40 ? '#ffcc00' : '#e34d59',
        })
      },
      form: {
        component: 'number',
        placeholder: '请输入亲密度(0-100)',
      },
    },
    {
      colKey: 'total_messages',
      title: '消息数',
      width: 100,
      align: 'center',
      hideInDescriptions: true,
    },
    {
      colKey: 'last_interaction_at',
      title: '最后交互',
      width: 180,
      render: (value: string | null) => value ? formatTime(value) : '-',
      hideInDescriptions: true,
    },
    {
      colKey: 'platform_user_id',
      title: '平台用户ID',
      width: 200,
      ellipsis: true,
      hideInTable: true,
    },
    {
      colKey: 'created_at',
      title: '创建时间',
      width: 180,
      render: (value: string) => formatTime(value),
      hideInTable: true,
    },
  ],
}))

// 查看用户详情 - 使用 ProTable 自带的抽屉
const handleView = (row: ProTableData) => {
  // ProTable 会自动打开详情抽屉
  console.log('查看用户:', row)
}

// 删除用户
const handleDelete = (row: ProTableData) => {
  const userRow = row as unknown as User
  const confirmDialog = DialogPlugin.confirm({
    header: '确认删除',
    body: `确定要删除用户 "${userRow.nickname || userRow.id}" 吗？此操作不可恢复。`,
    confirmBtn: {
      content: '删除',
      theme: 'danger',
    },
    onConfirm: async () => {
      try {
        await userApi.deleteUser(userRow.id)
        MessagePlugin.success('删除成功')
        proTableRef.value?.refresh()
        confirmDialog.destroy()
      } catch (error) {
        MessagePlugin.error('删除失败')
        console.error(error)
      }
    },
  })
}

// 提交编辑
const handleSubmit = async (data: ProTableData, isEdit: boolean) => {
  if (!isEdit) return

  try {
    await userApi.updateUser(data.id as string, {
      nickname: data.nickname as string,
      relationship_stage: data.relationship_stage as string,
      trust_score: data.trust_score as number,
      intimacy_score: data.intimacy_score as number,
    })
    MessagePlugin.success('保存成功')
    proTableRef.value?.refresh()
  } catch (error) {
    MessagePlugin.error('保存失败')
    console.error(error)
    throw error
  }
}

// 格式化时间
const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAccountTree()
})
</script>

<style scoped>
.users-view {
  height: 100%;
  padding: 16px;
}

.users-layout {
  display: flex;
  height: 100%;
  gap: 16px;
}

/* 左侧账号树 */
.account-tree {
  width: 280px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.tree-header {
  padding: 16px;
  border-bottom: 1px solid #e7e7e7;
}

.tree-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.account-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.account-item:hover {
  background: #f5f7fa;
}

.account-item.active {
  background: #e7f3ff;
}

.account-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 8px;
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.account-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #999;
}

.user-count {
  color: #666;
}

.empty-tree {
  padding: 40px 20px;
}

/* 右侧用户列表 */
.users-content {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
</style>
