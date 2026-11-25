export default function Composer({
  text,
  setText,
  onSend,
  onMic,
  listening,
  interim,
  busy,
  speaking,
  sttSupported,
  quickPrompts,
  callActive,
}) {
  const disabled = !callActive || busy;

  let hint = "Speak or type to continue the conversation.";
  if (!sttSupported) hint = "Voice input needs Chrome or Edge. Text works everywhere.";
  else if (listening) hint = "Listening — pause when you're done.";
  else if (speaking) hint = "Saathi is speaking. Tap the mic to interrupt.";
  else if (busy) hint = "Saathi is responding…";
  else if (!callActive) hint = "This conversation has ended. Start a new call to continue.";

  return (
    <div className="composer">
      <div className="quick-prompts" aria-label="Suggested prompts">
        {quickPrompts.map((prompt) => (
          <button
            type="button"
            className="chip"
            key={prompt}
            onClick={() => onSend(prompt)}
            disabled={disabled}
          >
            {prompt}
          </button>
        ))}
      </div>

      <form
        className="composer__form"
        onSubmit={(event) => {
          event.preventDefault();
          onSend(text);
        }}
      >
        <button
          type="button"
          className={`mic ${listening ? "mic--on" : ""}`}
          onClick={onMic}
          disabled={!callActive || busy || !sttSupported}
          title={sttSupported ? (listening ? "Stop listening" : "Start voice input") : "Voice input unavailable"}
          aria-label={listening ? "Stop listening" : "Start voice input"}
        >
          {listening ? (
            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2"/></svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="18" height="18" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"/><path d="M19 11a7 7 0 0 1-14 0"/><path d="M12 18v3"/></svg>
          )}
        </button>

        <input
          className="composer__input"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={callActive ? "Ask about pricing, security, or booking a demo…" : "Conversation ended"}
          disabled={!callActive || busy}
          aria-label="Message to Saathi"
        />

        <button
          type="submit"
          className="btn btn--primary composer__send"
          disabled={disabled || !text.trim()}
          aria-label="Send message"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </button>
      </form>

      <div className="composer__hint">
        <span>{hint}</span>
        {interim && <span className="composer__interim">Hearing: {interim}</span>}
      </div>
    </div>
  );
}
