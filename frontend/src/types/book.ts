export interface Book {
  id: string
  title: string
  author: string
  genres: string[]
  tags: string[]
  description: string
  language: string
  pages: number | null
}