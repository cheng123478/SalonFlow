import request from './request'

export function getOverview() {
  return request.get('/report/overview')
}

export function getReserveStats() {
  return request.get('/report/reserve-stats')
}

export function getRevenue() {
  return request.get('/report/revenue')
}

const FILENAMES = {
  members: 'members.xlsx',
  reserves: 'reserves.xlsx',
  inventory: 'inventory.xlsx',
  orders: 'orders.xlsx'
}

// 导出走原生 fetch（带 Authorization），读 blob 触发下载；
// 不能走 axios 拦截器，因为导出返回二进制而非 {code, message, data}
export async function exportExcel(type) {
  const token = localStorage.getItem('token')
  const res = await fetch(`/api/report/export/${type}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message || err.detail || `导出失败(${res.status})`)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = FILENAMES[type] || `${type}.xlsx`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
