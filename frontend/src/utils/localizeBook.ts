import type { Book } from '../types/book'
import { isAppLocale } from '../i18n'

export function localizeBook(book: Book, language?: string) {
  const locale = language?.split('-')[0] ?? 'en'

  const translation = isAppLocale(locale)
    ? book.translations?.[locale]
    : undefined

  // Keep the original metadata when an automatic translation is visibly broken.
  // This does not change the dataset or attempt to guess a corrected translation.
  function readable(value: string | undefined, original: string, title = false) {
    const text = value?.trim()
    if (!text || /(.{2,40})\1{5,}/u.test(text) || /href\s*=|https_{3,}/i.test(text)) return original
    if (title && text.length > Math.max(250, original.length * 3)) return original
    return text
  }
  const title = readable(translation?.title, book.title, true)
  const description = readable(translation?.description, book.description)
  return { title, description, translated: title !== book.title || description !== book.description }
}
