<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索物料名称" clearable style="width: 240px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openForm()">新增物料</el-button>
        <el-button @click="loadWarnings">低库存预警</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="name" label="物料名称" />
        <el-table-column prop="quantity" label="库存数量" width="110" />
        <el-table-column prop="threshold" label="安全阈值" width="110" />
        <el-table-column prop="unit" label="单位" width="90" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.low_stock ? 'danger' : 'success'">{{ row.low_stock ? '库存不足' : '正常' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" @click="openStock(row)">出入库</el-button>
            <el-button link type="primary" @click="openRecords(row)">流水</el-button>
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增 / 编辑物料 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑物料' : '新增物料'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.quantity" :min="0" />
        </el-form-item>
        <el-form-item label="安全阈值">
          <el-input-number v-model="form.threshold" :min="0" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" placeholder="如：瓶 / 盒 / ml" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 出入库 -->
    <el-dialog v-model="stockVisible" title="出入库" width="420px">
      <el-form label-width="80px">
        <el-form-item label="物料">{{ current.name }}</el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="stockForm.change_type">
            <el-radio value="in">入库</el-radio>
            <el-radio value="out">出库</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="stockForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="stockForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockVisible = false">取消</el-button>
        <el-button type="primary" @click="onStock">确认</el-button>
      </template>
    </el-dialog>

    <!-- 出入库流水 -->
    <el-dialog v-model="recordsVisible" title="出入库流水" width="600px">
      <el-table :data="records" border stripe>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">{{ row.change_type === 'in' ? '入库' : '出库' }}</template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="90" />
        <el-table-column prop="remark" label="备注" />
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listInventory,
  listWarnings,
  listRecords,
  createInventory,
  updateInventory,
  deleteInventory,
  changeStock
} from '../../api/inventory'

const list = ref([])
const records = ref([])
const loading = ref(false)
const keyword = ref('')
const dialogVisible = ref(false)
const stockVisible = ref(false)
const recordsVisible = ref(false)
const formRef = ref()
const current = ref({})
const emptyForm = { id: null, name: '', quantity: 0, threshold: 10, unit: '' }
const form = reactive({ ...emptyForm })
const stockForm = reactive({ change_type: 'in', quantity: 1, remark: '' })

const rules = {
  name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }]
}

function fmtDateTime(val) {
  return val ? String(val).replace('T', ' ').slice(0, 19) : ''
}

async function load() {
  loading.value = true
  try {
    const res = await listInventory({ keyword: keyword.value || undefined })
    list.value = res.data
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}

async function loadWarnings() {
  try {
    const res = await listWarnings()
    if (res.data.length === 0) {
      ElMessage.success('没有低库存物料')
    } else {
      ElMessage.warning(`有 ${res.data.length} 个物料库存不足`)
      list.value = res.data
    }
  } catch (e) {
    // 拦截器已提示错误
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
      await updateInventory(form.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createInventory({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

function openStock(row) {
  current.value = row
  Object.assign(stockForm, { change_type: 'in', quantity: 1, remark: '' })
  stockVisible.value = true
}

async function onStock() {
  try {
    await changeStock(current.value.id, { ...stockForm })
    ElMessage.success('出入库成功')
    stockVisible.value = false
    load()
  } catch (e) {
    // 拦截器已提示错误
  }
}

async function openRecords(row) {
  try {
    const res = await listRecords(row.id)
    records.value = res.data
    recordsVisible.value = true
  } catch (e) {
    // 拦截器已提示错误
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除物料「${row.name}」？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteInventory(row.id)
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
