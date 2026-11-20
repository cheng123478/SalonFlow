import request from './request'

// 流式聊天：直接返回 fetch 的 Response，由调用方按 SSE 解析
// （用 fetch 而非 EventSource，是为了能携带 Authorization 请求头）
export function chatStream(sessionId, message) {
  const token = localStorage.getItem('token')
  return fetch('/api/agent/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ session_id: sessionId, message })
  })
}

// 执行已确认的写操作（二次确认后落库）
export function executeAction(action, params) {
  return request.post('/agent/execute', { action, params })
}

// 对话历史：会话列表
export function listSessions() {
  return request.get('/agent/sessions')
}

// 对话历史：指定会话的消息记录
export function listHistory(sessionId) {
  return request.get(`/agent/sessions/${sessionId}/messages`)
}

// 删除指定会话（含其历史记录）
export function deleteSession(sessionId) {
  return request.delete(`/agent/sessions/${sessionId}`)
}