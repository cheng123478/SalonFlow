import request from './request'

export function listOrders(params) {
  return request.get('/order', { params })
}

export function createOrder(data) {
  return request.post('/order', data)
}

export function updateOrder(id, data) {
  return request.put(`/order/${id}`, data)
}

export function deleteOrder(id) {
  return request.delete(`/order/${id}`)
}
