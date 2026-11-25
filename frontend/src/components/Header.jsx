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
  const llmReady = Boolean(llm?.reachable && llm?.model_installed);

  return (
    <header className="header">
      <div className="brand">
        <div className="brand__mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3v3" /><path d="M12 18v3" /><path d="M4.2 7.5l2.6 1.5" /><path d="M17.2 15l2.6 1.5" /><path d="M4.2 16.5l2.6-1.5" /><path d="M17.2 9l2.6-1.5" /><circle cx="12" cy="12" r="4.2" />
          </svg>
        </div>
        <div className="brand__copy">
          <div className="brand__name">Saathi</div>
          <div className="brand__sub">by Fortivex AI</div>
        </div>
      </div>

      <div className="header__center">
        <div className={`system-pill ${llmReady ? "system-pill--ok" : "system-pill--warn"}`} title={llm?.model || "Checking local model"}>
          <span className="system-pill__dot" />
          <span>{llmReady ? "System ready" : llm?.reachable ? "Model needed" : "Checking system"}</span>
        </div>
      </div>

      <div className="header__actions">
        <label className="voice-toggle" title="Voice output">
          <span className="voice-toggle__label">Voice</span>
          <button
            type="button"
            role="switch"
            aria-checked={voiceEnabled}
            className={`switch ${voiceEnabled ? "switch--on" : ""}`}
            onClick={onToggleVoice}
          >
            <span className="switch__thumb" />
          </button>
        </label>

        <div className="lang-select">
          <select
            className="select"
            value={language}
            onChange={onLanguageChange}
            aria-label="Conversation language"
          >
            <option value="en-IN">English</option>
            <option value="hi-IN">हिन्दी</option>
          </select>
        </div>

        {callActive ? (
          <button type="button" className="btn btn--ghost" onClick={onEndCall} disabled={busy}>
            End call
          </button>
        ) : (
          <button type="button" className="btn btn--primary" onClick={onNewCall} disabled={busy}>
            New call
          </button>
        )}

        <button type="button" className="btn btn--subtle" onClick={onReset} disabled={busy} title="Clear demo data">
          Reset
        </button>
      </div>

      {!sttSupported && (
        <div className="header__note">
          Voice input needs Chrome or Edge. You can still type below.
        </div>
      )}
    </header>
  );
}
