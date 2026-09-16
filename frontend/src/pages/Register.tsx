import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { apiClient } from "../lib/apiClient";
import { useAuthStore } from "../store/useAuthStore";
import type { TelegramAuthResponse } from "../types/api";

export function Register() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setSaving(true);
    setError(null);
    try {
      const { data } = await apiClient.post<TelegramAuthResponse>("/auth/register", { name: trimmed });
      setAuth(data.token, data.user);
      navigate(data.user.grade ? "/home" : "/onboarding", { replace: true });
    } catch {
      setError(t("common.error"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-4 py-8">
      <div className="text-center">
        <img src="/assets/logo.png" alt="Bilim Sari" className="mx-auto h-16 w-16 rounded-xl" />
        <h1 className="mt-3 text-2xl font-semibold text-primary">Bilim Sari</h1>
        <p className="text-neutral-text/70 dark:text-white/70">{t("app.slogan")}</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label htmlFor="name" className="font-semibold">
            Ismingiz
          </label>
          <input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ismingizni kiriting"
            autoFocus
            className="rounded-xl border border-neutral-border bg-transparent px-3 py-2 outline-none focus:border-primary dark:border-dark-card"
          />
          {error ? <p className="text-sm text-error">{error}</p> : null}
          <Button type="submit" disabled={saving || !name.trim()}>
            Boshlash
          </Button>
        </form>
      </Card>
    </div>
  );
}
