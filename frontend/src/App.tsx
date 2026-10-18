import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { getBooks } from './services/books'
import type { Book } from './types/book'
import LanguageSwitcher from './components/LanguageSwitcher'
import RecommendationPanel from './components/RecommendationPanel'
import { localizeBook } from './utils/localizeBook'

import './App.css'

function App() {
  const { t, i18n } = useTranslation()

  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadBooks() {
      try {
        const data = await getBooks(controller.signal)

        if (!controller.signal.aborted) {
          setBooks(data)
        }
      } catch (error: unknown) {
        if (!controller.signal.aborted) {
          setError(
            error instanceof Error
              ? error.message
              : 'Unable to load books.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadBooks()

    return () => {
      controller.abort()
    }
  }, [])

  return (
    <main className="app">
      <div className="page-toolbar">
        <LanguageSwitcher />
      </div>

      <header className="page-header">
        <p className="eyebrow">{t('app.name')}</p>
        <h1>{t('app.heading')}</h1>
        <p>{t('app.description')}</p>
      </header>

      {loading && <p role="status">{t('library.loading')}</p>}

      {!loading && error && (
        <div className="error-message" role="alert">
          <p>{t('library.error')}</p>

          <button
            type="button"
            onClick={() => window.location.reload()}
          >
            {t('library.retry')}
          </button>
        </div>
      )}

      {!loading && !error && books.length === 0 && (
        <p>{t('library.empty')}</p>
      )}

      {!loading && !error && books.length > 0 && (
        <>
          <RecommendationPanel books={books} />

          <h2 className="library-heading">
            {t('library.heading')}
          </h2>

          <p className="result-count">
            {t('library.count', { count: books.length })}
          </p>

          <section
            className="book-grid"
            aria-label={t('library.heading')}
          >
            {books.map((book) => (
              <article className="book-card" key={book.id}>
                <div className="genre-list">
                  {book.genres.map((genre) => (
                    <span className="genre" key={genre}>
                      {t(`genres.${genre}`, {
                        defaultValue: genre,
                      })}
                    </span>
                  ))}
                </div>

                <h2>
                  {localizeBook(book, i18n.resolvedLanguage).title}
                </h2>

                <p className="book-author">
                  {t('library.author', { author: book.author })}
                </p>

                <p className="book-description">
                  {localizeBook(book, i18n.resolvedLanguage).description}
                </p>

                <p className="book-meta">
                  {t('library.editionLanguage', {
                    language: t(`languages.${book.language}`, {
                      defaultValue: book.language,
                    }),
                  })}
                  {' · '}
                  {book.pages == null
                    ? t('library.unknownPages')
                    : t('library.pages', { count: book.pages })}
                </p>
              </article>
            ))}
          </section>
        </>
      )}
    </main>
  )
}

export default App