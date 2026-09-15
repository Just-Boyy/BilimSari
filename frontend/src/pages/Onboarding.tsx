import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import i18n, { SUPPORTED_LANGS, type SupportedLang } from "../i18n";
import { apiClient } from "../lib/apiClient";
import { useAuthStore } from "../store/useAuthStore";
import type { UserOut } from "../types/api";

const LANG_LABELS: Record<SupportedLang, string> = { uz: "O'zbekcha", ru: "Русский", en: "English" };
const GRADES = Array.from({ length: 11 }, (_, i) => i + 1);

export function Onboarding() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const [lang, setLang] = useState<SupportedLang>((user?.lang as SupportedLang) ?? "uz");
  const [grade, setGrade] = useState<number | null>(user?.grade ?? null);
  const [saving, setSaving] = useState(false);

  async function handleContinue() {
    setSaving(true);
    try {
      const { data } = await apiClient.patch<UserOut>("/users/me", { lang, grade });
      updateUser(data);
      await i18n.changeLanguage(lang);
      navigate("/home", { replace: true });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-4 py-8">
      <div className="text-center">
        <img src="/assets/logo.png" alt="Bilim Sari" className="mx-auto h-16 w-16 rounded-xl" />
      </div>

      <Card>
        <h2 className="mb-3 font-semibold">{t("onboarding.chooseLanguage")}</h2>
        <div className="flex gap-2">
          {SUPPORTED_LANGS.map((code) => (
            <button
              key={code}
              onClick={() => setLang(code)}
              className={`flex-1 rounded-xl border px-3 py-2 text-sm font-semibold ${
                lang === code
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-neutral-border text-neutral-text/70 dark:border-dark-card dark:text-white/70"
              }`}
            >
              {LANG_LABELS[code]}
            </button>
          ))}
        </div>
      </Card>

      <Card>
        <h2 className="mb-3 font-semibold">{t("onboarding.chooseGrade")}</h2>
        <div className="grid grid-cols-4 gap-2">
          {GRADES.map((g) => (
            <button
              key={g}
              onClick={() => setGrade(g)}
              className={`rounded-xl border py-2 text-sm font-semibold ${
                grade === g
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-neutral-border text-neutral-text/70 dark:border-dark-card dark:text-white/70"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </Card>

      <Button onClick={handleContinue} disabled={saving || !grade}>
        {t("onboarding.continue")}
      </Button>
    </div>
  );
}
