import type { Book } from '../types/book'

export async function getBooks(signal?: AbortSignal): Promise<Book[]> {
  const response = await fetch('/api/books', { signal })

  if (!response.ok) {
    throw new Error(`Unable to load books (HTTP ${response.status}).`)
  }

  const books: Book[] = await response.json()
  return books
}