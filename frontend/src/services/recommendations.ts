import type { RecommendationRequest, RecommendationResult, ModelStatus, ModelId, ProfileSummary, Profile, PersonalizedResponse } from '../types/recommendation'
import { requestJson } from './api'

function post<T>(url: string, body: unknown, signal?: AbortSignal) {
  return requestJson<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
}

export function getRecommendations(preferences: RecommendationRequest, signal?: AbortSignal) {
  return post<RecommendationResult[]>('/api/recommendations/smart', preferences, signal)
}

export function getSimilarBooks(bookId: string, signal?: AbortSignal) {
  return post<RecommendationResult[]>('/api/recommendations/similar', { book_id: bookId, limit: 5 }, signal)
}

export function getModels(signal?: AbortSignal) {
  return requestJson<ModelStatus[]>('/api/models', { signal })
}

export function getProfiles(signal?: AbortSignal) {
  return requestJson<ProfileSummary[]>('/api/profiles', { signal })
}

export function getProfile(userId: string, signal?: AbortSignal) {
  return requestJson<Profile>(`/api/profiles/${encodeURIComponent(userId)}`, { signal })
}

export function getPersonalizedRecommendations(userId: string, model: ModelId, limit: number, signal?: AbortSignal) {
  return post<PersonalizedResponse>('/api/recommendations/personalized', { user_id: userId, model, limit }, signal)
}
