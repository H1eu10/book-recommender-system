
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from './LanguageSwitcher'

export default function SiteHeader() {
  const { t } = useTranslation()

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <a
          className="site-header__brand"
          href="#home"
          aria-label={t('navigation.home')}
        >

        <span className="site-header__logo" aria-hidden="true">
        <svg
            viewBox="0 0 24 24"
            width="30"
            height="30"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M12 7.5C9.5 5.5 6.5 5 3 5v13c3.5 0 6.5.5 9 2.5" />
            <path d="M12 7.5C14.5 5.5 17.5 5 21 5v13c-3.5 0-6.5.5-9 2.5" />
            <path d="M12 7.5v13" />
        </svg>
        </span>

        <span className="site-header__brand-content">
        <span className="site-header__brand-text">
            {t('navigation.brand')}
        </span>

        <span className="site-header__tagline">
            {t('navigation.tagline')}
        </span>
        </span>

        </a>

        <nav
          className="site-header__nav"
          aria-label={t('navigation.label')}
        >
          <a href="#home">
            {t('navigation.home')}
          </a>

          <a href="#recommendations">
            {t('navigation.recommendations')}
          </a>

          <a href="#library">
            {t('navigation.library')}
          </a>
        </nav>

        <div className="site-header__language">
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  )
}
