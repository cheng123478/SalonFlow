<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索姓名 / 手机号" clearable style="width: 240px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openForm()">新增会员</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="balance" label="储值余额" width="110" />
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="hair_remark" label="发质备注" />
        <el-table-column label="上次烫染" width="120">
          <template #default="{ row }">{{ fmtDate(row.last_dye_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑会员' : '新增会员'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="储值余额">
          <el-input-number v-model="form.balance" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="发质备注">
          <el-input v-model="form.hair_remark" />
        </el-form-item>
        <el-form-item label="上次烫染">
          <el-date-picker v-model="form.last_dye_time" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" />
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
import { listMembers, createMember, updateMember, deleteMember } from '../../api/member'

const list = ref([])
const loading = ref(false)
const keyword = ref('')
const dialogVisible = ref(false)
const formRef = ref()
const emptyForm = { id: null, phone: '', name: '', balance: 0, hair_remark: '', last_dye_time: null, remark: '' }
const form = reactive({ ...emptyForm })

const rules = {
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }]
}

function fmtDate(val) {
  return val ? String(val).slice(0, 10) : ''
}

async function load() {
  loading.value = true
  try {
    const res = await listMembers({ keyword: keyword.value || undefined })
    list.value = res.data
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}

function openForm(row) {
  if (row) {
    Object.assign(form, row)
    form.last_dye_time = row.last_dye_time ? String(row.last_dye_time).slice(0, 10) : null
  } else {
    Object.assign(form, emptyForm)
  }
  dialogVisible.value = true
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (form.id) {
      await updateMember(form.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createMember({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除会员「${row.name || row.phone}」？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteMember(row.id)
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
  margin-bottom: 16px;
}
</style>
