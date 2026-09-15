import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuthStore } from "../store/useAuthStore";

export function Home() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  return (
    <div className="mx-auto min-h-screen max-w-md px-4 py-6">
      <h1 className="text-xl font-semibold">
        {t("home.greeting")}
        {user?.first_name ? `, ${user.first_name}` : ""} 👋
      </h1>

      <Card className="mt-4 flex items-center justify-between">
        <div>
          <p className="text-sm text-neutral-text/60 dark:text-white/60">{t("home.streak")}</p>
          <p className="text-2xl font-semibold text-primary">{user?.streak ?? 0} 🔥</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-neutral-text/60 dark:text-white/60">XP</p>
          <p className="text-2xl font-semibold text-primary">{user?.total_xp ?? 0}</p>
        </div>
      </Card>

      <Card className="mt-4">
        <p className="mb-3 text-neutral-text/70 dark:text-white/70">{t("home.continueCard")}</p>
        <Button onClick={() => navigate("/subjects")}>{t("home.goToSubjects")}</Button>
      </Card>
    </div>
  );
}
