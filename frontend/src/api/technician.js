import request from './request'

export function listTechnicians(params) {
  return request.get('/technician', { params })
}

export function createTechnician(data) {
  return request.post('/technician', data)
}

export function updateTechnician(id, data) {
  return request.put(`/technician/${id}`, data)
}

export function deleteTechnician(id) {
  return request.delete(`/technician/${id}`)
}

export function uploadAvatar(file) {
  const form = new FormData()
  form.append('file', file)
  return request.post('/upload/avatar', form)
}
