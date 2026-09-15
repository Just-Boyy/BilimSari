import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./en.json";
import ru from "./ru.json";
import uz from "./uz.json";

export const SUPPORTED_LANGS = ["uz", "ru", "en"] as const;
export type SupportedLang = (typeof SUPPORTED_LANGS)[number];

void i18n.use(initReactI18next).init({
  resources: {
    uz: { translation: uz },
    ru: { translation: ru },
    en: { translation: en },
  },
  lng: "uz",
  fallbackLng: "uz",
  interpolation: { escapeValue: false },
});

export function detectInitialLang(telegramLanguageCode?: string): SupportedLang {
  const code = (telegramLanguageCode ?? "uz").slice(0, 2);
  return (SUPPORTED_LANGS as readonly string[]).includes(code) ? (code as SupportedLang) : "uz";
}

export default i18n;
