import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Book } from '../types/book'
import type { RecommendationResult } from '../types/recommendation'
import { getRecommendations } from '../services/recommendations'

interface RecommendationPanelProps {
  books: Book[]
}

function toggleSelection(values: string[], value: string): string[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value]
}

function RecommendationPanel({ books }: RecommendationPanelProps) {
  const [genres, setGenres] = useState<string[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [language, setLanguage] = useState('')
  const [maxPages, setMaxPages] = useState('')
  const [limit, setLimit] = useState('5')

  const [results, setResults] = useState<RecommendationResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSubmitted, setHasSubmitted] = useState(false)

  const requestRef = useRef<AbortController | null>(null)

  const availableGenres = [...new Set(
    books.flatMap((book) =>
      book.genres.map((genre) => genre.trim().toLowerCase()),
    ),
  )].filter(Boolean).sort()

  const availableTags = [...new Set(
    books.flatMap((book) =>
      book.tags.map((tag) => tag.trim().toLowerCase()),
    ),
  )].filter(Boolean).sort()

  const availableLanguages = [...new Set(
    books.map((book) => book.language.trim().toLowerCase()),
  )].filter(Boolean).sort()

  useEffect(() => {
    return () => {
      requestRef.current?.abort()
    }
  }, [])

  function clearPreviousResults() {
    setResults([])
    setError(null)
    setHasSubmitted(false)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (loading) {
      return
    }

    clearPreviousResults()

    if (genres.length === 0 && tags.length === 0) {
      setError('Please select at least one genre or topic.')
      return
    }

    const pageLimit = maxPages === '' ? null : Number(maxPages)
    const resultLimit = Number(limit)

    if (
      pageLimit !== null &&
      (!Number.isInteger(pageLimit) || pageLimit <= 0)
    ) {
      setError('Maximum pages must be a positive integer.')
      return
    }

    if (
      !Number.isInteger(resultLimit) ||
      resultLimit < 1 ||
      resultLimit > 20
    ) {
      setError('Number of results must be between 1 and 20.')
      return
    }

    requestRef.current?.abort()

    const controller = new AbortController()
    requestRef.current = controller

    setLoading(true)

    try {
      const data = await getRecommendations(
        {
          genres,
          tags,
          language: language || null,
          max_pages: pageLimit,
          limit: resultLimit,
        },
        controller.signal,
      )

      if (!controller.signal.aborted) {
        setResults(data)
        setHasSubmitted(true)
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setError(
          error instanceof Error
            ? error.message
            : 'Unable to get recommendations.',
        )
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
      }
    }
  }

  return (
    <section className="recommendation-panel">
      <h2>Find your next book</h2>
      <p className="section-description">
        Choose genres or topics you enjoy. Language and page count
        are optional filters.
      </p>

      <form onSubmit={handleSubmit}>
        <fieldset className="preference-fields" disabled={loading}>
          <legend>Your preferences</legend>

          <fieldset className="preference-group">
            <legend>Genres</legend>

            <div className="preference-options">
              {availableGenres.map((genre) => (
                <label className="preference-option" key={genre}>
                  <input
                    type="checkbox"
                    checked={genres.includes(genre)}
                    onChange={() => {
                      setGenres((current) =>
                        toggleSelection(current, genre),
                      )
                      clearPreviousResults()
                    }}
                  />
                  <span>{genre}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="preference-group">
            <legend>Topics</legend>

            <div className="preference-options">
              {availableTags.map((tag) => (
                <label className="preference-option" key={tag}>
                  <input
                    type="checkbox"
                    checked={tags.includes(tag)}
                    onChange={() => {
                      setTags((current) =>
                        toggleSelection(current, tag),
                      )
                      clearPreviousResults()
                    }}
                  />
                  <span>{tag}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="filter-grid">
            <label className="filter-field">
              <span>Language</span>
              <select
                value={language}
                onChange={(event) => {
                  setLanguage(event.target.value)
                  clearPreviousResults()
                }}
              >
                <option value="">Any language</option>
                {availableLanguages.map((value) => (
                  <option key={value} value={value}>
                    {value.toUpperCase()}
                  </option>
                ))}
              </select>
            </label>

            <label className="filter-field">
              <span>Maximum pages</span>
              <input
                type="number"
                min="1"
                step="1"
                placeholder="No limit"
                value={maxPages}
                onChange={(event) => {
                  setMaxPages(event.target.value)
                  clearPreviousResults()
                }}
              />
            </label>

            <label className="filter-field">
              <span>Number of results</span>
              <input
                type="number"
                min="1"
                max="20"
                step="1"
                required
                value={limit}
                onChange={(event) => {
                  setLimit(event.target.value)
                  clearPreviousResults()
                }}
              />
            </label>
          </div>

          <button className="primary-button" type="submit">
            {loading ? 'Finding books...' : 'Get recommendations'}
          </button>
        </fieldset>
      </form>

      {loading && (
        <p role="status">Looking for books that match your preferences...</p>
      )}

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}

      {hasSubmitted && results.length === 0 && (
        <p role="status">
          No matching books found. Try different preferences or less
          restrictive filters.
        </p>
      )}

      {hasSubmitted && results.length > 0 && (
        <section className="recommendation-results">
          <h3>Your recommendations</h3>
          <p className="section-description">
            Scores describe preference matches, not the probability
            that you will like a book.
          </p>

          <div className="book-grid">
            {results.map(({ book, score, reasons }) => (
              <article className="book-card" key={book.id}>
                <p className="match-score">
                  Match score: {score.toFixed(2)} / 1.00
                </p>

                <h2>{book.title}</h2>
                <p className="book-author">by {book.author}</p>
                <p className="book-description">{book.description}</p>

                <div className="recommendation-reasons">
                  <h4>Why this book?</h4>
                  <ul>
                    {reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </div>

                <p className="book-meta">
                  {book.language.toUpperCase()} ·{' '}
                  {book.pages === null
                    ? 'Page count unavailable'
                    : `${book.pages} pages`}
                </p>
              </article>
            ))}
          </div>
        </section>
      )}
    </section>
  )
}

export default RecommendationPanel