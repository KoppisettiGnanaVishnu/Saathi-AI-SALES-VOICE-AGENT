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

  let hint =
    "Click the mic and speak, or type a message. Browser speech recognition powers the demo.";
  if (!sttSupported) {
    hint = "Voice input needs Chrome or Edge. Text input works everywhere.";
  } else if (listening) {
    hint = "Listening — speak, then pause. Your words appear above.";
  } else if (speaking) {
    hint = "Saathi is speaking. Click the mic to interrupt.";
  } else if (busy) {
    hint = "Saathi is thinking…";
  } else if (!callActive) {
    hint = "This call has ended. Start a new call to continue.";
  }

  return (
    <div className="composer">
      <div className="quick-prompts">
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

      {listening && (
        <div className="interim-line">{interim || "Listening…"}</div>
      )}

      <form
        className="composer__form"
        onSubmit={(event) => {
          event.preventDefault();
          onSend(text);
        }}
      >
        <input
          className="composer__input"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={
            listening
              ? "Listening…"
              : sttSupported
                ? "Type a message, or use the mic"
                : "Type a message"
          }
          disabled={disabled}
          aria-label="Message to the sales agent"
        />
        <button
          type="submit"
          className="btn btn--primary"
          disabled={disabled || !text.trim()}
        >
          Send
        </button>
        <button
          type="button"
          className={`mic ${listening ? "mic--live" : ""}`}
          onClick={onMic}
          disabled={disabled || !sttSupported}
          title={
            sttSupported
              ? listening
                ? "Stop listening"
                : "Start speaking"
              : "Voice input is not supported in this browser"
          }
          aria-label={listening ? "Stop listening" : "Start speaking"}
        >
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Z"
              stroke="currentColor"
              strokeWidth="1.8"
            />
            <path
              d="M19 11a7 7 0 0 1-14 0M12 18v3M9 21h6"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </form>

      <p className="composer__hint">{hint}</p>
    </div>
  );
}
