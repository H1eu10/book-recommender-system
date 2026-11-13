
import { useTranslation } from 'react-i18next'

const navigationLinks = [
  { href: '#home', key: 'navigation.home' },
  { href: '#recommendations', key: 'navigation.recommendations' },
  { href: '#library', key: 'navigation.library' },
] as const

const projectInfo = {
  teamName: 'МПИ-25-1-2',

  members: [
    'Nhu Ngoc Le',
    'Minh Hieu Pham',
    'Khac Ngu Giang',
  ],

  email: 'ngocleltt@gmail.com',

  github: 'https://github.com/H1eu10/book-recommender-system',

  university: 'NUST MISIS',
  location: 'Moscow, Russia',
}

export default function SiteFooter() {
  const { t } = useTranslation()

  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__grid">

          <div className="site-footer__about">
            <div className="site-footer__brand">
              <svg
                viewBox="0 0 24 24"
                width="30"
                height="30"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 7.5C9.5 5.5 6.5 5 3 5v13c3.5 0 6.5.5 9 2.5" />
                <path d="M12 7.5C14.5 5.5 17.5 5 21 5v13c-3.5 0-6.5.5-9 2.5" />
                <path d="M12 7.5v13" />
              </svg>

              <span>{t('navigation.brand')}</span>
            </div>

            <p className="site-footer__description">
              {t('footer.description')}
            </p>
          </div>

          <nav
            className="site-footer__navigation"
            aria-label={t('footer.navigationLabel')}
          >
            <h2>{t('footer.explore')}</h2>

            <ul>
              {navigationLinks.map(link => (
                <li key={link.href}>
                  <a href={link.href}>
                    {t(link.key)}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div className="site-footer__team">
            <h2>{t('footer.team')}</h2>

            <p className="site-footer__team-name">
              {projectInfo.teamName}
            </p>

            <ul className="site-footer__members">
              {projectInfo.members.map(member => (
                <li key={member}>{member}</li>
              ))}
            </ul>
          </div>

          <div className="site-footer__contact">
            <h2>{t('footer.contact')}</h2>

            <p className="site-footer__academic-item">
              <span aria-hidden="true">✦</span>
              <span>{projectInfo.university}</span>
            </p>

            <p className="site-footer__academic-item">
              <span aria-hidden="true">⌖</span>
              <span>{projectInfo.location}</span>
            </p>

            <p className="site-footer__academic-item">
              <span aria-hidden="true">✉</span>
              <a href={`mailto:${projectInfo.email}`}>
                {projectInfo.email}
              </a>
            </p>

            <p className="site-footer__academic-item">
              <span aria-hidden="true">⌘</span>
              <a
                href={projectInfo.github}
                target="_blank"
                rel="noopener noreferrer"
              >
                {t('footer.github')}
              </a>
            </p>
          </div>
        </div>

        <div className="site-footer__bottom">
          <span>{t('footer.project')}</span>
          <span>{t('footer.educationalNote')}</span>
        </div>
      </div>
    </footer>
  )
}
