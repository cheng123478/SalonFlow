import request from './request'

export function listInventory(params) {
  return request.get('/inventory', { params })
}

export function listWarnings() {
  return request.get('/inventory/warnings')
}

export function listRecords(inventoryId) {
  return request.get('/inventory/records', { params: { inventory_id: inventoryId } })
}

export function createInventory(data) {
  return request.post('/inventory', data)
}

export function updateInventory(id, data) {
  return request.put(`/inventory/${id}`, data)
}

export function deleteInventory(id) {
  return request.delete(`/inventory/${id}`)
}

export function changeStock(id, data) {
  return request.post(`/inventory/${id}/stock`, data)
}
