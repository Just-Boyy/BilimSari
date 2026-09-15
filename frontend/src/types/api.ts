export interface UserOut {
  id: number;
  telegram_id: number;
  first_name: string | null;
  lang: "uz" | "ru" | "en";
  grade: number | null;
  role: string;
  streak: number;
  total_xp: number;
}

export interface TelegramAuthResponse {
  token: string;
  user: UserOut;
}

export interface SubjectOut {
  id: number;
  slug: string;
  title: string;
  icon: string | null;
  color: string | null;
  order: number;
  progress_pct: number;
  is_fallback: boolean;
}

export interface SectionOut {
  id: number;
  slug: string;
  title: string;
  order: number;
  is_fallback: boolean;
}

export type TopicStatus = "locked" | "unlocked" | "completed";

export interface TopicOut {
  id: number;
  slug: string;
  title: string;
  order: number;
  status: TopicStatus;
  is_fallback: boolean;
}

export interface StageStatus {
  lesson: TopicStatus;
  test: TopicStatus;
  quiz: TopicStatus;
  homework: TopicStatus;
}

export interface LessonOut {
  topic_id: number;
  title: string;
  content_html: string;
  media: Record<string, unknown> | null;
  is_fallback: boolean;
  stage_status: StageStatus;
}

export interface ProgressCompleteResponse {
  topic_id: number;
  stage: string;
  is_completed: boolean;
  next_unlocked: { stage: string | null; topic_id: number | null } | null;
}
