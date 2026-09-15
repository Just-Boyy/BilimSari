import { create } from "zustand";

import type { TopicStatus } from "../types/api";

interface ProgressState {
  /** sectionId -> (topicId -> status) — mavzular ro'yxati keshi, progress/complete'dan keyin yangilanadi. */
  bySection: Record<number, Record<number, TopicStatus>>;
  setSectionTopics: (sectionId: number, statuses: Record<number, TopicStatus>) => void;
  markCompleted: (sectionId: number, topicId: number) => void;
}

export const useProgressStore = create<ProgressState>((set) => ({
  bySection: {},
  setSectionTopics: (sectionId, statuses) =>
    set((state) => ({ bySection: { ...state.bySection, [sectionId]: statuses } })),
  markCompleted: (sectionId, topicId) =>
    set((state) => ({
      bySection: {
        ...state.bySection,
        [sectionId]: { ...state.bySection[sectionId], [topicId]: "completed" },
      },
    })),
}));
