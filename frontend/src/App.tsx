import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { getBooks } from './services/books'
import type { Book } from './types/book'
import LanguageSwitcher from './components/LanguageSwitcher'
import RecommendationPanel from './components/RecommendationPanel'
import PersonalizedPanel from './components/PersonalizedPanel'
import BookCard from './components/BookCard'
import BookDetails from './components/BookDetails'
import { errorKey } from './services/api'
import { localizeBook } from './utils/localizeBook'

import './App.css'

const ITEMS_PER_PAGE = 15

function App() {
  const { t, i18n } = useTranslation()

  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [query, setQuery] = useState('')
  const [genreFilter, setGenreFilter] = useState('')
  const [mode, setMode] = useState<'preferences' | 'personalized'>('preferences')
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)

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
            errorKey(error),
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

  const filteredBooks = useMemo(() => {
    const search = query.trim().toLocaleLowerCase()
    return books.filter(book => {
      const localized = localizeBook(book, i18n.resolvedLanguage)
      return (!genreFilter || book.genres.includes(genreFilter)) &&
        (!search || [book.title, localized.title, book.author].some(value => value.toLocaleLowerCase().includes(search)))
    })
  }, [books, query, genreFilter, i18n.resolvedLanguage])
  const availableGenres = [...new Set(books.flatMap(book => book.genres))].sort()
  const totalPages = Math.ceil(filteredBooks.length / ITEMS_PER_PAGE)
  const visiblePage = Math.min(currentPage, Math.max(1, totalPages))
  const indexOfLastBook = visiblePage * ITEMS_PER_PAGE
  const indexOfFirstBook = indexOfLastBook - ITEMS_PER_PAGE
  const currentBooks = filteredBooks.slice(indexOfFirstBook, indexOfLastBook)

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [currentPage])

  const handlePrevPage = () => setCurrentPage(Math.max(visiblePage - 1, 1))
  const handleNextPage = () => setCurrentPage(Math.min(visiblePage + 1, totalPages))

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
          <p>{t(error)}</p>

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
          <fieldset className="recommendation-mode">
            <legend>{t('recommendation.mode')}</legend>
            <label><input type="radio" name="mode" checked={mode === 'preferences'} onChange={() => setMode('preferences')} />
              {t('recommendation.byPreferences')}</label>
            <label><input type="radio" name="mode" checked={mode === 'personalized'} onChange={() => setMode('personalized')} />
              {t('recommendation.byHistory')}</label>
          </fieldset>
          {mode === 'preferences'
            ? <RecommendationPanel books={books} onDetails={setSelectedBook} />
            : <PersonalizedPanel books={books} onDetails={setSelectedBook} />}

          <h2 className="library-heading">
            {t('library.heading')}
          </h2>

          <div className="filter-grid library-filters">
            <label className="filter-field"><span>{t('library.search')}</span>
              <input type="search" value={query} placeholder={t('library.searchPlaceholder')}
                onChange={event => { setQuery(event.target.value); setCurrentPage(1) }} />
            </label>
            <label className="filter-field"><span>{t('recommendation.genres')}</span>
              <select value={genreFilter} onChange={event => { setGenreFilter(event.target.value); setCurrentPage(1) }}>
                <option value="">{t('library.allGenres')}</option>
                {availableGenres.map(genre => <option key={genre} value={genre}>{t(`genres.${genre}`, { defaultValue: genre })}</option>)}
              </select>
            </label>
          </div>
          <p className="result-count" role="status">{t('library.filteredCount', { count: filteredBooks.length, total: books.length })}</p>
          {!filteredBooks.length && <p>{t('library.noResults')}</p>}

          <section
            className="book-grid"
            aria-label={t('library.heading')}
          >
            {currentBooks.map((book) => (
              <BookCard book={book} key={book.id} onDetails={setSelectedBook} />
            ))}
          </section>
          {totalPages > 1 && (
            <div className="pagination">
              <button
                type="button"
                onClick={handlePrevPage}
                disabled={visiblePage === 1}
                className="pagination-button"
              >
                {t('pagination.previous')}
              </button>
              
              <span className="pagination-info">
                {t('pagination.pageInfo', {
                  current: visiblePage,
                  total: totalPages,
                })}
              </span>

              <button
                type="button"
                onClick={handleNextPage}
                disabled={visiblePage === totalPages}
                className="pagination-button"
              >
                {t('pagination.next')}
              </button>
            </div>
          )}
        </>
      )}
      {selectedBook && <BookDetails key={selectedBook.id} book={selectedBook}
        onClose={() => setSelectedBook(null)} onSelect={setSelectedBook} />}
    </main>
  )
}

export default App
