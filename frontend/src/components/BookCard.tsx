import { useTranslation } from 'react-i18next'
import type { Book } from '../types/book'
import type { Explanation } from '../types/recommendation'
import { localizeBook } from '../utils/localizeBook'
import BookCover from './BookCover'

interface Props {
  book: Book
  onDetails: (book: Book) => void
  score?: number
  explanations?: Explanation[]
  ranking?: boolean
}

export default function BookCard({ book, onDetails, score, explanations, ranking = false }: Props) {
  const { t, i18n } = useTranslation()
  const localized = localizeBook(book, i18n.resolvedLanguage)
  const explanationText = (explanation: Explanation) => {
    const category = explanation.code.includes('genres') ? 'genres' : 'tags'
    const values = explanation.values.map(value => t(`${category}.${value}`, { defaultValue: value })).join(', ')
    return t(`explanations.${explanation.code}`, { values })
  }
  return (
    <article className="book-card">
      <BookCover
        id={book.id}
        title={localized.title}
        author={book.author}
      />

      {score !== undefined && (
        <p className="match-score">
          {t(
            ranking
              ? 'recommendation.rankingScore'
              : 'recommendation.matchScore',
            { score: score.toFixed(3) },
          )}
        </p>
      )}
      {score !== undefined && <p className="match-score">
        {t(ranking ? 'recommendation.rankingScore' : 'recommendation.matchScore', { score: score.toFixed(3) })}
      </p>}
      <div className="genre-list">
        {book.genres.map(genre => <span className="genre" key={genre}>
          {t(`genres.${genre}`, { defaultValue: genre })}
        </span>)}
      </div>
      <h3>{localized.title}</h3>
      <p className="book-author">{t('library.author', { author: book.author })}</p>
      <p className="book-description">{localized.description}</p>
      {explanations && explanations.length > 0 && <div className="recommendation-reasons">
        <h4>{t('recommendation.why')}</h4>
        <ul>{explanations.map((reason, index) => <li key={`${reason.code}-${index}`}>{explanationText(reason)}</li>)}</ul>
      </div>}
      <p className="book-meta">
        {t('library.editionLanguage', { language: t(`languages.${book.language}`, { defaultValue: book.language }) })}
        {' · '}{book.pages == null ? t('library.unknownPages') : t('library.pages', { count: book.pages })}
      </p>
      <button type="button" className="secondary-button" onClick={() => onDetails(book)}>
        {t('details.open')}
      </button>
    </article>
  )
}
