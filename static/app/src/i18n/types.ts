import type en from '@/locales/en.json'

type LocaleMessages = typeof en

type LocalePath<T> = T extends string
  ? never
  : {
      [K in Extract<keyof T, string>]: T[K] extends string ? K : `${K}.${LocalePath<T[K]>}`
    }[Extract<keyof T, string>]

export type LocaleMessageKey = LocalePath<LocaleMessages>
