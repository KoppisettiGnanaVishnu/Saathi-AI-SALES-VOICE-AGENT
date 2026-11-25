import { useEffect, useRef } from "react";

function MessageBubble({ message, onPickSlot, busy }) {
  const isUser = message.role === "user";
  const slots = !isUser ? message.meta?.slots || [] : [];
  const booking = !isUser ? message.meta?.booking : null;
  return (
    <div className={`message ${isUser ? "message--user" : "message--agent"}`}>
      <div className="message__body">
        {!isUser && <div className="message__label">Saathi</div>}
        <div className={`bubble ${message.pending ? "bubble--pending" : ""}`}>{message.text || "…"}</div>
        {slots.length > 0 && !booking && (
          <div className="chat-slots" aria-label="Available demo slots">
            {slots.map((slot) => (
              <button
                type="button"
                className="chat-slot"
                key={slot.id}
                onClick={() => onPickSlot?.(slot.id)}
                disabled={busy}
              >
                <span className="chat-slot__label">{slot.label}</span>
                <span className="chat-slot__cta">Book this slot</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Transcript({ messages, interim, busy, speaking, starting, onPickSlot }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, interim, busy, speaking]);

  return (
    <div className="transcript" role="log" aria-live="polite" aria-label="Conversation transcript">
      {starting && (
        <div className="empty-state">
          <div className="empty-state__mark" aria-hidden="true" />
          <p className="empty-state__title">Preparing Saathi</p>
          <p className="empty-state__text">Setting up the conversation space.</p>
        </div>
      )}

      {!starting && messages.length === 0 && (
        <div className="empty-state">
          <div className="empty-state__mark" aria-hidden="true" />
          <p className="empty-state__title">Start the conversation</p>
          <p className="empty-state__text">Ask about Fortivex AI, pricing, security, or book a demo.</p>
        </div>
      )}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} onPickSlot={onPickSlot} busy={busy} />
      ))}

      {interim && (
        <div className="message message--user message--interim">
          <div className="message__body">
            <div className="bubble bubble--interim">{interim}</div>
          </div>
        </div>
      )}

      {busy && messages[messages.length - 1]?.role !== "assistant" && (
        <div className="message message--agent">
          <div className="message__body">
            <div className="message__label">Saathi</div>
            <div className="bubble bubble--thinking" aria-label="Saathi is thinking">
              <span /><span /><span />
            </div>
          </div>
        </div>
      )}

      {speaking && !busy && (
        <div className="speaking-indicator" aria-label="Saathi is speaking">
          <span /><span /><span /><span />
        </div>
      )}

      <div ref={endRef} />
    </div>
  );
}
