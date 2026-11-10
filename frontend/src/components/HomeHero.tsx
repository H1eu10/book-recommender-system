import { useTranslation } from 'react-i18next'

interface Props {
  ready: boolean
}

export default function HomeHero({ ready }: Props) {
  const { t } = useTranslation()

  return (
    <header className="home-hero">
      <div className="home-hero__content">
        <p className="eyebrow">{t('app.name')}</p>

        <h1>{t('home.hero.title')}</h1>

        <p className="home-hero__description">
          {t('home.hero.description')}
        </p>

        {ready && (
          <nav
            className="home-hero__actions"
            aria-label={t('home.hero.actionsLabel')}
          >
            <a
              className="primary-button"
              href="#recommendations"
            >
              {t('home.hero.findBooks')}
            </a>

            <a
              className="secondary-button"
              href="#library"
            >
              {t('home.hero.exploreLibrary')}
            </a>
          </nav>
        )}

        <p className="home-hero__note">
          {t('home.hero.note')}
        </p>
      </div>

      <div className="home-hero__art" aria-hidden="true">
        <span className="home-hero__halo" />

        <div className="hero-volume hero-volume--back">
          <span className="hero-volume__frame" />
        </div>

        <div className="hero-volume hero-volume--middle">
          <span className="hero-volume__frame" />
        </div>

        <div className="hero-volume hero-volume--front">
          <span className="hero-volume__frame" />
          <span className="hero-volume__ornament">✦</span>
          <span className="hero-volume__line" />
          <span className="hero-volume__line hero-volume__line--short" />
        </div>

        <span className="home-hero__shelf" />
      </div>
    </header>
  )
}