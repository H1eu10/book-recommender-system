import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

import { isAppLocale } from '../i18n'

function LanguageSwitcher() {
  const { t, i18n } = useTranslation()
const resolvedLanguage = i18n.resolvedLanguage ?? null
  const locale = isAppLocale(resolvedLanguage)
    ? resolvedLanguage
    : 'en'

  useEffect(() => {
    document.documentElement.lang = locale
    document.title = t('app.name')
  }, [locale, t])

  async function changeLocale(value: string) {
    if (!isAppLocale(value)) {
      return
    }

    await i18n.changeLanguage(value)

    try {
      localStorage.setItem('app-locale', value)
    } catch {
      // Language switching still works if storage is unavailable.
    }
  }

  return (
    <label className="language-switcher">
      <span>{t('locale.label')}</span>

      <select
        value={locale}
        onChange={(event) => {
          void changeLocale(event.target.value)
        }}
      >
        <option value="en">English</option>
        <option value="ru">Русский</option>
        <option value="vi">Tiếng Việt</option>
      </select>
    </label>
  )
}

export default LanguageSwitcher