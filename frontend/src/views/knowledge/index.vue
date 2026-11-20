<template>
  <div>
    <el-card shadow="never">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="例如：染发后护理" maxlength="200" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="粘贴门店知识内容，或点下方「上传文档」读取文件"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="onSubmit">
            {{ editingTitle ? '保存修改' : '入库' }}
          </el-button>
          <el-button v-if="editingTitle" @click="cancelEdit">取消编辑</el-button>
          <el-button @click="onUpload">上传文档（txt/md）</el-button>
          <input
            ref="fileRef"
            type="file"
            accept=".txt,.md,.csv,.json"
            style="display: none"
            @change="onFileChange"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <div class="toolbar">
        <span class="list-title">已有知识（{{ list.length }} 篇）</span>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="chunks" label="分块数" width="100" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="onEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ingestKnowledge, listKnowledge, getKnowledge, updateKnowledge, deleteKnowledge } from '../../api/knowledge'

const form = reactive({ title: '', content: '' })
const list = ref([])
const loading = ref(false)
const submitting = ref(false)
const editingTitle = ref('')
const fileRef = ref()

async function load() {
  loading.value = true
  try {
    const res = await listKnowledge()
    list.value = res.data || []
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  submitting.value = true
  try {
    if (editingTitle.value) {
      await updateKnowledge({
        old_title: editingTitle.value,
        title: form.title.trim(),
        content: form.content
      })
      ElMessage.success('更新成功')
    } else {
      const res = await ingestKnowledge({ title: form.title.trim(), content: form.content })
      ElMessage.success(`入库成功，共 ${res.data.chunks} 块`)
    }
    form.title = ''
    form.content = ''
    editingTitle.value = ''
    load()
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    submitting.value = false
  }
}

async function onEdit(row) {
  try {
    const res = await getKnowledge(row.title)
    form.title = res.data.title
    form.content = res.data.content
    editingTitle.value = row.title
  } catch (e) {
    // 拦截器已提示错误
  }
}

function cancelEdit() {
  editingTitle.value = ''
  form.title = ''
  form.content = ''
}

function onUpload() {
  fileRef.value.click()
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    form.content = String(reader.result || '')
    if (!form.title.trim()) {
      form.title = file.name.replace(/\.[^.]+$/, '')
    }
    ElMessage.success('已读取文件内容')
  }
  reader.readAsText(file, 'utf-8')
  e.target.value = ''
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除知识「${row.title}」？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteKnowledge(row.title)
    ElMessage.success('删除成功')
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.list-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
</style>