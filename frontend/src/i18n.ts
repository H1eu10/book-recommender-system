import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import ru from './locales/ru.json'
import vi from './locales/vi.json'

export const supportedLocales = ['en', 'ru', 'vi'] as const

export type AppLocale = (typeof supportedLocales)[number]

export function isAppLocale(value: string | null): value is AppLocale {
  return supportedLocales.some((locale) => locale === value)
}

function getInitialLocale(): AppLocale {
  try {
    const savedLocale = localStorage.getItem('app-locale')
    return isAppLocale(savedLocale) ? savedLocale : 'en'
  } catch {
    return 'en'
  }
}

export const i18nReady = i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ru: { translation: ru },
      vi: { translation: vi },
    },
    lng: getInitialLocale(),
    fallbackLng: 'en',
    supportedLngs: [...supportedLocales],
    interpolation: {
      escapeValue: false,
    },
  })

export default i18n