import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { ProgressRing } from "../components/ui/ProgressRing";
import { apiClient } from "../lib/apiClient";
import type { SubjectOut } from "../types/api";

export function Subjects() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [subjects, setSubjects] = useState<SubjectOut[] | null>(null);

  useEffect(() => {
    apiClient.get<SubjectOut[]>("/subjects").then((res) => setSubjects(res.data));
  }, []);

  return (
    <AppShell title={t("subjects.title")}>
      {subjects === null ? (
        <p className="text-neutral-text/60 dark:text-white/60">{t("common.loading")}</p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {subjects.map((subject) => (
            <Card
              key={subject.id}
              onClick={() => navigate(`/subjects/${subject.id}/sections`)}
              className="cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <span
                  className="flex h-10 w-10 items-center justify-center rounded-xl text-lg"
                  style={{ backgroundColor: `${subject.color ?? "#5CA904"}22`, color: subject.color ?? "#5CA904" }}
                >
                  📘
                </span>
                <ProgressRing percent={subject.progress_pct} size={40} strokeWidth={4} />
              </div>
              <p className="mt-3 font-semibold">{subject.title}</p>
              {subject.is_fallback && (
                <Badge variant="warning" className="mt-2">
                  {t("common.notAvailableInLanguage")}
                </Badge>
              )}
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
