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
  chatStream: async (sessionId, message, language, onEvent, signal) => {
    const response = await fetch(`${BASE}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message, language }),
      signal,
    });
    if (!response.ok) {
      let detail = `Request failed (${response.status})`;
      try {
        const body = await response.json();
        detail = body.detail || detail;
      } catch {
        // keep generic
      }
      throw new Error(detail);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finalEvent = null;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let newline = buffer.indexOf("\n");
      while (newline !== -1) {
        const line = buffer.slice(0, newline).trim();
        buffer = buffer.slice(newline + 1);
        if (line) {
          const event = JSON.parse(line);
          onEvent?.(event);
          if (event.type === "final") finalEvent = event;
          if (event.type === "error") throw new Error(event.detail || "Agent error");
        }
        newline = buffer.indexOf("\n");
      }
    }
    if (!finalEvent) throw new Error("Streaming response ended before final state");
    return finalEvent;
  },
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
