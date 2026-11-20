<template>
  <div class="agent-widget" ref="widgetEl" :style="widgetStyle">
    <!-- 悬浮按钮 -->
    <button v-if="!open" class="fab" title="SalonFlow 私人小助理（可拖拽）" @pointerdown="startDrag" @click="onClickFab">
      <span class="fab-emoji">🤖</span>
    </button>

    <!-- 聊天窗口（v-show 保持挂载，切换页面不丢对话） -->
    <transition name="chat-pop">
      <div v-show="open" class="chat-window">
        <div class="chat-header">
          <div class="chat-header-left">
            <div class="avatar">🤖</div>
            <div class="chat-header-info">
              <div class="chat-name">SalonFlow 小助理</div>
              <div class="chat-status"><span class="dot"></span>在线</div>
            </div>
          </div>
          <div class="chat-header-right">
            <button class="close-btn" title="收起" @click="open = false">✕</button>
          </div>
        </div>
        <div class="panel-wrap">
          <ChatPanel persist-session />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import ChatPanel from './ChatPanel.vue'

const open = ref(false)
const widgetEl = ref(null)
const pos = ref(null) // { left, top }，null 表示使用默认右下角定位

const widgetStyle = computed(() => {
  if (!pos.value) return {}
  return { left: pos.value.left + 'px', top: pos.value.top + 'px', right: 'auto', bottom: 'auto' }
})

let moved = false
let startX = 0
let startY = 0
let originLeft = 0
let originTop = 0
const FAB_SIZE = 60

function startDrag(e) {
  if (e.button != null && e.button !== 0) return
  moved = false
  startX = e.clientX
  startY = e.clientY
  const rect = widgetEl.value.getBoundingClientRect()
  originLeft = rect.left
  originTop = rect.top
  window.addEventListener('pointermove', onDrag)
  window.addEventListener('pointerup', endDrag)
  e.preventDefault()
}

function onDrag(e) {
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) moved = true
  const left = Math.min(Math.max(originLeft + dx, 0), window.innerWidth - FAB_SIZE)
  const top = Math.min(Math.max(originTop + dy, 0), window.innerHeight - FAB_SIZE)
  pos.value = { left, top }
}

function endDrag() {
  window.removeEventListener('pointermove', onDrag)
  window.removeEventListener('pointerup', endDrag)
}

function onClickFab() {
  if (moved) return
  open.value = true
}
</script>

<style scoped>
.agent-widget {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 2000;
  width: 60px;
  height: 60px;
}

/* 悬浮按钮 */
.fab {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: #64b5f6;
  color: #fff;
  cursor: grab;
  touch-action: none;
  user-select: none;
  box-shadow: 0 6px 18px rgba(100, 181, 246, 0.45);
  transition: transform 0.2s, box-shadow 0.2s;
}
.fab:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 22px rgba(100, 181, 246, 0.55);
}
.fab-emoji {
  font-size: 30px;
  line-height: 1;
  display: block;
}

/* 聊天窗口 */
.chat-window {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 400px;
  max-width: calc(100vw - 40px);
  height: 560px;
  max-height: calc(100vh - 120px);
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.16);
  border: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #64b5f6;
  color: #fff;
  flex-shrink: 0;
}
.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #fff;
  color: #64b5f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.chat-name {
  font-size: 15px;
  font-weight: 700;
}
.chat-status {
  font-size: 12px;
  opacity: 0.9;
  display: flex;
  align-items: center;
  gap: 4px;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2ed573;
  display: inline-block;
}
.chat-header-right {
  display: flex;
  align-items: center;
}
.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  opacity: 0.9;
  padding: 4px;
  line-height: 1;
}
.close-btn:hover {
  opacity: 1;
}

.panel-wrap {
  flex: 1;
  min-height: 0;
}

/* 弹出动画 */
.chat-pop-enter-active,
.chat-pop-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.chat-pop-enter-from,
.chat-pop-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}
</style>