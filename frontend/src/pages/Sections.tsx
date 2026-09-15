import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { apiClient } from "../lib/apiClient";
import type { SectionOut } from "../types/api";

export function Sections() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { subjectId } = useParams<{ subjectId: string }>();
  const [sections, setSections] = useState<SectionOut[] | null>(null);

  useEffect(() => {
    apiClient.get<SectionOut[]>(`/subjects/${subjectId}/sections`).then((res) => setSections(res.data));
  }, [subjectId]);

  return (
    <AppShell title={t("sections.title")}>
      {sections === null ? (
        <p className="text-neutral-text/60 dark:text-white/60">{t("common.loading")}</p>
      ) : (
        <div className="flex flex-col gap-3">
          {sections.map((section) => (
            <Card
              key={section.id}
              onClick={() => navigate(`/sections/${section.id}/topics`)}
              className="cursor-pointer"
            >
              <p className="font-semibold">{section.title}</p>
              {section.is_fallback && (
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
