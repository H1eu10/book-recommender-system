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
import HomeHero from './components/HomeHero'
import LibraryStats from './components/LibraryStats'
import ScrollReveal from './components/ScrollReveal'
import BookFade from './components/BookFade'

import './App.css'
import './styles/vintage.css'

const ITEMS_PER_PAGE = 15

function App() {
  const { t, i18n } = useTranslation()

  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [query, setQuery] = useState('')
  const [genreFilter, setGenreFilter] = useState('')
  const [sortBy, setSortBy] = useState<'default' | 'title' | 'pagesAsc' | 'pagesDesc'>('default')
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

  const sortedBooks = useMemo(() => {
    if (sortBy === 'default') {
      return filteredBooks
    }

    const sorted = [...filteredBooks]

    if (sortBy === 'title') {
      const collator = new Intl.Collator(
        i18n.resolvedLanguage || 'en',
        { sensitivity: 'base', numeric: true },
      )

      return sorted.sort((a, b) =>
        collator.compare(
          localizeBook(a, i18n.resolvedLanguage).title,
          localizeBook(b, i18n.resolvedLanguage).title,
        ),
      )
    }
    return sorted.sort((a, b) => {
      const aPages = a.pages
      const bPages = b.pages
      if (aPages == null && bPages == null) return 0
      if (aPages == null) return 1
      if (bPages == null) return -1

      return sortBy === 'pagesAsc'
        ? aPages - bPages
        : bPages - aPages
    })
  }, [filteredBooks, sortBy, i18n.resolvedLanguage])
  const availableGenres = [...new Set(books.flatMap(book => book.genres))].sort()
  const totalPages = Math.ceil(sortedBooks.length / ITEMS_PER_PAGE)
  const visiblePage = Math.min(currentPage, Math.max(1, totalPages))
  const indexOfLastBook = visiblePage * ITEMS_PER_PAGE
  const indexOfFirstBook = indexOfLastBook - ITEMS_PER_PAGE
  const currentBooks = sortedBooks.slice(indexOfFirstBook, indexOfLastBook)



function scrollToLibrary() {
  const heading = document.getElementById('library')

  if (!heading) return

  const reduceMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)',
  ).matches

  heading.scrollIntoView({
    behavior: reduceMotion ? 'auto' : 'smooth',
    block: 'start',
  })
}

function changeLibraryPage(nextPage: number) {
  const lastPage = Math.max(1, totalPages)
  const targetPage = Math.min(
    Math.max(nextPage, 1),
    lastPage,
  )

  if (targetPage === visiblePage) return

  setCurrentPage(targetPage)
  scrollToLibrary()
}

const handlePrevPage = () => {
  changeLibraryPage(visiblePage - 1)
}

const handleNextPage = () => {
  changeLibraryPage(visiblePage + 1)
}

  return (
    <main className="app">
      <div className="page-toolbar">
        <LanguageSwitcher />
      </div>

      <HomeHero ready={!loading && !error && books.length > 0} />
        {!loading && !error && books.length > 0 && (
            <ScrollReveal>
              <LibraryStats books={books} />
            </ScrollReveal>
        )}

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
          <fieldset
            id="recommendations"
            className="recommendation-mode"
          >
            <legend>{t('recommendation.mode')}</legend>

            <div className="discovery-options">
              <label className="discovery-option">
                <input
                  type="radio"
                  name="mode"
                  value="preferences"
                  checked={mode === 'preferences'}
                  onChange={() => setMode('preferences')}
                />

                <span className="discovery-option__content">
                  <span className="discovery-option__heading">
                    {t('recommendation.byPreferences')}
                  </span>

                  <span className="discovery-option__description">
                    {t('home.discovery.preferencesDescription')}
                  </span>
                </span>
              </label>

              <label className="discovery-option">
                <input
                  type="radio"
                  name="mode"
                  value="personalized"
                  checked={mode === 'personalized'}
                  onChange={() => setMode('personalized')}
                />
                <span className="discovery-option__content">
                  <span className="discovery-option__heading">
                    {t('recommendation.byHistory')}
                  </span>

                  <span className="discovery-option__description">
                    {t('home.discovery.historyDescription')}
                  </span>
                </span>
              </label>
            </div>
          </fieldset>
          {mode === 'preferences'
            ? <RecommendationPanel books={books} onDetails={setSelectedBook} />
            : <PersonalizedPanel books={books} onDetails={setSelectedBook} />}

          <h2 id="library" className="library-heading">
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
            <label className="filter-field">
              <span>{t('library.sort.label')}</span>

              <select
                value={sortBy}
                onChange={event => {
                  setSortBy(
                    event.target.value as
                      'default' | 'title' | 'pagesAsc' | 'pagesDesc',
                  )
                  setCurrentPage(1)
                }}
              >
                <option value="default">
                  {t('library.sort.default')}
                </option>

                <option value="title">
                  {t('library.sort.title')}
                </option>

                <option value="pagesAsc">
                  {t('library.sort.pagesAsc')}
                </option>

                <option value="pagesDesc">
                  {t('library.sort.pagesDesc')}
                </option>
              </select>
            </label>

          </div>
          <p className="result-count" role="status">{t('library.filteredCount', { count: filteredBooks.length, total: books.length })}</p>
          {!filteredBooks.length && <p>{t('library.noResults')}</p>}

          <section
            className="book-grid"
            aria-label={t('library.heading')}
          >
          {currentBooks.map((book, index) => (
            <BookFade key={book.id} index={index}>
              <BookCard
                book={book}
                onDetails={setSelectedBook}
              />
            </BookFade>
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
