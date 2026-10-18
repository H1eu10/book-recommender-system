import type { Book } from '../types/book'
import { isAppLocale } from '../i18n'

export function localizeBook(book: Book, language?: string) {
  const locale = language?.split('-')[0] ?? 'en'

  const translation = isAppLocale(locale)
    ? book.translations?.[locale]
    : undefined

  return {
    title: translation?.title ?? book.title,
    description: translation?.description ?? book.description,
  }
}