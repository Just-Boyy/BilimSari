import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { apiClient } from "../lib/apiClient";
import { getDebugInfo, getTelegramLanguageCode, waitForTelegramReady } from "../lib/telegram";
import { useAuthStore } from "../store/useAuthStore";
import type { TelegramAuthResponse } from "../types/api";
import i18n, { detectInitialLang } from "../i18n";

export function Splash() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      // Telegram Desktop'da platform va initData ikkalasi ham darhol emas, kechikib keladi —
      // shu sababli "Telegram ichida emasmiz" xatosini bermasdan turib qisqa muddat kutamiz.
      const { insideTelegram, initData } = import.meta.env.DEV
        ? { insideTelegram: false, initData: "" }
        : await waitForTelegramReady();
      if (cancelled) return;

      if (!insideTelegram && !import.meta.env.DEV) {
        setError(`Ilova faqat Telegram ichida ishlaydi. Iltimos, botdagi tugma orqali oching. [${getDebugInfo()}]`);
        return;
      }

      try {
        if (insideTelegram && !initData) {
          setError(`${t("common.error")} [${getDebugInfo()}]`);
          return;
        }

        // DIQQAT: /auth/dev-login faqat backend ENV=development bo'lganda ishlaydi
        // (production'da 404) — bu shunchaki Telegram'siz brauzerda UI'ni sinash uchun.
        const { data } = insideTelegram
          ? await apiClient.post<TelegramAuthResponse>("/auth/telegram", { init_data: initData })
          : await apiClient.post<TelegramAuthResponse>("/auth/dev-login");
        if (cancelled) return;

        setAuth(data.token, data.user);
        const lang = detectInitialLang(data.user.lang ?? getTelegramLanguageCode());
        await i18n.changeLanguage(lang);

        navigate(data.user.grade ? "/home" : "/onboarding", { replace: true });
      } catch (e) {
        if (!cancelled) {
          const status = (e as { response?: { status?: number } })?.response?.status;
          setError(`${t("common.error")} [status=${status ?? "?"} ${getDebugInfo()}]`);
        }
      }
    }

    void run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <img src="/assets/logo.png" alt="Bilim Sari" className="h-24 w-24 rounded-2xl shadow-md" />
      <h1 className="text-2xl font-semibold text-primary">Bilim Sari</h1>
      <p className="text-neutral-text/70 dark:text-white/70">{t("app.slogan")}</p>
      {error ? (
        <p className="mt-4 text-sm text-error">{error}</p>
      ) : (
        <p className="mt-4 text-sm text-neutral-text/50 dark:text-white/50">{t("common.loading")}</p>
      )}
    </div>
  );
}
