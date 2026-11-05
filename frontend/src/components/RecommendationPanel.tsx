import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Book } from '../types/book'
import type { RecommendationResult } from '../types/recommendation'
import { getRecommendations } from '../services/recommendations'
import { useTranslation } from 'react-i18next'
import BookCard from './BookCard'
import { errorKey } from '../services/api'

interface RecommendationPanelProps {
  books: Book[]
  onDetails: (book: Book) => void
}

function toggleSelection(values: string[], value: string): string[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value]
}

function RecommendationPanel({ books, onDetails }: RecommendationPanelProps) {
  const [genres, setGenres] = useState<string[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [language, setLanguage] = useState('')
  const [maxPages, setMaxPages] = useState('')
  const [limit, setLimit] = useState('5')

  const [results, setResults] = useState<RecommendationResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const { t } = useTranslation()

  const requestRef = useRef<AbortController | null>(null)

  const availableGenres = [...new Set(
    books.flatMap((book) =>
      book.genres.map((genre) => genre.trim().toLowerCase()),
    ),
  )].filter(Boolean).sort()

  const tagCounts = new Map<string, number>()
  books.forEach((book) => {
    book.tags.forEach((tag) => {
      const cleanTag = tag.trim().toLowerCase()
      if (cleanTag) {
        tagCounts.set(cleanTag, (tagCounts.get(cleanTag) || 0) + 1)
      }
    })
  })
  const availableTags = Array.from(tagCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([tag]) => tag)
    .sort()

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
      setError('recommendation.errors.preferences')
      return
    }

    const pageLimit = maxPages === '' ? null : Number(maxPages)
    const resultLimit = Number(limit)

    if (
      pageLimit !== null &&
      (!Number.isInteger(pageLimit) || pageLimit <= 0)
    ) {
      setError('recommendation.errors.pages')
      return
    }

    if (
      !Number.isInteger(resultLimit) ||
      resultLimit < 1 ||
      resultLimit > 20
    ) {
      setError('recommendation.errors.limit')
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
          errorKey(error),
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
      <h2>{t('recommendation.heading')}</h2>
      <p className="section-description">
        {t('recommendation.description')}
      </p>

      <form onSubmit={handleSubmit}>
        <fieldset className="preference-fields" disabled={loading}>
          <legend>{t('recommendation.preferences')}</legend>

          <fieldset className="preference-group">
            <legend>{t('recommendation.genres')}</legend>

              <div className="tags-scroll-container">
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
                      <span>{t(`genres.${genre}`, { defaultValue: genre })}</span>
                    </label>
                  ))}
                </div>
              </div>
          </fieldset>

          <fieldset className="preference-group">
            <legend>{t('recommendation.topics')}</legend>

            <div className="tags-scroll-container">
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
                    <span>{t(`tags.${tag}`, { defaultValue: tag })}</span>
                  </label>
                ))}
              </div>
            </div>
          </fieldset>

          <div className="filter-grid">
            <label className="filter-field">
              <span>{t('recommendation.language')}</span>
              <select
                value={language}
                onChange={(event) => {
                  setLanguage(event.target.value)
                  clearPreviousResults()
                }}
              >
                <option value="">{t('recommendation.anyLanguage')}</option>
                {availableLanguages.map((value) => (
                  <option key={value} value={value}>
                    {t(`languages.${value}`, { defaultValue: value })}
                  </option>
                ))}
              </select>
            </label>

            <label className="filter-field">
              <span>{t('recommendation.maxPages')}</span>
              <input
                type="number"
                min="1"
                step="1"
                placeholder={t('recommendation.noLimit')}
                value={maxPages}
                onChange={(event) => {
                  setMaxPages(event.target.value)
                  clearPreviousResults()
                }}
              />
            </label>

            <label className="filter-field">
              <span>{t('recommendation.limit')}</span>
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
            {t(loading ? 'recommendation.loading' : 'recommendation.submit')}
          </button>
          <button className="secondary-button reset-button" type="button" onClick={() => {
            setGenres([]); setTags([]); setLanguage(''); setMaxPages(''); setLimit('5'); clearPreviousResults()
          }}>{t('recommendation.reset')}</button>
        </fieldset>
      </form>

      {loading && (
        <p role="status">{t('recommendation.loading')}</p>
      )}

      {error && (
        <p className="error-message" role="alert">
          {t(error)}
        </p>
      )}

      {hasSubmitted && results.length === 0 && (
        <p role="status">
          {t('recommendation.empty')}
        </p>
      )}

      {hasSubmitted && results.length > 0 && (
        <section className="recommendation-results">
          <h3>{t('recommendation.results')}</h3>
          <p className="section-description">
            {t('recommendation.scoreNote')}
          </p>

          <div className="book-grid">
            {results.map(result => (
              <BookCard key={result.book.id} book={result.book} score={result.score}
                explanations={result.explanations ?? [{ code: 'text_similarity', values: [] }]}
                onDetails={onDetails} />
            ))}
          </div>
        </section>
      )}
    </section>
  )
}

export default RecommendationPanel
