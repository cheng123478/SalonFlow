<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索手机号 / 项目" clearable style="width: 220px" @keyup.enter="load" />
        <el-select v-model="filterPayStatus" placeholder="支付状态" clearable style="width: 130px" @change="load">
          <el-option v-for="o in payStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openForm()">新增订单</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="技师" width="90">
          <template #default="{ row }">{{ techName(row.technician_id) }}</template>
        </el-table-column>
        <el-table-column prop="project" label="项目" />
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }">¥{{ Number(row.amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="支付状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.pay_status === 'paid' ? 'success' : 'warning'">
              {{ row.pay_status === 'paid' ? '已支付' : '未支付' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="服务时间" width="160">
          <template #default="{ row }">{{ fmtDateTime(row.order_time) }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑订单' : '新增订单'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="技师" prop="technician_id">
          <el-select v-model="form.technician_id" placeholder="选择技师" style="width: 100%">
            <el-option v-for="t in technicians" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-input v-model="form.project" placeholder="如：剪发 / 烫染" />
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number v-model="form.amount" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="支付状态">
          <el-select v-model="form.pay_status" style="width: 100%">
            <el-option v-for="o in payStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务时间" prop="order_time">
          <el-date-picker v-model="form.order_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" />
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
import { listOrders, createOrder, updateOrder, deleteOrder } from '../../api/order'
import { listTechnicians } from '../../api/technician'

const list = ref([])
const technicians = ref([])
const loading = ref(false)
const keyword = ref('')
const filterPayStatus = ref('')
const dialogVisible = ref(false)
const formRef = ref()
const emptyForm = { id: null, phone: '', technician_id: null, project: '', amount: 0, pay_status: 'unpaid', order_time: '', remark: '' }
const form = reactive({ ...emptyForm })

const payStatusOptions = [
  { value: 'unpaid', label: '未支付' },
  { value: 'paid', label: '已支付' }
]

const rules = {
  technician_id: [{ required: true, message: '请选择技师', trigger: 'change' }],
  order_time: [{ required: true, message: '请选择服务时间', trigger: 'change' }]
}

function techName(id) {
  const t = technicians.value.find((x) => x.id === id)
  return t ? t.name : id
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
    const res = await listOrders({
      keyword: keyword.value || undefined,
      pay_status: filterPayStatus.value || undefined
    })
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
    form.order_time = row.order_time ? String(row.order_time).slice(0, 19) : ''
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
      await updateOrder(form.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createOrder({ ...form })
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
    await ElMessageBox.confirm(`确认删除订单（${row.phone || '未填手机号'} / ${row.project || '未填项目'}）？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteOrder(row.id)
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
