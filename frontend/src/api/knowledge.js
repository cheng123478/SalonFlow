import request from './request'

export function ingestKnowledge(data) {
  return request.post('/knowledge/ingest', data)
}

export function listKnowledge() {
  return request.get('/knowledge/list')
}

export function getKnowledge(title) {
  return request.get('/knowledge/detail', { params: { title } })
}

export function updateKnowledge(data) {
  return request.post('/knowledge/update', data)
}

export function deleteKnowledge(title) {
  return request.post('/knowledge/delete', { title })
}