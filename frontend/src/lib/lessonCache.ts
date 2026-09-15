import type { LessonOut } from "../types/api";

function cacheKey(topicId: number, lang: string): string {
  return `bilimsari.lesson.${topicId}.${lang}`;
}

export function cacheLesson(topicId: number, lang: string, lesson: LessonOut): void {
  try {
    localStorage.setItem(cacheKey(topicId, lang), JSON.stringify(lesson));
  } catch {
    // localStorage mavjud bo'lmasligi mumkin — offline kesh shunchaki ishlamaydi.
  }
}

export function readCachedLesson(topicId: number, lang: string): LessonOut | null {
  try {
    const raw = localStorage.getItem(cacheKey(topicId, lang));
    return raw ? (JSON.parse(raw) as LessonOut) : null;
  } catch {
    return null;
  }
}
