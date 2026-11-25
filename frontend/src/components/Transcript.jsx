import { useEffect, useRef } from "react";

function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const sources = [...new Set(message.meta?.sources || [])];
  const sentiment = message.meta?.sentiment;

  return (
    <div className={`message ${isUser ? "message--user" : "message--agent"}`}>
      <div className="avatar">{isUser ? "You" : "A"}</div>
      <div className="message__body">
        <div className="bubble">{message.text}</div>
        {(sources.length > 0 || (sentiment && !isUser)) && (
          <div className="message__meta">
            {sentiment && !isUser && (
              <span className={`sentiment sentiment--${sentiment}`}>
                {sentiment}
              </span>
            )}
            {sources.map((source) => (
              <span className="source-chip" key={source}>
                📄 {source}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Transcript({
  messages,
  interim,
  busy,
  speaking,
  starting,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, interim, busy, speaking]);

  return (
    <div className="transcript" aria-live="polite">
      {starting && messages.length === 0 && (
        <div className="transcript__empty">
          <div className="spinner" />
          <p>Connecting to the local agent…</p>
        </div>
      )}

      {!starting && messages.length === 0 && (
        <div className="transcript__empty">
          <p>Start by saying hello, or tap a suggestion below.</p>
        </div>
      )}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {interim && (
        <div className="message message--user">
          <div className="avatar">You</div>
          <div className="message__body">
            <div className="bubble bubble--interim">{interim}</div>
          </div>
        </div>
      )}

      {busy && (
        <div className="typing">
          <span />
          <span />
          <span />
          <em>Saathi is thinking…</em>
        </div>
      )}

      {speaking && <div className="speaking">🔊 Saathi is speaking…</div>}

      <div ref={bottomRef} />
    </div>
  );
}
