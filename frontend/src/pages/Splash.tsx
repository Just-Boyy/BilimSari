import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { apiClient } from "../lib/apiClient";
import { useAuthStore } from "../store/useAuthStore";
import type { UserOut } from "../types/api";

export function Splash() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clear);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      const token = useAuthStore.getState().token;
      if (!token) {
        navigate("/register", { replace: true });
        return;
      }

      try {
        const { data } = await apiClient.get<UserOut>("/users/me");
        if (cancelled) return;
        setAuth(token, data);
        navigate(data.grade ? "/home" : "/onboarding", { replace: true });
      } catch {
        if (!cancelled) {
          clearAuth();
          navigate("/register", { replace: true });
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
      <p className="mt-4 text-sm text-neutral-text/50 dark:text-white/50">{t("common.loading")}</p>
    </div>
  );
}
