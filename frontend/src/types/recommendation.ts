import type { Book } from './book'

export interface RecommendationRequest {
  genres: string[]
  tags: string[]
  language: string | null
  max_pages: number | null
  limit: number
}

export interface RecommendationResult {
  book: Book
  score: number
  reasons: string[]
  explanations?: Explanation[]
}

export interface Explanation {
  code: 'genres' | 'themes' | 'shared_genres' | 'shared_themes' | 'text_similarity' | 'history' | 'popularity'
  values: string[]
}

export interface ProfileSummary { id: string; liked_count: number }
export interface Profile { id: string; liked_book_ids: string[]; synthetic: boolean }
export type ModelId = 'popularity' | 'itemcf' | 'ncf' | 'lightgcn'
export interface ModelStatus { id: ModelId; available: boolean }
export interface PersonalizedResponse {
  model: ModelId
  score_type: 'ranking'
  fallback: boolean
  results: { book: Book; score: number; explanations: Explanation[] }[]
}
