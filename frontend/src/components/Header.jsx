export default function Header({
  health,
  callActive,
  busy,
  onEndCall,
  onNewCall,
  onReset,
  language,
  onLanguageChange,
  voiceEnabled,
  onToggleVoice,
  sttSupported,
}) {
  const llm = health?.llm;
  const rag = health?.rag;

  let badgeClass = "badge--warn";
  let badgeText = "Checking Ollama";
  let badgeTitle = "Checking the local model status";

  if (llm) {
    if (!llm.reachable) {
      badgeClass = "badge--bad";
      badgeText = "Ollama offline";
      badgeTitle = llm.error || "Start Ollama and retry";
    } else if (!llm.model_installed) {
      badgeClass = "badge--warn";
      badgeText = "Model not pulled";
      badgeTitle = `Run: ollama pull ${llm.model}`;
    } else {
      badgeClass = "badge--ok";
      badgeText = "Local LLM ready";
      badgeTitle = llm.model;
    }
  }

  return (
    <header className="header">
      <div className="brand">
        <div className="brand__mark">F</div>
        <div>
          <h1 className="brand__name">Fortivex AI</h1>
          <p className="brand__sub">Mira · Autonomous Sales Voice Agent</p>
        </div>
      </div>

      <div className="header__badges">
        <span className={`badge ${badgeClass}`} title={badgeTitle}>
          <span className="badge__dot" />
          {badgeText}
        </span>
        <span className="badge badge--muted" title="Knowledge retrieval mode">
          RAG · {rag?.mode || "…"}
        </span>
        <span className="badge badge--muted" title="Browser speech support">
          {sttSupported ? "Voice ready" : "Text only"}
        </span>
        {llm?.model && (
          <span className="badge badge--muted" title="Configured local model">
            {llm.model}
          </span>
        )}
      </div>

      <div className="header__actions">
        <label className="lang">
          <span>Language</span>
          <select
            value={language}
            onChange={onLanguageChange}
            disabled={busy}
            aria-label="Conversation language"
          >
            <option value="en-IN">English (India)</option>
            <option value="hi-IN">हिंदी (India)</option>
          </select>
        </label>

        <button
          type="button"
          className={`icon-btn ${voiceEnabled ? "" : "icon-btn--off"}`}
          onClick={onToggleVoice}
          title={voiceEnabled ? "Mute agent voice" : "Unmute agent voice"}
          aria-label={voiceEnabled ? "Mute agent voice" : "Unmute agent voice"}
        >
          {voiceEnabled ? "🔊" : "🔇"}
        </button>

        <button
          type="button"
          className="btn btn--ghost"
          onClick={onReset}
          disabled={busy}
        >
          Reset
        </button>

        {callActive ? (
          <button
            type="button"
            className="btn btn--danger"
            onClick={onEndCall}
            disabled={busy}
          >
            End call
          </button>
        ) : (
          <button
            type="button"
            className="btn btn--primary"
            onClick={onNewCall}
            disabled={busy}
          >
            New call
          </button>
        )}
      </div>
    </header>
  );
}
