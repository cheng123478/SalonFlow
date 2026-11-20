<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索姓名 / 擅长项目" clearable style="width: 240px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openForm()">新增技师</el-button>
      </div>

      <div v-loading="loading" class="card-grid">
        <div v-for="row in list" :key="row.id" class="tech-card">
          <div class="card-head">
            <div class="avatar-wrap">
              <img v-if="row.avatar" :src="row.avatar" class="avatar-img" alt="" />
              <div v-else class="avatar">{{ (row.name || '?').charAt(0) }}</div>
              <span class="presence" :class="row.is_on_duty ? 'on' : 'off'" />
            </div>
            <div class="head-meta">
              <div class="name-line">
                <span class="name">{{ row.name }}</span>
                <span class="status" :class="row.is_on_duty ? 'on' : 'off'">{{ row.is_on_duty ? '在岗' : '离岗' }}</span>
              </div>
              <div class="skills-tags">
                <template v-if="skillList(row.skills).length">
                  <span v-for="(s, i) in skillList(row.skills)" :key="i" class="skill-tag">{{ s }}</span>
                </template>
                <span v-else class="skills-empty">未填写擅长项目</span>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div class="info-row">
              <span class="info-icon"><el-icon><Calendar /></el-icon></span>
              <span class="label">休息日</span>
              <span class="value" :title="row.rest_days || '无'">{{ row.rest_days || '无' }}</span>
            </div>
            <div class="info-row">
              <span class="info-icon"><el-icon><Clock /></el-icon></span>
              <span class="label">排班</span>
              <span class="value" :title="row.schedule_config || '未配置'">{{ row.schedule_config || '未配置' }}</span>
            </div>
          </div>

          <div class="card-foot">
            <el-button link type="primary" :icon="EditPen" @click="openForm(row)">编辑</el-button>
            <span class="foot-divider" />
            <el-button link type="danger" :icon="Delete" @click="onDelete(row)">删除</el-button>
          </div>
        </div>

        <el-empty v-if="!loading && list.length === 0" description="暂无技师" class="empty" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑技师' : '新增技师'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="头像">
          <el-upload :show-file-list="false" :http-request="handleAvatarUpload" accept="image/*">
            <img v-if="form.avatar" :src="form.avatar" class="avatar-preview" alt="" />
            <div v-else class="avatar-preview avatar-uploader">+</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="擅长项目">
          <el-input v-model="form.skills" placeholder="如：剪发,烫染,造型（逗号分隔）" />
        </el-form-item>
        <el-form-item label="休息日">
          <el-input v-model="form.rest_days" placeholder="如：周一,周二" />
        </el-form-item>
        <el-form-item label="排班配置">
          <el-input v-model="form.schedule_config" type="textarea" placeholder="如：工作日 10:00-20:00" />
        </el-form-item>
        <el-form-item label="是否在岗">
          <el-switch v-model="form.is_on_duty" active-text="在岗" inactive-text="离岗" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Clock, EditPen, Delete } from '@element-plus/icons-vue'
import { listTechnicians, createTechnician, updateTechnician, deleteTechnician, uploadAvatar } from '../../api/technician'

const list = ref([])
const loading = ref(false)
const keyword = ref('')
const dialogVisible = ref(false)
const formRef = ref()
const emptyForm = { id: null, name: '', skills: '', rest_days: '', schedule_config: '', avatar: '', is_on_duty: true }
const form = reactive({ ...emptyForm })

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

function skillList(str) {
  return (str || '').split(/[,，]/).map((s) => s.trim()).filter(Boolean)
}

async function load() {
  loading.value = true
  try {
    const res = await listTechnicians({ keyword: keyword.value || undefined })
    list.value = res.data
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}

function openForm(row) {
  Object.assign(form, row ? row : emptyForm)
  dialogVisible.value = true
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (form.id) {
      await updateTechnician(form.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createTechnician({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

async function handleAvatarUpload(options) {
  try {
    const res = await uploadAvatar(options.file)
    form.avatar = res.data.url
    ElMessage.success('头像已上传')
    options.onSuccess(res)
  } catch (e) {
    options.onError(e)
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除技师「${row.name}」？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteTechnician(row.id)
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
  gap: 12px;
  margin-bottom: 20px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.tech-card {
  position: relative;
  border: 1px solid #ebeef5;
  border-radius: 18px;
  padding: 28px;
  background: #fff;
  transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.25s ease;
}

.tech-card:hover {
  border-color: #c6e2ff;
  box-shadow: 0 10px 28px rgba(31, 45, 61, 0.08);
  transform: translateY(-4px);
}

.card-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.avatar,
.avatar-img {
  width: 84px;
  height: 84px;
  border-radius: 50%;
}

.avatar {
  background: #ecf5ff;
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
  font-weight: 600;
}

.avatar-img {
  object-fit: cover;
  border: 1px solid #ebeef5;
}

.presence {
  position: absolute;
  right: 1px;
  bottom: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid #fff;
}

.presence.on {
  background: #67c23a;
}

.presence.off {
  background: #c0c4cc;
}

.head-meta {
  min-width: 0;
  flex: 1;
}

.name {
  font-size: 21px;
  font-weight: 700;
  color: #1f2d3d;
  letter-spacing: 0.3px;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 500;
  flex-shrink: 0;
}

.status.on {
  color: #67c23a;
  background: #f0f9eb;
}

.status.off {
  color: #909399;
  background: #f4f4f5;
}

.skills-tags {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-tag {
  font-size: 13px;
  color: #409eff;
  background: #ecf5ff;
  padding: 4px 12px;
  border-radius: 999px;
  line-height: 1.4;
}

.skills-empty {
  font-size: 13px;
  color: #c0c4cc;
}

.card-body {
  margin-top: 18px;
  padding: 16px 18px;
  background: #fafbfc;
  border-radius: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  padding: 5px 0;
}

.info-icon {
  color: #a8abb2;
  font-size: 16px;
  flex-shrink: 0;
  display: inline-flex;
}

.info-row .label {
  color: #909399;
  flex-shrink: 0;
}

.info-row .value {
  color: #606266;
  font-weight: 500;
  margin-left: auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid #f2f6fc;
}

.foot-divider {
  width: 1px;
  height: 14px;
  background: #e4e7ed;
}

.empty {
  grid-column: 1 / -1;
}

.avatar-preview {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-uploader {
  border: 1px dashed #dcdfe6;
  color: #c0c4cc;
  font-size: 28px;
  cursor: pointer;
}

.avatar-uploader:hover {
  border-color: #409eff;
  color: #409eff;
}
</style>
