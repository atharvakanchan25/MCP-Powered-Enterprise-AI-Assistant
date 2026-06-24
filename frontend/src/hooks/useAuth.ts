import { create } from "zustand";
import { authApi } from "@/lib/api";

interface User { id: string; email: string; username: string; role: string }
interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("access_token") : null,

  login: async (email, password) => {
    const { data } = await authApi.login(email, password);
    localStorage.setItem("access_token", data.access_token);
    set({ token: data.access_token });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    set({ user: null, token: null });
  },

  fetchMe: async () => {
    const { data } = await authApi.me();
    set({ user: data });
  },
}));
