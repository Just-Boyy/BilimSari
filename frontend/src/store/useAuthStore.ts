import { create } from "zustand";

import type { UserOut } from "../types/api";

const TOKEN_STORAGE_KEY = "bilimsari.token";

interface AuthState {
  token: string | null;
  user: UserOut | null;
  setAuth: (token: string, user: UserOut) => void;
  updateUser: (user: UserOut) => void;
  clear: () => void;
}

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  token: readStoredToken(),
  user: null,
  setAuth: (token, user) => {
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } catch {
      // localStorage mavjud bo'lmasligi mumkin (masalan, maxfiy rejim) — sessiya baribir ishlayveradi.
    }
    set({ token, user });
  },
  updateUser: (user) => set({ user }),
  clear: () => {
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    } catch {
      // e'tiborsiz qoldiriladi
    }
    set({ token: null, user: null });
  },
}));
