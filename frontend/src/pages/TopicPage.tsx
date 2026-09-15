import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { LessonRenderer } from "../components/lesson/LessonRenderer";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Tabs } from "../components/ui/Tabs";
import { apiClient } from "../lib/apiClient";
import { cacheLesson, readCachedLesson } from "../lib/lessonCache";
import i18n from "../i18n";
import { useProgressStore } from "../store/useProgressStore";
import type { LessonOut, ProgressCompleteResponse } from "../types/api";

type TabKey = "lesson" | "test" | "quiz" | "homework";

export function TopicPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { topicId } = useParams<{ topicId: string }>();
  const [searchParams] = useSearchParams();
  const sectionId = searchParams.get("section");

  const [activeTab, setActiveTab] = useState<TabKey>("lesson");
  const [lesson, setLesson] = useState<LessonOut | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [completing, setCompleting] = useState(false);
  const markCompleted = useProgressStore((state) => state.markCompleted);

  useEffect(() => {
    if (!topicId) return;
    const lang = i18n.language;

    apiClient
      .get<LessonOut>(`/topics/${topicId}/lesson`)
      .then((res) => {
        setLesson(res.data);
        setIsOffline(false);
        cacheLesson(Number(topicId), lang, res.data);
      })
      .catch(() => {
        const cached = readCachedLesson(Number(topicId), lang);
        if (cached) {
          setLesson(cached);
          setIsOffline(true);
        }
      });
  }, [topicId]);

  async function handleUnderstood() {
    if (!topicId) return;
    setCompleting(true);
    try {
      await apiClient.post<ProgressCompleteResponse>("/progress/complete", {
        topic_id: Number(topicId),
        stage: "lesson",
      });
      if (sectionId) markCompleted(Number(sectionId), Number(topicId));
      navigate(-1);
    } finally {
      setCompleting(false);
    }
  }

  const tabs = [
    { key: "lesson", label: t("topic.tabLesson") },
    { key: "test", label: t("topic.tabTest"), locked: true },
    { key: "quiz", label: t("topic.tabQuiz"), locked: true },
    { key: "homework", label: t("topic.tabHomework"), locked: true },
  ];

  return (
    <AppShell title={lesson?.title ?? t("common.loading")}>
      <Tabs tabs={tabs} active={activeTab} onChange={(key) => setActiveTab(key as TabKey)} />

      <div className="mt-4">
        {activeTab === "lesson" ? (
          lesson ? (
            <>
              {(lesson.is_fallback || isOffline) && (
                <div className="mb-3 flex gap-2">
                  {lesson.is_fallback && <Badge variant="warning">{t("common.notAvailableInLanguage")}</Badge>}
                  {isOffline && <Badge variant="neutral">{t("common.offline")}</Badge>}
                </div>
              )}
              <LessonRenderer contentHtml={lesson.content_html} />
              <Button className="mt-6" onClick={handleUnderstood} disabled={completing}>
                {t("topic.understood")}
              </Button>
            </>
          ) : (
            <p className="text-neutral-text/60 dark:text-white/60">{t("common.loading")}</p>
          )
        ) : (
          <div className="rounded-xl bg-neutral-border p-6 text-center dark:bg-dark-card">
            <p className="font-semibold">{t("topic.comingSoon")}</p>
            <p className="mt-1 text-sm text-neutral-text/60 dark:text-white/60">{t("topic.comingSoonDesc")}</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
