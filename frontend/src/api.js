const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // keep the generic message
    }
    throw new Error(detail);
  }

  return response.json();
}

export const api = {
  createSession: () => request("/api/session", { method: "POST" }),
  chat: (sessionId, message, language) =>
    request("/api/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, message, language }),
    }),
  bookSlot: (sessionId, slotId) =>
    request(`/api/session/${sessionId}/book`, {
      method: "POST",
      body: JSON.stringify({ slot_id: slotId }),
    }),
  endCall: (sessionId) =>
    request(`/api/session/${sessionId}/end`, { method: "POST" }),
  insights: () => request("/api/insights"),
  health: () => request("/api/health"),
  reset: () => request("/api/demo/reset", { method: "POST" }),
};
