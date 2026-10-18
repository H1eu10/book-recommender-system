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
}