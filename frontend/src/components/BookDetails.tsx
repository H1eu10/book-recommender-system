import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Book } from '../types/book'
import type { RecommendationResult } from '../types/recommendation'
import { getSimilarBooks } from '../services/recommendations'
import { errorKey } from '../services/api'
import { localizeBook } from '../utils/localizeBook'

interface Props { book: Book; onClose: () => void; onSelect: (book: Book) => void }

export default function BookDetails({ book, onClose, onSelect }: Props) {
  const { t, i18n } = useTranslation()
  const dialog = useRef<HTMLDialogElement>(null)
  const request = useRef<AbortController | null>(null)
  const [results, setResults] = useState<RecommendationResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const localized = localizeBook(book, i18n.resolvedLanguage)
  const source = book.source_url && /^https?:\/\//i.test(book.source_url) ? book.source_url : null

  useEffect(() => {
    const node = dialog.current
    node?.showModal()
    return () => { request.current?.abort(); node?.close() }
  }, [])

  async function loadSimilar() {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    setError(null)
    try {
      const data = await getSimilarBooks(book.id, controller.signal)
      if (!controller.signal.aborted) setResults(data)
    } catch (cause) {
      if (!controller.signal.aborted) setError(errorKey(cause))
    } finally {
      if (!controller.signal.aborted) setLoading(false)
    }
  }

  return <dialog ref={dialog} className="book-dialog" aria-labelledby="book-detail-title" onCancel={onClose}>
    <div className="dialog-toolbar">
      <button type="button" className="secondary-button" onClick={onClose} autoFocus>{t('details.close')}</button>
    </div>
    <h2 id="book-detail-title">{localized.title}</h2>
    {localized.title !== book.title && <p>{t('details.originalTitle', { title: book.title })}</p>}
    <p>{t('library.author', { author: book.author })}</p>
    <p className="full-description">{localized.description}</p>
    {localized.translated && book.metadata_notes?.translation_source &&
      <p className="section-description">{t('details.translationNote')}</p>}
    {localized.translated && <details><summary>{t('details.originalMetadata')}</summary>
      <h3>{book.title}</h3><p className="full-description">{book.description}</p>
    </details>}
    <dl className="book-facts">
      <dt>{t('recommendation.genres')}</dt><dd>{book.genres.map(g => t(`genres.${g}`, { defaultValue: g })).join(', ')}</dd>
      <dt>{t('recommendation.topics')}</dt><dd>{book.tags.map(tag => t(`tags.${tag}`, { defaultValue: tag })).join(', ') || t('details.notAvailable')}</dd>
      <dt>{t('recommendation.language')}</dt><dd>{t(`languages.${book.language}`, { defaultValue: book.language })}</dd>
      <dt>{t('details.pages')}</dt><dd>{book.pages ?? t('details.notAvailable')}</dd>
      {book.isbn && <><dt>ISBN</dt><dd>{book.isbn}</dd></>}
    </dl>
    {source && <p><a href={source} target="_blank" rel="noopener noreferrer">{t('details.source')}</a></p>}
    <button type="button" className="primary-button" onClick={() => void loadSimilar()} disabled={loading}>
      {t(loading ? 'recommendation.loading' : 'details.similar')}
    </button>
    {error && <p role="alert" className="error-message">{t(error)}</p>}
    {loading && <p role="status">{t('recommendation.loading')}</p>}
    {results && <section aria-label={t('details.similar')}>
      <h3>{t('details.similar')}</h3>
      {!results.length && <p role="status">{t('recommendation.empty')}</p>}
      <ul className="similar-list">{results.map(result => <li key={result.book.id}>
        <button type="button" className="text-button" onClick={() => onSelect(result.book)}>
          {localizeBook(result.book, i18n.resolvedLanguage).title}
        </button>
        {' — '}{result.book.author}
      </li>)}</ul>
    </section>}
  </dialog>
}
