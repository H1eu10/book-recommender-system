import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Book } from '../types/book'
import type { ModelId, ModelStatus, ProfileSummary, Profile, PersonalizedResponse } from '../types/recommendation'
import { getModels, getProfile, getProfiles, getPersonalizedRecommendations } from '../services/recommendations'
import { errorKey } from '../services/api'
import { localizeBook } from '../utils/localizeBook'
import BookCard from './BookCard'

interface Props { books: Book[]; onDetails: (book: Book) => void }

export default function PersonalizedPanel({ books, onDetails }: Props) {
  const { t, i18n } = useTranslation()
  const [profiles, setProfiles] = useState<ProfileSummary[]>([])
  const [profilesLoaded, setProfilesLoaded] = useState(false)
  const [models, setModels] = useState<ModelStatus[]>([])
  const [userId, setUserId] = useState('')
  const [model, setModel] = useState<ModelId>('itemcf')
  const [limit, setLimit] = useState(5)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [response, setResponse] = useState<PersonalizedResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [listError, setListError] = useState<string | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [retry, setRetry] = useState(0)
  const request = useRef<AbortController | null>(null)
  const bookMap = new Map(books.map(book => [book.id, book]))
  const profileLoading = Boolean(userId && (!profile || profile.id !== userId) && !profileError)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([getProfiles(controller.signal), getModels(controller.signal)])
      .then(([users, statuses]) => {
        if (controller.signal.aborted) return
        setProfiles(users)
        setProfilesLoaded(true)
        setModels(statuses)
        setUserId(users[0]?.id ?? '')
        setModel(statuses.find(status => status.id === 'lightgcn' && status.available)?.id
          ?? statuses.find(status => status.id === 'itemcf' && status.available)?.id ?? 'popularity')
      })
      .catch(cause => { if (!controller.signal.aborted) setListError(errorKey(cause)) })
    return () => { controller.abort(); request.current?.abort() }
  }, [retry])

  useEffect(() => {
    if (!userId) return
    const controller = new AbortController()
    getProfile(userId, controller.signal)
      .then(value => { if (!controller.signal.aborted) setProfile(value) })
      .catch(cause => { if (!controller.signal.aborted) setProfileError(errorKey(cause)) })
    return () => controller.abort()
  }, [userId, retry])

  function clearResults() { setResponse(null); setError(null) }

  function retryLoad() {
    setListError(null); setProfileError(null); setProfilesLoaded(false); setProfile(null)
    clearResults()
    setRetry(value => value + 1)
  }

  async function submit() {
    if (!profile || loading) return
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    clearResults()
    try {
      const value = await getPersonalizedRecommendations(userId, model, limit, controller.signal)
      if (!controller.signal.aborted) setResponse(value)
    } catch (cause) {
      if (!controller.signal.aborted) setError(errorKey(cause))
    } finally {
      if (!controller.signal.aborted) setLoading(false)
    }
  }

  return <section className="recommendation-panel" aria-labelledby="personalized-heading">
    <h2 id="personalized-heading">{t('personalized.heading')}</h2>
    <p className="section-description">{t('personalized.demoNote')}</p>
    {listError ? <div className="error-message" role="alert">
      <p>{t(listError)}</p><button type="button" onClick={retryLoad}>{t('library.retry')}</button>
    </div> : !profiles.length ? <p role="status">{t(profilesLoaded ? 'personalized.noProfiles' : 'personalized.loadingProfiles')}</p> : <>
      <form onSubmit={event => { event.preventDefault(); void submit() }}>
        <fieldset className="preference-fields" disabled={loading}>
          <legend>{t('personalized.settings')}</legend>
          <div className="filter-grid">
            <label className="filter-field"><span>{t('personalized.profile')}</span>
              <select value={userId} onChange={event => { setUserId(event.target.value); setProfile(null); setProfileError(null); clearResults() }}>
                {profiles.map(user => <option key={user.id} value={user.id}>{user.id} ({t('personalized.likeCount', { count: user.liked_count })})</option>)}
              </select>
            </label>
            <label className="filter-field"><span>{t('personalized.model')}</span>
              <select value={model} onChange={event => { setModel(event.target.value as ModelId); clearResults() }}>
                {models.map(status => <option key={status.id} value={status.id} disabled={!status.available}>
                  {t(`models.${status.id}`)}{status.available ? '' : ` (${t('personalized.unavailable')})`}
                </option>)}
              </select>
            </label>
            <label className="filter-field"><span>{t('recommendation.limit')}</span>
              <input type="number" min="1" max="20" required value={limit}
                onChange={event => { setLimit(Number(event.target.value)); clearResults() }} />
            </label>
          </div>
          <button type="submit" className="primary-button" disabled={profileLoading || !profile}>
            {t(loading ? 'recommendation.loading' : 'recommendation.submit')}
          </button>
        </fieldset>
      </form>
      {profileLoading && <p role="status">{t('personalized.loadingHistory')}</p>}
      {profileError && <div role="alert" className="error-message"><p>{t(profileError)}</p>
        <button type="button" onClick={retryLoad}>{t('library.retry')}</button>
      </div>}
      {profile && <section aria-label={t('personalized.history')}>
        <h3>{t('personalized.history')}</h3>
        <ul className="profile-history">{profile.liked_book_ids.map(id => {
          const book = bookMap.get(id)
          return book ? <li key={id}><button type="button" className="text-button" onClick={() => onDetails(book)}>
            {localizeBook(book, i18n.resolvedLanguage).title}
          </button></li> : null
        })}</ul>
      </section>}
      {loading && <p role="status">{t('recommendation.loading')}</p>}
      {error && <p role="alert" className="error-message">{t(error)}</p>}
      {response && <section className="recommendation-results" aria-labelledby="personalized-results-heading">
        <h3 id="personalized-results-heading">{t('recommendation.results')}</h3>
        <p className="section-description">{t('personalized.scoreNote')}</p>
        {response.fallback && <p role="status">{t('personalized.fallback')}</p>}
        {!response.results.length && <p role="status">{t('recommendation.empty')}</p>}
        <div className="book-grid">{response.results.map(result => <BookCard key={result.book.id}
          {...result} ranking onDetails={onDetails} />)}</div>
      </section>}
    </>}
  </section>
}
