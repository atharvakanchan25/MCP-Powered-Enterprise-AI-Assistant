import axios from "axios";

const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/";
    }
    return Promise.reject(err);
  }
);

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: object) => api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
};

export const agentApi = {
  query: (query: string, conversation_id?: string) =>
    api.post("/agent/query", { query, conversation_id }),
  getMemory: () => api.get("/agent/memory"),
  storeMemory: (key: string, value: string) =>
    api.post("/agent/memory", { key, value }),
  listTools: () => api.get("/agent/tools"),
};

export const documentsApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/documents/upload", form);
  },
  list: () => api.get("/documents/"),
  delete: (id: string) => api.delete(`/documents/${id}`),
  search: (query: string) => api.post("/documents/search", { query }),
  queryKB: (query: string) => api.post("/documents/query", { query }),
};

export const visionApi = {
  analyze: (file: File, task: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("task", task);
    return api.post("/vision/analyze", form);
  },
};

export const adminApi = {
  dashboard: () => api.get("/admin/dashboard"),
  auditLogs: (limit = 50) => api.get(`/admin/audit-logs?limit=${limit}`),
  exportReport: (data: object) => api.post("/admin/reports/export", data, { responseType: "blob" }),
  tokenStats: (limit = 100) => api.get(`/admin/monitoring/tokens?limit=${limit}`),
  errorLogs: (limit = 50) => api.get(`/admin/monitoring/errors?limit=${limit}`),
};

export const conversationsApi = {
  list: (limit = 20) => api.get(`/conversations/?limit=${limit}`),
  get: (id: string) => api.get(`/conversations/${id}`),
  create: (title: string) => api.post("/conversations/", { title }),
  delete: (id: string) => api.delete(`/conversations/${id}`),
};

export default api;
