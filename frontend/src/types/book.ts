export interface BookTranslation {
  title: string
  description: string
}

export interface Book {
  id: string
  title: string
  author: string
  genres: string[]
  tags: string[]
  description: string
  language: string
  pages: number | null

  work_id?: string | null
  original_language?: string | null
  isbn?: string | null
  source_url?: string | null

  translations?: Partial<
    Record<'en' | 'ru' | 'vi', BookTranslation>
  >

  metadata_notes?: Record<string, string>
}