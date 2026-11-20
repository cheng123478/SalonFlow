<template>
  <div class="chat-panel">
    <div class="chat-toolbar">
      <span class="session-tag">{{ sessionId ? '会话进行中' : '新对话' }}</span>
      <button v-if="!hideNewButton" class="new-btn" :disabled="streaming" @click="newSession">＋ 新对话</button>
    </div>
    <div class="chat-body" ref="bodyRef">
      <div v-if="messages.length === 0" class="empty">
        你好，我是 SalonFlow 门店智能助手，可以帮你查询门店数据、管理订单、员工和顾客信息。
        你可以这样问我：
        - 查询今日预约列表
        - 查看项目库存预警
        - 查找顾客【张三】的档案与消费记录
        - 统计本周门店营收
      </div>

      <div v-for="(m, i) in messages" :key="i" class="msg-row" :class="m.role">
        <div v-if="m.role === 'assistant'" class="avatar-sm">🤖</div>
        <div class="bubble-col">
          <div v-if="m.role === 'assistant'" class="bubble">
            {{ m.content }}
            <div v-if="m.sources && m.sources.length" class="sources">
              <button class="sources-toggle" @click="toggleSources(i)">
                📚 参考来源（{{ m.sources.length }}）
              </button>
              <div v-if="m.showSources" class="sources-body">
                <div v-for="(s, j) in m.sources" :key="j" class="source-item">
                  <div class="source-query">{{ s.title }} · 匹配度 {{ s.score }}</div>
                  <pre class="source-result">{{ s.excerpt }}</pre>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="bubble">{{ m.content }}</div>

          <div v-if="m.pendingAction" class="confirm">
            <span class="tip">检测到写操作方案，是否执行？</span>
            <el-button type="primary" size="small" :loading="m.executing" @click="confirm(i)">
              确认执行
            </el-button>
            <el-button size="small" @click="dismiss(i)">取消</el-button>
          </div>
        </div>
      </div>

      <div v-if="typing" class="msg-row assistant">
        <div class="avatar-sm">🤖</div>
        <div class="bubble typing"><span></span><span></span><span></span></div>
      </div>
    </div>

    <el-dialog v-model="reserveVisible" title="快速预约" width="420px" append-to-body>
      <el-form :model="reserveForm" label-width="80px">
        <el-form-item label="技师">
          <el-select v-model="reserveForm.techId" placeholder="选择技师" filterable style="width: 100%">
            <el-option v-for="t in technicians" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker
            v-model="reserveForm.time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择预约时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="reserveForm.project" placeholder="选择项目" clearable style="width: 100%">
            <el-option v-for="p in PROJECTS" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="reserveForm.phone" placeholder="顾客手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reserveVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReserve">生成并发送</el-button>
      </template>
    </el-dialog>

    <div class="chat-footer">
      <div class="more-menu">
        <button class="more-btn" :class="{ open: menuOpen }" :disabled="streaming" @click="menuOpen = !menuOpen">+</button>
        <div v-if="menuOpen" class="menu-pop">
          <button class="menu-item" :disabled="streaming" @click="openReserve">
            <span class="menu-icon"><el-icon><Calendar /></el-icon></span>预约
          </button>
          <button class="menu-item" :disabled="streaming" @click="quickSend('查会员')">
            <span class="menu-icon"><el-icon><User /></el-icon></span>查会员
          </button>
          <button class="menu-item" :disabled="streaming" @click="quickSend('查库存')">
            <span class="menu-icon"><el-icon><Box /></el-icon></span>查库存
          </button>
          <button class="menu-item" :disabled="streaming" @click="quickSend('查今日预约')">
            <span class="menu-icon"><el-icon><Clock /></el-icon></span>今日预约
          </button>
        </div>
      </div>
      <input
        v-model="input"
        class="chat-input"
        type="text"
        placeholder="输入消息，回车发送"
        :disabled="streaming"
        @keyup.enter="send"
      />
      <button class="send-btn" :disabled="streaming || !input.trim()" @click="send">➤</button>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Calendar, User, Box, Clock } from '@element-plus/icons-vue'
import { chatStream, executeAction, listHistory } from '../api/agent'
import { listTechnicians } from '../api/technician'

const props = defineProps({
  sessionId: { type: String, default: null },
  hideNewButton: { type: Boolean, default: false },
  persistSession: { type: Boolean, default: false }
})

const SESSION_STORAGE_KEY = 'salonflow_chat_session_id'

const emit = defineEmits(['session-updated'])

const messages = ref([]) // 展示用：{ role, content, pendingAction, executing, sources, showSources }
const input = ref('')
const streaming = ref(false)
const typing = ref(false)
const bodyRef = ref()
const sessionId = ref(
  props.sessionId || (props.persistSession ? localStorage.getItem(SESSION_STORAGE_KEY) : null)
)

onMounted(async () => {
  if (!sessionId.value) return
  try {
    const res = await listHistory(sessionId.value)
    const rows = res.data || []
    messages.value = rows.map((r) => ({
      role: r.role,
      content: r.content,
      pendingAction: null,
      executing: false,
      sources: [],
      showSources: false
    }))
    scrollBottom()
  } catch (e) {
    // 加载历史失败不阻塞新对话
  }
})

function newSession() {
  if (streaming.value) return
  sessionId.value = null
  messages.value = []
  if (props.persistSession) localStorage.removeItem(SESSION_STORAGE_KEY)
}

// 快捷预约表单
const reserveVisible = ref(false)
const menuOpen = ref(false)
const technicians = ref([])
const reserveForm = reactive({ techId: null, time: '', project: '', phone: '' })
const PROJECTS = ['剪发', '烫发', '染发', '护理', '造型', '洗护']

async function loadTechnicians() {
  try {
    const res = await listTechnicians()
    technicians.value = res.data || []
  } catch (e) {
    // 拦截器已提示
  }
}

function openReserve() {
  if (streaming.value) return
  menuOpen.value = false
  reserveForm.techId = null
  reserveForm.time = ''
  reserveForm.project = ''
  reserveForm.phone = ''
  loadTechnicians()
  reserveVisible.value = true
}

function submitReserve() {
  const tech = technicians.value.find((t) => t.id === reserveForm.techId)
  if (!tech) {
    ElMessage.warning('请选择技师')
    return
  }
  if (!reserveForm.time) {
    ElMessage.warning('请选择预约时间')
    return
  }
  if (!reserveForm.phone) {
    ElMessage.warning('请填写顾客手机号')
    return
  }
  const parts = [
    `技师 ${tech.name}(ID:${tech.id})`,
    `时间 ${reserveForm.time}`,
    `项目 ${reserveForm.project || '未定'}`,
    `手机号 ${reserveForm.phone}`
  ]
  reserveVisible.value = false
  input.value = `预约：${parts.join('，')}`
  send()
}

function quickSend(text) {
  if (streaming.value) return
  menuOpen.value = false
  input.value = text
  send()
}

async function send() {
  const text = input.value.trim()
  if (!text || streaming.value) return
  input.value = ''

  messages.value.push({ role: 'user', content: text })
  streaming.value = true
  typing.value = true
  scrollBottom()

  let answer = ''
  let pendingAction = null
  let assistantMsg = null

  // 首个 token 到达时才创建助手气泡，避免流式期间出现空白气泡 + 打字动画两个机器人
  const ensureAssistant = () => {
    if (!assistantMsg) {
      assistantMsg = {
        role: 'assistant',
        content: '',
        pendingAction: null,
        executing: false,
        sources: [],
        showSources: false,
      }
      messages.value.push(assistantMsg)
      typing.value = false
    }
    return assistantMsg
  }

  try {
    const res = await chatStream(sessionId.value, text)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.message || `请求失败(${res.status})`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')

      let sepIdx
      while ((sepIdx = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, sepIdx)
        buffer = buffer.slice(sepIdx + 2)

        // 按 SSE 规范拼接多条 data: 行（值为多行时后端会拆成多行 data:）
        let data = ''
        for (const line of block.split('\n')) {
          if (line.startsWith('data:')) {
            data += (data ? '\n' : '') + line.slice(5).replace(/^ /, '')
          }
        }
        if (!data) continue

        let evt
        try {
          evt = JSON.parse(data)
        } catch {
          continue
        }

        if (evt.type === 'token') {
          answer += evt.content
          ensureAssistant().content = answer
          scrollBottom()
        } else if (evt.type === 'done') {
          answer = evt.answer || answer
          const h = ensureAssistant()
          h.content = answer
          pendingAction = evt.pending_action || null
          h.sources = evt.sources || []
          if (evt.session_id) {
            sessionId.value = evt.session_id
            if (props.persistSession) localStorage.setItem(SESSION_STORAGE_KEY, evt.session_id)
            emit('session-updated', evt.session_id)
          }
        } else if (evt.type === 'error') {
          ElMessage.error(evt.message)
        }
      }
    }
  } catch (e) {
    ElMessage.error(e.message || '请求失败')
    const h = ensureAssistant()
    if (!h.content) h.content = '（请求失败，请重试）'
  } finally {
    streaming.value = false
    typing.value = false
    if (assistantMsg) assistantMsg.pendingAction = pendingAction
    scrollBottom()
  }
}

async function confirm(i) {
  const msg = messages.value[i]
  const { action, params } = msg.pendingAction
  msg.executing = true
  try {
    await executeAction(action, params)
    ElMessage.success('已执行')
    msg.pendingAction = null
  } catch (e) {
    // 拦截器已提示具体错误
  } finally {
    msg.executing = false
  }
}

function dismiss(i) {
  messages.value[i].pendingAction = null
}

function toggleSources(i) {
  messages.value[i].showSources = !messages.value[i].showSources
}

function scrollBottom() {
  nextTick(() => {
    if (bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  })
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

/* 顶部工具栏 */
.chat-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.session-tag {
  font-size: 12px;
  color: #909399;
}
.new-btn {
  border: none;
  background: none;
  color: #64b5f6;
  font-size: 13px;
  cursor: pointer;
  padding: 2px 4px;
}
.new-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 消息区 */
.chat-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
  background: #e3f2fd;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty {
  color: #9bb7d4;
  text-align: center;
  margin-top: 80px;
  line-height: 2;
}

.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.msg-row.user {
  justify-content: flex-end;
}

.avatar-sm {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.bubble-col {
  max-width: 78%;
  display: flex;
  flex-direction: column;
}
.msg-row.user .bubble-col {
  align-items: flex-end;
}

.bubble {
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-row.assistant .bubble {
  background: #fff;
  color: #333;
  border: 1px solid #eee;
  border-top-left-radius: 4px;
}
.msg-row.user .bubble {
  background: #64b5f6;
  color: #fff;
  border-top-right-radius: 4px;
}

/* 参考来源（在助手气泡内部） */
.sources {
  margin-top: 8px;
  border-top: 1px dashed #e0e0e0;
  padding-top: 6px;
}
.sources-toggle {
  border: none;
  background: none;
  color: #64b5f6;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}
.sources-body {
  margin-top: 6px;
}
.source-item {
  margin-bottom: 6px;
}
.source-query {
  font-size: 12px;
  color: #999;
  margin-bottom: 2px;
}
.source-result {
  margin: 0;
  padding: 6px 8px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #555;
  max-height: 100px;
  overflow-y: auto;
}

/* 正在输入动画 */
.typing {
  display: flex;
  gap: 4px;
  align-items: center;
  min-width: 48px;
  min-height: 12px;
  padding-top: 8px;
}
.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #bbb;
  animation: dots 1.2s infinite;
}
.typing span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes dots {
  0%, 80%, 100% { opacity: 0.25; }
  40% { opacity: 1; }
}

/* 写操作二次确认 */
.confirm {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #fdf6ec;
  border: 1px solid #f5dab1;
  border-radius: 6px;
}
.confirm .tip {
  font-size: 13px;
  color: #e6a23c;
  margin-right: 4px;
}

/* 更多快捷指令 */
.more-menu {
  position: relative;
  flex-shrink: 0;
}
.more-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid #dcdfe6;
  background: #fff;
  color: #606266;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s, border-color 0.2s;
}
.more-btn:hover,
.more-btn.open {
  color: #409eff;
  border-color: #409eff;
}
.menu-pop {
  position: absolute;
  bottom: calc(100% + 10px);
  left: 0;
  display: grid;
  grid-template-columns: repeat(2, auto);
  gap: 4px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 8px 24px rgba(31, 45, 61, 0.12);
  z-index: 10;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  background: transparent;
  font-size: 13px;
  color: #1f2d3d;
  cursor: pointer;
  white-space: nowrap;
}
.menu-item:hover {
  background: #f0f5ff;
}
.menu-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.menu-icon {
  color: #409eff;
  font-size: 16px;
  display: inline-flex;
}

/* 输入区 */
.chat-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border-top: 1px solid #eee;
}
.chat-input {
  flex: 1;
  padding: 9px 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 14px;
  outline: none;
}
.chat-input:focus {
  border-color: #64b5f6;
}
.send-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #64b5f6;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>