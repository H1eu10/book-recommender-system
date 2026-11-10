import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type { Book } from '../types/book'

interface Props {
  books: Book[]
}

export default function LibraryStats({ books }: Props) {
  const { t, i18n } = useTranslation()

  const stats = useMemo(() => {
    const authors = new Set<string>()
    const genres = new Set<string>()
    const languages = new Set<string>()

    for (const book of books) {
      const author = book.author.trim().toLowerCase()
      const language = book.language.trim().toLowerCase()

      if (author) authors.add(author)
      if (language) languages.add(language)

      for (const genre of book.genres) {
        const normalized = genre.trim().toLowerCase()

        if (normalized) genres.add(normalized)
      }
    }

    return [
      { key: 'books', value: books.length },
      { key: 'authors', value: authors.size },
      { key: 'genres', value: genres.size },
      { key: 'languages', value: languages.size },
    ]
  }, [books])

  const numberFormatter = useMemo(
    () => new Intl.NumberFormat(i18n.resolvedLanguage || 'en'),
    [i18n.resolvedLanguage],
  )

  return (
    <section
      className="library-stats"
      aria-labelledby="library-stats-heading"
    >
      <div className="library-stats__intro">
        <h2 id="library-stats-heading">
          {t('home.stats.title')}
        </h2>

        <p>{t('home.stats.description')}</p>
      </div>

      <dl className="library-stats__grid">
        {stats.map(stat => (
          <div className="library-stats__item" key={stat.key}>
            <dt>{t(`home.stats.${stat.key}`)}</dt>

            <dd>{numberFormatter.format(stat.value)}</dd>
          </div>
        ))}
      </dl>

      <p className="library-stats__note">
        {t('home.stats.note')}
      </p>
    </section>
  )
}