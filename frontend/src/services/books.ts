import type { Book } from '../types/book'
import { requestJson } from './api'

export function getBooks(signal?: AbortSignal): Promise<Book[]> {
  return requestJson<Book[]>('/api/books', { signal })
}
