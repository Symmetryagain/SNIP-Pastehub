// src/api/posts.js
import request from '../utils/request'

export function getPosts(skip = 0, limit = 50) {
  return request.get(`/posts/?skip=${skip}&limit=${limit}`)
}

export function getPostById(id) {
  return request.get(`/posts/${id}`)
}

export function createPost(data) {
  return request.post('/posts/', data)
}

export function updatePost(id, data) {
  return request.put(`/posts/${id}`, data)
}

export function deletePost(id) {
  return request.delete(`/posts/${id}`)
}