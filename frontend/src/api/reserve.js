import request from './request'

export function listReserves(params) {
  return request.get('/reserve', { params })
}

export function createReserve(data) {
  return request.post('/reserve', data)
}

export function updateReserve(id, data) {
  return request.put(`/reserve/${id}`, data)
}

export function deleteReserve(id) {
  return request.delete(`/reserve/${id}`)
}
