<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px" @change="load">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openForm()">新增预约</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column label="技师" width="100">
          <template #default="{ row }">{{ techName(row.technician_id) }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="顾客手机号" width="140" />
        <el-table-column label="预约时间" width="170">
          <template #default="{ row }">{{ fmtDateTime(row.reserve_time) }}</template>
        </el-table-column>
        <el-table-column prop="project" label="项目" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑预约' : '新增预约'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="技师" prop="technician_id">
          <el-select v-model="form.technician_id" placeholder="选择技师" style="width: 100%">
            <el-option v-for="t in technicians" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="预约时间" prop="reserve_time">
          <el-date-picker v-model="form.reserve_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="项目">
          <el-input v-model="form.project" placeholder="如：剪发 / 烫染" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
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
import { listReserves, createReserve, updateReserve, deleteReserve } from '../../api/reserve'
import { listTechnicians } from '../../api/technician'

const list = ref([])
const technicians = ref([])
const loading = ref(false)
const filterStatus = ref('')
const dialogVisible = ref(false)
const formRef = ref()
const emptyForm = { id: null, technician_id: null, phone: '', reserve_time: '', project: '', status: 'pending' }
const form = reactive({ ...emptyForm })

const statusOptions = [
  { value: 'pending', label: '待确认' },
  { value: 'confirmed', label: '已确认' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' }
]

const rules = {
  technician_id: [{ required: true, message: '请选择技师', trigger: 'change' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  reserve_time: [{ required: true, message: '请选择预约时间', trigger: 'change' }]
}

function techName(id) {
  const t = technicians.value.find((x) => x.id === id)
  return t ? t.name : id
}
function statusLabel(s) {
  return statusOptions.find((o) => o.value === s)?.label || s
}
function statusType(s) {
  return { pending: 'warning', confirmed: 'success', completed: 'info', cancelled: 'danger' }[s] || 'info'
}
function fmtDateTime(val) {
  return val ? String(val).replace('T', ' ').slice(0, 16) : ''
}

async function loadTechs() {
  try {
    const res = await listTechnicians()
    technicians.value = res.data
  } catch (e) {
    // 拦截器已提示错误
  }
}

async function load() {
  loading.value = true
  try {
    const res = await listReserves({ status: filterStatus.value || undefined })
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
    form.reserve_time = row.reserve_time ? String(row.reserve_time).slice(0, 19) : ''
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
      await updateReserve(form.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createReserve({ ...form })
      ElMessage.success('预约成功')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm('确认删除该预约？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteReserve(row.id)
    ElMessage.success('删除成功')
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

onMounted(() => {
  loadTechs()
  load()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
