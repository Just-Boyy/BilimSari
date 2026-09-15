import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { Card } from "../components/ui/Card";
import { StatusIcon } from "../components/ui/LockIcon";
import { apiClient } from "../lib/apiClient";
import { useProgressStore } from "../store/useProgressStore";
import type { TopicOut } from "../types/api";

export function Topics() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { sectionId } = useParams<{ sectionId: string }>();
  const [topics, setTopics] = useState<TopicOut[] | null>(null);
  const setSectionTopics = useProgressStore((state) => state.setSectionTopics);

  useEffect(() => {
    if (!sectionId) return;
    apiClient.get<TopicOut[]>(`/sections/${sectionId}/topics`).then((res) => {
      setTopics(res.data);
      setSectionTopics(
        Number(sectionId),
        Object.fromEntries(res.data.map((topic) => [topic.id, topic.status])),
      );
    });
  }, [sectionId, setSectionTopics]);

  const liveStatuses = useProgressStore((state) => (sectionId ? state.bySection[Number(sectionId)] : undefined));

  return (
    <AppShell title={t("topics.title")}>
      {topics === null ? (
        <p className="text-neutral-text/60 dark:text-white/60">{t("common.loading")}</p>
      ) : (
        <div className="flex flex-col gap-3">
          {topics.map((topic) => {
            const status = liveStatuses?.[topic.id] ?? topic.status;
            const locked = status === "locked";
            return (
              <Card
                key={topic.id}
                onClick={() => !locked && navigate(`/topics/${topic.id}?section=${sectionId}`)}
                className={locked ? "opacity-60" : "cursor-pointer"}
              >
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{topic.title}</p>
                  <StatusIcon status={status} />
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}
