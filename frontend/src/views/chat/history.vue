<template>
  <div class="history-page">
    <!-- 左：会话列表 -->
    <div class="left">
      <div class="toolbar">
        <span class="title">会话</span>
        <div class="toolbar-actions">
          <el-button size="small" type="primary" @click="newSession">新建对话</el-button>
          <el-button size="small" @click="load">刷新</el-button>
        </div>
      </div>
      <div class="session-list" v-loading="loading">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: current && current.id === s.id }"
          @click="select(s)"
        >
          <div class="s-head">
            <div class="s-title">{{ s.title }}</div>
            <button class="del-btn" title="删除会话" @click.stop="remove(s)">✕</button>
          </div>
          <div class="s-preview">{{ s.last_message || '（无内容）' }}</div>
          <div class="s-meta">{{ s.message_count }} 条 · {{ formatTime(s.updated_at) }}</div>
        </div>
        <el-empty v-if="!loading && sessions.length === 0" description="暂无对话记录" />
      </div>
    </div>

    <!-- 右：对话框（直接续聊） -->
    <div class="right">
      <ChatPanel
        :key="chatKey"
        :session-id="activeKey"
        :hide-new-button="true"
        @session-updated="load"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ChatPanel from '../../components/ChatPanel.vue'
import { deleteSession, listSessions } from '../../api/agent'

const sessions = ref([])
const current = ref(null) // 左侧当前选中的会话对象
const activeKey = ref(null) // 右侧 ChatPanel 绑定的 session_key（null = 新对话）
const chatKey = ref('init') // 用于切换会话时强制重建 ChatPanel
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await listSessions()
    sessions.value = res.data || []
    // 若当前选中的会话已被删除，则清空右侧
    if (current.value && !sessions.value.some((s) => s.id === current.value.id)) {
      resetChat()
    }
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}

function select(s) {
  current.value = s
  activeKey.value = s.session_key
  chatKey.value = `s-${s.id}`
}

function newSession() {
  resetChat()
}

function resetChat() {
  current.value = null
  activeKey.value = null
  chatKey.value = `new-${Date.now()}`
}

function formatTime(t) {
  if (!t) return ''
  return String(t).replace('T', ' ').slice(0, 16)
}

async function remove(s) {
  try {
    await ElMessageBox.confirm(`确认删除会话「${s.title}」及其全部历史？`, '提示', {
      type: 'warning'
    })
  } catch (e) {
    return
  }
  try {
    await deleteSession(s.session_key)
    ElMessage.success('删除成功')
    if (current.value && current.value.id === s.id) {
      resetChat()
    }
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

onMounted(load)
</script>

<style scoped>
.history-page {
  height: 100%;
  display: flex;
  gap: 16px;
}

.left {
  width: 300px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.toolbar-actions {
  display: flex;
  gap: 8px;
}

.session-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background 0.15s;
}
.session-item:hover {
  background: #f5f7fa;
}
.session-item.active {
  background: #e3f2fd;
}

.s-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.s-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.del-btn {
  border: none;
  background: none;
  color: #c0c4cc;
  font-size: 13px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
  visibility: hidden;
}
.session-item:hover .del-btn {
  visibility: visible;
}
.del-btn:hover {
  color: #f56c6c;
}

.s-preview {
  font-size: 13px;
  color: #909399;
  margin: 4px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.s-meta {
  font-size: 12px;
  color: #c0c4cc;
}

.right {
  flex: 1;
  min-width: 0;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>