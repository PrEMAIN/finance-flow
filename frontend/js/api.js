const API_BASE = "/api";
const TOKEN_KEY = "finance_flow_token";
const OFFLINE_QUEUE_KEY = "finance_flow_offline_queue";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function apiRequest(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await response.json();
  } else if (contentType.includes("text/csv")) {
    data = await response.text();
  }

  if (!response.ok) {
    const message = data?.error || "Ошибка запроса";
    throw new Error(message);
  }
  return data;
}

function queueOfflineRequest(path, method, body) {
  const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || "[]");
  queue.push({ path, method, body, ts: Date.now() });
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
}

async function flushOfflineQueue() {
  const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || "[]");
  if (!queue.length || !navigator.onLine || !getToken()) return;

  const remaining = [];
  for (const item of queue) {
    try {
      await apiRequest(item.path, {
        method: item.method,
        body: JSON.stringify(item.body),
      });
    } catch {
      remaining.push(item);
    }
  }
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
}

async function apiPost(path, body, allowOffline = false) {
  try {
    return await apiRequest(path, { method: "POST", body: JSON.stringify(body) });
  } catch (err) {
    if (allowOffline && !navigator.onLine) {
      queueOfflineRequest(path, "POST", body);
      throw new Error("OFFLINE_QUEUED");
    }
    throw err;
  }
}

window.addEventListener("online", () => flushOfflineQueue());

export const api = {
  getToken,
  setToken,
  flushOfflineQueue,
  register: (data) => apiRequest("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => apiRequest("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => apiRequest("/auth/me"),
  getTransactions: (params) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/transactions${query ? `?${query}` : ""}`);
  },
  createTransaction: (data) => apiPost("/transactions", data, true),
  updateTransaction: (id, data) =>
    apiRequest(`/transactions/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteTransaction: (id) => apiRequest(`/transactions/${id}`, { method: "DELETE" }),
  exportCsv: async () => {
    const token = getToken();
    const response = await fetch(`${API_BASE}/transactions/export`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Не удалось экспортировать данные");
    return response.blob();
  },
  getCategories: () => apiRequest("/categories"),
  createCategory: (data) => apiPost("/categories", data),
  deleteCategory: (id) => apiRequest(`/categories/${id}`, { method: "DELETE" }),
  getLimits: () => apiRequest("/budget-limits"),
  createLimit: (data) => apiPost("/budget-limits", data),
  deleteLimit: (id) => apiRequest(`/budget-limits/${id}`, { method: "DELETE" }),
  getGoals: () => apiRequest("/goals"),
  createGoal: (data) => apiPost("/goals", data),
  contributeGoal: (id, amount) =>
    apiPost(`/goals/${id}/contribute`, { amount }),
  deleteGoal: (id) => apiRequest(`/goals/${id}`, { method: "DELETE" }),
  getAchievements: () => apiRequest("/achievements"),
  getNotifications: () => apiRequest("/notifications"),
  markNotificationRead: (id) =>
    apiRequest(`/notifications/${id}/read`, { method: "PUT" }),
  markAllNotificationsRead: () =>
    apiRequest("/notifications/read-all", { method: "PUT" }),
  getSummary: (period) => apiRequest(`/statistics/summary?period=${period}`),
  getChart: (period) => apiRequest(`/statistics/chart?period=${period}`),
};
