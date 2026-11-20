import request from './request'

export function listMembers(params) {
  return request.get('/member', { params })
}

export function createMember(data) {
  return request.post('/member', data)
}

export function updateMember(id, data) {
  return request.put(`/member/${id}`, data)
}

export function deleteMember(id) {
  return request.delete(`/member/${id}`)
}
